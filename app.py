import streamlit as st
import pandas as pd
import csv
import io
import re
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

st.set_page_config(page_title="SENTINEL | Disaster Tweet Classifier", page_icon="🛰️", layout="wide")

# ============================================
# DESIGN TOKENS  —  "Situation Room" console theme
# ============================================
BG          = "#0A0E14"
SURFACE     = "#121826"
SURFACE_2   = "#1A2233"
BORDER      = "#242C3D"
TEXT        = "#E7EAF2"
TEXT_MUTED  = "#8B93A7"
AMBER       = "#F5A623"   # brand / primary accent
CRITICAL    = "#FF4D5E"
HIGH        = "#FF8A3D"
MEDIUM      = "#F5C518"
SAFE        = "#2ED988"
CYAN        = "#3AB7FF"

SEVERITY_COLOR = {'CRITICAL': CRITICAL, 'HIGH': HIGH, 'MEDIUM': MEDIUM, 'SAFE': SAFE}
SEVERITY_RANK  = {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1}

# ============================================
# SESSION STATE
# ============================================
defaults = {
    'history': [], 'all_keywords': [], 'all_locations': [], 'all_categories': [],
    'stats': {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'safe': 0},
    'tweet_input_value': "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================
# KEYWORD ENGINE
# word -> (severity, category)
# Matching uses regex word-boundaries so "fire" won't match "fireplace",
# and multi-word phrases like "gas leak" are matched as whole phrases.
# ============================================
DISASTER_WORDS = {
    # --- Natural disasters ---
    'earthquake': ('HIGH', '🌍 Natural Disaster'), 'aftershock': ('HIGH', '🌍 Natural Disaster'),
    'tsunami': ('CRITICAL', '🌍 Natural Disaster'), 'tidal wave': ('CRITICAL', '🌍 Natural Disaster'),
    'flood': ('HIGH', '🌍 Natural Disaster'), 'flooding': ('HIGH', '🌍 Natural Disaster'),
    'flash flood': ('CRITICAL', '🌍 Natural Disaster'),
    'hurricane': ('HIGH', '🌍 Natural Disaster'), 'typhoon': ('HIGH', '🌍 Natural Disaster'),
    'cyclone': ('CRITICAL', '🌍 Natural Disaster'), 'storm surge': ('CRITICAL', '🌍 Natural Disaster'),
    'tornado': ('HIGH', '🌍 Natural Disaster'), 'twister': ('HIGH', '🌍 Natural Disaster'),
    'volcano': ('CRITICAL', '🌍 Natural Disaster'), 'eruption': ('CRITICAL', '🌍 Natural Disaster'),
    'lava': ('HIGH', '🌍 Natural Disaster'),
    'landslide': ('HIGH', '🌍 Natural Disaster'), 'mudslide': ('HIGH', '🌍 Natural Disaster'),
    'avalanche': ('CRITICAL', '🌍 Natural Disaster'),
    'sinkhole': ('MEDIUM', '🌍 Natural Disaster'),
    'wildfire': ('HIGH', '🔥 Fire & Explosion'), 'bushfire': ('HIGH', '🔥 Fire & Explosion'),
    'drought': ('MEDIUM', '🌍 Natural Disaster'), 'famine': ('CRITICAL', '🌍 Natural Disaster'),
    'heatwave': ('MEDIUM', '🌍 Natural Disaster'), 'blizzard': ('MEDIUM', '🌍 Natural Disaster'),
    'hailstorm': ('MEDIUM', '🌍 Natural Disaster'), 'monsoon': ('MEDIUM', '🌍 Natural Disaster'),
    'storm': ('MEDIUM', '🌍 Natural Disaster'), 'thunderstorm': ('MEDIUM', '🌍 Natural Disaster'),

    # --- Fire & explosion ---
    'fire': ('MEDIUM', '🔥 Fire & Explosion'), 'wildfires': ('HIGH', '🔥 Fire & Explosion'),
    'explosion': ('CRITICAL', '🔥 Fire & Explosion'), 'blast': ('CRITICAL', '🔥 Fire & Explosion'),
    'gas leak': ('CRITICAL', '🔥 Fire & Explosion'), 'chemical leak': ('CRITICAL', '🔥 Fire & Explosion'),
    'chemical spill': ('CRITICAL', '🔥 Fire & Explosion'), 'oil spill': ('HIGH', '🔥 Fire & Explosion'),
    'arson': ('HIGH', '🔥 Fire & Explosion'), 'inferno': ('CRITICAL', '🔥 Fire & Explosion'),
    'burning': ('MEDIUM', '🔥 Fire & Explosion'), 'smoke': ('MEDIUM', '🔥 Fire & Explosion'),

    # --- Structural / transport accidents ---
    'collapse': ('HIGH', '🏚️ Structural Accident'), 'collapsed': ('HIGH', '🏚️ Structural Accident'),
    'building collapse': ('CRITICAL', '🏚️ Structural Accident'), 'bridge collapse': ('CRITICAL', '🏚️ Structural Accident'),
    'roof collapse': ('HIGH', '🏚️ Structural Accident'),
    'crash': ('MEDIUM', '🚧 Accident'), 'car crash': ('MEDIUM', '🚧 Accident'),
    'plane crash': ('CRITICAL', '🚧 Accident'), 'train crash': ('CRITICAL', '🚧 Accident'),
    'derailment': ('CRITICAL', '🚧 Accident'), 'derailed': ('CRITICAL', '🚧 Accident'),
    'shipwreck': ('HIGH', '🚧 Accident'), 'capsized': ('HIGH', '🚧 Accident'), 'sinking ship': ('CRITICAL', '🚧 Accident'),
    'pileup': ('HIGH', '🚧 Accident'), 'collision': ('MEDIUM', '🚧 Accident'),
    'power outage': ('MEDIUM', '🏚️ Structural Accident'), 'blackout': ('MEDIUM', '🏚️ Structural Accident'),
    'dam failure': ('CRITICAL', '🏚️ Structural Accident'), 'dam breach': ('CRITICAL', '🏚️ Structural Accident'),

    # --- Violence & security ---
    'attack': ('CRITICAL', '🛡️ Violence & Security'), 'terrorist': ('CRITICAL', '🛡️ Violence & Security'),
    'terrorism': ('CRITICAL', '🛡️ Violence & Security'), 'bombing': ('CRITICAL', '🛡️ Violence & Security'),
    'shooting': ('CRITICAL', '🛡️ Violence & Security'), 'gunfire': ('CRITICAL', '🛡️ Violence & Security'),
    'gunman': ('CRITICAL', '🛡️ Violence & Security'), 'active shooter': ('CRITICAL', '🛡️ Violence & Security'),
    'hostage': ('CRITICAL', '🛡️ Violence & Security'), 'kidnapping': ('CRITICAL', '🛡️ Violence & Security'),
    'stabbing': ('CRITICAL', '🛡️ Violence & Security'), 'riot': ('HIGH', '🛡️ Violence & Security'),
    'looting': ('HIGH', '🛡️ Violence & Security'), 'unrest': ('MEDIUM', '🛡️ Violence & Security'),

    # --- Health emergencies ---
    'outbreak': ('CRITICAL', '🏥 Health Emergency'), 'epidemic': ('CRITICAL', '🏥 Health Emergency'),
    'pandemic': ('CRITICAL', '🏥 Health Emergency'), 'virus': ('MEDIUM', '🏥 Health Emergency'),
    'infection': ('MEDIUM', '🏥 Health Emergency'), 'contamination': ('HIGH', '🏥 Health Emergency'),
    'quarantine': ('MEDIUM', '🏥 Health Emergency'),

    # --- Casualty / general emergency terms ---
    'killed': ('CRITICAL', '🚨 Casualty Report'), 'dead': ('CRITICAL', '🚨 Casualty Report'),
    'death': ('CRITICAL', '🚨 Casualty Report'), 'deaths': ('CRITICAL', '🚨 Casualty Report'),
    'casualties': ('CRITICAL', '🚨 Casualty Report'), 'fatalities': ('CRITICAL', '🚨 Casualty Report'),
    'injured': ('HIGH', '🚨 Casualty Report'), 'wounded': ('HIGH', '🚨 Casualty Report'),
    'missing': ('HIGH', '🚨 Casualty Report'), 'trapped': ('HIGH', '🚨 Casualty Report'),
    'victims': ('HIGH', '🚨 Casualty Report'),
    'evacuation': ('HIGH', '🚨 Casualty Report'), 'evacuate': ('HIGH', '🚨 Casualty Report'),
    'rescue': ('MEDIUM', '🚨 Casualty Report'), 'rescued': ('MEDIUM', '🚨 Casualty Report'),
    'emergency': ('HIGH', '🚨 Casualty Report'), 'sos': ('CRITICAL', '🚨 Casualty Report'),
    'warning': ('MEDIUM', '🚨 Casualty Report'), 'alert': ('MEDIUM', '🚨 Casualty Report'),
    'disaster': ('HIGH', '🚨 Casualty Report'), 'catastrophe': ('CRITICAL', '🚨 Casualty Report'),
    'state of emergency': ('CRITICAL', '🚨 Casualty Report'), 'declared emergency': ('CRITICAL', '🚨 Casualty Report'),
}

# sort longest phrase first so multi-word phrases are checked before single words
SORTED_TERMS = sorted(DISASTER_WORDS.keys(), key=len, reverse=True)
TERM_PATTERNS = {term: re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE) for term in SORTED_TERMS}

