# ==============================================================================
# SSS G-ABAY v23.14 (Revised - PLATINUM COMPLETE)
# "Visuals: V23.12 | Protection: V23.13 | Access & Integrity: V23.14"
# COPYRIGHT: © 2026 rpt/sssgingoog
# ==============================================================================
# FINAL BUILD NOTES:
#   - RESTORED: CSS Visual Engine (Jumbo Fonts, 6-Col Grid) from v23.12
#   - RESTORED: Full Admin Modules (Exemptions, Resources, etc.) from v23.13
#   - FIXED: GATE Transactions (Routed to Counter Lane)
#   - FIXED: Duplicate User ID Check
#   - FIXED: Kiosk Menu "Add Item"
#   - FIXED: "Call Next" Logic
# ==============================================================================

import streamlit as st
import pandas as pd
import datetime
import time
import uuid
import json
import os
import re
import html
import plotly.express as px
import shutil
import glob
import copy

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
st.set_page_config(page_title="SSS G-ABAY v23.14", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

# ==============================================================================
# ABSOLUTE PATH RESOLUTION
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "sss_data.json")
BACKUP_FILE = os.path.join(SCRIPT_DIR, "sss_data.bak")
ARCHIVE_FILE = os.path.join(SCRIPT_DIR, "sss_archive.json")
LOCK_FILE = os.path.join(SCRIPT_DIR, "sss_data.json.lock")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "backups")
CORRUPT_DIR = os.path.join(SCRIPT_DIR, "corrupt_files")

# ==============================================================================
# CONFIGURABLE CONSTANTS
# ==============================================================================
UTC_OFFSET_HOURS = 8
MIN_VALID_FILE_SIZE = 500
MAX_HOURLY_BACKUPS = 24
ARCHIVE_RETENTION_DAYS = 365
SESSION_TIMEOUT_MINUTES = 30
PARK_GRACE_MINUTES = 60
AUDIT_LOG_MAX_ENTRIES = 10000
DISPLAY_GRID_COLUMNS = 6

# --- LANES ---
LANE_CODES = {
    "T": {"name": "Teller", "desc": "Payments", "color": "#DC2626", "icon": "💳"},
    "A": {"name": "Employer", "desc": "Account Mgmt", "color": "#16A34A", "icon": "💼"},
    "C": {"name": "Counter", "desc": "Complex Trans", "color": "#2563EB", "icon": "👤"},
    "E": {"name": "eCenter", "desc": "Online Services", "color": "#2563EB", "icon": "💻"},
    "F": {"name": "Fast Lane", "desc": "Simple Trans", "color": "#2563EB", "icon": "⚡"},
    "GATE": {"name": "Screening", "desc": "Assessment", "color": "#7C3AED", "icon": "🛡️"}
}
LANE_NAME_TO_CODE = {"Teller": "T", "Employer": "A", "eCenter": "E", "Counter": "C", "Fast Lane": "F"}
LANE_CODE_TO_NAME = {v: k for k, v in LANE_NAME_TO_CODE.items()}
LANE_TO_CATEGORY = {"T": "PAYMENTS", "A": "EMPLOYERS", "C": "MEMBER SERVICES", "E": "MEMBER SERVICES", "F": "MEMBER SERVICES"}

# --- STATUS ---
TICKET_STATUSES = {
    "WAITING": {"label": "Waiting", "color": "#3B82F6", "desc": "In queue"},
    "SERVING": {"label": "Serving", "color": "#F59E0B", "desc": "Being served"},
    "PARKED": {"label": "Parked", "color": "#EF4444", "desc": "On hold"},
    "COMPLETED": {"label": "Completed", "color": "#10B981", "desc": "Finished"},
    "NO_SHOW": {"label": "No Show", "color": "#6B7280", "desc": "Client missing"},
    "EXPIRED": {"label": "Expired", "color": "#6B7280", "desc": "Midnight expiry"},
    "SYSTEM_CLOSED": {"label": "System Closed", "color": "#6B7280", "desc": "Auto-closed"}
}

# --- ROLES & PERMISSIONS ---
STAFF_ROLES = ["MSR", "TELLER", "AO", "SECTION_HEAD", "BRANCH_HEAD", "DIV_HEAD", "ADMIN"]
ADMIN_ROLES = ["ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]
SUPERVISOR_ROLES = ("BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD") # Hidden from TV
POWER_ROLES = ["ADMIN", "BRANCH_HEAD"] # Can see Users/Audit

ROLE_COLORS = {
    "TELLER": {"ready_color": "#DC2626", "border_color": "#DC2626", "lane": "T"},
    "AO": {"ready_color": "#16A34A", "border_color": "#16A34A", "lane": "A"},
    "MSR": {"ready_color": "#2563EB", "border_color": "#2563EB", "lane": "C"},
    "ADMIN": {"ready_color": "#6B7280", "border_color": "#6B7280", "lane": None},
    "BRANCH_HEAD": {"ready_color": "#6B7280", "border_color": "#6B7280", "lane": None},
    "SECTION_HEAD": {"ready_color": "#6B7280", "border_color": "#6B7280", "lane": None},
    "DIV_HEAD": {"ready_color": "#6B7280", "border_color": "#6B7280", "lane": None}
}
DEFAULT_ROLE_COLORS = {"ready_color": "#22c55e", "border_color": "#ccc", "lane": None}

# ==============================================================================
# 2. UTILITIES
# ==============================================================================
def get_ph_time():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=UTC_OFFSET_HOURS)

