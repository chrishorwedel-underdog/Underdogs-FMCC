import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { api, gameDate } from "@/lib/api";

const Fact = ({ k, v, id }) => <div className="row"><span style={{ color: "var(--mut)", flex: 1 }}>{k}</span><b data-testid={id}>{v}</b></div>;

export const PlayerSheet = ({ uid, onClose }) => {
  const { data } = useQuery({ queryKey: ["player", uid], queryFn: () => api.get(`/players/${uid}`).then((r) => r.data), enabled: !!uid });
  const p = data?.latest;
  return (
    <Sheet open={!!uid} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-[440px] sm:max-w-[440px] overflow-y-auto" style={{ background: "var(--s1)" }} data-testid="player-sheet">
        <SheetHeader>
          <SheetTitle data-testid="player-sheet-name">{data?.identity?.name}</SheetTitle>
          <SheetDescription>Game ID <span className="mono" data-testid="player-sheet-uid">{uid}</span> · matched across saves by this ID</SheetDescription>
        </SheetHeader>
        {p && (
          <div style={{ marginTop: 20 }}>
            <Fact k="Age" v={p.age} /><Fact k="Positions" v={p.positions.join(", ")} /><Fact k="Nationality" v={p.nationality} />
            <Fact k="Ability (CA / PA)" v={`${p.ca} / ${p.pa}`} id="player-sheet-ability" />
            <Fact k="Minutes this season" v={p.minutes} /><Fact k="Contract until" v={gameDate(p.contract_end, { day: "numeric", month: "short", year: "numeric" })} />
            <Fact k="First seen" v={gameDate(data.identity.first_seen_date)} />
          </div>
        )}
        {data?.role_ratings?.length > 0 && (
          <div className="card" style={{ marginTop: 20, padding: 14 }} data-testid="player-sheet-roles">
            <div className="ttl" style={{ marginBottom: 6 }}>Role ratings</div>
            <div className="mbars">{data.role_ratings.map((r) => (
              <div className="mb" key={r.role} style={{ gridTemplateColumns: "170px 1fr 30px" }}><span>{r.name} ({r.duty})</span>
                <div className="track"><i style={{ width: `${r.rating}%`, background: r.natural ? "var(--acc)" : "var(--mut)" }} /></div><span className="mono">{r.rating}</span></div>))}</div>
          </div>
        )}
        {data?.history?.length > 0 && (
          <div className="card" style={{ marginTop: 20, padding: 14 }}>
            <div className="ttl" style={{ marginBottom: 10 }}>Ability across saves</div>
            <div style={{ height: 180 }} data-testid="player-sheet-chart">
              <ResponsiveContainer>
                <LineChart data={data.history.map((h) => ({ ...h, label: gameDate(h.game_date, { month: "short" }) }))}>
                  <XAxis dataKey="label" stroke="#5C626C" fontSize={11} tickLine={false} />
                  <YAxis stroke="#5C626C" fontSize={11} domain={["dataMin - 3", "dataMax + 3"]} width={32} tickLine={false} />
                  <Tooltip contentStyle={{ background: "#121519", border: "1px solid rgba(255,255,255,.13)", borderRadius: 10, fontSize: 12 }} />
                  <Line type="monotone" dataKey="ca" name="Ability" stroke="#4C8DFF" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
};
