import { Home, Users, TrendingUp, Search, Activity, BarChart3, Zap, Star, Sprout, ShieldCheck, Palette, UserCog, Gavel, Package, ToggleRight, ArrowLeftRight, ClipboardList } from "lucide-react";

export const TOP_LINKS = [
  { to: "/settings?section=safety", key: "safety", label: "Project Safety", Icon: ShieldCheck },
  { to: "/extras", key: "extras", label: "Downloads", Icon: Package },
  { to: "/settings?section=appearance", key: "appearance", label: "Appearance", Icon: Palette },
  { to: "/settings?section=features", key: "features", label: "Features", Icon: ToggleRight },
];

export const GROUPS = ["My Club", "Player Development", "Recruitment", "Reports", "Utilities"];

export const NAV = [
  { group: "My Club", to: "/matches", key: "matches", label: "Matches", sub: "Chalkboard and match stats", c: "#FB923C", Icon: Activity },
  { group: "My Club", to: "/squad", key: "squad", label: "Squad", sub: "Lineups and depth charts", c: "#2DD4BF", Icon: Users },
  { group: "Player Development", to: "/breakout", key: "breakout", label: "Breakout Player", sub: "Picks the season's winner", c: "#FACC15", Icon: Star },
  { group: "Player Development", to: "/development", key: "development", label: "Development", sub: "Minutes and growth plans", c: "#34D399", Icon: Sprout },
  { group: "Player Development", to: "/dynamic-potential", key: "dp", label: "Dynamic Potential", sub: "Review development", c: "#4C8DFF", Icon: TrendingUp },
  { group: "Player Development", to: "/elite-training", key: "elite", label: "Elite Training", sub: "Nurture your next generation", c: "#E879F9", Icon: Zap },
  { group: "Recruitment", to: "/scouting", key: "scouting", label: "Scout Players", sub: "Search, Moneyball, youth intake", c: "#22D3EE", Icon: Search },
  { group: "Recruitment", to: "/transfer-market", key: "market", label: "Transfer Market", sub: "Who's available, what's moving", c: "#38BDF8", Icon: ArrowLeftRight },
  { group: "Reports", to: "/club-analysis", key: "club", label: "Club Analysis", sub: "What to do first", c: "#818CF8", Icon: ClipboardList },
  { group: "Reports", to: "/reports", key: "reports", label: "Monthly Awards", sub: "Who made waves last month", c: "#A78BFA", Icon: BarChart3 },
  { group: "Utilities", to: "/editor", key: "editor", label: "Player & Teams Editor", sub: "Faces, logos, names and clubs", c: "#F472B6", Icon: UserCog },
  { group: "Utilities", to: "/punish", key: "punish", label: "Punish a Club", sub: "Penalties for any club", c: "#F87171", Icon: Gavel },
];
export const HOME = { to: "/", key: "home", label: "Home", sub: "Your club at a glance", c: "#A3E635", Icon: Home };

export const STAGE_TEXT = {
  development: "Minutes plans, loan plans and development goals for each player, tracked automatically from every save.",
  scouting: "Automatic rankings of every player in the save by role fit, age, potential and value, with shortlists and Moneyball comparisons.",
  matches: "A Sofascore/Opta-style view of every match: xG timeline, chalkboard, player cards and replays from FMMatchLens.",
  reports: "An automatic squad snapshot each in-game month, with comparisons between months.",
  elite: "Nominations, training evidence from the save and potential boosts under your own rules.",
  appearance: "Themes, colours and how FMCC looks on your screen.",
  dof: "Your Director of Football to talk to. It sees your squad, plans, reports and history.",
};
