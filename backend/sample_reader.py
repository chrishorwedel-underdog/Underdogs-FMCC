"""Sample save reader: stands in for fmsave in the browser preview (no real FM saves here)."""
import random
from datetime import date

from roles import GK_ATTRS, OUTFIELD_ATTRS, SHARED_ATTRS

ALL_ATTRS = GK_ATTRS + OUTFIELD_ATTRS + SHARED_ATTRS
PROFILE = {
    "GK": GK_ATTRS + ["positioning", "decisions", "composure"],
    "CB": ["tackling", "marking", "heading", "positioning", "strength", "jumping_reach", "composure", "anticipation"],
    "FB": ["tackling", "marking", "pace", "stamina", "work_rate", "crossing", "acceleration", "positioning"],
    "DM": ["tackling", "positioning", "passing", "decisions", "composure", "anticipation", "work_rate", "stamina"],
    "CM": ["passing", "first_touch", "decisions", "vision", "stamina", "work_rate", "technique", "composure"],
    "AM": ["passing", "vision", "technique", "first_touch", "flair", "dribbling", "composure", "decisions"],
    "W": ["pace", "acceleration", "dribbling", "crossing", "technique", "flair", "off_the_ball", "first_touch"],
    "ST": ["finishing", "off_the_ball", "composure", "first_touch", "anticipation", "pace", "heading", "strength"],
}
GROUP = {"GK": "GK", "D (C)": "CB", "D (L)": "FB", "D (R)": "FB", "WB (L)": "FB", "WB (R)": "FB", "DM": "DM",
         "M (C)": "CM", "AM (C)": "AM", "AM (L)": "W", "AM (R)": "W", "ST": "ST"}
HOMEGROWN_NATIONS = {"England", "Scotland", "Ireland"}


def attributes(uid: int, positions: list, ca: int) -> dict:
    group = GROUP[positions[0]]
    base = 2 + ca / 200 * 13
    rng = random.Random(uid * 7)
    out = {}
    for a in ALL_ATTRS:
        noise = rng.uniform(-1.5, 1.5)
        if a in PROFILE[group]:
            v = base + 3.5 + noise
        elif group != "GK" and a in GK_ATTRS:
            v = 1 + abs(noise)
        elif group == "GK" and a in OUTFIELD_ATTRS:
            v = base - 5 + noise
        else:
            v = base - 1 + noise
        out[a] = int(max(1, min(20, round(v))))
    return out

READER_NAME = "Sample save reader"
SAMPLE_CLUB = "Sample Club FC"

# unique_id, name, birth, nationality, positions, ca, pa, monthly growth, monthly minutes, contract end, wage/wk, joins_at, leaves_at
SQUAD = [
    (20481101, "Tomas Varga", "1995-03-12", "Hungary", ["GK"], 148, 150, -0.3, 360, "2029-06-30", 32000, 0, None),
    (20481102, "Ben Okafor", "2004-09-02", "England", ["GK"], 112, 150, 1.2, 0, "2028-06-30", 6000, 0, None),
    (20481103, "Marco Silvestri", "1997-01-23", "Italy", ["D (C)"], 152, 154, 0.0, 360, "2028-06-30", 41000, 0, None),
    (20481104, "Jonas Lindqvist", "1998-07-30", "Sweden", ["D (C)"], 149, 151, 0.1, 340, "2030-06-30", 38000, 0, None),
    (20481105, "Luca Romano", "1998-04-11", "Italy", ["D (C)", "D (R)"], 138, 140, 0.0, 120, "2028-06-30", 22000, 0, None),
    (20481106, "Luca Romano", "2009-02-18", "Italy", ["D (C)"], 92, 158, 1.6, 45, "2030-06-30", 1500, 0, None),
    (20481107, "Kieran Doyle", "1999-11-05", "Ireland", ["D (R)"], 141, 143, 0.0, 330, "2029-06-30", 27000, 0, None),
    (20481108, "Rafael Mendes", "1994-05-19", "Portugal", ["D (L)"], 133, 136, -0.6, 300, "2028-06-30", 25000, 0, None),
    (20481109, "Noah Whitfield", "2007-12-01", "England", ["D (L)", "WB (L)"], 118, 162, 1.8, 150, "2029-06-30", 4500, 0, None),
    (20481110, "Ivan Petrović", "1996-08-14", "Croatia", ["DM", "M (C)"], 155, 156, 0.0, 360, "2029-06-30", 45000, 0, None),
    (20481111, "Samuel Adeyemi", "2008-03-27", "Nigeria", ["DM", "M (C)"], 124, 168, 2.0, 40, "2030-06-30", 5000, 0, None),
    (20481112, "Diego Alvarez", "1998-10-09", "Spain", ["M (C)"], 150, 152, 0.1, 350, "2028-06-30", 39000, 0, None),
    (20481113, "Felix Brandt", "1996-02-03", "Germany", ["M (C)", "AM (C)"], 147, 148, -0.1, 300, "2028-06-30", 36000, 0, None),
    (20481114, "Hugo Martin", "2000-06-21", "France", ["AM (C)", "M (C)"], 144, 150, 0.4, 220, "2029-06-30", 30000, 0, None),
    (20481115, "Arjun Mehta", "2007-01-15", "England", ["AM (C)", "AM (R)"], 116, 165, 1.7, 60, "2029-06-30", 3500, 0, None),
    (20481116, "Callum Reid", "1993-09-28", "Scotland", ["AM (L)", "ST"], 146, 147, -0.8, 280, "2028-06-30", 42000, 0, None),
    (20481117, "Yusuf Demir", "2001-04-04", "Turkey", ["AM (L)", "AM (R)"], 151, 155, 0.3, 340, "2030-06-30", 40000, 0, None),
    (20481118, "Matteo Ricci", "2006-11-30", "Italy", ["AM (R)"], 128, 160, 1.5, 200, "2029-06-30", 7000, 0, None),
    (20481119, "Oliver Hayes", "1997-12-17", "England", ["AM (R)"], 139, 141, 0.0, 120, "2028-06-30", 24000, 0, None),
    (20481120, "Erling Saetre", "1999-05-08", "Norway", ["ST"], 158, 160, 0.2, 360, "2030-06-30", 55000, 0, None),
    (20481121, "Kofi Mensah", "2006-07-12", "Ghana", ["ST"], 125, 163, 1.6, 90, "2029-06-30", 6500, 0, None),
    (20481122, "Pablo Navarro", "1992-01-29", "Spain", ["ST"], 140, 141, -1.0, 100, "2028-06-30", 33000, 0, 3),
    (20481123, "Theo Clarke", "2009-09-09", "England", ["M (C)"], 88, 155, 1.9, 30, "2031-06-30", 900, 0, None),
    (20481124, "Mateus Costa", "2008-05-05", "Brazil", ["AM (L)", "ST"], 110, 166, 2.1, 70, "2031-06-30", 2500, 3, None),
]

