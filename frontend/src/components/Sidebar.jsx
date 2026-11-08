import { NavLink } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { NAV } from "@/constants/nav";

export const Sidebar = () => (
  <aside className="side" data-testid="sidebar">
    <div className="brand"><img className="logo" src="/fmcc-logo.png" alt="FMCC — From Underdog Podcasts" data-testid="sidebar-logo" /></div>
    <div className="sec">Club</div>
    <nav>
      {NAV.map(({ to, key, label, sub, c, Icon, stage }) => (
        <NavLink key={key} to={to} end={to === "/"} style={{ "--c": c }} data-testid={`nav-${key}`}
          className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
          <span className="tile2"><Icon size={20} strokeWidth={2.2} /></span>
          <span className="tx"><b>{label}</b><small>{sub}</small></span>
          {stage && <span className="later">Stage {stage}</span>}
        </NavLink>
      ))}
    </nav>
    <div className="foot">
      <NavLink to="/dof" className="dofbtn" data-testid="nav-ask-dof">
        <b><Sparkles size={20} strokeWidth={2.3} />Ask your DOF</b>
        <small>Chat with your Director of Football</small>
      </NavLink>
    </div>
  </aside>
);
