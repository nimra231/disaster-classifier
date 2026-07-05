import streamlit as st
import pandas as pd
import csv
import io
import re
import time
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

import random

st.set_page_config(page_title="SENTINEL | Disaster Tweet Classifier", page_icon="🛰️", layout="wide")

# ============================================
# DESIGN TOKENS  —  Cinematic "Disaster Command" theme
# ============================================
BG          = "#05070A"
SURFACE     = "#121826"
SURFACE_2   = "#1A2233"
GLASS       = "rgba(18,24,38,0.66)"
BORDER      = "rgba(255,255,255,0.09)"
BORDER_MPL  = "#FFFFFF17"   # matplotlib-safe (8-digit hex) equivalent of BORDER, for charts only
TEXT        = "#F1F3F8"
TEXT_MUTED  = "#8B93A7"
AMBER       = "#F5A623"   # brand / warning accent
CRITICAL    = "#E8384F"   # cinematic crimson
HIGH        = "#FF8A3D"
MEDIUM      = "#F5C518"
SAFE        = "#2ED988"
CYAN        = "#2FD1C5"   # teal data accent

SEVERITY_COLOR = {'CRITICAL': CRITICAL, 'HIGH': HIGH, 'MEDIUM': MEDIUM, 'SAFE': SAFE}
SEVERITY_RANK  = {'CRITICAL': 3, 'HIGH': 2, 'MEDIUM': 1}

