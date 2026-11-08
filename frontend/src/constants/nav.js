import { Home, Users, TrendingUp, Search, Activity, BarChart3, Zap, Trophy } from "lucide-react";

export const NAV = [
  { to: "/", key: "home", label: "Home", sub: "Your club at a glance", c: "#A3E635", Icon: Home },
  { to: "/squad", key: "squad", label: "Squad", sub: "Lineups and depth charts", c: "#2DD4BF", Icon: Users },
  { to: "/development", key: "development", label: "Development", sub: "Minutes and growth plans", c: "#4C8DFF", Icon: TrendingUp },
  { to: "/scouting", key: "scouting", label: "Scouting", sub: "Targets and Moneyball", c: "#22D3EE", Icon: Search },
  { to: "/matches", key: "matches", label: "Matches", sub: "Chalkboard and match stats", c: "#FB923C", Icon: Activity, stage: 4 },
  { to: "/reports", key: "reports", label: "Reports", sub: "See the bigger picture", c: "#A78BFA", Icon: BarChart3 },
  { to: "/elite-training", key: "elite", label: "Elite Training", sub: "Nurture your next generation", c: "#E879F9", Icon: Zap },
  { to: "/awards", key: "awards", label: "Awards", sub: "Breakout and Dynamic Potential", c: "#FACC15", Icon: Trophy },
];

export const STAGE_TEXT = {
  development: "Minutes plans, loan plans and development goals for each player, tracked automatically from every save.",
  scouting: "Automatic rankings of every player in the save by role fit, age, potential and value, with shortlists and Moneyball comparisons.",
  matches: "A Sofascore/Opta-style view of every match: xG timeline, chalkboard, player cards and replays from FMMatchLens.",
  reports: "An automatic squad snapshot each in-game month, with comparisons between months.",
  elite: "Nominations, training evidence from the save and PA boosts under your own rules.",
  awards: "Annual Breakout and Dynamic Potential: nominations, reviews and official awards at season end.",
  dof: "Your Director of Football to talk to, using your own OpenAI key. It sees your squad, plans, reports and history.",
};
