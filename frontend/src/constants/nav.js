import { Home, Users, TrendingUp, Search, Activity, BarChart3, Zap, Star, Coins, Sprout, ShieldCheck, Palette, UserCog, Gavel, Package } from "lucide-react";

export const TOP_LINKS = [
  { to: "/safety", key: "safety", label: "Project Safety", Icon: ShieldCheck },
  { to: "/extras", key: "extras", label: "Downloads you need", Icon: Package },
  { to: "/appearance", key: "appearance", label: "Appearance", Icon: Palette },
];

export const NAV = [
  { to: "/", key: "home", label: "Home", sub: "Your club at a glance", c: "#A3E635", Icon: Home },
  { to: "/dynamic-potential", key: "dp", label: "Dynamic Potential", sub: "Review development", c: "#4C8DFF", Icon: TrendingUp },
  { to: "/breakout", key: "breakout", label: "Breakout Player", sub: "This season's breakout nominations", c: "#FACC15", Icon: Star },
  { to: "/scouting", key: "scouting", label: "Scout Players", sub: "Scout Window", c: "#22D3EE", Icon: Search },
  { to: "/reports", key: "reports", label: "Monthly Reports", sub: "See the bigger picture", c: "#A78BFA", Icon: BarChart3 },
  { to: "/moneyball", key: "moneyball", label: "Moneyball", sub: "Compare transfer options", c: "#F2B54A", Icon: Coins },
  { to: "/squad", key: "squad", label: "Squad", sub: "Lineups and depth charts", c: "#2DD4BF", Icon: Users },
  { to: "/development", key: "development", label: "Development", sub: "Minutes and growth plans", c: "#34D399", Icon: Sprout },
  { to: "/elite-training", key: "elite", label: "Elite Training", sub: "Nurture your next generation", c: "#E879F9", Icon: Zap },
  { to: "/matches", key: "matches", label: "Matches", sub: "Chalkboard and match stats", c: "#FB923C", Icon: Activity },
  { to: "/editor", key: "editor", label: "Player & Teams Editor", sub: "Faces, logos, names and clubs", c: "#F472B6", Icon: UserCog },
  { to: "/punish", key: "punish", label: "Punish a Club", sub: "Penalties for any club", c: "#F87171", Icon: Gavel },
];

export const STAGE_TEXT = {
  development: "Minutes plans, loan plans and development goals for each player, tracked automatically from every save.",
  scouting: "Automatic rankings of every player in the save by role fit, age, potential and value, with shortlists and Moneyball comparisons.",
  matches: "A Sofascore/Opta-style view of every match: xG timeline, chalkboard, player cards and replays from FMMatchLens.",
  reports: "An automatic squad snapshot each in-game month, with comparisons between months.",
  elite: "Nominations, training evidence from the save and PA boosts under your own rules.",
  appearance: "Themes, colours and how FMCC looks on your screen.",
  dof: "Your Director of Football to talk to. It sees your squad, plans, reports and history.",
};
