import gradio as gr
from datetime import datetime
import json
import os

# Disaster keywords with severity levels and categories
DISASTER_DATABASE = {
    'natural_disasters': {
        'earthquake': {'severity': 'CRITICAL', 'emoji': '🌍', 'description': 'Seismic Activity'},
        'flood': {'severity': 'HIGH', 'emoji': '🌊', 'description': 'Water Emergency'},
        'tsunami': {'severity': 'CRITICAL', 'emoji': '🌊', 'description': 'Tidal Wave'},
        'hurricane': {'severity': 'HIGH', 'emoji': '🌪️', 'description': 'Tropical Storm'},
        'tornado': {'severity': 'HIGH', 'emoji': '🌪️', 'description': 'Rotating Storm'},
        'landslide': {'severity': 'HIGH', 'emoji': '⛰️', 'description': 'Ground Movement'},
        'volcano': {'severity': 'CRITICAL', 'emoji': '🌋', 'description': 'Volcanic Activity'},
        'avalanche': {'severity': 'HIGH', 'emoji': '⛷️', 'description': 'Snow Slide'},
    },
    'accidents': {
        'crash': {'severity': 'HIGH', 'emoji': '🚗', 'description': 'Vehicle Collision'},
        'collision': {'severity': 'HIGH', 'emoji': '🚗', 'description': 'Crash'},
        'explosion': {'severity': 'CRITICAL', 'emoji': '💥', 'description': 'Blast'},
        'fire': {'severity': 'MEDIUM', 'emoji': '🔥', 'description': 'Uncontrolled Fire'},
        'collapse': {'severity': 'HIGH', 'emoji': '🏢', 'description': 'Structure Failure'},
    },
    'injuries': {
        'killed': {'severity': 'CRITICAL', 'emoji': '⚠️', 'description': 'Fatalities'},
        'death': {'severity': 'CRITICAL', 'emoji': '⚠️', 'description': 'Fatalities'},
        'injured': {'severity': 'HIGH', 'emoji': '🚑', 'description': 'Casualties'},
        'casualty': {'severity': 'HIGH', 'emoji': '🚑', 'description': 'Injured Person'},
        'trapped': {'severity': 'CRITICAL', 'emoji': '🆘', 'description': 'People in Danger'},
    },
    'emergency': {
        'evacuation': {'severity': 'HIGH', 'emoji': '🚨', 'description': 'Emergency Evacuation'},
        'rescue': {'severity': 'MEDIUM', 'emoji': '🆘', 'description': 'Rescue Operation'},
        'emergency': {'severity': 'HIGH', 'emoji': '🚨', 'description': 'Emergency Alert'},
        'warning': {'severity': 'MEDIUM', 'emoji': '⚠️', 'description': 'Alert Warning'},
        'alert': {'severity': 'MEDIUM', 'emoji': '⚠️', 'description': 'Emergency Alert'},
    }
}

# Flatten for easier access
DISASTER_WORDS = {}
for category, words in DISASTER_DATABASE.items():
    for word, details in words.items():
        DISASTER_WORDS[word] = details

# History file
HISTORY_FILE = 'detection_history.json'

