"use client";

import Link from "next/link";

/** Simplified Brazil choropleth using UF boxes by region (no heavy geo deps). */
const REGIOES: Record<string, string[]> = {
  Norte: ["RR", "AP", "AM", "PA", "AC", "RO", "TO"],
  Nordeste: ["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"],
  "Centro-Oeste": ["MT", "GO", "DF", "MS"],
  Sudeste: ["MG", "ES", "RJ", "SP"],
  Sul: ["PR", "SC", "RS"],
};

type UfDatum = {
  uf: string;
  gap: number | null;
  elegiveis: number;
  oportunidades_estimadas: number;
  pessoas_vacinadas: number;
};

function colorFor(value: number, max: number): string {
  if (max <= 0) return "#1a3a63";
  const t = Math.min(1, value / max);
  // navy → teal → warn
  if (t < 0.33) return "#7fa0d4";
  if (t < 0.66) return "#4a6aaf";
  return "#c77700";
}

export function BrazilUfGrid({ data }: { data: UfDatum[] }) {
  const map = Object.fromEntries(data.map((d) => [d.uf, d]));
  const max = Math.max(...data.map((d) => d.oportunidades_estimadas ?? d.elegiveis), 1);

  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">Oportunidades estimadas por UF</h2>
        <div className="flex items-center gap-2 text-[10px] text-[var(--muted)]">
          <span className="inline-block h-2 w-6 rounded" style={{ background: "#7fa0d4" }} /> baixo
          <span className="inline-block h-2 w-6 rounded" style={{ background: "#4a6aaf" }} /> médio
          <span className="inline-block h-2 w-6 rounded" style={{ background: "#c77700" }} /> alto
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Object.entries(REGIOES).map(([regiao, ufs]) => (
          <div key={regiao}>
            <div className="mb-2 text-xs uppercase tracking-wider text-[var(--muted)]">{regiao}</div>
            <div className="flex flex-wrap gap-1.5">
              {ufs.map((uf) => {
                const d = map[uf];
                const oportunidades = d?.oportunidades_estimadas ?? d?.elegiveis ?? 0;
                return (
                  <Link
                    key={uf}
                    href={`/ufs/${uf}`}
                    title={d ? `${uf}: oportunidades estimadas ${oportunidades.toLocaleString("pt-BR")}` : uf}
                    className="map-uf flex min-w-[3.2rem] flex-col items-center rounded-md px-2 py-1.5 text-center"
                    style={{ background: colorFor(oportunidades, max) }}
                  >
                    <span className="text-xs font-bold text-white">{uf}</span>
                    <span className="text-[10px] text-white/80">
                      {d ? (oportunidades / 1000).toFixed(0) + "k" : "—"}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