def sanitize_text(text):
    if not text: return ""
    return html.escape(str(text))

def clean_transaction_name(name):
    if not name: return ""
    return re.sub(r'\s+', ' ', str(name).strip())

USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{3,20}$')
def validate_user_id(user_id):
    if not user_id: return False, "User ID cannot be empty"
    if not USER_ID_PATTERN.match(user_id): return False, "User ID must be 3-20 alphanumeric characters"
    return True, "Valid"

# --- DEFAULTS ---
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
        "counter_map": [
            {"name": "Counter 1", "type": "Counter"},
            {"name": "Counter 2", "type": "Counter"},
            {"name": "Teller 1", "type": "Teller"},
            {"name": "Teller 2", "type": "Teller"},
            {"name": "Employer Desk", "type": "Employer"},
            {"name": "eCenter", "type": "eCenter"}
        ],
        "assignments": {"Counter": ["C","F","E"], "Teller": ["T"], "Employer": ["A"], "eCenter": ["E"], "Help": ["F","E"]}
    },
    "menu": {
        "Benefits": [("Maternity / Sickness", "Ben-Mat/Sick", "E"), ("Disability / Unemployment", "Ben-Dis/Unemp", "E"), ("Retirement", "Ben-Retirement", "GATE"), ("Death", "Ben-Death", "GATE"), ("Funeral", "Ben-Funeral", "GATE")],
        "Loans": [("Salary / Conso", "Ln-Sal/Conso", "E"), ("Calamity / Emergency", "Ln-Cal/Emerg", "E"), ("Pension Loan", "Ln-Pension", "E")],
        "Member Records": [("Contact Info Update", "Rec-Contact", "F"), ("Simple Correction", "Rec-Simple", "F"), ("Complex Correction", "Rec-Complex", "C"), ("Verification", "Rec-Verify", "C")],
        "eServices": [("My.SSS Reset", "eSvc-Reset", "E"), ("SS Number", "eSvc-SSNum", "E"), ("Status Inquiry", "eSvc-Status", "E"), ("DAEM / ACOP", "eSvc-DAEM/ACOP", "E")]
    },
    "staff": {
        "admin": {"pass": "sss2026", "role": "ADMIN", "name": "System Admin", "nickname": "Admin", "default_station": "Counter 1", "status": "ACTIVE", "online": False},
    }
}

# ==============================================================================
# 3. CSS VISUAL ENGINE (RESTORED FROM V23.12)
# ==============================================================================
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
    
    /* JUMBO CARD CSS - STRICT GRID OPTIMIZED */
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
    
    /* LEVEL 1: TICKET NUMBER */
    .jumbo-ticket {
        font-size: 11vw !important;
        font-weight: 900 !important;
        line-height: 1.0 !important;
        margin: 0 !important;
        padding: 10px 0 !important;
    }
    
    /* LEVEL 2: COUNTER NAME */
    .jumbo-counter {
        font-size: 1.8vw !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        color: #333;
        margin-bottom: 0px !important;
        line-height: 1.2 !important;
    }
    
    /* LEVEL 3: STAFF NICKNAME */
    .jumbo-staff {
        font-size: 1.4vw !important;
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

# ==============================================================================
# 4. DATA PROTECTION ENGINE
# ==============================================================================
def quarantine_corrupt_file(file_path, reason="unknown"):
    try:
        if not os.path.exists(CORRUPT_DIR): os.makedirs(CORRUPT_DIR)
        timestamp = get_ph_time().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        quarantine_name = f"{timestamp}_{reason}_{filename}"
        shutil.move(file_path, os.path.join(CORRUPT_DIR, quarantine_name))
    except: pass

def safe_load_json(file_path):
    try:
        if not os.path.exists(file_path): return None, False, "File not found"
        if os.path.getsize(file_path) < MIN_VALID_FILE_SIZE: return None, False, "File too small"
        with open(file_path, "r", encoding="utf-8") as f: data = json.load(f)
        if not isinstance(data, dict): return None, False, "Invalid structure"
        if not isinstance(data.get("staff"), dict) or len(data["staff"]) < 1: return None, False, "Empty staff"
        return data, True, None
    except Exception as e: return None, False, str(e)

def cascade_load_data():
    data, success, error = safe_load_json(DATA_FILE)
    if success: return data, "primary"
    
    data, success, error = safe_load_json(BACKUP_FILE)
    if success:
        if os.path.exists(DATA_FILE): quarantine_corrupt_file(DATA_FILE, "primary_corrupt")
        return data, "backup"
    
    if os.path.exists(BACKUP_DIR):
        backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "sss_data_*.json")), key=lambda x: os.path.getmtime(x), reverse=True)
        for b in backups[:10]:
            data, success, error = safe_load_json(b)
            if success: return data, f"hourly_{os.path.basename(b)}"
    
    if not os.path.exists(DATA_FILE) and not os.path.exists(BACKUP_FILE):
        return copy.deepcopy(DEFAULT_DATA), "first_run"
    
    st.session_state['data_load_failed'] = True
    return None, "FAILED"

