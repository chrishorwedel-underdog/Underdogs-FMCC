import { NavLink, Link } from "react-router-dom";
import { Sparkles, Lock } from "lucide-react";
import { toast } from "sonner";
import { NAV, GROUPS } from "@/constants/nav";
import { useNotices } from "@/components/Notify";
import { useFeatures, isOff } from "@/lib/features";

const HINT = "Turned off for this career. Turn it on in Features.";
const tip = (items) => (items?.length ? `New: ${items.join(" · ")}. Opening this page clears the dot.` : undefined);
const slug = (g) => g.toLowerCase().replace(/\s+/g, "-");

const Item = ({ n, feats, badges, notes }) => {
  const { to, key, label, sub, Icon, c } = n;
  if (isOff(feats, key)) {
    return <div className="nav-item locked" role="button" tabIndex={0} title={HINT} onClick={() => toast.info(HINT)} data-testid={`nav-${key}`}>
      <span className="tile2"><Icon size={20} strokeWidth={2.2} /></span><span className="tx"><b>{label}</b><small>{sub}</small></span><Lock size={13} className="lock-ic" /></div>;
  }
  return (
    <NavLink to={to} style={{ "--c": c }} data-testid={`nav-${key}`} title={badges.includes(to) ? tip(notes?.badge_items?.[to]) : undefined}
      className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
      <span className="tile2"><Icon size={20} strokeWidth={2.2} /></span>
      <span className="tx"><b>{label}</b><small>{sub}</small></span>
      {badges.includes(to) && <span className="nav-dot" data-testid={`nav-badge-${key}`} />}
    </NavLink>
  );
};

export const Sidebar = () => {
  const n = useNotices().data;
  const badges = n?.badges || [];
  const { data: feats } = useFeatures();
  const dofOff = isOff(feats, "dof");
  return (
  <aside className="side" data-testid="sidebar">
    <Link to="/" className="brand" title="Home" aria-label="FMCC Home" data-testid="sidebar-home-link">
      <img className="logo" src="/fmcc-logo.png" alt="FMCC — From Underdog Podcasts" data-testid="sidebar-logo" />
    </Link>
    <nav>
      {GROUPS.map((g) => (
        <div key={g} className="nav-grp" role="group" aria-label={g} data-testid={`nav-group-${slug(g)}`}>
          <div className="nav-grp-h">{g}</div>
          {NAV.filter((x) => x.group === g).map((x) => <Item key={x.key} n={x} feats={feats} badges={badges} notes={n} />)}
        </div>
      ))}
    </nav>
    <div className="foot">
      {dofOff ? <div className="dofbtn locked" role="button" tabIndex={0} title={HINT} onClick={() => toast.info(HINT)} data-testid="nav-ask-dof">
        <b><Lock size={18} />Chat with your Director of Football</b></div>
        : <NavLink to="/dof" className="dofbtn" data-testid="nav-ask-dof">
          <b><Sparkles size={18} strokeWidth={2.2} />Chat with your Director of Football</b>
        </NavLink>}
    </div>
  </aside>
  );
};
