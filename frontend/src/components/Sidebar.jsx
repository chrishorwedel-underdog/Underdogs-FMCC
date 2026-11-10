import { NavLink } from "react-router-dom";
import { Sparkles, Lock } from "lucide-react";
import { toast } from "sonner";
import { NAV } from "@/constants/nav";
import { useNotices } from "@/components/Notify";
import { useFeatures, isOff } from "@/lib/features";

const HINT = "Turned off for this career. Turn it on in Features.";
const tip = (items) => (items?.length ? `New: ${items.join(" · ")}. Opening this page clears the dot.` : undefined);

export const Sidebar = () => {
  const n = useNotices().data;
  const badges = n?.badges || [];
  const { data: feats } = useFeatures();
  const dofOff = isOff(feats, "dof");
  return (
  <aside className="side" data-testid="sidebar">
    <div className="brand"><img className="logo" src="/fmcc-logo.png" alt="FMCC — From Underdog Podcasts" data-testid="sidebar-logo" /></div>
    <nav>
      {NAV.map(({ to, key, label, sub, Icon, c, stage }) => (isOff(feats, key)
        ? <div key={key} className="nav-item locked" role="button" tabIndex={0} title={HINT} onClick={() => toast.info(HINT)} data-testid={`nav-${key}`}>
          <span className="tile2"><Icon size={20} strokeWidth={2.2} /></span><span className="tx"><b>{label}</b><small>{sub}</small></span><Lock size={13} className="lock-ic" /></div>
        : <NavLink key={key} to={to} end={to === "/"} style={{ "--c": c }} data-testid={`nav-${key}`} title={badges.includes(to) ? tip(n.badge_items?.[to]) : undefined}
          className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
          <span className="tile2"><Icon size={20} strokeWidth={2.2} /></span>
          <span className="tx"><b>{label}</b><small>{sub}</small></span>
          {stage && <span className="later">Stage {stage}</span>}
          {badges.includes(to) && <span className="nav-dot" data-testid={`nav-badge-${key}`} />}
        </NavLink>))}
    </nav>
    <div className="foot">
      {dofOff ? <div className="dofbtn locked" role="button" tabIndex={0} title={HINT} onClick={() => toast.info(HINT)} data-testid="nav-ask-dof">
        <b><Lock size={16} />Chat with your</b><small>Director of Football</small></div>
        : <NavLink to="/dof" className="dofbtn" data-testid="nav-ask-dof">
          <b><Sparkles size={18} strokeWidth={2.3} />Chat with your</b>
          <small>Director of Football</small>
        </NavLink>}
    </div>
  </aside>
  );
};
