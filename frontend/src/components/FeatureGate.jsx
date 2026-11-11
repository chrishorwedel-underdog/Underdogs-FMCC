import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useNotices } from "@/components/Notify";
import { useFeatures } from "@/lib/features";

const PATHS = { "/dynamic-potential": "dp", "/breakout": "breakout", "/scouting": "scouting", "/transfer-market": "market", "/club-analysis": "club", "/reports": "reports", "/moneyball": "moneyball", "/squad": "squad",
  "/development": "development", "/elite-training": "elite", "/matches": "matches", "/editor": "editor", "/punish": "punish", "/dof": "dof" };

export const FeatureGate = () => {
  const { pathname } = useLocation();
  const nav = useNavigate();
  const qc = useQueryClient();
  const { data: feats } = useFeatures();
  const badges = useNotices().data?.badges || [];
  useEffect(() => {
    if (!feats) { return; }
    if (feats.ask && pathname !== "/features") { nav("/features"); return; }
    const key = PATHS[pathname];
    if (key && feats.features[key] === false) { toast.info("Turned off for this career. Turn it on in Features."); nav("/"); }
  }, [feats, pathname]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (badges.includes(pathname)) { api.post("/notify/read-page", { path: pathname }).then(() => qc.invalidateQueries({ queryKey: ["notices"] })); }
  }, [pathname, badges.join()]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
};
