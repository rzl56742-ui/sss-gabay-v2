# ==============================================================================
# SSS G-ABAY v2.0 - BRANCH OPERATING SYSTEM
# "World-Class Service, Zero-Install Architecture"
#
# DEVELOPER NOTE: This system uses a "Federated State" architecture.
# Data is synced live to Google Sheets (Production) or RAM (Demo Mode).
#
# COPYRIGHT: © 2026 rpt/sssgingoog
# ==============================================================================

import streamlit as st
import pandas as pd
import datetime
import time
import uuid
import qrcode
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. MASTER CONFIGURATION (The "Brain")
# ==========================================
st.set_page_config(page_title="SSS G-ABAY v2.0", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

# CSS INJECTION (The "Glassmorphism" Look + Watermark)
st.markdown("""
<style>
    /* Global Watermark */
    .watermark {
        position: fixed;
        bottom: 10px;
        right: 10px;
        color: rgba(0,0,0,0.3);
        font-size: 12px;
        font-family: monospace;
        z-index: 9999;
        pointer-events: none;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card Styles */
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #0038A8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Ticket Styles */
    .ticket-display {
        text-align: center;
        border: 2px dashed #0038A8;
        padding: 20px;
        background-color: #ffffff;
        border-radius: 15px;
    }
</style>
<div class="watermark">© 2026 rpt/sssgingoog | v2.0.1</div>
""", unsafe_allow_html=True)

# ------------------------------------------
# LOGIC MAP (Editable by Admin)
# ------------------------------------------
DEFAULT_CONFIG = {
    "branch_name": "GINGOOG BRANCH",
    "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Social_Security_System_%28SSS%29.svg/1200px-Social_Security_System_%28SSS%29.svg.png", # Placeholder
    "operating_hours": {"start": 8, "end": 17},
    "lanes": {
        "E": {"name": "eCenter", "color": "#0052cc", "desc": "Online Services"},
        "F": {"name": "Fast Lane", "color": "#00875a", "desc": "Simple Trans"},
        "C": {"name": "Counter", "color": "#6554c0", "desc": "Complex Cases"},
        "T": {"name": "Teller", "color": "#de350b", "desc": "Payments"},
        "A": {"name": "Employer", "color": "#ff991f", "desc": "AMS Desk"}
    }
}

# ------------------------------------------
# DATABASE SIMULATION (Google Sheets Placeholder)
# ------------------------------------------
@st.cache_resource
def get_database():
    return {
        "tickets": [],          # Live Queue
        "history": [],          # For Analytics
        "appointments": [],     # Future Slots
        "staff": {              # User Accounts
            "admin": {"pass": "sss2026", "role": "ADMIN", "name": "System Admin"},
            "head": {"pass": "head123", "role": "BRANCH_HEAD", "name": "Branch Head"},
            "div": {"pass": "div123", "role": "DIVISION_HEAD", "name": "Division Head"},
            "c1": {"pass": "123", "role": "MSR", "name": "Maria Santos", "station": "Counter 1"},
            "c2": {"pass": "123", "role": "TELLER", "name": "Juan Cruz", "station": "Teller 1"}
        },
        "announcements": [],    # Ticker Messages
        "config": DEFAULT_CONFIG
    }

db = get_database()

# ==========================================
# 2. HELPER ALGORITHMS
# ==========================================

def generate_ticket(service, lane_code, is_priority, is_appointment=False):
    # PREFIX LOGIC: P=Priority, R=Regular, A=Appointment
    prefix = "A" if is_appointment else ("P" if is_priority else "R")
    
    # SEQUENCE GENERATOR
    today_count = len([t for t in db["tickets"] if t["lane"] == lane_code]) + 1
    ticket_num = f"{lane_code}{prefix}-{today_count:03d}"
    
    new_ticket = {
        "id": str(uuid.uuid4()),
        "number": ticket_num,
        "lane": lane_code,
        "service": service,
        "type": "APPOINTMENT" if is_appointment else ("PRIORITY" if is_priority else "REGULAR"),
        "status": "WAITING",
        "timestamp": datetime.datetime.now(),
        "park_timestamp": None,
        "history": [],
        "rating": None
    }
    
    # GOOGLE SHEETS SYNC WOULD GO HERE
    # sheet.append_row([...])
    
    db["tickets"].append(new_ticket)
    return new_ticket

def get_priority_score(ticket):
    # WEIGHTED TIME-BASED ALGORITHM (The "Fairness" Engine)
    # Returns a "virtual timestamp". Lower is served first.
    base_time = ticket["timestamp"].timestamp()
    
    bonus = 0
    if ticket.get("is_referral"): bonus = 2700     # 45 mins bonus
    elif ticket["type"] == "PRIORITY": bonus = 1800 # 30 mins bonus
    elif ticket["type"] == "APPOINTMENT": bonus = 3600 # 60 mins bonus
    
    return base_time - bonus

def auto_park_cleanup():
    # THE KILL SWITCH (30 Mins)
    now = datetime.datetime.now()
    for t in db["tickets"]:
        if t["status"] == "PARKED" and t["park_timestamp"]:
            elapsed = (now - t["park_timestamp"]).total_seconds() / 60
            if elapsed > 30:
                t["status"] = "NO_SHOW"
                t["history"].append(f"Auto-forfeited at {now.strftime('%H:%M')}")

# ==========================================
# 3. MODULES
# ==========================================

# --- MODULE 1: THE SMART KIOSK ---
def render_kiosk():
    conf = db["config"]
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(conf["logo_url"], width=100)
        st.markdown(f"<h1 style='text-align: center; color: #0038A8;'>SSS {conf['branch_name']}</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Welcome! Please select your transaction.</p>", unsafe_allow_html=True)

    # PRIORITY TOGGLE
    is_prio = st.toggle("❤️ Priority Mode (Senior / PWD / Pregnant)", value=False)
    
    st.markdown("---")
    
    # MAIN CATEGORIES
    c1, c2, c3 = st.columns(3)
    
    # 1. PAYMENTS
    if c1.button("💳 PAYMENTS\n(Contribution / Loans)", use_container_width=True, type="primary"):
        t = generate_ticket("Payment", "T", is_prio)
        st.session_state['last_ticket'] = t
        st.rerun()
        
    # 2. EMPLOYER
    if c2.button("💼 EMPLOYER\n(R1A / AMS)", use_container_width=True, type="primary"):
        t = generate_ticket("Employer Services", "A", is_prio)
        st.session_state['last_ticket'] = t
        st.rerun()
        
    # 3. MEMBER SERVICES (Sub-Menu)
    if c3.button("👤 MEMBER SERVICES\n(Claims / ID / Loans)", use_container_width=True):
        st.session_state['kiosk_page'] = 'mss'
        st.rerun()

    # SUB-MENU LOGIC
    if st.session_state.get('kiosk_page') == 'mss':
        st.info("Select Member Service Transaction:")
        g1, g2, g3, g4 = st.columns(4)
        
        # Group A: Benefits
        with g1:
            st.markdown("### 🏥 Benefits")
            if st.button("Maternity/Sickness"): 
                generate_ticket("Sickness/Mat", "E", is_prio); st.session_state['last_ticket'] = db["tickets"][-1]; st.rerun()
            if st.button("Retirement/Death"):
                # LOGIC GATE
                st.session_state['kiosk_page'] = 'gate_retirement'
                st.rerun()
                
        # Group B: Loans
        with g2:
            st.markdown("### 💰 Loans")
            if st.button("Salary/Calamity"): 
                generate_ticket("Salary Loan", "E", is_prio); st.session_state['last_ticket'] = db["tickets"][-1]; st.rerun()
                
        # Group C: Records
        with g3:
            st.markdown("### 📝 Records")
            if st.button("Simple Correction"): 
                generate_ticket("Simple E-4", "F", is_prio); st.session_state['last_ticket'] = db["tickets"][-1]; st.rerun()
            if st.button("Req. Verification"): 
                generate_ticket("Deep Verification", "C", is_prio); st.session_state['last_ticket'] = db["tickets"][-1]; st.rerun()
                
        # Group D: eServices
        with g4:
            st.markdown("### 💻 eServices")
            if st.button("My.SSS Reset"): 
                generate_ticket("Password Reset", "E", is_prio); st.session_state['last_ticket'] = db["tickets"][-1]; st.rerun()
            if st.button("Status Inquiry"): 
                generate_ticket("Inquiry", "E", is_prio); st.session_state['last_ticket'] = db["tickets"][-1]; st.rerun()
            
            # Back Button
            if st.button("⬅ Back"):
                del st.session_state['kiosk_page']
                st.rerun()

    # LOGIC GATE: SPECIAL CASE CHECK
    if st.session_state.get('kiosk_page') == 'gate_retirement':
        st.warning("⚠ Special Check: Do you have pending cases, portability issues, or guardianship?")
        col_y, col_n = st.columns(2)
        if col_y.button("YES (Complex)"):
            generate_ticket("Retirement (Complex)", "C", is_prio)
            st.session_state['last_ticket'] = db["tickets"][-1]; del st.session_state['kiosk_page']; st.rerun()
        if col_n.button("NO (Regular)"):
            generate_ticket("Retirement (Simple)", "E", is_prio)
            st.session_state['last_ticket'] = db["tickets"][-1]; del st.session_state['kiosk_page']; st.rerun()

    # TICKET POPUP
    if 'last_ticket' in st.session_state:
        t = st.session_state['last_ticket']
        st.markdown(f"""
        <div class="ticket-display">
            <h1 style='font-size: 80px; margin:0;'>{t['number']}</h1>
            <h3>{t['service']}</h3>
            <p>Please wait for your number.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # QR Code Generation
        qr = qrcode.make(f"https://sss-gabay.streamlit.app?track={t['number']}")
        img_byte_arr = BytesIO()
        qr.save(img_byte_arr, format='PNG')
        st.image(img_byte_arr, width=150, caption="Scan to Track on Mobile")
        
        if st.button("🖨️ PRINT TICKET (Ctrl+P)"):
            st.success("Sent to Printer...")
            time.sleep(2)
            del st.session_state['last_ticket']
            st.rerun()

# --- MODULE 2: COUNTER DASHBOARD ---
def render_counter(user):
    st.sidebar.title(f"👮 {user['station']}")
    st.sidebar.write(f"Logged in: {user['name']}")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state['user'] = None
        st.rerun()
        
    # STATION CONFIG (Which lanes do I serve?)
    # Defaulting Counter to C, E, F for demo
    my_lanes = ["C", "E", "F"] if "Counter" in user['station'] else ["T"]
    
    # 1. QUEUE LOGIC
    queue = [t for t in db["tickets"] if t["lane"] in my_lanes and t["status"] == "WAITING"]
    # SORT: Weighted Time Based (The Algorithm)
    queue.sort(key=get_priority_score)
    
    # 2. ACTIVE TICKET
    current = next((t for t in db["tickets"] if t["status"] == "SERVING" and t.get("served_by") == user['name']), None)
    
    # UI ZONES
    c_main, c_info = st.columns([2, 1])
    
    with c_main:
        st.subheader("NOW SERVING")
        if current:
            st.markdown(f"""
            <div style='background-color: #d1fae5; padding: 30px; border-radius: 15px; border: 2px solid green;'>
                <h1 style='font-size: 60px;'>{current['number']}</h1>
                <h3>{current['service']}</h3>
                <p>Started: {current['history'][-1] if current['history'] else 'Just now'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_act1, col_act2, col_act3, col_act4 = st.columns(4)
            if col_act1.button("✅ COMPLETE"):
                current["status"] = "COMPLETED"
                db["history"].append(current)
                st.success("Transaction Saved!")
                st.rerun()
                
            if col_act2.button("🔄 REFER"):
                st.session_state['transfer_mode'] = True
            
            if col_act3.button("🅿️ PARK"):
                current["status"] = "PARKED"
                current["park_timestamp"] = datetime.datetime.now()
                st.warning("Client Parked. 30 min timer started.")
                st.rerun()
                
            if col_act4.button("➕ ADD TRANS."):
                st.toast("Sub-transaction logged.")
                
            # REFERRAL POPUP
            if st.session_state.get('transfer_mode'):
                with st.form("referral"):
                    target = st.selectbox("Transfer to:", ["T", "A", "C", "E"])
                    reason = st.text_input("Reason (Required)")
                    if st.form_submit_button("Confirm Transfer"):
                        current["lane"] = target
                        current["status"] = "WAITING"
                        current["is_referral"] = True
                        current["served_by"] = None
                        current["history"].append(f"Referred by {user['name']}: {reason}")
                        del st.session_state['transfer_mode']
                        st.rerun()

        else:
            st.info("Station Ready.")
            if st.button("🔊 CALL NEXT", type="primary", use_container_width=True):
                if queue:
                    nxt = queue[0]
                    nxt["status"] = "SERVING"
                    nxt["served_by"] = user["name"]
                    nxt["history"].append(f"Called by {user['name']} at {datetime.datetime.now().strftime('%H:%M')}")
                    st.rerun()
                else:
                    st.error("No tickets in queue!")

    with c_info:
        st.subheader("Branch Pulse")
        st.metric("My Queue", len(queue))
        st.write("Up Next:")
        for t in queue[:3]:
            icon = "❤️" if t['type'] == 'PRIORITY' else ("🔄" if t.get('is_referral') else "👤")
            st.write(f"**{t['number']}** {icon} ({t['service']})")

        st.markdown("---")
        st.subheader("Parked / Missed")
        parked = [t for t in db["tickets"] if t["status"] == "PARKED"]
        for p in parked:
            if st.button(f"🔊 RECALL {p['number']}"):
                p["status"] = "SERVING"
                p["served_by"] = user["name"]
                st.rerun()

# --- MODULE 3: PUBLIC DISPLAY ---
def render_display():
    st.markdown("<h1 style='text-align: center;'>NOW SERVING</h1>", unsafe_allow_html=True)
    
    # 60/40 SPLIT
    left, right = st.columns([2, 3])
    
    with left:
        serving = [t for t in db["tickets"] if t["status"] == "SERVING"]
        if serving:
            for t in serving:
                st.markdown(f"""
                <div style='background-color: #0038A8; color: white; padding: 20px; margin-bottom: 10px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center;'>
                    <div style='font-size: 60px; font-weight: bold;'>{t['number']}</div>
                    <div style='text-align: right;'>
                        <div style='font-size: 20px;'>{t.get('served_by', 'Counter')}</div>
                        <div style='font-size: 14px; opacity: 0.8;'>{t['service']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Please wait for the next number...")

    with right:
        # VIDEO ZONE (Placeholder)
        st.video("https://www.youtube.com/watch?v=DummyVideoLink") # SSS Citizen Charter
        
        # RECALL BOX (The "Red Zone")
        parked = [t for t in db["tickets"] if t["status"] == "PARKED"]
        if parked:
            nums = ", ".join([t['number'] for t in parked])
            st.markdown(f"""
            <div style='background-color: #d32f2f; color: white; padding: 20px; border-radius: 10px; margin-top: 20px; animation: flash 2s infinite;'>
                <h3>⚠ MISSED NUMBERS</h3>
                <h2 style='margin:0;'>{nums}</h2>
                <p>Please approach counter immediately. Forfeited in 30 mins.</p>
            </div>
            """, unsafe_allow_html=True)
            
    # TICKER
    msgs = " | ".join([a["text"] for a in db["announcements"]]) or "Welcome to SSS Gingoog Branch. Office Hours: 8AM - 5PM."
    st.markdown(f"<marquee style='font-size: 20px; background: #FFD700; padding: 10px;'>{msgs}</marquee>", unsafe_allow_html=True)
    
    time.sleep(5)
    st.rerun()

# --- MODULE 4: MOBILE COMPANION ---
def render_mobile():
    params = st.query_params
    track_num = params.get("track", None)
    
    st.markdown(f"<div style='text-align: center;'><img src='{db['config']['logo_url']}' width=80></div>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🎫 Tracker", "🤖 G-ABAY Chat"])
    
    with tab1:
        if not track_num:
            track_num = st.text_input("Enter Ticket Number (e.g. EP-014)")
            
        if track_num:
            ticket = next((t for t in db["tickets"] if t["number"] == track_num), None)
            if ticket:
                status_color = "green" if ticket['status'] == 'SERVING' else ("red" if ticket['status'] == 'PARKED' else "blue")
                st.markdown(f"""
                <div style='background-color: {status_color}; color: white; padding: 30px; border-radius: 20px; text-align: center;'>
                    <h1>{ticket['status']}</h1>
                    <h3>{ticket['number']}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                if ticket['status'] == 'WAITING':
                    ahead = len([t for t in db["tickets"] if t['lane'] == ticket['lane'] and t['status'] == 'WAITING' and t['timestamp'] < ticket['timestamp']])
                    est_wait = ahead * 5 # Rolling average logic would replace this '5'
                    st.metric("People Ahead", ahead)
                    st.metric("Est. Wait Time", f"{est_wait} mins")
                
                if ticket['status'] == 'PARKED':
                    st.error("URGENT: Your number was called! You have limited time to approach the counter.")
            else:
                st.warning("Ticket not found.")
                
    with tab2:
        st.write("💬 **Ask GABAY (Multilingual)**")
        user_input = st.chat_input("Ask about ID, Loans, Sched...")
        if user_input:
            st.write(f"You: {user_input}")
            # SIMPLE KEYWORD MATCHING (The "Brain")
            resp = "I'm not sure. Please ask the PACD."
            lower = user_input.lower()
            if any(x in lower for x in ["reset", "lupa", "password"]):
                resp = "To reset your **My.SSS** password, please proceed to the eCenter."
            elif any(x in lower for x in ["id", "umid", "nawala"]):
                resp = "For UMID cards, please select 'Member Records' at the Kiosk."
            
            st.info(f"GABAY: {resp}")

# --- MODULE 5: ANALYTICS & ADMIN ---
def render_admin(user):
    st.title("Admin & Analytics Console")
    
    tabs = st.tabs(["Analytics", "Config", "Staff", "Appointments"])
    
    with tabs[0]: # ANALYTICS
        if user['role'] == "DIVISION_HEAD":
            st.selectbox("Select Branch", ["Gingoog", "Cagayan", "Iligan"])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Served", len(db["history"]))
        m2.metric("Pending", len([t for t in db["tickets"] if t["status"] == "WAITING"]))
        m3.metric("Avg Wait", "14 mins")
        
        # HEATMAP SIMULATION
        st.subheader("Traffic Heatmap")
        data = pd.DataFrame({'Hour': [8,9,10,11,12], 'Volume': [10, 45, 30, 15, 5]})
        st.bar_chart(data.set_index('Hour'))
        
        if st.button("📥 Download Report (Excel)"):
            st.success("Report Generated: rpt/sssgingoog_daily.xlsx")

    with tabs[3]: # APPOINTMENTS
        st.subheader("Upload Daily Appointments")
        with st.form("appt"):
            name = st.text_input("Member Name")
            time_slot = st.time_input("Slot")
            svc = st.selectbox("Service", ["Death Claim", "Pension"])
            if st.form_submit_button("Inject Appointment"):
                generate_ticket(svc, "C", True, is_appointment=True)
                st.success(f"Appointment set for {name}")

# ==========================================
# 4. MAIN ROUTER
# ==========================================

# Check URL for "Staff Mode"
query_params = st.query_params
access_code = query_params.get("access", [None])

if access_code == "staff":
    # AUTHENTICATION SCREEN
    if 'user' not in st.session_state or not st.session_state['user']:
        st.image(db["config"]["logo_url"], width=80)
        st.title("Staff Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            # Simple check against DB
            account = next((v for k,v in db["staff"].items() if v["name"] == u or k == u), None)
            if account and account["pass"] == p:
                st.session_state['user'] = account
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        # LOGGED IN ROUTER
        user = st.session_state['user']
        if user['role'] in ["MSR", "TELLER"]:
            render_counter(user)
        elif user['role'] in ["ADMIN", "BRANCH_HEAD", "DIVISION_HEAD"]:
            mode = st.sidebar.radio("Module", ["Analytics/Admin", "Kiosk Mode", "Display Mode"])
            if mode == "Analytics/Admin": render_admin(user)
            elif mode == "Kiosk Mode": render_kiosk()
            elif mode == "Display Mode": render_display()

else:
    # PUBLIC FACING (Mobile)
    # Check if this is a Kiosk Machine or Mobile Phone
    # (For demo, we use a sidebar toggle to simulate Kiosk vs Mobile)
    mode = st.sidebar.radio("View Mode (Simulated)", ["Mobile Companion", "Kiosk (Public)"])
    if mode == "Mobile Companion":
        render_mobile()
    else:
        render_kiosk()

# AUTO-CLEANUP BACKGROUND TASK
auto_park_cleanup()