# ============================================
# SESSION STATE
# ============================================
defaults = {
    'history': [], 'all_keywords': [], 'all_locations': [], 'all_categories': [],
    'stats': {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'safe': 0},
    'tweet_input_value': "",
    'scan_times_ms': [],
    'example_fill': None,
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

# Approximate coordinates for map plotting (city centroids / country capitals for country-level entries)
CITY_COORDS = {
    'Karachi': (24.8607, 67.0011), 'Lahore': (31.5497, 74.3436), 'Islamabad': (33.6844, 73.0479),
    'Peshawar': (34.0151, 71.5249), 'Quetta': (30.1798, 66.9750), 'Multan': (30.1575, 71.5249),
    'Faisalabad': (31.4504, 73.1350), 'Rawalpindi': (33.5651, 73.0169),
    'New York': (40.7128, -74.0060), 'Los Angeles': (34.0522, -118.2437), 'Chicago': (41.8781, -87.6298),
    'Florida': (27.6648, -81.5158), 'California': (36.7783, -119.4179), 'Texas': (31.9686, -99.9018),
    'Miami': (25.7617, -80.1918),
    'London': (51.5074, -0.1278), 'Manchester': (53.4808, -2.2426), 'Paris': (48.8566, 2.3522),
    'Berlin': (52.5200, 13.4050), 'Madrid': (40.4168, -3.7038), 'Rome': (41.9028, 12.4964),
    'Moscow': (55.7558, 37.6173),
    'Tokyo': (35.6762, 139.6503), 'Osaka': (34.6937, 135.5023), 'Beijing': (39.9042, 116.4074),
    'Shanghai': (31.2304, 121.4737), 'Seoul': (37.5665, 126.9780), 'Mumbai': (19.0760, 72.8777),
    'Delhi': (28.7041, 77.1025), 'Bangalore': (12.9716, 77.5946), 'Kolkata': (22.5726, 88.3639),
    'Dubai': (25.2048, 55.2708), 'Abu Dhabi': (24.4539, 54.3773), 'Riyadh': (24.7136, 46.6753),
    'Istanbul': (41.0082, 28.9784), 'Cairo': (30.0444, 31.2357), 'Jakarta': (-6.2088, 106.8456),
    'Manila': (14.5995, 120.9842), 'Bangkok': (13.7563, 100.5018),
    'Sydney': (-33.8688, 151.2093), 'Melbourne': (-37.8136, 144.9631), 'Toronto': (43.6532, -79.3832),
    'Vancouver': (49.2827, -123.1207), 'Pakistan': (30.3753, 69.3451), 'India': (20.5937, 78.9629),
    'Japan': (36.2048, 138.2529), 'China': (35.8617, 104.1954),
    'Afghanistan': (33.9391, 67.7100), 'Iran': (32.4279, 53.6880), 'Nepal': (28.3949, 84.1240),
    'Bangladesh': (23.6850, 90.3563), 'Turkey': (38.9637, 35.2433), 'Syria': (34.8021, 38.9968),
    'Yemen': (15.5527, 48.5164), 'Philippines': (12.8797, 121.7740),
    'Indonesia': (-0.7893, 113.9213), 'Australia': (-25.2744, 133.7751), 'Canada': (56.1304, -106.3468),
    'Mexico': (23.6345, -102.5528), 'Brazil': (-14.2350, -51.9253), 'Haiti': (18.9712, -72.2852),
    'Chile': (-35.6751, -71.5430), 'Nigeria': (9.0820, 8.6753),
}

# ============================================
# ML VERIFICATION LAYER — TF-IDF + Logistic Regression
# Trained on a small, hand-labeled dataset (built in-house, not a public dataset).
# Purpose: catch paraphrased disaster reports that contain NO exact keyword match,
# and flag keyword false-positives (e.g. "my exam was a disaster").
# Honesty note: this is a small dataset (~150 rows) — treat reported metrics as an
# internal sanity check, not a rigorous benchmark. Swap in a larger labeled dataset
# (e.g. the public "Real or Not? NLP with Disaster Tweets" dataset) for production use.
# ============================================
TRAINING_DATA = [
    # --- Disaster (label 1) — direct keyword examples ---
    ("earthquake hits downtown, several buildings collapsed", 1),
    ("wildfire spreading fast near the residential area, evacuation ordered", 1),
    ("flash flood warning issued for the valley tonight", 1),
    ("explosion reported at the factory, injuries confirmed", 1),
    ("gunman opens fire at the shopping mall, police responding", 1),
    ("tsunami warning issued after offshore earthquake", 1),
    ("hurricane makes landfall, mandatory evacuation ordered", 1),
    ("gas leak forces evacuation of the entire apartment building", 1),
    ("train derailment leaves dozens injured near the station", 1),
    ("landslide blocks the major highway after heavy rain", 1),
    ("bridge collapse traps several vehicles below", 1),
    ("volcano eruption forces thousands to flee the region", 1),
    ("wildfire outbreak destroys hundreds of homes overnight", 1),
    ("plane crash reported near the airport, rescue underway", 1),
    ("chemical spill contaminates the local water supply", 1),
    ("shooting at the university campus, students in lockdown", 1),
    ("dam breach threatens nearby villages downstream", 1),
    ("building collapse in the city center, rescue teams searching rubble", 1),
    ("avalanche buries part of the mountain village", 1),
    ("terrorist attack reported at the train station", 1),
    # --- Disaster (label 1) — paraphrased, NO exact trigger word ---
    ("the ground shook violently and the walls came down around us", 1),
    ("water rushed through the streets and people were stuck on rooftops", 1),
    ("the sky turned orange as thick clouds rolled in from the burning hillside", 1),
    ("residents were told to leave their homes immediately as the water kept rising", 1),
    ("the whole building came down in seconds, dust everywhere", 1),
    ("the ferry went under near the coast, many still unaccounted for", 1),
    ("the ground opened up and swallowed part of the street", 1),
    ("shots rang out at the shopping center, people scattered in panic", 1),
    ("hundreds are stuck without food or water after the crossing gave way", 1),
    ("the sky is black with smoke and I can barely breathe outside", 1),
    ("families are sleeping in tents after their homes were destroyed overnight", 1),
    ("the water level rose three feet in an hour, cars are floating away", 1),
    ("an entire neighborhood is underwater after the levee gave way", 1),
    ("the mountain let loose and buried the village below", 1),
    ("a wall of water swept away everything in its path along the coast", 1),
    ("the aircraft went down shortly after takeoff, crews rushing to the scene", 1),
    ("the whole block lost power after the transformer blew apart", 1),
    ("people are running from the flames as the hillside burns out of control", 1),
    ("the region has had no clean water for days after the pipeline burst", 1),
    ("several people were pulled unconscious from the wreckage this morning", 1),
    ("cars are stacked on top of each other after the multi-vehicle pileup", 1),
    ("the school was locked down after reports of an armed man inside", 1),
    ("the coastline is unrecognizable after the waves tore through overnight", 1),
    ("smoke is pouring out of the apartment complex and sirens are everywhere", 1),
    ("the whole town has been ordered out before the fire reaches the ridge", 1),
    ("the tremor knocked out power across half the city", 1),
    ("rescue crews are pulling survivors from the rubble at this hour", 1),
    ("roads are impassable after the hillside gave way onto the highway", 1),
    ("the storm ripped roofs off houses along the entire coastline", 1),
    ("dozens are missing after the boat went down in rough seas", 1),
    ("the whole valley is filling with smoke, visibility near zero", 1),
    ("panic broke out after loud blasts were heard near the market", 1),
    ("the riverbank gave way, sweeping homes into the current", 1),
    ("crews worked through the night pulling people from the collapsed structure", 1),
    ("the entire coastline was placed on high alert after the seabed shifted", 1),
    ("thick ash is falling on the city, streets are empty", 1),
    ("the whole apartment block was reduced to rubble within minutes", 1),
    # --- Not disaster (label 0) — casual/metaphorical use of disaster-adjacent words ---
    ("my exam was a total disaster lol i definitely failed", 0),
    ("this presentation was a trainwreck but somehow i survived", 0),
    ("my room is a disaster zone right now, need to clean", 0),
    ("that movie was an absolute catastrophe, don't waste your time", 0),
    ("trying to finish this project by tonight, my hair is basically on fire", 0),
    ("this diet crashed and burned by day two, back to pizza", 0),
    ("my code just crashed for the tenth time today, send help", 0),
    ("work has been an absolute emergency lately, so much overtime", 0),
    ("traffic today was an absolute nightmare, total gridlock for hours", 0),
    ("that concert was fire, best show i've seen all year", 0),
    ("my finances are a mess right now, total meltdown", 0),
    ("i'm drowning in homework this week, send coffee", 0),
    ("this new song is straight fire, on repeat all day", 0),
    ("the game last night was explosive, what a comeback", 0),
    ("my inbox is completely flooded with emails today", 0),
    ("that new burger place is an absolute bomb, so good", 0),
    ("my group project fell apart, total chaos honestly", 0),
    ("today was a whirlwind, so much happened at work", 0),
    ("the sale was insane, the store was a warzone of shoppers", 0),
    ("i bombed that interview so hard, cringing thinking about it", 0),
    ("that comedy show was killer, laughed the whole time", 0),
    ("my weekend plans just blew up, everyone cancelled", 0),
    ("the new update wrecked my whole workflow, so annoying", 0),
    ("my sleep schedule is a disaster this week", 0),
    ("that essay was a nightmare to write but it's finally done", 0),
    # --- Not disaster (label 0) — normal everyday tweets ---
    ("just had the best coffee of my life this morning", 0),
    ("excited for the weekend trip with friends", 0),
    ("watching the sunset from my balcony right now", 0),
    ("finally finished reading that book, loved every page", 0),
    ("grabbing lunch with my sister today, can't wait", 0),
    ("can't wait for the new season of my favorite show", 0),
    ("just adopted a puppy, so happy right now", 0),
    ("beautiful weather today, perfect for a long walk", 0),
    ("cooking dinner for the family tonight, trying a new recipe", 0),
    ("studying for finals at the library all afternoon", 0),
    ("went for a run this morning, feeling great", 0),
    ("new phone just arrived, loving the camera quality", 0),
    ("planning my vacation for next month, so excited", 0),
    ("had a great meeting with the team today", 0),
    ("trying out a new recipe this weekend, wish me luck", 0),
    ("caught up with an old friend over coffee today", 0),
    ("started a new book series, already hooked", 0),
    ("the farmers market was lovely this morning", 0),
    ("finished my workout, feeling strong today", 0),
    ("spent the afternoon painting, very relaxing", 0),
    ("got a promotion at work today, so thrilled", 0),
    ("baked cookies with my kids this afternoon", 0),
    ("the flight landed early, more time to explore the city", 0),
    ("finally organized my closet, feels so much better", 0),
    ("tried a new coffee shop downtown, really cozy vibe", 0),
    ("my plants are finally blooming, so proud of them", 0),
    ("caught the early train, got to work with time to spare", 0),
    ("spent the evening playing board games with family", 0),
    ("the museum exhibit was fascinating, highly recommend", 0),
    ("just wrapped up a great workout class", 0),
]


@st.cache_resource(show_spinner=False)
def train_ml_classifier():
    """Trains a small TF-IDF + Logistic Regression model once per app process."""
    texts = [t for t, _ in TRAINING_DATA]
    labels = [l for _, l in TRAINING_DATA]

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words='english', min_df=1)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=1000, C=2.0)
    model.fit(X_train_vec, y_train)

    preds = model.predict(X_test_vec)
    metrics = {
        'accuracy': accuracy_score(y_test, preds),
        'precision': precision_score(y_test, preds, zero_division=0),
        'recall': recall_score(y_test, preds, zero_division=0),
        'f1': f1_score(y_test, preds, zero_division=0),
        'train_size': len(X_train),
        'test_size': len(X_test),
    }
    return vectorizer, model, metrics


def ml_predict(text: str, vectorizer, model) -> float:
    """Returns probability (0-100) that the ML model thinks this tweet is disaster-related."""
    vec = vectorizer.transform([text])
    proba = model.predict_proba(vec)[0][1]
    return round(proba * 100, 1)


def resolve_verdict(found: list, keyword_severity, keyword_confidence: float, ml_score: float):
    """
    Single source of truth for the FINAL verdict — combines the keyword engine
    with the ML cross-check instead of letting the keyword engine always win
    while the ML result sits in a footnote underneath.

    Returns: (final_severity_or_None, note, final_confidence)
      note is one of:
        None                       keyword engine and ML agree, verdict stands as-is
        'override_false_positive'  keywords matched but ML strongly disagrees (<30%);
                                    verdict is downgraded and flagged for human review
        'soft_downgrade'           keywords matched but ML is unconvinced (30-49%);
                                    verdict is downgraded one severity tier
        'ml_only_catch'            no keyword match, but ML thinks it's disaster-related;
                                    verdict is upgraded from SAFE for human review
    """
    keyword_flagged = bool(found)
    ml_flagged = ml_score >= 50

    if keyword_flagged and ml_flagged:
        return keyword_severity, None, keyword_confidence

    if keyword_flagged and not ml_flagged:
        if ml_score < 30:
            return 'MEDIUM', 'override_false_positive', ml_score
        downgrade_map = {'CRITICAL': 'HIGH', 'HIGH': 'MEDIUM', 'MEDIUM': 'MEDIUM'}
        downgraded = downgrade_map[keyword_severity]
        note = 'soft_downgrade' if downgraded != keyword_severity else None
        return downgraded, note, (ml_score if note else keyword_confidence)

    if not keyword_flagged and ml_flagged:
        return 'MEDIUM', 'ml_only_catch', ml_score

    return None, None, keyword_confidence


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

