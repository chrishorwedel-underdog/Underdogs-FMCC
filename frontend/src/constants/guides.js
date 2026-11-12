// Plain-language guide shown at the top of every sidebar page: what it does, what's on it, how to use it.
// One or two very simple sentences per page: what the feature does, in everyday words.
export const SIMPLE = {
  "/": "Shows you the most important things about your club right now, so you know what to do next.",
  "/punish": "Lets you punish any club, for example by taking points off them or fining them, and puts it into your FM save for you.",
  "/dynamic-potential": "Players who play well can become better in the future, and players who play badly can lose some of their future. FMCC checks this twice a season.",
  "/breakout": "At the end of each season FMCC picks the first-team player who had the best season compared with his teammates, gives him a small boost in FM and does it all for you.",
  "/club-analysis": "Looks at your whole club and tells you, in order, what to fix first: weak positions, ageing players, contracts and money.",
  "/transfer-market": "Shows which players are for sale, who is cheap for how good he is, and what is moving around the world in your save.",
  "/club-history": "Remembers everything your club achieves in this save: trophies, every season, club records and big moments. Nothing is made up; anything the save doesn't include says Unavailable.",

  "/scouting": "Helps you find good players to sign, using their real match numbers and price, and tells you which ones are worth it.",
  "/reports": "A monthly news page for the whole football world in your save: who won, who scored and who moved clubs.",
  "/moneyball": "Shows which players give you the most for your money.",
  "/squad": "Helps you pick your best team and see who should play in each position.",
  "/development": "Helps your young players grow by checking they get enough games, the right loans and clear goals.",
  "/elite-training": "Gives your best young players an extra boost when they train really well.",
  "/matches": "Shows what happened in your matches with easy charts and numbers.",
  "/editor": "Lets you change names, looks and details of players and clubs in your FM save.",
  "/safety": "Keeps a backup of your saves and FMCC's data so nothing gets lost.",
  "/dof": "A helper you can chat with about your team. Ask it anything about your squad and plans.",
};


