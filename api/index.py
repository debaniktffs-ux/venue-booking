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
if os.environ.get("VERCEL"):
    BOOKINGS_FILE = "/tmp/bookings.csv"
    if not os.path.exists("/tmp"):
        os.makedirs("/tmp", exist_ok=True)
else:
    BOOKINGS_FILE = "bookings.csv"

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase init error: {e}")

CATEGORIES = {
    "sports": {
        "title": "Sports Hub",
        "description": "Rec Centre & Outdoor Courts",
        "accent": "orange",
        "venues": [
            "Rec Centre - 1st Floor", "Rec Centre - Squash Court 1", "Rec Centre - Squash Court 2",
            "Rec Centre - Yoga Room", "Rec Centre - Table Tennis Table1", "Rec Centre - Table Tennis Table2",
            "Rec Centre - Table Tennis Table3", "Rec Centre - Pool Table", "Rec Centre - Terrace (Pickleball)",
            "Rec Centre - Terrace (Cricket)", "AH Wadia School (Basketball)", "B30 Volleyball Court",
            "Other (Manual Entry)"
        ],
        "draft_label": "Whatsapp Game Invite",
        "draft_type": "whatsapp"
    },
    "cultural": {
        "title": "Cultural Hub",
        "description": "Auditoriums & Event Spaces",
        "accent": "purple",
        "venues": [
            "MLS Auditorium", "Gyan Auditorium", "Yoga Room", 
            "Recess Area near Acad Block", "Other (Manual Entry)"
        ],
        "draft_label": "Email Approval Draft",
        "draft_type": "email"
    },
    "academic": {
        "title": "Academic Hub",
        "description": "NCR Rooms & PD Blocks",
        "accent": "blue",
        "venues": [
            "B Block - Room 101", "B Block - Room 102",
            "C Block - Room 201", "C Block - Room 202", "D Block - Room 301", "D Block - Room 302",
            "Dome 1", "Dome 2", "Dome 3", "NCR 1", "NCR 2", "NCR 3", "NCR 4", "NCR 5",
            "NCR 6", "NCR 7", "NCR 8", "Other (Manual Entry)"
        ],
        "types": ["Class Adda", "PD Club Session"],
        "draft_label": "Email Approval Draft",
        "draft_type": "email"
    }
}

TIME_SLOTS = [
    "08:00 AM - 10:00 AM", "10:00 AM - 12:00 PM",
    "12:00 PM - 02:00 PM", "02:00 PM - 04:00 PM",
    "04:00 PM - 06:00 PM", "06:00 PM - 08:00 PM",
    "08:00 PM - 10:00 PM", "10:00 PM - 12:00 AM"
]

# --- HOLIDAY CONFIG ---
GOVT_HOLIDAYS = {
    "2026-01-26": "Republic Day",
    "2026-03-04": "Holi (University Holiday)",
    "2026-03-27": "Eid-ul-Fitr",
    "2026-04-10": "Good Friday",
    "2026-08-15": "Independence Day",
    "2026-10-02": "Gandhi Jayanti",
    "2026-10-21": "Dussehra",
    "2026-11-08": "Diwali (Break)",
}

# --- SETUP ---
templates = Jinja2Templates(directory="templates")
if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- DATA LAYER ---
def init_db():
    if not os.path.exists(BOOKINGS_FILE):
        try:
            df = pd.DataFrame(columns=["Category", "Type", "Venue", "Date", "Time_Slot", "Requested_By"])
            df.to_csv(BOOKINGS_FILE, index=False)
        except Exception as e:
            print(f"Init error: {e}")

def load_bookings(category: Optional[str] = None):
    init_db()
    try:
        if supabase:
            query = supabase.table("bookings").select("*")
            if category:
                query = query.eq("Category", category)
            response = query.execute()
            df = pd.DataFrame(response.data)
        else:
            if os.path.exists(BOOKINGS_FILE) and os.path.getsize(BOOKINGS_FILE) > 0:
                df = pd.read_csv(BOOKINGS_FILE)
                if category:
                    df = df[df["Category"] == category]
            else:
                df = pd.DataFrame(columns=["Category", "Type", "Venue", "Date", "Time_Slot", "Requested_By"])
        
        if "Type" not in df.columns:
            df["Type"] = ""
            
        return df.sort_values(by="Date", ascending=False)
    except Exception as e:
        print(f"Load error: {e}")
        return pd.DataFrame(columns=["Category", "Type", "Venue", "Date", "Time_Slot", "Requested_By"])