def load_history():
    """Load detection history from file"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    """Save detection history to file"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def detect_disaster(tweet):
    """Analyze tweet for disaster keywords"""
    tweet_lower = tweet.lower().strip()
    
    if not tweet:
        return "⚠️ **Please enter a tweet to analyze!**", "", "No Input"
    
    # Find disaster words with categories
    found_disasters = {}
    max_severity = None
    severity_order = {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1}
    
    for word, details in DISASTER_WORDS.items():
        if word in tweet_lower:
            category = None
            for cat, words in DISASTER_DATABASE.items():
                if word in words:
                    category = cat
                    break
            
            found_disasters[word] = {
                'details': details,
                'category': category
            }
            
            # Update max severity
            current_level = details['severity']
            if max_severity is None or severity_order.get(current_level, 0) > severity_order.get(max_severity, 0):
                max_severity = current_level
    
    # Generate response
    if found_disasters:
        if max_severity == 'CRITICAL':
            emoji_display = "🔴🔴🔴"
            action = "⚠️ **IMMEDIATE RESPONSE NEEDED** - Contact emergency services (911)"
            color_code = "danger"
        elif max_severity == 'HIGH':
            emoji_display = "🔴🔴"
            action = "🚨 **Dispatch emergency services immediately!**"
            color_code = "warning"
        else:
            emoji_display = "🟡"
            action = "📋 **Monitor situation, prepare response team**"
            color_code = "info"
        
        # Build detailed report
        keywords_list = "\n".join([
            f"  - **{word}** ({details['details']['description']}) - Severity: {details['details']['severity']}"
            for word, details in found_disasters.items()
        ])
        
        result = f"""
### {emoji_display} REAL DISASTER DETECTED {emoji_display}

**🎯 Severity Level:** `{max_severity}`

**📍 Keywords Detected:**
{keywords_list}

**🚨 Required Action:**
{action}

**📊 Confidence Score:** {min(100, len(found_disasters) * 25)}%
"""
        status = "DISASTER ALERT"
        
    else:
        result = """
### ✅ NOT A DISASTER

This tweet appears to be normal conversation or metaphorical language.

**🟢 No emergency response needed.**

**Confidence Score:** 0%
"""
        status = "SAFE"
    
    # Save to history
    history = load_history()
    history.insert(0, {
        'timestamp': datetime.now().isoformat(),
        'tweet': tweet,
        'status': status,
        'severity': max_severity or 'NONE',
        'keywords_found': list(found_disasters.keys())
    })
    # Keep only last 50 entries
    history = history[:50]
    save_history(history)
    
    # Create category breakdown
    category_breakdown = ""
    if found_disasters:
        categories_found = {}
        for word, details in found_disasters.items():
            cat = details['category']
            if cat not in categories_found:
                categories_found[cat] = []
            categories_found[cat].append(word)
        
        category_breakdown = "**Categories Detected:**\n"
        for cat, words in categories_found.items():
            emoji = '🌍' if 'natural' in cat else '🚗' if 'accident' in cat else '🚑' if 'injury' in cat else '🚨'
            category_breakdown += f"{emoji} {cat.replace('_', ' ').title()}: {', '.join(words)}\n"
    
    return result, category_breakdown, status

def get_statistics():
    """Get statistics from history"""
    history = load_history()
    
    if not history:
        return "📊 **No detection history yet!** Start analyzing tweets to build statistics."
    
    total_detections = len(history)
    disasters = sum(1 for h in history if h['status'] == 'DISASTER ALERT')
    safe = total_detections - disasters
    critical = sum(1 for h in history if h['severity'] == 'CRITICAL')
    high = sum(1 for h in history if h['severity'] == 'HIGH')
    medium = sum(1 for h in history if h['severity'] == 'MEDIUM')
    
    stats = f"""
### 📊 Detection Statistics

**Overall Summary:**
- 📈 Total Analyzed: `{total_detections}`
- 🔴 Disasters Detected: `{disasters}` ({disasters*100//total_detections}%)
- ✅ Safe Tweets: `{safe}` ({safe*100//total_detections}%)

**Severity Breakdown:**
- 🔴🔴🔴 Critical: `{critical}`
- 🔴🔴 High: `{high}`
- 🟡 Medium: `{medium}`

**Most Recent Alerts:**
"""
    
    # Show last 5 disasters
    recent_disasters = [h for h in history if h['status'] == 'DISASTER ALERT'][:5]
    if recent_disasters:
        for i, alert in enumerate(recent_disasters, 1):
            time = alert['timestamp'].split('T')[1][:5]
            keywords = ', '.join(alert['keywords_found'][:3])
            stats += f"\n{i}. **{alert['severity']}** - {keywords}... *(Time: {time})*"
    else:
        stats += "\nNo disasters detected yet."
    
    return stats

def get_history():
    """Get recent detection history"""
    history = load_history()
    
    if not history:
        return "📋 **No detection history yet!**"
    
    history_text = "### 📋 Recent Detection History\n\n"
    
    for i, entry in enumerate(history[:10], 1):
        timestamp = entry['timestamp'].split('T')
        date = timestamp[0]
        time = timestamp[1][:5]
        status_emoji = "🔴" if entry['status'] == 'DISASTER ALERT' else "✅"
        
        history_text += f"""
**{i}. {status_emoji} {entry['status']} - {date} {time}**
- Tweet: *"{entry['tweet'][:80]}..."*
- Severity: {entry['severity']}
- Keywords: {', '.join(entry['keywords_found']) if entry['keywords_found'] else 'None'}

---
"""
    
    return history_text

