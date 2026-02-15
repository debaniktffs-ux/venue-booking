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

import holidays

# --- CONFIGURATION ---
IND_HOLIDAYS = holidays.India(years=[2026])
GOVT_HOLIDAYS = {date.strftime("%Y-%m-%d"): name for date, name in IND_HOLIDAYS.items()}

# Add local university holidays if needed
GOVT_HOLIDAYS.update({
    "2026-03-04": "Holi (University Holiday)",
    "2026-11-08": "Diwali (Break)",
})

# --- DATA LAYER ---
# (Skipping init_db, load_bookings, save_booking_data as they are mostly unchanged)

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    df = load_bookings()
    today = dt_date.today()
    cal = calendar.monthcalendar(today.year, today.month)
    
    # Detailed booking mapping for interactive calendar
    bookings_by_day = {}
    if not df.empty:
        df['Date_obj'] = pd.to_datetime(df['Date'], errors='coerce')
        current_month = df[df['Date_obj'].dt.month == today.month]
        
        for _, row in current_month.iterrows():
            d = row['Date_obj'].day
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
        "year": today.year,
        "today": today.day,
        "bookings_by_day": bookings_by_day,
        "holidays": GOVT_HOLIDAYS
    })

# ... dashboard route ...

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
    
    # Monday Closure Logic (Sports Hub)
    if category == "sports":
        booking_date = datetime.strptime(date, "%Y-%m-%d").date()
        if booking_date.weekday() == 0:  # Monday is 0
            if "Rec Centre" in final_venue or "Yoga Room" in final_venue:
                error_msg = f"Rec Centre is closed on Mondays (Venue: {final_venue})"
                return RedirectResponse(url=f"/dashboard/{category}?error={urllib.parse.quote(error_msg)}", status_code=303)

    # Conflict Check
    df = load_bookings()
    if not df.empty:
        conflict = df[(df['Venue'] == final_venue) & (df['Date'] == date) & (df['Time_Slot'] == time_slot)]
        if not conflict.empty:
            return RedirectResponse(url=f"/dashboard/{category}?error=Conflict: {final_venue} is already reserved.", status_code=303)

    save_booking_data(category, booking_type, final_venue, date, time_slot, requested_by)
    return RedirectResponse(url=f"/dashboard/{category}", status_code=303)

@app.post("/delete/{category}/{index}")
async def delete(category: str, index: int):
    # Fetch filtered bookings to get the correct absolute index
    df_all = load_bookings()
    df_cat = df_all[df_all["Category"] == category]
    
    if 0 <= index < len(df_cat):
        actual_index = df_cat.index[index]
        df_all = df_all.drop(actual_index).reset_index(drop=True)
        df_all.to_csv(BOOKINGS_FILE, index=False)
        
    return RedirectResponse(url=f"/dashboard/{category}", status_code=303)

@app.get("/api/seed")
async def seed_data():
    import random
    from datetime import timedelta
    
    # Names for randomization
    names = ["Spin Club", "Dance Society", "Tech Hub", "MBA Batch A", "PGP Team", "Cricket XIX", "Admin", "Dean Office", "Music Club"]
    
    # Start date around current month
    start_date = dt_date(2026, 2, 1)
    
    for _ in range(200):
        cat_id = random.choice(list(CATEGORIES.keys()))
        cat_conf = CATEGORIES[cat_id]
        
        venue = random.choice(cat_conf["venues"])
        # Avoid manual entry for seed
        if venue == "Other (Manual Entry)":
            venue = cat_conf["venues"][0]
            
        b_type = random.choice(cat_conf.get("types", ["General"])) if cat_conf.get("types") else ""
        
        # Random date in Feb or March
        random_days = random.randint(0, 50)
        curr_date = (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")
        
        slot = random.choice(TIME_SLOTS)
        requester = random.choice(names)
        
        # Check conflict before seeding to keep it clean (optional for seed but good practice)
        save_booking_data(cat_id, b_type, venue, curr_date, slot, requester)
        
    return {"status": "success", "message": "200 test entries created across all categories"}

@app.get("/api/health")
def health():
    return {"status": "ok", "vercel": os.environ.get("VERCEL", False)}