def save_db(data):
    lock = acquire_file_lock()
    try:
        if lock: lock.acquire()
        create_hourly_backup()
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, default=str, indent=2)
            f.flush(); os.fsync(f.fileno())
        
        if os.path.getsize(temp_file) < MIN_VALID_FILE_SIZE: raise IOError("Save verification failed")
        
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) >= MIN_VALID_FILE_SIZE:
            shutil.copy2(DATA_FILE, BACKUP_FILE)
        
        os.replace(temp_file, DATA_FILE)
    finally:
        if lock and lock.is_locked: lock.release()

def create_hourly_backup():
    try:
        if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
        timestamp = get_ph_time().strftime("%Y%m%d_%H")
        backup_file = os.path.join(BACKUP_DIR, f"sss_data_{timestamp}.json")
        if os.path.exists(DATA_FILE) and not os.path.exists(backup_file):
            if os.path.getsize(DATA_FILE) >= MIN_VALID_FILE_SIZE: shutil.copy2(DATA_FILE, backup_file)
    except: pass

def acquire_file_lock(timeout=10):
    return FileLock(LOCK_FILE, timeout=timeout) if FILE_LOCK_AVAILABLE else None

def log_audit(action, user_name, details=None, target=None):
    try:
        local_db = load_db()
        if 'audit_log' not in local_db: local_db['audit_log'] = []
        local_db['audit_log'].append({
            "timestamp": get_ph_time().isoformat(), "action": action, "user": user_name,
            "target": target, "details": details
        })
        if len(local_db['audit_log']) > AUDIT_LOG_MAX_ENTRIES: 
            local_db['audit_log'] = local_db['audit_log'][-AUDIT_LOG_MAX_ENTRIES:]
        save_db(local_db)
    except: pass

# ==============================================================================
# 5. DATABASE ENGINE
# ==============================================================================
def load_db():
    current_date = get_ph_time().strftime("%Y-%m-%d")
    lock = acquire_file_lock()
    try:
        if lock: lock.acquire()
        data, source = cascade_load_data()
        
        if data is None:
            return {"_LOAD_FAILED": True, "staff": {}, "tickets": [], "config": {"branch_name": "ERROR"}}
        
        # Schema migration
        if "PAYMENTS" in data.get("menu", {}): data["menu"] = copy.deepcopy(DEFAULT_DATA["menu"])
        for key in DEFAULT_DATA:
            if key not in data: data[key] = copy.deepcopy(DEFAULT_DATA[key])
        
        # MIDNIGHT SWEEPER
        if data.get("system_date") != current_date:
            # POPULATION GUARD
            staff_count = len(data.get('staff', {}))
            if staff_count <= 1 and source != "first_run":
                if 'audit_log' not in data: data['audit_log'] = []
                data['audit_log'].append({
                    "timestamp": get_ph_time().isoformat(), "action": "POPULATION_GUARD_TRIGGERED",
                    "user": "SYSTEM", "details": f"Rollover blocked. Staff count: {staff_count}"
                })
                st.session_state['_guard_triggered'] = True
                return data 

            # Rollover Logic
            serving = [t for t in data.get('tickets', []) if t.get('status') == 'SERVING']
            for t in serving:
                t['status'] = 'SYSTEM_CLOSED'; t['end_time'] = get_ph_time().isoformat()
                t['auto_close_reason'] = 'MIDNIGHT_ROLLOVER'; data['history'].append(t)
            
            pending = [t for t in data.get('tickets', []) if t.get('status') in ['WAITING', 'PARKED']]
            for t in pending:
                t['status'] = 'EXPIRED'; t['end_time'] = get_ph_time().isoformat()
                t['auto_close_reason'] = 'MIDNIGHT_EXPIRY'; data['history'].append(t)
            
            data['tickets'] = []
            
            # Archive
            if os.path.exists(ARCHIVE_FILE):
                try: 
                    with open(ARCHIVE_FILE, "r") as af: ar = json.load(af)
                except: ar = []
            else: ar = []
            
            ar.append({
                "date": data.get("system_date"), "history": data.get("history", []),
                "incident_log": data.get("incident_log", []), "audit_log": data.get("audit_log", [])
            })
            # Prune Archive
            cutoff = (get_ph_time() - datetime.timedelta(days=ARCHIVE_RETENTION_DAYS)).strftime("%Y-%m-%d")
            ar = [x for x in ar if x.get('date', '9999') >= cutoff]
            
            try:
                with open(ARCHIVE_FILE, "w") as af: json.dump(ar, af, default=str)
            except: pass
            
            data["history"] = []; data["incident_log"] = []; data["audit_log"] = []
            data["system_date"] = current_date
            
            for uid in data.get('staff', {}):
                data['staff'][uid]['status'] = "ACTIVE"
                data['staff'][uid]['online'] = False
            
            # Persist Rollover
            try:
                if lock and lock.is_locked: lock.release()
                save_db(data)
                if lock: lock.acquire()
            except: pass
            
        return data
    finally:
        if lock and lock.is_locked: lock.release()

