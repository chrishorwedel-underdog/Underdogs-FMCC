import { useEffect, useState } from "react";
import { Sprout, Wand2 } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { SeedResults, SeedHistory } from "./SeedResults";
import { autoDownload } from "@/lib/autoDownload";
import { POS_WEIGHTS, STAFF_WEIGHTS, PLAYER_AGE_PRESETS, STAFF_AGE_PRESETS, split, Step, Stepper, Seg, CountGrid, Shares, Nations } from "./SeedParts";

const STORE = "fmcc-seed-form";
const DEFAULT = { surname: "", mode: null, playerTotal: 10, staffTotal: 3, posMode: "Balanced squad", players: {}, staffMode: "Typical backroom", staff: {},
  nations: [{ nation: "England", share: 5 }], pAge: "Balanced", sAge: "Balanced", player_ages: {}, staff_ages: {}, ethnicities: {},
  skin_lo: 1, skin_hi: 20, height_lo: 170, height_hi: 192, ca_lo: 30, ca_hi: 60, pa_lo: 60, pa_hi: 100, include_own_club: false, faces: true };
const sum = (o) => Object.values(o).reduce((a, b) => a + (Number(b) || 0), 0);
const load = () => { try { return { ...DEFAULT, ...JSON.parse(localStorage.getItem(STORE) || "{}") }; } catch { return DEFAULT; } };

const Range = ({ f, set, lo, hi, label, min, max }) => (
  <label className="note" style={{ display: "grid", gap: 4 }}>{label}
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      {[lo, hi].map((k, i) => <span key={k} style={{ display: "contents" }}>{i === 1 && "to"}<input className="inp mono" style={{ width: 70, height: 32 }} type="number" min={min} max={max} value={f[k]}
        onChange={(e) => set({ [k]: Math.max(min, Math.min(max, Number(e.target.value) || min)) })} data-testid={`seed-${k}`} /></span>)}</div></label>
);

const build = (f, mode) => {
  const players = f.posMode === "Balanced squad" ? split(f.playerTotal, POS_WEIGHTS) : f.players;
  const staff = f.staffMode === "Typical backroom" ? split(f.staffTotal, STAFF_WEIGHTS) : f.staff;
  const total = sum(players) + sum(staff);
  const counts = split(total, Object.fromEntries(f.nations.map((n) => [n.nation, n.share])));
  return { body: { surname: f.surname, mode, players, staff, nations: f.nations.map((n) => ({ nation: n.nation, count: counts[n.nation] || 0 })).filter((n) => n.count),
    ethnicities: Object.entries(f.ethnicities).filter(([, s]) => s > 0).map(([ethnicity, share]) => ({ ethnicity, share })),
    player_ages: f.pAge === "Custom" ? f.player_ages : PLAYER_AGE_PRESETS[f.pAge], staff_ages: f.sAge === "Custom" ? f.staff_ages : STAFF_AGE_PRESETS[f.sAge],
    ...Object.fromEntries(["skin_lo", "skin_hi", "height_lo", "height_hi", "ca_lo", "ca_hi", "pa_lo", "pa_hi", "include_own_club", "faces"].map((k) => [k, f[k]])) }, total, counts };
};

