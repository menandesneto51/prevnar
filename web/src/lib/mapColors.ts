/** Escala de gap — tema claro JAMBRO/IPADS */

export const GAP_SCALE = [
  { color: "#c5d0e0", label: "Sem dado / baixo" },
  { color: "#7fa0d4", label: "Baixo" },
  { color: "#4a6aaf", label: "Médio" },
  { color: "#c77700", label: "Alto" },
  { color: "#c62828", label: "Crítico" },
] as const;

export function gapFill(gap: number | null | undefined, max: number): string {
  if (gap == null || max <= 0) return GAP_SCALE[0].color;
  const t = Math.min(1, Math.max(0, gap / max));
  if (t < 0.2) return GAP_SCALE[1].color;
  if (t < 0.45) return GAP_SCALE[2].color;
  if (t < 0.75) return GAP_SCALE[3].color;
  return GAP_SCALE[4].color;
}

export function fmtGapShort(n: number | null | undefined): string {
  if (n == null) return "—";
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)} mi`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(0)} mil`;
  return n.toLocaleString("pt-BR");
}