CITIES = [
    'Karachi', 'Lahore', 'Islamabad', 'Peshawar', 'Quetta', 'Multan', 'Faisalabad', 'Rawalpindi',
    'New York', 'Los Angeles', 'Chicago', 'Florida', 'California', 'Texas', 'Miami',
    'London', 'Manchester', 'Paris', 'Berlin', 'Madrid', 'Rome', 'Moscow',
    'Tokyo', 'Osaka', 'Beijing', 'Shanghai', 'Seoul', 'Mumbai', 'Delhi', 'Bangalore', 'Kolkata',
    'Dubai', 'Abu Dhabi', 'Riyadh', 'Istanbul', 'Cairo', 'Jakarta', 'Manila', 'Bangkok',
    'Sydney', 'Melbourne', 'Toronto', 'Vancouver', 'Pakistan', 'India', 'Japan', 'China',
    'Afghanistan', 'Iran', 'Nepal', 'Bangladesh', 'Turkey', 'Syria', 'Yemen', 'Philippines',
    'Indonesia', 'Australia', 'Canada', 'Mexico', 'Brazil', 'Haiti', 'Chile', 'Nigeria',
]
CITY_PATTERNS = {c: re.compile(r'\b' + re.escape(c) + r'\b', re.IGNORECASE) for c in CITIES}