# ==============================================================================
# 6. CORE INIT
# ==============================================================================
db = load_db()
if db.get('_LOAD_FAILED'): 
    st.error("CRITICAL DATA FAILURE. Check backups folder."); st.stop()

if 'surge_mode' not in st.session_state: st.session_state['surge_mode'] = False
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())[:8]
if 'last_activity' not in st.session_state: st.session_state['last_activity'] = get_ph_time()

def update_activity(): st.session_state['last_activity'] = get_ph_time()

def check_session_timeout():
    if 'user' not in st.session_state: return False
    elapsed = (get_ph_time() - st.session_state.get('last_activity', get_ph_time())).total_seconds() / 60
    if elapsed >= SESSION_TIMEOUT_MINUTES: handle_safe_logout("TIMEOUT"); return True
    if st.session_state.get('login_date') != get_ph_time().strftime("%Y-%m-%d"): handle_safe_logout("ROLLOVER"); return True
    return False

def handle_safe_logout(reason="MANUAL"):
    if 'user' not in st.session_state: return
    try:
        local_db = load_db()
        user = st.session_state['user']
        key = next((k for k,v in local_db['staff'].items() if v['name'] == user['name']), None)
        if key:
            local_db['staff'][key]['online'] = False
            t = next((x for x in local_db['tickets'] if x['status'] == 'SERVING' and x.get('served_by_staff') == user['name']), None)
            if t: t['status'] = 'PARKED'; t['park_timestamp'] = get_ph_time().isoformat()
            save_db(local_db)
            log_audit("LOGOUT", user.get('name', 'Unknown'), details=f"Reason: {reason}")
    except: pass
    for k in ['user', 'refer_modal']: 
        if k in st.session_state: del st.session_state[k]

# ==============================================================================
# 7. HELPER LOGIC
# ==============================================================================
def get_staff_lanes(user, config):
    station = user.get('default_station', '')
    counter_obj = next((c for c in config['counter_map'] if c['name'] == station), None)
    if counter_obj:
        return config['assignments'].get(counter_obj['type'], [])
    role_lanes = {"TELLER": ["T"], "AO": ["A"], "MSR": ["C", "E", "F"]}
    return role_lanes.get(user.get('role'), ["C", "E", "F"])

def generate_ticket_manual(service, lane, is_priority, is_appt=False, appt_name=None, appt_time=None, assign_counter=None):
    local_db = load_db()
    count = len(local_db['tickets']) + len(local_db['history']) + 1
    num = f"APT-{count:03d}" if is_appt else f"{count:03d}"
    
    t = {
        "id": str(uuid.uuid4()), "number": num, "lane": lane, 
        "service": service, "type": "APPOINTMENT" if is_appt else ("PRIORITY" if is_priority else "REGULAR"),
        "status": "WAITING", "timestamp": get_ph_time().isoformat(),
        "appt_name": appt_name, "appt_time": str(appt_time) if appt_time else None,
        "assigned_to": assign_counter, "history": []
    }
    local_db['tickets'].append(t)
    save_db(local_db)
    return t

# ==============================================================================
# 8. MODULES
# ==============================================================================
def render_kiosk():
    st.markdown(f"<h1 style='text-align:center'>{db['config']['branch_name']}</h1>", unsafe_allow_html=True)
    if 'kiosk_step' not in st.session_state:
        c1, c2 = st.columns(2)
        with c1: 
            if st.button("👤 REGULAR", use_container_width=True): st.session_state.update({'is_prio': False, 'kiosk_step': 'menu'}); st.rerun()
        with c2: 
            if st.button("❤️ PRIORITY", use_container_width=True): st.session_state.update({'is_prio': True, 'kiosk_step': 'menu'}); st.rerun()
    
    elif st.session_state['kiosk_step'] == 'menu':
        st.subheader("Select Service")
        cols = st.columns(2)
        categories = list(db['menu'].keys())
        
        for i, cat_name in enumerate(categories):
            with cols[i % 2]:
                st.write(f"**{cat_name}**")
                for label, code, lane in db['menu'].get(cat_name, []):
                    if st.button(label, key=code, use_container_width=True):
                        # FIX: Route GATE transactions to Counter queue
                        final_lane = "C" if lane == "GATE" else lane 
                        generate_ticket_callback(code, final_lane, st.session_state['is_prio'])
                        st.rerun()
        
        st.markdown("---")
        if st.button("⬅ Back to Home"): del st.session_state['kiosk_step']; st.rerun()

    elif st.session_state['kiosk_step'] == 'ticket':
        t = st.session_state['last_ticket']
        st.success(f"Ticket: {t['number']}")
        if st.button("Done"): del st.session_state['kiosk_step']; st.rerun()

