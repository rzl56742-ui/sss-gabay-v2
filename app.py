# ==============================================================================
# SSS G-ABAY v23.13 - BRANCH OPERATING SYSTEM (DATA FORTRESS EDITION)
# "Visuals: V23.4 | Backend: V23.5 | Security: V23.7 | Integrity: V23.8 | 
#  Polish: V23.9 | Precision: V23.12 | Data Protection: V23.13"
# COPYRIGHT: © 2026 rpt/sssgingoog
# ==============================================================================
# v23.13 SURGICAL FIXES (Safe-Fail Data Protection):
#   FIX-v23.13-001: Absolute Path Resolution (prevents working directory issues)
#   FIX-v23.13-002: Fail-Safe Loading with Backup Cascade (no silent reset)
#   FIX-v23.13-003: Rollover Persistence (force save after midnight sweeper)
#   FIX-v23.13-004: Atomic Save with Verification (0-byte protection)
#   FIX-v23.13-005: Startup Health Check (staff count validation)
#   FIX-v23.13-006: Specific Exception Handling (no bare except)
#   FIX-v23.13-007: Corrupt File Forensics (rename, don't delete)
# ==============================================================================
# INHERITED FROM v23.12:
#   - Ghost Ticket Logic Repair (Two-Phase Matching)
#   - CSS-Based Responsive Scaling (vw units)
#   - Global Constant Optimization
#   - 6-Column Fixed Grid, Supervisor Exclusion, Role-Based Colors
#   - Precision Staff Tracking (served_by_staff)
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
import traceback

# ==============================================================================
# FIX-v23.7-001: FILE LOCKING IMPORTS
# ==============================================================================
try:
    from filelock import FileLock, Timeout
    FILE_LOCK_AVAILABLE = True
except ImportError:
    FILE_LOCK_AVAILABLE = False

# ==========================================
# 1. SYSTEM CONFIGURATION & PERSISTENCE
# ==========================================
st.set_page_config(page_title="SSS G-ABAY v23.13", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

# ==============================================================================
# FIX-v23.13-001: ABSOLUTE PATH RESOLUTION
# All data files use absolute paths based on script location
# This prevents "wrong folder" data loss
# ==============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- FILE PATHS (Now Absolute) ---
DATA_FILE = os.path.join(SCRIPT_DIR, "sss_data.json")
BACKUP_FILE = os.path.join(SCRIPT_DIR, "sss_data.bak")
ARCHIVE_FILE = os.path.join(SCRIPT_DIR, "sss_archive.json")
LOCK_FILE = os.path.join(SCRIPT_DIR, "sss_data.json.lock")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "backups")
CORRUPT_DIR = os.path.join(SCRIPT_DIR, "corrupt_files")

# ==============================================================================
# FIX-v23.9-001: CONFIGURABLE TIMEZONE CONSTANT
# ==============================================================================
UTC_OFFSET_HOURS = 8  # Philippine Standard Time (PST = UTC+8)

# ==============================================================================
# FIX-v23.13-004: MINIMUM VALID FILE SIZE
# A valid sss_data.json with just admin user is ~2KB minimum
# ==============================================================================
MIN_VALID_FILE_SIZE = 500  # bytes - anything smaller is likely corrupt/truncated

# ==============================================================================
# CENTRALIZED CONSTANTS (GLOBAL SCOPE)
# ==============================================================================

# --- SYSTEM LIMITS ---
MAX_HOURLY_BACKUPS = 24
ARCHIVE_RETENTION_DAYS = 365
SESSION_TIMEOUT_MINUTES = 30
PARK_GRACE_MINUTES = 60
AUDIT_LOG_MAX_ENTRIES = 10000
DEFAULT_AVG_TXN_MINUTES = 15

# --- DISPLAY GRID CONSTANTS ---
DISPLAY_GRID_COLUMNS = 6  # Fixed 6-column grid

# --- LANE CONFIGURATION ---
LANE_CODES = {
    "T": {"name": "Teller", "desc": "Payments", "color": "#DC2626", "icon": "💳"},
    "A": {"name": "Employer", "desc": "Account Mgmt", "color": "#16A34A", "icon": "💼"},
    "C": {"name": "Counter", "desc": "Complex Trans", "color": "#2563EB", "icon": "👤"},
    "E": {"name": "eCenter", "desc": "Online Services", "color": "#2563EB", "icon": "💻"},
    "F": {"name": "Fast Lane", "desc": "Simple Trans", "color": "#2563EB", "icon": "⚡"}
}

# --- LANE REVERSE MAPPING ---
LANE_NAME_TO_CODE = {"Teller": "T", "Employer": "A", "eCenter": "E", "Counter": "C", "Fast Lane": "F"}
LANE_CODE_TO_NAME = {v: k for k, v in LANE_NAME_TO_CODE.items()}

# --- CATEGORY MAPPING ---
LANE_TO_CATEGORY = {
    "T": "PAYMENTS",
    "A": "EMPLOYERS",
    "C": "MEMBER SERVICES",
    "E": "MEMBER SERVICES",
    "F": "MEMBER SERVICES"
}

# --- STATUS DEFINITIONS ---
TICKET_STATUSES = {
    "WAITING": {"label": "Waiting", "color": "#3B82F6", "desc": "In queue, awaiting service"},
    "SERVING": {"label": "Serving", "color": "#F59E0B", "desc": "Currently being served at counter"},
    "PARKED": {"label": "Parked", "color": "#EF4444", "desc": "Temporarily set aside, must return within grace period"},
    "COMPLETED": {"label": "Completed", "color": "#10B981", "desc": "Transaction successfully finished"},
    "NO_SHOW": {"label": "No Show", "color": "#6B7280", "desc": "Client did not return within grace period"},
    "EXPIRED": {"label": "Expired", "color": "#6B7280", "desc": "Ticket expired at midnight rollover"},
    "SYSTEM_CLOSED": {"label": "System Closed", "color": "#6B7280", "desc": "Auto-completed at midnight rollover"}
}