def analyze_text(text: str):
    """Single source of truth for classification — used by both Single Tweet and Batch tabs."""
    found, categories = [], []
    for term in SORTED_TERMS:
        if TERM_PATTERNS[term].search(text):
            found.append(term)
            categories.append(DISASTER_WORDS[term][1])

    severity = None
    if found:
        top_rank = max(SEVERITY_RANK[DISASTER_WORDS[t][0]] for t in found)
        severity = [k for k, v in SEVERITY_RANK.items() if v == top_rank][0]

    location = None
    for city in CITIES:
        if CITY_PATTERNS[city].search(text):
            location = city
            break

    category = Counter(categories).most_common(1)[0][0] if categories else None
    weight_sum = sum(SEVERITY_RANK[DISASTER_WORDS[t][0]] for t in found)
    confidence = min(97, 58 + weight_sum * 7) if found else 90

    return {
        'found': found, 'severity': severity, 'location': location,
        'category': category, 'confidence': confidence,
    }


def highlight_text(text: str, found: list) -> str:
    highlighted = text
    for term in sorted(found, key=len, reverse=True):
        pattern = TERM_PATTERNS[term]
        highlighted = pattern.sub(
            lambda m: f'<mark style="background:{AMBER}33; color:{AMBER}; padding:1px 4px; border-radius:3px; font-weight:600;">{m.group(0)}</mark>',
            highlighted
        )
    return highlighted

# ============================================
# GLOBAL STYLE
# ============================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: {BG}; color: {TEXT}; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.6rem; max-width: 1180px; }}
h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif !important; color: {TEXT} !important; }}