export const GUIDES = {
  "/punish": {
    what: "Punishes any club in your database, inspired by sortitoutsi's Punish Manchester City tool.",
    features: ["Search and pick any club", "Sporting, transfer, money, reputation and facility penalties, each with its own setting", "Presets: Light, Heavy and The full 115", "A plain-words summary before anything is made", "A new-career file for FM26 and FM27, and money, reputation and facilities queued on your current FM27 save", "Saved punishments you can download or remove"],
    how: ["Pick a club", "Switch on penalties or pick a preset, then check the summary", "Make the new-career file and pick it from FM's database list when you start a new career, or queue the live ones and approve them in Game changes"],
  },
  "/": {
    what: "Your club at a glance. Everything important from your latest save on one screen. A dot next to a menu item means that page has something new; opening the page clears it.",
    features: ["Up next in your save: urgent items first, then what's coming soon, each with one button", "The finance strip under the top bar: FFP, wages against turnover, transfer spending, budget and bank", "Cards with your squad, development, scouting, awards, game changes and reports (cards for features you've turned off are hidden)", "Your next match"],
    how: ["Play FM and save the game", "FMCC reads the new save on its own (or press the refresh button at the top)", "Click any card to open that module"],
  },
  "/dynamic-potential": {
    what: "Moves each player's hidden potential with how they actually play, following the Underdog FM Dynamic Potential Rulesheet: a winter review and a season-end review.",
    features: ["Performance Score: 55% match-rating percentile and 45% role output, compared with similar players", "Growth tiers, decline rules, age deduction and both tapers from the rulesheet", "Results go straight into your save; ratings-only growth above +4, small comparison groups and held declines wait for your review", "A plain-words breakdown for every player, never showing real CA or PA", "Every rule value editable in Settings, with reset and history"],
    how: ["Check the winter review date that splits the season", "Press Run winter review when the winter window opens, and Run season-end review after the last match", "Approve or reject anything under Needs your review"],
  },
  "/breakout": {
    what: "FMCC picks the season's Breakout Player automatically: the first-team player with the best season compared with his teammates. The reward is applied to your save for you.",
    features: ["A live ranking of your first-team players (22 and over) by season grade", "Fair for every position: each grade is scored against players in the same position", "At least 900 minutes to qualify", "Each player can only win once in his career", "Past winners", "Your own reward rules in Rules"],
    how: ["Play your season: the ranking updates with every save FMCC reads", "When FMCC reads your May or June save, the leader wins automatically", "His reward is applied to the save and you get a bell notice. Undo it in Game changes if you need to"],
  },
  "/club-analysis": {
    what: "Your whole club in one report: the weakest areas, what to do first, values, contracts and player radars.",
    features: ["What to do first, in order", "Weakest positions compared with your best options", "Squad value, wages and contracts", "Radar and heatmap views for your players", "Click any player to open his panel"],
    how: ["Read a save so FMCC has your latest squad", "Start with the first item in What to do first", "Open a player to see his details, or jump to Squad or Scout Players to act on it"],
  },
  "/club-history": {
    what: "Your club's story in this save: trophies, a permanent page for every season, club records, statistical leaders, a Hall of Fame and a milestone timeline.",
    features: ["Trophy Cabinet: latest honour, last three seasons, trophies, promotions, runner-up finishes, individual awards and milestones", "Seasons: one permanent page per season, kept as it happened", "Records: team, player, match and transfer records with previous holders, in League or All competitions", "Statistical Leaders: goals, assists, appearances, starts, minutes, average rating, clean sheets, tackles, duels won, plus npxG, xA, xG + xA, progressive passes and carries, goals prevented. Current season (top five) or All-Time (every season's leader ranked, this season in gold)", "Compare Seasons side by side", "Hall of Fame for your club legends", "Timeline with pinned moments"],
    how: ["FMCC adds to it every time it reads a save", "Click any season, player, match or record to see where it came from", "Missing figures show as Unavailable and fill in when a later save includes them"],
  },
  "/transfer-market": {
    what: "Who is available, what they cost and what is moving across your save's world.",
    features: ["Players for sale, on loan or with release clauses", "Best value for money", "Young players worth watching", "Recent transfers between clubs", "Click any player to open his panel"],
    how: ["Pick a list at the top", "Sort or filter to narrow it down", "Open a player, then Watch, Shortlist or Compare him"],
  },
  "/scouting": {
    what: "Finds and judges every player in your save using a combination of match stats and advanced analytics.",
    features: ["Full, Fair play or Moneyball view (top right): see everything, only what your scouts would know, or just stats and price", "Players: search, ready-made searches, filters, a stats table, saved searches and CSV export", "Click any player for his profile: grade, fair price, pizza chart, similar players and a scouting report", "My Club (your weakest positions), Deals & Offers (bargains, bid checks and a quadrant chart of performance against cost), Scatter, Compare, Computed stats and your own Formulas", "Advanced filters with AND/OR groups and percentile conditions, heat colours, and Find a replacement on every profile", "Leagues (how strong each league is) and Possession (adjusts stats for team style)"],
    how: ["Pick a view at the top", "Search or pick a ready-made search in Players", "Click a player to open his profile, star him for the shortlist or tick the scales to compare"],
  },
  "/reports": {
    what: "Who made waves across the world last month: news, tables, transfers, stat leaders and monthly awards for every loaded league.",
    features: ["The 12 biggest world stories (3–5 per country)", "Updated league tables with position changes", "The 10 biggest transfers by fee", "Top 10 leaders in every stat and analytics category, plus top 5 under-21s", "Attacker, Defender, Goalkeeper and U21 Player of the Month, each with two runners-up", "A report for the whole world, each continent, each nation and each league", "My squad: compare any two months of your own squad"],
    how: ["Keep playing and saving: each in-game month gets its own report", "Open the World report, or pick a continent, nation or league for its own report and winners"],
  },
  "/moneyball": {
    what: "Compares transfer options side by side, judged on numbers and price.",
    features: ["Up to 4 players side by side", "A computed stat broken into its parts for each player", "The same Full, Fair play and Moneyball views as Scout Players"],
    how: ["In Scout Players, tick the scales button on up to 4 players", "Come back here (or open Compare) to see them together"],
  },
  "/squad": {
    what: "Plans your team: who plays where, who's next in line and the best lineup.",
    features: ["Role ratings for every player", "Depth charts for each position", "Best XI: the highest-scoring lineup for your formation and roles", "Development XI: a lineup that gives your young players minutes", "Domestic, Cup and UEFA XI: league-registered, rotated and UEFA-registered lineups", "Up to 3 extra formations of your choice to experiment with", "Tactic fit: every player rated for every slot of a tactic (import an .fmf or pick a formation), squad gaps and a shape advisor", "Registration checks"],
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
    features: ["Player faces: pick from NG_Regens, upload your own or create one with ChatGPT", "Player Creator: build one player in detail (positions, attributes, personality, ability), or a batch", "Seed a Surname: spread one surname across new players and staff, or rename low-profile players in your save", "Clubs: logos (upload or ChatGPT), names and club attributes such as reputation and cash", "Kits: home, away and third, uploaded or designed by ChatGPT, even in bulk", "Licensing fix: give unlicensed clubs and leagues their real names", "Pack browser, Bulk import of a whole folder or zip, and a Pack check that finds missing or clashing pictures"],
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
