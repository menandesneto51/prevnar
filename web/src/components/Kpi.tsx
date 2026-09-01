import { fmtInt, fmtPct } from "@/lib/data";

export function Kpi({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "accent" | "warn" | "danger";
}) {
  const color =
    tone === "accent"
      ? "text-[var(--accent)]"
      : tone === "warn"
        ? "text-[var(--warn)]"
        : tone === "danger"
          ? "text-[var(--danger)]"
          : "text-[var(--primary-deep)]";
  return (
    <div className="kpi-card text-left">
      <div className="rotulo text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
        {label}
      </div>
      <div className={`kpi-value mt-2 text-2xl font-bold md:text-3xl ${color}`}>{value}</div>
      {hint ? <div className="mt-2 text-xs text-[var(--muted)]">{hint}</div> : null}
    </div>
  );
}

export function SituacaoBadge({ n }: { n: number }) {
  const cls = n === 1 ? "badge-sit1" : n === 2 ? "badge-sit2" : "badge-sit3";
  const label =
    n === 1 ? "Sit. 1 · cadastro" : n === 2 ? "Sit. 2 · prevalência" : "Sit. 3 · estimativa";
  return <span className={`badge ${cls}`}>{label}</span>;
}

export { fmtInt, fmtPct };
