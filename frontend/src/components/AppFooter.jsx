import { NavLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { TOP_LINKS } from "@/constants/nav";

const VersionTag = () => {
  const { data } = useQuery({ queryKey: ["updates"], queryFn: () => api.get("/updates").then((r) => r.data) });
  const f = data?.components.find((c) => c.key === "fmcc");
  if (!f) return null;
  const dev = f.installed_version === "dev";
  const ready = !dev && f.status === "update_available";
  return (
    <NavLink to="/settings" className="tl ver-tag" title={ready ? `FMCC ${f.latest_version} is ready to install` : undefined} data-testid="footer-version">
      {dev ? "FMCC preview build" : `FMCC ${f.installed_version}`}
      {ready && <span className="ver-dot" data-testid="footer-update-dot" />}
    </NavLink>
  );
};

export const AppFooter = () => (
  <footer className="app-foot" data-testid="app-footer">
    {TOP_LINKS.map(({ to, key, label, Icon }) => (
      <NavLink key={key} to={to} className={({ isActive }) => `tl${isActive ? " on" : ""}`} data-testid={`nav-${key}`}><Icon size={14} />{label}</NavLink>
    ))}
    <VersionTag />
  </footer>
);
