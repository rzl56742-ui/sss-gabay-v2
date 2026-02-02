# ==============================================================================
# SSS G-ABAY v23.10 - BRANCH OPERATING SYSTEM (CORRECTED GRID EDITION)
# "Visuals: Ticket Hero | Logic: 6-Col Auto-Grid | Display: Nickname Only"
# COPYRIGHT: © 2026 rpt/sssgingoog
# ==============================================================================

import streamlit as st
import pandas as pd
import datetime
import time
import uuid
import json
import os
import math
import re
import html
import plotly.express as px
import urllib.parse
import io
import base64
import shutil
import glob

# ==============================================================================
# FILE LOCKING IMPORTS
# ==============================================================================
try:
    from filelock import FileLock, Timeout
    FILE_LOCK_AVAILABLE = True
except ImportError:
    FILE_LOCK_AVAILABLE = False

# ==========================================
# 1. SYSTEM CONFIGURATION & PERSISTENCE
# ==========================================
st.set_page_config(page_title="SSS G-ABAY v23.10", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

# ==============================================================================
# CONSTANTS
# ==============================================================================
UTC_OFFSET_HOURS = 8  # Philippine Standard Time (PST = UTC+8)
DATA_FILE = "sss_data.json"
BACKUP_FILE = "sss_data.bak"
ARCHIVE_FILE = "sss_archive.json"
LOCK_FILE = "sss_data.json.lock"
BACKUP_DIR = "backups"
MAX_HOURLY_BACKUPS = 24
ARCHIVE_RETENTION_DAYS = 365
SESSION_TIMEOUT_MINUTES = 30
PARK_GRACE_MINUTES = 60
AUDIT_LOG_MAX_ENTRIES = 10000
DEFAULT_AVG_TXN_MINUTES = 15

# --- LANE CONFIGURATION ---
LANE_CODES = {
    "T": {"name": "Teller", "desc": "Payments", "color": "#DC2626", "icon": "💳"},
    "A": {"name": "Employer", "desc": "Account Mgmt", "color": "#16A34A", "icon": "💼"},
    "C": {"name": "Counter", "desc": "Complex Trans", "color": "#2563EB", "icon": "👤"},
    "E": {"name": "eCenter", "desc": "Online Services", "color": "#2563EB", "icon": "💻"},
    "F": {"name": "Fast Lane", "desc": "Simple Trans", "color": "#2563EB", "icon": "⚡"}
}

LANE_NAME_TO_CODE = {"Teller": "T", "Employer": "A", "eCenter": "E", "Counter": "C", "Fast Lane": "F"}
LANE_CODE_TO_NAME = {v: k for k, v in LANE_NAME_TO_CODE.items()}
LANE_TO_CATEGORY = {"T": "PAYMENTS", "A": "EMPLOYERS", "C": "MEMBER SERVICES", "E": "MEMBER SERVICES", "F": "MEMBER SERVICES"}

TICKET_STATUSES = {
    "WAITING": {"label": "Waiting", "color": "#3B82F6", "desc": "In queue, awaiting service"},
    "SERVING": {"label": "Serving", "color": "#F59E0B", "desc": "Currently being served at counter"},
    "PARKED": {"label": "Parked", "color": "#EF4444", "desc": "Temporarily set aside, must return within grace period"},
    "COMPLETED": {"label": "Completed", "color": "#10B981", "desc": "Transaction successfully finished"},
    "NO_SHOW": {"label": "No Show", "color": "#6B7280", "desc": "Client did not return within grace period"},
    "EXPIRED": {"label": "Expired", "color": "#6B7280", "desc": "Ticket expired at midnight rollover"},
    "SYSTEM_CLOSED": {"label": "System Closed", "color": "#6B7280", "desc": "Auto-completed at midnight rollover"}
}

STAFF_ROLES = ["MSR", "TELLER", "AO", "SECTION_HEAD", "BRANCH_HEAD", "DIV_HEAD", "ADMIN"]
ADMIN_ROLES = ["ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]
COUNTER_ROLES = ["ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]

# ==============================================================================
# UTILITIES
# ==============================================================================
def get_ph_time():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=UTC_OFFSET_HOURS)

def sanitize_text(text):
    if not text: return ""
    return html.escape(str(text))

USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{3,20}$')
def validate_user_id(user_id):
    if not user_id: return False, "User ID cannot be empty"
    if not USER_ID_PATTERN.match(user_id): return False, "User ID must be 3-20 alphanumeric characters"
    return True, "Valid"

# --- DEFAULT DATA ---
DEFAULT_TRANSACTIONS = {
    "PAYMENTS": ["Contribution Payment", "Loan Payment", "Miscellaneous Payment", "Status Inquiry (Payments)"],
    "EMPLOYERS": ["Employer Registration", "Employee Update (R1A)", "Contribution/Loan List", "Status Inquiry (Employer)"],
    "MEMBER SERVICES": ["Sickness/Maternity Claim", "Pension Claim", "Death/Funeral Claim", "Salary Loan Application", "Calamity Loan", "Verification/Static Info", "UMID/Card Inquiry", "My.SSS Reset"]
}

DEFAULT_DATA = {
    "system_date": get_ph_time().strftime("%Y-%m-%d"),
    "branch_status": "NORMAL", 
    "latest_announcement": {"text": "", "id": ""},
    "tickets": [],
    "history": [],
    "breaks": [],
    "reviews": [],
    "incident_log": [],
    "audit_log": [],
    "transaction_master": DEFAULT_TRANSACTIONS,
    "resources": [
        {"type": "LINK", "label": "🌐 SSS Official Website", "value": "https://www.sss.gov.ph"},
        {"type": "LINK", "label": "💻 My.SSS Member Portal", "value": "https://member.sss.gov.ph/members/"},
        {"type": "FAQ", "label": "How to reset My.SSS password?", "value": "Please visit our e-Center."}
    ],
    "announcements": ["Welcome to SSS Gingoog. Operating Hours: 8:00 AM - 5:00 PM."],
    "exemptions": {
        "Retirement": ["Dropped/Cancelled SS Number", "Multiple SS Numbers", "Maintenance of records"],
        "Death": ["Claimant is not legal spouse/child", "Pending Case"],
        "Funeral": ["Receipt Issues"]
    },
    "config": {
        "branch_name": "BRANCH GINGOOG",
        "branch_code": "H07",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Social_Security_System_%28SSS%29.svg/1200px-Social_Security_System_%28SSS%29.svg.png",
        "lanes": {
            "T": {"name": "Teller", "desc": "Payments"},
            "A": {"name": "Employer", "desc": "Account Mgmt"},
            "C": {"name": "Counter", "desc": "Complex Trans"},
            "E": {"name": "eCenter", "desc": "Online Services"},
            "F": {"name": "Fast Lane", "desc": "Simple Trans"}
        },
        "assignments": {
            "Counter": ["C", "F", "E"],
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
            ("Disability / Unemployment", "Ben-Dis/Unemp", "E"),
            ("Retirement", "Ben-Retirement", "GATE"), 
            ("Death", "Ben-Death", "GATE"),        
            ("Funeral", "Ben-Funeral", "GATE")     
        ],
        "Loans": [
            ("Salary / Conso", "Ln-Sal/Conso", "E"),
            ("Calamity / Emergency", "Ln-Cal/Emerg", "E"),
            ("Pension Loan", "Ln-Pension", "E")
        ],
        "Member Records": [
            ("Contact Info Update", "Rec-Contact", "F"),
            ("Simple Correction", "Rec-Simple", "F"),
            ("Complex Correction", "Rec-Complex", "C"),
            ("Verification", "Rec-Verify", "C")
        ],
        "eServices": [
            ("My.SSS Reset", "eSvc-Reset", "E"),
            ("SS Number", "eSvc-SSNum", "E"),
            ("Status Inquiry", "eSvc-Status", "E"),
            ("DAEM / ACOP", "eSvc-DAEM/ACOP", "E")
        ]
    },
    "staff": {
        "admin": {"pass": "sss2026", "role": "ADMIN", "name": "System Admin", "nickname": "Admin", "default_station": "Counter 1", "status": "ACTIVE", "online": False},
    }
}

# --- DATABASE ENGINE ---
def acquire_file_lock(timeout=10):
    if FILE_LOCK_AVAILABLE: return FileLock(LOCK_FILE, timeout=timeout)
    return None

def create_hourly_backup():
    if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
    timestamp = get_ph_time().strftime("%Y%m%d_%H")
    backup_file = os.path.join(BACKUP_DIR, f"sss_data_{timestamp}.json")
    if os.path.exists(DATA_FILE) and not os.path.exists(backup_file):
        shutil.copy2(DATA_FILE, backup_file)
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "sss_data_*.json")))
    while len(backups) > MAX_HOURLY_BACKUPS:
        try: os.remove(backups.pop(0))
        except: pass

