import gradio as gr

# Disaster keywords with severity levels
DISASTER_WORDS = {
    'earthquake': 'HIGH',
    'flood': 'HIGH',
    'tsunami': 'CRITICAL',
    'hurricane': 'HIGH',
    'tornado': 'HIGH',
    'explosion': 'CRITICAL',
    'fire': 'MEDIUM',
    'crash': 'MEDIUM',
    'killed': 'CRITICAL',
    'death': 'CRITICAL',
    'injured': 'HIGH',
    'evacuation': 'HIGH',
    'rescue': 'MEDIUM',
    'emergency': 'HIGH',
    'warning': 'MEDIUM',
    'collapse': 'HIGH',
}

def detect_disaster(tweet):
    tweet_lower = tweet.lower()
    
    # Find disaster words
    found_words = []
    severity = None
    
    for word, level in DISASTER_WORDS.items():
        if word in tweet_lower:
            found_words.append(word)
            if severity is None or level == 'CRITICAL':
                severity = level
    
    if found_words:
        if severity == 'CRITICAL':
            emoji = "🔴🔴🔴"
            action = "⚠️ IMMEDIATE RESPONSE NEEDED - Call 911!"
        elif severity == 'HIGH':
            emoji = "🔴🔴"
            action = "🚨 Dispatch emergency services immediately!"
        else:
            emoji = "🟡"
            action = "📋 Monitor situation, prepare response team"
        
        result = f"""
### {emoji} REAL DISASTER DETECTED {emoji}

**Severity:** {severity}
**Keywords found:** {', '.join(found_words)}
**Action Required:** {action}
"""
    else:
        result = """
### ✅ NOT A DISASTER

This tweet appears to be normal conversation or metaphorical language.

**No emergency response needed.**
"""
    
    return result

# Create the web app
with gr.Blocks(title="Disaster Tweet Classifier") as demo:
    gr.Markdown("# 🚨 Disaster Tweet Classifier - Emergency Response System")
    gr.Markdown("""
    ### 🎯 PURPOSE:
    This AI helps emergency services detect REAL disasters from social media noise.
    
    **Who Benefits:**
    - 🚒 Firefighters - Find fire/explosion reports
    - 🚑 EMS - Locate injured people
    - 📰 News - Verify breaking news
    - 🏛️ Government - Coordinate rescue
    """)
    
    gr.Markdown("### 📝 Enter a tweet to analyze:")
    tweet_input = gr.Textbox(label="Tweet", placeholder="Example: Earthquake in Tokyo", lines=3)
    output = gr.Markdown(label="Analysis Result")
    submit_btn = gr.Button("🔍 Analyze Tweet", variant="primary")
    
    submit_btn.click(fn=detect_disaster, inputs=tweet_input, outputs=output)
    
    gr.Markdown("""
    ---
    ### 💡 Try these examples:
    - "Earthquake in Tokyo"
    - "My exam was a disaster"  
    - "Building collapsed with people trapped"
    - "today is saturday"
    - "Fire at apartment building in Karachi"
    """)

# IMPORTANT: This is required for Railway to work
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
