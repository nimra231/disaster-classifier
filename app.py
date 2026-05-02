import streamlit as st
import pandas as pd
import csv
import io
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Disaster Tweet Classifier", page_icon="🚨", layout="wide")

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if 'primary_color' not in st.session_state:
    st.session_state.primary_color = "#667eea"
if 'secondary_color' not in st.session_state:
    st.session_state.secondary_color = "#764ba2"
if 'current_tweet' not in st.session_state:
    st.session_state.current_tweet = ""

# ============================================
# APPLY THEME
# ============================================
def apply_theme():
    primary = st.session_state.primary_color
    secondary = st.session_state.secondary_color
    
    st.markdown(f"""
    <style>
    .main {{ padding: 20px; }}
    
    .gradient-text {{
        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5em;
        font-weight: bold;
    }}
    
    .critical-box {{
        background: linear-gradient(135deg, #fef2f2, #fee2e2);
        border-left: 6px solid #dc3545;
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
    }}
    
    .high-box {{
        background: linear-gradient(135deg, #fff7ed, #ffedd5);
        border-left: 6px solid #fd7e14;
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
    }}
    
    .medium-box {{
        background: linear-gradient(135deg, #fffbeb, #fef3c7);
        border-left: 6px solid #ffc107;
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
    }}
    
    .safe-box {{
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border-left: 6px solid #28a745;
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, {primary}, {secondary}) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        transition: transform 0.2s !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
    }}
    
    .footer {{
        text-align: center;
        padding: 20px;
        margin-top: 30px;
        border-top: 1px solid #e0e0e0;
        font-size: 12px;
        color: #999;
    }}
    
    .made-by-card {{
        text-align: center;
        padding: 15px;
        background: linear-gradient(135deg, {primary}20, {secondary}20);
        border-radius: 12px;
        margin-top: 20px;
    }}
    
    .result-detail {{
        display: grid;
        grid-template-columns: 1fr 2fr;
        gap: 10px;
        margin: 10px 0;
    }}
    
    .result-label {{
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("### 🎨 Customize Theme")
    
    new_primary = st.color_picker("Primary Color", st.session_state.primary_color)
    new_secondary = st.color_picker("Secondary Color", st.session_state.secondary_color)
    
    if new_primary != st.session_state.primary_color:
        st.session_state.primary_color = new_primary
        st.rerun()
    if new_secondary != st.session_state.secondary_color:
        st.session_state.secondary_color = new_secondary
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Session Statistics")
    
    if 'stats' in st.session_state:
        total = st.session_state.stats.get('total', 0)
        critical = st.session_state.stats.get('critical', 0)
        high = st.session_state.stats.get('high', 0)
        medium = st.session_state.stats.get('medium', 0)
        safe = st.session_state.stats.get('safe', 0)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {st.session_state.primary_color}, {st.session_state.secondary_color}); padding: 15px; border-radius: 12px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span>📝 Total:</span>
                <span style="font-weight: bold; font-size: 20px;">{total}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span>🔴 Critical:</span>
                <span style="font-weight: bold;">{critical}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span>🟠 High:</span>
                <span style="font-weight: bold;">{high}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span>🟡 Medium:</span>
                <span style="font-weight: bold;">{medium}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span>🟢 Safe:</span>
                <span style="font-weight: bold;">{safe}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown(f"""
    <div class="made-by-card">
        <div style="font-size: 12px; color: #666;">👩‍💻 MADE BY</div>
        <div style="font-size: 18px; font-weight: bold; background: linear-gradient(135deg, {st.session_state.primary_color}, {st.session_state.secondary_color}); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">NIMRA IFTIKHAR</div>
        <div style="font-size: 11px; color: #888;">AI Project | Real-Time Disaster Detection</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# MAIN HEADER
# ============================================
st.markdown(f"""
<div style="text-align: center; margin-bottom: 20px;">
    <h1 class="gradient-text">🚨 Disaster Tweet Classifier</h1>
    <p style="color: #666;">AI-Powered Emergency Response | Real-time Disaster Detection</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# INITIALIZE DATA STORAGE
# ============================================
if 'history' not in st.session_state:
    st.session_state.history = []
if 'all_keywords' not in st.session_state:
    st.session_state.all_keywords = []
if 'all_locations' not in st.session_state:
    st.session_state.all_locations = []
if 'stats' not in st.session_state:
    st.session_state.stats = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'safe': 0}

# ============================================
# DISASTER DATABASE
# ============================================
DISASTER_WORDS = {
    'earthquake': 'HIGH', 'flood': 'HIGH', 'tsunami': 'CRITICAL',
    'hurricane': 'HIGH', 'tornado': 'HIGH', 'explosion': 'CRITICAL',
    'fire': 'MEDIUM', 'crash': 'MEDIUM', 'killed': 'CRITICAL',
    'death': 'CRITICAL', 'injured': 'HIGH', 'evacuation': 'HIGH',
    'rescue': 'MEDIUM', 'emergency': 'HIGH', 'warning': 'MEDIUM',
    'collapse': 'HIGH', 'attack': 'CRITICAL', 'landslide': 'HIGH',
    'wildfire': 'HIGH', 'cyclone': 'CRITICAL', 'blast': 'CRITICAL',
    'volcano': 'CRITICAL', 'drought': 'MEDIUM',
}

CITIES = [
    'Karachi', 'Lahore', 'Islamabad', 'New York', 'London', 'Tokyo',
    'California', 'Florida', 'Mumbai', 'Delhi', 'Pakistan', 'Japan',
    'Dubai', 'Paris', 'Berlin', 'Sydney', 'Toronto', 'Chicago'
]

def extract_location(tweet):
    for city in CITIES:
        if city.lower() in tweet.lower():
            return city
    return None

def get_disaster_type(keywords):
    if 'earthquake' in keywords: return '🌍 Earthquake'
    elif 'flood' in keywords: return '🌊 Flood'
    elif 'tsunami' in keywords: return '🌊 Tsunami'
    elif 'fire' in keywords: return '🔥 Fire'
    elif 'explosion' in keywords: return '💥 Explosion'
    else: return '⚠️ Emergency'

def analyze_and_display(tweet):
    """Analyze tweet and return result HTML"""
    if not tweet or not tweet.strip():
        return None, None, None, None, None, None
    
    tweet_lower = tweet.lower()
    found = []
    severity = None
    
    for word, level in DISASTER_WORDS.items():
        if word in tweet_lower:
            found.append(word)
            if severity is None:
                severity = level
            elif level == 'CRITICAL':
                severity = 'CRITICAL'
    
    location = extract_location(tweet)
    confidence = min(95, len(found) * 20 + 50) if found else 92
    disaster_type = get_disaster_type(found) if found else 'Normal Conversation'
    
    return found, severity, location, confidence, disaster_type, tweet

# ============================================
# MAIN CONTENT - Single Tweet with Auto Analysis
# ============================================
st.markdown("### 📝 Enter Tweet")

tweet_input = st.text_area(
    "",
    placeholder="Type a tweet here... Example: 'Fire in Lahore' or 'Earthquake in Tokyo'",
    height=100,
    label_visibility="collapsed",
    key="tweet_input"
)

# Clear button
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.current_tweet = ""
        st.rerun()

st.markdown("---")

# ============================================
# AUTO ANALYSIS - Result shows immediately as you type
# ============================================
if tweet_input:
    found, severity, location, confidence, disaster_type, tweet = analyze_and_display(tweet_input)
    
    # Update stats only once per unique tweet
    # (This happens when analyzing)
    
    if found:
        if severity == 'CRITICAL':
            st.markdown(f"""
            <div class="critical-box">
                <h2 style="color: #dc3545; margin: 0;">🔴🔴🔴 CRITICAL ALERT - DISASTER DETECTED!</h2>
                <hr>
                <div class="result-detail">
                    <div class="result-label">📌 Disaster Type:</div><div>{disaster_type}</div>
                    <div class="result-label">🔍 Keywords:</div><div>{', '.join(found)}</div>
                    <div class="result-label">📍 Location:</div><div><span style="background: #dc3545; color: white; padding: 2px 12px; border-radius: 20px;">{location if location else 'Unknown'}</span></div>
                    <div class="result-label">🎯 Confidence:</div><div><span style="font-size: 22px; font-weight: bold; color: #dc3545;">{confidence}%</span></div>
                    <div class="result-label">🚨 Action:</div><div><strong>CALL EMERGENCY SERVICES IMMEDIATELY!</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif severity == 'HIGH':
            st.markdown(f"""
            <div class="high-box">
                <h2 style="color: #fd7e14; margin: 0;">🟠🟠 HIGH ALERT - DISASTER DETECTED!</h2>
                <hr>
                <div class="result-detail">
                    <div class="result-label">📌 Disaster Type:</div><div>{disaster_type}</div>
                    <div class="result-label">🔍 Keywords:</div><div>{', '.join(found)}</div>
                    <div class="result-label">📍 Location:</div><div><span style="background: #fd7e14; color: white; padding: 2px 12px; border-radius: 20px;">{location if location else 'Unknown'}</span></div>
                    <div class="result-label">🎯 Confidence:</div><div><span style="font-size: 22px; font-weight: bold; color: #fd7e14;">{confidence}%</span></div>
                    <div class="result-label">📢 Action:</div><div><strong>DISPATCH EMERGENCY SERVICES!</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif severity == 'MEDIUM':
            st.markdown(f"""
            <div class="medium-box">
                <h2 style="color: #e65100; margin: 0;">🟡 MEDIUM ALERT - DISASTER DETECTED!</h2>
                <hr>
                <div class="result-detail">
                    <div class="result-label">📌 Disaster Type:</div><div>{disaster_type}</div>
                    <div class="result-label">🔍 Keywords:</div><div>{', '.join(found)}</div>
                    <div class="result-label">📍 Location:</div><div><span style="background: #e65100; color: white; padding: 2px 12px; border-radius: 20px;">{location if location else 'Unknown'}</span></div>
                    <div class="result-label">🎯 Confidence:</div><div><span style="font-size: 22px; font-weight: bold; color: #e65100;">{confidence}%</span></div>
                    <div class="result-label">👀 Action:</div><div><strong>MONITOR THE SITUATION</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="safe-box">
            <h2 style="color: #28a745; margin: 0;">✅ SAFE - NO DISASTER DETECTED</h2>
            <hr>
            <div class="result-detail">
                <div class="result-label">📌 Classification:</div><div>Normal Conversation</div>
                <div class="result-label">🎯 Confidence:</div><div><span style="font-size: 22px; font-weight: bold; color: #28a745;">{confidence}%</span></div>
                <div class="result-label">✅ Action:</div><div>No emergency response needed.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick stats row
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📝 Total", st.session_state.stats['total'])
    with col2:
        st.metric("🔴 Critical", st.session_state.stats['critical'])
    with col3:
        st.metric("🟠 High", st.session_state.stats['high'])
    with col4:
        st.metric("🟡 Medium", st.session_state.stats['medium'])
    with col5:
        st.metric("🟢 Safe", st.session_state.stats['safe'])

else:
    st.info("💡 Type a tweet above to analyze it instantly!")

# ============================================
# EXAMPLES SECTION
# ============================================
st.markdown("---")
st.markdown("### 💡 Try these examples:")

ex_col1, ex_col2, ex_col3 = st.columns(3)

def set_example(tweet_text):
    st.session_state.tweet_input = tweet_text
    st.rerun()

with ex_col1:
    if st.button("🌍 Earthquake in Tokyo", use_container_width=True):
        set_example("Earthquake in Tokyo! Buildings shaking, evacuations underway.")
    if st.button("🌊 Tsunami warning Japan", use_container_width=True):
        set_example("Tsunami warning issued for Japan coastline.")

with ex_col2:
    if st.button("🔥 Fire in Lahore", use_container_width=True):
        set_example("Fire in Lahore! People evacuating from building.")
    if st.button("💥 Explosion reported", use_container_width=True):
        set_example("Massive explosion at chemical plant, multiple casualties.")

with ex_col3:
    if st.button("📚 My exam disaster", use_container_width=True):
        set_example("My exam was a complete disaster.")
    if st.button("☀️ Beautiful day at beach", use_container_width=True):
        set_example("Beautiful sunny day at the beach.")

# ============================================
# BATCH ANALYSIS TAB (Keep existing functionality)
# ============================================
with st.expander("📋 Batch Analysis (Optional)"):
    st.markdown("Paste multiple tweets (one per line) to analyze them all at once.")
    batch_tweets = st.text_area("", placeholder="Earthquake in Tokyo\nFlood in Pakistan\nMy exam was a disaster", height=150, key="batch_input")
    
    if st.button("📊 Analyze All Tweets", type="primary"):
        if batch_tweets:
            lines = [l.strip() for l in batch_tweets.split('\n') if l.strip()][:20]
            disaster_count = 0
            safe_count = 0
            results = []
            
            for tweet in lines:
                found = any(word in tweet.lower() for word in DISASTER_WORDS)
                if found:
                    disaster_count += 1
                    results.append(f"⚠️ DISASTER: {tweet[:60]}")
                else:
                    safe_count += 1
                    results.append(f"✅ SAFE: {tweet[:60]}")
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {st.session_state.primary_color}, {st.session_state.secondary_color}); padding: 15px; border-radius: 10px; color: white;">
                <strong>Batch Summary</strong><br>
                🔴 DISASTER: {disaster_count} | 🟢 SAFE: {safe_count} | Total: {len(lines)}
            </div>
            """, unsafe_allow_html=True)
            
            for r in results:
                st.write(r)

# ============================================
# HISTORY & ANALYTICS (Tabs)
# ============================================
tab_analytics, tab_history = st.tabs(["📊 Analytics Dashboard", "📋 History"])

with tab_analytics:
    if st.session_state.stats['total'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            fig1, ax1 = plt.subplots(figsize=(5, 4))
            labels = []
            sizes = []
            colors = []
            
            if st.session_state.stats['critical'] > 0:
                labels.append('Critical'); sizes.append(st.session_state.stats['critical']); colors.append('#dc3545')
            if st.session_state.stats['high'] > 0:
                labels.append('High'); sizes.append(st.session_state.stats['high']); colors.append('#fd7e14')
            if st.session_state.stats['medium'] > 0:
                labels.append('Medium'); sizes.append(st.session_state.stats['medium']); colors.append('#ffc107')
            if st.session_state.stats['safe'] > 0:
                labels.append('Safe'); sizes.append(st.session_state.stats['safe']); colors.append('#28a745')
            
            if sizes:
                ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
                ax1.set_title('Severity Distribution', fontweight='bold')
                st.pyplot(fig1)
        
        with col2:
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            categories = ['Critical', 'High', 'Medium', 'Safe']
            values = [st.session_state.stats['critical'], st.session_state.stats['high'], 
                     st.session_state.stats['medium'], st.session_state.stats['safe']]
            bar_colors = ['#dc3545', '#fd7e14', '#ffc107', '#28a745']
            bars = ax2.bar(categories, values, color=bar_colors)
            ax2.set_title('Disaster Severity Analysis', fontweight='bold')
            ax2.set_ylabel('Count')
            for bar, val in zip(bars, values):
                if val > 0:
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, str(val), ha='center')
            st.pyplot(fig2)
        
        if st.session_state.all_keywords:
            st.markdown("### 🔑 Top Keywords")
            kw_counter = Counter(st.session_state.all_keywords)
            for kw, cnt in kw_counter.most_common(5):
                st.write(f"- {kw}: {cnt} times")
        
        if st.session_state.all_locations:
            st.markdown("### 📍 Top Locations")
            loc_counter = Counter(st.session_state.all_locations)
            for loc, cnt in loc_counter.most_common(5):
                st.write(f"- {loc}: {cnt} times")
    else:
        st.info("No data yet. Analyze some tweets above!")

with tab_history:
    if st.session_state.history:
        for h in st.session_state.history[:10]:
            icon = '🔴' if h['result'] == 'CRITICAL' else '🟠' if h['result'] == 'HIGH' else '🟡' if h['result'] == 'MEDIUM' else '🟢'
            st.write(f"{icon} **{h['time']}** | {h['result']} | {h['tweet']} | 📍 {h['location']} | {h['confidence']}%")
        
        if st.button("📥 Export to CSV"):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Time', 'Tweet', 'Result', 'Location', 'Confidence'])
            for h in st.session_state.history:
                writer.writerow([h['time'], h['tweet'], h['result'], h['location'], h['confidence']])
            st.download_button("Download CSV", output.getvalue(), "disaster_report.csv", "text/csv")
    else:
        st.info("No history yet")

# ============================================
# FOOTER
# ============================================
st.markdown(f"""
<div class="footer">
    <p><strong>MADE BY: NIMRA IFTIKHAR</strong> | AI Project | Real-Time Disaster Detection System</p>
</div>
""", unsafe_allow_html=True)
