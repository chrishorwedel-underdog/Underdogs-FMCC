import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/sonner";
import { api } from "@/lib/api";
import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";
import { CommandPalette } from "@/components/CommandPalette";
import { ComingSoon } from "@/components/ComingSoon";
import Setup from "@/pages/Setup";
import Home from "@/pages/Home";
import Squad from "@/pages/Squad";
import Settings from "@/pages/Settings";
import Scouting from "@/pages/Scouting";
import Development from "@/pages/Development";
import Reports from "@/pages/Reports";
import EliteTraining from "@/pages/EliteTraining";
import Awards from "@/pages/Awards";
import Changes from "@/pages/Changes";

const LATER = [["/matches", "matches"], ["/dof", "dof"]];

const Shell = ({ state }) => {
  const [pal, setPal] = useState(false);
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPal(true); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  return (
    <div className="app grain">
      <Sidebar />
      <section className="main">
        <TopBar career={state.career} onSearch={() => setPal(true)} />
        <div className="content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/squad" element={<Squad />} />
            <Route path="/settings" element={<Settings state={state} />} />
            <Route path="/scouting" element={<Scouting />} />
            <Route path="/development" element={<Development />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/elite-training" element={<EliteTraining />} />
            <Route path="/awards" element={<Awards />} />
            <Route path="/changes" element={<Changes />} />
            {LATER.map(([p, k]) => <Route key={k} path={p} element={<ComingSoon k={k} />} />)}
            <Route path="*" element={<Home />} />
          </Routes>
        </div>
      </section>
      <CommandPalette open={pal} onClose={() => setPal(false)} />
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