# Train (or fetch cached) ML verification model once per app process
ML_VECTORIZER, ML_MODEL, ML_METRICS = train_ml_classifier()

# ============================================
# GLOBAL STYLE
# ============================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

.stApp {{
    background:
        radial-gradient(ellipse 1000px 600px at 20% -10%, rgba(232,56,79,0.10), transparent 60%),
        radial-gradient(ellipse 800px 550px at 100% 0%, rgba(47,209,197,0.08), transparent 55%),
        linear-gradient(180deg, {BG} 0%, #030405 100%);
    color: {TEXT};
}}
/* film grain + grid, fixed full-page overlay */
.stApp::before {{
    content: "";
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
    background-size: 40px 40px;
    mask-image: radial-gradient(ellipse 1200px 700px at 50% 0%, black 0%, transparent 78%);
}}
.stApp::after {{
    content: "";
    position: fixed; inset: 0; pointer-events: none; z-index: 0; opacity: 0.5;
    background: radial-gradient(ellipse 90% 70% at 50% 40%, transparent 55%, rgba(0,0,0,0.55) 100%);
}}

#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.2rem; max-width: 1180px; }}
h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif !important; color: {TEXT} !important; }}

/* ---------- Cinematic hero ---------- */
.hero {{
    position: relative; overflow: hidden;
    border-radius: 16px; border: 1px solid {BORDER};
    padding: 46px 40px 34px 40px; margin-bottom: 22px;
    background: linear-gradient(180deg, rgba(5,7,10,0.2) 0%, rgba(5,7,10,0.85) 78%, {BG} 100%), #0B0E14;
    box-shadow: 0 20px 60px rgba(0,0,0,0.55);
}}
.hero-skyline {{ position: absolute; left: 0; right: 0; bottom: 0; height: 130px; opacity: 0.9; }}
.hero-embers {{ position: absolute; inset: 0; overflow: hidden; pointer-events: none; }}
.ember {{
    position: absolute; bottom: -10px; width: 4px; height: 4px; border-radius: 50%;
    background: radial-gradient(circle, {AMBER}, transparent 70%);
    box-shadow: 0 0 6px 2px {AMBER}aa;
    animation: rise linear infinite;
}}
@keyframes rise {{
    0%   {{ transform: translateY(0) translateX(0); opacity: 0; }}
    10%  {{ opacity: 1; }}
    100% {{ transform: translateY(-260px) translateX(var(--drift, 20px)); opacity: 0; }}
}}
.hero-scanline {{
    position: absolute; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, {CYAN}, transparent);
    box-shadow: 0 0 12px 2px {CYAN}aa;
    animation: scan 4.5s ease-in-out infinite;
    opacity: 0.7;
}}
@keyframes scan {{
    0%, 100% {{ top: 8%; opacity: 0; }}
    50% {{ top: 92%; opacity: 0.8; }}
}}
.hero-eyebrow {{
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 3px;
    color: {CRITICAL}; text-transform: uppercase; display: flex; align-items: center; gap: 8px;
    position: relative; z-index: 2;
}}
.hero-title {{
    font-family: 'Bebas Neue', sans-serif; font-size: 4.6rem; line-height: 0.95;
    letter-spacing: 2px; color: {TEXT}; margin: 6px 0 4px 0; position: relative; z-index: 2;
    text-shadow: 0 4px 30px rgba(232,56,79,0.25);
}}
.hero-title span {{ color: {AMBER}; }}
.hero-sub {{
    font-family: 'Inter', sans-serif; font-size: 1rem; color: {TEXT_MUTED}; max-width: 560px;
    position: relative; z-index: 2; line-height: 1.5;
}}
.status-pill {{
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; letter-spacing: 1px;
    color: {SAFE}; background: rgba(46, 217, 136, 0.1); border: 1px solid rgba(46, 217, 136, 0.35);
    padding: 7px 16px; border-radius: 20px; display: inline-flex; align-items: center; gap: 8px;
    box-shadow: 0 0 18px rgba(46, 217, 136, 0.18); position: relative; z-index: 2; margin-top: 14px;
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

/* ---------- 3D tilt utility ---------- */
.tilt {{ transition: transform 0.25s ease, box-shadow 0.25s ease; transform-style: preserve-3d; }}
.tilt:hover {{ transform: perspective(700px) rotateX(3deg) rotateY(-3deg) translateY(-5px); }}

/* ---------- Entrance animations ---------- */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
    from {{ opacity: 0; }} to {{ opacity: 1; }}
}}
.fade-in-up {{ animation: fadeInUp 0.55s cubic-bezier(0.16, 1, 0.3, 1) both; }}
.kpi-strip .kpi-card:nth-child(1) {{ animation: fadeInUp 0.5s ease both; animation-delay: 0.05s; }}
.kpi-strip .kpi-card:nth-child(2) {{ animation: fadeInUp 0.5s ease both; animation-delay: 0.12s; }}
.kpi-strip .kpi-card:nth-child(3) {{ animation: fadeInUp 0.5s ease both; animation-delay: 0.19s; }}
.kpi-strip .kpi-card:nth-child(4) {{ animation: fadeInUp 0.5s ease both; animation-delay: 0.26s; }}

/* ---------- Radar sweep (hero corner accent) ---------- */
.radar {{
    position: absolute; top: 22px; right: 30px; width: 86px; height: 86px; z-index: 2;
    border-radius: 50%; border: 1px solid {BORDER};
    background: radial-gradient(circle at center, rgba(47,209,197,0.06) 0%, transparent 70%);
}}
.radar::before {{
    content: ""; position: absolute; inset: 0; border-radius: 50%;
    background: conic-gradient(from 0deg, {CYAN}bb, transparent 30%);
    animation: spin 3.2s linear infinite;
    -webkit-mask: radial-gradient(circle, transparent 55%, black 56%);
            mask: radial-gradient(circle, transparent 55%, black 56%);
}}
.radar::after {{
    content: ""; position: absolute; top: 50%; left: 50%; width: 6px; height: 6px;
    background: {CYAN}; border-radius: 50%; transform: translate(-50%, -50%);
    box-shadow: 0 0 10px 3px {CYAN}aa;
}}
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
.radar-ring {{ position: absolute; border-radius: 50%; border: 1px solid {CYAN}55; inset: 14px; }}
.radar-ring::before {{ content:""; position:absolute; inset:14px; border-radius:50%; border:1px solid {CYAN}33; }}

