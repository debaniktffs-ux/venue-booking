import gradio as gr
import pandas as pd
import calendar
from datetime import date as dt_date
import os
import urllib.parse

# Path to the bookings file
BOOKINGS_FILE = "bookings.csv"

# Admin team list
ADMIN_TEAM = ["admin1@spjimr.org", "admin2@spjimr.org", "dean_office@spjimr.org"]

# SPJIMR Branding Colors
ORANGE = "#F37021"
PURPLE = "#512D6D"
BG_LIGHT = "#F4F7F9"
TEXT_DARK = "#2D3436"

CUSTOM_CSS = f"""
.gradio-container {{
    font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
    background-color: var(--background-fill-secondary) !important;
}}
.header-container {{
    display: flex;
    justify-content: flex-start;
    align-items: center;
    gap: 2.5rem;
    padding: 1.25rem 3rem;
    background: white !important; /* Force light background */
    border-bottom: 3px solid {PURPLE};
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    margin-bottom: 2.5rem;
}}
.title-block h1 {{
    color: {PURPLE} !important; /* Force purple title */
    font-weight: 800 !important;
    font-size: 2.2rem !important;
    margin: 0 !important;
    letter-spacing: -0.8px;
    line-height: 1.1;
}}
.title-block p {{
    color: #636E72 !important; /* Force gray subtitle */
    font-size: 0.85rem !important;
    margin: 0 !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 500;
    opacity: 0.8;
}}
.footer-text {{
    text-align: center;
    font-size: 0.75rem;
    color: var(--body-text-color-subdued);
    padding: 2rem 0;
    font-family: 'Inter', sans-serif;
}}
.dark .footer-text {{
    color: #DFE6E9 !important;
    opacity: 0.9 !important;
}}
.main-card {{
    background: var(--block-background-fill);
    padding: 2rem;
    border-radius: 8px;
    box-shadow: var(--block-shadow);
    border: 1px solid var(--border-color-primary);
    color: var(--body-text-color) !important;
}}
.sidebar-card {{
    background: var(--fill-tertiary);
    padding: 1.5rem;
    border-radius: 8px;
    border-left: 4px solid {ORANGE};
    color: var(--body-text-color) !important;
}}
.primary-button button {{
    background-color: {ORANGE} !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 4px !important;
    transition: all 0.2s ease !important;
}}
.primary-button button:hover {{
    background-color: #E6641A !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(243, 112, 33, 0.3);
}}
#gen_update_btn, #gmail_link_container, #gen_update_btn.padded, #gmail_link_container.padded {{
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    min-width: 200px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
#gen_update_btn {{
    height: 42px !important;
    min-height: 42px !important;
    font-weight: 600 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 4px !important;
    width: 100% !important;
    padding: 10px 20px !important;
    box-sizing: border-box !important;
    font-size: 14px !important;
    transition: all 0.2s ease !important;
    background-color: var(--block-background-fill) !important;
    color: {PURPLE} !important;
    border: 1px solid {PURPLE} !important;
}}
.dark #gen_update_btn {{
    color: #A29BFE !important;
    border-color: #A29BFE !important;
}}
#gen_update_btn:hover {{
    background-color: var(--fill-tertiary) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
}}
.gmail-button {{
    height: 42px !important;
    min-height: 42px !important;
    font-weight: 600 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 4px !important;
    width: 100% !important;
    padding: 10px 20px !important;
    box-sizing: border-box !important;
    font-size: 14px !important;
    transition: all 0.2s ease !important;
    background-color: #DB4437 !important;
    color: white !important;
    text-decoration: none !important;
}}
#gmail_link_container .prose, #gmail_link_container div {{
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
}}
#gmail_link_container {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
.tabs-container button[role="tab"] {{
    font-weight: 600 !important;
}}
.tabs-container button[role="tab"][aria-selected="true"] {{
    color: {PURPLE} !important;
    border-bottom-color: {PURPLE} !important;
}}
.dark .tabs-container button[role="tab"][aria-selected="true"] {{
    color: #A29BFE !important;
    border-bottom-color: #A29BFE !important;
}}

/* Calendar Specific Styles */
.calendar-widget {{
    background: var(--block-background-fill);
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid var(--border-color-primary);
    margin-bottom: 2rem;
}}
.calendar-header {{
    text-align: center;
    font-weight: bold;
    color: {PURPLE};
    padding: 0.5rem;
    border-bottom: 1px solid var(--border-color-divider);
    margin-bottom: 1rem;
}}
.dark .calendar-header {{
    color: #A29BFE;
}}
.custom-calendar-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 5px;
    text-align: center;
}}
.day-name {{
    font-size: 0.8rem;
    font-weight: bold;
    color: var(--body-text-color-subdued);
    padding-bottom: 5px;
}}
.day-cell {{
    padding: 10px;
    border-radius: 4px;
    font-size: 0.9rem;
    background: var(--fill-secondary);
    border: 1px solid var(--border-color-primary);
    position: relative;
    cursor: default;
    color: var(--body-text-color);
}}
.day-booked {{
    background: {ORANGE} !important;
    color: white !important;
    font-weight: bold;
    border: none !important;
    cursor: pointer;
}}
/* Tooltip styles */
.booking-details {{
    visibility: hidden;
    width: 200px;
    background-color: {PURPLE};
    color: #fff;
    text-align: left;
    border-radius: 6px;
    padding: 10px;
    position: absolute;
    z-index: 100;
    bottom: 125%;
    left: 50%;
    margin-left: -100px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 0.75rem;
    font-weight: normal;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    pointer-events: none;
    line-height: 1.4;
}}
.dark .booking-details {{
    background-color: #34495E;
}}
.booking-details::after {{
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: {PURPLE} transparent transparent transparent;
}}
.dark .booking-details::after {{
    border-color: #34495E transparent transparent transparent;
}}
.day-booked:hover .booking-details {{
    visibility: visible;
    opacity: 1;
}}
.detail-item {{
    border-bottom: 1px solid rgba(255,255,255,0.2);
    padding-bottom: 5px;
    margin-bottom: 5px;
}}
.detail-item:last-child {{
    border-bottom: none;
    padding-bottom: 0;
    margin-bottom: 0;
}}
.calendar-legend {{
    display: flex;
    justify-content: center;
    gap: 15px;
    margin-top: 1rem;
    font-size: 0.8rem;
    color: var(--body-text-color-subdued);
}}
.legend-item {{
    display: flex;
    align-items: center;
    gap: 5px;
}}
.legend-color {{
    width: 12px;
    height: 12px;
    border-radius: 2px;
    border: 1px solid var(--border-color-primary);
}}
.gmail-button {{
    height: 42px !important;
    min-height: 42px !important;
    font-weight: 600 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border-radius: 4px !important;
    width: 100% !important;
    padding: 10px 20px !important;
    box-sizing: border-box !important;
    font-size: 14px !important;
    transition: all 0.2s ease !important;
    background-color: #DB4437 !important;
    color: white !important;
    text-decoration: none !important;
}}
.gmail-button:hover {{
    background-color: #C53929 !important;
    box-shadow: 0 4px 8px rgba(219, 68, 55, 0.3) !important;
    transform: translateY(-1px);
}}
"""

