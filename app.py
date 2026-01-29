# ==============================================================================
# SSS G-ABAY v21.3 - BRANCH OPERATING SYSTEM (SYNC & STABILITY FIX)
# "World-Class Service, Zero-Install Architecture"
# COPYRIGHT: © 2026 rpt/sssgingoog
# ==============================================================================

import streamlit as st
import pandas as pd
import datetime
import time
import uuid
import json
import os

# ==========================================
# 1. SYSTEM CONFIGURATION & PERSISTENCE
# ==========================================
st.set_page_config(page_title="SSS G-ABAY v21.3", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

DATA_FILE = "sss_data.json"

# --- DEFAULT DATA ---
DEFAULT_DATA = {
    "tickets": [],
    "history": [],
    "breaks": [],
    "reviews": [],
    "knowledge_base": [
        {"topic": "Office Hours", "content": "We are open Monday to Friday, 8:00 AM to 5:00 PM."}
    ],
    "announcements": ["Welcome to SSS Gingoog. Operating Hours: 8:00 AM - 5:00 PM."],
    "config": {
        "branch_name": "BRANCH GINGOOG",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Social_Security_System_%28SSS%29.svg/1200px-Social_Security_System_%28SSS%29.svg.png",
        "lanes": {
            "T": {"name": "Teller", "desc": "Payments"},
            "A": {"name": "Employer", "desc": "Account Mgmt"},
            "C": {"name": "Counter", "desc": "Complex Trans"},
            "E": {"name": "eCenter", "desc": "Online Services"},
            "F": {"name": "Fast Lane", "desc": "Simple Trans"}
        },
        "assignments": {
            "Counter": ["C", "E", "F"],
            "Teller": ["T"],
            "Employer": ["A"],
            "eCenter": ["E"],
            "Help": ["F", "E"]
        },
        "counter_map": [
            {"name": "Counter 1", "type": "Counter"},
            {"name": "Counter 2", "type": "Counter"},
            {"name": "Teller 1", "type": "Teller"},
            {"name": "Teller 2", "type": "Teller"},
            {"name": "Employer Desk", "type": "Employer"},
            {"name": "eCenter", "type": "eCenter"}
        ]
    },
    "menu": {
        "Benefits": [
            ("Maternity / Sickness", "Ben-Mat/Sick", "E"),
            ("Retirement / Death / Funeral", "Ben-Ret/Death", "C"), 
            ("Disability / Unemployment", "Ben-Dis/Unemp", "E")
        ],
        "Loans": [
            ("Salary / Conso", "Ln-Sal/Conso", "E"),
            ("Calamity / Emergency", "Ln-Cal/Emerg", "E"),
            ("Pension Loan (Retiree and Survivor)", "Ln-Pension", "E")
        ],
        "Member Records Update": [
            ("Contact Information", "Rec-Contact", "F"),
            ("Simple Correction", "Rec-Simple", "F"),
            ("Complex Correction", "Rec-Complex", "C"),
            ("Request Verification", "Rec-Verify", "C")
        ],
        "eServices": [
            ("My.SSS Reset", "eSvc-Reset", "E"),
            ("SS Number", "eSvc-SSNum", "E"),
            ("Status Inquiry", "eSvc-Status", "E"),
            ("DAEM / ACOP", "eSvc-DAEM/ACOP", "E")
        ]
    },
    "staff": {
        "admin": {"pass": "sss2026", "role": "ADMIN", "name": "System Admin", "default_station": "Counter 1", "status": "ACTIVE"},
    }
}

# --- REAL-TIME DATABASE ENGINE ---
# V21.3 FIX: We do NOT rely on st.session_state for the database anymore.
# We reload from the file on every critical action to ensure all screens (TV, Kiosk, Staff) are in sync.

def load_db():
    """Forces a fresh load of the database from the disk."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                # Auto-Migration Checks
                if "breaks" not in data: data["breaks"] = []
                if "counter_map" not in data['config']: return DEFAULT_DATA 
                for uid in data['staff']:
                    if "status" not in data['staff'][uid]: data['staff'][uid]["status"] = "ACTIVE"
                return data
            except:
                return DEFAULT_DATA
    return DEFAULT_DATA

def save_db(data):
    """Commits changes immediately to the disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str)

# Global DB Access for Reading (Write operations must pass the modified DB back to save_db)
db = load_db()

