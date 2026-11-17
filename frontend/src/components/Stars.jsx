import { Star, StarHalf } from "lucide-react";

export const Stars = ({ value, size = 12, id }) => {
  const v = Math.max(0, Math.min(5, value || 0));
  const full = Math.floor(v), half = v - full >= 0.5;
  return (
    <span className="stars" role="img" aria-label={`${v} of 5 stars`} title={`${v} of 5 stars`} data-testid={id}>
      {Array.from({ length: 5 }, (_, i) => (i < full ? <Star key={i} size={size} className="on" />
        : i === full && half ? <span key={i} className="half"><Star size={size} /><StarHalf size={size} className="on" /></span> : <Star key={i} size={size} />))}
    </span>
  );
};

export const OopTag = ({ id }) => <span className="tag st a" title="Doesn't play here naturally; covering a short position" data-testid={id}>Out of position</span>;