.console-bar {{
    display: flex; align-items: center; justify-content: space-between;
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 14px 22px; margin-bottom: 22px;
}}
.console-title {{
    font-family: 'Space Grotesk', sans-serif; font-size: 1.7rem; font-weight: 700;
    letter-spacing: 0.5px; color: {TEXT}; margin: 0; display: flex; align-items: center; gap: 10px;
}}
.console-sub {{
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 1.5px;
    color: {TEXT_MUTED}; text-transform: uppercase; margin-top: 2px;
}}
.status-pill {{
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 1px;
    color: {SAFE}; background: rgba(46, 217, 136, 0.1); border: 1px solid rgba(46, 217, 136, 0.35);
    padding: 6px 14px; border-radius: 20px; display: flex; align-items: center; gap: 8px;
}}
.pulse-dot {{
    width: 8px; height: 8px; border-radius: 50%; background: {SAFE};
    box-shadow: 0 0 0 0 rgba(46, 217, 136, 0.7); animation: pulse 1.8s infinite;
}}
@keyframes pulse {{
    0% {{ box-shadow: 0 0 0 0 rgba(46, 217, 136, 0.6); }}
    70% {{ box-shadow: 0 0 0 8px rgba(46, 217, 136, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(46, 217, 136, 0); }}
}}

.impact-card {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-left: 3px solid {AMBER};
    border-radius: 8px; padding: 16px 18px; height: 100%;
}}
.impact-label {{
    font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; letter-spacing: 1.5px;
    color: {AMBER}; text-transform: uppercase; margin-bottom: 6px;
}}
.impact-text {{ color: {TEXT_MUTED}; font-size: 0.92rem; line-height: 1.5; }}
.impact-text b {{ color: {TEXT}; }}

.result-card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; padding: 22px 24px; margin: 16px 0; }}
.result-critical {{ border-left: 4px solid {CRITICAL}; }}
.result-high {{ border-left: 4px solid {HIGH}; }}
.result-medium {{ border-left: 4px solid {MEDIUM}; }}
.result-safe {{ border-left: 4px solid {SAFE}; }}

.result-head {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 700; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; }}
.result-row {{ display: flex; gap: 10px; padding: 6px 0; font-size: 0.93rem; border-bottom: 1px dashed {BORDER}; }}
.result-row:last-child {{ border-bottom: none; }}
.result-key {{ font-family: 'JetBrains Mono', monospace; color: {TEXT_MUTED}; min-width: 130px; font-size: 0.78rem; letter-spacing: 0.5px; text-transform: uppercase; padding-top: 2px; }}
.result-val {{ color: {TEXT}; }}
.tag {{ display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; background: {SURFACE_2}; border: 1px solid {BORDER}; color: {TEXT}; padding: 2px 9px; border-radius: 5px; margin: 2px 4px 2px 0; }}
.action-line {{ margin-top: 14px; padding: 10px 14px; border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; letter-spacing: 0.5px; }}
.tweet-preview {{ font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 7px; padding: 12px 14px; line-height: 1.6; margin-bottom: 4px; }}

section[data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
section[data-testid="stSidebar"] * {{ color: {TEXT}; }}
.sb-title {{ font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; letter-spacing: 1.5px; color: {TEXT_MUTED}; text-transform: uppercase; margin: 4px 0 10px 0; }}
.stat-line {{ display: flex; justify-content: space-between; align-items: center; padding: 7px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; border-bottom: 1px solid {BORDER}; }}
.stat-line:last-child {{ border-bottom: none; }}
.dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; margin-right: 8px; }}

.made-by-card {{ text-align: center; padding: 16px; background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 10px; margin-top: 18px; }}
.made-by-name {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.05rem; font-weight: 700; color: {AMBER}; letter-spacing: 0.5px; }}
.made-by-role {{ font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: {TEXT_MUTED}; letter-spacing: 1px; text-transform: uppercase; margin-top: 4px; }}

