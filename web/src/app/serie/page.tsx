import { Kpi, fmtInt, fmtPct } from "@/components/Kpi";
import { getNacional } from "@/lib/data";

type SerieLinha = {
  ano_mes: string;
  uf: string;
  doses: Record<string, number>;
  share_pct: Record<string, number>;
};

type Nacional = {
  serie_transicao?: {
    fonte?: string;
    linhas?: SerieLinha[];
    codigos?: Record<string, string>;
  };
};

export default async function SeriePage() {
  const data = (await getNacional()) as Nacional;
  const linhas = data.serie_transicao?.linhas || [];
  // agregar nacional por mês
  const byMes: Record<string, Record<string, number>> = {};
  for (const r of linhas) {
    const b = byMes[r.ano_mes] || {};
    for (const [k, v] of Object.entries(r.doses || {})) {
      b[k] = (b[k] || 0) + v;
    }
    byMes[r.ano_mes] = b;
  }
  const meses = Object.entries(byMes).sort(([a], [b]) => a.localeCompare(b));
  const last = meses[meses.length - 1]?.[1] || {};
  const totalLast = Object.values(last).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Série histórica · transição pneumocócica</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Share de doses VPC10 / VPC13 / VPP23 / VPC20 a partir do cache PNI. Fonte:{" "}
          {data.serie_transicao?.fonte || "—"}.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(last).map(([nome, n]) => (
          <Kpi
            key={nome}
            label={nome}
            value={fmtInt(n)}
            hint={`share ${fmtPct((100 * n) / totalLast)}`}
            tone={nome === "VPC20" ? "accent" : "default"}
          />
        ))}
      </div>

      <div className="card table-wrap p-2">
        <table className="data">
          <thead>
            <tr>
              <th>Mês</th>
              <th>VPC10</th>
              <th>VPC13</th>
              <th>VPP23?</th>
              <th>VPC20</th>
              <th>Share VPC20</th>
            </tr>
          </thead>
          <tbody>
            {meses.map(([mes, doses]) => {
              const t = Object.values(doses).reduce((a, b) => a + b, 0) || 1;
              return (
                <tr key={mes}>
                  <td className="font-mono">{mes}</td>
                  <td className="kpi-value">{fmtInt(doses["VPC10"] || 0)}</td>
                  <td className="kpi-value">{fmtInt(doses["VPC13"] || 0)}</td>
                  <td className="kpi-value">{fmtInt(doses["VPP23?"] || 0)}</td>
                  <td className="kpi-value text-[var(--accent)]">{fmtInt(doses["VPC20"] || 0)}</td>
                  <td className="kpi-value">{fmtPct((100 * (doses["VPC20"] || 0)) / t)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