def generate_ticket_callback(service, lane, prio):
    local_db = load_db()
    num = f"{len(local_db['tickets']) + len(local_db['history']) + 1:03d}"
    t = {"id": str(uuid.uuid4()), "number": num, "lane": lane, "service": service, "type": "PRIORITY" if prio else "REGULAR", "status": "WAITING", "timestamp": get_ph_time().isoformat()}
    local_db['tickets'].append(t)
    save_db(local_db)
    st.session_state['last_ticket'] = t
    st.session_state['kiosk_step'] = 'ticket'

def render_display():
    check_session_timeout()
    local_db = load_db()
    
    curr_audio = local_db.get('latest_announcement', {})
    if curr_audio.get('id') != st.session_state.get('last_audio_id') and curr_audio.get('text'):
        st.session_state['last_audio_id'] = curr_audio['id']
        st.markdown(f"<script>window.speechSynthesis.speak(new SpeechSynthesisUtterance('{sanitize_text(curr_audio['text'])}'));</script>", unsafe_allow_html=True)

    st.markdown(f"<h1 style='text-align:center; color:#0038A8'>NOW SERVING</h1>", unsafe_allow_html=True)
    
    staff_list = [s for s in local_db['staff'].values() if s.get('online') and s['role'] not in SUPERVISOR_ROLES and s['role'] != 'ADMIN']
    unique_map = {}
    for s in staff_list:
        st_name = s.get('default_station', 'Unassigned')
        if st_name not in unique_map:
            unique_map[st_name] = s
        else:
            serving = next((t for t in local_db['tickets'] if t['status']=='SERVING' and t.get('served_by_staff')==s['name']), None)
            if serving: unique_map[st_name] = s
            
    final_staff = list(unique_map.values())
    
    for i in range(0, len(final_staff), DISPLAY_GRID_COLUMNS):
        batch = final_staff[i:i+DISPLAY_GRID_COLUMNS]
        cols = st.columns(DISPLAY_GRID_COLUMNS)
        for idx, staff in enumerate(batch):
            with cols[idx]:
                role = staff.get('role', 'MSR')
                colors = ROLE_COLORS.get(role, DEFAULT_ROLE_COLORS)
                t = next((x for x in local_db['tickets'] if x['status']=='SERVING' and x.get('served_by_staff')==staff['name']), None)
                if not t: 
                    t = next((x for x in local_db['tickets'] if x['status']=='SERVING' and x.get('served_by')==staff.get('default_station') and not x.get('served_by_staff')), None)
                
                border = colors['border_color']
                if t:
                    ln_col = LANE_CODES.get(t.get('lane'), {}).get('color', '#000')
                    st.markdown(f"<div style='border-left:10px solid {ln_col}; padding:10px; background:#fff; text-align:center'><h3>{t['number']}</h3><small>{staff.get('default_station')}</small></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='border-left:10px solid {border}; padding:10px; background:#fff; text-align:center'><h3 style='color:{colors['ready_color']}'>READY</h3><small>{staff.get('default_station')}</small></div>", unsafe_allow_html=True)
    
    # RESTORED MARQUEE
    marquee_text = " | ".join(local_db.get('announcements', ["Welcome to SSS"]))
    st.markdown(f"""
        <div style='position:fixed; bottom:0; left:0; width:100%; background:#DC2626; color:white; padding:10px; font-weight:bold; font-size:24px;'>
            <marquee>{sanitize_text(marquee_text)}</marquee>
        </div>
    """, unsafe_allow_html=True)
    
    time.sleep(3)
    st.rerun()