.stTextArea textarea {{ background: {SURFACE} !important; color: {TEXT} !important; border: 1px solid {BORDER} !important; border-radius: 8px !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.9rem !important; }}
.stTextArea textarea:focus {{ border-color: {AMBER} !important; box-shadow: 0 0 0 1px {AMBER} !important; }}
.stButton > button {{ background: {AMBER} !important; color: #1A1300 !important; border: none !important; border-radius: 7px !important; padding: 9px 20px !important; font-weight: 600 !important; font-family: 'Inter', sans-serif !important; letter-spacing: 0.2px; }}
.stButton > button:hover {{ filter: brightness(1.08); }}

.stTabs [data-baseweb="tab-list"] {{ gap: 4px; background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px; }}
.stTabs [data-baseweb="tab"] {{ font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: {TEXT_MUTED}; border-radius: 7px; padding: 8px 16px; }}
.stTabs [aria-selected="true"] {{ background: {SURFACE_2} !important; color: {AMBER} !important; }}

.hist-row {{ display: grid; grid-template-columns: 78px 90px 1fr 110px 60px; gap: 10px; align-items: center; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; padding: 9px 12px; background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 7px; margin-bottom: 6px; }}
.hist-badge {{ font-size: 0.68rem; padding: 2px 8px; border-radius: 4px; text-align: center; font-weight: 600; }}

.footer-bar {{ text-align: center; padding: 16px; margin-top: 28px; border-top: 1px solid {BORDER}; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: {TEXT_MUTED}; letter-spacing: 0.5px; }}
.stAlert {{ background: {SURFACE} !important; border: 1px solid {BORDER} !important; color: {TEXT} !important; }}
</style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown('<div class="sb-title">📊 Session Statistics</div>', unsafe_allow_html=True)
    stats_rows = [
        ("Total Scanned", st.session_state.stats['total'], TEXT_MUTED),
        ("Critical", st.session_state.stats['critical'], CRITICAL),
        ("High", st.session_state.stats['high'], HIGH),
        ("Medium", st.session_state.stats['medium'], MEDIUM),
        ("Safe", st.session_state.stats['safe'], SAFE),
    ]
    rows_html = "".join(
        f'<div class="stat-line"><span><span class="dot" style="background:{c};"></span>{l}</span>'
        f'<span style="color:{c}; font-weight:600;">{v}</span></div>'
        for l, v, c in stats_rows
    )
    st.markdown(f'<div style="background:{SURFACE_2}; border:1px solid {BORDER}; border-radius:10px; padding:10px 14px;">{rows_html}</div>', unsafe_allow_html=True)

    # Live threat gauge based on recent history
    st.markdown("---")
    st.markdown('<div class="sb-title">🌡️ Live Threat Level</div>', unsafe_allow_html=True)
    recent = st.session_state.history[:10]
    if recent:
        score = sum(SEVERITY_RANK.get(h['result'], 0) for h in recent) / (len(recent) * 3) * 100
    else:
        score = 0
    if score >= 60:
        threat_label, threat_color = "ELEVATED", CRITICAL
    elif score >= 30:
        threat_label, threat_color = "GUARDED", HIGH
    elif score > 0:
        threat_label, threat_color = "LOW", MEDIUM
    else:
        threat_label, threat_color = "NOMINAL", SAFE
    st.markdown(f"""
    <div style="background:{SURFACE_2}; border:1px solid {BORDER}; border-radius:10px; padding:12px 14px;">
        <div style="display:flex; justify-content:space-between; font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:{TEXT_MUTED}; margin-bottom:6px;">
            <span>Based on last {len(recent)} scans</span><span style="color:{threat_color}; font-weight:700;">{threat_label}</span>
        </div>
        <div style="background:{BG}; border-radius:6px; height:8px; overflow:hidden;">
            <div style="width:{score}%; background:{threat_color}; height:100%; border-radius:6px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="sb-title">📚 Keyword Bank</div>', unsafe_allow_html=True)
    with st.expander(f"View all {len(DISASTER_WORDS)} trigger terms"):
        by_cat = {}
        for term, (sev, cat) in DISASTER_WORDS.items():
            by_cat.setdefault(cat, []).append(term)
        for cat, terms in by_cat.items():
            st.markdown(f"**{cat}**")
            st.caption(", ".join(sorted(terms)))

    st.markdown(f"""
    <div class="made-by-card">
        <div style="font-size: 11px; color: {TEXT_MUTED}; letter-spacing:1px;">👩‍💻 BUILT BY</div>
        <div class="made-by-name">NIMRA IFTIKHAR</div>
        <div class="made-by-role">AI Project · Real-Time Disaster Detection</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# CONSOLE HEADER
# ============================================
st.markdown(f"""
<div class="console-bar">
    <div>
        <p class="console-title">🛰️ SENTINEL <span style="color:{TEXT_MUTED}; font-weight:500; font-size:1rem;">— Disaster Tweet Classifier</span></p>
        <p class="console-sub">AI-Powered Emergency Signal Detection · {len(DISASTER_WORDS)}-term engine</p>
    </div>
    <div class="status-pill"><span class="pulse-dot"></span>MONITORING</div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class="impact-card">
        <div class="impact-label">⚠️ The Problem</div>
        <div class="impact-text">During natural disasters, over <b>10,000 tweets</b> are posted per minute. Emergency services cannot read them all manually.</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="impact-card" style="border-left-color:{SAFE};">
        <div class="impact-label" style="color:{SAFE};">✅ The Solution</div>
        <div class="impact-text">This AI system instantly detects <b>real emergencies</b> across {len(DISASTER_WORDS)}+ terms and filters out fake or joke tweets.</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

tab1, tab2, tab3, tab4 = st.tabs(["📝  SINGLE TWEET", "📋  BATCH", "📊  ANALYTICS", "📜  HISTORY"])

# ============================================
# TAB 1: SINGLE TWEET
# ============================================
with tab1:
    tweet_input = st.text_area(
        "", placeholder="Example: 'Gas leak reported near downtown Karachi' or 'Shooting at the mall in Chicago'",
        height=100, label_visibility="collapsed", key="tweet_input_value"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        analyze_btn = st.button("🔍 Analyze Tweet", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)

    if clear_btn:
        st.session_state.tweet_input_value = ""
        st.rerun()

    if analyze_btn and tweet_input:
        with st.spinner("Scanning transmission..."):
            result = analyze_text(tweet_input)

        found = result['found']
        severity = result['severity']
        location = result['location']
        category = result['category']
        confidence = result['confidence']

        if found:
            key = severity.lower()
            st.session_state.stats[key] += 1
            st.session_state.all_keywords.extend(found)
            st.session_state.all_categories.append(category)
        else:
            st.session_state.stats['safe'] += 1

        if location:
            st.session_state.all_locations.append(location)
        st.session_state.stats['total'] += 1

        st.session_state.history.insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'tweet': tweet_input[:80],
            'result': severity if found else 'SAFE',
            'location': location or '—',
            'confidence': confidence,
            'category': category or 'Normal Conversation',
        })

        highlighted = highlight_text(tweet_input, found)
        st.markdown(f'<div class="tweet-preview">{highlighted}</div>', unsafe_allow_html=True)

        keyword_tags = "".join([f'<span class="tag">{k}</span>' for k in found]) if found else '—'

        if found:
            css_class = {"CRITICAL": "result-critical", "HIGH": "result-high", "MEDIUM": "result-medium"}[severity]
            color = SEVERITY_COLOR[severity]
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}[severity]
            action = {
                "CRITICAL": "CALL 911 IMMEDIATELY",
                "HIGH": "DISPATCH EMERGENCY SERVICES",
                "MEDIUM": "MONITOR THE SITUATION",
            }[severity]

            st.markdown(f"""
            <div class="result-card {css_class}">
                <div class="result-head" style="color:{color};">{icon} {severity} — DISASTER DETECTED</div>
                <div class="result-row"><span class="result-key">Category</span><span class="result-val">{category}</span></div>
                <div class="result-row"><span class="result-key">Keywords</span><span class="result-val">{keyword_tags}</span></div>
                <div class="result-row"><span class="result-key">Location</span><span class="result-val">{location if location else 'Unknown'}</span></div>
                <div class="result-row"><span class="result-key">Confidence</span><span class="result-val">{confidence}%</span></div>
                <div class="action-line" style="background:{color}22; color:{color}; border:1px solid {color}55;">🚨 ACTION → {action}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="result-card result-safe">
                <div class="result-head" style="color:{SAFE};">✅ SAFE — NO DISASTER</div>
                <div class="result-row"><span class="result-key">Category</span><span class="result-val">Normal Conversation</span></div>
                <div class="result-row"><span class="result-key">Confidence</span><span class="result-val">{confidence}%</span></div>
                <div class="action-line" style="background:{SAFE}1a; color:{SAFE}; border:1px solid {SAFE}55;">✅ No emergency response needed</div>
            </div>
            """, unsafe_allow_html=True)

# ============================================
# TAB 2: BATCH ANALYSIS
# ============================================
with tab2:
    batch_tweets = st.text_area(
        "", placeholder="Earthquake hits Tokyo\nGas leak reported in Lahore\nMy exam was a disaster\nShooting near downtown Chicago",
        height=180, label_visibility="collapsed"
    )

    if st.button("📊 Analyze All", type="primary"):
        if batch_tweets:
            lines = [l.strip() for l in batch_tweets.split('\n') if l.strip()][:30]
            batch_results = []
            for tweet in lines:
                r = analyze_text(tweet)
                batch_results.append({'tweet': tweet, **r})

            disaster_count = sum(1 for r in batch_results if r['found'])
            safe_count = len(batch_results) - disaster_count
            critical_count = sum(1 for r in batch_results if r['severity'] == 'CRITICAL')

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("⚠️ Disaster", disaster_count)
            m2.metric("🔴 Critical", critical_count)
            m3.metric("✅ Safe", safe_count)
            m4.metric("📝 Total", len(lines))

            st.write("")
            for r in batch_results:
                if r['found']:
                    color = SEVERITY_COLOR[r['severity']]
                    badge = f'<span class="hist-badge" style="background:{color}22; color:{color};">{r["severity"]}</span>'
                    loc = f' · 📍 {r["location"]}' if r['location'] else ''
                    keywords = ", ".join(r['found'][:4])
                    st.markdown(
                        f'<div class="hist-row" style="grid-template-columns: 110px 1fr 130px;">'
                        f'{badge}<span>{highlight_text(r["tweet"][:90], r["found"])}{loc}</span>'
                        f'<span style="color:{TEXT_MUTED}; font-size:0.72rem;">{keywords}</span></div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="hist-row" style="grid-template-columns: 110px 1fr 130px;">'
                        f'<span class="hist-badge" style="background:{SAFE}22; color:{SAFE};">SAFE</span>'
                        f'<span>{r["tweet"][:90]}</span><span></span></div>',
                        unsafe_allow_html=True
                    )

            # push batch results into global stats/history too, so Analytics & History stay consistent
            for r in batch_results:
                if r['found']:
                    st.session_state.stats[r['severity'].lower()] += 1
                    st.session_state.all_keywords.extend(r['found'])
                    st.session_state.all_categories.append(r['category'])
                else:
                    st.session_state.stats['safe'] += 1
                if r['location']:
                    st.session_state.all_locations.append(r['location'])
                st.session_state.stats['total'] += 1
                st.session_state.history.insert(0, {
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'tweet': r['tweet'][:80],
                    'result': r['severity'] if r['found'] else 'SAFE',
                    'location': r['location'] or '—',
                    'confidence': r['confidence'],
                    'category': r['category'] or 'Normal Conversation',
                })

            st.write("")
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(['Tweet', 'Result', 'Category', 'Location', 'Confidence', 'Keywords'])
            for r in batch_results:
                writer.writerow([r['tweet'], r['severity'] if r['found'] else 'SAFE', r['category'] or '—', r['location'] or '—', r['confidence'], ", ".join(r['found'])])
            st.download_button("📥 Download Batch Report (CSV)", out.getvalue(), "batch_report.csv", "text/csv")
        else:
            st.info("Paste one tweet per line, then click Analyze All.")

# ============================================
# TAB 3: ANALYTICS
# ============================================
with tab3:
    if st.session_state.stats['total'] > 0:
        mpl.rcParams['font.family'] = 'sans-serif'
        col1, col2 = st.columns(2)

        with col1:
            fig1, ax1 = plt.subplots(figsize=(5, 4))
            fig1.patch.set_facecolor(SURFACE)
            ax1.set_facecolor(SURFACE)
            labels, sizes, colors = [], [], []
            for lbl, key, c in [('Critical', 'critical', CRITICAL), ('High', 'high', HIGH), ('Medium', 'medium', MEDIUM), ('Safe', 'safe', SAFE)]:
                if st.session_state.stats[key] > 0:
                    labels.append(lbl); sizes.append(st.session_state.stats[key]); colors.append(c)
            if sizes:
                ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                        textprops={'color': TEXT, 'fontsize': 9}, wedgeprops={'edgecolor': SURFACE, 'linewidth': 2})
                ax1.set_title('Severity Distribution', color=TEXT, fontsize=12, fontweight='bold')
                st.pyplot(fig1)

        with col2:
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            fig2.patch.set_facecolor(SURFACE)
            ax2.set_facecolor(SURFACE)
            categories_x = ['Critical', 'High', 'Medium', 'Safe']
            values = [st.session_state.stats['critical'], st.session_state.stats['high'], st.session_state.stats['medium'], st.session_state.stats['safe']]
            bars = ax2.bar(categories_x, values, color=[CRITICAL, HIGH, MEDIUM, SAFE])
            ax2.set_title('Disaster Severity', color=TEXT, fontsize=12, fontweight='bold')
            for spine in ['top', 'right']:
                ax2.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']:
                ax2.spines[spine].set_color(BORDER)
            ax2.tick_params(colors=TEXT_MUTED)
            for bar, val in zip(bars, values):
                if val > 0:
                    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, str(val), ha='center', color=TEXT)
            st.pyplot(fig2)

        col3, col4, col5 = st.columns(3)
        with col3:
            if st.session_state.all_keywords:
                st.markdown("##### 🔑 Top Keywords")
                for kw, cnt in Counter(st.session_state.all_keywords).most_common(6):
                    st.markdown(f'<span class="tag">{kw} · {cnt}×</span>', unsafe_allow_html=True)
        with col4:
            if st.session_state.all_locations:
                st.markdown("##### 📍 Top Locations")
                for loc, cnt in Counter(st.session_state.all_locations).most_common(6):
                    st.markdown(f'<span class="tag">{loc} · {cnt}×</span>', unsafe_allow_html=True)
        with col5:
            if st.session_state.all_categories:
                st.markdown("##### 🗂️ Top Categories")
                for cat, cnt in Counter(st.session_state.all_categories).most_common(6):
                    st.markdown(f'<span class="tag">{cat} · {cnt}×</span>', unsafe_allow_html=True)

        disaster_count = st.session_state.stats['critical'] + st.session_state.stats['high'] + st.session_state.stats['medium']
        rate = int(disaster_count / st.session_state.stats['total'] * 100) if st.session_state.stats['total'] > 0 else 0
        st.write("")
        st.info(f"📈 Disaster Rate: **{rate}%** ({disaster_count}/{st.session_state.stats['total']}) · Keyword Engine Coverage: **{len(DISASTER_WORDS)} terms**")
    else:
        st.info("No data yet. Analyze some tweets to populate analytics.")

# ============================================
# TAB 4: HISTORY
# ============================================
with tab4:
    if st.session_state.history:
        filter_choice = st.selectbox("Filter by severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "SAFE"])
        rows = st.session_state.history if filter_choice == "All" else [h for h in st.session_state.history if h['result'] == filter_choice]

        if rows:
            for h in rows[:20]:
                color = SEVERITY_COLOR.get(h['result'], TEXT_MUTED)
                icon = '🔴' if h['result'] == 'CRITICAL' else '🟠' if h['result'] == 'HIGH' else '🟡' if h['result'] == 'MEDIUM' else '🟢'
                st.markdown(f"""
                <div class="hist-row">
                    <span style="color:{TEXT_MUTED};">{h['time']}</span>
                    <span class="hist-badge" style="background:{color}22; color:{color};">{icon} {h['result']}</span>
                    <span>{h['tweet']}</span>
                    <span style="color:{CYAN};">📍 {h['location']}</span>
                    <span style="color:{TEXT_MUTED};">{h['confidence']}%</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No entries with severity: {filter_choice}")

        st.write("")
        if st.button("📥 Export Full History (CSV)"):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Time', 'Tweet', 'Result', 'Category', 'Location', 'Confidence'])
            for h in st.session_state.history:
                writer.writerow([h['time'], h['tweet'], h['result'], h.get('category', '—'), h['location'], h['confidence']])
            st.download_button("Download", output.getvalue(), "report.csv", "text/csv")

        if st.button("🧹 Clear History", type="secondary"):
            st.session_state.history = []
            st.session_state.all_keywords = []
            st.session_state.all_locations = []
            st.session_state.all_categories = []
            st.session_state.stats = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'safe': 0}
            st.rerun()
    else:
        st.info("No history yet. Classified tweets will appear here.")

# ============================================
# FOOTER
# ============================================
st.markdown(f"""
<div class="footer-bar">
    BUILT BY NIMRA IFTIKHAR &nbsp;·&nbsp; AI PROJECT &nbsp;·&nbsp; REAL-TIME DISASTER DETECTION SYSTEM
</div>
""", unsafe_allow_html=True)
