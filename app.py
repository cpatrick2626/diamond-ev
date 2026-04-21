import streamlit as st
import requests
import pandas as pd
import math

ODDS_KEY = "6dd0250f16fcdb5ce63e02aceebfaeca"

st.title("💎 Diamond EV+")

def clamp(v, mn, mx):
    return max(mn, min(mx, v))

def norm(v, mn, mx):
    return clamp((v - mn) / (mx - mn), 0, 1)

def score(p):
    return (
        0.5 * norm(p["iso"], 0.1, 0.35)
        + 0.3 * norm(p["hrRate"], 0.01, 0.1)
        - 0.1 * norm(p["k"], 0.1, 0.35)
    )

def prob(s):
    return clamp((1/(1+math.exp(-5*(s-0.5))))*0.35, 0.01, 0.4)

def get_games():
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
        data = requests.get(url).json()
        return data.get("dates", [{}])[0].get("games", [])
    except:
        return []

def get_odds():
    try:
        url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey={ODDS_KEY}&markets=h2h"
        data = requests.get(url).json()

        odds_map = {}
        for g in data:
            for b in g.get("bookmakers", []):
                for m in b.get("markets", []):
                    for o in m.get("outcomes", []):
                        odds_map[o["name"]] = int((o["price"]-1)*100)

        return odds_map
    except:
        return {}

players = []
games = get_games()
odds_map = get_odds()

# 🔥 fallback if APIs fail
if not games:
    st.warning("Using fallback data (API limit or error)")

    players = [
        {"Player":"Aaron Judge","Prob %":22.5,"EV %":10.2,"Odds":300},
        {"Player":"Shohei Ohtani","Prob %":21.0,"EV %":9.5,"Odds":280},
        {"Player":"Matt Olson","Prob %":19.2,"EV %":8.1,"Odds":260}
    ]

else:
    try:
        for g in games:
            for team in [g["teams"]["home"]["team"], g["teams"]["away"]["team"]]:

                roster = requests.get(
                    f"https://statsapi.mlb.com/api/v1/teams/{team['id']}/roster"
                ).json().get("roster", [])[:3]

                for pl in roster:

                    stats_data = requests.get(
                        f"https://statsapi.mlb.com/api/v1/people/{pl['person']['id']}/stats?stats=season"
                    ).json()

                    try:
                        s = stats_data["stats"][0]["splits"][0]["stat"]
                    except:
                        continue

                    avg = float(s.get("avg", 0.25))
                    slg = float(s.get("slg", 0.4))

                    stats = {
                        "iso": slg - avg,
                        "hrRate": (s.get("homeRuns",1)/(s.get("atBats",100))),
                        "k": (s.get("strikeOuts",1)/(s.get("atBats",100)))
                    }

                    sc = score(stats)
                    p = prob(sc)

                    odds = odds_map.get(pl["person"]["fullName"], 300)
                    ev = (p * (odds/100 + 1)) - 1

                    players.append({
                        "Player": pl["person"]["fullName"],
                        "Prob %": round(p*100,1),
                        "EV %": round(ev*100,2),
                        "Odds": odds
                    })

    except:
        st.warning("Partial data loaded")

df = pd.DataFrame(players)

if not df.empty:
    df = df.sort_values("EV %", ascending=False)
    st.dataframe(df.head(15), use_container_width=True)
else:
    st.error("No data available")