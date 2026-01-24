# ==============================================================================
# SSS G-ABAY v2.0 - BRANCH OPERATING SYSTEM
# "World-Class Service, Zero-Install Architecture"
# COPYRIGHT: © 2026 rpt/sssgingoog
# ==============================================================================

import streamlit as st
import pandas as pd
import datetime
import time
import uuid
import qrcode
from io import BytesIO

# ==========================================
# 1. SYSTEM CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="SSS G-ABAY v2.0", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

# CSS: GLASSMORPHISM, HIGH CONTRAST, & TV MODE HACKS
st.markdown("""
<style>
    /* Global Watermark */
    .watermark {
        position: fixed; bottom: 10px; right: 10px;
        color: rgba(0,0,0,0.3); font-size: 12px; font-family: monospace;
        z-index: 9999; pointer-events: none;
    }
    
    /* Hide Streamlit UI elements for Kiosk feel */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* BIG BUTTON STYLES */
    div.stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    
    /* DISPLAY MODE: Hide Sidebar Completely */
    [data-testid="stSidebar"] { display: none; }
    
    /* CUSTOM CLASSES FOR CARDS */
    .ticket-card {
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        margin: 20px 0;
        border: 2px solid white;
    }
</style>
<div class="watermark">© 2026 rpt/sssgingoog | v2.0.1</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & STATE (The "Brain")
# ==========================================
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "tickets": [],
        "history": [],
        "config": {
            "branch_name": "GINGOOG BRANCH",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Social_Security_System_%28SSS%29.svg/1200px-Social_Security_System_%28SSS%29.svg.png",
            "lanes": {"E": "eCenter", "F": "Fast Lane", "C": "Counter", "T": "Teller", "A": "Employer"}
        },
        "staff": {
            "admin": {"pass": "sss2026", "role": "ADMIN", "name": "System Admin"},
            "c1": {"pass": "123", "role": "MSR", "name": "Maria Santos", "station": "Counter 1"}
        },
        "announcements": ["Welcome to SSS Gingoog. Operating Hours: 8:00 AM - 5:00 PM."]
    }

db = st.session_state['db']

# ==========================================
# 3. HELPER FUNCTIONS (Logic Core)
# ==========================================
def generate_ticket(service, lane_code, is_priority, is_appt=False):
    prefix = "A" if is_appt else ("P" if is_priority else "R")
    count = len([t for t in db["tickets"] if t["lane"] == lane_code]) + 1
    ticket_num = f"{lane_code}{prefix}-{count:03d}"
    
    new_t = {
        "id": str(uuid.uuid4()), "number": ticket_num, "lane": lane_code,
        "service": service, "type": "PRIORITY" if is_priority else "REGULAR",
        "status": "WAITING", "timestamp": datetime.datetime.now(),
        "park_timestamp": None, "history": []
    }
    db["tickets"].append(new_t)
    return new_t

def get_prio_score(t):
    # LOWER SCORE = HIGHER PRIORITY
    base = t["timestamp"].timestamp()
    bonus = 3600 if t.get("is_appt") else (2700 if t.get("is_referral") else (1800 if t["type"] == "PRIORITY" else 0))
    return base - bonus

# ==========================================
# 4. MODULES
# ==========================================

# --- MODULE A: THE KIOSK (Corrected Design) ---
def render_kiosk():
    # HEADER
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image(db["config"]["logo_url"], width=80)
        st.markdown(f"<h2 style='text-align: center; color:#0038A8; margin:0;'>SSS {db['config']['branch_name']}</h2>", unsafe_allow_html=True)

    # PAGE 1: THE GATE (Split Screen)
    if 'kiosk_step' not in st.session_state:
        st.markdown("<br>", unsafe_allow_html=True)
        col_reg, col_prio = st.columns([3, 2], gap="large")
        
        with col_reg:
            st.info("👤 STANDARD TRANSACTIONS")
            if st.button("ENTER REGULAR LANE", type="primary", use_container_width=True):
                st.session_state['is_prio'] = False
                st.session_state['kiosk_step'] = 'menu'
                st.rerun()
        
        with col_prio:
            st.warning("♿ SENIOR / PWD / PREGNANT")
            if st.button("ENTER PRIORITY LANE", use_container_width=True):
                st.session_state['is_prio'] = True
                st.session_state['kiosk_step'] = 'menu'
                st.rerun()
            st.error("⚠ WARNING: Strictly for qualified members only. Non-qualified users will be transferred.")

    # PAGE 2: MAIN MENU (Big Cards)
    elif st.session_state['kiosk_step'] == 'menu':
        st.markdown("### Select Service Category")
        m1, m2, m3 = st.columns(3)
        
        with m1:
            if st.button("💳 PAYMENTS\n(Contrib/Loans)", type="primary", use_container_width=True):
                t = generate_ticket("Payment", "T", st.session_state['is_prio'])
                st.session_state['last_ticket'] = t; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            
        with m2:
            if st.button("💼 EMPLOYER\n(R1A / AMS)", type="primary", use_container_width=True):
                t = generate_ticket("Employer", "A", st.session_state['is_prio'])
                st.session_state['last_ticket'] = t; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            
        with m3:
            if st.button("👤 MEMBER SERVICES\n(Claims/ID/Loans)", type="primary", use_container_width=True):
                st.session_state['kiosk_step'] = 'mss'
                st.rerun()
            
        if st.button("⬅ Back"): del st.session_state['kiosk_step']; st.rerun()

    # PAGE 3: MSS SUB-MENU (Hardcoded List)
    elif st.session_state['kiosk_step'] == 'mss':
        st.markdown("### Member Services")
        g1, g2, g3, g4 = st.columns(4)
        
        with g1:
            st.error("🏥 BENEFITS")
            if st.button("Maternity/Sickness"): generate_ticket("Ben-Mat/Sick", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Retirement/Death"): st.session_state['kiosk_step'] = 'gate_rd'; st.rerun()
            
        with g2:
            st.warning("💰 LOANS")
            if st.button("Salary/Calamity"): generate_ticket("Ln-Sal/Cal", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Pension Loan"): generate_ticket("Ln-Pension", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()

        with g3:
            st.success("📝 RECORDS")
            if st.button("Simple Correction"): generate_ticket("Rec-Simple", "F", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Req. Verification"): generate_ticket("Rec-Verify", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()

        with g4:
            st.info("💻 eSERVICES")
            if st.button("My.SSS Reset"): generate_ticket("eSvc-Reset", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("SS Number"): generate_ticket("eSvc-SSNum", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()

        if st.button("⬅ Back"): st.session_state['kiosk_step'] = 'menu'; st.rerun()

    # PAGE 4: SPECIAL GATE (Retirement)
    elif st.session_state['kiosk_step'] == 'gate_rd':
        st.warning("SPECIAL CHECK: Do you have pending cases or portability issues?")
        if st.button("YES (Complex)"): generate_ticket("Ben-Ret(C)", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        if st.button("NO (Regular)"): generate_ticket("Ben-Ret(S)", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()

    # PAGE 5: TICKET DISPLAY (High Contrast Fix)
    elif st.session_state['kiosk_step'] == 'ticket':
        t = st.session_state['last_ticket']
        # COLOR LOGIC
        bg_col = "#FFD700" if t['type'] == 'PRIORITY' else "#0038A8"
        txt_col = "#0038A8" if t['type'] == 'PRIORITY' else "white"
        
        st.markdown(f"""
        <div class="ticket-card" style='background-color: {bg_col}; color: {txt_col};'>
            <h2 style='margin:0;'>YOUR NUMBER</h2>
            <h1 style='font-size: 100px; margin:0; font-weight: bold;'>{t['number']}</h1>
            <h3 style='margin:0;'>{t['service']}</h3>
            <p>Please sit and wait for the voice call.</p>
        </div>
        """, unsafe_allow_html=True)
        
        qr = qrcode.make(f"{t['number']}")
        img = BytesIO(); qr.save(img, format='PNG')
        st.image(img, width=150, caption="Scan to Track")
        
        if st.button("DONE / PRINT"):
            del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()

# --- MODULE B: DISPLAY (TV Mode) ---
def render_display():
    # CSS HACK to Hide Sidebar happens in global style above
    st.markdown(f"<h1 style='text-align: center; color: #0038A8; margin-top: -50px;'>NOW SERVING</h1>", unsafe_allow_html=True)
    
    col_q, col_v = st.columns([2, 3])
    
    with col_q:
        serving = [t for t in db["tickets"] if t["status"] == "SERVING"]
        if not serving: st.info("Waiting for counters...")
        for t in serving:
            # COLOR CODING LANES
            b_col = "#de350b" if t['lane'] == "T" else ("#0052cc" if t['lane'] == "E" else "#6554c0")
            st.markdown(f"""
            <div style='background-color: {b_col}; color: white; padding: 15px; margin-bottom: 10px; border-radius: 10px; display: flex; justify-content: space-between;'>
                <div style='font-size: 50px; font-weight: bold;'>{t['number']}</div>
                <div style='text-align: right;'>
                    <div style='font-size: 25px;'>{t.get('served_by','Counter')}</div>
                    <div style='font-size: 15px;'>{t['service']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_v:
        # VIDEO ZONE
        st.video("https://www.youtube.com/watch?v=DummyVideo") # Replace with SSS Loop
        
        # PARKED / RECALL ZONE
        parked = [t for t in db["tickets"] if t["status"] == "PARKED"]
        if parked:
            nums = ", ".join([t['number'] for t in parked])
            st.markdown(f"""
            <div style='background-color: #d32f2f; color: white; padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center; animation: flash 2s infinite;'>
                <h2 style='margin:0;'>⚠ RECALL: {nums}</h2>
                <p>Please approach counter immediately. Forfeiture in 30 mins.</p>
            </div>
            """, unsafe_allow_html=True)

    # TICKER
    txt = " | ".join(db["announcements"])
    st.markdown(f"<div style='background: #FFD700; color: black; padding: 10px; font-weight: bold;'><marquee>{txt}</marquee></div>", unsafe_allow_html=True)
    time.sleep(3)
    st.rerun()

# --- MODULE C: COUNTER & ADMIN (Unified) ---
def render_admin_panel(user):
    # SIDEBAR: Universal Access for Admin
    st.sidebar.title("👮 Staff Menu")
    
    # VISIBILITY LOGIC
    opts = ["Counter Mode", "Analytics/Admin", "Kiosk Mode", "Display Mode"]
    # If MSR, only show Counter. If Admin, show All.
    if user['role'] not in ["ADMIN", "BRANCH_HEAD"]:
        opts = ["Counter Mode"]
        
    mode = st.sidebar.radio("Select Module", opts)
    
    # 1. COUNTER MODE
    if mode == "Counter Mode":
        st.title(f"Station: {user.get('station', 'General')}")
        
        # QUEUE LOGIC
        my_lanes = ["C", "E", "F"] # Default lanes for testing
        queue = [t for t in db["tickets"] if t["status"] == "WAITING" and t["lane"] in my_lanes]
        queue.sort(key=get_prio_score)
        
        current = next((t for t in db["tickets"] if t["status"] == "SERVING" and t.get("served_by") == user['name']), None)
        
        c1, c2 = st.columns([2,1])
        with c1:
            if current:
                st.success(f"SERVING: {current['number']} - {current['service']}")
                b1, b2, b3 = st.columns(3)
                if b1.button("✅ COMPLETE"): current["status"] = "COMPLETED"; db["history"].append(current); st.rerun()
                if b2.button("🅿️ PARK"): current["status"] = "PARKED"; current["park_timestamp"] = datetime.datetime.now(); st.rerun()
                if b3.button("🔄 REFER"): current["lane"] = "T"; current["status"] = "WAITING"; current["served_by"] = None; st.rerun()
            else:
                if st.button("🔊 CALL NEXT", type="primary", use_container_width=True):
                    if queue:
                        nxt = queue[0]
                        nxt["status"] = "SERVING"
                        nxt["served_by"] = user["name"]
                        st.rerun()
                    else: st.info("Queue Empty")
                    
        with c2:
            st.metric("Waiting", len(queue))
            st.write("Up Next:")
            for t in queue[:3]: st.write(f"**{t['number']}** ({t['type']})")

    # 2. ANALYTICS / ADMIN
    elif mode == "Analytics/Admin":
        st.title("Admin Console")
        # FIXED: Explicit Tabs to prevent blank screen
        t1, t2, t3 = st.tabs(["📊 Analytics", "⚙️ Config", "📅 Appointments"])
        
        with t1:
            st.metric("Total Served Today", len(db["history"]))
            st.metric("Pending Tickets", len([t for t in db["tickets"] if t["status"] == "WAITING"]))
            
        with t2:
            st.text_input("Branch Name", value=db["config"]["branch_name"])
            if st.button("Save Config"): st.success("Saved!")
            
        with t3:
            with st.form("appt"):
                nm = st.text_input("Name")
                if st.form_submit_button("Add Appointment"):
                    generate_ticket("Appointment", "C", True, is_appt=True)
                    st.success(f"Added {nm} to top of queue.")

    elif mode == "Kiosk Mode": render_kiosk()
    elif mode == "Display Mode": render_display()

# ==========================================
# 5. MAIN ROUTER
# ==========================================
params = st.query_params
if params.get("access") == "staff":
    # LOGIN SCREEN
    if 'user' not in st.session_state:
        st.title("Staff Login")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            # Simple Auth
            acct = next((v for k,v in db["staff"].items() if v["name"] == u or k == u), None)
            if acct and acct["pass"] == p:
                st.session_state['user'] = acct
                st.rerun()
            else: st.error("Invalid")
    else:
        render_admin_panel(st.session_state['user'])
else:
    # PUBLIC ACCESS (Mobile / Kiosk)
    # Check if Mobile or Kiosk based on Sidebar Toggle (Simulated)
    # For production, we assume default is Mobile Tracker
    st.sidebar.title("Dev Tools")
    if st.sidebar.checkbox("Simulate Kiosk Mode"):
        render_kiosk()
    else:
        # MOBILE TRACKER
        st.image(db["config"]["logo_url"], width=50)
        st.markdown("### G-ABAY Mobile Tracker")
        tn = st.text_input("Enter Ticket #")
        if tn:
            t = next((x for x in db["tickets"] if x["number"] == tn), None)
            if t:
                st.info(f"Status: {t['status']}")
                if t['status'] == "WAITING":
                    pos = len([x for x in db["tickets"] if x['lane'] == t['lane'] and x['status'] == 'WAITING' and x['timestamp'] < t['timestamp']])
                    st.metric("People Ahead", pos)
            else: st.error("Not Found")
