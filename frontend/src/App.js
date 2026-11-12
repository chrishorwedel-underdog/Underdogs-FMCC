import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/sonner";
import { api } from "@/lib/api";
import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";
import { AppFooter } from "@/components/AppFooter";
import { WhatsNew } from "@/components/WhatsNew";
import { UpdateCard } from "@/components/VersionTag";
import { ClubColours } from "@/components/ClubColours";
import { FeatureGate } from "@/components/FeatureGate";
import { FinanceStrip } from "@/components/FinanceStrip";
import { A11y, SkipLink } from "@/components/A11y";
import { ScrollMemory } from "@/lib/remember";
import { useFeatures } from "@/lib/features";
import TransferMarket from "@/pages/TransferMarket";
import ClubAnalysis from "@/pages/ClubAnalysis";
import { PlayerPanelHost } from "@/components/player/PlayerPanel";
import { CommandPalette } from "@/components/CommandPalette";
import { ComingSoon } from "@/components/ComingSoon";
import { ModuleGuide, NeedSave } from "@/components/ModuleGuide";
import { Tour } from "@/components/Tour";
import { GlossaryHost } from "@/components/Glossary";
import Setup from "@/pages/Setup";
import Home from "@/pages/Home";
import Squad from "@/pages/Squad";
import Settings from "@/pages/Settings";
import Scouting from "@/pages/Scouting";
import Development from "@/pages/Development";
import Reports from "@/pages/Reports";
import EliteTraining from "@/pages/EliteTraining";
import Trophies from "@/pages/Trophies";
import DynamicPotentialPage from "@/pages/DynamicPotentialPage";
import BreakoutPage from "@/pages/BreakoutPage";
import Extras from "@/pages/Extras";
import PlayerTeamsEditor from "@/pages/PlayerTeamsEditor";
import Changes from "@/pages/Changes";
import Matches from "@/pages/Matches";
import Dof from "@/pages/Dof";
import Punish from "@/pages/Punish";

const LATER = [];
const MONEY = ["/", "/squad", "/scouting", "/transfer-market", "/club-analysis", "/matches"];

const ToSection = ({ section }) => {
  const { search } = useLocation();
  const q = new URLSearchParams(search);
  q.set("section", section);
  return <Navigate to={`/settings?${q}`} replace />;
};

const Finance = () => {
  const { pathname } = useLocation();
  return MONEY.includes(pathname) ? <FinanceStrip /> : null;
};

const Shell = ({ state }) => {
  const [pal, setPal] = useState(false);
  const { data: feats } = useFeatures();
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPal(true); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  return (
    <div className="app grain">
      <SkipLink />
      <A11y />
      <ScrollMemory />
      <Sidebar />
      <Tour ready={!!state.career && feats?.ask === false} />
      <section className="main">
        <TopBar career={state.career} sample={state.sample_mode} onSearch={() => setPal(true)} />
        <div className="content" id="main-content" tabIndex={-1} role="main">
          <NeedSave state={state} />
          <Finance />
          <ModuleGuide />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/squad" element={<Squad />} />
            <Route path="/settings" element={<Settings state={state} />} />
            <Route path="/scouting" element={<Scouting key="scouting" />} />
            <Route path="/moneyball" element={<Navigate to="/scouting?tab=moneyball" replace />} />
            <Route path="/development" element={<Development />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/elite-training" element={<EliteTraining />} />
            <Route path="/trophies" element={<Trophies />} />
            <Route path="/dynamic-potential" element={<DynamicPotentialPage />} />
            <Route path="/breakout" element={<BreakoutPage />} />
            <Route path="/awards" element={<Navigate to="/dynamic-potential" replace />} />
            <Route path="/connections" element={<ToSection section="connections" />} />
            <Route path="/safety" element={<ToSection section="safety" />} />
            <Route path="/extras" element={<Extras />} />
            <Route path="/appearance" element={<ToSection section="appearance" />} />
            <Route path="/features" element={<ToSection section="features" />} />
            <Route path="/transfer-market" element={<TransferMarket />} />
            <Route path="/club-analysis" element={<ClubAnalysis />} />
            <Route path="/editor" element={<PlayerTeamsEditor />} />
            <Route path="/changes" element={<Changes />} />
            <Route path="/matches" element={<Matches />} />
            <Route path="/dof" element={<Dof />} />
            <Route path="/punish" element={<Punish />} />
            {LATER.map(([p, k]) => <Route key={k} path={p} element={<ComingSoon k={k} />} />)}
            <Route path="*" element={<Home />} />
          </Routes>
        </div>
        <AppFooter />
      </section>
      <CommandPalette open={pal} onClose={() => setPal(false)} />
      <WhatsNew />
      <GlossaryHost />
      <UpdateCard />
      {state.career && <ClubColours />}
      {state.career && <FeatureGate />}
      {state.career && <PlayerPanelHost />}
    </div>
  );
};

function App() {
  const { data: state, isLoading, isError } = useQuery({ queryKey: ["state"], queryFn: () => api.get("/state").then((r) => r.data) });
  return (
    <BrowserRouter>
      {isLoading && <div className="setup"><p className="note">Starting FMCC…</p></div>}
      {isError && <div className="setup"><p className="note" data-testid="app-error">FMCC couldn't start. Please reload.</p></div>}
      {state && (state.setup_complete && state.career ? <Shell state={state} /> : <Setup />)}
      <Toaster theme="dark" position="bottom-right" />
    </BrowserRouter>
  );
}

export default App;