def load_db():
    current_date = get_ph_time().strftime("%Y-%m-%d")
    lock = acquire_file_lock()
    try:
        if lock: lock.acquire()
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                try: data = json.load(f)
                except: 
                    if os.path.exists(BACKUP_FILE):
                        with open(BACKUP_FILE, "r") as bf: data = json.load(bf)
                    else: data = DEFAULT_DATA
        else: data = DEFAULT_DATA

        if "PAYMENTS" in data.get("menu", {}): data["menu"] = DEFAULT_DATA["menu"]
        for key in DEFAULT_DATA:
            if key not in data: data[key] = DEFAULT_DATA[key]
        if "branch_code" not in data['config']: data['config']['branch_code'] = "H07"
        if "transaction_master" not in data: data['transaction_master'] = DEFAULT_TRANSACTIONS
        if "audit_log" not in data: data['audit_log'] = []

        if data["system_date"] != current_date:
            serving_tickets = [t for t in data['tickets'] if t['status'] == 'SERVING']
            for ticket in serving_tickets:
                ticket['status'] = 'SYSTEM_CLOSED'
                ticket['end_time'] = get_ph_time().isoformat()
                ticket['auto_closed'] = True
                ticket['auto_close_reason'] = 'MIDNIGHT_ROLLOVER'
                data['history'].append(ticket)
            
            pending_tickets = [t for t in data['tickets'] if t['status'] in ['WAITING', 'PARKED']]
            for ticket in pending_tickets:
                ticket['status'] = 'EXPIRED'
                ticket['end_time'] = get_ph_time().isoformat()
                ticket['auto_closed'] = True
                ticket['auto_close_reason'] = 'MIDNIGHT_EXPIRY'
                data['history'].append(ticket)
            
            data['tickets'] = []
            
            archive_data = []
            if os.path.exists(ARCHIVE_FILE):
                with open(ARCHIVE_FILE, "r") as af:
                    try: archive_data = json.load(af)
                    except: archive_data = []
            
            archive_entry = {
                "date": data["system_date"],
                "history": data["history"],
                "reviews": data["reviews"],
                "incident_log": data.get("incident_log", []),
                "audit_log": data.get("audit_log", []),
                "breaks": data["breaks"]
            }
            archive_data.append(archive_entry)
            
            cutoff_date = (get_ph_time() - datetime.timedelta(days=ARCHIVE_RETENTION_DAYS)).strftime("%Y-%m-%d")
            archive_data = [entry for entry in archive_data if entry.get('date', '9999-99-99') >= cutoff_date]
            
            with open(ARCHIVE_FILE, "w") as af: json.dump(archive_data, af, default=str)
                
            data["history"] = []
            data["breaks"] = []
            data["reviews"] = []
            data["incident_log"] = []
            data["audit_log"] = []
            data["system_date"] = current_date
            data["branch_status"] = "NORMAL"
            
            for uid in data['staff']:
                data['staff'][uid]['status'] = "ACTIVE"
                data['staff'][uid]['online'] = False
                if 'break_reason' in data['staff'][uid]: del data['staff'][uid]['break_reason']

        return data
    finally:
        if lock and lock.is_locked: lock.release()

def save_db(data):
    lock = acquire_file_lock()
    try:
        if lock: lock.acquire()
        create_hourly_backup()
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w") as f: json.dump(data, f, default=str)
        if os.path.exists(DATA_FILE): shutil.copy2(DATA_FILE, BACKUP_FILE)
        os.replace(temp_file, DATA_FILE)
    finally:
        if lock and lock.is_locked: lock.release()

def log_audit(action, user_name, details=None, target=None):
    local_db = load_db()
    if 'audit_log' not in local_db: local_db['audit_log'] = []
    entry = {
        "timestamp": get_ph_time().isoformat(),
        "action": action,
        "user": user_name,
        "target": target,
        "details": details,
        "session_id": st.session_state.get('session_id', 'unknown')
    }
    local_db['audit_log'].append(entry)
    if len(local_db['audit_log']) > AUDIT_LOG_MAX_ENTRIES: 
        local_db['audit_log'] = local_db['audit_log'][-AUDIT_LOG_MAX_ENTRIES:]
    save_db(local_db)

db = load_db()

# --- INIT ---
if 'surge_mode' not in st.session_state: st.session_state['surge_mode'] = False
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())[:8]
if 'last_activity' not in st.session_state: st.session_state['last_activity'] = get_ph_time()

def update_activity():
    st.session_state['last_activity'] = get_ph_time()

def check_session_timeout():
    if 'user' not in st.session_state: return False
    elapsed = (get_ph_time() - st.session_state.get('last_activity', get_ph_time())).total_seconds() / 60
    login_date = st.session_state.get('login_date', '')
    current_date = get_ph_time().strftime("%Y-%m-%d")
    
    if elapsed >= SESSION_TIMEOUT_MINUTES:
        handle_safe_logout(reason="TIMEOUT"); return True
    if login_date and login_date != current_date:
        handle_safe_logout(reason="DATE_ROLLOVER"); return True
    return False

def handle_safe_logout(reason="MANUAL"):
    if 'user' not in st.session_state: return
    local_db = load_db()
    user = st.session_state['user']
    user_key = next((k for k, v in local_db['staff'].items() if v['name'] == user['name']), None)
    
    if user_key:
        station = local_db['staff'][user_key].get('default_station', '')
        serving_ticket = next((t for t in local_db['tickets'] if t['status'] == 'SERVING' and t.get('served_by_staff') == user['name']), None)
        
        if not serving_ticket:
             station = local_db['staff'][user_key].get('default_station', '')
             serving_ticket = next((t for t in local_db['tickets'] if t['status'] == 'SERVING' and t.get('served_by') == station), None)

        if serving_ticket:
            serving_ticket['status'] = 'PARKED'
            serving_ticket['park_timestamp'] = get_ph_time().isoformat()
            serving_ticket['auto_parked'] = True
            serving_ticket['auto_park_reason'] = f'STAFF_LOGOUT_{reason}'
        
        local_db['staff'][user_key]['online'] = False
        save_db(local_db)
        log_audit("LOGOUT", user['name'], details=f"Reason: {reason}", target=station)
    
    for key in ['refer_modal', 'my_station', 'user', 'login_date']:
        if key in st.session_state: del st.session_state[key]

