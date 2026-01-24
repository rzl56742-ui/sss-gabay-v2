# ==============================================================================
# SSS G-ABAY v14.0 - BRANCH OPERATING SYSTEM (VERTICAL STACK EDITION)
# "World-Class Service, Zero-Install Architecture"
# COPYRIGHT: © 2026 rpt/sssgingoog
# ==============================================================================

import streamlit as st
import pandas as pd
import datetime
import time
import uuid
import base64

# ==========================================
# 1. SYSTEM CONFIGURATION & GLOBAL STATE
# ==========================================
st.set_page_config(page_title="SSS G-ABAY v14.0", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

# --- SINGLETON DATABASE (The "Glue") ---
@st.cache_resource
class SystemState:
    def __init__(self):
        self.tickets = []
        self.history = []
        self.reviews = []
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
            "assignments": {
                "Counter": ["C", "E", "F"],
                "Teller": ["T"],
                "Employer": ["A"],
                "eCenter": ["E"],
                "Help": ["F", "E"]
            },
            "counters": ["Counter 1", "Counter 2", "Counter 3", "Teller 1", "Teller 2", "Employer Desk", "eCenter", "Help Desk"]
        }
        self.staff = {
            "admin": {"pass": "sss2026", "role": "ADMIN", "name": "System Admin"},
            "head": {"pass": "head123", "role": "BRANCH_HEAD", "name": "Branch Head"},
            "c1": {"pass": "123", "role": "MSR", "name": "Maria Santos"},
            "c2": {"pass": "123", "role": "TELLER", "name": "Juan Cruz"}
        }
        self.announcements = ["Welcome to SSS Gingoog. Operating Hours: 8:00 AM - 5:00 PM."]

if 'system' not in st.session_state:
    st.session_state.system = SystemState()

db = st.session_state.system

