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

# Custom CSS for professional styling
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

* {
    font-family: 'Poppins', sans-serif;
}

body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.gradio-container {
    background: transparent !important;
    max-width: 1400px;
}

.header-container {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 50%, #c92a2a 100%);
    padding: 40px 20px;
    border-radius: 20px;
    color: white;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

.header-container h1 {
    font-size: 2.5em;
    margin: 0;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.header-container p {
    font-size: 1.2em;
    margin: 10px 0 0 0;
    opacity: 0.95;
    font-weight: 300;
}

.tab-nav {
    display: flex;
    gap: 15px;
    margin-bottom: 30px;
    flex-wrap: wrap;
}

.tab-button {
    padding: 12px 30px;
    border: none;
    border-radius: 50px;
    font-size: 1.1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.tab-button.active {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
}

.content-card {
    background: white;
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.input-section {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 30px;
    border-radius: 15px;
    margin-bottom: 20px;
}

.button-group {
    display: flex;
    gap: 15px;
    margin-top: 20px;
}

.button-group button {
    flex: 1;
    padding: 15px 30px;
    border: none;
    border-radius: 10px;
    font-size: 1.1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

.primary-btn {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
    color: white;
    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
}

.primary-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(255, 107, 107, 0.6);
}

.secondary-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.secondary-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

.result-box {
    background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
    border-left: 5px solid #ff6b6b;
    padding: 25px;
    border-radius: 10px;
    margin: 20px 0;
}

.result-box h3 {
    color: #c92a2a;
    margin-top: 0;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 25px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.stat-card h3 {
    margin: 0;
    font-size: 2.5em;
    font-weight: 700;
}

.stat-card p {
    margin: 10px 0 0 0;
    opacity: 0.9;
}

.example-box {
    background: #f0f9ff;
    border-left: 4px solid #667eea;
    padding: 20px;
    border-radius: 10px;
    margin: 15px 0;
}

.severity-critical {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}

.severity-high {
    background: linear-gradient(135deg, #ffa500 0%, #ff8c00 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}

.severity-medium {
    background: linear-gradient(135deg, #ffd700 0%, #ffc700 100%);
    color: #333;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}

.severity-safe {
    background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}

.markdown h1, .markdown h2, .markdown h3 {
    color: #2d3748;
    font-weight: 700;
}

.markdown strong {
    color: #c92a2a;
}

.icon-emoji {
    font-size: 2em;
    margin-right: 10px;
}

@media (max-width: 768px) {
    .content-card {
        padding: 20px;
    }
    
    .header-container h1 {
        font-size: 1.8em;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .button-group {
        flex-direction: column;
    }
}
"""

# Create the enhanced web app
with gr.Blocks(
    title="AI Disaster Detection Alert System",
    theme=gr.themes.Soft(primary_hue="red", secondary_hue="orange"),
    css=custom_css
) as demo:
    
    # Header
    gr.HTML("""
    <div class="header-container">
        <h1>🚨 AI DISASTER DETECTION ALERT SYSTEM</h1>
        <p>🤖 AI-Powered Emergency Response | Real-Time Social Media Monitoring</p>
    </div>
    """)
    
    with gr.Tabs():
        # TAB 1: Main Detection
        with gr.Tab("🔍 Disaster Detector", id="detector"):
            with gr.Column():
                gr.Markdown("""
                ## About This System
                This AI helps emergency services **detect REAL disasters** from social media noise in real-time.
                
                ✅ **Who Benefits:**
                - 🚒 Firefighters - Find fire/explosion reports
                - 🚑 EMS - Locate injured people  
                - 📰 News - Verify breaking news
                - 🏛️ Government - Coordinate rescue operations
                """)
                
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.HTML("<h3>📝 Analyze a Tweet</h3>")
                        tweet_input = gr.Textbox(
                            label="Enter Tweet to Analyze",
                            placeholder="Example: Earthquake reported near Tokyo - residents evacuating",
                            lines=5,
                            elem_classes="tweet-input"
                        )
                        
                        with gr.Row():
                            submit_btn = gr.Button("🔍 Analyze Tweet", variant="primary", size="lg")
                            clear_btn = gr.Button("🗑️ Clear", size="lg")
                    
                    with gr.Column(scale=1):
                        gr.HTML("<h3>💡 Quick Examples</h3>")
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
                
                gr.Markdown("---")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        output = gr.Markdown(label="Analysis Result")
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
        with gr.Tab("📊 Statistics & Analytics", id="stats"):
            with gr.Column():
                gr.HTML("<h2>📈 System Performance Metrics</h2>")
                
                stats_output = gr.Markdown(label="Statistics")
                refresh_btn = gr.Button("🔄 Refresh Statistics", variant="primary")
                
                refresh_btn.click(fn=get_statistics, outputs=stats_output)
                demo.load(fn=get_statistics, outputs=stats_output)
        
        # TAB 3: History
        with gr.Tab("📋 Detection History", id="history"):
            with gr.Column():
                gr.HTML("<h2>📜 Recent Detection History</h2>")
                
                history_output = gr.Markdown(label="History")
                refresh_history_btn = gr.Button("🔄 Refresh History", variant="primary")
                
                refresh_history_btn.click(fn=get_history, outputs=history_output)
                demo.load(fn=get_history, outputs=history_output)
        
        # TAB 4: About
        with gr.Tab("ℹ️ About & Guide", id="about"):
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