def render_counter(user):
    check_session_timeout()
    update_activity()
    local_db = load_db()
    st.sidebar.title(f"👮 {user['name']}")
    
    with st.sidebar.expander("🔒 Change Password"):
        with st.form("pwd_chg"):
            n_pass = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                key = next((k for k,v in local_db['staff'].items() if v['name'] == user['name']), None)
                if key: 
                    local_db['staff'][key]['pass'] = n_pass
                    save_db(local_db); st.success("Updated!"); st.rerun()

    if st.sidebar.button("Logout"): handle_safe_logout("MANUAL"); st.rerun()
    
    my_t = next((t for t in local_db['tickets'] if t['status']=='SERVING' and t.get('served_by_staff')==user['name']), None)
    
    c1, c2 = st.columns(2)
    with c1:
        if my_t:
            st.metric("Serving", my_t['number'])
            
            all_txns = []
            user_role = user.get('role', 'MSR')
            
            allowed_cats = []
            if user_role == 'TELLER': allowed_cats = ["PAYMENTS"]
            elif user_role == 'AO': allowed_cats = ["EMPLOYERS"]
            elif user_role == 'MSR': allowed_cats = ["MEMBER SERVICES"]
            else: allowed_cats = ["PAYMENTS", "EMPLOYERS", "MEMBER SERVICES"] 
            
            for cat in allowed_cats:
                if cat in local_db['transaction_master']:
                    for item in local_db['transaction_master'][cat]:
                        all_txns.append(f"[{cat}] {item}")
            
            with st.expander("📝 Reality Log (IOMS)", expanded=True):
                new_txn = st.selectbox("Add Transaction", all_txns)
                if st.button("➕ Add"):
                    if 'actual_transactions' not in my_t: my_t['actual_transactions'] = []
                    clean_txn = new_txn.split("] ")[1] if "]" in new_txn else new_txn
                    category = new_txn.split("] ")[0].replace("[","") if "]" in new_txn else "GENERAL"
                    my_t['actual_transactions'].append({"txn": clean_txn, "category": category, "staff": user['name'], "timestamp": get_ph_time().isoformat()})
                    save_db(local_db); st.rerun()
                
                if my_t.get('actual_transactions'):
                    st.write("---")
                    for i, txn in enumerate(my_t['actual_transactions']):
                        col_text, col_del = st.columns([4, 1])
                        col_text.text(f"• {txn['txn']}")
                        if col_del.button("🗑", key=f"del_{i}"):
                            my_t['actual_transactions'].pop(i)
                            save_db(local_db); st.rerun()

            st.write("---")
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("✅ Complete", use_container_width=True, type="primary"):
                    if not my_t.get('actual_transactions'): st.error("Log a transaction first!")
                    else:
                        my_t['status'] = 'COMPLETED'; my_t['end_time'] = get_ph_time().isoformat()
                        local_db['history'].append(my_t)
                        local_db['tickets'] = [x for x in local_db['tickets'] if x['id'] != my_t['id']]
                        save_db(local_db); log_audit("COMPLETE", user['name'], target=my_t['number']); st.rerun()
            with b_col2:
                if st.button("🅿️ Park", use_container_width=True):
                    my_t['status'] = 'PARKED'; my_t['park_timestamp'] = get_ph_time().isoformat()
                    save_db(local_db); log_audit("PARK", user['name'], target=my_t['number']); st.rerun()

        else:
            if st.button("Call Next", type="primary"):
                my_lanes = get_staff_lanes(user, local_db['config'])
                q = sorted([x for x in local_db['tickets'] if x['status']=='WAITING' and x['lane'] in my_lanes], key=lambda x: x['timestamp'])
                
                if q:
                    nxt = q[0]
                    nxt['status'] = 'SERVING'
                    nxt['served_by_staff'] = user['name']
                    nxt['served_by'] = user.get('default_station')
                    nxt['start_time'] = get_ph_time().isoformat()
                    local_db['latest_announcement'] = {"text": f"Ticket {nxt['number']}, please proceed to {user.get('default_station')}", "id": str(uuid.uuid4())}
                    save_db(local_db)
                    log_audit("TICKET_CALL", user.get('name', 'Unknown'), target=nxt['number'])
                    st.rerun()
                else: st.warning("Queue empty for your lane.")
    
    with c2:
        st.metric("Status", "Serving" if my_t else "IDLE")
        st.divider()
        st.write("🅿️ **Parked Tickets**")
        my_lanes = get_staff_lanes(user, local_db['config'])
        parked = [t for t in local_db['tickets'] if t['status']=='PARKED' and t['lane'] in my_lanes]
        
        for p in parked:
            if st.button(f"🔊 Recall {p['number']}", key=p['id']):
                p['status'] = 'SERVING'
                p['served_by_staff'] = user['name']
                p['served_by'] = user.get('default_station')
                p['start_time'] = get_ph_time().isoformat()
                local_db['latest_announcement'] = {"text": f"Ticket {p['number']}, please return to {user.get('default_station')}", "id": str(uuid.uuid4())}
                save_db(local_db)
                log_audit("RECALL", user['name'], target=p['number'])
                st.rerun()

