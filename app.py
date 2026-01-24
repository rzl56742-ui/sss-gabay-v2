# ==============================================================================
# SSS G-ABAY v4.0 - BRANCH OPERATING SYSTEM
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
st.set_page_config(page_title="SSS G-ABAY v4.0", page_icon="🇵🇭", layout="wide", initial_sidebar_state="collapsed")

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
<div class="watermark no-print">© 2026 rpt/sssgingoog | v4.0.0</div>
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
            "admin": {"pass": "sss2026", "role": "ADMIN", "name": "System Admin"},
            "head": {"pass": "head123", "role": "BRANCH_HEAD", "name": "Branch Head"},
            "section": {"pass": "sec123", "role": "SECTION_HEAD
