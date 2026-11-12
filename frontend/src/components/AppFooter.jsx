import { NavLink, useLocation } from "react-router-dom";
import { TOP_LINKS } from "@/constants/nav";
import { VersionTag } from "@/components/VersionTag";
import { DownloadLink } from "@/components/DownloadButton";

export const AppFooter = () => {
  const { pathname, search } = useLocation();
  const here = pathname + search;
  return (
    <footer className="app-foot" data-testid="app-footer">
      {TOP_LINKS.map(({ to, key, label, Icon }) => (
        <NavLink key={key} to={to} className={() => `tl${here === to || (to.includes("section=") && here.startsWith(to)) || (!to.includes("?") && pathname === to) ? " on" : ""}`} data-testid={`nav-${key}`}><Icon size={14} />{label}</NavLink>
      ))}
      {pathname === "/" && <DownloadLink />}
      <VersionTag />
    </footer>
  );
};