# Create the enhanced web app
with gr.Blocks(
    title="AI Disaster Detection Alert System",
    theme=gr.themes.Soft(primary_hue="red", secondary_hue="orange")
) as demo:
    
    gr.Markdown("""
    # 🚨 AI Disaster Detection Alert System
    
    **Emergency Response AI for Real-Time Social Media Monitoring**
    """)
    
    with gr.Tabs():
        # TAB 1: Main Detection
        with gr.Tab("🔍 Disaster Detector"):
            gr.Markdown("""
            ### About This System
            This AI helps emergency services **detect REAL disasters** from social media noise in real-time.
            
            **Who Benefits:**
            - 🚒 Firefighters - Find fire/explosion reports
            - 🚑 EMS - Locate injured people  
            - 📰 News - Verify breaking news
            - 🏛️ Government - Coordinate rescue operations
            - 🤖 AI Systems - Automated alert routing
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 Input Tweet")
                    tweet_input = gr.Textbox(
                        label="Enter Tweet to Analyze",
                        placeholder="Example: Earthquake reported near Tokyo - residents evacuating",
                        lines=4,
                        elem_classes="tweet-input"
                    )
                    
                    with gr.Row():
                        submit_btn = gr.Button("🔍 Analyze Tweet", variant="primary", size="lg")
                        clear_btn = gr.Button("🗑️ Clear", size="lg")
                
                with gr.Column(scale=1):
                    gr.Markdown("### 💡 Example Tweets")
                    gr.Examples(
                        examples=[
                            ["Earthquake magnitude 7.5 in Tokyo, buildings collapsing"],
                            ["Massive flood in Pakistan, evacuation ongoing"],
                            ["My exam was a total disaster"],
                            ["Building collapsed with people trapped inside"],
                            ["Today is a beautiful day"],
                            ["Fire at apartment building - 20 people injured"]
                        ],
                        inputs=tweet_input
                    )
            
            with gr.Row():
                with gr.Column(scale=2):
                    output = gr.Markdown(label="Analysis Result", elem_classes="result-box")
                with gr.Column(scale=1):
                    category_out = gr.Markdown(label="Category Breakdown")
                    status_out = gr.Textbox(label="Status", interactive=False)
            
            submit_btn.click(
                fn=detect_disaster,
                inputs=tweet_input,
                outputs=[output, category_out, status_out]
            )
            
            clear_btn.click(
                fn=lambda: ("", "", ""),
                outputs=[tweet_input, output, category_out]
            )
        
        # TAB 2: Statistics
        with gr.Tab("📊 Statistics & Analytics"):
            gr.Markdown("### 📈 System Performance Metrics")
            
            stats_output = gr.Markdown(label="Statistics")
            refresh_btn = gr.Button("🔄 Refresh Statistics", variant="primary")
            
            refresh_btn.click(fn=get_statistics, outputs=stats_output)
            
            # Auto-load on tab view
            demo.load(fn=get_statistics, outputs=stats_output)
        
        # TAB 3: History
        with gr.Tab("📋 Detection History"):
            gr.Markdown("### 📜 Recent Detection History")
            
            history_output = gr.Markdown(label="History")
            refresh_history_btn = gr.Button("🔄 Refresh History", variant="primary")
            
            refresh_history_btn.click(fn=get_history, outputs=history_output)
            
            demo.load(fn=get_history, outputs=history_output)
        
        # TAB 4: About
        with gr.Tab("ℹ️ About & Guide"):
            gr.Markdown("""
            ## 🚨 How the System Works
            
            ### Detection Categories:
            
            **🌍 Natural Disasters**
            - Earthquakes, floods, tsunamis, hurricanes, tornadoes, landslides, volcanoes, avalanches
            
            **🚗 Accidents & Incidents**
            - Vehicle crashes, explosions, fires, building collapses
            
            **🚑 Injuries & Casualties**
            - Killed, death, injured, casualties, people trapped
            
            **🚨 Emergency Response**
            - Evacuation, rescue, emergency alerts, warnings
            
            ### Severity Levels:
            
            | Level | Symbol | Response | Description |
            |-------|--------|----------|-------------|
            | **CRITICAL** | 🔴🔴🔴 | Immediate 911 Response | Loss of life, large-scale disaster |
            | **HIGH** | 🔴🔴 | Dispatch Emergency Services | Immediate threat to public safety |
            | **MEDIUM** | 🟡 | Monitor & Prepare | Potential emergency, gathering info |
            
            ### Features:
            
            ✨ **Real-Time Analysis** - Instant keyword detection
            📊 **Statistics Dashboard** - Track detection patterns
            📋 **History Tracking** - Review past detections
            🎯 **Confidence Scores** - Based on keyword matches
            🏷️ **Category Classification** - Identify disaster type
            
            ### Usage Tips:
            
            1. Paste real tweets or social media posts
            2. System analyzes for disaster keywords
            3. Provides severity rating and recommended action
            4. View history and statistics
            5. Use for training emergency response teams
            
            **Note:** This is an AI-assisted tool. Always verify alerts through official sources.
            """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