/* ---------- Hero KPI strip ---------- */
.kpi-strip {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }}
.kpi-card {{
    background: linear-gradient(160deg, {GLASS} 0%, rgba(26,34,51,0.7) 100%);
    backdrop-filter: blur(10px);
    border: 1px solid {BORDER}; border-radius: 12px; padding: 16px 18px;
    box-shadow: 0 10px 26px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04);
    position: relative; overflow: hidden;
}}
.kpi-card::after {{
    content: ""; position: absolute; right: -20px; top: -20px; width: 80px; height: 80px;
    border-radius: 50%; background: radial-gradient(circle, var(--kpi-glow, {AMBER}) 0%, transparent 70%);
    opacity: 0.22;
}}
.kpi-label {{ font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; letter-spacing: 1.3px; color: {TEXT_MUTED}; text-transform: uppercase; }}
.kpi-value {{ font-family: 'Space Grotesk', sans-serif; font-size: 2.1rem; font-weight: 700; margin-top: 4px; line-height: 1; }}
.kpi-foot {{ font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: {TEXT_MUTED}; margin-top: 6px; }}

.impact-card {{
    background: linear-gradient(160deg, {GLASS} 0%, rgba(26,34,51,0.7) 100%);
    backdrop-filter: blur(10px);
    border: 1px solid {BORDER}; border-left: 3px solid {AMBER};
    border-radius: 10px; padding: 18px 20px; height: 100%;
    box-shadow: 0 10px 24px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
}}
.impact-label {{
    font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; letter-spacing: 1.5px;
    color: {AMBER}; text-transform: uppercase; margin-bottom: 6px;
}}
.impact-text {{ color: {TEXT_MUTED}; font-size: 0.92rem; line-height: 1.5; }}
.impact-text b {{ color: {TEXT}; }}

.result-card {{
    background: linear-gradient(160deg, {GLASS} 0%, rgba(26,34,51,0.75) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid {BORDER}; border-radius: 14px; padding: 26px 28px; margin: 16px 0;
    box-shadow: 0 4px 10px rgba(0,0,0,0.25), 0 18px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
}}
.result-critical {{ border-left: 4px solid {CRITICAL}; box-shadow: 0 4px 10px rgba(0,0,0,0.25), 0 18px 40px rgba(0,0,0,0.4), -6px 0 32px -10px {CRITICAL}77; }}
.result-high {{ border-left: 4px solid {HIGH}; box-shadow: 0 4px 10px rgba(0,0,0,0.25), 0 18px 40px rgba(0,0,0,0.4), -6px 0 32px -10px {HIGH}55; }}
.result-medium {{ border-left: 4px solid {MEDIUM}; box-shadow: 0 4px 10px rgba(0,0,0,0.25), 0 18px 40px rgba(0,0,0,0.4), -6px 0 32px -10px {MEDIUM}44; }}
.result-safe {{ border-left: 4px solid {SAFE}; box-shadow: 0 4px 10px rgba(0,0,0,0.25), 0 18px 40px rgba(0,0,0,0.4), -6px 0 32px -10px {SAFE}44; }}

.result-head {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; font-weight: 700; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; letter-spacing: 0.2px; }}
.result-row {{ display: flex; gap: 10px; padding: 7px 0; font-size: 0.93rem; border-bottom: 1px dashed {BORDER}; }}
.result-row:last-child {{ border-bottom: none; }}
.result-key {{ font-family: 'JetBrains Mono', monospace; color: {TEXT_MUTED}; min-width: 130px; font-size: 0.78rem; letter-spacing: 0.5px; text-transform: uppercase; padding-top: 2px; }}
.result-val {{ color: {TEXT}; }}
.tag {{ display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; background: {SURFACE_2}; border: 1px solid {BORDER}; color: {TEXT}; padding: 3px 10px; border-radius: 5px; margin: 2px 4px 2px 0; transition: transform 0.15s ease, border-color 0.15s ease; }}
.tag:hover {{ transform: translateY(-1px); border-color: {AMBER}77; }}
.meter-wrap {{ display: flex; align-items: center; gap: 10px; width: 100%; }}
.meter-track {{ flex: 1; height: 7px; border-radius: 4px; background: {SURFACE_2}; border: 1px solid {BORDER}; overflow: hidden; }}
.meter-fill {{ height: 100%; border-radius: 4px; width: 0%; animation: growMeter 0.9s cubic-bezier(0.16,1,0.3,1) forwards; animation-delay: 0.1s; }}
@keyframes growMeter {{ to {{ width: var(--meter-pct, 0%); }} }}
.meter-pct {{ font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; font-weight: 700; min-width: 38px; text-align: right; }}
.action-line {{ margin-top: 16px; padding: 12px 16px; border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; letter-spacing: 0.5px; font-weight: 600; }}
.tweet-preview {{ font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 8px; padding: 14px 16px; line-height: 1.7; margin-bottom: 4px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.03); }}

section[data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
section[data-testid="stSidebar"] * {{ color: {TEXT}; }}
.sb-title {{ font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; letter-spacing: 1.5px; color: {TEXT_MUTED}; text-transform: uppercase; margin: 4px 0 10px 0; }}
.stat-line {{ display: flex; justify-content: space-between; align-items: center; padding: 7px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; border-bottom: 1px solid {BORDER}; }}
.stat-line:last-child {{ border-bottom: none; }}
.dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; margin-right: 8px; }}

.made-by-card {{
    text-align: center; padding: 18px; background: linear-gradient(160deg, {SURFACE_2} 0%, {SURFACE} 100%);
    border: 1px solid {AMBER}44; border-radius: 12px; margin-top: 18px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3), 0 0 24px -12px {AMBER}55;
}}
.made-by-name {{ font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 700; color: {AMBER}; letter-spacing: 0.5px; }}
.made-by-role {{ font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: {TEXT_MUTED}; letter-spacing: 1px; text-transform: uppercase; margin-top: 4px; }}

.stTextArea textarea {{ background: {SURFACE} !important; color: {TEXT} !important; border: 1px solid {BORDER} !important; border-radius: 8px !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.9rem !important; }}
.stTextArea textarea:focus {{ border-color: {AMBER} !important; box-shadow: 0 0 0 1px {AMBER}, 0 0 16px -4px {AMBER}88 !important; }}
.stButton > button {{
    background: linear-gradient(135deg, #FFC24D 0%, {AMBER} 55%, #E08E00 100%) !important;
    color: #1A1300 !important; border: none !important; border-radius: 8px !important;
    padding: 10px 22px !important; font-weight: 700 !important; font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.2px; box-shadow: 0 6px 16px -4px {AMBER}66; transition: all 0.15s ease;
}}
.stButton > button:hover {{ filter: brightness(1.08); box-shadow: 0 8px 20px -4px {AMBER}88; transform: translateY(-1px); }}
.stButton > button[kind="secondary"] {{
    background: {SURFACE_2} !important; color: {TEXT} !important; border: 1px solid {BORDER} !important; box-shadow: none;
}}

.stTabs [data-baseweb="tab-list"] {{ gap: 4px; background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; padding: 6px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.3); }}
.stTabs [data-baseweb="tab"] {{ font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: {TEXT_MUTED}; border-radius: 8px; padding: 9px 18px; transition: all 0.15s ease; }}
.stTabs [aria-selected="true"] {{ background: linear-gradient(135deg, {SURFACE_2}, {SURFACE_2}) !important; color: {AMBER} !important; box-shadow: 0 2px 10px rgba(0,0,0,0.3), inset 0 0 0 1px {AMBER}33; }}

