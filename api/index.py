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
from supabase import create_client, Client

app = FastAPI()

# --- CONFIGURATION ---
# Use /tmp for Vercel writable access (ephemeral)
if os.environ.get("VERCEL"):
    BOOKINGS_FILE = "/tmp/bookings.csv"
    # Ensure /tmp is actually used correctly
    if not os.path.exists("/tmp"):
        os.makedirs("/tmp", exist_ok=True)
else:
    BOOKINGS_FILE = "bookings.csv"

# Supabase Setup (Optional)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase init error: {e}")

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
    # Priority 1: Supabase
    if supabase:
        try:
            response = supabase.table("bookings").select("*").execute()
            df = pd.DataFrame(response.data)
            if not df.empty:
                return df.sort_values(by="Date", ascending=False)
            return pd.DataFrame(columns=["Venue", "Date", "Time_Slot", "Requested_By"])
        except Exception as e:
            print(f"Supabase load error: {e}")

    # Priority 2: Local CSV
    init_db()
    try:
        if os.path.exists(BOOKINGS_FILE) and os.path.getsize(BOOKINGS_FILE) > 0:
            df = pd.read_csv(BOOKINGS_FILE)
            return df.sort_values(by="Date", ascending=False)
        return pd.DataFrame(columns=["Venue", "Date", "Time_Slot", "Requested_By"])
    except Exception as e:
        print(f"Load error: {e}")
        return pd.DataFrame(columns=["Venue", "Date", "Time_Slot", "Requested_By"])

def save_booking_data(venue, date, time_slot, requested_by):
    # Priority 1: Supabase
    if supabase:
        try:
            data = {
                "Venue": venue, 
                "Date": date, 
                "Time_Slot": time_slot, 
                "Requested_By": requested_by
            }
            supabase.table("bookings").insert(data).execute()
            return True
        except Exception as e:
            print(f"Supabase save error: {e}")

    # Priority 2: Local CSV
    try:
        df = load_bookings()
        new_row = {
            "Venue": venue, 
            "Date": date, 
            "Time_Slot": time_slot, 
            "Requested_By": requested_by
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        # Force write to /tmp for Vercel
        df.to_csv(BOOKINGS_FILE, index=False)
        return True
    except Exception as e:
        print(f"Save error: {e}")
        raise e

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

    # Get latest booking for mail template
    latest_booking = bookings_list[0] if bookings_list else None
    mail_template = ""
    if latest_booking:
        mail_template = f"Subject: Venue Reservation Request - {latest_booking['Venue']}\n\nDear Admin Team,\n\nI would like to request a reservation for {latest_booking['Venue']} on {latest_booking['Date']} for the slot {latest_booking['Time_Slot']}.\n\nRequested By: {latest_booking['Requested_By']}\n\nBest regards,\n{latest_booking['Requested_By']}"

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
        "admin_team": ", ".join(ADMIN_TEAM),
        "mail_template": mail_template
    })

@app.post("/book")
async def book(
    venue: str = Form(...),
    manual_venue: str = Form(None),
    date: str = Form(...),
    time_slot: str = Form(...),
    requested_by: str = Form(...)
):
    final_venue = manual_venue if venue == "Other (Manual Entry)" and manual_venue else venue
    
    # Conflict Check
    df = load_bookings()
    if not df.empty:
        conflict = df[
            (df['Venue'] == final_venue) & 
            (df['Date'] == date) & 
            (df['Time_Slot'] == time_slot)
        ]
        if not conflict.empty:
            error_msg = f"Conflict: {final_venue} is already reserved for {date} at {time_slot}."
            return RedirectResponse(url=f"/?error={urllib.parse.quote(error_msg)}", status_code=303)

    try:
        save_booking_data(final_venue, date, time_slot, requested_by)
    except Exception as e:
        return RedirectResponse(url=f"/?error={urllib.parse.quote(str(e))}", status_code=303)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete/{index}")
async def delete_booking_route(index: int):
    # This is trickier with Supabase, ideally we'd use an ID. 
    # For now, we'll fetch all, drop, and overwrite (if using CSV) 
    # or implement proper delete if we add IDs to the table.
    
    df = load_bookings()
    if 0 <= index < len(df):
        try:
            if supabase:
                # Need an identifier. For now, we'll use a simple match (risky, but works for E2E)
                target = df.iloc[index]
                supabase.table("bookings").delete().match({
                    "Venue": target["Venue"],
                    "Date": target["Date"],
                    "Time_Slot": target["Time_Slot"]
                }).execute()
            else:
                df = df.drop(df.index[index]).reset_index(drop=True)
                df.to_csv(BOOKINGS_FILE, index=False)
        except Exception as e:
            return RedirectResponse(url=f"/?error={urllib.parse.quote(str(e))}", status_code=333)
            
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/health")
def health():
    return {"status": "ok", "vercel": os.environ.get("VERCEL", False), "supabase": bool(supabase)}
