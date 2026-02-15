import os
import pandas as pd
import calendar
from datetime import date as dt_date, datetime
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import urllib.parse
import json

app = FastAPI()

# --- CONFIGURATION ---
# Use /tmp for Vercel writable access (ephemeral)
BOOKINGS_FILE = "/tmp/bookings.csv" if os.environ.get("VERCEL") else "bookings.csv"
ADMIN_TEAM = ["admin1@spjimr.org", "admin2@spjimr.org", "dean_office@spjimr.org"]
VENUES = [
    "MLS Auditorium", 
    "Gyan Auditorium", 
    "Yoga Room", 
    "Recess Area near Acad Block", 
    "Other (Manual Entry)"
]
TIME_SLOTS = [
    "08:00 AM - 10:00 AM", "10:00 AM - 12:00 PM",
    "12:00 PM - 02:00 PM", "02:00 PM - 04:00 PM",
    "04:00 PM - 06:00 PM", "06:00 PM - 08:00 PM",
    "08:00 PM - 10:00 PM", "10:00 PM - 12:00 AM"
]

# --- SETUP ---
templates = Jinja2Templates(directory="templates")
if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- DATA LAYER ---
def init_db():
    if not os.path.exists(BOOKINGS_FILE):
        try:
            df = pd.DataFrame(columns=["Venue", "Date", "Time_Slot", "Requested_By"])
            df.to_csv(BOOKINGS_FILE, index=False)
        except Exception as e:
            print(f"Init error: {e}")

def load_bookings():
    init_db()
    try:
        if os.path.exists(BOOKINGS_FILE) and os.path.getsize(BOOKINGS_FILE) > 0:
            df = pd.read_csv(BOOKINGS_FILE)
            return df.sort_values(by="Date", ascending=False)
        return pd.DataFrame(columns=["Venue", "Date", "Time_Slot", "Requested_By"])
    except Exception as e:
        print(f"Load error: {e}")
        return pd.DataFrame(columns=["Venue", "Date", "Time_Slot", "Requested_By"])

def save_booking(venue, date, time_slot, requested_by):
    try:
        df = load_bookings()
        new_row = {
            "Venue": venue, 
            "Date": date, 
            "Time_Slot": time_slot, 
            "Requested_By": requested_by
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(BOOKINGS_FILE, index=False)
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    df = load_bookings()
    bookings_list = df.to_dict('records')
    
    today = dt_date.today()
    month = today.month
    year = today.year
    
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Identify booked days for this month
    booked_days = []
    if not df.empty:
        try:
            df['Date_obj'] = pd.to_datetime(df['Date'], errors='coerce')
            current_month_bookings = df[
                (df['Date_obj'].dt.month == month) & 
                (df['Date_obj'].dt.year == year)
            ]
            booked_days = current_month_bookings['Date_obj'].dt.day.dropna().unique().tolist()
        except:
            booked_days = []

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "venues": VENUES,
        "time_slots": TIME_SLOTS,
        "bookings": bookings_list,
        "month_name": month_name,
        "year": year,
        "calendar": cal,
        "today": today.day,
        "booked_days": booked_days,
        "admin_team": ", ".join(ADMIN_TEAM)
    })

@app.post("/book")
async def book(
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
async def delete_booking_route(index: int):
    df = load_bookings()
    if 0 <= index < len(df):
        df = df.drop(df.index[index]).reset_index(drop=True)
        df.to_csv(BOOKINGS_FILE, index=False)
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/health")
def health():
    return {"status": "ok", "vercel": os.environ.get("VERCEL", False)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