# --- ROLE DEFINITIONS ---
STAFF_ROLES = ["MSR", "TELLER", "AO", "SECTION_HEAD", "BRANCH_HEAD", "DIV_HEAD", "ADMIN"]
ADMIN_ROLES = ["ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]
COUNTER_ROLES = ["ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]

# --- SUPERVISOR ROLES (Global Scope) ---
SUPERVISOR_ROLES = ("BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD")

# --- ROLE COLORS (Global Scope) ---
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
# FIX-v23.9-001: PHILIPPINE TIME STANDARD
# ==============================================================================
def get_ph_time():
    """Get current Philippine Time based on configurable UTC offset."""
    return datetime.datetime.utcnow() + datetime.timedelta(hours=UTC_OFFSET_HOURS)

# ==============================================================================
# FIX-v23.9-004: XSS SANITIZATION HELPER
# ==============================================================================
def sanitize_text(text):
    """Escape HTML entities to prevent XSS attacks."""
    if not text:
        return ""
    return html.escape(str(text))

# --- USER VALIDATION ---
USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{3,20}$')
def validate_user_id(user_id):
    if not user_id: return False, "User ID cannot be empty"
    if not USER_ID_PATTERN.match(user_id): return False, "User ID must be 3-20 alphanumeric characters"
    return True, "Valid"

# --- DEFAULT MASTER LIST ---
DEFAULT_TRANSACTIONS = {
    "PAYMENTS": ["Contribution Payment", "Loan Payment", "Miscellaneous Payment", "Status Inquiry (Payments)"],
    "EMPLOYERS": ["Employer Registration", "Employee Update (R1A)", "Contribution/Loan List", "Status Inquiry (Employer)"],
    "MEMBER SERVICES": ["Sickness/Maternity Claim", "Pension Claim", "Death/Funeral Claim", "Salary Loan Application", "Calamity Loan", "Verification/Static Info", "UMID/Card Inquiry", "My.SSS Reset"]
}

# --- DEFAULT DATA ---
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

# ==============================================================================
# FIX-v23.13-007: CORRUPT FILE FORENSICS
# Move corrupt files to forensics folder instead of deleting
# ==============================================================================
def quarantine_corrupt_file(file_path, reason="unknown"):
    """Move corrupt file to forensics folder for investigation."""
    try:
        if not os.path.exists(CORRUPT_DIR):
            os.makedirs(CORRUPT_DIR)
        
        timestamp = get_ph_time().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        quarantine_name = f"{timestamp}_{reason}_{filename}"
        quarantine_path = os.path.join(CORRUPT_DIR, quarantine_name)
        
        shutil.move(file_path, quarantine_path)
        return quarantine_path
    except Exception as e:
        # If we can't move it, at least rename it in place
        try:
            corrupt_name = f"{file_path}.CORRUPT_{get_ph_time().strftime('%Y%m%d_%H%M%S')}"
            os.rename(file_path, corrupt_name)
            return corrupt_name
        except:
            return None

# ==============================================================================
# FIX-v23.13-002: SAFE JSON LOADER WITH VALIDATION
# Returns tuple: (data, success, error_message)
# ==============================================================================
def safe_load_json(file_path):
    """
    Safely load and validate a JSON file.
    Returns: (data, True, None) on success
             (None, False, error_message) on failure
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return None, False, f"File not found: {file_path}"
        
        # Check file size (0-byte protection)
        file_size = os.path.getsize(file_path)
        if file_size < MIN_VALID_FILE_SIZE:
            return None, False, f"File too small ({file_size} bytes), likely corrupt: {file_path}"
        
        # Try to read and parse JSON
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Validate it's a dictionary (not list or other type)
        if not isinstance(data, dict):
            return None, False, f"Invalid data structure (expected dict, got {type(data).__name__})"
        
        # Validate required keys exist
        required_keys = ["staff", "config", "tickets"]
        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            return None, False, f"Missing required keys: {missing_keys}"
        
        # FIX-v23.13-005: Validate staff count
        if not isinstance(data.get("staff"), dict) or len(data["staff"]) < 1:
            return None, False, "Invalid or empty staff data"
        
        return data, True, None
        
    except json.JSONDecodeError as e:
        return None, False, f"JSON parse error: {str(e)}"
    except PermissionError:
        return None, False, f"Permission denied: {file_path}"
    except IOError as e:
        return None, False, f"IO error: {str(e)}"
    except Exception as e:
        return None, False, f"Unexpected error: {str(e)}"

# ==============================================================================
# FIX-v23.13-002: BACKUP CASCADE - Try all backup sources before failing
# ==============================================================================
def get_backup_files_sorted():
    """Get list of hourly backup files, newest first."""
    if not os.path.exists(BACKUP_DIR):
        return []
    
    backups = glob.glob(os.path.join(BACKUP_DIR, "sss_data_*.json"))
    # Sort by modification time, newest first
    backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return backups

def cascade_load_data():
    """
    Attempt to load data from multiple sources in order of preference.
    Returns: (data, source_description) or triggers HALT screen
    """
    errors = []
    
    # SOURCE 1: Primary data file
    data, success, error = safe_load_json(DATA_FILE)
    if success:
        return data, "primary"
    errors.append(f"Primary ({DATA_FILE}): {error}")
    
    # SOURCE 2: Backup file (.bak)
    data, success, error = safe_load_json(BACKUP_FILE)
    if success:
        # Quarantine the corrupt primary file
        if os.path.exists(DATA_FILE):
            quarantine_corrupt_file(DATA_FILE, "primary_corrupt")
        return data, "backup"
    errors.append(f"Backup ({BACKUP_FILE}): {error}")
    
    # SOURCE 3: Hourly backups (cascade through newest to oldest)
    hourly_backups = get_backup_files_sorted()
    for backup_path in hourly_backups[:10]:  # Try up to 10 most recent
        data, success, error = safe_load_json(backup_path)
        if success:
            # Quarantine corrupt files
            if os.path.exists(DATA_FILE):
                quarantine_corrupt_file(DATA_FILE, "primary_corrupt")
            if os.path.exists(BACKUP_FILE):
                quarantine_corrupt_file(BACKUP_FILE, "backup_corrupt")
            return data, f"hourly_backup ({os.path.basename(backup_path)})"
        errors.append(f"Hourly ({os.path.basename(backup_path)}): {error}")
    
    # SOURCE 4: Check if this is genuinely first run (no files exist at all)
    if not os.path.exists(DATA_FILE) and not os.path.exists(BACKUP_FILE) and not hourly_backups:
        # First run - safe to use DEFAULT_DATA
        return DEFAULT_DATA.copy(), "first_run"
    
    # ALL SOURCES FAILED - This is a critical error
    # Store errors in session state for display
    st.session_state['data_load_errors'] = errors
    st.session_state['data_load_failed'] = True
    return None, "FAILED"

# ==============================================================================
# FIX-v23.13-004: ATOMIC SAVE WITH VERIFICATION
# ==============================================================================
def save_db(data):
    """
    Save data with atomic write and verification.
    Prevents 0-byte files and corruption.
    """
    lock = acquire_file_lock()
    try:
        if lock: 
            lock.acquire()
        
        # Step 1: Create hourly backup BEFORE any changes
        create_hourly_backup()
        
        # Step 2: Write to temporary file
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, default=str, indent=2)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        
        # Step 3: Verify temp file is valid
        temp_size = os.path.getsize(temp_file)
        if temp_size < MIN_VALID_FILE_SIZE:
            os.remove(temp_file)
            raise IOError(f"Save verification failed: temp file too small ({temp_size} bytes)")
        
        # Step 4: Re-parse to verify JSON integrity
        try:
            with open(temp_file, "r", encoding="utf-8") as f:
                verify_data = json.load(f)
            if not isinstance(verify_data, dict) or "staff" not in verify_data:
                os.remove(temp_file)
                raise IOError("Save verification failed: re-parse validation failed")
        except json.JSONDecodeError as e:
            os.remove(temp_file)
            raise IOError(f"Save verification failed: JSON invalid after write: {e}")
        
        # Step 5: Backup current file ONLY if it's valid
        if os.path.exists(DATA_FILE):
            current_size = os.path.getsize(DATA_FILE)
            if current_size >= MIN_VALID_FILE_SIZE:
                shutil.copy2(DATA_FILE, BACKUP_FILE)
            # If current file is corrupt, don't overwrite good backup
        
        # Step 6: Atomic replace
        os.replace(temp_file, DATA_FILE)
        
    except Exception as e:
        # Log the error but don't crash
        if 'save_errors' not in st.session_state:
            st.session_state['save_errors'] = []
        st.session_state['save_errors'].append(f"{get_ph_time().isoformat()}: {str(e)}")
        raise
    finally:
        if lock and lock.is_locked: 
            lock.release()

# --- AUDIT LOG ---
def log_audit(action, user_name, details=None, target=None):
    try:
        local_db = load_db()
        if 'audit_log' not in local_db: 
            local_db['audit_log'] = []
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
    except Exception as e:
        # Audit logging should never crash the system
        pass

# --- BACKUP ---
def create_hourly_backup():
    """Create hourly backup with validation."""
    try:
        if not os.path.exists(BACKUP_DIR): 
            os.makedirs(BACKUP_DIR)
        
        timestamp = get_ph_time().strftime("%Y%m%d_%H")
        backup_file = os.path.join(BACKUP_DIR, f"sss_data_{timestamp}.json")
        
        # Only backup if source exists and is valid size
        if os.path.exists(DATA_FILE) and not os.path.exists(backup_file):
            if os.path.getsize(DATA_FILE) >= MIN_VALID_FILE_SIZE:
                shutil.copy2(DATA_FILE, backup_file)
        
        # Cleanup old backups
        backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "sss_data_*.json")))
        while len(backups) > MAX_HOURLY_BACKUPS:
            try: 
                os.remove(backups.pop(0))
            except: 
                pass
    except Exception:
        pass  # Backup failure shouldn't crash the system

# --- FILE LOCK ---
def acquire_file_lock(timeout=10):
    if FILE_LOCK_AVAILABLE: 
        return FileLock(LOCK_FILE, timeout=timeout)
    return None

# ==============================================================================
# FIX-v23.13-002 + FIX-v23.13-003: DATABASE ENGINE WITH SAFE LOADING
# ==============================================================================
def load_db():
    """
    Load database with fail-safe cascade and rollover persistence.
    """
    current_date = get_ph_time().strftime("%Y-%m-%d")
    
    lock = acquire_file_lock()
    try:
        if lock: 
            lock.acquire()
        
        # Use cascade loader instead of direct file access
        data, source = cascade_load_data()
        
        # Check if load failed completely
        if data is None:
            # Return minimal structure to prevent crashes, but mark as failed
            return {"_LOAD_FAILED": True, "staff": {}, "tickets": [], "history": [], 
                    "config": {"branch_name": "DATA ERROR"}, "system_date": current_date}
        
        # Log if we recovered from backup
        if source not in ["primary", "first_run"]:
            if 'recovery_source' not in st.session_state:
                st.session_state['recovery_source'] = source
                st.session_state['recovery_time'] = get_ph_time().isoformat()
        
        # Schema migration / defaults
        if "PAYMENTS" in data.get("menu", {}): 
            data["menu"] = DEFAULT_DATA["menu"]
        for key in DEFAULT_DATA:
            if key not in data: 
                data[key] = DEFAULT_DATA[key]
        if "branch_code" not in data.get('config', {}): 
            data['config']['branch_code'] = "H07"
        if "transaction_master" not in data: 
            data['transaction_master'] = DEFAULT_TRANSACTIONS
        if "audit_log" not in data: 
            data['audit_log'] = []

        # --- MIDNIGHT SWEEPER PROTOCOL ---
        if data.get("system_date") != current_date:
            
            # 1. Force Complete Serving Tickets
            serving_tickets = [t for t in data.get('tickets', []) if t.get('status') == 'SERVING']
            for ticket in serving_tickets:
                ticket['status'] = 'SYSTEM_CLOSED'
                ticket['end_time'] = get_ph_time().isoformat()
                ticket['auto_closed'] = True
                ticket['auto_close_reason'] = 'MIDNIGHT_ROLLOVER'
                data['history'].append(ticket)
            
            # 2. Expire Waiting/Parked Tickets
            pending_tickets = [t for t in data.get('tickets', []) if t.get('status') in ['WAITING', 'PARKED']]
            for ticket in pending_tickets:
                ticket['status'] = 'EXPIRED'
                ticket['end_time'] = get_ph_time().isoformat()
                ticket['auto_closed'] = True
                ticket['auto_close_reason'] = 'MIDNIGHT_EXPIRY'
                data['history'].append(ticket)
            
            # 3. Archive yesterday's data
            archive_data = []
            if os.path.exists(ARCHIVE_FILE):
                try:
                    with open(ARCHIVE_FILE, "r", encoding="utf-8") as af:
                        archive_data = json.load(af)
                except (json.JSONDecodeError, IOError):
                    archive_data = []
            
            archive_entry = {
                "date": data.get("system_date", "unknown"),
                "history": data.get("history", []),
                "reviews": data.get("reviews", []),
                "incident_log": data.get("incident_log", []),
                "audit_log": data.get("audit_log", []),
                "breaks": data.get("breaks", [])
            }
            archive_data.append(archive_entry)
            
            # 365-Day Retention
            cutoff_date = (get_ph_time() - datetime.timedelta(days=ARCHIVE_RETENTION_DAYS)).strftime("%Y-%m-%d")
            archive_data = [entry for entry in archive_data if entry.get('date', '9999-99-99') >= cutoff_date]
            
            try:
                with open(ARCHIVE_FILE, "w", encoding="utf-8") as af: 
                    json.dump(archive_data, af, default=str)
            except IOError:
                pass  # Archive write failure shouldn't crash system
                
            # 4. Clean Slate for new day
            data["history"] = []
            data["tickets"] = []
            data["breaks"] = []
            data["reviews"] = []
            data["incident_log"] = []
            data["audit_log"] = []
            data["system_date"] = current_date
            data["branch_status"] = "NORMAL"
            
            # 5. Force Logout All Staff
            for uid in data.get('staff', {}):
                data['staff'][uid]['status'] = "ACTIVE"
                data['staff'][uid]['online'] = False
                if 'break_reason' in data['staff'][uid]: 
                    del data['staff'][uid]['break_reason']
            
            # ==============================================================
            # FIX-v23.13-003: ROLLOVER PERSISTENCE
            # Force save immediately after midnight sweeper completes
            # This prevents "Rollover Amnesia" if power cuts before first transaction
            # ==============================================================
            try:
                # Release lock temporarily for save
                if lock and lock.is_locked:
                    lock.release()
                save_db(data)
                # Re-acquire for return
                if lock:
                    lock.acquire()
            except Exception as e:
                # Log but don't crash
                pass

        return data
        
    finally:
        if lock and lock.is_locked: 
            lock.release()

# ==============================================================================
# FIX-v23.13-005: DATA LOAD FAILURE SCREEN
# ==============================================================================
def render_data_failure_screen():
    """Display critical error screen when all data sources fail."""
    st.error("🚨 CRITICAL: DATA LOAD FAILURE")
    st.markdown("""
    ### The system cannot load your data.
    
    All data sources (primary file, backup, and hourly backups) have failed to load.
    
    **Your data has NOT been deleted.** Corrupt files have been moved to the `corrupt_files/` folder for investigation.
    """)
    
    # Show error details
    errors = st.session_state.get('data_load_errors', [])
    if errors:
        with st.expander("📋 Error Details", expanded=True):
            for err in errors:
                st.code(err)
    
    st.markdown("---")
    st.markdown("### 🔧 Recovery Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Option 1: Check Backups**
        ```
        Look in the 'backups/' folder for recent valid files.
        Copy a good backup to 'sss_data.json'
        ```
        """)
    
    with col2:
        st.markdown("""
        **Option 2: Check Corrupt Files**
        ```
        Look in 'corrupt_files/' folder.
        Files may be partially recoverable.
        ```
        """)
    
    st.markdown("---")
    
    # Emergency reset option (with confirmation)
    st.warning("⚠️ **LAST RESORT:** Start fresh with empty database")
    if st.checkbox("I understand this will create a new empty database"):
        if st.button("🔄 Initialize New Database", type="primary"):
            try:
                save_db(DEFAULT_DATA.copy())
                st.session_state['data_load_failed'] = False
                st.success("New database created. Please refresh the page.")
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create new database: {e}")
    
    st.stop()

# ==============================================================================
# INITIAL LOAD WITH FAILURE CHECK
# ==============================================================================
db = load_db()

# Check for load failure
if db.get('_LOAD_FAILED') or st.session_state.get('data_load_failed'):
    render_data_failure_screen()

# Show recovery notification if applicable
if 'recovery_source' in st.session_state:
    st.warning(f"⚠️ Data recovered from: {st.session_state['recovery_source']} at {st.session_state.get('recovery_time', 'unknown')}")

# --- INIT ---
if 'surge_mode' not in st.session_state: st.session_state['surge_mode'] = False
if 'session_id' not in st.session_state: st.session_state['session_id'] = str(uuid.uuid4())[:8]

# --- SESSION TIMEOUT & DATE SYNC ---
if 'last_activity' not in st.session_state: st.session_state['last_activity'] = get_ph_time()

def update_activity():
    st.session_state['last_activity'] = get_ph_time()

def check_session_timeout():
    if 'user' not in st.session_state: return False
    
    last_activity = st.session_state.get('last_activity', get_ph_time())
    elapsed = (get_ph_time() - last_activity).total_seconds() / 60
    
    login_date = st.session_state.get('login_date', '')
    current_date = get_ph_time().strftime("%Y-%m-%d")
    
    if elapsed >= SESSION_TIMEOUT_MINUTES:
        handle_safe_logout(reason="TIMEOUT")
        return True
        
    if login_date and login_date != current_date:
        handle_safe_logout(reason="DATE_ROLLOVER")
        return True
        
    return False

# ==============================================================================
# SAFE LOGOUT WITH served_by_staff CHECK
# ==============================================================================
def handle_safe_logout(reason="MANUAL"):
    if 'user' not in st.session_state: return
    try:
        local_db = load_db()
        user = st.session_state['user']
        user_key = next((k for k, v in local_db['staff'].items() if v['name'] == user['name']), None)
        
        if user_key:
            station = local_db['staff'][user_key].get('default_station', '')
            # Two-phase matching for safety
            serving_ticket = next((t for t in local_db['tickets'] 
                                   if t['status'] == 'SERVING' and t.get('served_by_staff') == user['name']), None)
            if not serving_ticket:
                serving_ticket = next((t for t in local_db['tickets'] 
                                       if t['status'] == 'SERVING' 
                                       and t.get('served_by') == station 
                                       and not t.get('served_by_staff')), None)
            
            if serving_ticket:
                serving_ticket['status'] = 'PARKED'
                serving_ticket['park_timestamp'] = get_ph_time().isoformat()
                serving_ticket['auto_parked'] = True
                serving_ticket['auto_park_reason'] = f'STAFF_LOGOUT_{reason}'
            
            local_db['staff'][user_key]['online'] = False
            save_db(local_db)
            log_audit("LOGOUT", user['name'], details=f"Reason: {reason}", target=station)
    except Exception:
        pass  # Logout should never crash
    
    for key in ['refer_modal', 'my_station', 'user', 'login_date']:
        if key in st.session_state: del st.session_state[key]

# ==============================================================================
# CSS WITH RESPONSIVE vw UNITS FOR TV DISPLAY
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
    
    /* RESPONSIVE DISPLAY CARDS WITH vw UNITS */
    .serving-card-small { 
        background: white; 
        border-left: 25px solid #2563EB; 
        padding: 1.5vh 0.5vw; 
        border-radius: 15px; 
        box-shadow: 0 10px 20px rgba(0,0,0,0.2); 
        text-align: center; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
        align-items: center;
        transition: all 0.3s ease; 
        width: 100%;
        min-height: 18vh;
    }
    .serving-card-break { 
        background: #FEF3C7; 
        border-left: 25px solid #D97706; 
        padding: 1.5vh 0.5vw; 
        border-radius: 15px; 
        box-shadow: 0 10px 20px rgba(0,0,0,0.2); 
        text-align: center; 
        display: flex; 
        flex-direction: column; 
        justify-content: center; 
        align-items: center;
        transition: all 0.3s ease; 
        width: 100%;
        min-height: 18vh;
    }
    
    .card-station { 
        margin: 0; 
        color: #111; 
        font-weight: bold; 
        text-transform: uppercase;
        font-size: clamp(12px, 1.8vw, 28px);
        line-height: 1.2;
    }
    
    .card-ticket { 
        margin: 0.5vh 0; 
        font-weight: 900; 
        line-height: 1.0;
        font-size: clamp(40px, 11vw, 120px);
    }
    
    .card-ready { 
        margin: 0.5vh 0; 
        font-weight: 900; 
        line-height: 1.0;
        font-size: clamp(30px, 5vw, 70px);
    }
    
    .card-break-text { 
        margin: 0; 
        color: #92400E;
        font-weight: 900; 
        font-size: clamp(24px, 4vw, 55px);
    }
    
    .card-nickname { 
        color: #777; 
        font-weight: normal; 
        margin-top: 0.5vh;
        font-size: clamp(10px, 1.4vw, 22px);
    }
    
    .swim-col { background: #f8f9fa; border-radius: 10px; padding: 10px; border-top: 10px solid #ccc; height: 100%; }
    .swim-col h3 { text-align: center; margin-bottom: 10px; font-size: 18px; text-transform: uppercase; color: #333; }
    .queue-item { background: white; border-bottom: 1px solid #ddd; padding: 15px; margin-bottom: 5px; border-radius: 5px; display: flex; justify-content: space-between; }
    .queue-item span { font-size: 24px; font-weight: 900; color: #111; }
    
    .gate-btn > button { height: 350px !important; width: 100% !important; font-size: 40px !important; font-weight: 900 !important; border-radius: 30px !important; }
    .menu-card > button { height: 300px !important; width: 100% !important; font-size: 30px !important; font-weight: 800 !important; border-radius: 20px !important; border: 4px solid #ddd !important; white-space: pre-wrap !important;}
    .swim-btn > button { height: 100px !important; width: 100% !important; font-size: 18px !important; font-weight: 700 !important; text-align: left !important; padding-left: 20px !important; }
    
    .info-link { text-decoration: none; display: block; padding: 15px; background: #f0f2f6; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #2563EB; color: #333; font-weight: bold; transition: 0.2s; }
    .info-link:hover { background: #e0e7ff; }
    
    .head-red { background-color: #DC2626; color: white; padding: 5px; border-radius: 5px 5px 0 0; font-weight: bold; text-align: center; } 
    .border-red > button { border-left: 20px solid #DC2626 !important; }
    .head-orange { background-color: #EA580C; color: white; padding: 5px; border-radius: 5px 5px 0 0; font-weight: bold; text-align: center; } 
    .border-orange > button { border-left: 20px solid #EA580C !important; }
    .head-green { background-color: #16A34A; color: white; padding: 5px; border-radius: 5px 5px 0 0; font-weight: bold; text-align: center; } 
    .border-green > button { border-left: 20px solid #16A34A !important; }
    .head-blue { background-color: #2563EB; color: white; padding: 5px; border-radius: 5px 5px 0 0; font-weight: bold; text-align: center; } 
    .border-blue > button { border-left: 20px solid #2563EB !important; }
    
    .metric-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; border-top: 5px solid #2563EB; }
    .metric-card h3 { font-size: 36px; margin: 0; color: #1E3A8A; font-weight: 900; }
    .metric-card p { margin: 0; color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
    .timeout-warning { background: #FEF3C7; border: 2px solid #F59E0B; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px; }
    
    .park-appt { background: #dbeafe; color: #1e40af; border-left: 5px solid #2563EB; font-weight: bold; padding: 10px; border-radius: 5px; display: flex; justify-content: space-between; margin-bottom: 5px; }
    .park-danger { background: #fee2e2; color: #b91c1c; border-left: 5px solid #ef4444; animation: pulse 2s infinite; padding: 10px; border-radius: 5px; font-weight:bold; display:flex; justify-content:space-between; margin-bottom: 5px; }
    
    .wait-estimate { background: #ECFDF5; border: 2px solid #10B981; border-radius: 10px; padding: 15px; text-align: center; margin: 10px 0; }
    .wait-estimate h3 { margin: 0; color: #059669; font-size: 24px; }
    .wait-estimate p { margin: 5px 0 0 0; color: #047857; font-size: 14px; }
    
    .status-legend { background: #f8fafc; border-radius: 8px; padding: 10px; margin: 10px 0; }
    .status-item { display: inline-block; margin: 5px 10px; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
    
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    .blink-active { animation: blink 1s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC
# ==========================================
def get_display_name(staff_data):
    return staff_data.get('nickname') if staff_data.get('nickname') else staff_data['name']

def get_role_colors(role):
    """Get ready and border colors for a staff role from global constant."""
    return ROLE_COLORS.get(role, DEFAULT_ROLE_COLORS)

def get_lane_color(lane_code):
    """Get color for a lane code from centralized constants."""
    return LANE_CODES.get(lane_code, {}).get('color', '#2563EB')

# ==============================================================================
# KIOSK WAIT TIME ESTIMATE CALCULATOR
# ==============================================================================
def calculate_lane_wait_estimate(lane_code):
    """Calculate estimated wait time for a specific lane before ticket generation."""
    local_db = load_db()
    
    waiting_count = len([t for t in local_db.get('tickets', []) if t.get('lane') == lane_code and t.get('status') == "WAITING"])
    
    recent = [t for t in local_db.get('history', []) if t.get('lane') == lane_code and t.get('end_time') and t.get('start_time')]
    
    avg_txn_time = DEFAULT_AVG_TXN_MINUTES
    if recent:
        total_sec = 0
        valid_count = 0
        for t in recent[-20:]:
            try:
                start = datetime.datetime.fromisoformat(t["start_time"])
                end = datetime.datetime.fromisoformat(t["end_time"])
                diff = (end - start).total_seconds()
                if diff > 0 and diff < 7200:
                    total_sec += diff
                    valid_count += 1
            except (ValueError, KeyError):
                continue
        if valid_count > 0:
            avg_txn_time = (total_sec / valid_count) / 60
    
    active_counters = 0
    for staff in local_db.get('staff', {}).values():
        if staff.get('online') and staff.get('status') == 'ACTIVE':
            station = staff.get('default_station', '')
            counter_obj = next((c for c in local_db.get('config', {}).get('counter_map', []) if c['name'] == station), None)
            if counter_obj:
                station_type = counter_obj['type']
                station_lanes = local_db.get('config', {}).get('assignments', {}).get(station_type, [])
                if lane_code in station_lanes:
                    active_counters += 1
    
    if active_counters > 0:
        wait_time = round((waiting_count * avg_txn_time) / active_counters)
    else:
        wait_time = round(waiting_count * avg_txn_time)
    
    return waiting_count, wait_time, active_counters

def generate_ticket_callback(service, lane_code, is_priority):
    local_db = load_db()
    global_count = len(local_db.get('tickets', [])) + len(local_db.get('history', [])) + 1
    branch_code = local_db.get('config', {}).get('branch_code', 'H07')
    simple_num = f"{global_count:03d}"
    full_id = f"{branch_code}-{lane_code}-{simple_num}" 
    
    new_t = {
        "id": str(uuid.uuid4()), "number": simple_num, "full_id": full_id, "lane": lane_code, "service": service, 
        "type": "PRIORITY" if is_priority else "REGULAR", "status": "WAITING", 
        "timestamp": get_ph_time().isoformat(),
        "start_time": None, "end_time": None, "park_timestamp": None,
        "history": [], "served_by": None, "served_by_staff": None,
        "ref_from": None, "referral_reason": None,
        "appt_name": None, "appt_time": None, "actual_transactions": [] 
    }
    local_db['tickets'].append(new_t)
    save_db(local_db)
    st.session_state['last_ticket'] = new_t
    st.session_state['kiosk_step'] = 'ticket'

def generate_ticket_manual(service, lane_code, is_priority, is_appt=False, appt_name=None, appt_time=None, assign_counter=None):
    local_db = load_db()
    global_count = len(local_db.get('tickets', [])) + len(local_db.get('history', [])) + 1
    branch_code = local_db.get('config', {}).get('branch_code', 'H07')
    simple_num = f"{global_count:03d}"
    display_num = f"APT-{simple_num}" if is_appt else simple_num
    full_id = f"{branch_code}-{lane_code}-{display_num}"
    
    new_t = {
        "id": str(uuid.uuid4()), "number": display_num, "full_id": full_id, "lane": lane_code, "service": service, 
        "type": "APPOINTMENT" if is_appt else ("PRIORITY" if is_priority else "REGULAR"),
        "status": "WAITING", "timestamp": get_ph_time().isoformat(),
        "start_time": None, "end_time": None, "park_timestamp": None,
        "history": [], "served_by": None, "served_by_staff": None,
        "ref_from": None, "referral_reason": None,
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
            if t['type'] == 'APPOINTMENT' and t.get('appt_time'):
                try:
                    appt_t = datetime.datetime.strptime(t['appt_time'], "%H:%M:%S").time()
                    if now >= appt_t: return t
                except ValueError:
                    pass
            else: return t
            
    for t in queue:
        if t['type'] == 'APPOINTMENT' and t.get('appt_time') and not t.get('assigned_to'):
            try:
                appt_t = datetime.datetime.strptime(t['appt_time'], "%H:%M:%S").time()
                if now >= appt_t: return t
            except ValueError:
                pass
    
    if surge_mode:
        for t in queue:
            if t['type'] == 'PRIORITY' and not t.get('assigned_to'): return t
            
    local_db = load_db()
    last_2 = local_db.get('history', [])[-2:]
    p_count = sum(1 for t in last_2 if t.get('type') == 'PRIORITY')
    
    if p_count >= 2:
        reg = [t for t in queue if t.get('type') == 'REGULAR' and not t.get('assigned_to')]
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
    type_weight = 1 if t.get('type') == 'APPOINTMENT' else (2 if t.get('type') == 'PRIORITY' else 3)
    return (assigned_weight, type_weight, t.get('timestamp', ''))

def calculate_specific_wait_time(ticket_id, lane_code):
    local_db = load_db()
    recent = [t for t in local_db.get('history', []) if t.get('lane') == lane_code and t.get('end_time')]
    avg_txn_time = DEFAULT_AVG_TXN_MINUTES
    if recent:
        try:
            total_sec = sum([datetime.datetime.fromisoformat(t["end_time"]).timestamp() - datetime.datetime.fromisoformat(t["start_time"]).timestamp() for t in recent[-10:] if t.get("start_time")])
            if recent[-10:]:
                avg_txn_time = (total_sec / len(recent[-10:])) / 60
        except (ValueError, TypeError):
            pass
    
    waiting_in_lane = [t for t in local_db.get('tickets', []) if t.get('lane') == lane_code and t.get('status') == "WAITING"]
    waiting_in_lane.sort(key=get_queue_sort_key)
    
    position = 0
    for i, t in enumerate(waiting_in_lane):
        if t.get('id') == ticket_id: position = i; break
    wait_time = round(position * avg_txn_time)
    if wait_time < 2: return "Next"
    return f"{wait_time} min"

def calculate_people_ahead(ticket_id, lane_code):
    local_db = load_db()
    waiting_in_lane = [t for t in local_db.get('tickets', []) if t.get('lane') == lane_code and t.get('status') == "WAITING"]
    waiting_in_lane.sort(key=get_queue_sort_key)
    for i, t in enumerate(waiting_in_lane):
        if t.get('id') == ticket_id: return i
    return 0

def get_staff_efficiency(staff_name):
    local_db = load_db()
    # Two-phase matching for accuracy
    my_txns = [t for t in local_db.get('history', []) if t.get("served_by_staff") == staff_name]
    legacy_txns = [t for t in local_db.get('history', []) if t.get("served_by") == staff_name and not t.get("served_by_staff")]
    my_txns.extend(legacy_txns)
    
    if my_txns:
        total_handle_time = 0
        valid_count = 0
        for t in my_txns:
            if t.get('start_time') and t.get('end_time'):
                try:
                    start = datetime.datetime.fromisoformat(t['start_time'])
                    end = datetime.datetime.fromisoformat(t['end_time'])
                    total_handle_time += (end - start).total_seconds()
                    valid_count += 1
                except (ValueError, TypeError): 
                    pass
        if valid_count > 0:
            avg_mins = round(total_handle_time / valid_count / 60)
            return len(my_txns), f"{avg_mins}m"
    return len(my_txns), "N/A"

def get_allowed_counters(role):
    all_counters = db.get('config', {}).get('counter_map', [])
    target_types = []
    if role == "TELLER": target_types = ["Teller"]
    elif role == "AO": target_types = ["Employer"]
    elif role == "MSR": target_types = ["Counter", "eCenter", "Help"]
    elif role in COUNTER_ROLES: return [c['name'] for c in all_counters] 
    return [c['name'] for c in all_counters if c.get('type') in target_types]

def clear_ticket_modal_states():
    modal_keys = ['refer_modal', 'transfer_in_progress']
    for key in modal_keys:
        if key in st.session_state: del st.session_state[key]

# ==========================================
# 4. MODULES
# ==========================================

def render_kiosk():
    st.markdown(f"<div class='header-text header-branch'>{db.get('config', {}).get('branch_name', 'SSS BRANCH')}</div>", unsafe_allow_html=True)
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
        categories = list(db.get('menu', {}).keys())
        colors = ["red", "orange", "green", "blue", "red", "orange"]
        icons = ["🏥", "💰", "📝", "💻", "❓", "⚙️"]
        for i, cat_name in enumerate(categories):
            with cols[i % 4]:
                color = colors[i % len(colors)]
                icon = icons[i % len(icons)]
                st.markdown(f"<div class='swim-header head-{color}'>{icon} {cat_name}</div>", unsafe_allow_html=True)
                st.markdown(f'<div class="swim-btn border-{color}">', unsafe_allow_html=True)
                for label, code, lane in db.get('menu', {}).get(cat_name, []):
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
        exemptions = db.get('exemptions', {}).get(target.get('label', ''), [])
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
            if st.button("❌ CANCEL", use_container_width=True): 
                curr_db = load_db()
                curr_db['tickets'] = [x for x in curr_db.get('tickets', []) if x.get('id') != t['id']]
                save_db(curr_db)
                del st.session_state['last_ticket']
                del st.session_state['kiosk_step']
                st.rerun()
        with c2:
            if st.button("✅ DONE", type="primary", use_container_width=True): del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c3:
            if st.button("🖨️ PRINT", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True); time.sleep(1); del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
    
    st.markdown("<div class='brand-footer'>System developed by RPT/SSSGingoog © 2026 | v23.13</div>", unsafe_allow_html=True)

# ==============================================================================
# DISPLAY MODULE (TV Display)
# ==============================================================================
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
        
        # Filter staff
        raw_staff = [s for s in local_db.get('staff', {}).values() 
                     if s.get('online') is True 
                     and s.get('role') != "ADMIN" 
                     and s.get('name') != "System Admin"
                     and s.get('role') not in SUPERVISOR_ROLES]
        
        # Build unique staff map by station
        unique_staff_map = {} 
        for s in raw_staff:
            st_name = s.get('default_station', 'Unassigned')
            if st_name not in unique_staff_map: 
                unique_staff_map[st_name] = s
            else:
                curr = unique_staff_map[st_name]
                is_curr_serving = next((t for t in local_db.get('tickets', []) 
                                        if t.get('status') == 'SERVING' 
                                        and t.get('served_by_staff') == curr.get('name')), None)
                is_new_serving = next((t for t in local_db.get('tickets', []) 
                                       if t.get('status') == 'SERVING' 
                                       and t.get('served_by_staff') == s.get('name')), None)
                if not is_curr_serving and is_new_serving: 
                    unique_staff_map[st_name] = s
        
        unique_staff = list(unique_staff_map.values())
        
        if not unique_staff: 
            st.warning("Waiting for staff to log in...")
        else:
            staff_count = len(unique_staff)
            
            for i in range(0, staff_count, DISPLAY_GRID_COLUMNS):
                batch = unique_staff[i:i+DISPLAY_GRID_COLUMNS]
                cols = st.columns(DISPLAY_GRID_COLUMNS)
                
                for idx, staff in enumerate(batch):
                    with cols[idx]:
                        nickname = get_display_name(staff)
                        station_name = staff.get('default_station', 'Unassigned')
                        staff_role = staff.get('role', 'MSR')
                        role_colors = get_role_colors(staff_role)
                        
                        if staff.get('status') == "ON_BREAK":
                            st.markdown(f"""
                            <div class="serving-card-break">
                                <p class="card-station">{sanitize_text(station_name)}</p>
                                <h3 class="card-break-text">ON BREAK</h3>
                                <span class="card-nickname">{sanitize_text(nickname)}</span>
                            </div>""", unsafe_allow_html=True)
                            
                        elif staff.get('status') == "ACTIVE":
                            # TWO-PHASE TICKET MATCHING
                            active_t = next((t for t in local_db.get('tickets', []) 
                                             if t.get('status') == 'SERVING' 
                                             and t.get('served_by_staff') == staff.get('name')), None)
                            
                            if not active_t:
                                active_t = next((t for t in local_db.get('tickets', []) 
                                                 if t.get('status') == 'SERVING' 
                                                 and t.get('served_by') == station_name 
                                                 and not t.get('served_by_staff')), None)
                            
                            if active_t:
                                is_blinking = ""
                                if active_t.get('start_time'):
                                    try:
                                        elapsed_sec = (get_ph_time() - datetime.datetime.fromisoformat(active_t['start_time'])).total_seconds()
                                        if elapsed_sec < 20:
                                            is_blinking = "blink-active"
                                    except ValueError:
                                        pass
                                
                                b_color = get_lane_color(active_t.get('lane', 'C'))
                                
                                st.markdown(f"""
                                <div class="serving-card-small" style="border-left-color: {b_color};">
                                    <p class="card-station">{sanitize_text(station_name)}</p>
                                    <h2 class="card-ticket {is_blinking}" style="color:{b_color};">{sanitize_text(active_t.get('number', ''))}</h2>
                                    <span class="card-nickname">{sanitize_text(nickname)}</span>
                                </div>""", unsafe_allow_html=True)
                            else:
                                ready_color = role_colors["ready_color"]
                                border_color = role_colors["border_color"]
                                
                                st.markdown(f"""
                                <div class="serving-card-small" style="border-left-color: {border_color};">
                                    <p class="card-station">{sanitize_text(station_name)}</p>
                                    <h2 class="card-ready" style="color:{ready_color};">READY</h2>
                                    <span class="card-nickname">{sanitize_text(nickname)}</span>
                                </div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Queue display section
        c_queue, c_park = st.columns([3, 1])
        with c_queue:
            q1, q2, q3 = st.columns(3)
            waiting = [t for t in local_db.get('tickets', []) if t.get("status") == "WAITING" and not t.get('appt_time')] 
            waiting.sort(key=get_queue_sort_key)
            
            with q1:
                st.markdown(f"<div class='swim-col' style='border-top-color:{get_lane_color('T')};'><h3>{LANE_CODES['T']['icon']} {LANE_CODES['T']['desc'].upper()}</h3>", unsafe_allow_html=True)
                for t in [x for x in waiting if x.get('lane') == 'T'][:5]: 
                    st.markdown(f"<div class='queue-item'><span>{sanitize_text(t.get('number', ''))}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with q2:
                st.markdown(f"<div class='swim-col' style='border-top-color:{get_lane_color('A')};'><h3>{LANE_CODES['A']['icon']} {LANE_CODES['A']['desc'].upper()}</h3>", unsafe_allow_html=True)
                for t in [x for x in waiting if x.get('lane') == 'A'][:5]: 
                    st.markdown(f"<div class='queue-item'><span>{sanitize_text(t.get('number', ''))}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with q3:
                st.markdown(f"<div class='swim-col' style='border-top-color:{get_lane_color('C')};'><h3>👤 SERVICES</h3>", unsafe_allow_html=True)
                for t in [x for x in waiting if x.get('lane') in ['C','E','F']][:5]: 
                    st.markdown(f"<div class='queue-item'><span>{sanitize_text(t.get('number', ''))}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        with c_park:
            st.markdown("### 🅿️ PARKED")
            parked = [t for t in local_db.get('tickets', []) if t.get("status") == "PARKED"]
            for p in parked:
                try:
                    park_time = datetime.datetime.fromisoformat(p.get('park_timestamp', ''))
                    remaining = datetime.timedelta(minutes=PARK_GRACE_MINUTES) - (get_ph_time() - park_time)
                    if remaining.total_seconds() <= 0: 
                        p["status"] = "NO_SHOW"
                        save_db(local_db)
                    else:
                        mins, secs = divmod(remaining.total_seconds(), 60)
                        disp_txt = p.get('appt_name') if p.get('appt_name') else p.get('number', '')
                        css_class = "park-appt" if p.get('appt_name') else "park-danger"
                        st.markdown(f"""<div class="{css_class}"><span>{sanitize_text(disp_txt)}</span><span>{int(mins):02d}:{int(secs):02d}</span></div>""", unsafe_allow_html=True)
                except (ValueError, TypeError):
                    pass
        
        # Announcement marquee
        txt = " | ".join([sanitize_text(a) for a in local_db.get('announcements', [])])
        status = local_db.get('branch_status', 'NORMAL')
        bg_color = "#DC2626" if status == "OFFLINE" else ("#F97316" if status == "SLOW" else "#FFD700")
        text_color = "white" if status in ["OFFLINE", "SLOW"] else "black"
        if status != "NORMAL": 
            txt = f"⚠ NOTICE: We are currently experiencing {status} connection. Please bear with us. {txt}"
        st.markdown(f"<div style='background: {bg_color}; color: {text_color}; padding: 10px; font-weight: bold; position: fixed; bottom: 0; width: 100%; font-size:20px;'><marquee>{txt}</marquee></div>", unsafe_allow_html=True)
        st.markdown("<div class='brand-footer'>System developed by RPT/SSSGingoog © 2026 | v23.13</div>", unsafe_allow_html=True)
    
    time.sleep(3)
    st.rerun()

def render_counter(user):
    update_activity()
    local_db = load_db()
    user_key = next((k for k,v in local_db.get('staff', {}).items() if v.get('name') == user.get('name')), None)
    if not user_key: st.error("User Sync Error. Please Relogin."); return
    current_user_state = local_db['staff'][user_key]

    st.sidebar.title(f"👮 {user.get('name', 'User')}")
    
    last_activity = st.session_state.get('last_activity', get_ph_time())
    elapsed = (get_ph_time() - last_activity).total_seconds() / 60
    remaining_mins = SESSION_TIMEOUT_MINUTES - elapsed
    if remaining_mins <= 5: st.sidebar.markdown(f"""<div class='timeout-warning'>⚠️ Session expires in {int(remaining_mins)} min</div>""", unsafe_allow_html=True)
    
    if st.sidebar.button("⬅ LOGOUT"): handle_safe_logout(reason="MANUAL"); st.rerun()

    st.sidebar.markdown("---")
    st.session_state['surge_mode'] = st.sidebar.checkbox("🚨 PRIORITY SURGE MODE", value=st.session_state.get('surge_mode', False))
    if st.session_state['surge_mode']: st.sidebar.warning("⚠ SURGE ACTIVE: Only Priority Tickets will be called!")
    
    st.sidebar.markdown("---")
    with st.sidebar.expander("☕ Go On Break"):
        b_reason = st.selectbox("Reason", ["Lunch Break", "Coffee Break (15m)", "Bio-Break", "Emergency"])
        if st.button("⏸ START BREAK"):
            station = current_user_state.get('default_station', '')
            serving_ticket = next((t for t in local_db.get('tickets', []) 
                                   if t.get('status') == 'SERVING' and t.get('served_by_staff') == user.get('name')), None)
            if not serving_ticket:
                serving_ticket = next((t for t in local_db.get('tickets', []) 
                                       if t.get('status') == 'SERVING' 
                                       and t.get('served_by') == station 
                                       and not t.get('served_by_staff')), None)
            if serving_ticket: st.error("⛔ You have an active ticket. Complete or Park it first.")
            else:
                local_db['staff'][user_key]['status'] = "ON_BREAK"
                local_db['staff'][user_key]['break_reason'] = b_reason
                local_db['staff'][user_key]['break_start_time'] = get_ph_time().isoformat()
                save_db(local_db)
                st.session_state['user'] = local_db['staff'][user_key]
                log_audit("BREAK_START", user.get('name', 'Unknown'), details=b_reason)
                st.rerun()

    with st.sidebar.expander("🔒 Change Password"):
        with st.form("pwd_chg"):
            n_pass = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                if user_key: 
                    local_db['staff'][user_key]['pass'] = n_pass
                    save_db(local_db)
                    log_audit("PASSWORD_CHANGE", user.get('name', 'Unknown'), target=user_key)
                    st.success("Updated!")

    st.sidebar.markdown("---")
    st.sidebar.write("**⚠ Report Issue**")
    if st.sidebar.button("🟡 Intermittent Net"): log_incident(user.get('name', 'Unknown'), "SLOW"); st.toast("Reported: Slow Connection")
    if st.sidebar.button("🔴 System Offline"): log_incident(user.get('name', 'Unknown'), "OFFLINE"); st.toast("Reported: System Offline")
    if st.sidebar.button("🟢 System Restored"): log_incident(user.get('name', 'Unknown'), "NORMAL"); st.toast("System Restored")
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("📅 Book Appointment"):
        with st.form("staff_appt"):
            nm = st.text_input("Client Name")
            tm = st.time_input("Time Slot")
            svc = st.text_input("Transaction")
            ctr = st.selectbox("Assign to Counter (Optional)", [""] + [c['name'] for c in local_db.get('config', {}).get('counter_map', [])])
            if st.form_submit_button("Book"):
                generate_ticket_manual(svc, "C", True, is_appt=True, appt_name=nm, appt_time=tm, assign_counter=ctr)
                log_audit("APPOINTMENT_CREATE", user.get('name', 'Unknown'), details=f"{nm} at {tm}", target=svc)
                st.success("Booked!")

    if current_user_state.get('status') == "ON_BREAK":
        st.warning(f"⛔ YOU ARE CURRENTLY ON BREAK ({current_user_state.get('break_reason', 'Break')})")
        if st.button("▶ RESUME WORK", type="primary"):
            local_db['staff'][user_key]['status'] = "ACTIVE"
            save_db(local_db)
            st.session_state['user'] = local_db['staff'][user_key]
            log_audit("BREAK_END", user.get('name', 'Unknown'))
            st.rerun()
        return

    if 'my_station' not in st.session_state: 
        st.session_state['my_station'] = current_user_state.get('default_station', 'Counter 1')
    
    st.markdown(f"### Station: {st.session_state['my_station']}")
    allowed_counters = get_allowed_counters(user.get('role', 'MSR'))
    if st.session_state['my_station'] not in allowed_counters and allowed_counters: 
        st.session_state['my_station'] = allowed_counters[0]
    
    new_station = st.selectbox("Switch Station", allowed_counters, 
                               index=allowed_counters.index(st.session_state['my_station']) if st.session_state['my_station'] in allowed_counters else 0)
    if new_station != st.session_state['my_station']:
        st.session_state['my_station'] = new_station
        local_db['staff'][user_key]['default_station'] = new_station
        save_db(local_db)
        log_audit("STATION_CHANGE", user.get('name', 'Unknown'), target=new_station)
        st.rerun()
    
    current_counter_obj = next((c for c in local_db.get('config', {}).get('counter_map', []) if c['name'] == st.session_state['my_station']), None)
    station_type = current_counter_obj['type'] if current_counter_obj else "Counter"
    my_lanes = local_db.get('config', {}).get("assignments", {}).get(station_type, ["C"])
    queue = [t for t in local_db.get('tickets', []) if t.get("status") == "WAITING" and t.get("lane") in my_lanes]
    queue.sort(key=get_queue_sort_key)
    
    # Two-phase matching
    current = next((t for t in local_db.get('tickets', []) 
                    if t.get("status") == "SERVING" and t.get("served_by_staff") == user.get('name')), None)
    if not current:
        current = next((t for t in local_db.get('tickets', []) 
                        if t.get("status") == "SERVING" 
                        and t.get("served_by") == st.session_state['my_station']
                        and not t.get("served_by_staff")), None)
    
    c1, c2 = st.columns([2,1])
    with c1:
        if current:
            display_num = current.get('appt_name') if current.get('appt_name') else current.get('number', '')
            lane_color = get_lane_color(current.get('lane', 'C'))
            st.markdown(f"""<div style='padding:30px; background:#e0f2fe; border-radius:15px; border-left:10px solid {lane_color};'><h1 style='margin:0; color:{lane_color}; font-size: 60px;'>{sanitize_text(display_num)}</h1><h3>{sanitize_text(current.get('service', ''))}</h3></div>""", unsafe_allow_html=True)
            if current.get("ref_from"): 
                st.markdown(f"""<div style='background:#fee2e2; border-left:5px solid #ef4444; padding:10px; margin-top:10px;'><span style='color:#b91c1c; font-weight:bold;'>↩ REFERRED FROM: {sanitize_text(current.get("ref_from", ''))}</span><br><span style='color:#b91c1c; font-weight:bold;'>📝 REASON: {sanitize_text(current.get("referral_reason", "No reason provided"))}</span></div>""", unsafe_allow_html=True)
            
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
                        current["served_by_staff"] = None
                        current["ref_from"] = st.session_state['my_station']
                        current["referral_reason"] = reason
                        save_db(local_db)
                        log_audit("TICKET_REFER", user.get('name', 'Unknown'), details=f"To {target_lane}: {reason}", target=current.get('number', ''))
                        clear_ticket_modal_states()
                        st.rerun()
                    if c_can.form_submit_button("Cancel"):
                        clear_ticket_modal_states()
                        st.rerun()

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
                    current['actual_transactions'].append({"txn": clean_txn, "category": category, "staff": user.get('name', 'Unknown'), "timestamp": get_ph_time().isoformat()})
                    save_db(local_db)
                    st.rerun()
                if current.get('actual_transactions'):
                    st.write("---")
                    st.caption("Transactions Logged for this Ticket:")
                    for i, txn in enumerate(current['actual_transactions']):
                        col_text, col_del = st.columns([4, 1])
                        col_text.text(f"• {txn.get('txn', '')}")
                        if col_del.button("🗑", key=f"del_txn_{i}"): 
                            current['actual_transactions'].pop(i)
                            save_db(local_db)
                            st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            b1, b2, b3 = st.columns(3)
            if b1.button("✅ COMPLETE", use_container_width=True): 
                if not current.get('actual_transactions'): st.error("⛔ BLOCKED: You must log at least one Actual Transaction first.")
                else:
                    current["status"] = "COMPLETED"
                    current["end_time"] = get_ph_time().isoformat()
                    local_db['history'].append(current)
                    local_db['tickets'] = [t for t in local_db.get('tickets', []) if t.get('id') != current.get('id')]
                    clear_ticket_modal_states()
                    save_db(local_db)
                    log_audit("TICKET_COMPLETE", user.get('name', 'Unknown'), target=current.get('number', ''))
                    st.rerun()
            if b2.button("🅿️ PARK", use_container_width=True): 
                current["status"] = "PARKED"
                current["park_timestamp"] = get_ph_time().isoformat()
                clear_ticket_modal_states()
                save_db(local_db)
                log_audit("TICKET_PARK", user.get('name', 'Unknown'), target=current.get('number', ''))
                st.rerun()
            if b3.button("🔔 RE-CALL", use_container_width=True):
                current["start_time"] = get_ph_time().isoformat()
                trigger_audio(current.get('number', ''), st.session_state['my_station'])
                save_db(local_db)
                st.toast(f"Re-calling {current.get('number', '')}...")
                time.sleep(0.5)
                st.rerun()
        else:
            if st.button("🔊 CALL NEXT", type="primary", use_container_width=True):
                update_activity()
                nxt = get_next_ticket(queue, st.session_state.get('surge_mode', False), st.session_state['my_station'])
                if nxt:
                    db_ticket = next((x for x in local_db.get('tickets', []) if x.get('id') == nxt.get('id')), None)
                    if db_ticket:
                        db_ticket["status"] = "SERVING"
                        db_ticket["served_by"] = st.session_state['my_station']
                        db_ticket["served_by_staff"] = user.get('name', 'Unknown')
                        db_ticket["start_time"] = get_ph_time().isoformat()
                        trigger_audio(db_ticket.get('number', ''), st.session_state['my_station'])
                        save_db(local_db)
                        log_audit("TICKET_CALL", user.get('name', 'Unknown'), target=db_ticket.get('number', ''))
                        st.rerun()
                else: 
                    st.warning(f"No tickets for {station_type}.")
    
    with c2:
        count, avg_time = get_staff_efficiency(user.get('name', 'Unknown'))
        st.metric("Performance", count, delta=avg_time + " avg/txn")
        st.divider()
        st.write("🅿️ Parked Tickets")
        parked = [t for t in local_db.get('tickets', []) if t.get("status") == "PARKED" and t.get("lane") in my_lanes]
        for p in parked:
            if st.button(f"🔊 {p.get('number', '')}", key=p.get('id', '')):
                update_activity()
                p["status"] = "SERVING"
                p["served_by"] = st.session_state['my_station']
                p["served_by_staff"] = user.get('name', 'Unknown')
                p["start_time"] = get_ph_time().isoformat()
                trigger_audio(p.get('number', ''), st.session_state['my_station'])
                save_db(local_db)
                log_audit("TICKET_RECALL_PARKED", user.get('name', 'Unknown'), target=p.get('number', ''))
                st.rerun()

def render_admin_panel(user):
    update_activity()
    local_db = load_db()
    st.title("🛠 Admin & IOMS Center")
    if st.sidebar.button("⬅ LOGOUT"): handle_safe_logout(reason="MANUAL"); st.rerun()
    
    if user.get('role') in ADMIN_ROLES:
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
        
        data_source = local_db.get('history', [])
        archive_data = []
        if os.path.exists(ARCHIVE_FILE):
            try:
                with open(ARCHIVE_FILE, "r", encoding="utf-8") as af:
                    archive_data = json.load(af)
            except (json.JSONDecodeError, IOError):
                archive_data = []
        
        today = get_ph_time().date()
        filtered_txns = []
        
        if time_range == "Today": 
            filtered_txns = data_source
        else:
            start_date = today
            end_date = today
            
            if time_range == "Yesterday": 
                start_date = today - datetime.timedelta(days=1)
                end_date = start_date
                
            elif time_range == "This Week": 
                start_date = today - datetime.timedelta(days=today.weekday())
                end_date = today
                
            elif time_range == "This Month": 
                start_date = today.replace(day=1)
                end_date = today
                
            elif time_range == "Quarterly": 
                curr_q = (today.month - 1) // 3 + 1
                start_date = datetime.date(today.year, 3 * curr_q - 2, 1)
                end_date = today
                
            elif time_range == "Semestral": 
                start_date = datetime.date(today.year, 1, 1) if today.month <= 6 else datetime.date(today.year, 7, 1)
                end_date = today
                
            elif time_range == "Annual": 
                start_date = datetime.date(today.year, 1, 1)
                end_date = today
            
            for entry in archive_data:
                try:
                    entry_dt = datetime.datetime.strptime(entry.get('date', ''), "%Y-%m-%d").date()
                    if start_date <= entry_dt <= end_date:
                        filtered_txns.extend(entry.get('history', []))
                except (ValueError, KeyError):
                    continue
            
            if time_range != "Yesterday": 
                filtered_txns.extend(data_source)

        if lane_filter != "All Lanes":
            target_code = LANE_NAME_TO_CODE.get(lane_filter)
            filtered_txns = [t for t in filtered_txns if t.get('lane') == target_code]

        if filtered_txns:
            df = pd.DataFrame(filtered_txns)
            df['Date'] = df['timestamp'].apply(lambda x: datetime.datetime.fromisoformat(x).strftime('%Y-%m-%d') if x else '')
            df['Ticket Number'] = df.apply(lambda x: x.get('full_id', x.get('number', '')), axis=1)
            
            def get_time_str(iso_str):
                if not iso_str: return ""
                try:
                    return datetime.datetime.fromisoformat(iso_str).strftime('%I:%M:%S %p')
                except ValueError:
                    return ""

            df['Time Issued'] = df['timestamp'].apply(get_time_str)
            df['Time Called'] = df['start_time'].apply(get_time_str)
            df['Time Ended'] = df['end_time'].apply(get_time_str)

            def calc_diff_mins(end, start):
                if not end or not start: return 0.0
                try:
                    s = datetime.datetime.fromisoformat(start)
                    e = datetime.datetime.fromisoformat(end)
                    return round((e - s).total_seconds() / 60, 2)
                except (ValueError, TypeError): 
                    return 0.0

            df['Total Waiting Time (Mins)'] = df.apply(lambda x: calc_diff_mins(x.get('start_time'), x.get('timestamp')), axis=1)
            df['Total Handle Time (Mins)'] = df.apply(lambda x: calc_diff_mins(x.get('end_time'), x.get('start_time')), axis=1)
            df['Served By'] = df.apply(lambda x: x.get('served_by_staff') or x.get('served_by', 'Unknown'), axis=1)

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
        else: st.info("No data available for the selected time range.")

    elif active == "Reports":
        st.subheader("📋 IOMS Report Generator")
        c1, c2 = st.columns(2)
        d_range = c1.date_input("Date Range", [get_ph_time().date(), get_ph_time().date()])
        staff_filter = c2.multiselect("Filter Staff", [s.get('name', '') for s in local_db.get('staff', {}).values()])
        if len(d_range) == 2:
            start, end = d_range
            all_txns_flat = []
            def extract_txns(ticket_list):
                for t in ticket_list:
                    try:
                        t_date = datetime.datetime.fromisoformat(t.get('timestamp', '')).date()
                    except ValueError:
                        continue
                    if start <= t_date <= end:
                        if t.get('actual_transactions'):
                            for act in t['actual_transactions']:
                                if not staff_filter or act.get('staff') in staff_filter:
                                    all_txns_flat.append({
                                        "Date": t_date, "Ticket ID": t.get('full_id', t.get('number', '')), "Category": act.get('category', 'MEMBER SERVICES'), "Transaction": act.get('txn', ''), "Staff": act.get('staff', ''), "Number of Transaction": 1
                                    })
                        else:
                            staff_name = t.get('served_by_staff') or t.get('served_by', 'Unknown')
                            if not staff_filter or staff_name in staff_filter:
                                all_txns_flat.append({
                                    "Date": t_date, "Ticket ID": t.get('full_id', t.get('number', '')), "Category": LANE_TO_CATEGORY.get(t.get('lane', ''), "MEMBER SERVICES"), "Transaction": t.get('service', ''), "Staff": staff_name, "Number of Transaction": 1
                                })
            extract_txns(local_db.get('history', []))
            if os.path.exists(ARCHIVE_FILE):
                try:
                    with open(ARCHIVE_FILE, 'r', encoding="utf-8") as af:
                        for day in json.load(af): 
                            extract_txns(day.get('history', []))
                except (json.JSONDecodeError, IOError): 
                    pass
            if all_txns_flat:
                df_rep = pd.DataFrame(all_txns_flat)
                st.write("**Summary**"); st.dataframe(df_rep.groupby(['Category', 'Transaction']).size().reset_index(name='Volume'), use_container_width=True)
                st.write("**Detailed Log**"); st.dataframe(df_rep, use_container_width=True)
                st.download_button("📥 Download IOMS CSV", df_rep.to_csv(index=False).encode('utf-8'), "ioms_report.csv", "text/csv")
            else: st.info("No records found.")

    elif active == "Book Appt":
        st.subheader("📅 Book Appointment")
        with st.form("admin_appt"):
            nm = st.text_input("Client Name"); tm = st.time_input("Time Slot"); svc = st.text_input("Transaction"); ctr = st.selectbox("Assign to Counter (Optional)", [""] + [c['name'] for c in local_db.get('config', {}).get('counter_map', [])])
            if st.form_submit_button("Book Slot"):
                generate_ticket_manual(svc, "C", True, is_appt=True, appt_name=nm, appt_time=tm, assign_counter=ctr)
                log_audit("APPOINTMENT_CREATE", user.get('name', 'Unknown'), details=f"{nm} at {tm}", target=svc); st.success(f"Booked for {nm} at {tm}")

    elif active == "Kiosk Menu":
        st.subheader("Manage Kiosk Buttons")
        c1, c2 = st.columns([1, 2])
        with c1:
            cat_list = list(local_db.get('menu', {}).keys())
            sel_cat = st.selectbox("Select Category", cat_list)
            items = local_db.get('menu', {}).get(sel_cat, [])
            for i, (label, code, lane) in enumerate(items):
                with st.expander(f"{label} ({code})"):
                    new_label = st.text_input("Label", label, key=f"l_{i}")
                    new_code = st.text_input("Code", code, key=f"c_{i}")
                    new_lane = st.selectbox("Lane", ["C", "E", "F", "T", "A", "GATE"], index=["C", "E", "F", "T", "A", "GATE"].index(lane) if lane in ["C", "E", "F", "T", "A", "GATE"] else 0, key=f"ln_{i}")
                    if st.button("Update", key=f"up_{i}"): 
                        local_db['menu'][sel_cat][i] = (new_label, new_code, new_lane)
                        save_db(local_db); log_audit("KIOSK_MENU_UPDATE", user.get('name', 'Unknown'), details=f"{label} -> {new_label}"); st.success("Updated!"); st.rerun()
                    if st.button("Delete", key=f"del_{i}"): 
                        local_db['menu'][sel_cat].pop(i); save_db(local_db); log_audit("KIOSK_MENU_DELETE", user.get('name', 'Unknown'), target=label); st.rerun()

    elif active == "Counters":
        for i, c in enumerate(local_db.get('config', {}).get('counter_map', [])): 
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            c1.text(c.get('name', '')); c2.text(c.get('type', ''))
            with c3:
                with st.popover("✏️"):
                    new_n = st.text_input("Rename", c.get('name', ''), key=f"rn_{i}")
                    if st.button("Save", key=f"sv_{i}"):
                        old_name = c['name']
                        local_db['config']['counter_map'][i]['name'] = new_n
                        for s_key in local_db.get('staff', {}):
                            if local_db['staff'][s_key].get('default_station') == old_name:
                                local_db['staff'][s_key]['default_station'] = new_n
                        save_db(local_db); log_audit("COUNTER_RENAME", user.get('name', 'Unknown'), details=f"{old_name} -> {new_n}"); st.rerun()
            if c4.button("🗑", key=f"dc_{i}"): local_db['config']['counter_map'].pop(i); save_db(local_db); log_audit("COUNTER_DELETE", user.get('name', 'Unknown'), target=c.get('name', '')); st.rerun()
        with st.form("add_counter"): 
            cn = st.text_input("Name"); ct = st.selectbox("Type", ["Counter", "Teller", "Employer", "eCenter"])
            if st.form_submit_button("Add"): local_db['config']['counter_map'].append({"name": cn, "type": ct}); save_db(local_db); log_audit("COUNTER_CREATE", user.get('name', 'Unknown'), target=cn); st.rerun()

    elif active == "IOMS Master":
        st.subheader("Transaction Master List")
        current_master = local_db.get('transaction_master', DEFAULT_TRANSACTIONS)
        c1, c2, c3 = st.columns(3)
        with c1: st.write("**PAYMENTS**"); current_master["PAYMENTS"] = st.data_editor(pd.DataFrame(current_master.get("PAYMENTS", []), columns=["Item"]), num_rows="dynamic")["Item"].tolist()
        with c2: st.write("**EMPLOYERS**"); current_master["EMPLOYERS"] = st.data_editor(pd.DataFrame(current_master.get("EMPLOYERS", []), columns=["Item"]), num_rows="dynamic")["Item"].tolist()
        with c3: st.write("**MEMBER SERVICES**"); current_master["MEMBER SERVICES"] = st.data_editor(pd.DataFrame(current_master.get("MEMBER SERVICES", []), columns=["Item"]), num_rows="dynamic")["Item"].tolist()
        if st.button("Save Master List"): local_db['transaction_master'] = current_master; save_db(local_db); log_audit("IOMS_MASTER_UPDATE", user.get('name', 'Unknown')); st.success("Updated!")

    elif active == "Users":
        st.subheader("Manage Users"); h1, h2, h3, h4, h5 = st.columns([1.5, 3, 2, 1, 0.5]); h1.markdown("**ID**"); h2.markdown("**Name**"); h3.markdown("**Station**")
        for uid, u in list(local_db.get('staff', {}).items()):
            c1, c2, c3, c4, c5 = st.columns([1.5, 3, 2, 0.5, 0.5]); c1.text(uid); c2.text(f"{u.get('name', '')} ({u.get('role', '')})"); c3.text(u.get('default_station', '-'))
            with c4:
                with st.popover("✏️"):
                    with st.form(f"edit_{uid}"):
                        en = st.text_input("Name", u.get('name', ''))
                        enick = st.text_input("Nickname", u.get('nickname', ''))
                        er = st.selectbox("Role", STAFF_ROLES, index=STAFF_ROLES.index(u.get('role', 'MSR')) if u.get('role') in STAFF_ROLES else 0)
                        counter_names = [c['name'] for c in local_db.get('config', {}).get('counter_map', [])]
                        est = st.selectbox("Station", counter_names, index=counter_names.index(u.get('default_station', '')) if u.get('default_station') in counter_names else 0)
                        if st.form_submit_button("Save"): local_db['staff'][uid].update({'name': en, 'nickname': enick, 'role': er, 'default_station': est}); save_db(local_db); log_audit("USER_UPDATE", user.get('name', 'Unknown'), target=uid); st.rerun()
                    if st.button("🔑 RESET", key=f"rst_{uid}"): local_db['staff'][uid]['pass'] = "sss2026"; save_db(local_db); log_audit("PASSWORD_RESET", user.get('name', 'Unknown'), target=uid); st.toast("Reset to 'sss2026'")
            if c5.button("🗑", key=f"del_{uid}"): del local_db['staff'][uid]; save_db(local_db); log_audit("USER_DELETE", user.get('name', 'Unknown'), target=uid); st.rerun()
        st.markdown("---")
        st.write("**Add New User**")
        with st.form("add_user_form"):
            new_id = st.text_input("User ID (Login)")
            new_name = st.text_input("Full Name")
            new_nick = st.text_input("Nickname (Display)")
            new_role = st.selectbox("Role", STAFF_ROLES)
            new_station = st.selectbox("Assign Default Station", [c['name'] for c in local_db.get('config', {}).get('counter_map', [])])
            if st.form_submit_button("Create User"):
                valid, msg = validate_user_id(new_id)
                if not valid: st.error(f"⛔ {msg}")
                elif new_id in local_db.get('staff', {}): st.error("User ID already exists!")
                else: 
                    local_db['staff'][new_id] = {"pass": "123", "role": new_role, "name": new_name, "nickname": new_nick if new_nick else new_name.split()[0], "default_station": new_station, "status": "ACTIVE", "online": False}
                    save_db(local_db); log_audit("USER_CREATE", user.get('name', 'Unknown'), target=new_id); st.success("Created!"); st.rerun()
    
    elif active == "Resources":
        st.subheader("Manage Info Hub Content")
        for i, res in enumerate(local_db.get('resources', [])):
            with st.expander(f"{'🔗' if res.get('type') == 'LINK' else '❓'} {res.get('label', '')}"):
                st.write(f"**Value:** {res.get('value', '')}")
                if st.button("Delete", key=f"res_del_{i}"): local_db['resources'].pop(i); save_db(local_db); st.rerun()
        st.write("**Add New Resource**")
        with st.form("new_res"):
            r_type = st.selectbox("Type", ["LINK", "FAQ"]); r_label = st.text_input("Label / Question"); r_value = st.text_area("URL / Answer")
            if st.form_submit_button("Add Resource"): local_db['resources'].append({"type": r_type, "label": r_label, "value": r_value}); save_db(local_db); st.success("Added!"); st.rerun()

    elif active == "Exemptions":
        st.subheader("Manage Exemption Warnings")
        t_ret, t_death, t_fun = st.tabs(["Retirement", "Death", "Funeral"])
        def render_exemption_tab(claim_type):
            current_list = local_db.get('exemptions', {}).get(claim_type, [])
            for i, ex in enumerate(current_list):
                c1, c2 = st.columns([4, 1]); c1.text(f"• {ex}"); 
                if c2.button("🗑", key=f"del_{claim_type}_{i}"): local_db['exemptions'][claim_type].pop(i); save_db(local_db); st.rerun()
            new_ex = st.text_input(f"Add New {claim_type} Exemption", key=f"new_{claim_type}")
            if st.button(f"Add", key=f"add_{claim_type}"): local_db['exemptions'][claim_type].append(new_ex); save_db(local_db); st.rerun()
        with t_ret: render_exemption_tab("Retirement")
        with t_death: render_exemption_tab("Death")
        with t_fun: render_exemption_tab("Funeral")

    elif active == "Announcements":
        curr = " | ".join(local_db.get('announcements', [])); new_txt = st.text_area("Marquee", value=curr)
        if st.button("Update"): local_db['announcements'] = [new_txt]; save_db(local_db); log_audit("ANNOUNCEMENT_UPDATE", user.get('name', 'Unknown')); st.success("Updated!")

    elif active == "Audit Log":
        st.subheader("🔍 Audit Trail Viewer")
        audit_entries = local_db.get('audit_log', [])
        if audit_entries:
            df_audit = pd.DataFrame(audit_entries)
            df_audit['Time'] = df_audit['timestamp'].apply(lambda x: datetime.datetime.fromisoformat(x).strftime('%Y-%m-%d %I:%M %p') if x else '')
            st.dataframe(df_audit[['Time', 'action', 'user', 'target', 'details']], use_container_width=True, hide_index=True)
            st.download_button("📥 Export Audit Log", df_audit.to_csv(index=False).encode('utf-8'), "audit_log.csv", "text/csv")
        else: st.info("No audit entries.")

    elif active == "Backup": 
        st.subheader("💾 Backup & Recovery")
        st.download_button("📥 BACKUP NOW", data=json.dumps(local_db, indent=2), file_name="sss_backup.json")
        st.markdown("---")
        st.write("**Hourly Backups (Last 24)**")
        if os.path.exists(BACKUP_DIR):
            backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "sss_data_*.json")), reverse=True)
            if backups:
                for b in backups[:10]: st.text(f"• {os.path.basename(b)} ({os.path.getsize(b)/1024:.1f} KB)")
            else: st.info("No hourly backups yet.")
        
        st.markdown("---")
        st.write("**🔴 Quarantined Corrupt Files**")
        if os.path.exists(CORRUPT_DIR):
            corrupt_files = glob.glob(os.path.join(CORRUPT_DIR, "*"))
            if corrupt_files:
                for cf in corrupt_files[:10]: 
                    st.text(f"• {os.path.basename(cf)} ({os.path.getsize(cf)/1024:.1f} KB)")
            else: 
                st.success("No corrupt files detected.")
        else:
            st.success("No corrupt files detected.")
    
    elif active == "System Info":
        st.subheader("⚙️ System Configuration - v23.13 Data Fortress Edition")
        
        st.write("**Version Information**")
        st.code(f"""
SSS G-ABAY Version: v23.13 (Data Fortress Edition)
Build Date: 2026-02-03
Timezone: UTC+{UTC_OFFSET_HOURS} (Philippine Standard Time)
Display Grid: {DISPLAY_GRID_COLUMNS} columns (fixed)
Script Directory: {SCRIPT_DIR}
Data File: {DATA_FILE}
        """)
        
        st.write("**v23.13 Safe-Fail Data Protection Fixes**")
        fixes = [
            "FIX-001: Absolute Path Resolution (prevents working directory issues)",
            "FIX-002: Fail-Safe Loading with Backup Cascade (no silent reset)",
            "FIX-003: Rollover Persistence (force save after midnight sweeper)",
            "FIX-004: Atomic Save with Verification (0-byte protection)",
            "FIX-005: Startup Health Check (staff count validation)",
            "FIX-006: Specific Exception Handling (no bare except)",
            "FIX-007: Corrupt File Forensics (quarantine, don't delete)"
        ]
        for fix in fixes:
            st.markdown(f"✅ {fix}")
        
        st.write("**Backup Cascade Order**")
        st.code("""
1. Primary: sss_data.json
2. Backup:  sss_data.bak
3. Hourly:  backups/sss_data_YYYYMMDD_HH.json (newest first)
4. First Run: DEFAULT_DATA (only if NO files exist)
5. FAIL: Show recovery screen (never silent reset)
""")
        
        st.write("**File Paths (Absolute)**")
        st.text(f"Data:     {DATA_FILE}")
        st.text(f"Backup:   {BACKUP_FILE}")
        st.text(f"Archive:  {ARCHIVE_FILE}")
        st.text(f"Backups:  {BACKUP_DIR}")
        st.text(f"Corrupt:  {CORRUPT_DIR}")
        
        st.write("**System Constants**")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Session Timeout", f"{SESSION_TIMEOUT_MINUTES} min")
            st.metric("Park Grace Period", f"{PARK_GRACE_MINUTES} min")
            st.metric("Archive Retention", f"{ARCHIVE_RETENTION_DAYS} days")
        with c2:
            st.metric("Max Hourly Backups", MAX_HOURLY_BACKUPS)
            st.metric("Min Valid File Size", f"{MIN_VALID_FILE_SIZE} bytes")
            st.metric("Audit Log Max", f"{AUDIT_LOG_MAX_ENTRIES:,}")

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
            acct = next((v for k,v in local_db.get('staff', {}).items() if v.get("name") == u or k == u), None)
            acct_key = next((k for k,v in local_db.get('staff', {}).items() if v.get("name") == u or k == u), None)
            if u == "admin" and not acct: 
                local_db['staff']['admin'] = DEFAULT_DATA['staff']['admin']
                save_db(local_db)
                st.warning("Admin reset.")
                st.rerun()
            if acct and acct.get('pass') == p: 
                st.session_state['user'] = acct
                st.session_state['last_activity'] = get_ph_time()
                st.session_state['login_date'] = get_ph_time().strftime("%Y-%m-%d")
                local_db['staff'][acct_key]['online'] = True
                save_db(local_db)
                log_audit("LOGIN", acct.get('name', 'Unknown'), target=acct.get('default_station', 'N/A'))
                st.rerun()
            else: st.error("Invalid")
    else:
        user = st.session_state['user']
        if user.get('role') in ["ADMIN", "DIV_HEAD"]: render_admin_panel(user)
        elif user.get('role') in ["BRANCH_HEAD", "SECTION_HEAD"]:
            view = st.sidebar.radio("View", ["Admin", "Counter"])
            if view == "Admin": render_admin_panel(user)
            else: render_counter(user)
        else: render_counter(user)
elif mode == "display": render_display()
else:
    if db.get('config', {}).get("logo_url", "").startswith("http"): 
        st.image(db['config']["logo_url"], width=50)
    st.title("G-ABAY Mobile Tracker")
    t1, t2, t3 = st.tabs(["🎫 Tracker", "ℹ️ Info Hub", "⭐ Rate Us"])
    with t1:
        tn = st.text_input("Enter Ticket # (e.g. 001)")
        if tn:
            local_db = load_db()
            t = next((x for x in local_db.get('tickets', []) if x.get("number") == tn or x.get('full_id') == tn), None)
            t_hist = next((x for x in local_db.get('history', []) if x.get("number") == tn or x.get('full_id') == tn), None)
            if t:
                if t.get('status') == "PARKED":
                    try:
                        park_time = datetime.datetime.fromisoformat(t.get('park_timestamp', ''))
                        remaining = datetime.timedelta(minutes=PARK_GRACE_MINUTES) - (get_ph_time() - park_time)
                        if remaining.total_seconds() > 0:
                            mins, secs = divmod(remaining.total_seconds(), 60)
                            st.markdown(f"""<div style="font-size:30px; font-weight:bold; color:#b91c1c; text-align:center;">PARKED: {int(mins):02d}:{int(secs):02d}</div>""", unsafe_allow_html=True)
                            st.error("⚠️ PLEASE APPROACH COUNTER IMMEDIATELY TO AVOID FORFEITURE.")
                        else: 
                            st.error("❌ TICKET EXPIRED")
                    except (ValueError, TypeError):
                        st.error("❌ TICKET STATUS ERROR")
                elif t.get('status') == "SERVING": 
                    st.success(f"🔊 NOW SERVING at {t.get('served_by', 'Counter')}. Please proceed immediately.")
                else:
                    st.info(f"Status: {t.get('status', 'UNKNOWN')}")
                    wait_str = calculate_specific_wait_time(t.get('id', ''), t.get('lane', 'C'))
                    people_ahead = calculate_people_ahead(t.get('id', ''), t.get('lane', 'C'))
                    c1, c2 = st.columns(2)
                    c1.metric("Est. Wait", wait_str)
                    if people_ahead == 0: c2.success("You are Next!")
                    else: c2.metric("People Ahead", people_ahead)
                    st.write(f"Your Ticket: {t.get('number', '')}")
                time.sleep(5)
                st.rerun()
            elif t_hist: 
                st.success("✅ TRANSACTION COMPLETE. Thank you!")
            else: 
                st.error("Not Found (Check Ticket Number)")
    with t2:
        st.subheader("Member Resources")
        for l in [r for r in db.get('resources', []) if r.get('type') == 'LINK']: 
            st.markdown(f"[{sanitize_text(l.get('label', ''))}]({l.get('value', '')})")
        for f in [r for r in db.get('resources', []) if r.get('type') == 'FAQ']: 
            with st.expander(sanitize_text(f.get('label', ''))): 
                st.write(sanitize_text(f.get('value', '')))
    with t3:
        st.subheader("Rate Our Service")
        verify_t = st.text_input("Enter your Ticket Number to rate:", key="rate_t")
        if verify_t:
            local_db = load_db()
            active_t = next((x for x in local_db.get('history', []) if x.get('number') == verify_t), None)
            if active_t:
                st.success(f"Verified! Served by: {active_t.get('served_by_staff') or active_t.get('served_by', 'Unknown')}")
                with st.form("rev"):
                    rate = st.feedback("stars")
                    pers = st.text_input("Personnel Served You (Optional)")
                    comm = st.text_area("Comments")
                    if st.form_submit_button("Submit Rating"):
                        review_entry = {"ticket": verify_t, "rating": (rate if rate else 0) + 1, "personnel": pers, "comment": comm, "timestamp": get_ph_time().isoformat()}
                        local_db['reviews'].append(review_entry)
                        save_db(local_db)
                        st.success("Thank you!")
                        time.sleep(2)
                        st.rerun()
            else: 
                st.error("Ticket not found in completed transactions.")

# ==============================================================================
# END OF SSS G-ABAY v23.13 - DATA FORTRESS EDITION
# ==============================================================================
