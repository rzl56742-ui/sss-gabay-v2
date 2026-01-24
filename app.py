# ==============================================================================
# SSS G-ABAY v10.0 - BRANCH OPERATING SYSTEM (PLATINUM EDITION)
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
st.set_page_config(page_title="SSS G-ABAY v10.0", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

# --- SINGLETON DATABASE (The "Glue" that connects all tabs) ---
@st.cache_resource
class SystemState:
    def __init__(self):
        self.tickets = []
        self.history = []
        self.reviews = []
        self.config = {
            "branch_name": "GINGOOG BRANCH",
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
                "Help Desk": ["F", "E"]
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

# Initialize once
if 'system' not in st.session_state:
    st.session_state.system = SystemState()

db = st.session_state.system

# --- INDUSTRIAL CSS & JS INJECTION ---
st.markdown("""
<script>
// REAL-TIME TIMER FOR PARKED TICKETS
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
    /* Global */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"][aria-expanded="false"] { display: none; }
    
    /* KIOSK BUTTONS */
    .reg-card > button {
        background-color: #2563EB !important; color: white !important;
        height: 350px !important; width: 100% !important;
        border-radius: 30px !important; font-size: 40px !important;
        font-weight: 900 !important; border: 6px solid #1E40AF !important;
        text-transform: uppercase;
    }
    .prio-card > button {
        background-color: #FFC107 !important; color: #1E3A8A !important;
        height: 350px !important; width: 100% !important;
        border-radius: 30px !important; font-size: 40px !important;
        font-weight: 900 !important; border: 6px solid #B45309 !important;
        text-transform: uppercase;
    }
    .grid-card > button {
        height: 150px !important; width: 100% !important;
        font-size: 20px !important; font-weight: 700 !important;
        border-radius: 15px !important; border: 2px solid #ddd !important;
        background-color: white !important; color: #333 !important;
    }

    /* DISPLAY MODULE STYLES */
    .serving-card {
        background-color: white; border-left: 15px solid #2563EB;
        padding: 20px; margin-bottom: 20px; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; justify-content: space-between;
    }
    .recall-box {
        background-color: #DC2626; color: white; padding: 30px;
        border-radius: 15px; text-align: center; animation: pulse 2s infinite;
    }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.8; } 100% { opacity: 1; } }
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. LOGIC CORE
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

# --- MODULE A: KIOSK ---
def render_kiosk():
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if db.config["logo_url"].startswith("http"): st.image(db.config["logo_url"], width=100)
        else: st.markdown(f'<img src="data:image/png;base64,{db.config["logo_url"]}" width="100">', unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; color:#0038A8; margin:0;'>SSS {db.config['branch_name']}</h1>", unsafe_allow_html=True)

    if 'kiosk_step' not in st.session_state:
        st.markdown("<br>", unsafe_allow_html=True)
        col_reg, col_prio = st.columns([1, 1], gap="large")
        with col_reg:
            st.markdown('<div class="reg-card">', unsafe_allow_html=True)
            if st.button("👤 REGULAR LANE\n\nStandard Access"):
                st.session_state['is_prio'] = False; st.session_state['kiosk_step'] = 'menu'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col_prio:
            st.markdown('<div class="prio-card">', unsafe_allow_html=True)
            if st.button("❤️ PRIORITY LANE\n\nSenior, PWD, Pregnant"):
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
        st.markdown('<div class="grid-card">', unsafe_allow_html=True)
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            if st.button("Maternity/Sickness"): generate_ticket("Ben-Mat/Sick", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Retirement/Death"): st.session_state['kiosk_step'] = 'gate_rd'; st.rerun()
            if st.button("Disability/Unemp."): generate_ticket("Ben-Dis/Unemp", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with g2:
            if st.button("Salary/Conso"): generate_ticket("Ln-Sal/Conso", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Calamity/Emergency"): generate_ticket("Ln-Cal/Emerg", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Pension Loan"): generate_ticket("Ln-Pension", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with g3:
            if st.button("Contact Update"): generate_ticket("Rec-Contact", "F", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Simple Corrections"): generate_ticket("Rec-Simple", "F", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Complex Correct."): generate_ticket("Rec-Complex", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Req. Verification"): generate_ticket("Rec-Verify", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with g4:
            if st.button("My.SSS Reset"): generate_ticket("eSvc-Reset", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("SS Number"): generate_ticket("eSvc-SSNum", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Status Inquiry"): generate_ticket("eSvc-Status", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("DAEM/ACOP"): generate_ticket("eSvc-DAEM/ACOP", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db.tickets[-1]; st.session_state['k
