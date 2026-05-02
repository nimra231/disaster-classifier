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
if 'history' not in st.session_state:
    st.session_state.history = []
if 'all_keywords' not in st.session_state:
    st.session_state.all_keywords = []
if 'all_locations' not in st.session_state:
    st.session_state.all_locations = []
if 'stats' not in st.session_state:
    st.session_state.stats = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'safe': 0}
if 'last_tweet' not in st.session_state:
    st.session_state.last_tweet = ""

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
        margin: 15px 0;
    }}
    
    .high-box {{
        background: linear-gradient(135deg, #fff7ed, #ffedd5);
        border-left: 6px solid #fd7e14;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
    }}
    
    .medium-box {{
        background: linear-gradient(135deg, #fffbeb, #fef3c7);
        border-left: 6px solid #ffc107;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
    }}
    
    .safe-box {{
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border-left: 6px solid #28a745;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, {primary}, {secondary}) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
    }}
    
    .footer {{
        text-align: center;
        padding: 15px;
        margin-top: 20px;
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
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {st.session_state.primary_color}, {st.session_state.secondary_color}); padding: 15px; border-radius: 12px;">
        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
            <span>📝 Total:</span>
            <span style="font-weight: bold; font-size: 20px;">{st.session_state.stats['total']}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
            <span>🔴 Critical:</span>
            <span style="font-weight: bold;">{st.session_state.stats['critical']}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
            <span>🟠 High:</span>
            <span style="font-weight: bold;">{st.session_state.stats['high']}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
            <span>🟡 Medium:</span>
            <span style="font-weight: bold;">{st.session_state.stats['medium']}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
            <span>🟢 Safe:</span>
            <span style="font-weight: bold;">{st.session_state.stats['safe']}</span>
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

CITIES = ['Karachi', 'Lahore', 'Islamabad', 'New York', 'London', 'Tokyo', 'Dubai', 'Paris', 'Berlin', 'Sydney']

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

# ============================================
# TWEET INPUT - MAIN FEATURE
# ============================================
st.markdown("### 📝 Enter Tweet")
tweet_input = st.text_area(
    "",
    placeholder="Type a tweet here... Example: 'Fire in Lahore' or 'Earthquake in Tokyo'",
    height=100,
    label_visibility="collapsed",
    key="tweet_input"
)

# ============================================
# ANALYZE AND DISPLAY RESULT
# ============================================
if tweet_input and tweet_input != st.session_state.last_tweet:
    st.session_state.last_tweet = tweet_input
    
    tweet_lower = tweet_input.lower()
    found = []
    severity = None
    
    for word, level in DISASTER_WORDS.items():
        if word in tweet_lower:
            found.append(word)
            if severity is None:
                severity = level
            elif level == 'CRITICAL':
                severity = 'CRITICAL'
    
    location = extract_location(tweet_input)
    confidence = min(95, len(found) * 20 + 50) if found else 92
    disaster_type = get_disaster_type(found) if found else 'Normal Conversation'
    
    # Update stats
    if found:
        if severity == 'CRITICAL':
            st.session_state.stats['critical'] += 1
        elif severity == 'HIGH':
            st.session_state.stats['high'] += 1
        else:
            st.session_state.stats['medium'] += 1
        st.session_state.all_keywords.extend(found)
    else:
        st.session_state.stats['safe'] += 1
    
    if location:
        st.session_state.all_locations.append(location)
    st.session_state.stats['total'] += 1
    
    # Save to history
    st.session_state.history.insert(0, {
        'time': datetime.now().strftime('%H:%M:%S'),
        'tweet': tweet_input[:50],
        'result': severity if found else 'SAFE',
        'location': location or '—',
        'confidence': confidence,
    })
    
    # Display result
    if found:
        if severity == 'CRITICAL':
            st.markdown(f"""
            <div class="critical-box">
                <h2 style="color: #dc3545; margin: 0;">🔴🔴🔴 CRITICAL ALERT - DISASTER DETECTED!</h2>
                <hr>
                <p><strong>📌 Disaster Type:</strong> {disaster_type}</p>
                <p><strong>🔍 Keywords Detected:</strong> {', '.join(found)}</p>
                <p><strong>📍 Location:</strong> <span style="background: #dc3545; color: white; padding: 2px 10px; border-radius: 15px;">{location if location else 'Unknown'}</span></p>
                <p><strong>🎯 Confidence:</strong> <span style="font-size: 24px; font-weight: bold;">{confidence}%</span></p>
                <p><strong>🚨 Action:</strong> CALL EMERGENCY SERVICES IMMEDIATELY!</p>
            </div>
            """, unsafe_allow_html=True)
        elif severity == 'HIGH':
            st.markdown(f"""
            <div class="high-box">
                <h2 style="color: #fd7e14; margin: 0;">🟠🟠 HIGH ALERT - DISASTER DETECTED!</h2>
                <hr>
                <p><strong>📌 Disaster Type:</strong> {disaster_type}</p>
                <p><strong>🔍 Keywords Detected:</strong> {', '.join(found)}</p>
                <p><strong>📍 Location:</strong> <span style="background: #fd7e14; color: white; padding: 2px 10px; border-radius: 15px;">{location if location else 'Unknown'}</span></p>
                <p><strong>🎯 Confidence:</strong> <span style="font-size: 24px; font-weight: bold;">{confidence}%</span></p>
                <p><strong>📢 Action:</strong> DISPATCH EMERGENCY SERVICES!</p>
            </div>
            """, unsafe_allow_html=True)
        elif severity == 'MEDIUM':
            st.markdown(f"""
            <div class="medium-box">
                <h2 style="color: #e65100; margin: 0;">🟡 MEDIUM ALERT - DISASTER DETECTED!</h2>
                <hr>
                <p><strong>📌 Disaster Type:</strong> {disaster_type}</p>
                <p><strong>🔍 Keywords Detected:</strong> {', '.join(found)}</p>
                <p><strong>📍 Location:</strong> <span style="background: #e65100; color: white; padding: 2px 10px; border-radius: 15px;">{location if location else 'Unknown'}</span></p>
                <p><strong>🎯 Confidence:</strong> <span style="font-size: 24px; font-weight: bold;">{confidence}%</span></p>
                <p><strong>👀 Action:</strong> MONITOR THE SITUATION</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="safe-box">
            <h2 style="color: #28a745; margin: 0;">✅ SAFE - NO DISASTER DETECTED</h2>
            <hr>
            <p><strong>📌 Classification:</strong> Normal Conversation</p>
            <p><strong>🎯 Confidence:</strong> <span style="font-size: 24px; font-weight: bold; color: #28a745;">{confidence}%</span></p>
            <p><strong>✅ Action:</strong> No emergency response needed.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.rerun()

# ============================================
# ANALYTICS & HISTORY SECTION (Always visible)
# ============================================
st.markdown("---")
st.markdown("### 📊 Analytics Dashboard")

col1, col2 = st.columns(2)

with col1:
    if st.session_state.stats['total'] > 0:
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
    else:
        st.info("No data yet. Enter a tweet above.")

with col2:
    if st.session_state.stats['total'] > 0:
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
    else:
        st.info("No data yet. Enter a tweet above.")

# Top Keywords and Locations
if st.session_state.stats['total'] > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.all_keywords:
            st.markdown("### 🔑 Top Keywords")
            kw_counter = Counter(st.session_state.all_keywords)
            for kw, cnt in kw_counter.most_common(5):
                st.write(f"- **{kw}**: {cnt} times")
    
    with col2:
        if st.session_state.all_locations:
            st.markdown("### 📍 Top Locations")
            loc_counter = Counter(st.session_state.all_locations)
            for loc, cnt in loc_counter.most_common(5):
                st.write(f"- **{loc}**: {cnt} times")

# History Section
st.markdown("---")
st.markdown("### 📋 Recent History")

if st.session_state.history:
    for h in st.session_state.history[:10]:
        icon = '🔴' if h['result'] == 'CRITICAL' else '🟠' if h['result'] == 'HIGH' else '🟡' if h['result'] == 'MEDIUM' else '🟢'
        st.write(f"{icon} **{h['time']}** | {h['result']} | {h['tweet']} | 📍 {h['location']} | {h['confidence']}%")
    
    # Export button
    if st.button("📥 Export History to CSV"):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Time', 'Tweet', 'Result', 'Location', 'Confidence'])
        for h in st.session_state.history:
            writer.writerow([h['time'], h['tweet'], h['result'], h['location'], h['confidence']])
        st.download_button("Download CSV", output.getvalue(), "disaster_report.csv", "text/csv")
else:
    st.info("No history yet. Enter a tweet above to start.")

# ============================================
# FOOTER
# ============================================
st.markdown(f"""
<div class="footer">
    <p><strong>MADE BY: NIMRA IFTIKHAR</strong> | AI Project | Real-Time Disaster Detection System</p>
</div>
""", unsafe_allow_html=True)
