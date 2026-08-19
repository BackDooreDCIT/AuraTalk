import asyncio
from datetime import date
import json
import os
import subprocess
import tempfile
import time
from typing import Dict
from fastapi import APIRouter, File, Request, Depends, HTTPException, UploadFile
from fastapi import params
from fastapi.params import Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import torch
from fastapi import Response
from transformers import pipeline
from pydantic import BaseModel


# from supabase import *
from app.db.db import supabase, get_user

#^ patient

router = APIRouter()
templates = Jinja2Templates(directory="templates")

#^ from noeysod - อันนี้เช็ค role
def check_patient_role(request: Request):
    role = request.cookies.get("role")
    if not role:
        return RedirectResponse(url="/login", status_code=302)
    if role == "slp":
        return RedirectResponse(url="/slp/", status_code=302)
    if role != "patient":
        return RedirectResponse(url="/login", status_code=302)
        #* 2
        # raise HTTPException(
        #     status_code=302, 
        #     detail="Redirect", 
        #     headers={"Location": "/slp"}
        # )

#^ เก็บไว้ดูเป็นตัวอย่าง
# @router.get("/")
# async def showHome(request: Request):
#     return templates.TemplateResponse(request=request, name="home_patient.html", context={
#         "request": request
#     })

#* 2
# @router.get("/")
# async def showHome(request: Request, _: None = Depends(check_patient_role)):
#     return templates.TemplateResponse(request=request, name="home_patient.html", context={
#         "request": request
#     })

@router.get("/")
async def showHome(request: Request, resp=Depends(check_patient_role)):
    if isinstance(resp, RedirectResponse):
        return resp
    
        # ดึง user_id จาก cookie
    user_id = request.cookies.get("user_id")
    assignments = []
    if user_id:
        # response = supabase.table("assignment_full").select("*").eq("patient_id", user_id).execute()
        # assignments = response.data

        response = supabase.table("home").select("*").eq("patientid", user_id).execute()
        assignments = response.data

        response2 = supabase.table("home_assignmentdescription").select("*").execute()
        assignments_description = response2.data

        # response2 = await db.execute(
        #     text("SELECT * FROM home_assignmentdescription"))
        # assignments_description = [dict(row) for row in response.mappings().all()]

        response3 = supabase.table("assignmentforanotherpage").select("*").eq("patientid", user_id).execute()
        asganotherpage = response3.data
        print("🤓🤓🤓lenasganotherpage:", len(asganotherpage))
        print("🤓🤓🤓lenassignment:", len(assignments))


        print(f"😳😳😳😳 userid: {user_id} \nasganotherpage: {asganotherpage} 😳😳😳😳")  # Debugging line
        print(f"🪲🪲🪲 Assignments for user_id {user_id}: {assignments} 🪲🪲🪲")  # Debugging line

        print(f"🙏🙏🙏 Assignments description: {assignments_description} 🙏🙏🙏")


    return templates.TemplateResponse(request=request, name="home_patient.html", context={
        "request": request,
        "assignments": assignments,
        "assignments_description": assignments_description,
        'asganotherpage': asganotherpage
    })

@router.get("/mission")
async def showMission(request: Request, resp=Depends(check_patient_role)):
    if isinstance(resp, RedirectResponse):
        return resp

    userId = request.cookies.get("user_id")

    patient_response = supabase.table("patients").select("*").eq("patientid", userId).single().execute()
    patient = patient_response.data if patient_response.data else {}

    today_str = date.today().isoformat()

    response = supabase.table("mission").select("*").eq("patientid", userId).execute()
    missions = response.data[0]["data"] if response.data else []

    return templates.TemplateResponse(request=request, name="mission.html", context={
        "request": request,
        "patient": patient,
        "missions": missions
    })

@router.get("/profile")
async def showProfile(request: Request, resp=Depends(check_patient_role)):
    if isinstance(resp, RedirectResponse):
        return resp

    user_id = request.cookies.get("user_id")
    history = []
    lesson_scores = {}

    if user_id:
        response3 = supabase.table("history_assignmenteachday_patient_templatecontents") \
            .select("*") \
            .eq("patientid", user_id) \
            .eq("isdone", True) \
            .execute()
        history = response3.data

        ahids = list({h["ahid"] for h in history if h.get("ahid") is not None})

        ahid_to_name = {}
        if ahids:
            response2 = supabase.table("assignmentforanotherpage") \
                .select("ahid,activityname") \
                .in_("ahid", ahids) \
                .execute()
            ahid_to_name = {item["ahid"]: item["activityname"] for item in response2.data}

        for h in history:
            h["activityname"] = ahid_to_name.get(h["ahid"], "ไม่ทราบชื่อแบบฝึก")

        for row in history:
            ahid = row.get("ahid")
            retries = row.get("retries", {})
            retry_count = sum(retries.values())
            score = max(0, 100 - retry_count * 10)

            if ahid is not None:
                lesson_scores.setdefault(ahid, []).append(score)

        avg_by_name = {
            ahid_to_name.get(ahid, f"แบบฝึก {ahid}"): round(sum(scores) / len(scores), 2)
            for ahid, scores in lesson_scores.items()
        }

        lesson_names = list(avg_by_name.keys())
        avg_scores = list(avg_by_name.values())

        return templates.TemplateResponse(request=request, name="profile_patient.html", context={
            "request": request,
            "user_data": history,
            "chart_labels": lesson_names,
            "chart_data": avg_scores
        })



