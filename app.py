import streamlit as st
import pandas as pd
import csv
import io
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="Disaster Tweet Classifier", page_icon="🚨")

# Disaster keywords
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

CITIES = ['Karachi', 'Lahore', 'Islamabad', 'New York', 'London', 'Tokyo']

st.title("🚨 Disaster Tweet Classifier")
st.markdown("*AI-Powered Emergency Response | Real-time Disaster Detection*")

# Sidebar for stats
st.sidebar.header("📊 Session Statistics")

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'total' not in st.session_state:
    st.session_state.total = 0
    st.session_state.critical = 0
    st.session_state.high = 0
    st.session_state.medium = 0
    st.session_state.safe = 0

def extract_location(tweet):
    for city in CITIES:
        if city.lower() in tweet.lower():
            return city
    return None

# Main input
tweet = st.text_area("Enter Tweet", placeholder="Example: Earthquake in Tokyo...", height=100)

col1, col2 = st.columns(2)
with col1:
    analyze = st.button("🔍 Analyze", type="primary")
with col2:
    clear = st.button("🗑️ Clear")

if analyze and tweet:
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
    confidence = min(95, len(found) * 20 + 50) if found else 90
    
    # Update stats
    if found:
        if severity == 'CRITICAL':
            st.session_state.critical += 1
        elif severity == 'HIGH':
            st.session_state.high += 1
        else:
            st.session_state.medium += 1
    else:
        st.session_state.safe += 1
    st.session_state.total += 1
    
    # Save to history
    st.session_state.history.insert(0, {
        'time': datetime.now().strftime('%H:%M:%S'),
        'tweet': tweet[:50],
        'result': severity if found else 'SAFE',
        'location': location or '—',
        'confidence': confidence,
    })
    
    # Display result
    if found:
        if severity == 'CRITICAL':
            st.error(f"🔴 CRITICAL ALERT - DISASTER DETECTED!\n\nKeywords: {', '.join(found)}\nLocation: {location or 'Unknown'}\nConfidence: {confidence}%\nAction: CALL EMERGENCY SERVICES!")
        elif severity == 'HIGH':
            st.warning(f"🟠 HIGH ALERT - DISASTER DETECTED!\n\nKeywords: {', '.join(found)}\nLocation: {location or 'Unknown'}\nConfidence: {confidence}%\nAction: DISPATCH EMERGENCY SERVICES!")
        else:
            st.info(f"🟡 MEDIUM ALERT - DISASTER DETECTED!\n\nKeywords: {', '.join(found)}\nLocation: {location or 'Unknown'}\nConfidence: {confidence}%\nAction: MONITOR THE SITUATION")
    else:
        st.success(f"✅ SAFE - NO DISASTER DETECTED\n\nConfidence: {confidence}%\nNo emergency response needed.")

elif clear:
    st.rerun()

# Display stats in sidebar
st.sidebar.metric("Total Analyses", st.session_state.total)
st.sidebar.metric("🔴 Critical", st.session_state.critical)
st.sidebar.metric("🟠 High", st.session_state.high)
st.sidebar.metric("🟡 Medium", st.session_state.medium)
st.sidebar.metric("🟢 Safe", st.session_state.safe)

# History
st.subheader("📋 Recent History")
if st.session_state.history:
    for h in st.session_state.history[:10]:
        icon = '🔴' if h['result'] == 'CRITICAL' else '🟠' if h['result'] == 'HIGH' else '🟡' if h['result'] == 'MEDIUM' else '🟢'
        st.text(f"{icon} {h['time']} | {h['result']} | {h['tweet']} | {h['location']} | {h['confidence']}%")
else:
    st.info("No analyses yet")

st.markdown("---")
st.markdown("*Created by NIMRA IFTIKHAR | 4th Semester AI Project*")