def load_bookings():
    try:
        if os.path.exists(BOOKINGS_FILE) and os.path.getsize(BOOKINGS_FILE) > 0:
            df = pd.read_csv(BOOKINGS_FILE)
            expected_cols = ["Venue", "Date", "Time Slot", "Requested By"]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            return df[expected_cols]
        return pd.DataFrame(columns=["Venue", "Date", "Time Slot", "Requested By"])
    except Exception as e:
        print(f"Error loading bookings: {e}")
        return pd.DataFrame(columns=["Venue", "Date", "Time Slot", "Requested By"])

def generate_calendar_html(df=None):
    if df is None:
        df = load_bookings()
    
    today = dt_date.today()
    year = today.year
    month = today.month
    
    # Group bookings by day for this month
    bookings_by_day = {}
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        valid_df = df.dropna(subset=['Date'])
        month_df = valid_df[(valid_df['Date'].dt.year == year) & (valid_df['Date'].dt.month == month)]
        
        for idx, row in month_df.iterrows():
            d = row['Date'].day
            if d not in bookings_by_day:
                bookings_by_day[d] = []
            bookings_by_day[d].append(f"<b>{row['Venue']}</b><br>{row['Time Slot']}")

    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    html = f'<div class="calendar-widget">'
    html += f'<div class="calendar-header">{month_name} {year}</div>'
    html += '<div class="custom-calendar-grid">'
    
    # Day Names
    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        html += f'<div class="day-name">{day}</div>'
    
    # Day Cells
    for week in cal:
        for day in week:
            if day == 0:
                html += '<div class="day-empty"></div>'
            else:
                is_booked = day in bookings_by_day
                if is_booked:
                    details = "".join([f'<div class="detail-item">{item}</div>' for item in bookings_by_day[day]])
                    html += f'<div class="day-cell day-booked">{day}<div class="booking-details">{details}</div></div>'
                else:
                    html += f'<div class="day-cell">{day}</div>'
    
    html += '</div>'
    html += f'<div class="calendar-legend">'
    html += f'<div class="legend-item"><div class="legend-color" style="background: #F9F9F9; border: 1px solid #EEE;"></div> Available</div>'
    html += f'<div class="legend-item"><div class="legend-color" style="background: {ORANGE};"></div> reserved</div>'
    html += '</div></div>'
    
    return html

