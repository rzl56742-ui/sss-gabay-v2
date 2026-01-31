# ==============================================================================
# SSS G-ABAY v22.15 - BRANCH OPERATING SYSTEM (INFO HUB EDITION)
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
import math

# ==========================================
# 1. SYSTEM CONFIGURATION & PERSISTENCE
# ==========================================
st.set_page_config(page_title="SSS G-ABAY v22.15", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

DATA_FILE = "sss_data.json"

# --- DEFAULT DATA ---
DEFAULT_DATA = {
    "system_date": datetime.datetime.now().strftime("%Y-%m-%d"),
    "latest_announcement": {"text": "", "id": ""},
    "tickets": [],
    "history": [],
    "breaks": [],
    "reviews": [],
    # NEW: Default Resources for Info Hub
    "resources": [
        {"type": "LINK", "label": "🌐 SSS Official Website", "value": "https://www.sss.gov.ph"},
        {"type": "LINK", "label": "💻 My.SSS Member Portal", "value": "https://member.sss.gov.ph/members/"},
        {"type": "LINK", "label": "📖 Citizen's Charter", "value": "https://www.sss.gov.ph/sss/DownloadContent?fileName=SSS_Citizens_Charter_2024.pdf"},
        {"type": "LINK", "label": "📥 Downloadable Forms", "value": "https://www.sss.gov.ph/sss/appmanager/viewArticle.jsp?page=forms"},
        {"type": "FAQ", "label": "How to reset My.SSS password?", "value": "Please visit our e-Center for assistance or use the 'Forgot User ID/Password' feature on the My.SSS portal."},
        {"type": "FAQ", "label": "What are the requirements for Funeral Claim?", "value": "1. Death Certificate (LCR certified)\n2. Official Receipt of Funeral Expenses\n3. Valid ID of claimant"}
    ],
    "announcements": ["Welcome to SSS Gingoog. Operating Hours: 8:00 AM - 5:00 PM."],
    "exemptions": {
        "Retirement": ["Dropped/Cancelled SS Number", "Multiple SS Numbers", "Portability (SGS)", "Maintenance/Adjustment of records"],
        "Death": ["Dropped/Cancelled SS Number", "Multiple SS Numbers", "Claimant is not legal spouse/child", "Pending Case"],
        "Funeral": ["Dropped/Cancelled SS Number", "Multiple SS Numbers", "Receipt Issues"]
    },
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
        "admin": {"pass": "sss2026", "role": "ADMIN", "name": "System Admin", "default_station": "Counter 1", "status": "ACTIVE", "online": False},
    }
}

# --- DATABASE ENGINE ---
def load_db():
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                if "resources" not in data: data["resources"] = DEFAULT_DATA["resources"]
                if "exemptions" not in data: data["exemptions"] = DEFAULT_DATA["exemptions"]
                if "breaks" not in data: data["breaks"] = []
                if "latest_announcement" not in data: data["latest_announcement"] = {"text": "", "id": ""}
                if "system_date" not in data: data["system_date"] = current_date
                
                # DAILY RESET
                if data["system_date"] != current_date:
                    data["history"] = [] 
                    data["tickets"] = []
                    data["breaks"] = []
                    data["system_date"] = current_date
                    for uid in data['staff']:
                        data['staff'][uid]['status'] = "ACTIVE"
                        data['staff'][uid]['online'] = False
                        if 'break_reason' in data['staff'][uid]: del data['staff'][uid]['break_reason']
                        if 'break_start_time' in data['staff'][uid]: del data['staff'][uid]['break_start_time']
                
                # MENU PRESERVATION (V22.13 Logic)
                if "menu" in data:
                    if "Benefits" not in data['menu']: data['menu']['Benefits'] = []
                    fragments = ["Retirement", "Death", "Funeral", "Benefits (Short-Term)"]
                    for frag in fragments:
                        if frag in data['menu']:
                            for item in data['menu'][frag]:
                                if not any(existing[1] == item[1] for existing in data['menu']['Benefits']):
                                    data['menu']['Benefits'].append(item)
                            del data['menu'][frag]
                    updated_benefits = []
                    for lbl, code, lane in data['menu']['Benefits']:
                        if ("Retirement" in lbl or "Death" in lbl or "Funeral" in lbl) and lane != "GATE":
                            updated_benefits.append((lbl, code, "GATE"))
                        else:
                            updated_benefits.append((lbl, code, lane))
                    data['menu']['Benefits'] = updated_benefits

                if "Counter" not in data['config']['assignments']:
                    data['config']['assignments']['Counter'] = ["C", "F", "E"]
                for uid in data['staff']:
                    if 'online' not in data['staff'][uid]: data['staff'][uid]['online'] = False
                    
                return data
            except:
                return DEFAULT_DATA
    return DEFAULT_DATA

def save_db(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str)

