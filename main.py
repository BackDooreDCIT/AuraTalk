from fastapi import FastAPI, Request, Form, Depends, Query
from app.routers import userRoute
from app.routers import docRoute
from fastapi.middleware import Middleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db.db import supabase #, get_user, get_db
from passlib.context import CryptContext
import jwt, os
from io import BytesIO
from fastapi.responses import StreamingResponse
import requests
# from db import get_user
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, JSONResponse

# middleware=[Middleware(AuthMiddleware)]
app = FastAPI()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.include_router(userRoute.router, prefix="/patient")
app.include_router(docRoute.router, prefix="/slp")

app.mount("/static", StaticFiles(directory="static"), name="static")

# SET FOR VAJA API
API_KEY = os.getenv("API_VAJA")
SPEAKER = "farah"

# from app.db import models, schemas, crud
# from app.db.db import engine, get_db
# from sqlalchemy.orm import Session

# @app.get("/kuy", response_model=list[schemas.Patient])
# def read_patients(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
#     patients = crud.get_patients(db, skip=skip, limit=limit)
#     return patients

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request=request, name="disclaimer.html")

# ^ from noeysod
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(request=request, name="testlogin.html")

# ^ from noeysod
@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    # & just for checking


    #! ยังไม่ hash password เก่าเลยยังไม่ใส่เดียวพัง
    # hashed_pw = hash_password(password)
    # slp_response = supabase.table("slp").select("*").eq("slpusername", username).eq("slppassword", hashed_pw).execute()

    # print(f"😭😭😭 Username: {username}, Password: {password}, hashed password: {hashed_pw}")
    #! ------------------------------------

    slp_response = supabase.table("slp").select("*").eq("slpusername", username).execute()
    slp_users = slp_response.data

    if slp_users:
        user = slp_users[0]
        hashed_pw = user["slppassword"]

        # 👉 Use verify to compare input password with stored hash
        if pwd_context.verify(password, hashed_pw):
            user_id = user["slpid"]
            res = RedirectResponse(url="/slp/", status_code=302)
            res.set_cookie(key="user_id", value=str(user_id))
            res.set_cookie(key="role", value="slp")
            return res

    # If not an SLP, check as patient
    patient_response = supabase.table("patients").select("*").eq("pusername", username).execute()
    patient_users = patient_response.data

    if patient_users:
        user = patient_users[0]
        hashed_pw = user["ppassword"]

        if pwd_context.verify(password, hashed_pw):
            user_id = user["patientid"]
            res = RedirectResponse(url="/patient/", status_code=302)
            res.set_cookie(key="user_id", value=str(user_id))
            res.set_cookie(key="role", value="patient")
            return res

    # return PlainTextResponse("noooo try again", status_code=401)

    return templates.TemplateResponse(request=request, name="testlogin.html", context={
        "error": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
    })


@app.get("/logout")
async def logout(request: Request):
    res = RedirectResponse(url="/login", status_code=302)
    res.delete_cookie("user_id", path="/")
    res.delete_cookie("role", path="/")
    return res


@app.get("/signup")
async def showSignUp(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html")

@app.post("/signup")
async def create_user(
    request: Request,
    slpfirstname: str = Form(...),
    slplastname: str = Form(...),
    slpemail: str = Form(...),
    slpusername: str = Form(...),
    slppassword: str = Form(...),
    slphospital: str = Form(...)
):
    
    existing_user = supabase.table("slp").select("slpusername").eq("slpusername", slpusername).execute()

    if existing_user.data:
        print(f'😭😭😭 @router.post("/signup")')
        print('ไม่เข้าเว้ย')
        return templates.TemplateResponse(request=request, name="signup.html", context={
            "error": "ชื่อผู้ใช้นี้ถูกใช้ไปแล้ว กรุณาใช้ชื่ออื่น"
        })


    print('😭😭😭 /signup debug')
    print('😭 slpfirstname: ', slpfirstname)
    print('😭 slplastname: ', slplastname)
    print('😭 slpemail: ', slpemail)
    print('😭 slpusername: ', slpusername)
    print('😭 slppassword: ', slppassword)
    print('😭 slphospital: ', slphospital)

    data = {
        "slpfirstname": slpfirstname,
        "slplastname": slplastname,
        "slpemail": slpemail,
        "slpusername": slpusername,
        "slppassword": pwd_context.hash(slppassword),  # ควร hash ถ้าใช้จริง!
        "slphospital": slphospital
    }

    res = supabase.table("slp").insert(data).execute()
    print(res.data)


    return RedirectResponse(url="/login", status_code=302)

@app.post("/api/tts/")
async def get_tts(request: Request):
    data = await request.json()
    text = data.get("text", "")
    
    vaja_url = "https://api.aiforthai.in.th/vaja"
    headers = {
        "Apikey": os.getenv("API_VAJA"),
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "speaker": SPEAKER
    }

    response = requests.post(vaja_url, json=payload, headers=headers)
    result = response.json()

    audio_url = result.get("audio_url")
    return JSONResponse(content={"audio_url": audio_url})