def save_booking(venue, date, time_slot, requested_by):
    if not venue or not date or not time_slot or not requested_by:
        return "Error: All fields are required to process the request.", load_bookings(), generate_mail_template(), generate_calendar_html()

    try:
        df = load_bookings()
        duplicate = df[(df["Venue"] == venue) & (df["Date"] == date) & (df["Time Slot"] == time_slot)]
        if not duplicate.empty:
            return f"Conflict: {venue} is already reserved for {date} during {time_slot}.", df, generate_mail_template(), generate_calendar_html(df)

        new_row = {"Venue": venue, "Date": date, "Time Slot": time_slot, "Requested By": requested_by}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(BOOKINGS_FILE, index=False)
        return f"Confirmed: Slot secured for {venue} on {date}.", df, generate_mail_template(), generate_calendar_html(df)
    except Exception as e:
        return f"System Error: Unable to complete booking. {str(e)}", load_bookings(), "Error generating template", generate_calendar_html()

def delete_booking(row_index):
    try:
        df = load_bookings()
        if 0 <= row_index < len(df):
            removed_venue = df.iloc[row_index]['Venue']
            removed_date = df.iloc[row_index]['Date']
            df = df.drop(df.index[row_index]).reset_index(drop=True)
            df.to_csv(BOOKINGS_FILE, index=False)
            return f"Removed: Reservation for {removed_venue} on {removed_date} has been deleted.", df, generate_calendar_html(df)
        return "Error: Invalid record selection.", df, generate_calendar_html(df)
    except Exception as e:
        return f"Error: {str(e)}", load_bookings(), generate_calendar_html()

def generate_mail_template():
    try:
        df = load_bookings()
        if df.empty:
            return "No recent bookings available. Please secure a slot to generate a template."
        latest = df.iloc[-1]
        requester = latest['Requested By']
        template = f"""Subject: Venue Reservation Request - {latest['Venue']}

Dear Admin Team,

This message serves as a formal request to reserve {latest['Venue']} for an upcoming cultural event.

Reservation Details:
- Date: {latest['Date']}
- Time Slot: {latest['Time Slot']}
- Requested By: {requester}

We kindly request you to review and approve this reservation at your earliest convenience.

Best regards,

{requester}
SPJIMR Bhavan's Campus

---
Recipients: {', '.join(ADMIN_TEAM)}
"""
        return template
    except Exception as e:
        return f"Template Error: {e}"

def get_gmail_link(template):
    if not template or "No recent bookings" in template or "Error" in template:
        return ""
    
    try:
        lines = template.split('\n')
        subject = ""
        body_lines = []
        is_body = False
        
        for line in lines:
            if line.startswith("Subject: "):
                subject = line.replace("Subject: ", "").strip()
                is_body = True
                continue
            if is_body:
                body_lines.append(line)
        
        body = "\n".join(body_lines).strip()
        params = {
            "view": "cm",
            "fs": "1",
            "su": subject,
            "body": body
        }
        query = urllib.parse.urlencode(params)
        return f"https://mail.google.com/mail/?{query}"
    except:
        return ""

def get_gmail_button_html(template):
    link = get_gmail_link(template)
    if not link:
        return ""
    return f'<a href="{link}" target="_blank" class="gmail-button">Link Gmail</a>'

def update_gmail_button(template):
    html = get_gmail_button_html(template)
    if not html:
        return gr.update(value="", visible=False)
    return gr.update(value=html, visible=True)

# UI Components
venues = ["MLS Auditorium", "Gyan Auditorium", "Yoga Room", "Recess Area near Acad Block", "Other (Manual Entry)"]
time_slots = [
    "08:00 AM - 10:00 AM",
    "10:00 AM - 12:00 PM",
    "12:00 PM - 02:00 PM",
    "02:00 PM - 04:00 PM",
    "04:00 PM - 06:00 PM",
    "06:00 PM - 08:00 PM",
    "08:00 PM - 10:00 PM",
    "10:00 PM - 12:00 AM"
]