# --- INDUSTRIAL CSS & JS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"][aria-expanded="false"] { display: none; }
    
    .header-text { text-align: center; font-family: sans-serif; }
    .header-branch { font-size: 30px; font-weight: 800; color: #333; margin-top: 5px; text-transform: uppercase; }
    
    /* TV DISPLAY */
    .serving-row { 
        display: flex; flex-direction: row; flex-wrap: wrap; 
        gap: 20px; justify-content: center; width: 100%; margin-bottom: 20px; 
    }
    .serving-card-small {
        background: white; border-left: 15px solid #2563EB; padding: 20px;
        border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.15); text-align: center;
        flex: 1 1 300px; min-width: 250px; animation: fadeIn 0.5s;
    }
    .serving-card-small h2 { margin: 0; font-size: 50px; color: #0038A8; font-weight: 900; }
    .serving-card-small p { margin: 0; font-size: 22px; color: #333; font-weight: bold; }
    .serving-card-small span { font-size: 16px; color: #555; }
    
    /* PARKED COUNTDOWN */
    .park-row {
        background: #fff3cd; color: #333; padding: 10px; margin-bottom: 5px; border-radius: 5px;
        font-weight: bold; display: flex; justify-content: space-between; border-left: 5px solid #ffc107;
    }
    .park-danger { 
        background: #fee2e2; color: #b91c1c; border-left: 5px solid #ef4444; 
        animation: pulse 2s infinite; display: flex; justify-content: space-between; padding: 10px; border-radius: 5px; font-weight: bold;
    }
    
    /* SWIMLANES */
    .swim-col { background: #f8f9fa; border-radius: 10px; padding: 10px; border-top: 10px solid #ccc; height: 100%; }
    .swim-col h3 { text-align: center; margin-bottom: 10px; font-size: 18px; text-transform: uppercase; color: #333; }
    .queue-item { 
        background: white; border-bottom: 1px solid #ddd; padding: 15px; margin-bottom: 5px;
        border-radius: 5px; display: flex; justify-content: space-between;
    }
    .queue-item span { font-size: 24px; font-weight: 900; color: #111; }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.8; } 100% { opacity: 1; } }
    
    /* KIOSK */
    .gate-btn > button { height: 350px !important; width: 100% !important; font-size: 40px !important; font-weight: 900 !important; border-radius: 30px !important; }
    .menu-card > button { height: 300px !important; width: 100% !important; font-size: 30px !important; font-weight: 800 !important; border-radius: 20px !important; border: 4px solid #ddd !important; }
    .swim-btn > button { height: 100px !important; width: 100% !important; font-size: 18px !important; font-weight: 700 !important; text-align: left !important; padding-left: 20px !important; }
    
    .head-red { background-color: #DC2626; } .border-red > button { border-left: 20px solid #DC2626 !important; }
    .head-orange { background-color: #EA580C; } .border-orange > button { border-left: 20px solid #EA580C !important; }
    .head-green { background-color: #16A34A; } .border-green > button { border-left: 20px solid #16A34A !important; }
    .head-blue { background-color: #2563EB; } .border-blue > button { border-left: 20px solid #2563EB !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC
# ==========================================
def generate_ticket(service, lane_code, is_priority, is_appt=False, appt_name=None, appt_time=None):
    # RELOAD DB TO ENSURE NO ID CONFLICTS
    local_db = load_db()
    
    prefix = "A" if is_appt else ("P" if is_priority else "R")
    count = len([t for t in local_db['tickets'] if t["lane"] == lane_code]) + 1
    ticket_num = f"{lane_code}{prefix}-{count:03d}"
    
    new_t = {
        "id": str(uuid.uuid4()), "number": ticket_num, "lane": lane_code,
        "service": service, "type": "APPOINTMENT" if is_appt else ("PRIORITY" if is_priority else "REGULAR"),
        "status": "WAITING", "timestamp": datetime.datetime.now().isoformat(),
        "start_time": None, "end_time": None, "park_timestamp": None,
        "history": [], "served_by": None, "ref_from": None, "referral_reason": None,
        "appt_name": appt_name, "appt_time": str(appt_time) if appt_time else None
    }
    local_db['tickets'].append(new_t)
    save_db(local_db)
    return new_t

def get_prio_score(t):
    ts = datetime.datetime.fromisoformat(t["timestamp"]).timestamp()
    if t.get("appt_time"): return ts - 100000 
    bonus = 1800 if t["type"] == "PRIORITY" else 0
    return ts - bonus

def calculate_real_wait_time(lane_code):
    local_db = load_db()
    recent = [t for t in local_db['history'] if t['lane'] == lane_code and t['end_time']]
    if not recent: return 15
    total_sec = sum([datetime.datetime.fromisoformat(t["end_time"]).timestamp() - datetime.datetime.fromisoformat(t["start_time"]).timestamp() for t in recent[-10:]])
    avg_txn_time = (total_sec / len(recent[-10:])) / 60 
    queue_len = len([t for t in local_db['tickets'] if t['lane'] == lane_code and t['status'] == "WAITING"])
    return round(queue_len * avg_txn_time)

def get_staff_efficiency(staff_name):
    local_db = load_db()
    my_txns = [t for t in local_db['history'] if t.get("served_by") == staff_name]
    return len(my_txns), "5m"

def get_allowed_counters(role):
    # Use global DB which is loaded on script run
    all_counters = db['config']['counter_map']
    target_types = []
    
    # STRICT LANE MAPPING
    if role == "TELLER": target_types = ["Teller"]
    elif role == "AO": target_types = ["Employer"]
    elif role == "MSR": target_types = ["Counter", "eCenter", "Help"]
    elif role in ["ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]: return [c['name'] for c in all_counters] 
    
    return [c['name'] for c in all_counters if c['type'] in target_types]

# ==========================================
# 4. MODULES
# ==========================================

def render_kiosk():
    st.markdown("""
        <div class='header-text'>
            <div style='font-size: 14px; color: #555; text-transform: uppercase; letter-spacing: 2px;'>Republic of the Philippines</div>
            <div style='font-size: 40px; font-weight: 900; color: #0038A8; text-transform: uppercase; font-style: italic;'>SOCIAL SECURITY SYSTEM</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<div class='header-text header-branch'>{db['config']['branch_name']}</div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; color:#555;'>Gabay sa bawat miyembro. Mangyaring pumili ng uri ng serbisyo.</div><br>", unsafe_allow_html=True)

    if 'kiosk_step' not in st.session_state:
        col_reg, col_prio = st.columns([1, 1], gap="large")
        with col_reg:
            st.markdown('<div class="gate-btn" style="border: 8px solid #1E40AF; border-radius:30px; overflow:hidden;">', unsafe_allow_html=True)
            if st.button("👤 REGULAR\n\nStandard Access"):
                st.session_state['is_prio'] = False; st.session_state['kiosk_step'] = 'menu'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_prio:
            st.markdown('<div class="gate-btn" style="border: 8px solid #B45309; border-radius:30px; overflow:hidden;">', unsafe_allow_html=True)
            if st.button("❤️ PRIORITY\n\nSenior, PWD, Pregnant"):
                st.session_state['is_prio'] = True; st.session_state['kiosk_step'] = 'menu'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.warning("⚠ NOTICE: Non-priority users will be transferred to end of line.")
    elif st.session_state['kiosk_step'] == 'menu':
        st.markdown("### Select Service Category")
        m1, m2, m3 = st.columns(3, gap="medium")
        with m1:
            st.markdown('<div class="menu-card">', unsafe_allow_html=True)
            if st.button("💳 PAYMENTS\n(Contrib/Loans)"):
                t = generate_ticket("Payment", "T", st.session_state['is_prio'])
                st.session_state['last_ticket'] = t; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with m2:
            st.markdown('<div class="menu-card">', unsafe_allow_html=True)
            if st.button("💼 EMPLOYERS\n(Account Mgmt)"):
                t = generate_ticket("Account Management", "A", st.session_state['is_prio'])
                st.session_state['last_ticket'] = t; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with m3:
            st.markdown('<div class="menu-card">', unsafe_allow_html=True)
            if st.button("👤 MEMBER SERVICES\n(Claims, ID, Records)"):
                st.session_state['kiosk_step'] = 'mss'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("⬅ GO BACK", type="secondary", use_container_width=True): del st.session_state['kiosk_step']; st.rerun()
    elif st.session_state['kiosk_step'] == 'mss':
        st.markdown("### 👤 Member Services")
        cols = st.columns(4, gap="small")
        categories = ["Benefits", "Loans", "Member Records Update", "eServices"]
        colors = ["red", "orange", "green", "blue"]
        icons = ["🏥", "💰", "📝", "💻"]
        for i, cat_name in enumerate(categories):
            with cols[i]:
                st.markdown(f"<div class='swim-header head-{colors[i]}'>{icons[i]} {cat_name}</div>", unsafe_allow_html=True)
                st.markdown(f'<div class="swim-btn border-{colors[i]}">', unsafe_allow_html=True)
                for label, svc_code, lane in db['menu'].get(cat_name, []):
                    if st.button(label, key=label):
                        if "Retirement" in label: st.session_state['kiosk_step'] = 'gate_rd'; st.rerun()
                        else:
                            generate_ticket(svc_code, lane, st.session_state['is_prio'])
                            st.session_state['last_ticket'] = db['tickets'][-1]
                            st.session_state['kiosk_step'] = 'ticket'; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ GO BACK", type="secondary", use_container_width=True): st.session_state['kiosk_step'] = 'menu'; st.rerun()
    elif st.session_state['kiosk_step'] == 'gate_rd':
        st.warning("Pre-Qualification: Do you have pending cases/portability issues?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("YES (Complex)", type="primary", use_container_width=True): generate_ticket("Ben-Ret(C)", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db['tickets'][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with c2:
            if st.button("NO (Regular)", type="primary", use_container_width=True): generate_ticket("Ben-Ret(S)", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db['tickets'][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        st.button("⬅ CANCEL", on_click=lambda: st.session_state.update({'kiosk_step': 'mss'}))
    elif st.session_state['kiosk_step'] == 'ticket':
        t = st.session_state['last_ticket']
        bg = "#FFC107" if t['type'] == 'PRIORITY' else "#2563EB"
        col = "#0038A8" if t['type'] == 'PRIORITY' else "white"
        
        prio_text = ""
        if t['type'] == 'PRIORITY':
            prio_text = "**⚠ PRIORITY LANE:** For Seniors, PWDs, Pregnant ONLY. Non-qualified users will be sent to END of queue."
        
        st.markdown(f"""
        <div class="ticket-card no-print" style='background:{bg}; color:{col}; padding:40px; border-radius:20px; text-align:center; margin:20px 0;'>
            <h1>{t['number']}</h1><h3>{t['service']}</h3><p>Please wait for the voice call.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if prio_text: st.error(prio_text)
        st.info("**POLICY:** Ticket forfeited if parked for 30 mins.")

        c1, c2, c3 = st.columns(3)
        with c1: 
            # LOAD DB TO DELETE
            if st.button("❌ CANCEL", use_container_width=True): 
                curr_db = load_db()
                curr_db['tickets'] = [x for x in curr_db['tickets'] if x['id'] != t['id']]
                save_db(curr_db)
                del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c2:
            if st.button("✅ DONE", type="primary", use_container_width=True): del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c3:
            if st.button("🖨️ PRINT", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True); time.sleep(1); del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()

def render_display():
    # RELOAD DB ON EVERY REFRESH FOR SYNC
    local_db = load_db()
    
    st.markdown(f"<h1 style='text-align: center; color: #0038A8;'>NOW SERVING</h1>", unsafe_allow_html=True)
    
    # 1. SERVING GRID
    serving_tickets = [t for t in local_db['tickets'] if t["status"] == "SERVING"]
    if serving_tickets:
        st.markdown('<div class="serving-row">', unsafe_allow_html=True)
        for t in serving_tickets:
            staff_obj = next((v for k,v in local_db['staff'].items() if v['name'] == t.get('served_by')), None)
            if staff_obj and staff_obj.get('status') == "ON_BREAK": continue
            
            b_color = "#DC2626" if t['lane'] == "T" else ("#16A34A" if t['lane'] == "A" else "#2563EB")
            st.markdown(f"""
            <div class="serving-card-small" style="border-left: 15px solid {b_color};">
                <h2 style="color:{b_color}">{t['number']}</h2>
                <p>{t.get('served_by','Counter')}</p>
                <span>{t['service']}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Waiting for next number...")
        
    c_queue, c_park = st.columns([3, 1])
    
    # 2. SWIMLANE QUEUES
    with c_queue:
        q1, q2, q3 = st.columns(3)
        waiting = [t for t in local_db['tickets'] if t["status"] == "WAITING"]
        waiting.sort(key=get_prio_score)
        
        with q1:
            st.markdown(f"<div class='swim-col' style='border-top-color:#DC2626;'><h3>💳 PAYMENTS</h3>", unsafe_allow_html=True)
            for t in [x for x in waiting if x['lane'] == 'T'][:5]:
                st.markdown(f"<div class='queue-item'><span>{t['number']}</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with q2:
            st.markdown(f"<div class='swim-col' style='border-top-color:#16A34A;'><h3>💼 EMPLOYERS</h3>", unsafe_allow_html=True)
            for t in [x for x in waiting if x['lane'] == 'A'][:5]:
                st.markdown(f"<div class='queue-item'><span>{t['number']}</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with q3:
            st.markdown(f"<div class='swim-col' style='border-top-color:#2563EB;'><h3>👤 SERVICES</h3>", unsafe_allow_html=True)
            for t in [x for x in waiting if x['lane'] in ['C','E','F']][:5]:
                st.markdown(f"<div class='queue-item'><span>{t['number']}</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # 3. PARKED COUNTDOWN
    with c_park:
        st.markdown("### 🅿️ PARKED")
        parked = [t for t in local_db['tickets'] if t["status"] == "PARKED"]
        for p in parked:
            park_time = datetime.datetime.fromisoformat(p['park_timestamp'])
            elapsed = datetime.datetime.now() - park_time
            remaining = datetime.timedelta(minutes=30) - elapsed
            
            if remaining.total_seconds() <= 0:
                p["status"] = "NO_SHOW"
                save_db(local_db) # Save change
                st.rerun()
            else:
                mins, secs = divmod(remaining.total_seconds(), 60)
                css_class = "park-danger" if mins < 5 else "park-row"
                st.markdown(f"""
                <div class="{css_class}">
                    <span>{p['number']}</span>
                    <span>{int(mins):02d}:{int(secs):02d}</span>
                </div>""", unsafe_allow_html=True)

    txt = " | ".join(local_db['announcements'])
    st.markdown(f"<div style='background: #FFD700; color: black; padding: 10px; font-weight: bold; position: fixed; bottom: 0; width: 100%; font-size:20px;'><marquee>{txt}</marquee></div>", unsafe_allow_html=True)
    time.sleep(3); st.rerun()

def render_counter(user):
    # FORCE RELOAD TO GET FRESH TICKETS
    local_db = load_db()
    
    # Get user object from FRESH DB to see Break Status
    user_key = next((k for k,v in local_db['staff'].items() if v['name'] == user['name']), None)
    if not user_key: st.error("User Sync Error. Please Relogin."); return
    
    current_user_state = local_db['staff'][user_key]

    # BREAK SCREEN
    if current_user_state.get('status') == "ON_BREAK":
        st.warning(f"⛔ YOU ARE CURRENTLY ON BREAK ({current_user_state.get('break_reason', 'Break')})")
        st.info(f"Break started at: {current_user_state.get('break_start_time', '')}")
        start_dt = datetime.datetime.fromisoformat(current_user_state.get('break_start_time'))
        elapsed = datetime.datetime.now() - start_dt
        st.metric("Time Elapsed", str(elapsed).split('.')[0])
        
        if st.button("▶ RESUME WORK", type="primary"):
            local_db['breaks'].append({
                "name": user['name'], "reason": current_user_state.get('break_reason'), 
                "start": current_user_state.get('break_start_time'),
                "end": datetime.datetime.now().isoformat(), "duration_sec": elapsed.total_seconds()
            })
            local_db['staff'][user_key]['status'] = "ACTIVE"
            del local_db['staff'][user_key]['break_reason']
            del local_db['staff'][user_key]['break_start_time']
            save_db(local_db)
            st.session_state['user'] = local_db['staff'][user_key]
            st.rerun()
        return

    # STATION SELECTOR
    if 'my_station' not in st.session_state: st.session_state['my_station'] = current_user_state.get('default_station', 'Counter 1')
    st.sidebar.title(f"👮 {user['name']}")
    
    with st.sidebar.expander("☕ Go On Break"):
        b_reason = st.selectbox("Reason", ["Lunch Break", "Coffee Break (15m)", "Bio-Break", "Emergency"])
        if st.button("⏸ START BREAK"):
            local_db['staff'][user_key]['status'] = "ON_BREAK"
            local_db['staff'][user_key]['break_reason'] = b_reason
            local_db['staff'][user_key]['break_start_time'] = datetime.datetime.now().isoformat()
            save_db(local_db)
            st.session_state['user'] = local_db['staff'][user_key]
            st.rerun()

    with st.sidebar.expander("🔒 Change Password"):
        with st.form("pwd_chg"):
            n_pass = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                if user_key: local_db['staff'][user_key]['pass'] = n_pass; save_db(local_db); st.success("Updated!")
    if st.sidebar.button("⬅ LOGOUT"): del st.session_state['user']; del st.session_state['my_station']; st.rerun()
    
    if user['role'] in ["SECTION_HEAD", "BRANCH_HEAD"]:
        with st.sidebar.expander("📅 Add Appointment"):
            with st.form("add_appt"):
                nm = st.text_input("Name"); svc = st.selectbox("Service", ["Pension", "Death", "Loan"]); tm = st.time_input("Time")
                if st.form_submit_button("Book Slot"): generate_ticket(svc, "C", True, is_appt=True, appt_name=nm, appt_time=tm); st.success("Booked!")
                    
    st.markdown(f"### Station: {st.session_state['my_station']}")
    
    # RE-FETCH ALLOWED STATIONS
    allowed_counters = get_allowed_counters(user['role'])
    if st.session_state['my_station'] not in allowed_counters and allowed_counters: st.session_state['my_station'] = allowed_counters[0]
    st.session_state['my_station'] = st.selectbox("Switch Station", allowed_counters, index=allowed_counters.index(st.session_state['my_station']) if st.session_state['my_station'] in allowed_counters else 0)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # QUEUE LOGIC FROM FRESH DB
    current_counter_obj = next((c for c in local_db['config']['counter_map'] if c['name'] == st.session_state['my_station']), None)
    station_type = current_counter_obj['type'] if current_counter_obj else "Counter"
    my_lanes = local_db['config']["assignments"].get(station_type, ["C"]) # Fallback to C if mapping fails
    
    # VISIBILITY FIX: MSRs (Type=Counter) only see C/E/F tickets. Tellers only see T.
    queue = [t for t in local_db['tickets'] if t["status"] == "WAITING" and t["lane"] in my_lanes]
    queue.sort(key=get_prio_score)
    
    # Check if I am serving someone (from FRESH DB)
    current = next((t for t in local_db['tickets'] if t["status"] == "SERVING" and t.get("served_by") == st.session_state['my_station']), None)
    
    if 'refer_modal' not in st.session_state: st.session_state['refer_modal'] = False
    c1, c2 = st.columns([2,1])
    with c1:
        if current:
            st.markdown(f"""<div style='padding:30px; background:#e0f2fe; border-radius:15px; border-left:10px solid #0369a1;'>
            <h1 style='margin:0; color:#0369a1; font-size: 80px;'>{current['number']}</h1>
            <h3>{current['service']}</h3></div>""", unsafe_allow_html=True)
            
            if current.get("ref_from"): 
                st.markdown(f"""
                <div style='background:#fee2e2; border-left:5px solid #ef4444; padding:10px; margin-top:10px;'>
                    <span style='color:#b91c1c; font-weight:bold;'>↩ REFERRED FROM: {current["ref_from"]}</span><br>
                    <span style='color:#b91c1c; font-weight:bold;'>📝 REASON: {current.get("referral_reason", "No reason provided")}</span>
                </div>""", unsafe_allow_html=True)

            if st.session_state['refer_modal']:
                with st.form("referral"):
                    st.write("**Referral Details**")
                    target = st.selectbox("Transfer To", ["Teller", "Employer", "eCenter", "Counter"])
                    reason = st.text_input("Reason for Referral (Required)") 
                    c_col1, c_col2 = st.columns(2)
                    with c_col1:
                        if st.form_submit_button("✅ CONFIRM TRANSFER"):
                            if not reason: st.error("Reason required!"); st.stop()
                            
                            current_lane = current['lane']
                            target_lane = {"Teller":"T", "Employer":"A", "eCenter":"E", "Counter":"C"}[target]
                            
                            if current['type'] == 'PRIORITY':
                                current['type'] = 'REGULAR' 
                                current['timestamp'] = datetime.datetime.now().isoformat() 
                            else:
                                ts = datetime.datetime.fromisoformat(current['timestamp'])
                                if current_lane == "C" and target_lane != "C": ts -= datetime.timedelta(minutes=30)
                                elif current_lane != "C" and target_lane == "C": ts += datetime.timedelta(minutes=45)
                                current['timestamp'] = ts.isoformat()
                            
                            current["lane"] = target_lane; current["status"] = "WAITING"; current["served_by"] = None
                            current["ref_from"] = st.session_state['my_station']
                            current["referral_reason"] = reason 
                            
                            # SAVE TO DB
                            save_db(local_db)
                            st.session_state['refer_modal'] = False; st.rerun()
                    with c_col2:
                        if st.form_submit_button("❌ CANCEL"): st.session_state['refer_modal'] = False; st.rerun()
            else:
                st.markdown("<br>", unsafe_allow_html=True)
                b1, b2, b3 = st.columns(3)
                if b1.button("✅ COMPLETE", use_container_width=True): 
                    current["status"] = "COMPLETED"; current["end_time"] = datetime.datetime.now().isoformat(); 
                    local_db['history'].append(current)
                    save_db(local_db)
                    st.rerun()
                if b2.button("🅿️ PARK", use_container_width=True): 
                    current["status"] = "PARKED"; current["park_timestamp"] = datetime.datetime.now().isoformat(); 
                    save_db(local_db)
                    st.rerun()
                if b3.button("🔄 REFER", use_container_width=True): st.session_state['refer_modal'] = True; st.rerun()
        else:
            if st.button("🔊 CALL NEXT", type="primary", use_container_width=True):
                # FRESH QUEUE CHECK
                if queue:
                    nxt = queue[0]
                    # Find ticket in local_db to modify it properly (by ID)
                    db_ticket = next((x for x in local_db['tickets'] if x['id'] == nxt['id']), None)
                    if db_ticket:
                        db_ticket["status"] = "SERVING"
                        db_ticket["served_by"] = st.session_state['my_station']
                        db_ticket["start_time"] = datetime.datetime.now().isoformat()
                        save_db(local_db)
                        st.rerun()
                else: st.warning(f"No tickets for {station_type}.")
    with c2:
        count, avg_time = get_staff_efficiency(user['name'])
        st.metric("Performance", count, delta=avg_time + " avg/txn")
        st.divider()
        st.write("🅿️ Parked Tickets")
        parked = [t for t in local_db['tickets'] if t["status"] == "PARKED"]
        for p in parked:
            if st.button(f"🔊 {p['number']}", key=p['id']):
                p["status"] = "SERVING"; p["served_by"] = st.session_state['my_station']; 
                save_db(local_db)
                st.rerun()

def render_admin_panel(user):
    # FORCE RELOAD FOR ADMIN
    local_db = load_db()
    
    st.title("🛠 Admin & Brain Console")
    if st.sidebar.button("⬅ LOGOUT"): del st.session_state['user']; st.rerun()
    tabs = []
    if user['role'] in ["ADMIN", "BRANCH_HEAD"]: tabs.extend(["Users", "Counters", "Menu", "Brain (KB)", "Announcements", "Backup"])
    if user['role'] in ["BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]: tabs.append("Analytics")
    if not tabs: st.error("Access Denied"); return
    active = st.radio("Module", tabs, horizontal=True)
    st.divider()
    
    if active == "Users":
        st.subheader("Manage Users")
        h1, h2, h3, h4, h5 = st.columns([1.5, 3, 2, 1, 0.5])
        h1.markdown("**User ID**"); h2.markdown("**Name (Role)**"); h3.markdown("**Station**"); h4.markdown("**Actions**")
        st.divider()
        for uid, udata in list(local_db['staff'].items()):
            c1, c2, c3, c4, c5 = st.columns([1.5, 3, 2, 0.5, 0.5])
            c1.text(uid); c2.text(f"{udata['name']} ({udata['role']})"); c3.text(udata.get('default_station', '-'))
            if c4.button("✏️", key=f"ed_{uid}"): st.session_state['edit_uid'] = uid; st.rerun()
            if c5.button("🗑", key=f"del_{uid}"): 
                if uid == user['name']: st.error("Cannot delete yourself!")
                else: del local_db['staff'][uid]; save_db(local_db); st.rerun()
        st.divider()
        uid_to_edit = st.session_state.get('edit_uid', None)
        if uid_to_edit and uid_to_edit not in local_db['staff']: del st.session_state['edit_uid']; st.rerun()
        with st.form("user_form"):
            st.write(f"**{'Edit User: ' + uid_to_edit if uid_to_edit else 'Add New User'}**")
            st.info("ℹ️ NOTE: Default password for new users is '123'.")
            def_id = uid_to_edit if uid_to_edit else ""; def_name = local_db['staff'][uid_to_edit]['name'] if uid_to_edit else ""; def_role = local_db['staff'][uid_to_edit]['role'] if uid_to_edit else "MSR"
            u_id = st.text_input("User ID (Login)", value=def_id); u_name = st.text_input("Display Name", value=def_name)
            u_role = st.selectbox("Role", ["MSR", "TELLER", "AO", "SECTION_HEAD", "DIV_HEAD", "BRANCH_HEAD", "ADMIN"], index=["MSR", "TELLER", "AO", "SECTION_HEAD", "DIV_HEAD", "BRANCH_HEAD", "ADMIN"].index(def_role))
            avail_stations = get_allowed_counters(u_role); u_station = st.selectbox("Default Station", avail_stations if avail_stations else ["None"])
            reset_requested = False
            if uid_to_edit:
                st.markdown("---"); 
                if st.checkbox("RESET PASSWORD TO '123'"): reset_requested = True
            if st.form_submit_button("Save User"):
                old_pass = "123"
                if uid_to_edit: old_pass = local_db['staff'][uid_to_edit]['pass']; 
                if uid_to_edit and u_id != uid_to_edit: del local_db['staff'][uid_to_edit]
                if reset_requested: old_pass = "123"
                local_db['staff'][u_id] = {"pass": old_pass, "role": u_role, "name": u_name, "default_station": u_station, "status": "ACTIVE"}
                save_db(local_db); 
                if 'edit_uid' in st.session_state: del st.session_state['edit_uid']
                st.success("Saved!"); st.rerun()
    elif active == "Counters":
        st.info("Configure Branch Architecture")
        for i, c in enumerate(local_db['config']['counter_map']):
            c1, c2, c3 = st.columns([3, 2, 1]); c1.write(f"**{c['name']}**"); c2.write(f"Type: {c['type']}")
            if c3.button("🗑", key=f"dc_{i}"): local_db['config']['counter_map'].pop(i); save_db(local_db); st.rerun()
        with st.form("add_counter"):
            cn = st.text_input("Counter Name"); ct = st.selectbox("Category", ["Counter", "Teller", "Employer", "eCenter"])
            if st.form_submit_button("Add"): local_db['config']['counter_map'].append({"name": cn, "type": ct}); save_db(local_db); st.success("Added!"); st.rerun()
    elif active == "Menu":
        st.info("Edit Kiosk Buttons"); cat = st.selectbox("Category", list(local_db['menu'].keys()))
        for i, (label, code, lane) in enumerate(local_db['menu'][cat]):
            c1, c2 = st.columns([4, 1]); c1.text(f"{label} ({code}) -> {lane}")
            if c2.button("🗑", key=f"del_{i}"): local_db['menu'][cat].pop(i); save_db(local_db); st.rerun()
        with st.form("new_btn"):
            n_lbl = st.text_input("Label"); n_code = st.text_input("Code"); n_lane = st.selectbox("Lane", ["C", "E", "F", "T", "A"])
            if st.form_submit_button("Add"): local_db['menu'][cat].append((n_lbl, n_code, n_lane)); save_db(local_db); st.rerun()
    elif active == "Brain (KB)":
        st.info("Train Chatbot"); 
        for i, item in enumerate(local_db['knowledge_base']):
            with st.expander(f"📚 {item['topic']}"): st.write(item['content']); 
            if st.button("Delete", key=f"kb_{i}"): local_db['knowledge_base'].pop(i); save_db(local_db); st.rerun()
        with st.form("new_kb"):
            topic = st.text_input("Topic"); content = st.text_area("Content")
            if st.form_submit_button("Add"): local_db['knowledge_base'].append({"topic": topic, "content": content}); save_db(local_db); st.success("Learned!")
    elif active == "Announcements":
        curr = " | ".join(local_db['announcements']); new_txt = st.text_area("Display Marquee", value=curr)
        if st.button("Update"): local_db['announcements'] = [new_txt]; save_db(local_db); st.success("Updated!")
    elif active == "Backup":
        st.download_button("📥 DOWNLOAD DATABASE", data=json.dumps(local_db), file_name="sss_backup.json", mime="application/json")
        up = st.file_uploader("📤 RESTORE DATABASE", type="json")
        if up: st.session_state.db = json.load(up); save_db(local_db); st.success("Restored!"); time.sleep(1); st.rerun()
    elif active == "Analytics":
        st.subheader("📊 Ticket History"); st.dataframe(pd.DataFrame(local_db['history'])); st.divider()
        st.subheader("☕ Staff Break Logs")
        if "breaks" in local_db: st.dataframe(pd.DataFrame(local_db['breaks']))
        else: st.info("No break data yet.")

# ==========================================
# 5. ROUTER
# ==========================================
params = st.query_params
mode = params.get("mode")

if mode == "kiosk": render_kiosk()
elif mode == "staff":
    # STAFF LOGIN SCREEN
    if 'user' not in st.session_state:
        st.title("Staff Login")
        u = st.text_input("Username"); p = st.text_input("Password", type="password")
        if st.button("Login"):
            local_db = load_db() # Fresh load to check new users
            acct = next((v for k,v in local_db['staff'].items() if v["name"] == u or k == u), None)
            if acct: 
                if acct['pass'] == p: st.session_state['user'] = acct; st.rerun()
                else: st.error("Wrong Password")
            else: st.error("User not found")
    else:
        user = st.session_state['user']
        if user['role'] in ["ADMIN", "DIV_HEAD"]: render_admin_panel(user)
        elif user['role'] in ["BRANCH_HEAD", "SECTION_HEAD"]:
            view = st.sidebar.radio("View", ["Admin", "Counter"])
            if view == "Admin": render_admin_panel(user)
            else: render_counter(user)
        else: render_counter(user)
elif mode == "display": render_display()
else:
    if db['config']["logo_url"].startswith("http"): st.image(db['config']["logo_url"], width=50)
    st.title("G-ABAY Mobile Tracker")
    t1, t2, t3 = st.tabs(["🎫 Tracker", "💬 Ask G-ABAY", "⭐ Rate Us"])
    with t1:
        tn = st.text_input("Enter Ticket #")
        if tn:
            local_db = load_db() # Fresh check
            t = next((x for x in local_db['tickets'] if x["number"] == tn), None)
            if t:
                if t['status'] == "PARKED":
                    park_time = datetime.datetime.fromisoformat(t['park_timestamp'])
                    remaining = datetime.timedelta(minutes=30) - (datetime.datetime.now() - park_time)
                    if remaining.total_seconds() > 0:
                        mins, secs = divmod(remaining.total_seconds(), 60)
                        st.warning(f"⚠ TICKET PARKED.\nTime Remaining to No-Show: {int(mins):02d}:{int(secs):02d}")
                    else: st.error("❌ TICKET FORFEITED (NO SHOW). Please get a new number.")
                else:
                    st.info(f"Status: {t['status']}")
                    if t['status'] == "WAITING":
                        est = calculate_real_wait_time(t['lane'])
                        st.metric("Est. Wait", f"{est} mins")
            else: st.error("Not Found")
    with t2:
        st.markdown("### 🤖 Chatbot")
        now = datetime.datetime.now()
        is_offline = not (8 <= now.hour < 17) # 8AM to 5PM
        if "messages" not in st.session_state: st.session_state.messages = []
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if prompt := st.chat_input("Ask about SSS..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            if is_offline:
                resp = "Hello! I am currently offline. My operating hours are Monday to Friday, 8:00 AM to 5:00 PM. For immediate assistance, please visit the official SSS website at www.sss.gov.ph"
            else:
                found = False
                for kb in db['knowledge_base']:
                    if prompt.lower() in kb['topic'].lower() or prompt.lower() in kb['content'].lower():
                        resp = f"**Found in {kb['topic']}:**\n{kb['content']}"; found = True; break
                if not found: resp = "I couldn't find that in my records. Please visit the eCenter."
            st.session_state.messages.append({"role": "assistant", "content": resp})
            with st.chat_message("assistant"): st.markdown(resp)
    with t3:
        with st.form("rev"):
            rate = st.slider("Rating", 1, 5); pers = st.text_input("Personnel"); comm = st.text_area("Comments")
            if st.form_submit_button("Submit"): 
                local_db = load_db()
                local_db['reviews'].append({"rating": rate, "personnel": pers, "comment": comm})
                save_db(local_db)
                st.success("Thanks!")
