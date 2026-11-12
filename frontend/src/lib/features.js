import { useGet } from "@/lib/ui";

export const FEATURE_TEXT = {
  home: ["Your club at a glance: squad summary, your next match, what needs your attention and what's coming up in your save. Always on.", "See at a glance that two contracts end this summer and the transfer window opens in 3 weeks."],
  dp: ["Lets player potential rise or fall based on how players actually perform and develop, using rules you control. Changes go into your game automatically unless you switch on Review changes before applying.", "A 19-year-old who keeps starting and scoring gets a potential boost, and a notification tells you."],
  breakout: ["Once a season, FMCC picks the player who broke out the most and gives them an ability bonus in your save.", "Your fringe winger has a huge season and is named Breakout Player, earning a bonus."],
  scouting: ["Ranks every player in your save by how well they fit each role, their age and value, with a full Stats Table: per-90 stats, percentile shading, advanced filters, saved views and CSV export.", "Find the best young ball-playing centre-backs in the top 20% for progressive passes."],
  reports: ["Each in-game month, the news across the world, a continent, a nation or a league. Top stories, tables, the biggest transfers, stat leaders and Players of the Month.", "Read who won Attacker of the Month in Europe and which club went top in Italy."],
  market: ["Ready-made transfer lists (contracts ending, free agents, best under-21s), what changed since your last save, and value rankings for any league, club, country, position or age.", "See which players' contracts end this year and who moved since your last save."],
  club: ["A ranked list of what your club should do first, where your squad is weakest, and three groups of signing ideas: upgrades, affordable options and successors.", "\"No cover at left-back\", with a link straight to a ready-made search."],
  moneyball: ["Compares transfer targets side by side on value for money and fit, to help you decide who to buy.", "Put three strikers next to each other and see who gives the most for the money."],
  squad: ["Your best lineups and depth charts for league, cup and European games, using your save's own tactics.", "See your strongest cup XI and who's next in line in every position."],
  development: ["Minutes and growth plans for each young player, tracked automatically from every save, with how much each has improved.", "Get told when a youngster is short of his monthly minutes target."],
  elite: ["Nominate your most promising youngsters; FMCC checks their training and can boost their potential under your rules.", "Your best academy prospect trains brilliantly all season and gets a potential boost."],
  matches: ["A detailed view of every match: chances (xG), a chalkboard, player ratings and replays.", "Check where your chances came from in last week's draw."],
  editor: ["Faces, club logos, kits, names, a player creator and Seed a Surname.", "Give your regens real faces or build a custom player for a new save."],
  punish: ["Hand out penalties to any club, such as points deductions, fines or transfer bans.", "Dock a rival 10 points for financial trouble."],
  dof: ["An assistant that knows your squad, plans and history; ask it questions or for suggestions.", "Ask \"Who should I sell this summer?\" and get an answer based on your save."],
};

export const useFeatures = () => useGet("features", "/features");
export const isOff = (data, key) => !!data && key !== "home" && data.features[key] === false;