.hist-row {{ display: grid; grid-template-columns: 78px 90px 1fr 110px 60px; gap: 10px; align-items: center; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; padding: 10px 14px; background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; margin-bottom: 6px; transition: border-color 0.15s ease; }}
.hist-row:hover {{ border-color: {AMBER}55; }}
.hist-badge {{ font-size: 0.68rem; padding: 3px 9px; border-radius: 5px; text-align: center; font-weight: 700; }}

.footer-bar {{ text-align: center; padding: 18px; margin-top: 28px; border-top: 1px solid {BORDER}; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: {TEXT_MUTED}; letter-spacing: 0.5px; }}
.stAlert {{ background: {SURFACE} !important; border: 1px solid {BORDER} !important; color: {TEXT} !important; border-radius: 10px !important; }}

/* ---------- Responsive: tablet ---------- */
@media (max-width: 900px) {{
    .hero-title {{ font-size: 3.4rem; }}
    .kpi-strip {{ grid-template-columns: repeat(2, 1fr); }}
    .radar {{ width: 60px; height: 60px; top: 16px; right: 16px; }}
    .hist-row {{ grid-template-columns: 64px 80px 1fr; }}
    .hist-row span:nth-child(4), .hist-row span:nth-child(5) {{ display: none; }}
}}
/* ---------- Responsive: mobile ---------- */
@media (max-width: 560px) {{
    .hero {{ padding: 32px 22px 24px 22px; }}
    .hero-title {{ font-size: 2.6rem; }}
    .hero-sub {{ font-size: 0.9rem; }}
    .kpi-strip {{ grid-template-columns: 1fr 1fr; gap: 10px; }}
    .kpi-value {{ font-size: 1.6rem; }}
    .radar {{ display: none; }}
    .result-card {{ padding: 18px 16px; }}
    .result-row {{ flex-direction: column; gap: 2px; }}
    .result-key {{ min-width: 0; }}
}}
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
    dial_deg = max(6, min(360, score * 3.6))
    st.markdown(f"""
    <div style="background:linear-gradient(160deg,{SURFACE_2} 0%,{SURFACE} 100%); border:1px solid {BORDER}; border-radius:12px; padding:16px; box-shadow:0 6px 18px rgba(0,0,0,0.3);">
        <div style="display:flex; align-items:center; gap:16px;">
            <div style="position:relative; width:72px; height:72px; border-radius:50%;
                        background:conic-gradient({threat_color} {dial_deg}deg, {BORDER} {dial_deg}deg);
                        display:flex; align-items:center; justify-content:center;
                        box-shadow:0 0 20px -6px {threat_color}88;">
                <div style="width:52px; height:52px; border-radius:50%; background:{SURFACE_2};
                            display:flex; align-items:center; justify-content:center;
                            font-family:'JetBrains Mono',monospace; font-size:0.72rem; font-weight:700; color:{threat_color};">
                    {int(score)}%
                </div>
            </div>
            <div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:{TEXT_MUTED}; letter-spacing:0.5px;">Last {len(recent)} scans</div>
                <div style="font-family:'Space Grotesk',sans-serif; font-size:1.05rem; font-weight:700; color:{threat_color}; margin-top:2px;">{threat_label}</div>
            </div>
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
# CINEMATIC HERO
# ============================================
random.seed(7)  # stable ember layout across reruns
embers_html = "".join(
    f'<span class="ember" style="left:{random.randint(2, 98)}%; '
    f'animation-duration:{random.uniform(3.5, 7.5):.1f}s; '
    f'animation-delay:{random.uniform(0, 6):.1f}s; '
    f'--drift:{random.randint(-30, 30)}px;"></span>'
    for _ in range(22)
)

SKYLINE_SVG = f"""
<svg class="hero-skyline" viewBox="0 0 1200 160" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="glow" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0%" stop-color="{CRITICAL}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{CRITICAL}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="0" y="90" width="1200" height="70" fill="url(#glow)"/>
  <g fill="#0B0E14" stroke="rgba(255,255,255,0.06)">
    <rect x="20" y="60" width="60" height="100"/>
    <rect x="90" y="30" width="50" height="130"/>
    <rect x="150" y="75" width="45" height="85"/>
    <rect x="205" y="15" width="55" height="145"/>
    <rect x="270" y="95" width="40" height="65"/>
    <rect x="320" y="50" width="65" height="110"/>
    <rect x="400" y="20" width="50" height="140"/>
    <rect x="460" y="80" width="45" height="80"/>
    <rect x="515" y="40" width="60" height="120"/>
    <rect x="585" y="65" width="40" height="95"/>
    <rect x="635" y="10" width="55" height="150"/>
    <rect x="700" y="90" width="50" height="70"/>
    <rect x="760" y="45" width="60" height="115"/>
    <rect x="830" y="70" width="45" height="90"/>
    <rect x="885" y="25" width="55" height="135"/>
    <rect x="950" y="85" width="40" height="75"/>
    <rect x="1000" y="55" width="65" height="105"/>
    <rect x="1075" y="15" width="50" height="145"/>
    <rect x="1135" y="75" width="45" height="85"/>
  </g>
  <g fill="{AMBER}" opacity="0.55">
    <rect x="35" y="80" width="6" height="6"/><rect x="55" y="100" width="6" height="6"/>
    <rect x="105" y="55" width="6" height="6"/><rect x="220" y="45" width="6" height="6"/>
    <rect x="335" y="75" width="6" height="6"/><rect x="415" y="50" width="6" height="6"/>
    <rect x="530" y="70" width="6" height="6"/><rect x="650" y="40" width="6" height="6"/>
    <rect x="775" y="80" width="6" height="6"/><rect x="900" y="55" width="6" height="6"/>
    <rect x="1015" y="85" width="6" height="6"/><rect x="1090" y="45" width="6" height="6"/>
  </g>
</svg>
"""

st.markdown(f"""
<div class="hero">
    <div class="hero-embers">{embers_html}</div>
    <div class="hero-scanline"></div>
    <div class="hero-eyebrow"><span class="pulse-dot" style="background:{CRITICAL}; box-shadow:0 0 0 0 {CRITICAL}99;"></span>LIVE EMERGENCY SIGNAL DETECTION</div>
    <h1 class="hero-title">SENTINEL<span>.</span></h1>
    <p class="hero-sub">AI-powered classification engine that scans tweets in real time, separates genuine disasters from noise, and scores severity in seconds — built on a {len(DISASTER_WORDS)}-term detection model.</p>
    <div class="status-pill"><span class="pulse-dot"></span>MONITORING</div>
    <div class="radar"><div class="radar-ring"></div></div>
    {SKYLINE_SVG}
</div>
""", unsafe_allow_html=True)

# ============================================
# HERO KPI STRIP
# ============================================
_total = st.session_state.stats['total']
_critical = st.session_state.stats['critical']
_disaster = _critical + st.session_state.stats['high'] + st.session_state.stats['medium']
_rate = int(_disaster / _total * 100) if _total else 0
_avg_scan_ms = f"{sum(st.session_state.scan_times_ms) / len(st.session_state.scan_times_ms):.1f}ms" if st.session_state.scan_times_ms else "—"

st.markdown(f"""
<div class="kpi-strip">
    <div class="kpi-card tilt" style="--kpi-glow:{AMBER};">
        <div class="kpi-label">Tweets Scanned</div>
        <div class="kpi-value" style="color:{TEXT};">{_total}</div>
        <div class="kpi-foot">this session</div>
    </div>
    <div class="kpi-card tilt" style="--kpi-glow:{CRITICAL};">
        <div class="kpi-label">Critical Alerts</div>
        <div class="kpi-value" style="color:{CRITICAL};">{_critical}</div>
        <div class="kpi-foot">require immediate response</div>
    </div>
    <div class="kpi-card tilt" style="--kpi-glow:{CYAN};">
        <div class="kpi-label">Disaster Rate</div>
        <div class="kpi-value" style="color:{CYAN};">{_rate}%</div>
        <div class="kpi-foot">{_disaster}/{_total if _total else 0} flagged</div>
    </div>
    <div class="kpi-card tilt" style="--kpi-glow:{SAFE};">
        <div class="kpi-label">Avg Scan Time</div>
        <div class="kpi-value" style="color:{SAFE};">{_avg_scan_ms}</div>
        <div class="kpi-foot">measured, this session</div>
    </div>
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

with st.expander("⚙️  How SENTINEL classifies a tweet — pipeline breakdown"):
    steps = [
        ("1. Ingest", "Raw tweet text comes in from the input box, batch paste, or (in a live deployment) a streaming API."),
        ("2. Keyword Match", f"Text is scanned against a {len(DISASTER_WORDS)}-term dictionary using word-boundary regex, so 'fire' won't false-positive on 'fireplace', and multi-word phrases like 'gas leak' are matched as whole phrases."),
        ("3. Severity Scoring", "Each matched term carries a severity weight (Critical/High/Medium). The tweet inherits its highest-weight match, and a weighted sum drives the confidence score."),
        ("4. Location Extraction", "A city/country gazetteer is checked against the text and, if matched, plotted on a map using known coordinates."),
        ("5. Action Recommendation", "Severity maps to a suggested response tier — this is a decision-support signal, not an automated dispatch."),
        ("6. ML Cross-Check", "Independently, a small TF-IDF + Logistic Regression model — trained on hand-labeled examples, including paraphrased disaster reports with no exact keyword — scores the same text. It's shown as a second opinion, especially useful for catching wording the keyword list misses, or flagging keyword false-positives like 'my exam was a disaster.'"),
    ]
    for title, desc in steps:
        st.markdown(f"**{title}** — {desc}")
    st.caption("Two independent layers, by design: the keyword engine is fast and fully explainable (every flag traces to an exact term); the ML layer generalizes to paraphrasing but is a statistical model trained on a small internal dataset, not production-scale. See 'ML Verification Layer' in the Analytics tab for real evaluation metrics.")

tab1, tab2, tab3, tab4 = st.tabs(["📝  SINGLE TWEET", "📋  BATCH", "📊  ANALYTICS", "📜  HISTORY"])

# ============================================
# TAB 1: SINGLE TWEET
# ============================================
with tab1:
    EXAMPLES = {
        "🔴 Critical": "BREAKING: Massive explosion and gas leak reported near downtown Karachi, multiple casualties feared, evacuation underway",
        "🟠 High": "7.2 magnitude earthquake hits Tokyo, buildings collapsed, rescue teams trapped residents",
        "🟡 Medium": "Heavy storm and flooding warning issued for Miami this weekend, residents advised to stay alert",
        "✅ Safe / joke": "my exam today was an absolute disaster lol I definitely failed 😭",
    }
    ex_cols = st.columns(len(EXAMPLES))
    for (label, sample), c in zip(EXAMPLES.items(), ex_cols):
        with c:
            if st.button(label, key=f"ex_{label}", use_container_width=True):
                st.session_state.example_fill = sample
                st.rerun()

    if st.session_state.example_fill is not None:
        st.session_state.tweet_input_value = st.session_state.example_fill
        st.session_state.example_fill = None

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
            _t0 = time.perf_counter()
            result = analyze_text(tweet_input)
            ml_score = ml_predict(tweet_input, ML_VECTORIZER, ML_MODEL)
            _elapsed_ms = (time.perf_counter() - _t0) * 1000
            st.session_state.scan_times_ms.append(_elapsed_ms)

        found = result['found']
        severity = result['severity']
        location = result['location']
        category = result['category']
        confidence = result['confidence']

        # ---- Final verdict: keyword engine + ML cross-check combined ----
        final_severity, verdict_note, final_confidence = resolve_verdict(found, severity, confidence, ml_score)
        final_flagged = final_severity is not None
        display_category = category or ('🤖 ML-Detected (Unclassified)' if verdict_note == 'ml_only_catch' else category)

        if final_flagged:
            st.session_state.stats[final_severity.lower()] += 1
            if found:
                st.session_state.all_keywords.extend(found)
            st.session_state.all_categories.append(display_category or 'Uncategorized')
        else:
            st.session_state.stats['safe'] += 1

        if location:
            st.session_state.all_locations.append(location)
        st.session_state.stats['total'] += 1

        st.session_state.history.insert(0, {
            'time': datetime.now().strftime('%H:%M:%S'),
            'tweet': tweet_input[:80],
            'result': final_severity if final_flagged else 'SAFE',
            'location': location or '—',
            'confidence': final_confidence,
            'category': display_category or 'Normal Conversation',
        })

        highlighted = highlight_text(tweet_input, found)
        st.markdown(f'<div class="tweet-preview">{highlighted}</div>', unsafe_allow_html=True)

        keyword_tags = "".join([f'<span class="tag">{k}</span>' for k in found]) if found else '—'
        breakdown_tags = "".join(
            f'<span class="tag" style="border-color:{SEVERITY_COLOR[DISASTER_WORDS[k][0]]}55; color:{SEVERITY_COLOR[DISASTER_WORDS[k][0]]};">{k} → {DISASTER_WORDS[k][0]}</span>'
            for k in found
        ) if found else ''

        if final_flagged:
            css_class = {"CRITICAL": "result-critical", "HIGH": "result-high", "MEDIUM": "result-medium"}[final_severity]
            color = SEVERITY_COLOR[final_severity]

            # Verdict headline + action adapt to whether the ML layer agreed,
            # downgraded, overrode, or independently caught this tweet.
            if verdict_note is None:
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}[final_severity]
                headline = f"{icon} {final_severity} — DISASTER DETECTED"
                action = {
                    "CRITICAL": "CALL 911 IMMEDIATELY",
                    "HIGH": "DISPATCH EMERGENCY SERVICES",
                    "MEDIUM": "MONITOR THE SITUATION",
                }[final_severity]
            elif verdict_note == 'override_false_positive':
                icon = "⚠️"
                headline = f"{icon} {final_severity} — KEYWORD MATCH OVERRIDDEN BY ML (LIKELY FALSE POSITIVE)"
                action = "FLAG FOR HUMAN REVIEW — ML MODEL STRONGLY DISAGREES WITH KEYWORD MATCH"
            elif verdict_note == 'soft_downgrade':
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}[final_severity]
                headline = f"{icon} {final_severity} — DOWNGRADED (ML LESS CONFIDENT THAN KEYWORDS SUGGEST)"
                action = "MONITOR THE SITUATION — HUMAN REVIEW SUGGESTED"
            else:  # ml_only_catch
                icon = "🤖"
                headline = f"{icon} {final_severity} — ML-DETECTED (NO KEYWORD MATCH)"
                action = "FLAG FOR HUMAN REVIEW — POSSIBLE PARAPHRASED REPORT"

            st.markdown(f"""
            <div class="result-card tilt fade-in-up {css_class}">
                <div class="result-head" style="color:{color};">{headline}</div>
                <div class="result-row"><span class="result-key">Category</span><span class="result-val">{display_category}</span></div>
                <div class="result-row"><span class="result-key">Keywords</span><span class="result-val">{keyword_tags}</span></div>
                <div class="result-row"><span class="result-key">Location</span><span class="result-val">{location if location else 'Unknown'}</span></div>
                <div class="result-row"><span class="result-key">Confidence</span>
                    <span class="result-val meter-wrap">
                        <span class="meter-track"><span class="meter-fill" style="--meter-pct:{final_confidence}%; background:{color};"></span></span>
                        <span class="meter-pct" style="color:{color};">{final_confidence}%</span>
                    </span>
                </div>
                <div class="action-line" style="background:{color}22; color:{color}; border:1px solid {color}55;">🚨 ACTION → {action}</div>
            </div>
            """, unsafe_allow_html=True)
            if breakdown_tags:
                st.markdown(f'<div style="margin:-6px 0 4px 4px; font-family:\'JetBrains Mono\',monospace; font-size:0.72rem; color:{TEXT_MUTED}; letter-spacing:0.5px;">WHY FLAGGED &nbsp;→&nbsp; {breakdown_tags}</div>', unsafe_allow_html=True)
            if location and location in CITY_COORDS:
                lat, lon = CITY_COORDS[location]
                map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                st.map(map_df, zoom=5, color=color)
        else:
            st.markdown(f"""
            <div class="result-card tilt fade-in-up result-safe">
                <div class="result-head" style="color:{SAFE};">✅ SAFE — NO DISASTER</div>
                <div class="result-row"><span class="result-key">Category</span><span class="result-val">Normal Conversation</span></div>
                <div class="result-row"><span class="result-key">Confidence</span>
                    <span class="result-val meter-wrap">
                        <span class="meter-track"><span class="meter-fill" style="--meter-pct:{final_confidence}%; background:{SAFE};"></span></span>
                        <span class="meter-pct" style="color:{SAFE};">{final_confidence}%</span>
                    </span>
                </div>
                <div class="action-line" style="background:{SAFE}1a; color:{SAFE}; border:1px solid {SAFE}55;">✅ No emergency response needed</div>
            </div>
            """, unsafe_allow_html=True)

        # ---- ML cross-check panel (shows the evidence behind the verdict above) ----
        ml_color = CRITICAL if ml_score >= 66 else (HIGH if ml_score >= 40 else SAFE)
        keyword_flagged = bool(found)
        ml_flagged = ml_score >= 50
        agree = keyword_flagged == ml_flagged
        if agree:
            agree_badge = f'<span style="color:{SAFE};">✓ AGREES with keyword engine</span>'
        elif verdict_note == 'override_false_positive':
            agree_badge = f'<span style="color:{AMBER};">⚠ DISAGREED with keyword engine — verdict above was overridden</span>'
        elif verdict_note == 'soft_downgrade':
            agree_badge = f'<span style="color:{AMBER};">⚠ PARTIALLY DISAGREED — verdict above was downgraded</span>'
        elif verdict_note == 'ml_only_catch':
            agree_badge = f'<span style="color:{CYAN};">⚠ CAUGHT what keywords missed — verdict above was upgraded</span>'
        else:
            agree_badge = f'<span style="color:{AMBER};">⚠ DISAGREES with keyword engine</span>'
        st.markdown(f"""
        <div class="result-card fade-in-up" style="border-left:4px solid {CYAN}; padding:18px 22px; margin-top:-4px;">
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; letter-spacing:1px; color:{CYAN}; text-transform:uppercase; margin-bottom:10px;">🤖 ML VERIFICATION LAYER · trained model, independent of keyword list</div>
            <div class="result-row"><span class="result-key">Disaster Probability</span>
                <span class="result-val meter-wrap">
                    <span class="meter-track"><span class="meter-fill" style="--meter-pct:{ml_score}%; background:{ml_color};"></span></span>
                    <span class="meter-pct" style="color:{ml_color};">{ml_score}%</span>
                </span>
            </div>
            <div class="result-row" style="font-size:0.82rem;"><span class="result-key">Cross-check</span><span class="result-val">{agree_badge}</span></div>
        </div>
        """, unsafe_allow_html=True)
        if verdict_note == 'ml_only_catch':
            st.warning("The ML model thinks this may be disaster-related even though it matched **no exact keywords** — likely a paraphrased report. Verdict above was upgraded for human review.")
        elif verdict_note == 'override_false_positive':
            st.info("Keywords matched, but the ML model rates this as unlikely to be a real disaster — verdict above was downgraded and flagged for human review instead of auto-dispatch.")
        elif verdict_note == 'soft_downgrade':
            st.info("Keywords matched, but the ML model was only partially convinced — verdict above was softened by one severity tier pending human review.")

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
                _t0 = time.perf_counter()
                r = analyze_text(tweet)
                r['ml_score'] = ml_predict(tweet, ML_VECTORIZER, ML_MODEL)
                # Combine keyword + ML into one final verdict, same logic as Single Tweet tab
                final_severity, verdict_note, final_confidence = resolve_verdict(
                    r['found'], r['severity'], r['confidence'], r['ml_score']
                )
                r['final_severity'] = final_severity
                r['verdict_note'] = verdict_note
                r['final_confidence'] = final_confidence
                st.session_state.scan_times_ms.append((time.perf_counter() - _t0) * 1000)
                batch_results.append({'tweet': tweet, **r})

            disaster_count = sum(1 for r in batch_results if r['final_severity'] is not None)
            safe_count = len(batch_results) - disaster_count
            critical_count = sum(1 for r in batch_results if r['final_severity'] == 'CRITICAL')
            ml_catch_count = sum(1 for r in batch_results if r['verdict_note'] == 'ml_only_catch')
            override_count = sum(1 for r in batch_results if r['verdict_note'] == 'override_false_positive')

            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("⚠️ Disaster", disaster_count)
            m2.metric("🔴 Critical", critical_count)
            m3.metric("✅ Safe", safe_count)
            m4.metric("📝 Total", len(lines))
            m5.metric("🤖 ML-only catches", ml_catch_count, help="Tweets the keyword engine marked SAFE but the trained ML model flagged as likely disaster-related — probable paraphrases. Verdict upgraded for review.")
            m6.metric("⚠️ ML overrides", override_count, help="Tweets that matched a keyword but the ML model strongly disagreed — verdict downgraded, flagged as likely false positives instead of auto-dispatch.")

            st.write("")
            for r in batch_results:
                final_severity = r['final_severity']
                verdict_note = r['verdict_note']
                if final_severity is not None and verdict_note is None:
                    color = SEVERITY_COLOR[final_severity]
                    badge = f'<span class="hist-badge" style="background:{color}22; color:{color};">{final_severity}</span>'
                    loc = f' · 📍 {r["location"]}' if r['location'] else ''
                    keywords = ", ".join(r['found'][:4])
                    ml_tag = f' <span style="color:{CYAN}; font-size:0.68rem;">🤖 {r["ml_score"]}%</span>'
                    st.markdown(
                        f'<div class="hist-row" style="grid-template-columns: 110px 1fr 150px;">'
                        f'{badge}<span>{highlight_text(r["tweet"][:90], r["found"])}{loc}</span>'
                        f'<span style="color:{TEXT_MUTED}; font-size:0.72rem;">{keywords}{ml_tag}</span></div>',
                        unsafe_allow_html=True
                    )
                elif verdict_note == 'ml_only_catch':
                    st.markdown(
                        f'<div class="hist-row" style="grid-template-columns: 110px 1fr 150px; border-color:{CYAN}66;">'
                        f'<span class="hist-badge" style="background:{CYAN}22; color:{CYAN};">🤖 ML CATCH</span>'
                        f'<span>{r["tweet"][:90]}</span>'
                        f'<span style="color:{CYAN}; font-size:0.72rem;">{r["ml_score"]}% disaster-likely, no keyword match</span></div>',
                        unsafe_allow_html=True
                    )
                elif verdict_note == 'override_false_positive':
                    st.markdown(
                        f'<div class="hist-row" style="grid-template-columns: 110px 1fr 150px; border-color:{AMBER}66;">'
                        f'<span class="hist-badge" style="background:{AMBER}22; color:{AMBER};">⚠ ML OVERRIDE</span>'
                        f'<span>{highlight_text(r["tweet"][:90], r["found"])}</span>'
                        f'<span style="color:{AMBER}; font-size:0.72rem;">keyword hit, but ML only {r["ml_score"]}% — likely false positive</span></div>',
                        unsafe_allow_html=True
                    )
                elif verdict_note == 'soft_downgrade':
                    color = SEVERITY_COLOR[final_severity]
                    st.markdown(
                        f'<div class="hist-row" style="grid-template-columns: 110px 1fr 150px; border-color:{color}66;">'
                        f'<span class="hist-badge" style="background:{color}22; color:{color};">{final_severity} ↓</span>'
                        f'<span>{highlight_text(r["tweet"][:90], r["found"])}</span>'
                        f'<span style="color:{TEXT_MUTED}; font-size:0.72rem;">downgraded — ML {r["ml_score"]}%</span></div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="hist-row" style="grid-template-columns: 110px 1fr 150px;">'
                        f'<span class="hist-badge" style="background:{SAFE}22; color:{SAFE};">SAFE</span>'
                        f'<span>{r["tweet"][:90]}</span><span></span></div>',
                        unsafe_allow_html=True
                    )

            # push batch results into global stats/history too, so Analytics & History stay consistent
            for r in batch_results:
                final_severity = r['final_severity']
                display_category = r['category'] or ('🤖 ML-Detected (Unclassified)' if r['verdict_note'] == 'ml_only_catch' else r['category'])
                if final_severity is not None:
                    st.session_state.stats[final_severity.lower()] += 1
                    if r['found']:
                        st.session_state.all_keywords.extend(r['found'])
                    st.session_state.all_categories.append(display_category or 'Uncategorized')
                else:
                    st.session_state.stats['safe'] += 1
                if r['location']:
                    st.session_state.all_locations.append(r['location'])
                st.session_state.stats['total'] += 1
                st.session_state.history.insert(0, {
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'tweet': r['tweet'][:80],
                    'result': final_severity if final_severity is not None else 'SAFE',
                    'location': r['location'] or '—',
                    'confidence': r['final_confidence'],
                    'category': display_category or 'Normal Conversation',
                })

            st.write("")
            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(['Tweet', 'Final Verdict', 'Verdict Note', 'Category', 'Location', 'Confidence', 'Keywords', 'ML Disaster Probability %'])
            for r in batch_results:
                writer.writerow([
                    r['tweet'],
                    r['final_severity'] if r['final_severity'] is not None else 'SAFE',
                    r['verdict_note'] or 'agrees',
                    r['category'] or '—', r['location'] or '—', r['final_confidence'],
                    ", ".join(r['found']), r['ml_score']
                ])
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
                wedges, _, autotexts = ax1.pie(
                    sizes, colors=colors, autopct='%1.0f%%', pctdistance=0.82, startangle=90,
                    textprops={'color': BG, 'fontsize': 9, 'fontweight': 'bold'},
                    wedgeprops={'edgecolor': SURFACE, 'linewidth': 3, 'width': 0.42}
                )
                # center label — donut hole shows the total count
                ax1.text(0, 0.08, str(sum(sizes)), ha='center', va='center',
                          color=TEXT, fontsize=22, fontweight='bold', family='sans-serif')
                ax1.text(0, -0.18, 'SCANNED', ha='center', va='center',
                          color=TEXT_MUTED, fontsize=8, family='monospace')
                ax1.legend(wedges, labels, loc='upper center', bbox_to_anchor=(0.5, 0.02),
                           ncol=len(labels), frameon=False, labelcolor=TEXT_MUTED, fontsize=8)
                ax1.set_title('Severity Distribution', color=TEXT, fontsize=12, fontweight='bold', pad=12)
                fig1.tight_layout()
                st.pyplot(fig1)

        with col2:
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            fig2.patch.set_facecolor(SURFACE)
            ax2.set_facecolor(SURFACE)
            categories_x = ['Critical', 'High', 'Medium', 'Safe']
            values = [st.session_state.stats['critical'], st.session_state.stats['high'], st.session_state.stats['medium'], st.session_state.stats['safe']]
            bar_colors = [CRITICAL, HIGH, MEDIUM, SAFE]
            ax2.grid(axis='y', color=BORDER_MPL, linewidth=0.8, zorder=0)
            ax2.set_axisbelow(True)
            bars = ax2.bar(categories_x, values, color=bar_colors, width=0.58,
                            edgecolor=SURFACE, linewidth=1.5, zorder=3)
            ax2.set_title('Disaster Severity', color=TEXT, fontsize=12, fontweight='bold', pad=12)
            for spine in ['top', 'right']:
                ax2.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']:
                ax2.spines[spine].set_color(BORDER_MPL)
            ax2.tick_params(colors=TEXT_MUTED, labelsize=9)
            for bar, val, c in zip(bars, values, bar_colors):
                if val > 0:
                    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.03,
                              str(val), ha='center', color=c, fontweight='bold', fontsize=10)
            fig2.tight_layout()
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

    st.write("")
    st.markdown("##### 🤖 ML Verification Layer — Model Evaluation")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accuracy", f"{ML_METRICS['accuracy']*100:.0f}%")
    m2.metric("Precision", f"{ML_METRICS['precision']*100:.0f}%")
    m3.metric("Recall", f"{ML_METRICS['recall']*100:.0f}%")
    m4.metric("F1 Score", f"{ML_METRICS['f1']*100:.0f}%")
    st.caption(
        f"TF-IDF + Logistic Regression, trained on {ML_METRICS['train_size']} examples, "
        f"validated on a held-out set of {ML_METRICS['test_size']} examples never seen during training. "
        f"⚠️ Small, hand-labeled internal dataset — treat as a sanity check, not a production benchmark. "
        f"Swap in a larger public dataset (e.g. the 'Real or Not? NLP with Disaster Tweets' dataset) to strengthen this."
    )

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
            st.session_state.scan_times_ms = []
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
