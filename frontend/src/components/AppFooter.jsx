import { NavLink, useLocation } from "react-router-dom";
import { TOP_LINKS } from "@/constants/nav";
import { VersionTag } from "@/components/VersionTag";
import { DownloadLink } from "@/components/DownloadButton";

export const AppFooter = () => {
  const { pathname } = useLocation();
  return (
    <footer className="app-foot" data-testid="app-footer">
      {TOP_LINKS.map(({ to, key, label, Icon }) => (
        <NavLink key={key} to={to} className={({ isActive }) => `tl${isActive ? " on" : ""}`} data-testid={`nav-${key}`}><Icon size={14} />{label}</NavLink>
      ))}
      {pathname === "/" && <DownloadLink />}
      <VersionTag />
    </footer>
  );
};
