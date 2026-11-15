import { ChevronDown, ChevronUp } from "lucide-react";
import { usePersist } from "@/lib/remember";

// A Home section with a remembered open/closed state.
export const HomeSection = ({ id, title, sub, children }) => {
  const [shut, setShut] = usePersist(`home-shut:${id}`, false);
  return (
    <section className="home-sec" data-testid={`home-section-${id}`}>
      <button className="home-sec-head" onClick={() => setShut(!shut)} aria-expanded={!shut} data-testid={`home-section-${id}-toggle`}>
        <b>{title}</b>{sub && <span>{sub}</span>}{shut ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
      </button>
      {!shut && children}
    </section>
  );
};
