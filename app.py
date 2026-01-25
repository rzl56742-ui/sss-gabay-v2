# ==============================================================================
# SSS G-ABAY v18.0 - BRANCH OPERATING SYSTEM (CONNECTED DYNAMIC EDITION)
# "World-Class Service, Zero-Install Architecture"
# COPYRIGHT: © 2026 rpt/sssgingoog
# ==============================================================================

import streamlit as st
import pandas as pd
import datetime
import time
import uuid

# ==========================================
# 1. SYSTEM CONFIGURATION & GLOBAL STATE
# ==========================================
st.set_page_config(page_title="SSS G-ABAY v18.0", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

# --- SINGLETON DATABASE (The "Glue") ---
@st.cache_resource
class SystemState:
    def __init__(self):
        self.tickets = []
        self.history = []
        self.reviews = []
        
        # DYNAMIC CONFIGURATION (Editable by Admin/BH)
        self.config = {
            "branch_name": "BRANCH GINGOOG",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Social_Security_System_%28SSS%29.svg/1200px-Social_Security_System_%28SSS%29.svg.png",
            "lanes": {
                "T": {"name": "Teller", "desc": "Payments"},
                "A": {"name": "Employer", "desc": "Account Mgmt"},
                "C": {"name": "Counter", "desc": "Complex Trans"},
                "E": {"name": "eCenter", "desc": "Online Services"},
                "F": {"name": "Fast Lane", "desc": "Simple Trans"}
            },
            # Defines which lanes a counter type pulls from
            "assignments": {
                "Counter": ["C", "E", "F"],
                "Teller": ["T"],
                "Employer": ["A"],
                "eCenter": ["E"],
                "Help": ["F", "E"]
            },
            "counters": ["Counter 1", "Counter 2", "Counter 3", "Teller 1", "Teller 2", "Employer Desk", "eCenter", "Help Desk"]
        }
        
        # DYNAMIC MENU STRUCTURE (v17.0 Default Layout)
        # Format: "Category": [("Label", "ServiceCode", "LaneCode")]
        self.menu = {
            "Benefits": [
                ("Maternity / Sickness", "Ben-Mat/Sick", "E"),
                ("Retirement / Death", "Ben-Ret/Death", "C"), # C triggers gate
                ("Disability / Unemployment", "Ben-Dis/Unemp", "E")
            ],
            "Loans": [
                ("Salary / Conso", "Ln-Sal/Conso", "E"),
                ("Calamity / Emergency", "Ln-Cal/Emerg", "E"),
                ("Pension Loan (Retiree/Survivor)", "Ln-Pension", "E")
            ],
            "Records": [
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
        }

        # ROLE MATRIX & USERS
        self.staff = {
            "admin": {"pass": "sss2026", "role": "ADMIN", "name": "System Admin"},
            "head": {"pass": "head123", "role": "BRANCH_HEAD", "name": "Branch Head"},
            "div": {"pass": "div123", "role": "DIV_HEAD", "name": "Division Head"},
            "section": {"pass": "sec123", "role": "SECTION_HEAD", "name": "Section Head"},
            "ao1": {"pass": "123", "role": "AO", "name": "Account Officer 1"},
            "teller1": {"pass": "123", "role": "TELLER", "name": "Teller 1"},
            "msr1": {"pass": "123", "role": "MSR", "name": "MSR 1"}
        }
        self.announcements = ["Welcome to SSS Gingoog. Operating Hours: 8:00 AM - 5:00 PM."]

if 'system' not in st.session_state:
    st.session_state.system = SystemState()

db = st.session_state.system

# --- INDUSTRIAL CSS & JS ---
st.markdown("""
<script>
function startTimer(duration, displayId) {
    var timer = duration, minutes, seconds;
    var display = document.getElementById(displayId);
    if (!display) return;
    
    var interval = setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
        display.textContent = minutes + ":" + seconds;
        if (--timer < 0) { 
            clearInterval(interval); 
            display.textContent = "EXPIRED";
        }
    }, 1000);
}
</script>
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"][aria-expanded="false"] { display: none; }
    
    /* HEADER */
    .header-text { text-align: center; font-family: sans-serif; }
    .header-top { font-size: 14px; color: #555; text-transform: uppercase; letter-spacing: 2px; }
    .header-main { font-size: 40px; font-weight: 900; color: #0038A8; margin: 0; padding: 0; text-transform: uppercase; font-style: italic; }
    .header-branch { font-size: 30px; font-weight: 800; color: #333; margin-top: 5px; text-transform: uppercase; }
    
    /* KIOSK MAIN BUTTONS */
    .gate-btn > button {
        height: 350px !important; width: 100% !important;
        font-size: 40px !important; font-weight: 900 !important;
        border-radius: 30px !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    /* MAIN MENU CARDS */
    .menu-card > button {
        height: 300px !important; width: 100% !important;
        font-size: 30px !important; font-weight: 800 !important;
        border-radius: 20px !important; border: 4px solid #ddd !important;
        background-color: white !important; color: #0038A8 !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    
    /* SUB-MENU VERTICAL STACK BUTTONS */
    .swim-btn > button {
        height: 100px !important; width: 100% !important;
        font-size: 18px !important; font-weight: 700 !important;
        border-radius: 10px !important; border: 2px solid #eee !important;
        background-color: white !important; color: #333 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 10px !important;
        text-align: left !important; padding-left: 20px !important;
        white-space: normal !important; /* Allow text wrap */
        line-height: 1.2 !important;
    }
    .swim-btn > button:hover { background-color: #f0f9ff !important; transform: scale(1.02); }

    /* SECTION HEADERS */
    .section-header {
        font-size: 20px; font-weight: 900; text-align: center;
        padding: 10px; border-radius: 10px 10px 0 0; color: white;
        margin-bottom: 10px; text-transform: uppercase;
    }
    
    /* COLOR CODING */
    .head-red { background-color: #DC2626; }
    .head-orange { background-color: #EA580C; }
    .head-green { background-color: #16A34A; }
    .head-blue { background-color: #2563EB; }
    
    .border-red > button { border-left: 20px solid #DC2626 !important; }
    .border-orange > button { border-left: 20px solid #EA580C !important; }
    .border-green > button { border-left: 20px solid #16A34A !important; }
    .border-blue > button { border-left: 20px solid #2563EB !important; }

    /* DISPLAY MODULE */
    .serving-card {
        background-color: white; border-left: 20px solid #2563EB;
        padding: 40px; margin-bottom: 20px; border-radius: 15px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1); text-align: center;
    }
    .queue-list {
        background-color: #f8f9fa; padding: 20px; border-radius: 15px;
        border: 2px solid #ddd; height: 100%;
    }
    .queue-item {
        font-size: 24px; border-bottom: 1px solid #ccc; padding: 10px;
        display: flex; justify-content: space-between;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC
# ==========================================
def generate_ticket(service, lane_code, is_priority, is_appt=False, appt_name=None, appt_time=None):
    prefix = "A" if is_appt else ("P" if is_priority else "R")
    count = len([t for t in db.tickets if t["lane"] == lane_code]) + 1
    ticket_num = f"{lane_code}{prefix}-{count:03d}"
    
    # Calculate Priority Score (Time Bonus Logic)
    # Default: Use current time.
    # If transferred from Slow to Fast: -30 mins (Bonus)
    # If transferred from Fast to Slow: +45 mins (Penalty)
    
    new_t = {
        "id": str(uuid.uuid4()), "number": ticket_num, "lane": lane_code,
        "service": service, "type": "APPOINTMENT" if is_appt else ("PRIORITY" if is_priority else "REGULAR"),
        "status": "WAITING", "timestamp": datetime.datetime.now(),
        "start_time": None, "end_time": None, "park_timestamp": None,
        "history": [], "served_by": None, "ref_from": None,
        "appt_name": appt_name, "appt_time": appt_time
    }
    db.tickets.append(new_t)
    return new_t

def get_prio_score(t):
    # Base score is timestamp
    base = t["timestamp"].timestamp()
    
    # APPOINTMENT LOGIC: If appt_time exists and is in future, push to bottom. If passed, push to top.
    if t.get("appt_time"):
        # Not implemented full scheduler for demo, treating as SUPER PRIORITY
        return base - 100000 
        
    # REFERRAL & PRIORITY LOGIC
    bonus = 0
    if t.get("ref_from"):
        # Referral bonus logic handled at transfer time by modifying timestamp? 
        # Better: Modify score here. 
        # But user asked for specific +30/-45 min injection.
        # We will assume timestamp was modified during transfer.
        pass
    else:
        if t["type"] == "PRIORITY": bonus = 1800 # 30 mins advantage
        
    return base - bonus

def calculate_real_wait_time(lane_code):
    recent = [t for t in db.history if t['lane'] == lane_code and t['end_time']]
    if not recent: return 15
    total_sec = sum([(t["end_time"] - t["start_time"]).total_seconds() for t in recent[-10:]])
    avg_txn_time = (total_sec / len(recent[-10:])) / 60 
    queue_len = len([t for t in db.tickets if t['lane'] == lane_code and t['status'] == "WAITING"])
    return round(queue_len * avg_txn_time)

def get_staff_efficiency(staff_name):
    my_txns = [t for t in db.history if t.get("served_by") == staff_name and t.get("start_time") and t.get("end_time")]
    if not my_txns: return 0, "0m"
    total_sec = sum([(t["end_time"] - t["start_time"]).total_seconds() for t in my_txns])
    avg_min = round((total_sec / len(my_txns)) / 60, 1)
    return len(my_txns), f"{avg_min}m"

# ==========================================
# 4. MODULES
# ==========================================

# --- MODULE A: KIOSK (Dynamic & Swimlane) ---
def render_kiosk():
    st.markdown("""
        <div class='header-text'>
            <div class='header-top'>Republic of the Philippines</div>
            <div class='header-main'>SOCIAL SECURITY SYSTEM</div>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,3,1])
    with c2:
        st.markdown(f"<div style='text-align:center'><img src='{db.config['logo_url']}' width='100'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='header-text header-branch'>{db.config['branch_name']}</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#555;'>Gabay sa bawat miyembro. Mangyaring pumili ng uri ng serbisyo.</div><br>", unsafe_allow_html=True)

    if 'kiosk_step' not in st.session_state:
        # PAGE 1: GATE
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
        # PAGE 2: MAIN MENU
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
        # PAGE 3: MEMBER SERVICES (DYNAMIC RENDERING)
        st.markdown("### 👤 Member Services")
        
        # Mapped Columns to preserve layout: Benefits(0), Loans(1), Records(2), eServices(3)
        cols = st.columns(4, gap="small")
        categories = ["Benefits", "Loans", "Records", "eServices"]
        colors = ["red", "orange", "green", "blue"]
        icons = ["🏥", "💰", "📝", "💻"]
        
        for i, cat_name in enumerate(categories):
            with cols[i]:
                # Header
                st.markdown(f"<div class='swim-header head-{colors[i]}'>{icons[i]} {cat_name}</div>", unsafe_allow_html=True)
                # Buttons Loop
                st.markdown(f'<div class="swim-btn border-{colors[i]}">', unsafe_allow_html=True)
                for label, svc_code, lane in db.menu.get(cat_name, []):
                    if st.button(label, key=label):
                        # Special logic for Retirement (Gate)
                        if "Retirement" in label:
                            st.session_state['kiosk_step'] = 'gate_rd'; st.rerun()
                        else:
                            generate_ticket(svc_code, lane, st.session_state['is_prio'])
                            st.session_state['last_ticket'] = db.tickets[-1]
                            st.session_state['kiosk_step'] = 'ticket'; st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ GO BACK", type="secondary", use_container_width=True): st.session_state['kiosk_step'] = 'menu'; st.rerun()

    elif st.session_state['kiosk_step'] == 'gate_rd':
        st.warning("Pre-Qualification: Do you have pending cases/portability issues?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("YES (Complex)", type="primary", use_container_width=True): generate_ticket("Ben-Ret(C)", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with c2:
            if st.button("NO (Regular)", type="primary", use_container_width=True): generate_ticket("Ben-Ret(S)", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        st.button("⬅ CANCEL", on_click=lambda: st.session_state.update({'kiosk_step': 'mss'}))

    elif st.session_state['kiosk_step'] == 'ticket':
        t = st.session_state['last_ticket']
        bg = "#FFC107" if t['type'] == 'PRIORITY' else "#2563EB"
        col = "#0038A8" if t['type'] == 'PRIORITY' else "white"
        st.markdown(f"""
        <div class="ticket-card no-print" style='background:{bg}; color:{col}; padding:40px; border-radius:20px; text-align:center; margin:20px 0;'>
            <h1>{t['number']}</h1><h3>{t['service']}</h3><p>Please wait for the voice call.</p>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("❌ CANCEL", use_container_width=True): 
                db.tickets.remove(t); del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c2:
            if st.button("✅ DONE", type="primary", use_container_width=True): 
                del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c3:
            if st.button("🖨️ PRINT", use_container_width=True): 
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True); time.sleep(1); 
                del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()

# --- MODULE B: DISPLAY ---
def render_display():
    st.markdown(f"<h1 style='text-align: center; color: #0038A8;'>NOW SERVING</h1>", unsafe_allow_html=True)
    
    col_serve, col_queue = st.columns([3, 2])
    with col_serve:
        serving = [t for t in db.tickets if t["status"] == "SERVING"]
        if serving:
            for t in serving:
                b_col = "#2563EB" if t['lane'] == "E" else ("#DC2626" if t['lane'] == "T" else "#4B5563")
                ref = f" (Ref: {t['ref_from']})" if t.get('ref_from') else ""
                st.markdown(f"""
                <div class="serving-card">
                    <div style='font-size: 80px; font-weight: 900; color:{b_col};'>{t['number']}</div>
                    <div style='font-size: 40px; font-weight:bold;'>{t.get('served_by','Counter')}</div>
                    <div style='font-size: 20px; color:gray;'>{t['service']}{ref}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Waiting for next number...")
            
        parked = [t for t in db.tickets if t["status"] == "PARKED"]
        if parked:
            p = parked[0]
            timer_id = f"timer_{p['id']}"
            st.markdown(f"""
            <div class="recall-box">
                <h1 style='margin:0; font-size: 50px;'>⚠ RECALL: {p['number']}</h1>
                <h3>PLEASE PROCEED TO COUNTER</h3>
                <div id="{timer_id}" style="font-size:30px;">30:00</div>
                <script>startTimer(1800, "{timer_id}");</script>
            </div>""", unsafe_allow_html=True)

    with col_queue:
        st.markdown("### 🕒 NEXT IN QUEUE")
        waiting = [t for t in db.tickets if t["status"] == "WAITING"]
        waiting.sort(key=get_prio_score)
        
        st.markdown('<div class="queue-list">', unsafe_allow_html=True)
        if waiting:
            for t in waiting[:7]: 
                icon = "♿" if t['type'] == 'PRIORITY' else "👤"
                st.markdown(f"<div class='queue-item'><span>{icon} <b>{t['number']}</b></span> <span>{t['lane']} Lane</span></div>", unsafe_allow_html=True)
        else:
            st.write("Queue is empty.")
        st.markdown('</div>', unsafe_allow_html=True)

    txt = " | ".join(db.announcements)
    st.markdown(f"<div style='background: #FFD700; color: black; padding: 10px; font-weight: bold; position: fixed; bottom: 0; width: 100%; font-size:20px;'><marquee>{txt}</marquee></div>", unsafe_allow_html=True)
    time.sleep(3); st.rerun()

# --- MODULE C: COUNTER (With Time Logic & Appointments) ---
def render_counter(user):
    if 'my_station' not in st.session_state: st.session_state['my_station'] = db.config["counters"][0]
    
    st.sidebar.title(f"👮 {user['name']}")
    if st.sidebar.button("⬅ LOGOUT"): del st.session_state['user']; st.rerun()
    
    # SH/BH EXCLUSIVE: APPOINTMENT INJECTOR
    if user['role'] in ["SECTION_HEAD", "BRANCH_HEAD"]:
        with st.sidebar.expander("📅 Add Appointment"):
            with st.form("add_appt"):
                nm = st.text_input("Name"); svc = st.selectbox("Service", ["Pension", "Death", "Loan"])
                tm = st.time_input("Time")
                if st.form_submit_button("Book Slot"):
                    generate_ticket(svc, "C", True, is_appt=True, appt_name=nm)
                    st.success("Booked!")

    st.markdown(f"### Station: {st.session_state['my_station']}")
    st.session_state['my_station'] = st.selectbox("Switch Station", db.config["counters"], index=0)
    st.markdown("<hr>", unsafe_allow_html=True)

    station_type = st.session_state['my_station'].split()[0]
    my_lanes = db.config["assignments"].get(station_type, ["C"])
    
    queue = [t for t in db.tickets if t["status"] == "WAITING" and t["lane"] in my_lanes]
    queue.sort(key=get_prio_score)
    current = next((t for t in db.tickets if t["status"] == "SERVING" and t.get("served_by") == st.session_state['my_station']), None)
    
    if 'refer_modal' not in st.session_state: st.session_state['refer_modal'] = False

    c1, c2 = st.columns([2,1])
    with c1:
        if current:
            st.markdown(f"""<div style='padding:30px; background:#e0f2fe; border-radius:15px; border-left:10px solid #0369a1;'>
            <h1 style='margin:0; color:#0369a1; font-size: 80px;'>{current['number']}</h1>
            <h3>{current['service']}</h3></div>""", unsafe_allow_html=True)
            if current.get("ref_from"): st.markdown(f'<div class="ref-badge">↩ REFERRED FROM: {current["ref_from"]}</div>', unsafe_allow_html=True)
            
            if st.session_state['refer_modal']:
                with st.form("referral"):
                    target = st.selectbox("Transfer To", ["Teller", "Employer", "eCenter", "Counter"])
                    reason = st.text_input("Reason")
                    c_col1, c_col2 = st.columns(2)
                    with c_col1:
                        if st.form_submit_button("✅ CONFIRM TRANSFER"):
                            # TIME TRAVEL LOGIC
                            # If Current=Complex(C) -> Target=Teller(T/E/F/A) => BONUS (-30 mins)
                            # If Current=Simple(T/E/F/A) -> Target=Complex(C) => PENALTY (+45 mins)
                            current_lane = current['lane']
                            target_lane = {"Teller":"T", "Employer":"A", "eCenter":"E", "Counter":"C"}[target]
                            
                            if current_lane == "C" and target_lane != "C":
                                current['timestamp'] -= datetime.timedelta(minutes=30) # Boost
                            elif current_lane != "C" and target_lane == "C":
                                current['timestamp'] += datetime.timedelta(minutes=45) # Penalty
                                
                            current["lane"] = target_lane
                            current["status"] = "WAITING"
                            current["served_by"] = None
                            current["ref_from"] = st.session_state['my_station']
                            st.session_state['refer_modal'] = False; st.rerun()
                    with c_col2:
                        if st.form_submit_button("❌ CANCEL"):
                            st.session_state['refer_modal'] = False; st.rerun()
            else:
                st.markdown("<br>", unsafe_allow_html=True)
                b1, b2, b3 = st.columns(3)
                if b1.button("✅ COMPLETE", use_container_width=True): 
                    current["status"] = "COMPLETED"; current["end_time"] = datetime.datetime.now()
                    db.history.append(current); st.rerun()
                if b2.button("🅿️ PARK", use_container_width=True): 
                    current["status"] = "PARKED"; current["park_timestamp"] = datetime.datetime.now(); st.rerun()
                if b3.button("🔄 REFER", use_container_width=True): st.session_state['refer_modal'] = True; st.rerun()
        else:
            if st.button("🔊 CALL NEXT", type="primary", use_container_width=True):
                if queue:
                    nxt = queue[0]; nxt["status"] = "SERVING"; nxt["served_by"] = st.session_state['my_station']
                    nxt["start_time"] = datetime.datetime.now(); st.rerun()
                else: st.warning(f"No tickets for {station_type}.")
    with c2:
        count, avg_time = get_staff_efficiency(user['name'])
        st.metric("Performance", count, delta=avg_time + " avg/txn")
        st.divider()
        st.write("🅿️ Parked Tickets")
        parked = [t for t in db.tickets if t["status"] == "PARKED"]
        for p in parked:
            if st.button(f"🔊 {p['number']}", key=p['id']):
                p["status"] = "SERVING"; p["served_by"] = st.session_state['my_station']; st.rerun()

# --- MODULE D: ADMIN (Dynamic Config) ---
def render_admin_panel(user):
    st.title("🛠 Admin Console")
    if st.sidebar.button("⬅ LOGOUT"): del st.session_state['user']; st.rerun()
    
    # TABS: Users | Menu | Analytics (If BH/SH/DH)
    tabs = ["User Mgmt", "Menu Config"]
    if user['role'] in ["BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]: tabs.append("Analytics")
    
    active_tab = st.radio("Module", tabs, horizontal=True)
    st.divider()
    
    if active_tab == "User Mgmt":
        st.dataframe(pd.DataFrame.from_dict(db.staff, orient='index'))
        with st.form("add_user"):
            u_id = st.text_input("User ID"); u_name = st.text_input("Name")
            u_role = st.selectbox("Role", ["MSR", "TELLER", "AO", "SECTION_HEAD", "DIV_HEAD", "ADMIN"])
            if st.form_submit_button("Save User"):
                db.staff[u_id] = {"pass": "123", "role": u_role, "name": u_name}
                st.success("User Added")
                
    elif active_tab == "Menu Config":
        st.info("Edit Kiosk Buttons Here. Changes reflect instantly.")
        cat = st.selectbox("Select Category", list(db.menu.keys()))
        
        # Display Current Buttons
        current_btns = db.menu[cat]
        st.write(f"Buttons in {cat}:")
        for i, (label, code, lane) in enumerate(current_btns):
            c1, c2 = st.columns([4, 1])
            c1.text(f"{label} ({code}) -> Lane {lane}")
            if c2.button("🗑", key=f"del_{cat}_{i}"):
                db.menu[cat].pop(i); st.rerun()
        
        # Add New Button
        with st.form("new_btn"):
            n_lbl = st.text_input("Button Label")
            n_code = st.text_input("Service Code (e.g. Ben-Mat)")
            n_lane = st.selectbox("Target Lane", ["C", "E", "F", "T", "A"])
            if st.form_submit_button("Add Button"):
                db.menu[cat].append((n_lbl, n_code, n_lane))
                st.success("Added! Check Kiosk.")
                
    elif active_tab == "Analytics":
        st.subheader("📊 Branch Performance")
        if db.history:
            df = pd.DataFrame(db.history)
            st.write(df)
        else: st.info("No data yet.")

# ==========================================
# 5. ROUTER (Strict Role Enforcement)
# ==========================================
params = st.query_params
mode = params.get("mode")

if mode == "kiosk": render_kiosk()
elif mode == "staff":
    if 'user' not in st.session_state:
        st.title("Staff Login")
        u = st.text_input("Username"); p = st.text_input("Password", type="password")
        if st.button("Login"):
            acct = next((v for k,v in db.staff.items() if v["name"] == u or k == u), None)
            if acct: st.session_state['user'] = acct; st.rerun()
            else: st.error("Invalid")
    else:
        user = st.session_state['user']
        # ROUTING LOGIC
        if user['role'] in ["ADMIN", "DIV_HEAD"]: 
            render_admin_panel(user)
        elif user['role'] in ["BRANCH_HEAD", "SECTION_HEAD"]:
            # Hybrid Users: Can choose view
            view = st.sidebar.radio("Mode", ["Management", "Counter"])
            if view == "Management": render_admin_panel(user)
            else: render_counter(user)
        else:
            render_counter(user)
elif mode == "display": render_display()
else:
    # PUBLIC MOBILE
    if db.config["logo_url"].startswith("http"): st.image(db.config["logo_url"], width=50)
    st.title("G-ABAY Mobile Tracker")
    t1, t2, t3 = st.tabs(["🎫 Tracker", "💬 Ask G-ABAY", "⭐ Rate Us"])
    with t1:
        tn = st.text_input("Enter Ticket #")
        if tn:
            t = next((x for x in db.tickets if x["number"] == tn), None)
            if t:
                st.info(f"Status: {t['status']}")
                if t['status'] == "WAITING":
                    est = calculate_real_wait_time(t['lane'])
                    st.metric("Est. Wait", f"{est} mins")
            else: st.error("Not Found")
    with t2:
        st.write("Chatbot Demo")
    with t3:
        with st.form("rev"):
            rate = st.slider("Rating", 1, 5)
            pers = st.text_input("Personnel"); comm = st.text_area("Comments")
            if st.form_submit_button("Submit"): db.reviews.append({"rating": rate, "personnel": pers, "comment": comm}); st.success("Thanks!")
