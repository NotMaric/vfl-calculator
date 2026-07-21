import streamlit as st

st.set_page_config(page_title="VFL Points Calculator", page_icon="🎯", layout="centered")

# ---------------------------------------------------------------------------
# Styling — tactical HUD look: near-black background, signature red accent,
# angular (non-rounded) panels, condensed display type + monospace stats.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }

.stApp { background-color: #0F1923; }

/* Hero */
.vfl-hero { margin-bottom: 0.25rem; }
.vfl-hero .eyebrow {
    font-family: 'JetBrains Mono', monospace;
    color: #FF4655;
    letter-spacing: 0.3em;
    font-size: 0.75rem;
    font-weight: 700;
}
.vfl-hero h1 {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700;
    font-size: 3rem;
    letter-spacing: 0.02em;
    color: #ECE8E1;
    margin: 0.1rem 0 0.3rem 0;
    line-height: 1;
}
.vfl-hero .accent-bar {
    width: 64px; height: 4px; background: #FF4655;
    clip-path: polygon(0 0, 100% 0, 88% 100%, 0% 100%);
    margin-bottom: 0.6rem;
}
.vfl-hero p { color: #8B978F; font-size: 0.95rem; margin: 0; }

/* Section labels */
.vfl-section-label {
    font-family: 'JetBrains Mono', monospace;
    color: #FF4655;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    border-left: 3px solid #FF4655;
    padding-left: 0.5rem;
    margin: 1.6rem 0 0.6rem 0;
}

/* Bordered containers -> angular panels, no rounded corners */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 0px !important;
    border: 1px solid #2A3644 !important;
    background-color: #151F29;
}

/* Inputs */
.stTextInput input, .stNumberInput input {
    background-color: #0F1923 !important;
    border: 1px solid #2A3644 !important;
    border-radius: 0px !important;
    color: #ECE8E1 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #FF4655 !important;
    box-shadow: none !important;
}
label { color: #8B978F !important; font-weight: 600 !important; font-size: 0.85rem !important; }

/* Radio / selectbox */
div[data-baseweb="select"] > div {
    background-color: #0F1923 !important;
    border-radius: 0px !important;
    border: 1px solid #2A3644 !important;
}

/* Buttons */
.stButton button {
    background-color: #FF4655 !important;
    color: #0F1923 !important;
    border: none !important;
    border-radius: 0px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1rem !important;
    clip-path: polygon(0 0, 100% 0, 100% 70%, 97% 100%, 0 100%);
}
.stButton button:hover { background-color: #FF6B76 !important; }

/* Scoreboard metrics */
div[data-testid="stMetric"] {
    background-color: #151F29;
    border: 1px solid #2A3644;
    padding: 0.9rem 0.5rem;
    text-align: center;
}
div[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    color: #8B978F !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    justify-content: center !important;
}
div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    color: #ECE8E1 !important;
    justify-content: center !important;
}

hr { border-color: #2A3644 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown("""
<div class="vfl-hero">
    <div class="eyebrow">VALORANT FANTASY LEAGUE</div>
    <h1>POINTS CALCULATOR</h1>
    <div class="accent-bar"></div>
    <p>Enter a player's match stats to tally their weekly score.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Player + maps won
# ---------------------------------------------------------------------------
st.markdown('<div class="vfl-section-label">PLAYER</div>', unsafe_allow_html=True)
with st.container(border=True):
    Name = st.text_input("Player's name")

    match_format = st.selectbox("Match format", ["Bo3", "Bo5"])
    max_wins = 2 if match_format == "Bo3" else 3

    col1, col2 = st.columns(2)
    with col1:
        A_Map = st.selectbox("Maps won", options=list(range(0, max_wins + 1)))
    with col2:
        B_Map = st.selectbox("Opponent's maps won", options=list(range(0, max_wins + 1)))

maps_to_process = A_Map + B_Map

if maps_to_process == 0:
    st.info("Enter maps won by each side to continue.")
    st.stop()

map_points = A_Map
kill_points = 0
bonus_points = 0

if B_Map == 0 and A_Map == 2:
    map_points += 2
elif B_Map == 0 and A_Map == 3:
    map_points += 4
elif B_Map == 1 and A_Map == 3:
    map_points += 1

# ---------------------------------------------------------------------------
# Per-map stats
# ---------------------------------------------------------------------------
map_stats = []
for i in range(1, maps_to_process + 1):
    st.markdown(f'<div class="vfl-section-label">MAP 0{i}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            kills = st.number_input(f"Kills", min_value=0, value=0, step=1, key=f"kills_{i}")
            fourk = st.number_input(f"4k's", min_value=0, value=0, step=1, key=f"fourk_{i}")
            fivek = st.number_input(f"5k's", min_value=0, value=0, step=1, key=f"fivek_{i}")
        with c2:
            rnd_diff = st.number_input(
                f"Round differential", min_value=-13, max_value=13, value=0, step=1, key=f"rnd_{i}",
                help=f"{Name or 'Player'}'s team rounds minus enemy team rounds. Negative if they lost."
            )
            sixk = st.number_input(f"6k's", min_value=0, value=0, step=1, key=f"sixk_{i}")
            sevenk = st.number_input(f"7k's", min_value=0, value=0, step=1, key=f"sevenk_{i}")

    map_stats.append({
        "kills": kills, "rnd_diff": rnd_diff,
        "fourk": fourk, "fivek": fivek, "sixk": sixk, "sevenk": sevenk
    })

# ---------------------------------------------------------------------------
# VLR rating bonus
# ---------------------------------------------------------------------------
st.markdown('<div class="vfl-section-label">MATCH RATING</div>', unsafe_allow_html=True)
with st.container(border=True):
    vlr = st.number_input("VLR rating for the match", min_value=0.0, value=1.0, step=0.01, format="%.2f")
    top3 = st.radio("Top 3 in VLR rating for the match?", ["No", "Yes"], horizontal=True)
    pos = None
    if top3 == "Yes":
        pos = st.selectbox("Position (1, 2 or 3)", [1, 2, 3])

st.write("")

# ---------------------------------------------------------------------------
# Calculate
# ---------------------------------------------------------------------------
if st.button("Calculate Points", type="primary"):
    for stats in map_stats:
        kills = stats["kills"]
        rnd_diff = stats["rnd_diff"]
        fourk = stats["fourk"]
        fivek = stats["fivek"]
        sixk = stats["sixk"]
        sevenk = stats["sevenk"]

        if kills == 0:
            kill_points -= 3
        elif kills < 5:
            kill_points -= 1
        else:
            k = kills - 10
            while k >= 0:
                kill_points += 1
                k -= 5

        if rnd_diff == 13:
            map_points += 5
        elif rnd_diff == -13:
            map_points -= 5
        elif rnd_diff > 9:
            map_points += 2
        elif rnd_diff > 4:
            map_points += 1
        elif rnd_diff < -9:
            map_points -= 1

        kill_points += fourk
        kill_points += fivek * 3
        kill_points += sixk * 5
        kill_points += sevenk * 10

    if top3 == "Yes" and pos is not None:
        if pos == 1:
            bonus_points += 3
        elif pos == 2:
            bonus_points += 2
        elif pos == 3:
            bonus_points += 1

    if vlr >= 2:
        bonus_points += 3
    elif vlr >= 1.75:
        bonus_points += 2
    elif vlr >= 1.5:
        bonus_points += 1

    points = kill_points + map_points + bonus_points

    st.markdown(f'<div class="vfl-section-label">RESULT — {(Name or "PLAYER").upper()}</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kill Pts", kill_points)
    m2.metric("Map Pts", map_points)
    m3.metric("Bonus Pts", bonus_points)
    m4.metric("Total", points)    clip-path: polygon(0 0, 100% 0, 88% 100%, 0% 100%);
    margin-bottom: 0.6rem;
}
.vfl-hero p { color: #8B978F; font-size: 0.95rem; margin: 0; }

/* Section labels */
.vfl-section-label {
    font-family: 'JetBrains Mono', monospace;
    color: #FF4655;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    border-left: 3px solid #FF4655;
    padding-left: 0.5rem;
    margin: 1.6rem 0 0.6rem 0;
}

/* Bordered containers -> angular panels, no rounded corners */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 0px !important;
    border: 1px solid #2A3644 !important;
    background-color: #151F29;
}

/* Inputs */
.stTextInput input, .stNumberInput input {
    background-color: #0F1923 !important;
    border: 1px solid #2A3644 !important;
    border-radius: 0px !important;
    color: #ECE8E1 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #FF4655 !important;
    box-shadow: none !important;
}
label { color: #8B978F !important; font-weight: 600 !important; font-size: 0.85rem !important; }

/* Radio / selectbox */
div[data-baseweb="select"] > div {
    background-color: #0F1923 !important;
    border-radius: 0px !important;
    border: 1px solid #2A3644 !important;
}

/* Buttons */
.stButton button {
    background-color: #FF4655 !important;
    color: #0F1923 !important;
    border: none !important;
    border-radius: 0px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1rem !important;
    clip-path: polygon(0 0, 100% 0, 100% 70%, 97% 100%, 0 100%);
}
.stButton button:hover { background-color: #FF6B76 !important; }

/* Scoreboard metrics */
div[data-testid="stMetric"] {
    background-color: #151F29;
    border: 1px solid #2A3644;
    padding: 0.9rem 0.5rem;
    text-align: center;
}
div[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    color: #8B978F !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    justify-content: center !important;
}
div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    color: #ECE8E1 !important;
    justify-content: center !important;
}

hr { border-color: #2A3644 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown("""
<div class="vfl-hero">
    <div class="eyebrow">VALORANT FANTASY LEAGUE</div>
    <h1>POINTS CALCULATOR</h1>
    <div class="accent-bar"></div>
    <p>Enter a player's match stats to tally their weekly score.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Player + maps won
# ---------------------------------------------------------------------------
st.markdown('<div class="vfl-section-label">PLAYER</div>', unsafe_allow_html=True)
with st.container(border=True):
    Name = st.text_input("Player's name")
    col1, col2 = st.columns(2)
    with col1:
        A_Map = st.number_input("Maps won", min_value=0, max_value=3, value=0, step=1)
    with col2:
        B_Map = st.number_input("Opponent's maps won", min_value=0, max_value=3, value=0, step=1)

maps_to_process = A_Map + B_Map

if maps_to_process == 0:
    st.info("Enter maps won by each side to continue.")
    st.stop()

map_points = A_Map
kill_points = 0
bonus_points = 0

if B_Map == 0 and A_Map == 2:
    map_points += 2
elif B_Map == 0 and A_Map == 3:
    map_points += 4
elif B_Map == 1 and A_Map == 3:
    map_points += 1

# ---------------------------------------------------------------------------
# Per-map stats
# ---------------------------------------------------------------------------
map_stats = []
for i in range(1, maps_to_process + 1):
    st.markdown(f'<div class="vfl-section-label">MAP 0{i}</div>', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            kills = st.number_input(f"Kills", min_value=0, value=0, step=1, key=f"kills_{i}")
            fourk = st.number_input(f"4k's", min_value=0, value=0, step=1, key=f"fourk_{i}")
            fivek = st.number_input(f"5k's", min_value=0, value=0, step=1, key=f"fivek_{i}")
        with c2:
            rnd_diff = st.number_input(
                f"Round differential", min_value=-13, max_value=13, value=0, step=1, key=f"rnd_{i}",
                help=f"{Name or 'Player'}'s team rounds minus enemy team rounds. Negative if they lost."
            )
            sixk = st.number_input(f"6k's", min_value=0, value=0, step=1, key=f"sixk_{i}")
            sevenk = st.number_input(f"7k's", min_value=0, value=0, step=1, key=f"sevenk_{i}")

    map_stats.append({
        "kills": kills, "rnd_diff": rnd_diff,
        "fourk": fourk, "fivek": fivek, "sixk": sixk, "sevenk": sevenk
    })

# ---------------------------------------------------------------------------
# VLR rating bonus
# ---------------------------------------------------------------------------
st.markdown('<div class="vfl-section-label">MATCH RATING</div>', unsafe_allow_html=True)
with st.container(border=True):
    vlr = st.number_input("VLR rating for the match", min_value=0.0, value=1.0, step=0.01, format="%.2f")
    top3 = st.radio("Top 3 in VLR rating for the match?", ["No", "Yes"], horizontal=True)
    pos = None
    if top3 == "Yes":
        pos = st.selectbox("Position (1, 2 or 3)", [1, 2, 3])

st.write("")

# ---------------------------------------------------------------------------
# Calculate
# ---------------------------------------------------------------------------
if st.button("Calculate Points", type="primary"):
    for stats in map_stats:
        kills = stats["kills"]
        rnd_diff = stats["rnd_diff"]
        fourk = stats["fourk"]
        fivek = stats["fivek"]
        sixk = stats["sixk"]
        sevenk = stats["sevenk"]

        if kills == 0:
            kill_points -= 3
        elif kills < 5:
            kill_points -= 1
        else:
            k = kills - 10
            while k >= 0:
                kill_points += 1
                k -= 5

        if rnd_diff == 13:
            map_points += 5
        elif rnd_diff == -13:
            map_points -= 5
        elif rnd_diff > 9:
            map_points += 2
        elif rnd_diff > 4:
            map_points += 1
        elif rnd_diff < -9:
            map_points -= 1

        kill_points += fourk
        kill_points += fivek * 3
        kill_points += sixk * 5
        kill_points += sevenk * 10

    if top3 == "Yes" and pos is not None:
        if pos == 1:
            bonus_points += 3
        elif pos == 2:
            bonus_points += 2
        elif pos == 3:
            bonus_points += 1

    if vlr >= 2:
        bonus_points += 3
    elif vlr >= 1.75:
        bonus_points += 2
    elif vlr >= 1.5:
        bonus_points += 1

    points = kill_points + map_points + bonus_points

    st.markdown(f'<div class="vfl-section-label">RESULT — {(Name or "PLAYER").upper()}</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Kill Pts", kill_points)
    m2.metric("Map Pts", map_points)
    m3.metric("Bonus Pts", bonus_points)
    m4.metric("Total", points)