with gr.Blocks(title="SPJIMR Venue Management") as demo:
    with gr.Row(elem_classes="header-container"):
        logo_path = os.path.join(os.path.dirname(__file__), "spjimr_logo.png")
        gr.Image(logo_path, show_label=False, container=False, width=130, interactive=False)
        with gr.Column(elem_classes="title-block"):
            gr.Markdown("# Venue Booking Portal")
            gr.Markdown("Academic Block & Cultural Events")
            
    with gr.Tabs(elem_classes="tabs-container") as tabs:
        # Booking Tab
        with gr.TabItem("Secure a Slot", id=0):
            with gr.Row(equal_height=False, variant="panel"):
                with gr.Column(scale=3, elem_classes="main-card"):
                    gr.Markdown("### Reservation Details")
                    with gr.Group():
                        venue_input = gr.Dropdown(choices=venues, label="Select Venue", value=venues[0])
                        manual_venue = gr.Textbox(label="Specify Venue Name", placeholder="Enter venue details...", visible=False)
                        date_input = gr.DateTime(label="Event Date", include_time=False, type="string")
                        time_input = gr.Dropdown(choices=time_slots, label="Time Slot", value=time_slots[0])
                        req_by_input = gr.Textbox(label="Requester Name/Club", placeholder="e.g., Dance Club Head")
                    
                    def toggle_manual(choice):
                        return gr.update(visible=(choice == "Other (Manual Entry)"))
                    
                    venue_input.change(toggle_manual, inputs=venue_input, outputs=manual_venue)
                    
                    with gr.Row():
                        submit_btn = gr.Button("Submit Reservation", variant="primary", elem_classes="primary-button")
                    
                    output_msg = gr.Markdown()
                
                with gr.Column(scale=1, elem_classes="sidebar-card"):
                    gr.Markdown("### Policy & Guidelines")
                    gr.Markdown("""
                    - **Internal Records**: This portal maintains institutional records for venue allocation.
                    - **Approval Workflow**: Once a slot is secured, a mail template is triggered. Users must send this to the requested faculty member for official approval.
                    - **Record Management**: Upon faculty approval, the record should be maintained. If the request is denied or cancelled, users are required to delete the entry from the 'Booking History'.
                    - **Submission**: Must be submitted by authorized club representatives only.
                    """)

        # History Tab
        with gr.TabItem("Booking History", id=1):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Monthly Availability Overview")
                    calendar_display = gr.HTML(value=generate_calendar_html())
                with gr.Column(scale=2, elem_classes="main-card"):
                    gr.Markdown("### Institutional Calendar Records")
                    history_table = gr.Dataframe(value=load_bookings(), interactive=False)
                    
                    with gr.Row():
                        refresh_btn = gr.Button("Refresh Records", size="sm", elem_classes="secondary-button")
                    
                    gr.Markdown("---")
                    gr.Markdown("### Manage Records")
                    with gr.Row(variant="compact"):
                        delete_index = gr.Number(label="Enter Row # to Delete (Starts from 0)", precision=0, minimum=0)
                        delete_btn = gr.Button("Delete Selected Entry", variant="stop", size="sm")
                    delete_status = gr.Markdown()

        # Mail Template Tab
        with gr.TabItem("Email Template", id=2):
            with gr.Column(elem_classes="main-card"):
                gr.Markdown("### Administrative Communication Draft")
                gr.Markdown("Use this pre-drafted message for official correspondence with the administrative team.")
                mail_output = gr.TextArea(label="Email Content", value=generate_mail_template(), interactive=False, lines=12)
                with gr.Row(elem_classes="action-button-row"):
                    refresh_mail_btn = gr.Button("Generate Update", elem_id="gen_update_btn")
                    gmail_btn_html = gr.HTML(value=get_gmail_button_html(generate_mail_template()), elem_id="gmail_link_container")

    gr.Markdown("Created by Debanik Mukherjee", elem_classes="footer-text")

    # Define interactions
    def on_submit(venue, manual, date, time, req_by):
        final_venue = manual if venue == "Other (Manual Entry)" else venue
        msg, df, mail, cal_html = save_booking(final_venue, date, time, req_by)
        return msg, df, mail, cal_html

    submit_btn.click(
        on_submit, 
        inputs=[venue_input, manual_venue, date_input, time_input, req_by_input], 
        outputs=[output_msg, history_table, mail_output, calendar_display]
    ).then(
        fn=update_gmail_button,
        inputs=mail_output,
        outputs=gmail_btn_html
    )
    
    def on_refresh():
        df = load_bookings()
        return df, generate_calendar_html(df)

    refresh_btn.click(on_refresh, outputs=[history_table, calendar_display])
    refresh_mail_btn.click(
        fn=generate_mail_template,
        outputs=mail_output
    ).then(
        fn=update_gmail_button,
        inputs=mail_output,
        outputs=gmail_btn_html
    )
    delete_btn.click(
        fn=delete_booking,
        inputs=delete_index,
        outputs=[delete_status, history_table, calendar_display]
    )

if __name__ == "__main__":
    demo.launch(
        theme=gr.themes.Default(primary_hue="orange", secondary_hue="slate"),
        css=CUSTOM_CSS
    )
else:
    # When imported (e.g. by Vercel/FastAPI), we need to ensure the app is configured
    demo.theme = gr.themes.Default(primary_hue="orange", secondary_hue="slate")
    demo.css = CUSTOM_CSS