export const SeedTab = () => {
  const { data: meta } = useGet("seed-meta", "/seed/meta");
  const { data: draft, refetch } = useGet("seed-draft", "/seed/draft");
  const act = useAct();
  const [f, setF] = useState(load);
  useEffect(() => { localStorage.setItem(STORE, JSON.stringify(f)); }, [f]);
  const set = (p) => setF((x) => ({ ...x, ...p }));
  if (!meta) return null;
  const mode = f.mode || meta.suggested_mode;
  const { body, total, counts } = build(f, mode);
  const roles = Object.values(meta.staff).flat();
  const ready = f.surname.trim().length >= 2 && total > 0;
  const create = () => act(() => api.post("/seed/create", { ...body, seed: Math.floor(Math.random() * 999999) }), (r) => `${r.people.length} ${r.mode === "new" ? "people created" : "people picked"}. Check them below`, ["seed-draft"]);
  const apply = () => window.confirm(draft.mode === "new" ? `Seed ${draft.people.length} new people called ${draft.surname} into a new-save file?` : `Rename ${draft.people.length} people in your save to ${draft.surname}?`)
    && act(() => api.post("/seed/apply"), (r) => (r.mode === "new" ? `${draft.surname} seeded: ${r.people.length} people${r.placed ? " placed in your FM editor data folder" : ""}. The file is downloading` : `${draft.surname} seeded: ${r.people.length - r.failed} people renamed${r.sample ? " in the SAMPLE save" : ""}`), ["seed-draft", "seed-history", "editor-state"])
      .then((r) => r?.mode === "new" && autoDownload(`/seed/history/${r.id}/file`, r.file_name));
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: 16 }} data-testid="seed-tab">
      <div className="seed-hero"><Sprout size={22} /><div><b>Seed a Surname</b><small className="note">Spread one surname through the football world in four quick steps. Nothing goes into your game until you press Seed The Surname.</small></div></div>
      <Step n={1} title="Pick the surname" hint="And whether it goes into a brand-new save or the one you're playing" id="seed-step-1">
        <input className="inp seed-surname" maxLength={40} placeholder="e.g. Horwedel" value={f.surname} onChange={(e) => set({ surname: e.target.value })} data-testid="seed-surname" />
        <div className="seg" style={{ justifySelf: "start" }} data-testid="seed-mode">
          <button className={mode === "new" ? "on" : ""} onClick={() => set({ mode: "new" })} data-testid="seed-mode-new">New save</button>
          <button className={mode === "current" ? "on" : ""} onClick={() => set({ mode: "current" })} data-testid="seed-mode-current">Current save</button></div>
        <small className="note" data-testid="seed-mode-note">{mode === "new" ? "Creates brand-new players and staff. Pick FMCC's file from FM's database list when you start the new save." : `Renames existing low-profile people (free agents, youngsters, fringe players and backroom staff, never ${meta.club}'s). Their club, job, age and ability stay the same.`}</small>
      </Step>
      <Step n={2} title="How many people?" hint="FMCC spreads them across positions and jobs for you" id="seed-step-2">
        <div className="seed-steppers">
          <div style={{ display: "grid", gap: 10, alignContent: "start" }}>
            <Stepper label="Players" v={f.playerTotal} set={(v) => set({ playerTotal: v, ...(f.posMode === "Choose positions" ? { players: split(v, sum(f.players) ? f.players : POS_WEIGHTS) } : {}) })} picks={[5, 10, 25, 50, 100]} max={200} id="seed-players" />
            <Seg opts={["Balanced squad", "Choose positions"]} v={f.posMode} set={(v) => set({ posMode: v, players: v === "Choose positions" && !sum(f.players) ? split(f.playerTotal, POS_WEIGHTS) : f.players })} id="seed-posmode" />
            {f.posMode === "Choose positions" ? <CountGrid keys={meta.positions} vals={f.players} set={(v) => set({ players: v, playerTotal: sum(v) })} id="seed-pl" />
              : <small className="note" data-testid="seed-pos-summary">{Object.entries(split(f.playerTotal, POS_WEIGHTS)).map(([k, v]) => `${v} ${k}`).join(" · ") || "No players"}</small>}
          </div>
          <div style={{ display: "grid", gap: 10, alignContent: "start" }}>
            <Stepper label="Staff" v={f.staffTotal} set={(v) => set({ staffTotal: v, ...(f.staffMode === "Choose jobs" ? { staff: split(v, sum(f.staff) ? f.staff : STAFF_WEIGHTS) } : {}) })} picks={[0, 3, 5, 10, 20]} max={100} id="seed-staff" />
            <Seg opts={["Typical backroom", "Choose jobs"]} v={f.staffMode} set={(v) => set({ staffMode: v, staff: v === "Choose jobs" && !sum(f.staff) ? split(f.staffTotal, STAFF_WEIGHTS) : f.staff })} id="seed-staffmode" />
            {f.staffMode === "Choose jobs" ? <Accordion type="multiple" className="seed-acc">{Object.entries(meta.staff).map(([g, rs]) => <AccordionItem key={g} value={g}>
              <AccordionTrigger data-testid={`seed-staff-group-${g}`}>{g} <span className="st n" style={{ marginRight: 8 }}>{rs.reduce((a, r) => a + (f.staff[r] || 0), 0)}</span></AccordionTrigger>
              <AccordionContent><CountGrid keys={rs} vals={f.staff} set={(v) => set({ staff: v, staffTotal: roles.reduce((a, r) => a + (v[r] || 0), 0) })} id="seed-st" /></AccordionContent></AccordionItem>)}</Accordion>
              : <small className="note" data-testid="seed-staff-summary">{Object.entries(split(f.staffTotal, STAFF_WEIGHTS)).map(([k, v]) => `${v} ${k}`).join(" · ") || "No staff"}</small>}
          </div>
        </div>
      </Step>
      <Step n={3} title="Where are they from?" hint="Slide to give a nationality a bigger share; FMCC works out the numbers" id="seed-step-3">
        <Nations list={f.nations} set={(v) => set({ nations: v })} all={meta.nations} counts={counts} />
      </Step>
      <Step n={4} title="How old are they?" id="seed-step-4">
        <div style={{ display: "grid", gap: 6 }}><div className="eyebrow">Players</div><Seg opts={[...Object.keys(PLAYER_AGE_PRESETS), "Custom"]} v={f.pAge} set={(v) => set({ pAge: v, player_ages: v === "Custom" ? (f.pAge !== "Custom" ? PLAYER_AGE_PRESETS[f.pAge] : f.player_ages) : f.player_ages })} id="seed-page-preset" />
          {f.pAge === "Custom" && <Shares items={meta.player_ages.map((b) => [b.key, `${b.label} (${b.lo}–${b.hi})`])} vals={f.player_ages} set={(v) => set({ player_ages: v })} id="seed-page" />}</div>
        <div style={{ display: "grid", gap: 6 }}><div className="eyebrow">Staff</div><Seg opts={[...Object.keys(STAFF_AGE_PRESETS), "Custom"]} v={f.sAge} set={(v) => set({ sAge: v, staff_ages: v === "Custom" ? (f.sAge !== "Custom" ? STAFF_AGE_PRESETS[f.sAge] : f.staff_ages) : f.staff_ages })} id="seed-sage-preset" />
          {f.sAge === "Custom" && <Shares items={meta.staff_ages.map((b) => [b.key, `${b.label} (${b.lo}–${b.hi})`])} vals={f.staff_ages} set={(v) => set({ staff_ages: v })} id="seed-sage" />}</div>
      </Step>
      <Accordion type="single" collapsible className="card seed-adv" data-testid="seed-advanced">
        <AccordionItem value="adv" style={{ border: 0 }}>
          <AccordionTrigger data-testid="seed-advanced-toggle">Fine-tune looks, height and ability (optional)</AccordionTrigger>
          <AccordionContent><div style={{ display: "grid", gap: 16 }}>
            <div><div className="eyebrow" style={{ marginBottom: 6 }}>Ethnicity mix (all at 0 = typical for each nationality)</div><Shares items={meta.ethnicities.map((e) => [e, e])} vals={f.ethnicities} set={(v) => set({ ethnicities: v })} id="seed-eth" /></div>
            <div style={{ display: "flex", gap: 22, flexWrap: "wrap" }}>
              <Range f={f} set={set} lo="skin_lo" hi="skin_hi" label="Skin tone (1 light – 20 dark)" min={1} max={20} />
              <Range f={f} set={set} lo="height_lo" hi="height_hi" label="Player height (cm)" min={150} max={210} />
              <Range f={f} set={set} lo="ca_lo" hi="ca_hi" label={`Current ability (max ${meta.caps.ca})`} min={1} max={meta.caps.ca} />
              <Range f={f} set={set} lo="pa_lo" hi="pa_hi" label={`Potential ability (max ${meta.caps.pa})`} min={1} max={meta.caps.pa} />
            </div>
            {mode === "new" ? <label className="note" style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" checked={f.faces} onChange={(e) => set({ faces: e.target.checked })} data-testid="seed-faces" />Match NG_Regens faces for players</label>
              : <label className="note" style={{ display: "flex", gap: 8, alignItems: "center" }}><input type="checkbox" checked={f.include_own_club} onChange={(e) => set({ include_own_club: e.target.checked })} data-testid="seed-own-club" />Also rename {meta.club}'s low-profile people</label>}
          </div></AccordionContent>
        </AccordionItem>
      </Accordion>
      <div className="seed-bar" data-testid="seed-summary-bar">
        <div style={{ minWidth: 0 }}><b data-testid="seed-total">{f.surname.trim() || "Your surname"} · {total} {total === 1 ? "person" : "people"}</b>
          <small className="note">{sum(body.players)} players · {sum(body.staff)} staff · {f.nations.map((n) => `${n.nation} ${counts[n.nation] || 0}`).join(", ")} · {mode === "new" ? "new save" : "current save"}</small></div>
        <button className="btn btn-l" disabled={!ready} onClick={create} data-testid="seed-create"><Wand2 size={16} />Create</button>
        <button className="btn btn-g btn-l" disabled={!draft?.people?.length} onClick={apply} data-testid="seed-apply"><Sprout size={16} />Seed The Surname</button>
      </div>
      {draft?.people?.length > 0 && <SeedResults d={draft} meta={meta} act={act} onChange={refetch} />}
      <SeedHistory act={act} />
    </div>
  );
};