@router.get("/lesson/{assignment_id}")
async def showLession(assignment_id: int, request: Request, resp=Depends(check_patient_role)):
    if isinstance(resp, RedirectResponse):
        return resp

    # Get assignments
    assignment_res = supabase.table("home_assignmentdescription").select("*").eq("assignmentid", assignment_id).execute()
    if not assignment_res.data:
        raise HTTPException(status_code=404, detail="No assignment descriptions found")
    assignments = assignment_res.data

    # Create lesson list
    lessons = []

    for a in assignments:
        template_res = supabase.table("templates").select("*").eq("templateid", a["templateid"]).execute()
        if not template_res.data:
            continue
        template = template_res.data[0]


        activity_res = supabase.table("activities").select("*").eq("activityid", template["activityid"]).execute()
        if not activity_res.data:
            continue
        activity = activity_res.data[0]


        lessons.append({
            "assignment": a,
            "template": template,
            "activity": activity
        })

    print(lessons)

    # ✅ Create response from TemplateResponse
    response = templates.TemplateResponse(request=request, name="each_lesson.html", context={
        "request": request,
        "lessons": lessons
    })
    return response

@router.get("/activity/{activity_id}")
async def showActivity(
    activity_id: int,
    request: Request,
    assignment_id: int = Query(...),
    templateid: int = Query(...),
    resp=Depends(check_patient_role)
):
    if isinstance(resp, RedirectResponse):
        return resp

    tc_contents = []
    story_data = {}
    if activity_id:
        tc_view_res = supabase.table("tc_view").select("*").eq("activityid", activity_id).eq("assignmentid", assignment_id).execute()
        tc_contents = tc_view_res.data if tc_view_res.data else []

        if tc_contents:
            raw_sentence = tc_contents[0]["sentence"]
            try:
                story_data = json.loads(raw_sentence)
            except Exception as e:
                print("❌ Error parsing sentence JSON:", e)

    file_list = {
        1: "les_listen_speak2.html",
        2: "les_listen_speak.html",
        3: "les_speak_similar.html",
        4: "les_short_story.html",
        5: "les_thinkpic.html",
        6: "les_listen_speak3.html",
        8: "les_seq.html"
    }

    print("tc_contents : ", tc_contents)
    print("story_data : ", story_data)

    return templates.TemplateResponse(request=request, name=file_list[activity_id], context={
        "request": request,
        "story_data": story_data,
        "tc_contents": tc_contents,
        "assignment_id": assignment_id
    })


# if 0 = GPU, if can't use GPU, use CPU
device = 0 if torch.cuda.is_available() else "cpu" 
asr = pipeline(
    task="automatic-speech-recognition",
    model="biodatlab/whisper-th-medium-combined",
    chunk_length_s=30,
    device=device
)

async def run_asr(wav_path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: asr(wav_path, generate_kwargs={"language": "<|th|>", "task": "transcribe"}))

@router.post("/transcribe/")
async def transcribe(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_webm:
        temp_webm.write(await file.read())
        webm_path = temp_webm.name

    wav_path = webm_path.replace(".webm", ".wav")
    subprocess.run(["ffmpeg", "-i", webm_path, "-ar", "16000", "-ac", "1", wav_path], check=True)

    try:
        # Timeout ASR after 15 seconds
        result = await asyncio.wait_for(run_asr(wav_path), timeout=30)#เปลี่ยน timeout หน่วยเป็นวินาที
        text = result.get("text", "").strip()
        print(f"Transcription result: {text}")
        if len(text) > 50:
            return {"text": "เราได้ยินไม่ชัด ลองพูดใหม่ดูนะ"}
    except asyncio.TimeoutError:
        print("ASR process timed out.")
        return {"text": "เราได้ยินไม่ชัด ลองพูดใหม่ดูนะ"}

    finally:
        if os.path.exists(webm_path):
            os.remove(webm_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

    return {"text": text}


@router.post("/check_answer/")
async def check_answer(request: Request):
    data = await request.json()
    answer = data.get("answer", "").strip().lower().replace(" ", "").replace("ไหม้", "ไม่")
    word = data.get("word", "").strip().lower()
    print(f"🔍 Checking: '{answer}' vs '{word}'")
    isCorrect = word in answer
    

    if isCorrect:
        return JSONResponse(status_code=200, content={"message": "Correct"})
    else:
        raise HTTPException(status_code=400, detail="Incorrect")

class FinishRequest(BaseModel):
    completed: bool
    wrong_summary: Dict[str, int]
    activityid: int
    templateid: int
    assignmentid: int

@router.post("/finish/")
async def finish_task(data: FinishRequest, request: Request):
    # Process summary here (store in DB, mark as done, etc.)
    print("Patient finished:", data.completed)
    print("Wrong attempts:", data.wrong_summary)
    print("Activity ID:", data.activityid)
    print("templateid ID:", data.templateid)
    print("Assignment ID:", data.assignmentid)

    userId = 2#request.cookies.get("user_id")

    ahid_result = supabase.table("assignmenteachday").select("ahid").eq("templateid", data.templateid).eq("assignmentid", data.assignmentid).execute()
    print("ahid:", ahid_result.data[0]["ahid"])
    ahid_value = ahid_result.data[0]["ahid"]
    if ahid_result:
        insert_result = supabase.table("histories").insert({
            "ahid": ahid_value,
            "retries": data.wrong_summary,
            "patientid": userId,
        }).execute()

    update_result = supabase.table("assignmenteachday").update({
        "isdone": True
    }).eq("ahid", ahid_value).execute()

    return {"status": "success"}


@router.get("/timer/")
async def timer(request: Request):
    return templates.TemplateResponse(request=request, name="timer.html", context={"request": request})