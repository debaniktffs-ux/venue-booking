import os
import pandas as pd
import calendar
from datetime import date as dt_date, datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import urllib.parse

app = FastAPI()

# Configuration
BOOKINGS_FILE = "/tmp/bookings.csv" if os.environ.get("VERCEL") else "bookings.csv"
ADMIN_TEAM = ["admin1@spjimr.org", "admin2@spjimr.org", "dean_office@spjimr.org"]
VENUES = ["MLS Auditorium", "Gyan Auditorium", "Yoga Room", "Recess Area near Acad Block", "Other (Manual Entry)"]
TIME_SLOTS = [
    "08:00 AM - 10:00 AM", "10:00 AM - 12:00 PM",
    "12:00 PM - 02:00 PM", "02:00 PM - 04:00 PM",
    "04:00 PM - 06:00 PM", "06:00 PM - 08:00 PM",
    "08:00 PM - 10:00 PM", "10:00 PM - 12:00 AM"
]

# Setup Templates & Static Files
templates = Jinja2Templates(directory="templates")
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

def init_db():
    if not os.path.exists(BOOKINGS_FILE):
        df = pd.DataFrame(columns=["Venue", "Date", "Time Slot", "Requested By"])
        df.to_csv(BOOKINGS_FILE, index=False)

def load_bookings():
    init_db()
    try:
        if os.path.exists(BOOKINGS_FILE) and os.path.getsize(BOOKINGS_FILE) > 0:
            df = pd.read_csv(BOOKINGS_FILE)
            return df
        return pd.DataFrame(columns=["Venue", "Date", "Time Slot", "Requested By"])
    except:
        return pd.DataFrame(columns=["Venue", "Date", "Time Slot", "Requested By"])

def save_booking(venue, date, time_slot, requested_by):
    df = load_bookings()
    new_row = {"Venue": venue, "Date": date, "Time Slot": time_slot, "Requested By": requested_by}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(BOOKINGS_FILE, index=False)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    bookings = load_bookings().to_dict('records')
    today = dt_date.today()
    cal = calendar.monthcalendar(today.year, today.month)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "venues": VENUES,
        "time_slots": TIME_SLOTS,
        "bookings": bookings,
        "month_name": calendar.month_name[today.month],
        "year": today.year,
        "calendar": cal,
        "today": today.day
    })

@app.post("/book")
async def book(
    request: Request,
    venue: str = Form(...),
    manual_venue: str = Form(None),
    date: str = Form(...),
    time_slot: str = Form(...),
    requested_by: str = Form(...)
):
    final_venue = manual_venue if venue == "Other (Manual Entry)" else venue
    save_booking(final_venue, date, time_slot, requested_by)
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete/{index}")
async def delete(index: int):
    df = load_bookings()
    if 0 <= index < len(df):
        df = df.drop(df.index[index]).reset_index(drop=True)
        df.to_csv(BOOKINGS_FILE, index=False)
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/health")
def health():
    return {"status": "ok"}