def save_booking_data(category, type_val, venue, date, time_slot, requested_by):
    if supabase:
        data = {"Category": category, "Type": type_val, "Venue": venue, "Date": date, "Time_Slot": time_slot, "Requested_By": requested_by}
        supabase.table("bookings").insert(data).execute()
    else:
        df = load_bookings()
        new_row = {"Category": category, "Type": type_val, "Venue": venue, "Date": date, "Time_Slot": time_slot, "Requested_By": requested_by}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(BOOKINGS_FILE, index=False)

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    try:
        df = load_bookings()
        today = dt_date.today()
        cal = calendar.monthcalendar(today.year, today.month)
        
        bookings_by_day = {}
        if not df.empty:
            df['Date_obj'] = pd.to_datetime(df['Date'], errors='coerce')
            current_month = df[df['Date_obj'].dt.month == today.month]
            
            for _, row in current_month.iterrows():
                if pd.isna(row['Date_obj']): continue
                d = int(row['Date_obj'].day)
                if d not in bookings_by_day:
                    bookings_by_day[d] = []
                
                bookings_by_day[d].append({
                    "Category": row['Category'],
                    "Venue": row['Venue'],
                    "Time_Slot": row['Time_Slot'],
                    "Requested_By": row['Requested_By'],
                    "Type": row.get('Type', '')
                })

        return templates.TemplateResponse("landing.html", {
            "request": request,
            "calendar": cal,
            "month_name": calendar.month_name[today.month],
            "month": today.month,
            "year": today.year,
            "today": today.day,
            "bookings_by_day": bookings_by_day,
            "holidays": GOVT_HOLIDAYS
        })
    except Exception as e:
        import traceback
        return HTMLResponse(content=f"Error in landing route: {str(e)}<pre>{traceback.format_exc()}</pre>", status_code=500)

@app.get("/dashboard/{category}", response_class=HTMLResponse)
async def dashboard(request: Request, category: str):
    if category not in CATEGORIES:
        return RedirectResponse(url="/")
    
    cat_config = CATEGORIES[category]
    df = load_bookings(category)
    bookings_list = df.to_dict('records')
    
    today = dt_date.today()
    cal = calendar.monthcalendar(today.year, today.month)
    
    booked_days = []
    if not df.empty:
        try:
            df['Date_obj'] = pd.to_datetime(df['Date'], errors='coerce')
            booked_days = df[df['Date_obj'].dt.month == today.month]['Date_obj'].dt.day.dropna().astype(int).unique().tolist()
        except: pass

    draft = ""
    if bookings_list:
        latest = bookings_list[0]
        prefix = f"[{latest.get('Type', '')}] " if latest.get('Type') else ""
        if cat_config["draft_type"] == "whatsapp":
            draft = f"Hey everyone! ⚽ I've reserved {latest['Venue']} for a game on {latest['Date']} ({latest['Time_Slot']}). Join in!"
        else:
            draft = f"Subject: Venue Reservation Request - {prefix}{latest['Venue']}\n\nDear Admin Team,\n\nI would like to request a reservation for {latest['Venue']} on {latest['Date']} for the slot {latest['Time_Slot']}.\n\nRequested By: {latest['Requested_By']}\n\nBest regards,\n{latest['Requested_By']}"

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "category": category,
        "config": cat_config,
        "venues": cat_config["venues"],
        "types": cat_config.get("types", []),
        "time_slots": TIME_SLOTS,
        "bookings": bookings_list,
        "calendar": cal,
        "month_name": calendar.month_name[today.month],
        "year": today.year,
        "today": today.day,
        "booked_days": booked_days,
        "draft": draft
    })

@app.post("/book/{category}")
async def book(
    category: str,
    booking_type: str = Form(None),
    venue: str = Form(...),
    manual_venue: str = Form(None),
    date: str = Form(...),
    time_slot: str = Form(...),
    requested_by: str = Form(...)
):
    final_venue = manual_venue if venue == "Other (Manual Entry)" and manual_venue else venue
    
    if category == "sports":
        booking_date = datetime.strptime(date, "%Y-%m-%d").date()
        if booking_date.weekday() == 0:
            if "Rec Centre" in final_venue or "Yoga Room" in final_venue:
                error_msg = f"Rec Centre is closed on Mondays (Venue: {final_venue})"
                return RedirectResponse(url=f"/dashboard/{category}?error={urllib.parse.quote(error_msg)}", status_code=303)

    df = load_bookings()
    if not df.empty:
        conflict = df[(df['Venue'] == final_venue) & (df['Date'] == date) & (df['Time_Slot'] == time_slot)]
        if not conflict.empty:
            return RedirectResponse(url=f"/dashboard/{category}?error=Conflict: {final_venue} is already reserved.", status_code=303)

    save_booking_data(category, booking_type, final_venue, date, time_slot, requested_by)
    return RedirectResponse(url=f"/dashboard/{category}", status_code=303)

@app.post("/delete/{category}/{index}")
async def delete(category: str, index: int):
    df_all = load_bookings()
    df_cat = df_all[df_all["Category"] == category]
    
    if 0 <= index < len(df_cat):
        actual_index = df_cat.index[index]
        df_all = df_all.drop(actual_index).reset_index(drop=True)
        df_all.to_csv(BOOKINGS_FILE, index=False)
        
    return RedirectResponse(url=f"/dashboard/{category}", status_code=303)

@app.get("/api/health")
def health():
    return {"status": "ok", "vercel": os.environ.get("VERCEL", False)}