db = load_db()

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
            display.style.color = "red";
        }
    }, 1000);
}
</script>
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"][aria-expanded="false"] { display: none; }
    .header-text { text-align: center; font-family: sans-serif; }
    .header-branch { font-size: 30px; font-weight: 800; color: #333; margin-top: 5px; text-transform: uppercase; }
    .brand-footer { position: fixed; bottom: 5px; right: 10px; font-family: monospace; font-size: 12px; color: #888; opacity: 0.7; pointer-events: none; z-index: 9999; }
    
    @keyframes blink { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.05); color: #dc2626; } 100% { opacity: 1; transform: scale(1); } }
    .blink-active { animation: blink 1.5s infinite; }
    
    /* SERVING CARDS */
    .serving-card-small { background: white; border-left: 25px solid #2563EB; padding: 10px; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.2); text-align: center; display: flex; flex-direction: column; justify-content: center; transition: all 0.3s ease; width: 100%; }
    .serving-card-break { background: #FEF3C7; border-left: 25px solid #D97706; padding: 10px; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.2); text-align: center; display: flex; flex-direction: column; justify-content: center; transition: all 0.3s ease; width: 100%; }
    
    /* DYNAMIC FONT SIZES */
    .serving-card-small p { margin: 0; font-weight: bold; text-transform: uppercase; color: #111; line-height: 1.2; }
    .serving-card-small span { font-weight: normal; color: #555; }
    
    .swim-col { background: #f8f9fa; border-radius: 10px; padding: 10px; border-top: 10px solid #ccc; height: 100%; }
    .swim-col h3 { text-align: center; margin-bottom: 10px; font-size: 18px; text-transform: uppercase; color: #333; }
    .queue-item { background: white; border-bottom: 1px solid #ddd; padding: 15px; margin-bottom: 5px; border-radius: 5px; display: flex; justify-content: space-between; }
    .queue-item span { font-size: 24px; font-weight: 900; color: #111; }
    .park-row { background: #fff3cd; color: #333; padding: 8px; margin-bottom: 5px; border-radius: 5px; border-left: 5px solid #ffc107; font-weight:bold; display:flex; justify-content:space-between; }
    .park-danger { background: #fee2e2; color: #b91c1c; border-left: 5px solid #ef4444; animation: pulse 2s infinite; padding: 8px; border-radius: 5px; font-weight:bold; display:flex; justify-content:space-between;}
    .gate-btn > button { height: 350px !important; width: 100% !important; font-size: 40px !important; font-weight: 900 !important; border-radius: 30px !important; }
    .menu-card > button { height: 300px !important; width: 100% !important; font-size: 30px !important; font-weight: 800 !important; border-radius: 20px !important; border: 4px solid #ddd !important; }
    .swim-btn > button { height: 100px !important; width: 100% !important; font-size: 18px !important; font-weight: 700 !important; text-align: left !important; padding-left: 20px !important; }
    
    /* INFO HUB BUTTONS */
    .info-link { text-decoration: none; display: block; padding: 15px; background: #f0f2f6; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #2563EB; color: #333; font-weight: bold; transition: 0.2s; }
    .info-link:hover { background: #e0e7ff; }
    
    .head-red { background-color: #DC2626; } .border-red > button { border-left: 20px solid #DC2626 !important; }
    .head-orange { background-color: #EA580C; } .border-orange > button { border-left: 20px solid #EA580C !important; }
    .head-green { background-color: #16A34A; } .border-green > button { border-left: 20px solid #16A34A !important; }
    .head-blue { background-color: #2563EB; } .border-blue > button { border-left: 20px solid #2563EB !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. CORE LOGIC
# ==========================================
def format_nickname(full_name):
    try:
        if "," in full_name: return full_name.split(",")[1].strip().split(" ")[0]
        return full_name.split(" ")[0]
    except: return full_name

def generate_ticket_callback(service, lane_code, is_priority):
    local_db = load_db()
    prefix = "P" if is_priority else "R"
    today_count = len([t for t in local_db['tickets'] if t["lane"] == lane_code]) + \
                  len([t for t in local_db['history'] if t["lane"] == lane_code]) + 1
    ticket_num = f"{lane_code}{prefix}-{today_count:03d}"
    
    new_t = {
        "id": str(uuid.uuid4()), "number": ticket_num, "lane": lane_code,
        "service": service, "type": "PRIORITY" if is_priority else "REGULAR",
        "status": "WAITING", "timestamp": datetime.datetime.now().isoformat(),
        "start_time": None, "end_time": None, "park_timestamp": None,
        "history": [], "served_by": None, "ref_from": None, "referral_reason": None,
        "appt_name": None, "appt_time": None
    }
    local_db['tickets'].append(new_t)
    save_db(local_db)
    st.session_state['last_ticket'] = new_t
    st.session_state['kiosk_step'] = 'ticket'

def generate_ticket_manual(service, lane_code, is_priority, is_appt=False, appt_name=None, appt_time=None):
    local_db = load_db()
    prefix = "A" if is_appt else ("P" if is_priority else "R")
    today_count = len([t for t in local_db['tickets'] if t["lane"] == lane_code]) + \
                  len([t for t in local_db['history'] if t["lane"] == lane_code]) + 1
    ticket_num = f"{lane_code}{prefix}-{today_count:03d}"
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

def calculate_specific_wait_time(ticket_id, lane_code):
    local_db = load_db()
    recent = [t for t in local_db['history'] if t['lane'] == lane_code and t['end_time']]
    avg_txn_time = 15
    if recent:
        total_sec = sum([datetime.datetime.fromisoformat(t["end_time"]).timestamp() - datetime.datetime.fromisoformat(t["start_time"]).timestamp() for t in recent[-10:]])
        avg_txn_time = (total_sec / len(recent[-10:])) / 60
    waiting_in_lane = [t for t in local_db['tickets'] if t['lane'] == lane_code and t['status'] == "WAITING"]
    waiting_in_lane.sort(key=get_prio_score)
    position = 0
    for i, t in enumerate(waiting_in_lane):
        if t['id'] == ticket_id: position = i; break
    wait_time = round(position * avg_txn_time)
    if wait_time < 2: return "Next"
    return f"{wait_time} min"

def calculate_people_ahead(ticket_id, lane_code):
    local_db = load_db()
    waiting_in_lane = [t for t in local_db['tickets'] if t['lane'] == lane_code and t['status'] == "WAITING"]
    waiting_in_lane.sort(key=get_prio_score)
    for i, t in enumerate(waiting_in_lane):
        if t['id'] == ticket_id: return i
    return 0

def get_staff_efficiency(staff_name):
    local_db = load_db()
    my_txns = [t for t in local_db['history'] if t.get("served_by") == staff_name]
    return len(my_txns), "5m"

def get_allowed_counters(role):
    all_counters = db['config']['counter_map']
    target_types = []
    if role == "TELLER": target_types = ["Teller"]
    elif role == "AO": target_types = ["Employer"]
    elif role == "MSR": target_types = ["Counter", "eCenter", "Help"]
    elif role in ["ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]: return [c['name'] for c in all_counters] 
    return [c['name'] for c in all_counters if c['type'] in target_types]

def get_next_ticket(queue, surge_mode):
    if not queue: return None
    if surge_mode:
        prio_tickets = [t for t in queue if t['type'] == 'PRIORITY']
        if prio_tickets: return prio_tickets[0] 
        return queue[0] 
    local_db = load_db()
    last_2 = local_db['history'][-2:]
    p_count = sum(1 for t in last_2 if t['type'] == 'PRIORITY')
    if p_count >= 2:
        reg_tickets = [t for t in queue if t['type'] == 'REGULAR']
        if reg_tickets: return reg_tickets[0]
    return queue[0]

def trigger_audio(ticket_num, counter_name):
    local_db = load_db()
    spoken_text = f"Priority Ticket... " if "P" in ticket_num else "Ticket... "
    clean_num = ticket_num.replace("-", " ")
    spelled_out = ""
    for char in clean_num:
        if char.isdigit():
            if char == "0": spelled_out += "Zero... "
            else: spelled_out += f"{char}... "
        else:
            spelled_out += f"{char}... "
    spoken_text += f"{spelled_out} please proceed to... {counter_name}."
    local_db['latest_announcement'] = {
        "text": spoken_text,
        "id": str(uuid.uuid4())
    }
    save_db(local_db)

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
            st.markdown('<div class="menu-card">', unsafe_allow_html=True)
            if st.button("💳 PAYMENTS\n(Contrib/Loans)"):
                generate_ticket_callback("Payment", "T", st.session_state['is_prio']); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with m2:
            st.markdown('<div class="menu-card">', unsafe_allow_html=True)
            if st.button("💼 EMPLOYERS\n(Account Mgmt)"):
                generate_ticket_callback("Account Management", "A", st.session_state['is_prio']); st.rerun()
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
                        is_gate_trans = (lane == "GATE") or any(x in label for x in ["Retirement", "Death", "Funeral"])
                        if is_gate_trans:
                            st.session_state['gate_target'] = {"label": label, "code": code}
                            st.session_state['kiosk_step'] = 'gate_check'
                            st.rerun()
                        else:
                            generate_ticket_callback(code, lane, st.session_state['is_prio'])
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ GO BACK", type="secondary", use_container_width=True): st.session_state['kiosk_step'] = 'menu'; st.rerun()
    
    elif st.session_state['kiosk_step'] == 'gate_check':
        target = st.session_state.get('gate_target', {})
        label = target.get('label', 'Transaction')
        claim_type = "Retirement" if "Retirement" in label else ("Death" if "Death" in label else "Funeral")
        exemptions = db['exemptions'].get(claim_type, [])
        st.warning(f"⚠️ PRE-QUALIFICATION FOR {label.upper()}")
        st.markdown(f"**Do NOT proceed to Online Filing if you have:**")
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
        print_dt = datetime.datetime.now().strftime("%B %d, %Y - %I:%M %p")
        st.markdown(f"""<div class="ticket-card no-print" style='background:{bg}; color:{col}; padding:40px; border-radius:20px; text-align:center; margin:20px 0;'><h1>{t['number']}</h1><h3>{t['service']}</h3><p style="font-size:18px;">{print_dt}</p></div>""", unsafe_allow_html=True)
        if t['type'] == 'PRIORITY': st.error("**⚠ PRIORITY LANE:** For Seniors, PWDs, Pregnant ONLY.")
        st.info("**POLICY:** Ticket forfeited if parked for 30 mins.")
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("❌ CANCEL", use_container_width=True): curr_db = load_db(); curr_db['tickets'] = [x for x in curr_db['tickets'] if x['id'] != t['id']]; save_db(curr_db); del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c2:
            if st.button("✅ DONE", type="primary", use_container_width=True): del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c3:
            if st.button("🖨️ PRINT", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True); time.sleep(1); del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
    
    st.markdown("<div class='brand-footer'>System developed by RPT/SSSGingoog © 2026</div>", unsafe_allow_html=True)

def render_display():
    placeholder = st.empty()
    last_audio_id = ""
    
    while True:
        local_db = load_db()
        audio_script = ""
        current_audio = local_db.get('latest_announcement', {})
        if current_audio.get('id') != last_audio_id and current_audio.get('text'):
            last_audio_id = current_audio['id']
            text_safe = current_audio['text'].replace("'", "")
            audio_script = f"""<script>var msg = new SpeechSynthesisUtterance(); msg.text = "{text_safe}"; msg.rate = 1.0; msg.pitch = 1.1; var voices = window.speechSynthesis.getVoices(); var fVoice = voices.find(v => v.name.includes('Female') || v.name.includes('Zira')); if(fVoice) msg.voice = fVoice; window.speechSynthesis.speak(msg);</script>"""
        
        with placeholder.container():
            if audio_script: st.markdown(audio_script, unsafe_allow_html=True)
            st.markdown(f"<h1 style='text-align: center; color: #0038A8;'>NOW SERVING</h1>", unsafe_allow_html=True)
            
            # --- DEDUPLICATION LOGIC ---
            raw_staff = [s for s in local_db['staff'].values() if s.get('online') is True and s['role'] != "ADMIN" and s['name'] != "System Admin"]
            
            unique_staff_map = {} 
            for s in raw_staff:
                st_name = s.get('default_station', 'Unassigned')
                if st_name not in unique_staff_map:
                    unique_staff_map[st_name] = s
                else:
                    curr = unique_staff_map[st_name]
                    is_curr_serving = next((t for t in local_db['tickets'] if t['status'] == 'SERVING' and t.get('served_by') == st_name), None)
                    is_new_serving = next((t for t in local_db['tickets'] if t['status'] == 'SERVING' and t.get('served_by') == st_name and t.get('served_by') == s.get('default_station')), None) 
                    if not is_curr_serving and is_new_serving:
                        unique_staff_map[st_name] = s
            
            unique_staff = list(unique_staff_map.values())
            
            if not unique_staff:
                st.warning("Waiting for staff to log in...")
            else:
                count = len(unique_staff)
                num_rows = math.ceil(count / 6)
                card_height = 65 // num_rows
                font_scale = 1.0 if num_rows == 1 else (0.8 if num_rows == 2 else 0.7)
                
                for i in range(0, count, 6):
                    batch = unique_staff[i:i+6]
                    cols = st.columns(len(batch))
                    for idx, staff in enumerate(batch):
                        with cols[idx]:
                            nickname = format_nickname(staff['name'])
                            station_name = staff.get('default_station', 'Unassigned')
                            style_str = f"height: {card_height}vh;"
                            if staff.get('status') == "ON_BREAK":
                                st.markdown(f"""<div class="serving-card-break" style="{style_str}"><p style="font-size: {35*font_scale}px;">{station_name}</p><h3 style="margin:0; font-size:{50*font_scale}px; color:#92400E;">ON BREAK</h3><span style="font-size: {24*font_scale}px;">{nickname}</span></div>""", unsafe_allow_html=True)
                            elif staff.get('status') == "ACTIVE":
                                active_t = next((t for t in local_db['tickets'] if t['status'] == 'SERVING' and t.get('served_by') == station_name), None)
                                if active_t:
                                    is_blinking = "blink-active" if active_t.get('start_time') and (datetime.datetime.now() - datetime.datetime.fromisoformat(active_t['start_time'])).total_seconds() < 20 else ""
                                    b_color = "#DC2626" if active_t['lane'] == "T" else ("#16A34A" if active_t['lane'] == "A" else "#2563EB")
                                    st.markdown(f"""<div class="serving-card-small" style="border-left: 25px solid {b_color}; {style_str}"><p style="font-size: {35*font_scale}px;">{station_name}</p><h2 style="color:{b_color}; font-size: {110*font_scale}px;" class="{is_blinking}">{active_t['number']}</h2><span style="font-size: {24*font_scale}px;">{nickname}</span></div>""", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""<div class="serving-card-small" style="border-left: 25px solid #ccc; {style_str}"><p style="font-size: {35*font_scale}px;">{station_name}</p><h2 style="color:#22c55e; font-size: {70*font_scale}px;">READY</h2><span style="font-size: {24*font_scale}px;">{nickname}</span></div>""", unsafe_allow_html=True)

            st.markdown("---")
            c_queue, c_park = st.columns([3, 1])
            with c_queue:
                q1, q2, q3 = st.columns(3)
                waiting = [t for t in local_db['tickets'] if t["status"] == "WAITING"]
                waiting.sort(key=get_prio_score)
                with q1:
                    st.markdown(f"<div class='swim-col' style='border-top-color:#DC2626;'><h3>💳 PAYMENTS</h3>", unsafe_allow_html=True)
                    for t in [x for x in waiting if x['lane'] == 'T'][:5]: st.markdown(f"<div class='queue-item'><span>{t['number']}</span></div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                with q2:
                    st.markdown(f"<div class='swim-col' style='border-top-color:#16A34A;'><h3>💼 EMPLOYERS</h3>", unsafe_allow_html=True)
                    for t in [x for x in waiting if x['lane'] == 'A'][:5]: st.markdown(f"<div class='queue-item'><span>{t['number']}</span></div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                with q3:
                    st.markdown(f"<div class='swim-col' style='border-top-color:#2563EB;'><h3>👤 SERVICES</h3>", unsafe_allow_html=True)
                    for t in [x for x in waiting if x['lane'] in ['C','E','F']][:5]: st.markdown(f"<div class='queue-item'><span>{t['number']}</span></div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            with c_park:
                st.markdown("### 🅿️ PARKED")
                parked = [t for t in local_db['tickets'] if t["status"] == "PARKED"]
                for p in parked:
                    park_time = datetime.datetime.fromisoformat(p['park_timestamp']); remaining = datetime.timedelta(minutes=30) - (datetime.datetime.now() - park_time)
                    if remaining.total_seconds() <= 0: p["status"] = "NO_SHOW"; save_db(local_db); st.rerun()
                    else:
                        mins, secs = divmod(remaining.total_seconds(), 60)
                        st.markdown(f"""<div class="park-danger" style="background:#fee2e2; color:#b91c1c; border-left:5px solid #ef4444; padding:10px;"><span>{p['number']}</span><span>{int(mins):02d}:{int(secs):02d}</span></div>""", unsafe_allow_html=True)
            
            txt = " | ".join(local_db['announcements'])
            st.markdown(f"<div style='background: #FFD700; color: black; padding: 10px; font-weight: bold; position: fixed; bottom: 0; width: 100%; font-size:20px;'><marquee>{txt}</marquee></div>", unsafe_allow_html=True)
            st.markdown("<div class='brand-footer'>System developed by RPT/SSSGingoog © 2026</div>", unsafe_allow_html=True)
        time.sleep(3)

def render_counter(user):
    local_db = load_db()
    user_key = next((k for k,v in local_db['staff'].items() if v['name'] == user['name']), None)
    if not user_key: st.error("User Sync Error. Please Relogin."); return
    current_user_state = local_db['staff'][user_key]

    if current_user_state.get('status') == "ON_BREAK":
        st.warning(f"⛔ YOU ARE CURRENTLY ON BREAK ({current_user_state.get('break_reason', 'Break')})")
        st.info(f"Break started at: {current_user_state.get('break_start_time', '')}")
        start_dt = datetime.datetime.fromisoformat(current_user_state.get('break_start_time'))
        elapsed = datetime.datetime.now() - start_dt
        st.metric("Time Elapsed", str(elapsed).split('.')[0])
        if st.button("▶ RESUME WORK", type="primary"):
            local_db['breaks'].append({"name": user['name'], "reason": current_user_state.get('break_reason'), "start": current_user_state.get('break_start_time'), "end": datetime.datetime.now().isoformat(), "duration_sec": elapsed.total_seconds()})
            local_db['staff'][user_key]['status'] = "ACTIVE"; del local_db['staff'][user_key]['break_reason']; del local_db['staff'][user_key]['break_start_time']
            save_db(local_db); st.session_state['user'] = local_db['staff'][user_key]; st.rerun()
        return

    if 'my_station' not in st.session_state: st.session_state['my_station'] = current_user_state.get('default_station', 'Counter 1')
    st.sidebar.title(f"👮 {user['name']}")
    if 'surge_mode' not in st.session_state: st.session_state['surge_mode'] = False
    st.sidebar.markdown("---")
    st.session_state['surge_mode'] = st.sidebar.checkbox("🚨 PRIORITY SURGE MODE", value=st.session_state['surge_mode'])
    if st.session_state['surge_mode']: st.sidebar.warning("⚠ SURGE ACTIVE: Only Priority Tickets will be called!")
    st.sidebar.markdown("---")
    
    with st.sidebar.expander("☕ Go On Break"):
        b_reason = st.selectbox("Reason", ["Lunch Break", "Coffee Break (15m)", "Bio-Break", "Emergency"])
        if st.button("⏸ START BREAK"):
            local_db['staff'][user_key]['status'] = "ON_BREAK"; local_db['staff'][user_key]['break_reason'] = b_reason; local_db['staff'][user_key]['break_start_time'] = datetime.datetime.now().isoformat()
            save_db(local_db); st.session_state['user'] = local_db['staff'][user_key]; st.rerun()

    with st.sidebar.expander("🔒 Change Password"):
        with st.form("pwd_chg"):
            n_pass = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                if user_key: local_db['staff'][user_key]['pass'] = n_pass; save_db(local_db); st.success("Updated!")
                
    if st.sidebar.button("⬅ LOGOUT"): local_db['staff'][user_key]['online'] = False; save_db(local_db); del st.session_state['user']; del st.session_state['my_station']; st.rerun()
    
    if user['role'] in ["SECTION_HEAD", "BRANCH_HEAD"]:
        with st.sidebar.expander("📅 Add Appointment"):
            with st.form("add_appt"):
                nm = st.text_input("Name"); svc = st.selectbox("Service", ["Pension", "Death", "Loan"]); tm = st.time_input("Time")
                if st.form_submit_button("Book Slot"): generate_ticket_manual(svc, "C", True, is_appt=True, appt_name=nm, appt_time=tm); st.success("Booked!")
                    
    st.markdown(f"### Station: {st.session_state['my_station']}")
    allowed_counters = get_allowed_counters(user['role'])
    if st.session_state['my_station'] not in allowed_counters and allowed_counters: st.session_state['my_station'] = allowed_counters[0]
    new_station = st.selectbox("Switch Station", allowed_counters, index=allowed_counters.index(st.session_state['my_station']) if st.session_state['my_station'] in allowed_counters else 0)
    if new_station != st.session_state['my_station'] or new_station != current_user_state.get('default_station'):
        st.session_state['my_station'] = new_station; local_db['staff'][user_key]['default_station'] = new_station; save_db(local_db); st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    current_counter_obj = next((c for c in local_db['config']['counter_map'] if c['name'] == st.session_state['my_station']), None)
    station_type = current_counter_obj['type'] if current_counter_obj else "Counter"
    my_lanes = local_db['config']["assignments"].get(station_type, ["C"])
    queue = [t for t in local_db['tickets'] if t["status"] == "WAITING" and t["lane"] in my_lanes]
    if "C" in my_lanes: queue.sort(key=lambda x: ({"C":0, "F":1, "E":2}.get(x['lane'], 3), get_prio_score(x)))
    else: queue.sort(key=get_prio_score)
    current = next((t for t in local_db['tickets'] if t["status"] == "SERVING" and t.get("served_by") == st.session_state['my_station']), None)
    
    if 'refer_modal' not in st.session_state: st.session_state['refer_modal'] = False
    c1, c2 = st.columns([2,1])
    with c1:
        if current:
            st.markdown(f"""<div style='padding:30px; background:#e0f2fe; border-radius:15px; border-left:10px solid #0369a1;'><h1 style='margin:0; color:#0369a1; font-size: 80px;'>{current['number']}</h1><h3>{current['service']}</h3></div>""", unsafe_allow_html=True)
            if current.get("ref_from"): st.markdown(f"""<div style='background:#fee2e2; border-left:5px solid #ef4444; padding:10px; margin-top:10px;'><span style='color:#b91c1c; font-weight:bold;'>↩ REFERRED FROM: {current["ref_from"]}</span><br><span style='color:#b91c1c; font-weight:bold;'>📝 REASON: {current.get("referral_reason", "No reason provided")}</span></div>""", unsafe_allow_html=True)
            if st.session_state['refer_modal']:
                with st.form("referral"):
                    st.write("**Referral Details**")
                    target = st.selectbox("Transfer To", ["Teller", "Employer", "eCenter", "Counter"])
                    reason = st.text_input("Reason for Referral (Required)") 
                    c_col1, c_col2 = st.columns(2)
                    with c_col1:
                        if st.form_submit_button("✅ CONFIRM TRANSFER"):
                            if not reason: st.error("Reason required!"); st.stop()
                            current_lane = current['lane']; target_lane = {"Teller":"T", "Employer":"A", "eCenter":"E", "Counter":"C"}[target]
                            if current['type'] == 'PRIORITY': current['type'] = 'REGULAR'; current['timestamp'] = datetime.datetime.now().isoformat() 
                            else:
                                ts = datetime.datetime.fromisoformat(current['timestamp'])
                                if current_lane == "C" and target_lane != "C": ts -= datetime.timedelta(minutes=30)
                                elif current_lane != "C" and target_lane == "C": ts += datetime.timedelta(minutes=45)
                                current['timestamp'] = ts.isoformat()
                            current["lane"] = target_lane; current["status"] = "WAITING"; current["served_by"] = None
                            current["ref_from"] = st.session_state['my_station']; current["referral_reason"] = reason 
                            save_db(local_db); st.session_state['refer_modal'] = False; st.rerun()
                    with c_col2:
                        if st.form_submit_button("❌ CANCEL"): st.session_state['refer_modal'] = False; st.rerun()
            else:
                st.markdown("<br>", unsafe_allow_html=True)
                b1, b2, b3 = st.columns(3)
                if b1.button("✅ COMPLETE", use_container_width=True): 
                    current["status"] = "COMPLETED"; current["end_time"] = datetime.datetime.now().isoformat(); local_db['history'].append(current); save_db(local_db); st.rerun()
                if b2.button("🅿️ PARK", use_container_width=True): 
                    current["status"] = "PARKED"; current["park_timestamp"] = datetime.datetime.now().isoformat(); save_db(local_db); st.rerun()
                if b3.button("🔔 RE-CALL", use_container_width=True):
                    current["start_time"] = datetime.datetime.now().isoformat()
                    for i, t in enumerate(local_db['tickets']):
                        if t['id'] == current['id']: local_db['tickets'][i]['start_time'] = current["start_time"]; break
                    trigger_audio(current['number'], st.session_state['my_station']); save_db(local_db); st.toast(f"Re-calling {current['number']}..."); time.sleep(0.5); st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 REFER", use_container_width=True): st.session_state['refer_modal'] = True; st.rerun()
        else:
            if st.button("🔊 CALL NEXT", type="primary", use_container_width=True):
                nxt = get_next_ticket(queue, st.session_state['surge_mode'])
                if nxt:
                    db_ticket = next((x for x in local_db['tickets'] if x['id'] == nxt['id']), None)
                    if db_ticket:
                        db_ticket["status"] = "SERVING"; db_ticket["served_by"] = st.session_state['my_station']; db_ticket["start_time"] = datetime.datetime.now().isoformat()
                        trigger_audio(db_ticket['number'], st.session_state['my_station']); save_db(local_db); st.rerun()
                else: st.warning(f"No tickets for {station_type}.")
    with c2:
        count, avg_time = get_staff_efficiency(user['name'])
        st.metric("Performance", count, delta=avg_time + " avg/txn")
        st.divider()
        st.write("🅿️ Parked Tickets")
        parked = [t for t in local_db['tickets'] if t["status"] == "PARKED" and t["lane"] in my_lanes]
        for p in parked:
            if st.button(f"🔊 {p['number']}", key=p['id']):
                p["status"] = "SERVING"; p["served_by"] = st.session_state['my_station']; p["start_time"] = datetime.datetime.now().isoformat(); trigger_audio(p['number'], st.session_state['my_station']); save_db(local_db); st.rerun()

def render_admin_panel(user):
    local_db = load_db()
    st.title("🛠 Admin & Resources Manager")
    if st.sidebar.button("⬅ LOGOUT"): local_db['staff'][next((k for k,v in local_db['staff'].items() if v['name'] == user['name']), None)]['online'] = False; save_db(local_db); del st.session_state['user']; st.rerun()
    
    if user['role'] == "ADMIN": tabs = ["Users", "Counters", "Menu", "Exemptions", "Resources", "Announcements", "Backup"]
    elif user['role'] in ["BRANCH_HEAD", "SECTION_HEAD", "DIV_HEAD"]: tabs = ["Users", "Counters", "Menu", "Exemptions", "Resources", "Announcements", "Backup", "Analytics"]
    else: st.error("Access Denied"); return
    
    active = st.radio("Module", tabs, horizontal=True)
    st.divider()
    
    if active == "Menu":
        st.subheader("Manage Services Menu")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.info("Edit Transaction Types")
            cat_list = list(local_db['menu'].keys())
            sel_cat = st.selectbox("Select Category", cat_list)
            items = local_db['menu'][sel_cat]
            for i, (label, code, lane) in enumerate(items):
                with st.expander(f"{label} ({code})"):
                    new_label = st.text_input("Label", label, key=f"l_{i}")
                    new_code = st.text_input("Code", code, key=f"c_{i}")
                    new_lane = st.selectbox("Lane", ["C", "E", "F", "T", "A", "GATE"], index=["C", "E", "F", "T", "A", "GATE"].index(lane), key=f"ln_{i}")
                    if st.button("Update", key=f"up_{i}"): local_db['menu'][sel_cat][i] = (new_label, new_code, new_lane); save_db(local_db); st.success("Updated!"); st.rerun()
                    if st.button("Delete", key=f"del_{i}"): local_db['menu'][sel_cat].pop(i); save_db(local_db); st.rerun()
            st.markdown("---")
            st.write("Add New Transaction")
            add_lbl = st.text_input("New Label")
            add_code = st.text_input("New Code")
            add_lane = st.selectbox("Target Lane", ["C", "E", "F", "T", "A", "GATE"])
            if st.button("Add Transaction"): local_db['menu'][sel_cat].append((add_lbl, add_code, add_lane)); save_db(local_db); st.success("Added!"); st.rerun()

    elif active == "Exemptions":
        st.subheader("Manage Exemption Warnings")
        t_ret, t_death, t_fun = st.tabs(["Retirement", "Death", "Funeral"])
        def render_exemption_tab(claim_type):
            current_list = local_db['exemptions'].get(claim_type, [])
            st.write(f"Current Exemptions for **{claim_type}**:")
            for i, ex in enumerate(current_list):
                c1, c2 = st.columns([4, 1])
                c1.text(f"• {ex}")
                if c2.button("🗑", key=f"del_{claim_type}_{i}"): local_db['exemptions'][claim_type].pop(i); save_db(local_db); st.rerun()
            st.markdown("---")
            new_ex = st.text_input(f"Add New {claim_type} Exemption", key=f"new_{claim_type}")
            if st.button(f"Add to {claim_type}", key=f"add_{claim_type}"):
                if claim_type not in local_db['exemptions']: local_db['exemptions'][claim_type] = []
                local_db['exemptions'][claim_type].append(new_ex); save_db(local_db); st.success("Added!"); st.rerun()
        with t_ret: render_exemption_tab("Retirement")
        with t_death: render_exemption_tab("Death")
        with t_fun: render_exemption_tab("Funeral")

    elif active == "Users":
        st.subheader("Manage Users"); h1, h2, h3, h4, h5 = st.columns([1.5, 3, 2, 1, 0.5]); h1.markdown("**ID**"); h2.markdown("**Name**"); h3.markdown("**Station**")
        for uid, u in list(local_db['staff'].items()):
            c1, c2, c3, c4, c5 = st.columns([1.5, 3, 2, 0.5, 0.5]); c1.text(uid); c2.text(f"{u['name']} ({u['role']})"); c3.text(u.get('default_station', '-'))
            if c4.button("✏️", key=f"ed_{uid}"): st.session_state['edit_uid'] = uid; st.rerun()
            if c5.button("🗑", key=f"del_{uid}"): del local_db['staff'][uid]; save_db(local_db); st.rerun()
        st.markdown("---")
        uid_to_edit = st.session_state.get('edit_uid', None)
        if uid_to_edit:
            st.write(f"**Edit User: {uid_to_edit}**")
            with st.form("edit_user_form"):
                u_name = st.text_input("Name", local_db['staff'][uid_to_edit]['name'])
                u_role = st.selectbox("Role", ["MSR", "TELLER", "AO", "SECTION_HEAD", "BRANCH_HEAD", "ADMIN"], index=["MSR", "TELLER", "AO", "SECTION_HEAD", "BRANCH_HEAD", "ADMIN"].index(local_db['staff'][uid_to_edit]['role']))
                if st.form_submit_button("Save Changes"): local_db['staff'][uid_to_edit]['name'] = u_name; local_db['staff'][uid_to_edit]['role'] = u_role; save_db(local_db); del st.session_state['edit_uid']; st.success("Saved!"); st.rerun()
        else:
            st.write("**Add New User**")
            with st.form("add_user_form"):
                new_id = st.text_input("User ID (Login)")
                new_name = st.text_input("Display Name")
                new_role = st.selectbox("Role", ["MSR", "TELLER", "AO", "SECTION_HEAD", "BRANCH_HEAD", "ADMIN"])
                if st.form_submit_button("Create User"):
                    if new_id and new_name: local_db['staff'][new_id] = {"pass": "123", "role": new_role, "name": new_name, "default_station": "Counter 1", "status": "ACTIVE", "online": False}; save_db(local_db); st.success("Created!"); st.rerun()

    elif active == "Counters":
        for i, c in enumerate(local_db['config']['counter_map']): 
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.text(c['name']); c2.text(c['type'])
            if c3.button("🗑", key=f"dc_{i}"): local_db['config']['counter_map'].pop(i); save_db(local_db); st.rerun()
        with st.form("add_counter"): 
            cn = st.text_input("Name"); ct = st.selectbox("Type", ["Counter", "Teller", "Employer", "eCenter"])
            if st.form_submit_button("Add"): local_db['config']['counter_map'].append({"name": cn, "type": ct}); save_db(local_db); st.rerun()

    # --- V22.15 RESOURCES MANAGER (REPLACING BRAIN) ---
    elif active == "Resources":
        st.subheader("Manage Info Hub Content")
        
        # Display Current Resources
        for i, res in enumerate(local_db.get('resources', [])):
            with st.expander(f"{'🔗' if res['type'] == 'LINK' else '❓'} {res['label']}"):
                st.write(f"**Value:** {res['value']}")
                if st.button("Delete", key=f"res_del_{i}"): local_db['resources'].pop(i); save_db(local_db); st.rerun()
        
        st.markdown("---")
        st.write("**Add New Resource**")
        with st.form("new_res"):
            r_type = st.selectbox("Type", ["LINK", "FAQ"])
            r_label = st.text_input("Label / Question")
            r_value = st.text_area("URL / Answer")
            if st.form_submit_button("Add Resource"):
                if "resources" not in local_db: local_db['resources'] = []
                local_db['resources'].append({"type": r_type, "label": r_label, "value": r_value})
                save_db(local_db); st.success("Added!"); st.rerun()

    elif active == "Announcements":
        curr = " | ".join(local_db['announcements']); new_txt = st.text_area("Marquee", value=curr)
        if st.button("Update"): local_db['announcements'] = [new_txt]; save_db(local_db); st.success("Updated!")

    elif active == "Backup": st.download_button("📥 BACKUP", data=json.dumps(local_db), file_name="sss_backup.json")
    elif active == "Analytics": st.subheader("Data"); st.dataframe(pd.DataFrame(local_db['history']))

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
            local_db = load_db(); acct = next((v for k,v in local_db['staff'].items() if v["name"] == u or k == u), None); acct_key = next((k for k,v in local_db['staff'].items() if v["name"] == u or k == u), None)
            if acct and acct['pass'] == p: st.session_state['user'] = acct; local_db['staff'][acct_key]['online'] = True; save_db(local_db); st.rerun()
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
        tn = st.text_input("Enter Ticket #")
        if tn:
            local_db = load_db(); t = next((x for x in local_db['tickets'] if x["number"] == tn), None); t_hist = next((x for x in local_db['history'] if x["number"] == tn), None)
            if t:
                if t['status'] == "PARKED":
                    park_time = datetime.datetime.fromisoformat(t['park_timestamp']); remaining = datetime.timedelta(minutes=30) - (datetime.datetime.now() - park_time)
                    if remaining.total_seconds() > 0:
                        mins, secs = divmod(remaining.total_seconds(), 60)
                        st.markdown(f"""<div id="mob_timer_{t['id']}" style="font-size:30px; font-weight:bold; color:#b91c1c; text-align:center;">{int(mins):02d}:{int(secs):02d}</div><script>startTimer({remaining.total_seconds()}, "mob_timer_{t['id']}");</script>""", unsafe_allow_html=True); st.warning("⚠ TICKET PARKED. Please return to counter immediately.")
                    else: st.error("❌ YOUR TICKET HAS EXPIRED."); st.markdown("<h3 style='text-align:center; color:red;'>Please get a new ticket.</h3>", unsafe_allow_html=True)
                else:
                    st.info(f"Status: {t['status']}"); wait_str = calculate_specific_wait_time(t['id'], t['lane']); people_ahead = calculate_people_ahead(t['id'], t['lane']); c1, c2 = st.columns(2); c1.metric("Est. Wait", wait_str); c2.metric("People Ahead", f"{people_ahead}")
            elif t_hist: st.success("✅ TRANSACTION COMPLETE. Thank you for visiting SSS Gingoog!")
            else: st.error("Not Found")
            st.markdown("<div class='brand-footer'>System developed by RPT/SSSGingoog © 2026</div>", unsafe_allow_html=True)
    
    # --- V22.15 INFO HUB (NEW) ---
    with t2:
        st.subheader("Member Resources")
        
        # 1. Links
        st.markdown("### 🔗 Quick Links")
        links = [r for r in db.get('resources', []) if r['type'] == 'LINK']
        for l in links:
            st.markdown(f"""<a href="{l['value']}" target="_blank" class="info-link">{l['label']}</a>""", unsafe_allow_html=True)
        
        # 2. FAQs
        st.markdown("### ❓ Frequently Asked Questions")
        faqs = [r for r in db.get('resources', []) if r['type'] == 'FAQ']
        for f in faqs:
            with st.expander(f['label']):
                st.write(f['value'])

    with t3:
        with st.form("rev"):
            rate = st.slider("Rating", 1, 5); pers = st.text_input("Personnel"); comm = st.text_area("Comments")
            if st.form_submit_button("Submit"): local_db = load_db(); local_db['reviews'].append({"rating": rate, "personnel": pers, "comment": comm}); save_db(local_db); st.success("Thanks!")
    time.sleep(5); st.rerun()
