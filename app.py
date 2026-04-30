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

DISASTER_WORDS = {}
for category, words in DISASTER_DATABASE.items():
    for word, details in words.items():
        DISASTER_WORDS[word] = details

HISTORY_FILE = 'detection_history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def detect_disaster(tweet):
    tweet_lower = tweet.lower().strip()
    
    if not tweet:
        return "⚠️ **Please enter a tweet to analyze!**", "", "No Input"
    
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
            
            current_level = details['severity']
            if max_severity is None or severity_order.get(current_level, 0) > severity_order.get(max_severity, 0):
                max_severity = current_level
    
    if found_disasters:
        if max_severity == 'CRITICAL':
            emoji_display = "🔴🔴🔴"
            action = "⚠️ **IMMEDIATE RESPONSE NEEDED** - Contact emergency services (911)"
        elif max_severity == 'HIGH':
            emoji_display = "🔴🔴"
            action = "🚨 **Dispatch emergency services immediately!**"
        else:
            emoji_display = "🟡"
            action = "📋 **Monitor situation, prepare response team**"
        
        keywords_list = "\n".join([
            f"  • **{word}** - {details['details']['description']}"
            for word, details in found_disasters.items()
        ])
        
        result = f"""### {emoji_display} DISASTER DETECTED {emoji_display}
**Severity:** {max_severity}
**Keywords:** {keywords_list}
**Action:** {action}
**Confidence:** {min(100, len(found_disasters) * 25)}%"""
        status = "DISASTER ALERT"
        
    else:
        result = """### ✅ SAFE
No disaster keywords found."""
        status = "SAFE"
    
    history = load_history()
    history.insert(0, {
        'timestamp': datetime.now().isoformat(),
        'tweet': tweet,
        'status': status,
        'severity': max_severity or 'NONE',
        'keywords_found': list(found_disasters.keys())
    })
    history = history[:50]
    save_history(history)
    
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
    history = load_history()
    
    if not history:
        return "📊 **No detection history yet!**"
    
    total = len(history)
    disasters = sum(1 for h in history if h['status'] == 'DISASTER ALERT')
    safe = total - disasters
    critical = sum(1 for h in history if h['severity'] == 'CRITICAL')
    high = sum(1 for h in history if h['severity'] == 'HIGH')
    medium = sum(1 for h in history if h['severity'] == 'MEDIUM')
    
    stats = f"""### 📊 STATISTICS
**Total Analyzed:** {total}
**Disasters Detected:** {disasters} ({disasters*100//total if total > 0 else 0}%)
**Safe Tweets:** {safe} ({safe*100//total if total > 0 else 0}%)

**Severity Breakdown:**
🔴🔴🔴 Critical: {critical}
🔴🔴 High: {high}
🟡 Medium: {medium}"""
    
    return stats

def get_history():
    history = load_history()
    
    if not history:
        return "📋 **No history yet!**"
    
    history_text = "### 📋 RECENT DETECTIONS\n"
    
    for i, entry in enumerate(history[:10], 1):
        timestamp = entry['timestamp'].split('T')
        date = timestamp[0]
        time = timestamp[1][:5]
        emoji = "🔴" if entry['status'] == 'DISASTER ALERT' else "✅"
        
        history_text += f"\n{i}. {emoji} {entry['status']} ({date} {time})\n"
        history_text += f"   Tweet: {entry['tweet'][:60]}...\n"
        history_text += f"   Severity: {entry['severity']}\n"
    
    return history_text

# Simple inline CSS
simple_css = """
.container { max-width: 1200px; }
.header { background: linear-gradient(90deg, #FF6B6B, #FF8C42); padding: 30px; color: white; text-align: center; border-radius: 15px; margin-bottom: 20px; }
.header h1 { font-size: 2.5em; margin: 0; }
.header p { margin: 5px 0 0 0; }
button { background: linear-gradient(90deg, #FF6B6B, #FF8C42) !important; color: white !important; border-radius: 10px !important; }
"""

with gr.Blocks(
    title="🚨 AI Disaster Detection",
    theme=gr.themes.Soft(primary_hue="red"),
    css=simple_css
) as demo:
    
    gr.HTML("""
    <div class="header">
        <h1>🚨 AI DISASTER DETECTION ALERT</h1>
        <p>Real-Time Emergency Response System</p>
    </div>
    """)
    
    with gr.Tabs():
        with gr.Tab("🔍 DETECTOR"):
            gr.Markdown("### Analyze tweets for disasters")
            
            with gr.Row():
                with gr.Column():
                    tweet = gr.Textbox(
                        label="Tweet",
                        placeholder="Enter tweet...",
                        lines=5
                    )
                    with gr.Row():
                        btn_analyze = gr.Button("🔍 ANALYZE", variant="primary")
                        btn_clear = gr.Button("🗑️ CLEAR")
                
                with gr.Column():
                    gr.Markdown("### Examples")
                    gr.Examples(
                        examples=[
                            ["Earthquake in Tokyo!"],
                            ["Building collapsed!"],
                            ["My exam was a disaster"],
                            ["Today is nice"]
                        ],
                        inputs=tweet
                    )
            
            with gr.Row():
                result = gr.Textbox(label="Result", interactive=False)
            
            with gr.Row():
                category = gr.Textbox(label="Categories", interactive=False)
                status = gr.Textbox(label="Status", interactive=False)
            
            btn_analyze.click(
                fn=detect_disaster,
                inputs=tweet,
                outputs=[result, category, status]
            )
            btn_clear.click(fn=lambda: ("", "", ""), outputs=[tweet, result, category])
        
        with gr.Tab("📊 STATS"):
            stats_out = gr.Markdown()
            btn_refresh = gr.Button("🔄 REFRESH")
            btn_refresh.click(fn=get_statistics, outputs=stats_out)
            demo.load(fn=get_statistics, outputs=stats_out)
        
        with gr.Tab("📋 HISTORY"):
            history_out = gr.Markdown()
            btn_refresh2 = gr.Button("🔄 REFRESH")
            btn_refresh2.click(fn=get_history, outputs=history_out)
            demo.load(fn=get_history, outputs=history_out)
        
        with gr.Tab("ℹ️ ABOUT"):
            gr.Markdown("""
            ### 🚨 How It Works
            
            **Categories:**
            - 🌍 Natural Disasters
            - 🚗 Accidents
            - 🚑 Injuries
            - 🚨 Emergency
            
            **Severity Levels:**
            - 🔴🔴🔴 CRITICAL - Call 911
            - 🔴🔴 HIGH - Dispatch services
            - 🟡 MEDIUM - Monitor
            """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