OPPONENTS = ["Northbridge Athletic", "Castleford Rovers", "Port Ellis United", "Kingsmere Town",
             "Redhill Albion", "Westvale City", "Harrow Bay FC", "Ashdown Wanderers"]


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    return date(d.year + m // 12, m % 12 + 1, 1)


def _age(birth: str, on: date) -> int:
    b = date.fromisoformat(birth)
    return on.year - b.year - ((on.month, on.day) < (b.month, b.day))


FIRST = {"Italy": ["Marco", "Luca", "Davide", "Andrea"], "Netherlands": ["Daan", "Sem", "Jesse", "Milan"], "Portugal": ["Rui", "Tiago", "Nuno", "Diogo"],
         "England": ["Jack", "Harry", "Mason", "Leo"], "Brazil": ["Caio", "Vitor", "Rafael", "Lucas"], "France": ["Hugo", "Enzo", "Theo", "Noe"],
         "Spain": ["Pablo", "Alvaro", "Iker", "Sergio"], "Nigeria": ["Tobi", "Chidi", "Ade", "Emeka"]}
LAST = {"Italy": ["Bianchi", "Greco", "Conti", "Marino"], "Netherlands": ["de Vries", "Bakker", "Visser", "Smit"], "Portugal": ["Silva", "Costa", "Pereira", "Lopes"],
        "England": ["Walker", "Bennett", "Hughes", "Turner"], "Brazil": ["Souza", "Lima", "Rocha", "Alves"], "France": ["Moreau", "Laurent", "Girard", "Faure"],
        "Spain": ["Ruiz", "Moreno", "Ortega", "Castro"], "Nigeria": ["Okoye", "Eze", "Balogun", "Nwosu"]}
LEAGUES = {"Premier Division": ["Northbridge Athletic", "Castleford Rovers", "Port Ellis United", "Kingsmere Town"],
           "Serie A": ["AC Valdora", "Sporting Lerici", "US Montebello"],
           "Eredivisie": ["FC Zuiderhaven", "SV Oostmeer", "Go Ahead Linden"],
           "Primeira Liga": ["CD Alvorada", "SC Ribeira", "FC Douro Norte"]}
POS_POOL = [["GK"], ["D (C)"], ["D (C)"], ["D (L)"], ["D (R)"], ["DM", "M (C)"], ["M (C)"], ["AM (C)"], ["AM (L)"], ["AM (R)"], ["ST"], ["ST"]]


def scouting_pool(save_no: int, game_date: date, months_played: int, edits: dict) -> list:
    out, uid = [], 30500000
    for league, clubs in LEAGUES.items():
        for club in clubs:
            for i in range(10):
                uid += 1
                rng = random.Random(uid)
                nat = rng.choice(list(FIRST))
                age = rng.randint(17, 33)
                pa = rng.randint(110, 185)
                growth = 1.2 if age < 21 else 0.4 if age < 24 else 0 if age < 29 else -0.5
                ca = int(max(60, min(pa, pa - rng.randint(0, 60) * (1 if age < 23 else 0.3) + growth * save_no)))
                e = edits.get(uid, {})
                ca, pa2 = max(1, min(200, ca + e.get("ca", 0))), max(1, min(200, pa + e.get("pa", 0)))
                pos = POS_POOL[i % len(POS_POOL)] if i < 10 else rng.choice(POS_POOL)
                minutes = int(months_played * rng.uniform(40, 360))
                exp = 6.0 + (ca - 100) / 100
                out.append({"unique_id": uid, "name": f"{rng.choice(FIRST[nat])} {rng.choice(LAST[nat])}", "age": age, "nationality": nat,
                            "club": club, "league": league, "positions": pos, "ca": ca, "pa": pa2,
                            "value": int(max(150_000, (ca - 60) ** 2.4 * (1.6 if age < 23 else 1) * rng.uniform(0.6, 1.5)) // 50_000 * 50_000),
                            "wage": int((ca - 50) * 160 * rng.uniform(0.7, 1.3)), "minutes": minutes, "appearances": minutes // 80,
                            "avg_rating": round(exp + rng.uniform(-0.5, 0.5), 2) if minutes else None,
                            "goals": int(minutes / 90 * (0.45 if "ST" in pos else 0.15) * rng.uniform(0.3, 1.4)),
                            "attributes": attributes(uid, pos, ca)})
    return out


def read_save(save_no: int, club_name: str, edits: dict | None = None) -> dict:
    """Return the save as fmsave-shaped records: club, game date, players, scouting pool and next fixture."""
    edits = edits or {}
    game_date = _add_months(date(2027, 8, 1), save_no)
    season_year = game_date.year if game_date.month >= 7 else game_date.year - 1
    months_played = (game_date.month - 7) % 12
    players = []
    for uid, name, birth, nat, pos, ca, pa, growth, mins, contract, wage, joins, leaves in SQUAD:
        if save_no < joins or (leaves is not None and save_no >= leaves):
            continue
        rng = random.Random(uid * 31 + save_no)
        months_here = save_no - joins
        e = edits.get(uid, {})
        pa = max(1, min(200, pa + e.get("pa", 0)))
        cur = int(round(min(pa, max(40, ca + growth * months_here + rng.choice([-1, 0, 0, 1]) + e.get("ca", 0)))))
        played = 0
        for m in range(months_played):
            played += max(0, int(mins * random.Random(uid + m).uniform(0.6, 1.15)))
        apps = played // 80
        players.append({
            "unique_id": uid, "name": name, "birth_date": birth, "age": _age(birth, game_date),
            "nationality": nat, "positions": pos, "ca": cur, "pa": pa,
            "contract_end": contract, "wage": wage, "minutes": played, "appearances": apps,
            "avg_rating": round(6.4 + (cur - 100) / 120 + rng.uniform(-0.2, 0.2), 2) if apps else None,
            "goals": int(played / 90 * (0.5 if "ST" in pos else 0.2 if any(x.startswith("AM") for x in pos) else 0.04)),
            "assists": int(played / 90 * (0.3 if any(x.startswith("AM") for x in pos) else 0.08)),
            "training_rating": round(min(9.5, 6.2 + (pa - cur) / 40 + (growth * 0.6) + rng.uniform(-0.3, 0.3)), 1),
            "homegrown": nat in HOMEGROWN_NATIONS or birth >= "2006-01-01",
            "attributes": attributes(uid, pos, cur),
        })
    rng = random.Random(save_no)
    fixture = {"opponent": OPPONENTS[save_no % len(OPPONENTS)], "home": save_no % 2 == 0,
               "date": date(game_date.year, game_date.month, 6).isoformat(), "competition": "League",
               "kickoff": "15:00", "form": [rng.choice("WWDLW") for _ in range(5)]}
    return {
        "file_name": f"{club_name.replace(' ', '_')}_{game_date.isoformat()}.fm",
        "club_name": club_name, "game_date": game_date.isoformat(),
        "season": f"{season_year}/{str(season_year + 1)[2:]}",
        "players": players, "next_fixture": fixture,
        "pool": scouting_pool(save_no, game_date, months_played, edits),
    }


def editor_supports(edition: str) -> bool:
    """Edition-specific validation for the (sample) game editor."""
    return edition in ("FM26", "FM27")


def detect_install(edition: str) -> dict:
    year = "2027" if edition == "FM27" else "2026"
    return {"found": True, "edition": edition, "sample": True,
            "save_folder": f"C:\\Users\\[You]\\Documents\\Sports Interactive\\Football Manager {year}\\games"}
