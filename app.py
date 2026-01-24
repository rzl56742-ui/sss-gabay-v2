# ==============================================================================
# SSS G-ABAY v4.1 - BRANCH OPERATING SYSTEM
# "World-Class Service, Zero-Install Architecture"
# COPYRIGHT: © 2026 rpt/sssgingoog
# ==============================================================================

import streamlit as st
import pandas as pd
import datetime
import time
import uuid
import qrcode
import base64
from io import BytesIO

# ==========================================
# 1. SYSTEM CONFIGURATION & CSS
# ==========================================
st.set_page_config(page_title="SSS G-ABAY v4.1", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

# CSS: WORLD-CLASS VISUALS & PRINT MEDIA QUERY
st.markdown("""
<style>
    /* Global Watermark */
    .watermark {
        position: fixed; bottom: 15px; right: 15px;
        color: rgba(0,0,0,0.5); font-size: 14px; font-family: monospace; font-weight: bold;
        z-index: 99999; pointer-events: none;
    }
    
    /* HIDE STREAMLIT UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* BIG BUTTON OVERRIDE */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 5em;
        font-weight: 800;
        font-size: 22px;
        text-transform: uppercase;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }

    /* SMALLER ACTION BUTTONS (For Counter/Admin) */
    .small-btn > button {
        height: 3em !important;
        font-size: 16px !important;
    }
    
    /* PRIORITY WARNING BOX */
    .prio-warning {
        background-color: #fee2e2; color: #991b1b; padding: 15px; border-radius: 10px;
        border: 2px solid #ef4444; text-align: center; font-weight: bold; margin-top: 10px; font-size: 14px;
    }
    
    /* REFERRAL BADGE */
    .ref-badge {
        background-color: #e0f2fe; color: #0369a1; padding: 5px 10px; border-radius: 5px;
        border: 1px solid #0369a1; font-size: 14px; font-weight: bold; margin-bottom: 10px; display: inline-block;
    }

    /* HIDE SIDEBAR IN DISPLAY MODE */
    [data-testid="stSidebar"][aria-expanded="false"] { display: none; }

    /* --- PRINT STYLES (2" x 4" Landscape) --- */
    @media print {
        @page { size: 4in 2in landscape; margin: 0; }
        body * { visibility: hidden; }
        .printable-ticket, .printable-ticket * { visibility: visible; }
        .printable-ticket {
            position: fixed; left: 0; top: 0; width: 100%; height: 100%;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            background: white; color: black; font-family: sans-serif;
            border: 2px solid black; padding: 10px;
        }
        .no-print { display: none !important; }
    }
</style>
<div class="watermark no-print">© 2026 rpt/sssgingoog | v4.1.0</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE (THE BRAIN)
# ==========================================
if 'db' not in st.session_state:
    st.session_state['db'] = {
        "tickets": [],
        "history": [], 
        "reviews": [], # Stores customer feedback
        "config": {
            "branch_name": "GINGOOG BRANCH",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Social_Security_System_%28SSS%29.svg/1200px-Social_Security_System_%28SSS%29.svg.png",
            "lanes": {"E": "eCenter", "F": "Fast Lane", "C": "Counter", "T": "Teller", "A": "Employer"}
        },
        "staff": {
            "admin": {
                "pass": "sss2026", 
                "role": "ADMIN", 
                "name": "System Admin"
            },
            "head": {
                "pass": "head123", 
                "role": "BRANCH_HEAD", 
                "name": "Branch Head"
            },
            "section": {
                "pass": "sec123", 
                "role": "SECTION_HEAD", 
                "name": "Section Head"
            },
            "c1": {
                "pass": "123", 
                "role": "MSR", 
                "name": "Maria Santos", 
                "station": "Counter 1", 
                "break": False, 
                "break_log": []
            },
            "c2": {
                "pass": "123", 
                "role": "TELLER", 
                "name": "Juan Cruz", 
                "station": "Teller 1", 
                "break": False, 
                "break_log": []
            }
        },
        "announcements": ["Welcome to SSS Gingoog. Operating Hours: 8:00 AM - 5:00 PM."]
    }

db = st.session_state['db']

# ==========================================
# 3. CORE LOGIC & METRICS
# ==========================================
def generate_ticket(service, lane_code, is_priority, is_appt=False, appt_name=None):
    prefix = "A" if is_appt else ("P" if is_priority else "R")
    count = len([t for t in db["tickets"] if t["lane"] == lane_code]) + 1
    ticket_num = f"{lane_code}{prefix}-{count:03d}"
    
    new_t = {
        "id": str(uuid.uuid4()), 
        "number": ticket_num, 
        "lane": lane_code,
        "service": service, 
        "type": "APPOINTMENT" if is_appt else ("PRIORITY" if is_priority else "REGULAR"),
        "status": "WAITING", 
        "timestamp": datetime.datetime.now(), # Arrival
        "start_time": None, 
        "end_time": None, 
        "park_timestamp": None, 
        "history": [],
        "appt_name": appt_name,
        "served_by": None,
        "ref_from": None
    }
    db["tickets"].append(new_t)
    return new_t

def get_prio_score(t):
    base = t["timestamp"].timestamp()
    bonus = 3600 if t.get("appt_name") else (2700 if t.get("ref_from") else (1800 if t["type"] == "PRIORITY" else 0))
    return base - bonus

def get_staff_efficiency(staff_name):
    my_txns = [t for t in db["history"] if t.get("served_by") == staff_name and t.get("start_time") and t.get("end_time")]
    if not my_txns: return 0, "0m"
    total_sec = sum([(t["end_time"] - t["start_time"]).total_seconds() for t in my_txns])
    avg_min = round((total_sec / len(my_txns)) / 60, 1)
    return len(my_txns), f"{avg_min}m"

# ==========================================
# 4. MODULES
# ==========================================

# --- MODULE A: THE KIOSK ---
def render_kiosk():
    # HEADER
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        if db["config"]["logo_url"].startswith("http"): st.image(db["config"]["logo_url"], width=100)
        else: st.markdown(f'<img src="data:image/png;base64,{db["config"]["logo_url"]}" width="100">', unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; color:#0038A8; margin:0;'>SSS {db['config']['branch_name']}</h1>", unsafe_allow_html=True)

    # PAGE 1: THE GATE
    if 'kiosk_step' not in st.session_state:
        st.markdown("<br>", unsafe_allow_html=True)
        col_reg, col_prio = st.columns([3, 2], gap="large")
        
        with col_reg:
            if st.button("👤 REGULAR LANE", type="primary"):
                st.session_state['is_prio'] = False; st.session_state['kiosk_step'] = 'menu'; st.rerun()
            st.info("Standard Transactions")
        
        with col_prio:
            if st.button("♿ PRIORITY LANE"):
                st.session_state['is_prio'] = True; st.session_state['kiosk_step'] = 'menu'; st.rerun()
            st.markdown('<div class="prio-warning">⚠ WARNING: SENIOR / PWD / PREGNANT ONLY<br>Wrong selection will be transferred.</div>', unsafe_allow_html=True)

    # PAGE 2: MAIN MENU
    elif st.session_state['kiosk_step'] == 'menu':
        st.markdown("### Select Service Category")
        m1, m2, m3 = st.columns(3)
        
        with m1:
            if st.button("💳 PAYMENTS\n(Contrib/Loans)", type="primary"):
                t = generate_ticket("Payment", "T", st.session_state['is_prio'])
                st.session_state['last_ticket'] = t; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with m2:
            if st.button("💼 EMPLOYERS", type="primary"):
                t = generate_ticket("Account Management", "A", st.session_state['is_prio'])
                st.session_state['last_ticket'] = t; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            st.caption("Account Management Section")
        with m3:
            if st.button("👤 MEMBER SERVICES", type="primary"):
                st.session_state['kiosk_step'] = 'mss'; st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ START OVER"): del st.session_state['kiosk_step']; st.rerun()

    # PAGE 3: MSS SUB-MENU
    elif st.session_state['kiosk_step'] == 'mss':
        st.markdown("### 👤 Member Services")
        g1, g2, g3, g4 = st.columns(4)
        
        with g1:
            st.error("🏥 BENEFITS")
            if st.button("Maternity/Sickness"): generate_ticket("Ben-Mat/Sick", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Retirement/Death/Funeral"): st.session_state['kiosk_step'] = 'gate_rd'; st.rerun()
            if st.button("Disability/Unemployment"): generate_ticket("Ben-Dis/Unemp", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with g2:
            st.warning("💰 LOANS")
            if st.button("Salary/Conso"): generate_ticket("Ln-Sal/Conso", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Calamity/Emergency"): generate_ticket("Ln-Cal/Emerg", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Pension Loan (Retiree/Survivor)"): generate_ticket("Ln-Pension", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with g3:
            st.success("📝 MEMBER DATA CHANGE")
            if st.button("1. Contact Info Update"): generate_ticket("Rec-Contact", "F", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("2. Simple Corrections"): generate_ticket("Rec-Simple", "F", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("3. Complex Corrections"): generate_ticket("Rec-Complex", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("4. Request Verification"): generate_ticket("Rec-Verify", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with g4:
            st.info("💻 eSERVICES")
            if st.button("My.SSS Reset"): generate_ticket("eSvc-Reset", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("SS Number"): generate_ticket("eSvc-SSNum", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("Status Inquiry"): generate_ticket("eSvc-Status", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
            if st.button("DAEM/ACOP"): generate_ticket("eSvc-DAEM/ACOP", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⬅ Back"): st.session_state['kiosk_step'] = 'menu'; st.rerun()

    # PAGE 4: SPECIAL GATE
    elif st.session_state['kiosk_step'] == 'gate_rd':
        st.warning("SPECIAL CHECK: Do you have pending cases, portability issues, or guardianship?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("YES (Complex Case)"): generate_ticket("Ben-Ret(C)", "C", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()
        with c2:
            if st.button("NO (Regular Claim)"): generate_ticket("Ben-Ret(S)", "E", st.session_state['is_prio']); st.session_state['last_ticket'] = db["tickets"][-1]; st.session_state['kiosk_step'] = 'ticket'; st.rerun()

    # PAGE 5: TICKET DISPLAY
    elif st.session_state['kiosk_step'] == 'ticket':
        t = st.session_state['last_ticket']
        bg_col = "#FFD700" if t['type'] == 'PRIORITY' else "#0038A8"
        txt_col = "#0038A8" if t['type'] == 'PRIORITY' else "white"
        
        st.markdown(f"""
        <div class="ticket-card no-print" style='background-color: {bg_col}; color: {txt_col};'>
            <h2 style='margin:0;'>YOUR NUMBER</h2>
            <h1 style='font-size: 120px; margin:0; font-weight: 800;'>{t['number']}</h1>
            <h3 style='margin:0; font-size: 30px;'>{t['service']}</h3>
            <p style='margin-top:20px;'>Please sit and wait for the voice call.</p>
        </div>
        <div class="printable-ticket">
            <h2 style="margin:0;">SSS {db['config']['branch_name']}</h2>
            <h1 style="font-size: 80px; margin: 10px 0;">{t['number']}</h1>
            <h3 style="margin:0;">{t['service']}</h3>
            <p>{t['timestamp'].strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ DONE (No Print)"):
                del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()
        with c2:
            if st.button("🖨️ PRINT TICKET"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
                time.sleep(2)
                del st.session_state['last_ticket']; del st.session_state['kiosk_step']; st.rerun()

# --- MODULE B: DISPLAY (TV Mode) ---
def render_display():
    st.markdown(f"<h1 style='text-align: center; color: #0038A8; margin-top: -50px;'>NOW SERVING</h1>", unsafe_allow_html=True)
    col_q, col_v = st.columns([2, 3])
    with col_q:
        serving = [t for t in db["tickets"] if t["status"] == "SERVING"]
        if not serving: st.info("Waiting for counters...")
        for t in serving:
            b_col = "#de350b" if t['lane'] == "T" else ("#0052cc" if t['lane'] == "E" else "#6554c0")
            display_name = t.get("appt_name") if t.get("appt_name") else t['number']
            extra_style = "border: 4px solid gold;" if t.get("appt_name") else ""
            ref_badge = f"<div style='background:white; color:black; font-size:12px; padding:2px 5px; border-radius:3px;'>FROM: {t.get('ref_from')}</div>" if t.get('ref_from') else ""

            st.markdown(f"""
            <div style='background-color: {b_col}; color: white; padding: 20px; margin-bottom: 15px; border-radius: 15px; display: flex; justify-content: space-between; {extra_style}'>
                <div><div style='font-size: 60px; font-weight: bold;'>{display_name}</div>{ref_badge}</div>
                <div style='text-align: right;'>
                    <div style='font-size: 30px;'>{t.get('served_by','Counter')}</div>
                    <div style='font-size: 18px;'>{t['service']}</div>
                </div>
            </div>""", unsafe_allow_html=True)
    with col_v:
        st.video("https://www.youtube.com/watch?v=DummyVideo") 
        parked = [t for t in db["tickets"] if t["status"] == "PARKED"]
        if parked:
            nums = ", ".join([t['number'] for t in parked])
            st.markdown(f"""
            <div style='background-color: #b91c1c; color: white; padding: 25px; border-radius: 15px; margin-top: 20px; text-align: center; animation: pulse 2s infinite;'>
                <h2 style='margin:0;'>⚠ RECALL: {nums}</h2>
                <p>Please approach counter immediately. Forfeiture in 30 mins.</p>
            </div>""", unsafe_allow_html=True)
    txt = " | ".join(db["announcements"])
    st.markdown(f"<div style='background: #FFD700; color: black; padding: 10px; font-weight: bold; position: fixed; bottom: 0; width: 100%;'><marquee>{txt}</marquee></div>", unsafe_allow_html=True)
    time.sleep(3); st.rerun()

# --- MODULE C: COUNTER (Locked Auto-Next) ---
def render_counter(user):
    st.sidebar.title(f"👮 {user['name']}")
    
    # BREAK MODE
    on_break = st.sidebar.toggle("☕ Break Mode", value=user.get('break', False))
    if on_break != user.get('break', False): 
        user['break'] = on_break
        if on_break: 
            user.setdefault('break_log', []).append({'start': datetime.datetime.now(), 'end': None})
        else:
            if user.get('break_log'): user['break_log'][-1]['end'] = datetime.datetime.now()
        st.rerun()
    if on_break: st.warning("⛔ You are on break."); return

    st.title(f"Station: {user.get('station', 'General')}")
    
    my_lanes = ["C", "E", "F"] 
    queue = [t for t in db["tickets"] if t["status"] == "WAITING" and t["lane"] in my_lanes]
    queue.sort(key=get_prio_score)
    current = next((t for t in db["tickets"] if t["status"] == "SERVING" and t.get("served_by") == user['name']), None)
    
    if 'refer_modal' not in st.session_state: st.session_state['refer_modal'] = False

    c1, c2 = st.columns([2,1])
    with c1:
        if current:
            st.markdown(f"""<div style='padding:20px; background:#e0f2fe; border-radius:10px; border-left:5px solid #0369a1;'>
            <h1 style='margin:0; color:#0369a1'>{current['number']}</h1>
            <h3>{current['service']}</h3></div>""", unsafe_allow_html=True)
            if current.get("ref_from"): st.markdown(f'<div class="ref-badge">↩ REFERRED FROM: {current["ref_from"]}</div>', unsafe_allow_html=True)
            if current.get("appt_name"): st.info(f"📅 APPOINTMENT: {current['appt_name']}")
            
            if st.session_state['refer_modal']:
                with st.form("referral_form"):
                    st.write("🔄 Transfer Details")
                    target = st.selectbox("To Lane", ["T (Teller)", "A (Employer)", "C (Complex)", "E (eCenter)"])
                    reason = st.text_input("Reason")
                    if st.form_submit_button("Confirm Transfer"):
                        current["lane"] = target.split()[0]; current["status"] = "WAITING"; current["served_by"] = None
                        current["ref_from"] = user['name']; current["history"].append(f"Ref by {user['name']}: {reason}")
                        st.session_state['refer_modal'] = False; st.rerun()
            else:
                st.markdown("<br>", unsafe_allow_html=True)
                b1, b2, b3 = st.columns(3)
                if b1.button("✅ COMPLETE", key="comp"): 
                    current["status"] = "COMPLETED"; current["end_time"] = datetime.datetime.now()
                    db["history"].append(current); st.rerun()
                if b2.button("🅿️ PARK", key="park"): 
                    current["status"] = "PARKED"; current["park_timestamp"] = datetime.datetime.now(); st.rerun()
                if b3.button("🔄 REFER", key="ref"): 
                    st.session_state['refer_modal'] = True; st.rerun()
        else:
            # LOCKED: ONLY AUTO-NEXT ALLOWED
            if st.button("🔊 CALL NEXT TICKET", type="primary"):
                if queue:
                    nxt = queue[0]; nxt["status"] = "SERVING"; nxt["served_by"] = user["name"]
                    nxt["start_time"] = datetime.datetime.now(); st.rerun()
                else: st.info("No tickets in queue.")
                
    with c2:
        count, avg_time = get_staff_efficiency(user['name'])
        st.metric("My Performance", count, delta=avg_time + " avg/txn")
        st.divider()
        st.write("🅿️ Recall Parked")
        parked = [t for t in db["tickets"] if t["status"] == "PARKED"]
        for p in parked:
            if st.button(f"🔊 {p['number']}", key=p['id']):
                p["status"] = "SERVING"; p["served_by"] = user["name"]; st.rerun()

# --- MODULE D: ADMIN (Deep Analytics) ---
def render_admin_panel(user):
    st.sidebar.title("🛠 Admin Menu")
    
    if user['role'] == "ADMIN":
        mode = st.sidebar.radio("Module", ["User Management", "System Config"])
        if mode == "User Management":
            st.title("Staff CRUD")
            st.dataframe(pd.DataFrame.from_dict(db["staff"], orient='index'))
            c1, c2 = st.columns(2)
            with c1:
                with st.form("add_user"):
                    st.subheader("Add/Edit User")
                    u_id = st.text_input("Username (ID)"); u_name = st.text_input("Full Name")
                    u_role = st.selectbox("Role", ["MSR", "TELLER", "ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIVISION_HEAD"])
                    u_pass = st.text_input("Password")
                    if st.form_submit_button("Save User"):
                        db["staff"][u_id] = {"pass": u_pass, "role": u_role, "name": u_name, "station": "General"}
                        st.success("Saved"); st.rerun()
            with c2:
                with st.form("del_user"):
                    st.subheader("Delete User")
                    del_id = st.text_input("Username to Delete")
                    if st.form_submit_button("DELETE"):
                        if del_id in db["staff"]: del db["staff"][del_id]; st.success("Deleted"); st.rerun()

        elif mode == "System Config":
            st.title("System Configuration")
            st.text_input("Branch Name", value=db["config"]["branch_name"])
            
    elif user['role'] in ["BRANCH_HEAD", "SECTION_HEAD", "DIVISION_HEAD"]:
        mode = st.sidebar.radio("Module", ["Advanced Analytics", "Appointments"])
        
        if mode == "Advanced Analytics":
            st.title("📊 Branch Performance Intelligence")
            
            # 1. KPI CARDS
            hist = db["history"]
            if hist:
                df = pd.DataFrame(hist)
                # Calcs
                df['wait_sec'] = df.apply(lambda x: (x['start_time'] - x['timestamp']).total_seconds(), axis=1)
                df['svc_sec'] = df.apply(lambda x: (x['end_time'] - x['start_time']).total_seconds(), axis=1)
                
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Avg Wait Time", f"{round(df['wait_sec'].mean()/60, 1)} min")
                k2.metric("Max Wait Time", f"{round(df['wait_sec'].max()/60, 1)} min")
                k3.metric("Avg Svc Time", f"{round(df['svc_sec'].mean()/60, 1)} min")
                k4.metric("Total Transactions", len(df))
                
                # 2. TRENDS
                st.subheader("📈 Volume Trends")
                st.bar_chart(df['service'].value_counts())
                
                # 3. CUSTOMER REVIEWS
                st.subheader("⭐ Customer Feedback")
                if db["reviews"]:
                    rev_df = pd.DataFrame(db["reviews"])
                    avg_rate = rev_df['rating'].mean()
                    st.metric("Customer Satisfaction Score (CSAT)", f"{round(avg_rate, 1)} / 5.0")
                    st.dataframe(rev_df[['rating', 'personnel', 'comment', 'timestamp']])
                else: st.info("No reviews yet.")

            else: st.info("No transaction history yet.")
            
        elif mode == "Appointments":
            st.title("Appointment Manager")
            with st.form("appt"):
                nm = st.text_input("Member Name"); svc = st.selectbox("Service", ["Death Claim", "Pension", "Salary Loan"])
                if st.form_submit_button("Inject Appointment"):
                    generate_ticket(svc, "C", True, is_appt=True, appt_name=nm)
                    st.success(f"Added {nm} to Top of Queue")

# ==========================================
# 5. MAIN ROUTER
# ==========================================
st.sidebar.title("🔧 Dev Tools")
st.sidebar.info("Use this menu to switch views without login.")
sim_mode = st.sidebar.radio("View Mode", ["Public (Mobile)", "Staff Login", "Simulate Kiosk"])

params = st.query_params
access_code = params.get("access")

if access_code == "staff" or sim_mode == "Staff Login":
    if 'user' not in st.session_state:
        st.title("Staff Login")
        u = st.text_input("Username"); p = st.text_input("Password", type="password")
        if st.button("Login"):
            acct = next((v for k,v in db["staff"].items() if v["name"] == u or k == u), None)
            if acct and acct["pass"] == p: st.session_state['user'] = acct; st.rerun()
            else: st.error("Invalid")
    else:
        user = st.session_state['user']
        if user['role'] in ["MSR", "TELLER"]: render_counter(user)
        elif user['role'] in ["ADMIN", "BRANCH_HEAD", "SECTION_HEAD", "DIVISION_HEAD"]:
            sub_mode = st.sidebar.selectbox("Console View", ["Management Panel", "Display Mode"])
            if sub_mode == "Management Panel": render_admin_panel(user)
            else: render_display()

elif sim_mode == "Simulate Kiosk":
    render_kiosk()

else:
    # PUBLIC MOBILE TRACKER & FEEDBACK
    if db["config"]["logo_url"].startswith("http"): st.image(db["config"]["logo_url"], width=50)
    else: st.markdown(f'<img src="data:image/png;base64,{db["config"]["logo_url"]}" width="50">', unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🎫 Tracker", "⭐ Rate Us"])
    
    with t1:
        st.markdown("### G-ABAY Mobile Tracker")
        tn = st.text_input("Enter Ticket # (e.g. TC-001)")
        if tn:
            t = next((x for x in db["tickets"] if x["number"] == tn), None)
            if t:
                st.info(f"Status: {t['status']}")
                if t['status'] == "WAITING":
                    pos = len([x for x in db["tickets"] if x['lane'] == t['lane'] and x['status'] == 'WAITING' and x['timestamp'] < t['timestamp']])
                    st.metric("People Ahead", pos)
                elif t['status'] == "PARKED": st.error("URGENT: YOU WERE CALLED!")
            else: st.error("Ticket Not Found")

    with t2:
        st.markdown("### We value your feedback!")
        with st.form("review"):
            st.markdown("##### How was your experience?")
            c1, c2, c3, c4, c5 = st.columns(5)
            # Simple radio for 1-5 rating
            rate = st.radio("Rating", [1,2,3,4,5], horizontal=True, format_func=lambda x: "⭐" * x)
            
            pers = st.text_input("Name of Personnel (Optional)")
            comm = st.text_area("Comments / Suggestions")
            if st.form_submit_button("Submit Feedback"):
                db["reviews"].append({
                    "rating": rate, "personnel": pers, "comment": comm, 
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.success("Thank you for your feedback!")