def render_admin_panel(user):
    update_activity()
    st.title("Admin Console")
    if st.sidebar.button("Logout"): handle_safe_logout("MANUAL"); st.rerun()
    
    if st.session_state.get('_guard_triggered'):
        st.error("⚠️ POPULATION GUARD: Midnight rollover was blocked because staff count was too low (possible glitch). Check Users.")
        if st.button("Dismiss Alert"): del st.session_state['_guard_triggered']; st.rerun()

    tabs = ["Dashboard", "Reports", "IOMS Master", "Book Appt", "Kiosk Menu", "Counters", "Resources", "Exemptions", "Announcements", "Backup"]
    
    is_power_user = user['role'] in POWER_ROLES
    if is_power_user:
        tabs.extend(["Users", "Audit Log", "System Info"])
    
    active = st.radio("Module", tabs, horizontal=True)

    if active == "Dashboard":
        local_db = load_db()
        st.subheader("Branch Analytics")
        hist = local_db.get('history', [])
        if hist:
            df = pd.DataFrame(hist)
            st.metric("Total Transactions", len(df))
            if not df.empty and 'service' in df.columns:
                fig = px.pie(df, names='service', title='Service Mix')
                st.plotly_chart(fig)
        else: st.info("No data yet.")

    elif active == "IOMS Master":
        local_db = load_db()
        st.subheader("Manage Transaction List")
        current_master = local_db.get('transaction_master', DEFAULT_TRANSACTIONS)
        
        c1, c2, c3 = st.columns(3)
        with c1: st.write("**PAYMENTS**"); p_list = st.data_editor(pd.DataFrame(current_master.get("PAYMENTS", []), columns=["Item"]), num_rows="dynamic", key="de_pay")
        with c2: st.write("**EMPLOYERS**"); e_list = st.data_editor(pd.DataFrame(current_master.get("EMPLOYERS", []), columns=["Item"]), num_rows="dynamic", key="de_emp")
        with c3: st.write("**MEMBER SERVICES**"); m_list = st.data_editor(pd.DataFrame(current_master.get("MEMBER SERVICES", []), columns=["Item"]), num_rows="dynamic", key="de_mem")
        
        if st.button("Save Master List"):
            clean_p = list(dict.fromkeys([clean_transaction_name(x) for x in p_list["Item"].tolist() if x]))
            clean_e = list(dict.fromkeys([clean_transaction_name(x) for x in e_list["Item"].tolist() if x]))
            clean_m = list(dict.fromkeys([clean_transaction_name(x) for x in m_list["Item"].tolist() if x]))
            local_db['transaction_master'] = {"PAYMENTS": clean_p, "EMPLOYERS": clean_e, "MEMBER SERVICES": clean_m}
            save_db(local_db)
            log_audit("IOMS_MASTER_UPDATE", user.get('name', 'Unknown'), details="Auto-cleaned and saved")
            st.success("Updated & Cleaned!")
            st.rerun()

    elif active == "Reports":
        st.subheader("IOMS Reports")
        local_db = load_db()
        c1, c2 = st.columns(2)
        d_range = c1.date_input("Date Range", [get_ph_time().date(), get_ph_time().date()])
        
        if len(d_range) == 2:
            start, end = d_range
            all_txns_flat = []
            
            sources = [local_db.get('history', [])]
            if os.path.exists(ARCHIVE_FILE):
                try:
                    with open(ARCHIVE_FILE, 'r') as af:
                        sources.extend([day.get('history', []) for day in json.load(af)])
                except: pass
            
            for source in sources:
                for t in source:
                    try: t_date = datetime.datetime.fromisoformat(t.get('timestamp', '')).date()
                    except: continue
                    if start <= t_date <= end:
                        if t.get('actual_transactions'):
                            for act in t['actual_transactions']:
                                all_txns_flat.append({
                                    "Category": act.get('category', 'GENERAL'),
                                    "Transaction": act.get('txn', 'Unknown')
                                })
            
            if all_txns_flat:
                df = pd.DataFrame(all_txns_flat)
                t1, t2 = st.tabs(["Detailed View (Category)", "Consolidated View (Total)"])
                with t1:
                    summary = df.groupby(['Category', 'Transaction']).size().reset_index(name='Volume')
                    st.dataframe(summary, use_container_width=True)
                with t2:
                    consolidated = df.groupby(['Transaction']).size().reset_index(name='Total Volume')
                    consolidated = consolidated.sort_values(by='Total Volume', ascending=False)
                    st.dataframe(consolidated, use_container_width=True)
            else: st.info("No records found.")

    elif active == "Book Appt":
        st.subheader("Book Appointment")
        local_db = load_db()
        with st.form("admin_appt"):
            nm = st.text_input("Client Name"); tm = st.time_input("Time Slot"); svc = st.text_input("Transaction"); ctr = st.selectbox("Assign to Counter", [""] + [c['name'] for c in local_db.get('config',{}).get('counter_map',[])])
            if st.form_submit_button("Book"):
                generate_ticket_manual(svc, "C", True, is_appt=True, appt_name=nm, appt_time=tm, assign_counter=ctr)
                st.success("Booked")

    elif active == "Kiosk Menu":
        st.subheader("Kiosk Configuration")
        local_db = load_db()
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
                        save_db(local_db); st.rerun()
                    if st.button("Delete", key=f"del_{i}"): 
                        local_db['menu'][sel_cat].pop(i); save_db(local_db); st.rerun()
            
            # FIX: ADD NEW ITEM FORM
            st.markdown("---")
            st.write("Add New Item")
            with st.form("add_new_m"):
                nl = st.text_input("Label")
                nc = st.text_input("Code")
                nln = st.selectbox("Lane", ["C", "E", "F", "T", "A", "GATE"])
                if st.form_submit_button("Add Item"):
                    local_db['menu'][sel_cat].append((nl, nc, nln))
                    save_db(local_db); st.rerun()

    elif active == "Counters":
        local_db = load_db()
        for i, c in enumerate(local_db['config']['counter_map']): 
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            c1.text(c['name']); c2.text(c['type'])
            if c4.button("🗑", key=f"dc_{i}"): local_db['config']['counter_map'].pop(i); save_db(local_db); st.rerun()
        with st.form("add_counter"): 
            cn = st.text_input("Name"); ct = st.selectbox("Type", ["Counter", "Teller", "Employer", "eCenter"])
            if st.form_submit_button("Add"): local_db['config']['counter_map'].append({"name": cn, "type": ct}); save_db(local_db); st.rerun()

    elif active == "Users":
        st.subheader("User Management")
        local_db = load_db()
        if local_db['staff']:
            df_users = pd.DataFrame.from_dict(local_db['staff'], orient='index')
            df_users.index.name = 'User ID'
            st.dataframe(df_users)
        
        with st.form("add_u"):
            uid = st.text_input("ID")
            nm = st.text_input("Name")
            rl = st.selectbox("Role", STAFF_ROLES)
            if st.form_submit_button("Add"):
                # FIX: PREVENT OVERWRITE
                if uid in local_db['staff']: st.error("User ID already exists!")
                elif uid and nm:
                    local_db['staff'][uid] = {"name": nm, "role": rl, "pass": "123", "status": "ACTIVE", "online": False}
                    save_db(local_db); st.success("Added"); st.rerun()
    
    elif active == "Audit Log":
        local_db = load_db()
        st.dataframe(local_db.get('audit_log', []))
        
    elif active == "Backup":
        st.subheader("Backup & Recovery")
        local_db = load_db()
        st.download_button("📥 Backup Now", data=json.dumps(local_db), file_name="sss_backup.json")

    elif active == "System Info":
        st.subheader("System Information")
        st.code("SSS G-ABAY v23.14 (Revised)\nData Protection: Active\nAccess Control: Active")
        
    elif active == "Resources":
        local_db = load_db()
        st.subheader("Info Hub Manager")
        for i, res in enumerate(local_db.get('resources', [])):
            with st.expander(f"{res['label']}"):
                if st.button("Delete", key=f"rd_{i}"): local_db['resources'].pop(i); save_db(local_db); st.rerun()
        with st.form("nr"):
            l = st.text_input("Label"); v = st.text_input("Value"); t = st.selectbox("Type", ["LINK", "FAQ"])
            if st.form_submit_button("Add"): local_db['resources'].append({"type": t, "label": l, "value": v}); save_db(local_db); st.rerun()
            
    elif active == "Exemptions":
        local_db = load_db()
        st.subheader("Exemptions Manager")
        for k in ["Retirement", "Death", "Funeral"]:
            st.write(f"**{k}**")
            for i, ex in enumerate(local_db['exemptions'].get(k, [])):
                c1, c2 = st.columns([4,1])
                c1.text(ex)
                if c2.button("Del", key=f"del_{k}_{i}"): local_db['exemptions'][k].pop(i); save_db(local_db); st.rerun()
            new_e = st.text_input(f"Add {k} Exemption", key=f"ne_{k}")
            if st.button(f"Add {k}", key=f"ba_{k}"): 
                 local_db['exemptions'][k].append(new_e); save_db(local_db); st.rerun()

    elif active == "Announcements":
        local_db = load_db()
        st.subheader("Marquee Manager")
        curr = " | ".join(local_db.get('announcements', []))
        new_txt = st.text_area("Marquee Text", value=curr)
        if st.button("Update"): 
            local_db['announcements'] = [new_txt]; save_db(local_db); st.success("Updated!"); st.rerun()

# ==========================================
# 9. ROUTER
# ==========================================
params = st.query_params
mode = params.get("mode")

if mode == "kiosk": render_kiosk()
elif mode == "display": render_display()
elif mode == "staff":
    if 'user' not in st.session_state:
        u = st.text_input("User"); p = st.text_input("Pass", type="password")
        if st.button("Login"):
            db = load_db()
            user = next((v for k,v in db['staff'].items() if v['name']==u and v['pass']==p), None)
            if user: 
                st.session_state['user'] = user
                st.session_state['login_date'] = get_ph_time().strftime("%Y-%m-%d")
                user['online'] = True; save_db(db)
                log_audit("LOGIN", user['name'])
                st.rerun()
            else: st.error("Fail")
    else:
        user = st.session_state['user']
        if user['role'] in ADMIN_ROLES: render_admin_panel(user)
        else: render_counter(user)
else:
    st.info("Select mode: ?mode=kiosk | ?mode=staff | ?mode=display")
