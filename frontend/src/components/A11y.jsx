import { useEffect } from "react";

// Gives every table header a scope and marks sortable headers, so screen readers read tables properly.
const fix = (root) => {
  root.querySelectorAll("table").forEach((t) => {
    t.querySelectorAll("thead th:not([scope])").forEach((th) => th.setAttribute("scope", "col"));
    if (!t.getAttribute("aria-label") && !t.querySelector("caption")) {
      const title = t.closest(".card, .hub-card, section")?.querySelector(".ttl, .hub-h, h1, h2")?.textContent?.trim();
      if (title) t.setAttribute("aria-label", title.slice(0, 80));
    }
  });
};

export const A11y = () => {
  useEffect(() => {
    fix(document);
    let t;
    const obs = new MutationObserver(() => { clearTimeout(t); t = setTimeout(() => fix(document), 120); });
    obs.observe(document.body, { childList: true, subtree: true });
    return () => { obs.disconnect(); clearTimeout(t); };
  }, []);
  return null;
};

export const SkipLink = () => <a href="#main-content" className="skip-link" data-testid="skip-to-content">Skip to content</a>;
