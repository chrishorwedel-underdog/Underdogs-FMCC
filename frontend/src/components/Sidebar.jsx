import { NavLink } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { NAV, TOP_LINKS } from "@/constants/nav";
import { useNotices } from "@/components/Notify";

export const Sidebar = () => {
  const badges = useNotices().data?.badges || [];
  return (
  <aside className="side" data-testid="sidebar">
    <div className="brand"><img className="logo" src="/fmcc-logo.png" alt="FMCC — From Underdog Podcasts" data-testid="sidebar-logo" /></div>
    <div className="toplinks">
      {TOP_LINKS.map(({ to, key, label, Icon }) => (
        <NavLink key={key} to={to} className={({ isActive }) => `tl${isActive ? " on" : ""}`} data-testid={`nav-${key}`}><Icon size={14} />{label}</NavLink>
      ))}
    </div>
    <div className="sec">Your workspace</div>
    <nav>
      {NAV.map(({ to, key, label, sub, c, Icon, stage }) => (
        <NavLink key={key} to={to} end={to === "/"} style={{ "--c": c }} data-testid={`nav-${key}`}
          className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
          <span className="tile2"><Icon size={20} strokeWidth={2.2} /></span>
          <span className="tx"><b>{label}</b><small>{sub}</small></span>
          {stage && <span className="later">Stage {stage}</span>}
          {badges.includes(to) && <span className="nav-dot" data-testid={`nav-badge-${key}`} />}
        </NavLink>
      ))}
    </nav>
    <div className="foot">
      <NavLink to="/dof" className="dofbtn" data-testid="nav-ask-dof">
        <b><Sparkles size={18} strokeWidth={2.3} />Chat with your</b>
        <small>Director of Football</small>
      </NavLink>
    </div>
  </aside>
  );
};