# --- CSS (JUMBO EDITION - OPTIMIZED FOR 6-COL GRID) ---
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
        if (--timer < 0) { clearInterval(interval); display.textContent = "EXPIRED"; display.style.color = "red"; }
    }, 1000);
}
</script>
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"][aria-expanded="false"] { display: none; }
    .header-text { text-align: center; font-family: sans-serif; }
    .header-branch { font-size: 30px; font-weight: 800; color: #333; margin-top: 5px; text-transform: uppercase; }
    .brand-footer { position: fixed; bottom: 5px; left: 10px; font-family: monospace; font-size: 12px; color: #888; opacity: 0.7; pointer-events: none; z-index: 9999; }
    
    /* JUMBO CARD CSS - 6 COL GRID OPTIMIZED */
    .serving-card-jumbo { 
        background: white; 
        border-radius: 15px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.15); 
        text-align: center; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
        height: 100%;
        width: 100%;
        overflow: hidden;
        padding: 5px;
    }
    
    /* LEVEL 1: TICKET NUMBER (BIGGEST, 10vw for 6-col fit) */
    .jumbo-ticket {
        font-size: 10vw !important;
        font-weight: 900 !important;
        line-height: 1.0 !important;
        margin: 0 !important;
        padding: 10px 0 !important;
    }
    
    /* LEVEL 2: COUNTER NAME (2vw) */
    .jumbo-counter {
        font-size: 2vw !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        color: #333;
        margin-bottom: 0px !important;
        line-height: 1.2 !important;
    }
    
    /* LEVEL 3: STAFF NICKNAME (1.5vw, Normal Weight) */
    .jumbo-staff {
        font-size: 1.5vw !important;
        font-weight: 400 !important;
        color: #666;
        margin-top: 0px !important;
    }
    
    .serving-card-break { 
        background: #FEF3C7; 
        border: 5px solid #D97706; 
        border-radius: 20px; 
        height: 100%;
        display: flex; flex-direction: column; justify-content: center; text-align: center;
    }
    .serving-card-break h3 { font-size: 4vw; color: #D97706; margin: 0; }
    
    .swim-col { background: #f8f9fa; border-radius: 10px; padding: 10px; border-top: 10px solid #ccc; height: 100%; }
    .swim-col h3 { text-align: center; margin-bottom: 10px; font-size: 18px; text-transform: uppercase; color: #333; }
    .queue-item { background: white; border-bottom: 1px solid #ddd; padding: 15px; margin-bottom: 5px; border-radius: 5px; display: flex; justify-content: space-between; }
    .queue-item span { font-size: 24px; font-weight: 900; color: #111; }
    
    .park-appt { background: #dbeafe; color: #1e40af; border-left: 5px solid #2563EB; font-weight: bold; padding: 10px; border-radius: 5px; display: flex; justify-content: space-between; margin-bottom: 5px; }
    .gate-btn > button { height: 350px !important; width: 100% !important; font-size: 40px !important; font-weight: 900 !important; border-radius: 30px !important; }
    .menu-card > button { height: 300px !important; width: 100% !important; font-size: 30px !important; font-weight: 800 !important; border-radius: 20px !important; border: 4px solid #ddd !important; white-space: pre-wrap !important;}
    .swim-btn > button { height: 100px !important; width: 100% !important; font-size: 18px !important; font-weight: 700 !important; text-align: left !important; padding-left: 20px !important; }
    
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    .blink-active { animation: blink 1s infinite; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC
# ==========================================
def get_display_name(staff_data):
    return staff_data.get('nickname') if staff_data.get('nickname') else staff_data['name']

def calculate_lane_wait_estimate(lane_code):
    local_db = load_db()
    waiting_count = len([t for t in local_db['tickets'] if t['lane'] == lane_code and t['status'] == "WAITING"])
    recent = [t for t in local_db['history'] if t['lane'] == lane_code and t.get('end_time') and t.get('start_time')]
    avg_txn_time = DEFAULT_AVG_TXN_MINUTES
    if recent:
        total_sec = 0; valid_count = 0
        for t in recent[-20:]:
            try:
                start = datetime.datetime.fromisoformat(t["start_time"])
                end = datetime.datetime.fromisoformat(t["end_time"])
                diff = (end - start).total_seconds()
                if diff > 0 and diff < 7200: total_sec += diff; valid_count += 1
            except: continue
        if valid_count > 0: avg_txn_time = (total_sec / valid_count) / 60
    active_counters = 0
    for staff in local_db['staff'].values():
        if staff.get('online') and staff.get('status') == 'ACTIVE':
            station = staff.get('default_station', '')
            counter_obj = next((c for c in local_db['config']['counter_map'] if c['name'] == station), None)
            if counter_obj:
                station_type = counter_obj['type']
                station_lanes = local_db['config']['assignments'].get(station_type, [])
                if lane_code in station_lanes: active_counters += 1
    if active_counters > 0: wait_time = round((waiting_count * avg_txn_time) / active_counters)
    else: wait_time = round(waiting_count * avg_txn_time)
    return waiting_count, wait_time, active_counters

def generate_ticket_callback(service, lane_code, is_priority):
    local_db = load_db()
    global_count = len(local_db['tickets']) + len(local_db['history']) + 1
    branch_code = local_db['config'].get('branch_code', 'H07')
    simple_num = f"{global_count:03d}"
    full_id = f"{branch_code}-{lane_code}-{simple_num}" 
    new_t = {
        "id": str(uuid.uuid4()), "number": simple_num, "full_id": full_id, "lane": lane_code, "service": service, 
        "type": "PRIORITY" if is_priority else "REGULAR", "status": "WAITING", 
        "timestamp": get_ph_time().isoformat(), "start_time": None, "end_time": None, "park_timestamp": None,
        "history": [], "served_by": None, "ref_from": None, "referral_reason": None,
        "appt_name": None, "appt_time": None, "actual_transactions": [] 
    }
    local_db['tickets'].append(new_t)
    save_db(local_db)
    st.session_state['last_ticket'] = new_t
    st.session_state['kiosk_step'] = 'ticket'

def generate_ticket_manual(service, lane_code, is_priority, is_appt=False, appt_name=None, appt_time=None, assign_counter=None):
    local_db = load_db()
    global_count = len(local_db['tickets']) + len(local_db['history']) + 1
    branch_code = local_db['config'].get('branch_code', 'H07')
    simple_num = f"{global_count:03d}"
    display_num = f"APT-{simple_num}" if is_appt else simple_num
    full_id = f"{branch_code}-{lane_code}-{display_num}"
    new_t = {
        "id": str(uuid.uuid4()), "number": display_num, "full_id": full_id, "lane": lane_code, "service": service, 
        "type": "APPOINTMENT" if is_appt else ("PRIORITY" if is_priority else "REGULAR"),
        "status": "WAITING", "timestamp": get_ph_time().isoformat(), "start_time": None, "end_time": None, "park_timestamp": None,
        "history": [], "served_by": None, "ref_from": None, "referral_reason": None,
        "appt_name": appt_name, "appt_time": str(appt_time) if appt_time else None,
        "assigned_to": assign_counter, "actual_transactions": []
    }
    local_db['tickets'].append(new_t)
    save_db(local_db)
    return new_t

def log_incident(user_name, status_type):
    local_db = load_db()
    local_db['branch_status'] = status_type
    entry = {"timestamp": get_ph_time().isoformat(), "staff": user_name, "type": status_type, "action": "Reported Issue" if status_type != "NORMAL" else "Restored System"}
    if 'incident_log' not in local_db: local_db['incident_log'] = []
    local_db['incident_log'].append(entry)
    msg = "System operations restored."
    if status_type == "OFFLINE": msg = "We are experiencing system difficulties."
    elif status_type == "SLOW": msg = "Notice: Intermittent connection."
    local_db['latest_announcement'] = {"text": msg, "id": str(uuid.uuid4())}
    save_db(local_db)
    log_audit("INCIDENT_REPORT", user_name, details=f"Status changed to {status_type}")

def get_next_ticket(queue, surge_mode, my_station):
    if not queue: return None
    queue.sort(key=get_queue_sort_key)
    now = get_ph_time().time()
    for t in queue:
        if t.get('assigned_to') == my_station:
            if t['type'] == 'APPOINTMENT' and t['appt_time']:
                appt_t = datetime.datetime.strptime(t['appt_time'], "%H:%M:%S").time()
                if now >= appt_t: return t
            else: return t
    for t in queue:
        if t['type'] == 'APPOINTMENT' and t['appt_time'] and not t.get('assigned_to'):
            appt_t = datetime.datetime.strptime(t['appt_time'], "%H:%M:%S").time()
            if now >= appt_t: return t
    if surge_mode:
        for t in queue:
            if t['type'] == 'PRIORITY' and not t.get('assigned_to'): return t
    local_db = load_db()
    last_2 = local_db['history'][-2:]
    p_count = sum(1 for t in last_2 if t['type'] == 'PRIORITY')
    if p_count == 2:
        reg = [t for t in queue if t['type'] == 'REGULAR' and not t.get('assigned_to')]
        if reg: return reg[0]
    for t in queue:
        if not t.get('assigned_to'): return t
    return None

def trigger_audio(ticket_num, counter_name):
    local_db = load_db()
    spoken_text = f"Priority Ticket... " if "P" in ticket_num or "APT" in ticket_num else "Ticket... "
    clean_num = ticket_num.replace("-", " ").replace("APT", "Appointment")
    spelled_out = "".join([f"{char}... " if char.isdigit() else f"{char}... " for char in clean_num])
    spoken_text += f"{spelled_out} please proceed to... {counter_name}."
    local_db['latest_announcement'] = {"text": spoken_text, "id": str(uuid.uuid4())}
    save_db(local_db)

def get_queue_sort_key(t):
    assigned_weight = 0 if t.get('assigned_to') else 1
    type_weight = 1 if t['type'] == 'APPOINTMENT' else (2 if t['type'] == 'PRIORITY' else 3)
    return (assigned_weight, type_weight, t['timestamp'])

def calculate_specific_wait_time(ticket_id, lane_code):
    local_db = load_db()
    recent = [t for t in local_db['history'] if t['lane'] == lane_code and t['end_time']]
    avg_txn_time = DEFAULT_AVG_TXN_MINUTES
    if recent:
        total_sec = sum([datetime.datetime.fromisoformat(t["end_time"]).timestamp() - datetime.datetime.fromisoformat(t["start_time"]).timestamp() for t in recent[-10:]])
        avg_txn_time = (total_sec / len(recent[-10:])) / 60
    waiting_in_lane = [t for t in local_db['tickets'] if t['lane'] == lane_code and t['status'] == "WAITING"]
    waiting_in_lane.sort(key=get_queue_sort_key)
    position = 0
    for i, t in enumerate(waiting_in_lane):
        if t['id'] == ticket_id: position = i; break
    wait_time = round(position * avg_txn_time)
    if wait_time < 2: return "Next"
    return f"{wait_time} min"

def calculate_people_ahead(ticket_id, lane_code):
    local_db = load_db()
    waiting_in_lane = [t for t in local_db['tickets'] if t['lane'] == lane_code and t['status'] == "WAITING"]
    waiting_in_lane.sort(key=get_queue_sort_key)
    for i, t in enumerate(waiting_in_lane):
        if t['id'] == ticket_id: return i
    return 0

def get_staff_efficiency(staff_name):
    local_db = load_db()
    my_txns = [t for t in local_db['history'] if t.get("served_by") == staff_name]
    if my_txns:
        total_handle_time = 0; valid_count = 0
        for t in my_txns:
            if t.get('start_time') and t.get('end_time'):
                try:
                    start = datetime.datetime.fromisoformat(t['start_time'])
                    end = datetime.datetime.fromisoformat(t['end_time'])
                    total_handle_time += (end - start).total_seconds(); valid_count += 1
                except: pass
        if valid_count > 0:
            avg_mins = round(total_handle_time / valid_count / 60)
            return len(my_txns), f"{avg_mins}m"
    return len(my_txns), "N/A"

def get_allowed_counters(role):
    all_counters = db['config']['counter_map']
    target_types = []
    if role == "TELLER": target_types = ["Teller"]
    elif role == "AO": target_types = ["Employer"]
    elif role == "MSR": target_types = ["Counter", "eCenter", "Help"]
    elif role in COUNTER_ROLES: return [c['name'] for c in all_counters] 
    return [c['name'] for c in all_counters if c['type'] in target_types]

def clear_ticket_modal_states():
    modal_keys = ['refer_modal', 'transfer_in_progress']
    for key in modal_keys:
        if key in st.session_state: del st.session_state[key]

def get_lane_color(lane_code):
    return LANE_CODES.get(lane_code, {}).get('color', '#2563EB')

# ==========================================
# 4. MODULES
# ==========================================

def render_kiosk():
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
            waiting, wait_min, counters = calculate_lane_wait_estimate("T")
            st.markdown('<div class="menu-card">', unsafe_allow_html=True)
            if st.button("💳 PAYMENTS\n(Contri/Loans)"):
                generate_ticket_callback("Payment", "T", st.session_state['is_prio']); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='wait-estimate'><h3>~{wait_min} min</h3><p>{waiting} in queue • {counters} counter(s)</p></div>", unsafe_allow_html=True)
        with m2:
            waiting, wait_min, counters = calculate_lane_wait_estimate("A")
            st.markdown('<div class="menu-card">', unsafe_allow_html=True)
            if st.button("💼 EMPLOYERS\n(Account Management)"):
                generate_ticket_callback("Account Management", "A", st.session_state['is_prio']); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='wait-estimate'><h3>~{wait_min} min</h3><p>{waiting} in queue • {counters} counter(s)</p></div>", unsafe_allow_html=True)
        with m3:
            waiting_c, wait_c, counters_c = calculate_lane_wait_estimate("C")
            waiting_e, wait_e, counters_e = calculate_lane_wait_estimate("E")
            waiting_f, wait_f, counters_f = calculate_lane_wait_estimate("F")
            total_waiting = waiting_c + waiting_e + waiting_f
            total_counters = counters_c + counters_e + counters_f
            avg_wait = round((wait_c + wait_e + wait_f) / 3) if total_counters > 0 else round((total_waiting * DEFAULT_AVG_TXN_MINUTES))
            st.markdown('<div class="menu-card">', unsafe_allow_html=True)
            if st.button("👤 MEMBER SERVICES\n(Claims, Requests, Updates)"):
                st.session_state['kiosk_step'] = 'mss'; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='wait-estimate'><h3>~{avg_wait} min</h3><p>{total_waiting} in queue • {total_counters} counter(s)</p></div>", unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("⬅ GO BACK", type="secondary", use_container_width=True): del st.session_state['kiosk_step']; st.rerun()
    elif st.session_state['kiosk_step'] == 'mss':
        st.markdown("### 👤 Member Services")
        cols = st.columns(4, gap="small")
        categories = list(db['menu'].keys())
        colors = ["red", "orange", "green", "blue", "red", "orange"]
        icons = ["🏥", "💰", "📝", "💻", "❓", "⚙️"]
        for i, cat_name in enumerate(categories):
            with cols[i % 4]:
                color = colors[i % len(colors)]
                icon = icons[i % len(icons)]
                st.markdown(f"<div class='swim-header head-{color}'>{icon} {cat_name}</div>", unsafe_allow_html=True)
                st.markdown(f'<div class="swim-btn border-{color}">', unsafe_allow_html=True)
                for label, code, lane in db['menu'].get(cat_name, []):
                    if st.button(label, key=label):
                        if lane == "GATE":
                            st.session_state['gate_target'] = {"label": label, "code": code}
                            st.session_state['kiosk_step'] = 'gate_check'; st.rerun()
                        else:
                            generate_ticket_callback(code, lane, st.session_state['is_prio']); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ GO BACK", type="secondary", use_container_width=True): st.session_state['kiosk_step'] = 'menu'; st.rerun()
    elif st.session_state['kiosk_step'] == 'gate_check':
        target = st.session_state.get('gate_target', {})
        label = target.get('label', 'Transaction')
        exemptions = db['exemptions'].get(target.get('label', ''), [])
        st.warning(f"⚠️ PRE-QUALIFICATION FOR {label.upper()}")
        for ex in exemptions: st.markdown(f"- {ex}")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📂 YES, I have one of these issues", type="primary", use_container_width=True):
                generate_ticket_callback(f"{label} (Complex)", "C", st.session_state['is_prio']); st.rerun()
        with c2:
            if st.button("💻 NO, none of these apply to me", type="primary", use_container_width=True):
                generate_ticket_callback(f"{label} (Online)", "E", st.session_state['is_prio']); st.rerun()
        if st.button("⬅ CANCEL"): st.session_state['kiosk_step'] = 'mss'; st.rerun()
    elif st.session_state['kiosk_step'] == 'ticket':
        t = st.session_state['last_ticket']
        bg = "#FFC107" if t['type'] == 'PRIORITY' else "#2563EB"
        col = "#0038A8" if t['type'] == 'PRIORITY' else "white"
        print_dt = get_ph_time().strftime("%B %d, %Y - %I:%M %p")
        waiting, wait_min, counters = calculate_lane_wait_estimate(t['lane'])
        c_left, c_right = st.columns([2, 1])
        with c_left:
            st.markdown(f"""<div class="ticket-card no-print" style='background:{bg}; color:{col}; padding:40px; border-radius:20px; text-align:center; margin:20px 0;'><h1>{t['number']}</h1><h3>{t['service']}</h3><p style="font-size:18px;">{print_dt}</p></div>""", unsafe_allow_html=True)
            st.markdown(f"<div class='wait-estimate'><h3>Estimated Wait: ~{wait_min} min</h3><p>{waiting} people ahead • {counters} counter(s) active</p></div>", unsafe_allow_html=True)
        with c_right:
            base_url = st.query_params.get("base_url", "http://192.168.1.X:8501")
            if isinstance(base_url, list): base_url = base_url[0]
            st.markdown(f"<div style='text-align:center; margin-top:30px; font-weight:bold;'>TRACK YOUR TICKET<br><br>Scan or Go To:<br><span style='color:blue;'>{base_url}</span><br>Enter: {t['number']}</div>", unsafe_allow_html=True)
        if t['type'] == 'PRIORITY': st.error("**⚠ PRIORITY LANE:** For Seniors, PWDs, Pregnant ONLY.")
        st.markdown(f"<h4 style='color:red; text-align:center;'>⚠ POLICY: Ticket forfeited if parked for {PARK_GRACE_MINUTES} MINUTES.</h4>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("❌ CANCEL", use_container_width=True): curr_db = load_db(); curr_db['tickets'] = [x for x in curr_db['tickets'] if x['id'] != t['id']]; save_db(curr_db); del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c2:
            if st.button("✅ DONE", type="primary", use_container_width=True): del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c3:
            if st.button("🖨️ PRINT", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True); time.sleep(1); del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
    st.markdown("<div class='brand-footer'>System developed by RPT/SSSGingoog © 2026 | v23.10</div>", unsafe_allow_html=True)

def render_display():
    check_session_timeout()
    local_db = load_db()
    audio_script = ""
    current_audio = local_db.get('latest_announcement', {})
    last_audio_id = st.session_state.get('last_audio_id', "")
    if current_audio.get('id') != last_audio_id and current_audio.get('text'):
        st.session_state['last_audio_id'] = current_audio['id']
        text_safe = sanitize_text(current_audio['text']).replace("'", "")
        audio_script = f"""<script>var msg = new SpeechSynthesisUtterance(); msg.text = "{text_safe}"; msg.rate = 1.0; msg.pitch = 1.1; var voices = window.speechSynthesis.getVoices(); var fVoice = voices.find(v => v.name.includes('Female') || v.name.includes('Zira')); if(fVoice) msg.voice = fVoice; window.speechSynthesis.speak(msg);</script>"""
    placeholder = st.empty()
    with placeholder.container():
        if audio_script: st.markdown(audio_script, unsafe_allow_html=True)
        status = local_db.get('branch_status', 'NORMAL')
        if status != "NORMAL":
            color = "red" if status == "OFFLINE" else "orange"
            text = "⚠ SYSTEM OFFLINE: MANUAL PROCESSING" if status == "OFFLINE" else "⚠ INTERMITTENT CONNECTION"
            st.markdown(f"<h2 style='text-align:center; color:{color}; animation: blink 1.5s infinite;'>{text}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; color: #0038A8;'>NOW SERVING</h1>", unsafe_allow_html=True)
        
        active_staff_list = [s for s in local_db['staff'].values() if s.get('online') is True and s['role'] != "ADMIN" and s['name'] != "System Admin"]
        
        if not active_staff_list: st.warning("Waiting for staff to log in...")
        else:
            # FIX: RESTORE 6-COL GRID
            cols_per_row = 6
            count = len(active_staff_list)
            num_rows = math.ceil(count / cols_per_row)
            card_height = 65 // num_rows
            
            for i in range(0, count, cols_per_row):
                batch = active_staff_list[i:i+cols_per_row]
                cols = st.columns(len(batch))
                for idx, staff in enumerate(batch):
                    with cols[idx]:
                        nickname = get_display_name(staff); station_name = staff.get('default_station', 'Unassigned'); style_str = f"height: {card_height}vh;"
                        if staff.get('status') == "ON_BREAK": 
                            st.markdown(f"""
                            <div class="serving-card-break" style="{style_str}">
                                <div class="jumbo-counter">{sanitize_text(station_name)}</div>
                                <h3 style="margin:0; font-size:4vw; color:#D97706;">ON BREAK</h3>
                                <div class="jumbo-staff">{sanitize_text(nickname)}</div>
                            </div>""", unsafe_allow_html=True)
                        elif staff.get('status') == "ACTIVE":
                            active_t = next((t for t in local_db['tickets'] if t['status'] == 'SERVING' and t.get('served_by_staff') == staff['name']), None)
                            if not active_t:
                                active_t = next((t for t in local_db['tickets'] if t['status'] == 'SERVING' and t.get('served_by') == station_name and not t.get('served_by_staff')), None)
                            
                            if active_t:
                                is_blinking = "blink-active" if active_t.get('start_time') and (get_ph_time() - datetime.datetime.fromisoformat(active_t['start_time'])).total_seconds() < 20 else ""
                                b_color = get_lane_color(active_t['lane'])
                                st.markdown(f"""
                                <div class="serving-card-jumbo" style="border-left: 20px solid {b_color}; {style_str}">
                                    <div class="jumbo-counter">{sanitize_text(station_name)}</div>
                                    <h2 style="color:{b_color};" class="jumbo-ticket {is_blinking}">{sanitize_text(active_t['number'])}</h2>
                                    <div class="jumbo-staff">{sanitize_text(nickname)}</div>
                                </div>""", unsafe_allow_html=True)
                            else: 
                                st.markdown(f"""
                                <div class="serving-card-jumbo" style="border-left: 20px solid #ccc; {style_str}">
                                    <div class="jumbo-counter">{sanitize_text(station_name)}</div>
                                    <h2 style="color:#22c55e; font-size: 6vw;">READY</h2>
                                    <div class="jumbo-staff">{sanitize_text(nickname)}</div>
                                </div>""", unsafe_allow_html=True)
        st.markdown("---")
        c_queue, c_park = st.columns([3, 1])
        with c_queue:
            q1, q2, q3 = st.columns(3)
            waiting = [t for t in local_db['tickets'] if t["status"] == "WAITING" and not t.get('appt_time')] 
            waiting.sort(key=get_queue_sort_key)
            with q1:
                st.markdown(f"<div class='swim-col' style='border-top-color:{get_lane_color('T')};'><h3>{LANE_CODES['T']['icon']} {LANE_CODES['T']['desc'].upper()}</h3>", unsafe_allow_html=True)
                for t in [x for x in waiting if x['lane'] == 'T'][:5]: st.markdown(f"<div class='queue-item'><span>{sanitize_text(t['number'])}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with q2:
                st.markdown(f"<div class='swim-col' style='border-top-color:{get_lane_color('A')};'><h3>{LANE_CODES['A']['icon']} {LANE_CODES['A']['desc'].upper()}</h3>", unsafe_allow_html=True)
                for t in [x for x in waiting if x['lane'] == 'A'][:5]: st.markdown(f"<div class='queue-item'><span>{sanitize_text(t['number'])}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with q3:
                st.markdown(f"<div class='swim-col' style='border-top-color:{get_lane_color('C')};'><h3>👤 SERVICES</h3>", unsafe_allow_html=True)
                for t in [x for x in waiting if x['lane'] in ['C','E','F']][:5]: st.markdown(f"<div class='queue-item'><span>{sanitize_text(t['number'])}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        with c_park:
            st.markdown("### 🅿️ PARKED")
            parked = [t for t in local_db['tickets'] if t["status"] == "PARKED"]
            for p in parked:
                park_time = datetime.datetime.fromisoformat(p['park_timestamp']); remaining = datetime.timedelta(minutes=PARK_GRACE_MINUTES) - (get_ph_time() - park_time)
                if remaining.total_seconds() <= 0: p["status"] = "NO_SHOW"; save_db(local_db)
                else:
                    mins, secs = divmod(remaining.total_seconds(), 60)
                    disp_txt = p['appt_name'] if p.get('appt_name') else p['number']
                    css_class = "park-appt" if p.get('appt_name') else "park-danger"
                    st.markdown(f"""<div class="{css_class}"><span>{sanitize_text(disp_txt)}</span><span>{int(mins):02d}:{int(secs):02d}</span></div>""", unsafe_allow_html=True)
        txt = " | ".join([sanitize_text(a) for a in local_db['announcements']])
        status = local_db.get('branch_status', 'NORMAL')
        bg_color = "#DC2626" if status == "OFFLINE" else ("#F97316" if status == "SLOW" else "#FFD700")
        text_color = "white" if status in ["OFFLINE", "SLOW"] else "black"
        if status != "NORMAL": txt = f"⚠ NOTICE: We are currently experiencing {status} connection. Please bear with us. {txt}"
        st.markdown(f"<div style='background: {bg_color}; color: {text_color}; padding: 10px; font-weight: bold; position: fixed; bottom: 0; width: 100%; font-size:20px;'><marquee>{txt}</marquee></div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-footer'>System developed by RPT/SSSGingoog © 2026 | v23.10</div>", unsafe_allow_html=True)
    time.sleep(3); st.rerun()

def render_counter(user):
    update_activity()
    local_db = load_db()
    user_key = next((k for k,v in local_db['staff'].items() if v['name'] == user['name']), None)
    if not user_key: st.error("User Sync Error. Please Relogin."); return
    current_user_state = local_db['staff'][user_key]

    st.sidebar.title(f"👮 {user['name']}")
    
    last_activity = st.session_state.get('last_activity', get_ph_time())
    elapsed = (get_ph_time() - last_activity).total_seconds() / 60
    remaining_mins = SESSION_TIMEOUT_MINUTES - elapsed
    if remaining_mins <= 5: st.sidebar.markdown(f"""<div class='timeout-warning'>⚠️ Session expires in {int(remaining_mins)} min</div>""", unsafe_allow_html=True)
    
    if st.sidebar.button("⬅ LOGOUT"): handle_safe_logout(reason="MANUAL"); st.rerun()

    st.sidebar.markdown("---")
    st.session_state['surge_mode'] = st.sidebar.checkbox("🚨 PRIORITY SURGE MODE", value=st.session_state['surge_mode'])
    if st.session_state['surge_mode']: st.sidebar.warning("⚠ SURGE ACTIVE: Only Priority Tickets will be called!")
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("☕ Go On Break"):
        b_reason = st.selectbox("Reason", ["Lunch Break", "Coffee Break (15m)", "Bio-Break", "Emergency"])
        if st.button("⏸ START BREAK"):
            station = current_user_state.get('default_station', '')
            serving_ticket = next((t for t in local_db['tickets'] if t['status'] == 'SERVING' and t.get('served_by') == station), None)
            if serving_ticket: st.error("⛔ You have an active ticket. Complete or Park it first.")
            else:
                local_db['staff'][user_key]['status'] = "ON_BREAK"; local_db['staff'][user_key]['break_reason'] = b_reason; local_db['staff'][user_key]['break_start_time'] = get_ph_time().isoformat()
                save_db(local_db); st.session_state['user'] = local_db['staff'][user_key]; log_audit("BREAK_START", user['name'], details=b_reason); st.rerun()

    with st.sidebar.expander("🔒 Change Password"):
        with st.form("pwd_chg"):
            n_pass = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                if user_key: local_db['staff'][user_key]['pass'] = n_pass; save_db(local_db); log_audit("PASSWORD_CHANGE", user['name'], target=user_key); st.success("Updated!")

    st.sidebar.markdown("---")
    st.sidebar.write("**⚠ Report Issue**")
    if st.sidebar.button("🟡 Intermittent Net"): log_incident(user['name'], "SLOW"); st.toast("Reported: Slow Connection")
    if st.sidebar.button("🔴 System Offline"): log_incident(user['name'], "OFFLINE"); st.toast("Reported: System Offline")
    if st.sidebar.button("🟢 System Restored"): log_incident(user['name'], "NORMAL"); st.toast("System Restored")
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("📅 Book Appointment"):
        with st.form("staff_appt"):
            nm = st.text_input("Client Name"); tm = st.time_input("Time Slot"); svc = st.text_input("Transaction"); ctr = st.selectbox("Assign to Counter (Optional)", [""] + [c['name'] for c in local_db['config']['counter_map']])
            if st.form_submit_button("Book"):
                generate_ticket_manual(svc, "C", True, is_appt=True, appt_name=nm, appt_time=tm, assign_counter=ctr)
                log_audit("APPOINTMENT_CREATE", user['name'], details=f"{nm} at {tm}", target=svc); st.success("Booked!")

    if current_user_state.get('status') == "ON_BREAK":
        st.warning(f"⛔ YOU ARE CURRENTLY ON BREAK ({current_user_state.get('break_reason', 'Break')})")
        if st.button("▶ RESUME WORK", type="primary"):
            local_db['staff'][user_key]['status'] = "ACTIVE"; save_db(local_db); st.session_state['user'] = local_db['staff'][user_key]; log_audit("BREAK_END", user['name']); st.rerun()
        return

    if 'my_station' not in st.session_state: st.session_state['my_station'] = current_user_state.get('default_station', 'Counter 1')
    st.markdown(f"### Station: {st.session_state['my_station']}")
    allowed_counters = get_allowed_counters(user['role'])
    if st.session_state['my_station'] not in allowed_counters and allowed_counters: st.session_state['my_station'] = allowed_counters[0]
    new_station = st.selectbox("Switch Station", allowed_counters, index=allowed_counters.index(st.session_state['my_station']) if st.session_state['my_station'] in allowed_counters else 0)
    if new_station != st.session_state['my_station']:
        st.session_state['my_station'] = new_station; local_db['staff'][user_key]['default_station'] = new_station; save_db(local_db); log_audit("STATION_CHANGE", user['name'], target=new_station); st.rerun()
    
    current_counter_obj = next((c for c in local_db['config']['counter_map'] if c['name'] == st.session_state['my_station']), None)
    station_type = current_counter_obj['type'] if current_counter_obj else "Counter"
    my_lanes = local_db['config']["assignments"].get(station_type, ["C"])
    queue = [t for t in local_db['tickets'] if t["status"] == "WAITING" and t["lane"] in my_lanes]
    queue.sort(key=get_queue_sort_key)
    current = next((t for t in local_db['tickets'] if t["status"] == "SERVING" and t.get("served_by") == st.session_state['my_station']), None)
    
    c1, c2 = st.columns([2,1])
    with c1:
        if current:
            display_num = current['appt_name'] if current.get('appt_name') else current['number']
            lane_color = get_lane_color(current['lane'])
            st.markdown(f"""<div style='padding:30px; background:#e0f2fe; border-radius:15px; border-left:10px solid {lane_color};'><h1 style='margin:0; color:{lane_color}; font-size: 60px;'>{sanitize_text(display_num)}</h1><h3>{sanitize_text(current['service'])}</h3></div>""", unsafe_allow_html=True)
            if current.get("ref_from"): st.markdown(f"""<div style='background:#fee2e2; border-left:5px solid #ef4444; padding:10px; margin-top:10px;'><span style='color:#b91c1c; font-weight:bold;'>↩ REFERRED FROM: {sanitize_text(current["ref_from"])}</span><br><span style='color:#b91c1c; font-weight:bold;'>📝 REASON: {sanitize_text(current.get("referral_reason", "No reason provided"))}</span></div>""", unsafe_allow_html=True)
            
            if st.button("🔄 REFER", use_container_width=True): st.session_state['refer_modal'] = True
            
            if st.session_state.get('refer_modal'):
                with st.form("refer_form"):
                    st.write("Transfer Ticket To:")
                    target_lane = st.selectbox("Lane", list(LANE_NAME_TO_CODE.keys()))
                    reason = st.text_input("Reason")
                    c_sub, c_can = st.columns(2)
                    if c_sub.form_submit_button("Confirm Transfer"):
                        current["lane"] = LANE_NAME_TO_CODE[target_lane]
                        current["status"] = "WAITING"
                        current["served_by"] = None
                        current["ref_from"] = st.session_state['my_station']
                        current["referral_reason"] = reason
                        save_db(local_db)
                        log_audit("TICKET_REFER", user['name'], details=f"To {target_lane}: {reason}", target=current['number'])
                        clear_ticket_modal_states(); st.rerun()
                    if c_can.form_submit_button("Cancel"):
                        clear_ticket_modal_states(); st.rerun()

            with st.expander("📝 Reality Log (IOMS - Verify & Edit)", expanded=True):
                all_txns = []
                for cat, items in local_db.get('transaction_master', {}).items():
                    for item in items: all_txns.append(f"[{cat}] {item}")
                c_txn, c_btn = st.columns([3, 1])
                new_txn = c_txn.selectbox("Add Transaction", all_txns)
                if c_btn.button("➕ Add"):
                    if 'actual_transactions' not in current: current['actual_transactions'] = []
                    clean_txn = new_txn.split("] ")[1] if "]" in new_txn else new_txn
                    category = new_txn.split("] ")[0].replace("[","") if "]" in new_txn else "GENERAL"
                    current['actual_transactions'].append({"txn": clean_txn, "category": category, "staff": user['name'], "timestamp": get_ph_time().isoformat()})
                    save_db(local_db); st.rerun()
                if 'actual_transactions' in current and current['actual_transactions']:
                    st.write("---")
                    st.caption("Transactions Logged for this Ticket:")
                    for i, txn in enumerate(current['actual_transactions']):
                        col_text, col_del = st.columns([4, 1])
                        col_text.text(f"• {txn['txn']}")
                        if col_del.button("🗑", key=f"del_txn_{i}"): current['actual_transactions'].pop(i); save_db(local_db); st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            if b1.button("✅ COMPLETE", use_container_width=True): 
                if not current.get('actual_transactions'): st.error("⛔ BLOCKED: You must log at least one Actual Transaction first.")
                else:
                    current["status"] = "COMPLETED"
                    current["end_time"] = get_ph_time().isoformat()
                    local_db['history'].append(current)
                    local_db['tickets'] = [t for t in local_db['tickets'] if t['id'] != current['id']]
                    clear_ticket_modal_states(); save_db(local_db); log_audit("TICKET_COMPLETE", user['name'], target=current['number']); st.rerun()
            if b2.button("🅿️ PARK", use_container_width=True): 
                current["status"] = "PARKED"; current["park_timestamp"] = get_ph_time().isoformat()
                clear_ticket_modal_states(); save_db(local_db); log_audit("TICKET_PARK", user['name'], target=current['number']); st.rerun()
            if b3.button("🔔 RE-CALL", use_container_width=True):
                current["start_time"] = get_ph_time().isoformat()
                trigger_audio(current['number'], st.session_state['my_station']); save_db(local_db); st.toast(f"Re-calling {current['number']}..."); time.sleep(0.5); st.rerun()
        else:
            if st.button("🔊 CALL NEXT", type="primary", use_container_width=True):
                update_activity()
                nxt = get_next_ticket(queue, st.session_state['surge_mode'], st.session_state['my_station'])
                if nxt:
                    db_ticket = next((x for x in local_db['tickets'] if x['id'] == nxt['id']), None)
                    if db_ticket:
                        db_ticket["status"] = "SERVING"; db_ticket["served_by"] = st.session_state['my_station']; db_ticket["start_time"] = get_ph_time().isoformat()
                        trigger_audio(db_ticket['number'], st.session_state['my_station']); save_db(local_db); log_audit("TICKET_CALL", user['name'], target=db_ticket['number']); st.rerun()
                else: st.warning(f"No tickets for {station_type}.")
    with c2:
        count, avg_time = get_staff_efficiency(user['name'])
        st.metric("Performance", count, delta=avg_time + " avg/txn")
        st.divider()
        st.write("🅿️ Parked Tickets")
        parked = [t for t in local_db['tickets'] if t["status"] == "PARKED" and t["lane"] in my_lanes]
        for p in parked:
            if st.button(f"🔊 {p['number']}", key=p['id']):
                update_activity()
                p["status"] = "SERVING"; p["served_by"] = st.session_state['my_station']; p["start_time"] = get_ph_time().isoformat(); trigger_audio(p['number'], st.session_state['my_station']); save_db(local_db); log_audit("TICKET_RECALL_PARKED", user['name'], target=p['number']); st.rerun()

def render_admin_panel(user):
    update_activity()
    local_db = load_db()
    st.title("🛠 Admin & IOMS Center")
    if st.sidebar.button("⬅ LOGOUT"): handle_safe_logout(reason="MANUAL"); st.rerun()
    
    if user['role'] in ["ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]:
        tabs = ["Dashboard", "Reports", "Book Appt", "Kiosk Menu", "IOMS Master", "Counters", "Users", "Resources", "Exemptions", "Announcements", "Audit Log", "Backup", "System Info"]
    else: st.error("Access Denied"); return
    
    active = st.radio("Module", tabs, horizontal=True)
    st.divider()
    
    if active == "Dashboard":
        st.subheader("📊 G-ABAY Precision Analytics")
        with st.expander("📖 Status Legend", expanded=False):
            st.markdown("<div class='status-legend'>", unsafe_allow_html=True)
            for status_code, status_info in TICKET_STATUSES.items():
                st.markdown(f"<span class='status-item' style='background-color: {status_info['color']}20; border: 1px solid {status_info['color']};'><strong>{status_info['label']}</strong>: {status_info['desc']}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1: time_range = st.selectbox("Select Time Range", ["Today", "Yesterday", "This Week", "This Month", "Quarterly", "Semestral", "Annual"])
        with c2: lane_filter = st.selectbox("Select Lane / Section", ["All Lanes", "Teller", "Employer", "Counter", "eCenter", "Fast Lane"])
        
        data_source = local_db['history']
        archive_data = []
        if os.path.exists(ARCHIVE_FILE):
            with open(ARCHIVE_FILE, "r") as af:
                try: archive_data = json.load(af)
                except: archive_data = []
        
        today = get_ph_time().date()
        filtered_txns = []
        start_date, end_date = today, today
        
        if time_range == "Today": filtered_txns = data_source
        else:
            if time_range == "Yesterday": start_date = today - datetime.timedelta(days=1); end_date = start_date
            elif time_range == "This Week": start_date = today - datetime.timedelta(days=today.weekday())
            elif time_range == "This Month": start_date = today.replace(day=1)
            elif time_range == "Quarterly": curr_q = (today.month - 1) // 3 + 1; start_date = datetime.date(today.year, 3 * curr_q - 2, 1)
            
            for entry in archive_data:
                entry_dt = datetime.datetime.strptime(entry['date'], "%Y-%m-%d").date()
                if start_date <= entry_dt <= end_date: filtered_txns.extend(entry.get('history', []))
            if time_range != "Yesterday": filtered_txns.extend(data_source)

        if lane_filter != "All Lanes":
            target_code = LANE_NAME_TO_CODE.get(lane_filter)
            filtered_txns = [t for t in filtered_txns if t['lane'] == target_code]

        if filtered_txns:
            df = pd.DataFrame(filtered_txns)
            df['Date'] = df['timestamp'].apply(lambda x: datetime.datetime.fromisoformat(x).strftime('%Y-%m-%d'))
            df['Ticket Number'] = df.apply(lambda x: x.get('full_id', x['number']), axis=1)
            
            def get_time_str(iso_str):
                if not iso_str: return ""
                return datetime.datetime.fromisoformat(iso_str).strftime('%I:%M:%S %p')

            df['Time Issued'] = df['timestamp'].apply(get_time_str)
            df['Time Called'] = df['start_time'].apply(get_time_str)
            df['Time Ended'] = df['end_time'].apply(get_time_str)

            def calc_diff_mins(end, start):
                if not end or not start: return 0.0
                try:
                    s = datetime.datetime.fromisoformat(start)
                    e = datetime.datetime.fromisoformat(end)
                    return round((e - s).total_seconds() / 60, 2)
                except: return 0.0

            df['Total Waiting Time (Mins)'] = df.apply(lambda x: calc_diff_mins(x['start_time'], x['timestamp']), axis=1)
            df['Total Handle Time (Mins)'] = df.apply(lambda x: calc_diff_mins(x['end_time'], x['start_time']), axis=1)
            df.rename(columns={'served_by': 'Served By'}, inplace=True)

            export_cols = ['Date', 'Ticket Number', 'Time Issued', 'Time Called', 'Time Ended', 'Total Waiting Time (Mins)', 'Total Handle Time (Mins)', 'Served By']
            csv_export = df[export_cols].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Raw Data (CSV)", csv_export, "raw_data.csv", "text/csv")
            
            df_valid = df[df['Total Handle Time (Mins)'] > 0]
            avg_wait = round(df_valid['Total Waiting Time (Mins)'].mean()) if not df_valid.empty else 0
            avg_handle = round(df_valid['Total Handle Time (Mins)'].mean()) if not df_valid.empty else 0
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Volume", len(filtered_txns))
            m2.metric("Avg Wait", f"{avg_wait}m")
            m3.metric("Avg Handle", f"{avg_handle}m")
            m4.metric("CSAT", "4.8⭐")
            
            c1, c2 = st.columns(2)
            with c1:
                svc_stats = df.groupby('service').size().reset_index(name='count')
                fig_pie = px.pie(svc_stats, names='service', values='count', title='Transaction Mix', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                df['lane_name'] = df['lane'].map(LANE_CODE_TO_NAME)
                lane_stats = df.groupby('lane_name')['Total Waiting Time (Mins)'].mean().reset_index()
                fig_bar = px.bar(lane_stats, x='lane_name', y='Total Waiting Time (Mins)', title='Avg Wait by Lane', color='Total Waiting Time (Mins)', color_continuous_scale=['green', 'orange', 'red'])
                st.plotly_chart(fig_bar, use_container_width=True)
        else: st.info("No data available.")

    elif active == "Reports":
        st.subheader("📋 IOMS Report Generator")
        c1, c2 = st.columns(2)
        d_range = c1.date_input("Date Range", [get_ph_time().date(), get_ph_time().date()])
        staff_filter = c2.multiselect("Filter Staff", [s['name'] for s in local_db['staff'].values()])
        if len(d_range) == 2:
            start, end = d_range
            all_txns_flat = []
            def extract_txns(ticket_list):
                for t in ticket_list:
                    t_date = datetime.datetime.fromisoformat(t['timestamp']).date()
                    if start <= t_date <= end:
                        if t.get('actual_transactions'):
                            for act in t['actual_transactions']:
                                if not staff_filter or act['staff'] in staff_filter:
                                    all_txns_flat.append({
                                        "Date": t_date, "Ticket ID": t.get('full_id', t['number']), "Category": act.get('category', 'MEMBER SERVICES'), "Transaction": act['txn'], "Staff": act['staff'], "Number of Transaction": 1
                                    })
                        else:
                            if not staff_filter or t.get('served_by') in staff_filter:
                                all_txns_flat.append({
                                    "Date": t_date, "Ticket ID": t.get('full_id', t['number']), "Category": LANE_TO_CATEGORY.get(t['lane'], "MEMBER SERVICES"), "Transaction": t['service'], "Staff": t.get('served_by', 'Unknown'), "Number of Transaction": 1
                                })
            extract_txns(local_db['history'])
            if os.path.exists(ARCHIVE_FILE):
                with open(ARCHIVE_FILE, 'r') as af:
                    try: 
                        for day in json.load(af): extract_txns(day.get('history', []))
                    except: pass
            if all_txns_flat:
                df_rep = pd.DataFrame(all_txns_flat)
                st.write("**Summary**"); st.dataframe(df_rep.groupby(['Category', 'Transaction']).size().reset_index(name='Volume'), use_container_width=True)
                st.write("**Detailed Log**"); st.dataframe(df_rep, use_container_width=True)
                st.download_button("📥 Download IOMS CSV", df_rep.to_csv(index=False).encode('utf-8'), "ioms_report.csv", "text/csv")
            else: st.info("No records found.")

    elif active == "Book Appt":
        st.subheader("📅 Book Appointment")
        with st.form("admin_appt"):
            nm = st.text_input("Client Name"); tm = st.time_input("Time Slot"); svc = st.text_input("Transaction"); ctr = st.selectbox("Assign to Counter (Optional)", [""] + [c['name'] for c in local_db['config']['counter_map']])
            if st.form_submit_button("Book Slot"):
                generate_ticket_manual(svc, "C", True, is_appt=True, appt_name=nm, appt_time=tm, assign_counter=ctr)
                log_audit("APPOINTMENT_CREATE", user['name'], details=f"{nm} at {tm}", target=svc); st.success(f"Booked for {nm} at {tm}")

    elif active == "Kiosk Menu":
        st.subheader("Manage Kiosk Buttons")
        c1, c2 = st.columns([1, 2])
        with c1:
            cat_list = list(local_db['menu'].keys())
            sel_cat = st.selectbox("Select Category", cat_list)
            items = local_db['menu'][sel_cat]
            for i, (label, code, lane) in enumerate(items):
                with st.expander(f"{label} ({code})"):
                    new_label = st.text_input("Label", label, key=f"l_{i}")
                    new_code = st.text_input("Code", code, key=f"c_{i}")
                    new_lane = st.selectbox("Lane", ["C", "E", "F", "T", "A", "GATE"], index=["C", "E", "F", "T", "A", "GATE"].index(lane), key=f"ln_{i}")
                    if st.button("Update", key=f"up_{i}"): 
                        local_db['menu'][sel_cat][i] = (new_label, new_code, new_lane)
                        save_db(local_db); log_audit("KIOSK_MENU_UPDATE", user['name'], details=f"{label} -> {new_label}"); st.success("Updated!"); st.rerun()
                    if st.button("Delete", key=f"del_{i}"): 
                        local_db['menu'][sel_cat].pop(i); save_db(local_db); log_audit("KIOSK_MENU_DELETE", user['name'], target=label); st.rerun()

    elif active == "Counters":
        for i, c in enumerate(local_db['config']['counter_map']): 
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            c1.text(c['name']); c2.text(c['type'])
            with c3:
                with st.popover("✏️"):
                    new_n = st.text_input("Rename", c['name'], key=f"rn_{i}")
                    if st.button("Save", key=f"sv_{i}"):
                        old_name = c['name']
                        local_db['config']['counter_map'][i]['name'] = new_n
                        for s_key in local_db['staff']:
                            if local_db['staff'][s_key].get('default_station') == old_name:
                                local_db['staff'][s_key]['default_station'] = new_n
                        save_db(local_db); log_audit("COUNTER_RENAME", user['name'], details=f"{old_name} -> {new_n}"); st.rerun()
            if c4.button("🗑", key=f"dc_{i}"): local_db['config']['counter_map'].pop(i); save_db(local_db); log_audit("COUNTER_DELETE", user['name'], target=c['name']); st.rerun()
        with st.form("add_counter"): 
            cn = st.text_input("Name"); ct = st.selectbox("Type", ["Counter", "Teller", "Employer", "eCenter"])
            if st.form_submit_button("Add"): local_db['config']['counter_map'].append({"name": cn, "type": ct}); save_db(local_db); log_audit("COUNTER_CREATE", user['name'], target=cn); st.rerun()

    elif active == "IOMS Master":
        st.subheader("Transaction Master List")
        current_master = local_db.get('transaction_master', DEFAULT_TRANSACTIONS)
        c1, c2, c3 = st.columns(3)
        with c1: st.write("**PAYMENTS**"); current_master["PAYMENTS"] = st.data_editor(pd.DataFrame(current_master["PAYMENTS"], columns=["Item"]), num_rows="dynamic")["Item"].tolist()
        with c2: st.write("**EMPLOYERS**"); current_master["EMPLOYERS"] = st.data_editor(pd.DataFrame(current_master["EMPLOYERS"], columns=["Item"]), num_rows="dynamic")["Item"].tolist()
        with c3: st.write("**MEMBER SERVICES**"); current_master["MEMBER SERVICES"] = st.data_editor(pd.DataFrame(current_master["MEMBER SERVICES"], columns=["Item"]), num_rows="dynamic")["Item"].tolist()
        if st.button("Save Master List"): local_db['transaction_master'] = current_master; save_db(local_db); log_audit("IOMS_MASTER_UPDATE", user['name']); st.success("Updated!")

    elif active == "Users":
        st.subheader("Manage Users"); h1, h2, h3, h4, h5 = st.columns([1.5, 3, 2, 1, 0.5]); h1.markdown("**ID**"); h2.markdown("**Name**"); h3.markdown("**Station**")
        for uid, u in list(local_db['staff'].items()):
            c1, c2, c3, c4, c5 = st.columns([1.5, 3, 2, 0.5, 0.5]); c1.text(uid); c2.text(f"{u['name']} ({u['role']})"); c3.text(u.get('default_station', '-'))
            with c4:
                with st.popover("✏️"):
                    with st.form(f"edit_{uid}"):
                        en = st.text_input("Name", u['name'])
                        enick = st.text_input("Nickname", u.get('nickname', ''))
                        er = st.selectbox("Role", STAFF_ROLES, index=STAFF_ROLES.index(u['role']) if u['role'] in STAFF_ROLES else 0)
                        est = st.selectbox("Station", [c['name'] for c in local_db['config']['counter_map']], index=[c['name'] for c in local_db['config']['counter_map']].index(u.get('default_station', '')) if u.get('default_station') in [c['name'] for c in local_db['config']['counter_map']] else 0)
                        if st.form_submit_button("Save"): local_db['staff'][uid].update({'name': en, 'nickname': enick, 'role': er, 'default_station': est}); save_db(local_db); log_audit("USER_UPDATE", user['name'], target=uid); st.rerun()
                    if st.button("🔑 RESET", key=f"rst_{uid}"): local_db['staff'][uid]['pass'] = "sss2026"; save_db(local_db); log_audit("PASSWORD_RESET", user['name'], target=uid); st.toast("Reset to 'sss2026'")
            if c5.button("🗑", key=f"del_{uid}"): del local_db['staff'][uid]; save_db(local_db); log_audit("USER_DELETE", user['name'], target=uid); st.rerun()
        st.markdown("---")
        st.write("**Add New User**")
        with st.form("add_user_form"):
            new_id = st.text_input("User ID (Login)")
            new_name = st.text_input("Full Name")
            new_nick = st.text_input("Nickname (Display)")
            new_role = st.selectbox("Role", STAFF_ROLES)
            new_station = st.selectbox("Assign Default Station", [c['name'] for c in local_db['config']['counter_map']])
            if st.form_submit_button("Create User"):
                valid, msg = validate_user_id(new_id)
                if not valid: st.error(f"⛔ {msg}")
                elif new_id in local_db['staff']: st.error("User ID already exists!")
                else: 
                    local_db['staff'][new_id] = {"pass": "123", "role": new_role, "name": new_name, "nickname": new_nick if new_nick else new_name.split()[0], "default_station": new_station, "status": "ACTIVE", "online": False}
                    save_db(local_db); log_audit("USER_CREATE", user['name'], target=new_id); st.success("Created!"); st.rerun()
    
    elif active == "Resources":
        st.subheader("Manage Info Hub Content")
        for i, res in enumerate(local_db.get('resources', [])):
            with st.expander(f"{'🔗' if res['type'] == 'LINK' else '❓'} {res['label']}"):
                st.write(f"**Value:** {res['value']}")
                if st.button("Delete", key=f"res_del_{i}"): local_db['resources'].pop(i); save_db(local_db); st.rerun()
        st.write("**Add New Resource**")
        with st.form("new_res"):
            r_type = st.selectbox("Type", ["LINK", "FAQ"]); r_label = st.text_input("Label / Question"); r_value = st.text_area("URL / Answer")
            if st.form_submit_button("Add Resource"): local_db['resources'].append({"type": r_type, "label": r_label, "value": r_value}); save_db(local_db); st.success("Added!"); st.rerun()

    elif active == "Exemptions":
        st.subheader("Manage Exemption Warnings")
        t_ret, t_death, t_fun = st.tabs(["Retirement", "Death", "Funeral"])
        def render_exemption_tab(claim_type):
            current_list = local_db['exemptions'].get(claim_type, [])
            for i, ex in enumerate(current_list):
                c1, c2 = st.columns([4, 1]); c1.text(f"• {ex}"); 
                if c2.button("🗑", key=f"del_{claim_type}_{i}"): local_db['exemptions'][claim_type].pop(i); save_db(local_db); st.rerun()
            new_ex = st.text_input(f"Add New {claim_type} Exemption", key=f"new_{claim_type}")
            if st.button(f"Add", key=f"add_{claim_type}"): local_db['exemptions'][claim_type].append(new_ex); save_db(local_db); st.rerun()
        with t_ret: render_exemption_tab("Retirement")
        with t_death: render_exemption_tab("Death")
        with t_fun: render_exemption_tab("Funeral")

    elif active == "Announcements":
        curr = " | ".join(local_db['announcements']); new_txt = st.text_area("Marquee", value=curr)
        if st.button("Update"): local_db['announcements'] = [new_txt]; save_db(local_db); log_audit("ANNOUNCEMENT_UPDATE", user['name']); st.success("Updated!")

    elif active == "Audit Log":
        st.subheader("🔍 Audit Trail Viewer")
        audit_entries = local_db.get('audit_log', [])
        if audit_entries:
            df_audit = pd.DataFrame(audit_entries)
            df_audit['Time'] = df_audit['timestamp'].apply(lambda x: datetime.datetime.fromisoformat(x).strftime('%Y-%m-%d %I:%M %p'))
            st.dataframe(df_audit[['Time', 'action', 'user', 'target', 'details']], use_container_width=True, hide_index=True)
            st.download_button("📥 Export Audit Log", df_audit.to_csv(index=False).encode('utf-8'), "audit_log.csv", "text/csv")
        else: st.info("No audit entries.")

    elif active == "Backup": 
        st.subheader("💾 Backup & Recovery")
        st.download_button("📥 BACKUP NOW", data=json.dumps(local_db), file_name="sss_backup.json")
        st.markdown("---")
        st.write("**Hourly Backups (Last 24)**")
        if os.path.exists(BACKUP_DIR):
            backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "sss_data_*.json")), reverse=True)
            if backups:
                for b in backups[:10]: st.text(f"• {os.path.basename(b)} ({os.path.getsize(b)/1024:.1f} KB)")
            else: st.info("No hourly backups yet.")
    
    elif active == "System Info":
        st.subheader("⚙️ System Configuration")
        st.write("**Version Information**")
        st.code(f"""
SSS G-ABAY Version: v23.10 (Corrected Grid Edition)
Build Date: 2026-02-02
Timezone: UTC+{UTC_OFFSET_HOURS} (Philippine Standard Time)
        """)
        st.write("**System Constants**")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Session Timeout", f"{SESSION_TIMEOUT_MINUTES} min")
            st.metric("Park Grace Period", f"{PARK_GRACE_MINUTES} min")
            st.metric("Archive Retention", f"{ARCHIVE_RETENTION_DAYS} days")
        with c2:
            st.metric("Max Hourly Backups", MAX_HOURLY_BACKUPS)
            st.metric("Audit Log Max", f"{AUDIT_LOG_MAX_ENTRIES:,}")
            st.metric("Default Avg Txn Time", f"{DEFAULT_AVG_TXN_MINUTES} min")
        st.write("**Status Legend**")
        for status_code, status_info in TICKET_STATUSES.items():
            st.markdown(f"- **{status_code}** ({status_info['label']}): {status_info['desc']}")
        st.write("**Lane Configuration**")
        for lane_code, lane_info in LANE_CODES.items():
            st.markdown(f"- **{lane_code}** - {lane_info['icon']} {lane_info['name']}: {lane_info['desc']} (Color: {lane_info['color']})")

# ==========================================
# 5. ROUTER
# ==========================================
params = st.query_params
mode = params.get("mode")

if mode == "staff" and 'user' in st.session_state:
    if check_session_timeout(): st.warning("⚠️ Session expired due to inactivity."); st.rerun()

if mode == "kiosk": render_kiosk()
elif mode == "staff":
    if 'user' not in st.session_state:
        st.title("Staff Login")
        u = st.text_input("Username"); p = st.text_input("Password", type="password")
        if st.button("Login"):
            local_db = load_db()
            acct = next((v for k,v in local_db['staff'].items() if v["name"] == u or k == u), None)
            acct_key = next((k for k,v in local_db['staff'].items() if v["name"] == u or k == u), None)
            if u == "admin" and not acct: local_db['staff']['admin'] = DEFAULT_DATA['staff']['admin']; save_db(local_db); st.warning("Admin reset."); st.rerun()
            if acct and acct['pass'] == p: 
                st.session_state['user'] = acct
                st.session_state['last_activity'] = get_ph_time()
                st.session_state['login_date'] = get_ph_time().strftime("%Y-%m-%d")
                local_db['staff'][acct_key]['online'] = True
                save_db(local_db)
                log_audit("LOGIN", acct['name'], target=acct.get('default_station', 'N/A'))
                st.rerun()
            else: st.error("Invalid")
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
    t1, t2, t3 = st.tabs(["🎫 Tracker", "ℹ️ Info Hub", "⭐ Rate Us"])
    with t1:
        tn = st.text_input("Enter Ticket # (e.g. 001)")
        if tn:
            local_db = load_db()
            t = next((x for x in local_db['tickets'] if x["number"] == tn or x.get('full_id') == tn), None)
            t_hist = next((x for x in local_db['history'] if x["number"] == tn or x.get('full_id') == tn), None)
            if t:
                if t['status'] == "PARKED":
                    park_time = datetime.datetime.fromisoformat(t['park_timestamp']); remaining = datetime.timedelta(minutes=PARK_GRACE_MINUTES) - (get_ph_time() - park_time)
                    if remaining.total_seconds() > 0:
                        mins, secs = divmod(remaining.total_seconds(), 60)
                        st.markdown(f"""<div style="font-size:30px; font-weight:bold; color:#b91c1c; text-align:center;">PARKED: {int(mins):02d}:{int(secs):02d}</div>""", unsafe_allow_html=True); st.error("⚠️ PLEASE APPROACH COUNTER IMMEDIATELY TO AVOID FORFEITURE.")
                        st.markdown(f"""<script>startTimer({remaining.total_seconds()}, "mob_park_{t['id']}");</script>""", unsafe_allow_html=True)
                    else: st.error("❌ TICKET EXPIRED")
                elif t['status'] == "SERVING": st.success(f"🔊 NOW SERVING at {t.get('served_by', 'Counter')}. Please proceed immediately.")
                else:
                    st.info(f"Status: {t['status']}")
                    wait_str = calculate_specific_wait_time(t['id'], t['lane']); people_ahead = calculate_people_ahead(t['id'], t['lane'])
                    c1, c2 = st.columns(2); c1.metric("Est. Wait", wait_str)
                    if people_ahead == 0: c2.success("You are Next!")
                    else: c2.metric("People Ahead", people_ahead)
                    st.write(f"Your Ticket: {t['number']}")
                time.sleep(5); st.rerun()
            elif t_hist: st.success("✅ TRANSACTION COMPLETE. Thank you!")
            else: st.error("Not Found (Check Ticket Number)")
    with t2:
        st.subheader("Member Resources")
        for l in [r for r in db.get('resources', []) if r['type'] == 'LINK']: st.markdown(f"[{sanitize_text(l['label'])}]({l['value']})")
        for f in [r for r in db.get('resources', []) if r['type'] == 'FAQ']: 
            with st.expander(sanitize_text(f['label'])): st.write(sanitize_text(f['value']))
    with t3:
        st.subheader("Rate Our Service")
        verify_t = st.text_input("Enter your Ticket Number to rate:", key="rate_t")
        if verify_t:
            local_db = load_db()
            active_t = next((x for x in local_db['history'] if x['number'] == verify_t), None)
            target_ticket = active_t
            if target_ticket:
                st.success(f"Verified! Served by: {target_ticket.get('served_by', 'Unknown')}")
                with st.form("rev"):
                    rate = st.feedback("stars")
                    pers = st.text_input("Personnel Served You (Optional)")
                    comm = st.text_area("Comments")
                    if st.form_submit_button("Submit Rating"):
                        review_entry = {"ticket": verify_t, "rating": (rate if rate else 0) + 1, "personnel": pers, "comment": comm, "timestamp": get_ph_time().isoformat()}
                        local_db['reviews'].append(review_entry); save_db(local_db); st.success("Thank you!"); time.sleep(2); st.rerun()
            else: st.error("Ticket not found.")
