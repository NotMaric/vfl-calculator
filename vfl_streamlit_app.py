import subprocess
import sys
import streamlit as st
from vlr_scraper import get_player_match_data

st.set_page_config(page_title="VFL Points Calculator", page_icon="🎯", layout="centered")


@st.cache_resource
def _ensure_playwright_browser():
    """
    vlr.gg loads its stats with JavaScript, so we need a real (headless)
    browser to scrape it — Playwright doesn't ship one by default, so we
    install it once per app instance and cache the result so it doesn't
    re-download on every interaction. Using `sys.executable -m playwright`
    instead of the bare `playwright` command avoids PATH issues — it always
    calls the same Python environment this script is running under.
    """
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


with st.spinner("Setting up browser for VLR.gg fetching (first load only)..."):
    _ensure_playwright_browser()

# ---------------------------------------------------------------------------
# Styling — tactical HUD look: near-black background, signature red accent,
# angular (non-rounded) panels, condensed display type + monospace stats.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }

.stApp { background-color: #0A0E14; }

/* Hero */
.vfl-hero { margin-bottom: 0.25rem; }
.vfl-hero .eyebrow {
    font-family: 'JetBrains Mono', monospace;
    color: #FF4D61;
    letter-spacing: 0.3em;
    font-size: 0.75rem;
    font-weight: 700;
}
.vfl-hero h1 {
    font-family: 'Anton', sans-serif;
    font-weight: 400;
    font-size: 3.1rem;
    letter-spacing: 0.01em;
    color: #ECE8E1;
    margin: 0.1rem 0 0.3rem 0;
    line-height: 1;
    text-transform: uppercase;
}
.vfl-hero .accent-bar {
    width: 64px; height: 4px; background: #FF4D61;
    clip-path: polygon(0 0, 100% 0, 88% 100%, 0% 100%);
    margin-bottom: 0.6rem;
}
.vfl-hero p { color: #8B978F; font-size: 0.95rem; margin: 0; }

/* Section labels — mirrors VFL's "// DATABASE FILTER" convention */
.vfl-section-label {
    font-family: 'JetBrains Mono', monospace;
    color: #FF4D61;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    border-left: 3px solid #FF4D61;
    padding-left: 0.5rem;
    margin: 1.6rem 0 0.6rem 0;
}
.vfl-section-label::before { content: "// "; opacity: 0.7; }

/* Bordered containers -> angular panels, no rounded corners */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 0px !important;
    border: 1px solid #212836 !important;
    background-color: #10141D;
}

/* Inputs */
.stTextInput input, .stNumberInput input {
    background-color: #0A0E14 !important;
    border: 1px solid #212836 !important;
    border-radius: 0px !important;
    color: #ECE8E1 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #FF4D61 !important;
    box-shadow: none !important;
}
label { color: #8B978F !important; font-weight: 600 !important; font-size: 0.85rem !important; }

/* Radio / selectbox */
div[data-baseweb="select"] > div {
    background-color: #0A0E14 !important;
    border-radius: 0px !important;
    border: 1px solid #212836 !important;
}

/* Buttons — outlined style, matching VFL's TRANSFER/MANAGE buttons */
.stButton button {
    background-color: transparent !important;
    color: #FF4D61 !important;
    border: 1px solid #FF4D61 !important;
    border-radius: 0px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1rem !important;
}
.stButton button:hover {
    background-color: rgba(255, 77, 97, 0.1) !important;
    color: #FF6B7D !important;
    border-color: #FF6B7D !important;
}

/* Scoreboard metrics */
div[data-testid="stMetric"] {
    background-color: #10141D;
    border: 1px solid #212836;
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

/* Alert banners — mirrors VFL's "[!] SYSTEM ALERTS" bracket convention */
div[data-testid="stAlert"] {
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 0px !important;
}

hr { border-color: #212836 !important; }
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
# Auto-fill from VLR.gg
# ---------------------------------------------------------------------------
st.markdown('<div class="vfl-section-label">AUTO-FILL FROM VLR.GG</div>', unsafe_allow_html=True)
with st.container(border=True):
    vlr_url = st.text_input("VLR.gg match URL", placeholder="> https://www.vlr.gg/12345/team-a-vs-team-b-...")
    vlr_player = st.text_input("Player name (as shown on VLR.gg)", placeholder="> e.g. Alfajer")
    fetch_clicked = st.button("Fetch Stats from VLR.gg")

    if fetch_clicked:
        if not vlr_url or not vlr_player:
            st.warning("Enter both a match URL and a player name first.")
        else:
            with st.spinner("Fetching from VLR.gg — this can take 15–30 seconds..."):
                try:
                    data = get_player_match_data(vlr_url, vlr_player, include_multikills=True)
                    maps = data["maps"]
                    overall_rating = data["overall_rating"]

                    if not maps:
                        st.error(f"Couldn't find '{vlr_player}' in that match. Double check the name and URL.")
                    else:
                        num_maps = len(maps)
                        st.session_state["match_format_select"] = "Bo5" if num_maps > 3 else "Bo3"

                        wins = sum(1 for m in maps if m["rnd_diff"] > 0)
                        losses = sum(1 for m in maps if m["rnd_diff"] < 0)
                        st.session_state["a_map_select"] = wins
                        st.session_state["b_map_select"] = losses
                        st.session_state["name_input"] = vlr_player

                        if overall_rating is not None:
                            st.session_state["vlr_rating_input"] = float(overall_rating)

                        for m in maps:
                            idx = m["map_num"]
                            st.session_state[f"kills_{idx}"] = m["kills"]
                            st.session_state[f"rnd_{idx}"] = max(-13, min(13, m["rnd_diff"]))
                            st.session_state[f"fourk_{idx}"] = m["fourk"]
                            st.session_state[f"fivek_{idx}"] = m["fivek"]
                            st.session_state[f"sixk_{idx}"] = m["sixk"]
                            st.session_state[f"sevenk_{idx}"] = m["sevenk"]

                        st.success(f"Fetched {num_maps} map(s) for {vlr_player}. Review below, then calculate.")
                except Exception as e:
                    st.error(f"Fetch failed: {e}")

st.caption(
    "Note: 'Top 3 in VLR rating' and multi-kills beyond 5K still need to be entered "
    "manually — vlr.gg doesn't publish either of those in a scrapable form."
)

# ---------------------------------------------------------------------------
# Player + maps won
# ---------------------------------------------------------------------------
st.markdown('<div class="vfl-section-label">PLAYER</div>', unsafe_allow_html=True)
with st.container(border=True):
    Name = st.text_input("Player's name", key="name_input")

    match_format = st.selectbox("Match format", ["Bo3", "Bo5"], key="match_format_select")
    max_wins = 2 if match_format == "Bo3" else 3

    col1, col2 = st.columns(2)
    with col1:
        A_Map = st.selectbox("Maps won", options=list(range(0, max_wins + 1)), key="a_map_select")
    with col2:
        B_Map = st.selectbox("Opponent's maps won", options=list(range(0, max_wins + 1)), key="b_map_select")

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
            st.session_state.setdefault(f"kills_{i}", 0)
            st.session_state.setdefault(f"fourk_{i}", 0)
            st.session_state.setdefault(f"fivek_{i}", 0)
            kills = st.number_input("Kills", min_value=0, step=1, key=f"kills_{i}")
            fourk = st.number_input("4k's", min_value=0, step=1, key=f"fourk_{i}")
            fivek = st.number_input("5k's", min_value=0, step=1, key=f"fivek_{i}")
        with c2:
            st.session_state.setdefault(f"rnd_{i}", 0)
            st.session_state.setdefault(f"sixk_{i}", 0)
            st.session_state.setdefault(f"sevenk_{i}", 0)
            rnd_diff = st.number_input(
                "Round differential", min_value=-13, max_value=13, step=1, key=f"rnd_{i}",
                help=f"{Name or 'Player'}'s team rounds minus enemy team rounds. Negative if they lost."
            )
            sixk = st.number_input("6k's", min_value=0, step=1, key=f"sixk_{i}")
            sevenk = st.number_input("7k's", min_value=0, step=1, key=f"sevenk_{i}")

    map_stats.append({
        "kills": kills, "rnd_diff": rnd_diff,
        "fourk": fourk, "fivek": fivek, "sixk": sixk, "sevenk": sevenk
    })

# ---------------------------------------------------------------------------
# VLR rating bonus
# ---------------------------------------------------------------------------
st.markdown('<div class="vfl-section-label">MATCH RATING</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.session_state.setdefault("vlr_rating_input", 1.0)
    vlr = st.number_input("VLR rating for the match", min_value=0.0, step=0.01, format="%.2f", key="vlr_rating_input")
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
