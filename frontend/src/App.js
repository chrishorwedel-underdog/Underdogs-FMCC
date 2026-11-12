import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
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
import Features from "@/pages/Features";
import TransferMarket from "@/pages/TransferMarket";
import ClubAnalysis from "@/pages/ClubAnalysis";
import { DossierHost } from "@/components/analysis/Dossier";
import { CommandPalette } from "@/components/CommandPalette";
import { ComingSoon } from "@/components/ComingSoon";
import { ModuleGuide, NeedSave } from "@/components/ModuleGuide";
import { PageCountdown } from "@/components/Notify";
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
import DynamicPotentialPage from "@/pages/DynamicPotentialPage";
import BreakoutPage from "@/pages/BreakoutPage";
import Connections from "@/pages/Connections";
import Safety from "@/pages/Safety";
import Extras from "@/pages/Extras";
import Appearance from "@/pages/Appearance";
import PlayerTeamsEditor from "@/pages/PlayerTeamsEditor";
import Changes from "@/pages/Changes";
import Matches from "@/pages/Matches";
import Dof from "@/pages/Dof";
import Punish from "@/pages/Punish";

const LATER = [];

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
        <FinanceStrip />
        <div className="content" id="main-content" tabIndex={-1} role="main">
          <NeedSave state={state} />
          <ModuleGuide />
          <PageCountdown />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/squad" element={<Squad />} />
            <Route path="/settings" element={<Settings state={state} />} />
            <Route path="/scouting" element={<Scouting key="scouting" />} />
            <Route path="/moneyball" element={<Navigate to="/scouting?tab=moneyball" replace />} />
            <Route path="/development" element={<Development />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/elite-training" element={<EliteTraining />} />
            <Route path="/dynamic-potential" element={<DynamicPotentialPage />} />
            <Route path="/breakout" element={<BreakoutPage />} />
            <Route path="/awards" element={<Navigate to="/dynamic-potential" replace />} />
            <Route path="/connections" element={<Connections />} />
            <Route path="/safety" element={<Safety />} />
            <Route path="/extras" element={<Extras />} />
            <Route path="/appearance" element={<Appearance />} />
            <Route path="/features" element={<Features />} />
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
      {state.career && <DossierHost />}
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
