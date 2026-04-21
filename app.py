import streamlit as st
import requests
import pandas as pd
import math
import json

ODDS_KEY = "6dd0250f16fcdb5ce63e02aceebfaeca"

st.set_page_config(layout="wide")
st.title("💎 Diamond EV+ (Statcast Edition)")

# ===== LOAD STATCAST =====
with open("statcast.json") as f:
    statcast = json.load(f)

sc_map = {p["player_name"]: p for p in statcast}

# ===== HELPERS =====
def clamp(v, mn, mx):
    return max(mn, min(mx, v))

def prob(s):
    return clamp((1/(1+math.exp(-5*(s-0.5))))*0.35, 0.01, 0.4)

# ===== STATCAST MODEL =====
def score(p):
    s = 0
    s += 0.45 * p["xiso"]
    s += 0.15 * p["xslg"]
    s += 0.10 * (p["exit_velocity_avg"]/100)
    s += 0.08 * p["barrel_batted_rate"]
    s += 0.07 * (p["hard_hit_percent"]/100)
    s += 0.05 * (p["sweet_spot_percent"]/100)
    return s

# ===== FETCH MLB GAMES =====
@st.cache_data(ttl=60)
def get_games():
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
        data = requests.get(url).json()
        return data.get("dates", [{}])[0].get("games", [])
    except:
        return []

games = get_games()

players = []

# ===== MAIN LOOP =====
if not games:
    st.warning("No live MLB games found today")
else:
    for g in games:
        for team in [g["teams"]["home"]["team"], g["teams"]["away"]["team"]]:

            roster = requests.get(
                f"https://statsapi.mlb.com/api/v1/teams/{team['id']}/roster"
            ).json().get("roster", [])[:6]

            for pl in roster:

                name = pl["person"]["fullName"]

                sc = sc_map.get(name)

                if not sc:
                    continue

                s = score(sc)
                p = prob(s)

                # temporary placeholder odds until props fixed
                odds = 3.0

                ev = (p * odds) - 1

                players.append({
                    "Player": name,
                    "Prob %": round(p*100,1),
                    "EV %": round(ev*100,2),
                    "Odds": odds
                })

# ===== DISPLAY =====
df = pd.DataFrame(players)

if df.empty:
    st.error("No Statcast players matched today's games")
else:
    df = df.sort_values("EV %", ascending=False)

    st.subheader("🔥 Top HR Plays (Statcast Model)")
    st.dataframe(df.head(15), use_container_width=True)