# --- INDUSTRIAL CSS & JS ---
st.markdown("""
<script>
function startTimer(duration, display) {
    var timer = duration, minutes, seconds;
    setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
        display.textContent = minutes + ":" + seconds;
        if (--timer < 0) { timer = 0; }
    }, 1000);
}
</script>
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"][aria-expanded="false"] { display: none; }
    
    /* HEADER STYLES */
    .header-text { text-align: center; font-family: sans-serif; }
    .header-top { font-size: 14px; color: #555; text-transform: uppercase; letter-spacing: 2px; }
    .header-main { font-size: 40px; font-weight: 900; color: #0038A8; margin: 0; padding: 0; text-transform: uppercase; font-style: italic; }
    .header-branch { font-size: 30px; font-weight: 800; color: #333; margin-top: 5px; text-transform: uppercase; }
    
    /* MAIN MENU BUTTONS (HUGE) */
    .reg-card > button {
        background-color: #2563EB !important; color: white !important;
        height: 350px !important; width: 100% !important;
        border-radius: 30px !important; font-size: 40px !important;
        font-weight: 900 !important; border: 8px solid #1E40AF !important;
        text-transform: uppercase; box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .prio-card > button {
        background-color: #FFC107 !important; color: #1E3A8A !important;
        height: 350px !important; width: 100% !important;
        border-radius: 30px !important; font-size: 40px !important;
        font-weight: 900 !important; border: 8px solid #B45309 !important;
        text-transform: uppercase; box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    /* SUB-MENU BUTTONS (UNIFORM & COMPACT) */
    .sub-btn > button {
        height: 100px !important; width: 100% !important;
        font-size: 20px !important; font-weight: 700 !important;
        border-radius: 12px !important; border: 2px solid #ddd !important;
        background-color: white !important; color: #333 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 5px;
    }
    .sub-btn > button:hover {
        background-color: #f0f9ff !important;
        transform: translateY(-2px);
    }
    
    /* COLOR CODING */
    .btn-red > button { border-left: 10px solid #DC2626 !important; }
    .btn-orange > button { border-left: 10px solid #EA580C !important; }
    .btn-green > button { border-left: 10px solid #16A34A !important; }
    .btn-blue > button { border-left: 10px solid #2563EB !important; }

    /* SECTION HEADERS */
    .section-header {
        font-size: 24px; font-weight: bold; color: #444;
        margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #eee; padding-bottom: 5px;
    }

    /* DISPLAY MODULE STYLES */
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
    
    /* PRINT STYLES */
    @media print {
        @page { size: 4in 2in landscape; margin: 0; }
        body * { visibility: hidden; }
        .printable-ticket, .printable-ticket * { visibility: visible; }
        .printable-ticket {
            position: fixed; left: 0; top: 0; width: 100%; height: 100%;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            background: white; color: black; font-family: sans-serif;
            border: 5px solid black; padding: 10px;
        }
        .no-print { display: none !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC
# ==========================================
def generate_ticket(service, lane_code, is_priority, is_appt=False):
    prefix = "A" if is_appt else ("P" if is_priority else "R")
    count = len([t for t in db.tickets if t["lane"] == lane_code]) + 1
    ticket_num = f"{lane_code}{prefix}-{count:03d}"
    
    new_t = {
        "id": str(uuid.uuid4()), "number": ticket_num, "lane": lane_code,
        "service": service, "type": "PRIORITY" if is_priority else "REGULAR",
        "status": "WAITING", "timestamp": datetime.datetime.now(),
        "start_time": None, "end_time": None, "park_timestamp": None,
        "history": [], "served_by": None, "ref_from": None
    }
    db.tickets.append(new_t)
    return new_t

def get_prio_score(t):
    base = t["timestamp"].timestamp()
    bonus = 3600 if t.get("ref_from") else (1800 if t["type"] == "PRIORITY" else 0)
    return base - bonus

def calculate_real_wait_time(lane_code):
    recent = [t for t in db.history if t['lane'] == lane_code and t['end_time']]
    if not recent: return 15
    recent = recent[-10:]
    total_sec = sum([(t["end_time"] - t["start_time"]).total_seconds() for t in recent])
    avg_txn_time = (total_sec / len(recent)) / 60 
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

# --- MODULE A: KIOSK (Fixed Headers & Buttons) ---
def render_kiosk():
    # HEADERS
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
        col_reg, col_prio = st.columns([1, 1], gap="large")
        with col_reg:
            st.markdown('<div class="reg-card">', unsafe_allow_html=True)
            if st.button("👤 REGULAR\n\nStandard Access"):
                st.session_state['is_prio'] = False; st.session_state['kiosk_step'] = 'menu'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_prio:
            st.markdown('<div class="prio-card">', unsafe_allow_html=True)
            if st.button("❤️ PRIORITY\n\nSenior, PWD, Pregnant"):
                st.session_state['is_prio'] = True; st.session_state['kiosk_step'] = 'menu'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.warning("⚠ NOTICE: Non-priority users will be transferred to end of line.")

    elif st.session_state['kiosk_step'] == 'menu':
        st.markdown("### Select Service Category")
        st.markdown('<div class="grid-card">', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            if st.button("💳 PAYMENTS\n(Contrib/Loans)"):
                t = generate_ticket("Payment", "T", st.session_state['is_prio'])
                st.session_state['last_ticket'] = t; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with m2:
            if st.button("💼 EMPLOYERS\n(Account Mgmt)"):
                t = generate_ticket("Account Management", "A", st.session_state['is_prio'])
                st.session_state['last_ticket'] = t; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with m3:
            if st.button("👤 MEMBER SERVICES\n(Claims, ID, Records)"):
                st.session_state['kiosk_step'] = 'mss'; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ GO BACK", type="secondary", use_container_width=True): del st.session_state['kiosk_step']; st.rerun()

    elif st.session_state['kiosk_step'] == 'mss':
        st.markdown("### 👤 Member Services")
        
        # --- SECTION 1: BENEFITS (RED) ---
        st.markdown("<div class='section-header'>🏥 Benefit Claims</div>", unsafe_allow_html=True)
        st.markdown('<div class="sub-btn btn-red">', unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        with b1: 
            if st.button("Maternity/Sickness"): generate_ticket("Ben-Mat/Sick", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with b2:
            if st.button("Retirement/Death"): st.session_state['kiosk_step'] = 'gate_rd'; st.rerun()
        with b3:
            if st.button("Disability/Unemp."): generate_ticket("Ben-Dis/Unemp", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # --- SECTION 2: LOANS (ORANGE) ---
        st.markdown("<div class='section-header'>💰 Loans</div>", unsafe_allow_html=True)
        st.markdown('<div class="sub-btn btn-orange">', unsafe_allow_html=True)
        l1, l2, l3 = st.columns(3)
        with l1:
            if st.button("Salary/Conso"): generate_ticket("Ln-Sal/Conso", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with l2:
            if st.button("Calamity/Emerg."): generate_ticket("Ln-Cal/Emerg", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with l3:
            if st.button("Pension Loan"): generate_ticket("Ln-Pension", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # --- SECTION 3: RECORDS (GREEN) ---
        st.markdown("<div class='section-header'>📝 Member Data Change</div>", unsafe_allow_html=True)
        st.markdown('<div class="sub-btn btn-green">', unsafe_allow_html=True)
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            if st.button("Contact Update"): generate_ticket("Rec-Contact", "F", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with r2:
            if st.button("Simple Correct."): generate_ticket("Rec-Simple", "F", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with r3:
            if st.button("Complex Correct."): generate_ticket("Rec-Complex", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with r4:
            if st.button("Req. Verification"): generate_ticket("Rec-Verify", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # --- SECTION 4: eSERVICES (BLUE) ---
        st.markdown("<div class='section-header'>💻 eServices</div>", unsafe_allow_html=True)
        st.markdown('<div class="sub-btn btn-blue">', unsafe_allow_html=True)
        e1, e2, e3, e4 = st.columns(4)
        with e1:
            if st.button("My.SSS Reset"): generate_ticket("eSvc-Reset", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with e2:
            if st.button("SS Number"): generate_ticket("eSvc-SSNum", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with e3:
            if st.button("Status Inquiry"): generate_ticket("eSvc-Status", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with e4:
            if st.button("DAEM/ACOP"): generate_ticket("eSvc-DAEM/ACOP", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
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
            if st.button("❌ CANCEL", use_container_width=True): db.tickets.remove(t); del st.session_state['last_ticket']; st.session_state['kiosk_step']='menu'; st.rerun()
        with c2:
            if st.button("✅ DONE", type="primary", use_container_width=True): del st.session_state['last_ticket']; st.session_state['kiosk_step']='menu'; st.rerun()
        with c3:
            if st.button("🖨️ PRINT", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True); time.sleep(1); del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()

# --- MODULE B: DISPLAY (RESTORED QUEUE LIST) ---
def render_display():
    st.markdown(f"<h1 style='text-align: center; color: #0038A8;'>NOW SERVING</h1>", unsafe_allow_html=True)
    
    col_serve, col_queue = st.columns([3, 2])
    
    with col_serve:
        # SERVING CARD
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
            
        # PARKED SECTION
        parked = [t for t in db.tickets if t["status"] == "PARKED"]
        if parked:
            p = parked[0]
            st.markdown(f"""
            <div class="recall-box">
                <h1 style='margin:0; font-size: 50px;'>⚠ RECALL: {p['number']}</h1>
                <h3>PLEASE PROCEED TO COUNTER</h3>
                <div id="timer_{p['id']}" style="font-size:30px;">30:00</div>
                <script>startTimer(1800, document.querySelector('#timer_{p['id']}'));</script>
            </div>""", unsafe_allow_html=True)

    with col_queue:
        st.markdown("### 🕒 NEXT IN QUEUE")
        waiting = [t for t in db.tickets if t["status"] == "WAITING"]
        # Sort by priority
        waiting.sort(key=get_prio_score)
        
        st.markdown('<div class="queue-list">', unsafe_allow_html=True)
        if waiting:
            for t in waiting[:7]: # Show top 7
                icon = "♿" if t['type'] == 'PRIORITY' else "👤"
                st.markdown(f"<div class='queue-item'><span>{icon} <b>{t['number']}</b></span> <span>{t['lane']} Lane</span></div>", unsafe_allow_html=True)
        else:
            st.write("Queue is empty.")
        st.markdown('</div>', unsafe_allow_html=True)

    txt = " | ".join(db.announcements)
    st.markdown(f"<div style='background: #FFD700; color: black; padding: 10px; font-weight: bold; position: fixed; bottom: 0; width: 100%; font-size:20px;'><marquee>{txt}</marquee></div>", unsafe_allow_html=True)
    time.sleep(3); st.rerun()

# --- MODULE C: COUNTER ---
def render_counter(user):
    if 'my_station' not in st.session_state: st.session_state['my_station'] = db.config["counters"][0]
    
    st.sidebar.title(f"👮 {user['name']}")
    if st.sidebar.button("⬅ LOGOUT / SWITCH STATION"): del st.session_state['user']; st.rerun()
    
    on_break = st.sidebar.toggle("☕ Break Mode", value=user.get('break', False))
    if on_break != user.get('break', False): user['break'] = on_break; st.rerun()
    if on_break: st.warning("⛔ You are on break."); return

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
                    if st.form_submit_button("CONFIRM"):
                        lane_map = {"Teller": "T", "Employer": "A", "eCenter": "E", "Counter": "C"}
                        current["lane"] = lane_map[target]
                        current["status"] = "WAITING"
                        current["served_by"] = None
                        current["ref_from"] = st.session_state['my_station']
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

# --- MODULE D: ADMIN ---
def render_admin_panel(user):
    st.title("🛠 Admin Console")
    if st.sidebar.button("⬅ LOGOUT"): del st.session_state['user']; st.rerun()
    
    tab1, tab2 = st.tabs(["Users", "Config"])
    with tab1:
        st.dataframe(pd.DataFrame.from_dict(db.staff, orient='index'))
        with st.form("add_user"):
            u_id = st.text_input("User ID"); u_name = st.text_input("Name"); u_role = st.selectbox("Role", ["MSR", "TELLER", "ADMIN"])
            if st.form_submit_button("Save"):
                db.staff[u_id] = {"pass": "123", "role": u_role, "name": u_name}
                st.success("User Added!")
    with tab2:
        st.write("Lane Configuration")
        new_lane = st.text_input("Add Lane Code (e.g., S)")
        new_desc = st.text_input("Description")
        if st.button("Add Lane"):
            db.config["lanes"][new_lane] = {"name": new_desc, "desc": new_desc}
            st.success("Lane Added")

# ==========================================
# 5. ROUTER
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
        if user['role'] == "ADMIN": render_admin_panel(user)
        else: render_counter(user)
elif mode == "display": render_display()
else:
    # MOBILE DEFAULT (RESTORED COMPLETE FEATURES)
    if db.config["logo_url"].startswith("http"): st.image(db.config["logo_url"], width=50)
    else: st.markdown(f'<img src="data:image/png;base64,{db.config["logo_url"]}" width="50">', unsafe_allow_html=True)
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
        st.markdown("### 🤖 Chatbot")
        if "messages" not in st.session_state: st.session_state.messages = []
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if prompt := st.chat_input("Ask me..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            st.session_state.messages.append({"role": "assistant", "content": "Please proceed to PACD."})
    with t3:
        st.markdown("### Feedback")
        with st.form("rev"):
            rate = st.slider("Rating", 1, 5)
            pers = st.text_input("Name of Personnel")
            comm = st.text_area("Comments / Suggestions")
            if st.form_submit_button("Submit"):
                db.reviews.append({"rating": rate, "personnel": pers, "comment": comm})
                st.success("Thanks!")
