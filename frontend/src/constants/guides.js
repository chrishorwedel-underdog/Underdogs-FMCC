// Plain-language guide shown at the top of every sidebar page: what it does, what's on it, how to use it.
export const GUIDES = {
  "/": {
    what: "Your club at a glance. Everything important from your latest save on one screen.",
    features: ["Six cards with your squad, development, scouting, awards, matches and reports", "Needs your attention: contracts ending, players short of minutes and changes waiting for approval", "Your next match", "Updates, backups and careers"],
    how: ["Play FM and save the game", "FMCC reads the new save on its own (or press the refresh button at the top)", "Click any card to open that module"],
  },
  "/dynamic-potential": {
    what: "Adjusts potential (PA) up or down for players who are developing faster or slower than expected, under rules you set.",
    features: ["Run it for every player at your club (and other clubs, if you switch them on)", "Your own growth and decline rules in the Rules tab", "A review list where you untick players or whole clubs before anything is queued", "Changes stay hidden: FMCC never shows who goes up or down, so you find out by playing"],
    how: ["Press Run Dynamic Potential after a save is read", "Untick anyone you want to leave alone", "Queue the changes; you confirm them in Game changes before anything touches FM"],
  },
  "/breakout": {
    what: "Picks this season's breakout players: the ones performing far above what was expected.",
    features: ["Automatic nominations from match numbers and growth", "The reasons behind each nomination", "One award per player per season, so nobody is rewarded twice", "Your own rules and thresholds"],
    how: ["Open the nominations", "Approve the players you agree with", "The award is queued in Game changes for you to confirm"],
  },
  "/scouting": {
    what: "Finds and judges every player in your save: ScoutSheet's scouting with deep FMDataLab-style stats.",
    features: ["Full, Fair play or Moneyball view (top right): see everything, only what your scouts would know, or just stats and price", "Players: search, ready-made searches, filters, a stats table, saved searches and CSV export", "Click any player for his profile: grade, fair price, pizza chart, similar players and a scouting report", "My Club (your weakest positions), Deals & Offers (bargains, bid checks and a quadrant chart of performance against cost), Scatter, Compare, Computed stats and your own Formulas", "Advanced filters with AND/OR groups and percentile conditions, heat colours, and Find a replacement on every profile", "Leagues (how strong each league is) and Possession (adjusts stats for team style)"],
    how: ["Pick a view at the top", "Search or pick a ready-made search in Players", "Click a player to open his profile, star him for the shortlist or tick the scales to compare"],
  },
  "/reports": {
    what: "A snapshot of your squad every in-game month, so you can see the bigger picture over time.",
    features: ["A report created automatically for each in-game month", "Compare any two months side by side", "Your own report rules"],
    how: ["Keep playing and saving: reports appear once FMCC has read saves from two different months", "Open Compare months to see how the squad changed"],
  },
  "/moneyball": {
    what: "Compares transfer options side by side, judged on numbers and price.",
    features: ["Up to 4 players side by side", "A computed stat broken into its parts for each player", "The same Full, Fair play and Moneyball views as Scout Players"],
    how: ["In Scout Players, tick the scales button on up to 4 players", "Come back here (or open Compare) to see them together"],
  },
  "/squad": {
    what: "Plans your team: who plays where, who's next in line and the best lineup.",
    features: ["Role ratings for every player", "Depth charts for each position", "Best XI: the highest-scoring lineup for your formation and roles", "Development XI: a lineup that gives your young players minutes", "Tactic fit: every player rated for every slot of a tactic (import an .fmf or pick a formation), squad gaps and a shape advisor", "Registration checks"],
    how: ["Pick a formation", "Look at Best XI and Development XI on the pitch", "Save a lineup to keep it in your history"],
  },
  "/development": {
    what: "Plans how each player develops: minutes, loans and goals.",
    features: ["A minutes plan, loan plan and development goals for each player", "Progress tracked automatically from every save", "Revising a plan keeps every earlier version"],
    how: ["Open a player and set his plan", "FMCC checks progress every time a save is read and flags anyone falling behind"],
  },
  "/elite-training": {
    what: "Gives your best young players an extra development boost when they earn it in training.",
    features: ["Nominations from training evidence in the save", "PA boosts under your own rules", "History of every decision"],
    how: ["Review the nominations", "Approve the ones you agree with", "Boosts go to Game changes for you to confirm"],
  },
  "/matches": {
    what: "A Sofascore/Opta-style view of your matches.",
    features: ["Shots, passes, defensive actions and heat maps on the chalkboard", "Match stats and player match cards", "Season per-90 numbers", "Setup for the match add-on"],
    how: ["Install the match add-on from Connections", "Play matches in FM", "Open a match here. (Real match files arrive once FMCC can read them; the preview shows sample matches.)"],
  },
  "/editor": {
    what: "Changes how players and clubs look and are named in FM.",
    features: ["Player faces: pick from NG_Regens, upload your own or create one with ChatGPT", "Clubs: logos (upload or ChatGPT), names and club attributes such as reputation and cash", "Kits: home, away and third, uploaded or designed by ChatGPT, even in bulk", "Licensing fix: give unlicensed clubs and leagues their real names", "Pack browser, Bulk import of a whole folder or zip, and a Pack check that finds missing or clashing pictures"],
    how: ["Pick a tab at the top", "Every change shows a preview first and can be undone", "Reload graphics in FM (or restart it) to see the changes"],
  },
  "/safety": {
    what: "Keeps your saves and FMCC's data safe, and checks each save for player changes.",
    features: ["Verified backups, made automatically before every save read and every change", "Save checks: new players, players who left and players with the same ID but a new name, so nobody is mixed up", "The record of every game change FMCC has made, with undo"],
    how: ["Look here after a save is read to confirm the player checks", "Restore a backup if you ever need to"],
  },
  "/dof": {
    what: "Talk to your Director of Football. It knows your squad, plans, reports and history.",
    features: ["Ask anything about your squad, transfers or young players", "It can suggest actions, such as a shortlist, which you approve first", "Your conversations are kept"],
    how: ["Type a question or tap a suggested one", "Read the answer and approve any suggested action you like"],
  },
};
