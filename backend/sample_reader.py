"""Sample save reader: stands in for fmsave in the browser preview (no real FM saves here)."""
import random
from datetime import date

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


def read_save(save_no: int, club_name: str) -> dict:
    """Return the save as fmsave-shaped records: club, game date, players and next fixture."""
    game_date = _add_months(date(2027, 8, 1), save_no)
    season_year = game_date.year if game_date.month >= 7 else game_date.year - 1
    months_played = (game_date.month - 7) % 12
    players = []
    for uid, name, birth, nat, pos, ca, pa, growth, mins, contract, wage, joins, leaves in SQUAD:
        if save_no < joins or (leaves is not None and save_no >= leaves):
            continue
        rng = random.Random(uid * 31 + save_no)
        months_here = save_no - joins
        cur = int(round(min(pa, max(40, ca + growth * months_here + rng.choice([-1, 0, 0, 1])))))
        played = 0
        for m in range(months_played):
            played += max(0, int(mins * random.Random(uid + m).uniform(0.6, 1.15)))
        apps = played // 80
        players.append({
            "unique_id": uid, "name": name, "birth_date": birth, "age": _age(birth, game_date),
            "nationality": nat, "positions": pos, "ca": cur, "pa": pa,
            "contract_end": contract, "wage": wage, "minutes": played, "appearances": apps,
            "avg_rating": round(6.4 + (cur - 100) / 120 + rng.uniform(-0.2, 0.2), 2) if apps else None,
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
    }


def detect_install(edition: str) -> dict:
    year = "2027" if edition == "FM27" else "2026"
    return {"found": True, "edition": edition, "sample": True,
            "save_folder": f"C:\\Users\\[You]\\Documents\\Sports Interactive\\Football Manager {year}\\games"}
