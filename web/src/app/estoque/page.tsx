import { Kpi, fmtInt, fmtPct } from "@/components/Kpi";
import { getNacional } from "@/lib/data";

type Row = {
  uf: string;
  distribuidas: number;
  aplicadas: number;
  razao_dist_aplic: number | null;
  doses_por_crie?: number | null;
  pct_fora_crie?: number | null;
  n_cries_seed?: number | null;
};

export default async function EstoquePage() {
  const data = (await getNacional()) as {
    kpis?: { doses_por_crie?: number | null; pct_fora_crie?: number | null };
    estoque_uf?: Row[];
    sies_resumo?: { por_classe_insumo?: Record<string, number>; nota?: string };
    qualidade?: { sies_nota?: string };
  };
  const rows = data.estoque_uf || [];
  const dist = rows.reduce((a, r) => a + r.distribuidas, 0);
  const apl = rows.reduce((a, r) => a + r.aplicadas, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Estoque · SIES + oferta CRIE</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Doses distribuídas (SIES) vs aplicadas (numerador VPC20), com doses por CRIE e % fora
          do CNES CRIE.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Kpi label="Distribuídas (seed/API)" value={fmtInt(dist)} />
        <Kpi label="Aplicadas" value={fmtInt(apl)} tone="accent" />
        <Kpi
          label="Razão dist÷aplic"
          value={apl ? (dist / apl).toFixed(2) : "—"}
          tone="warn"
        />
        <Kpi
          label="Doses / CRIE (nac.)"
          value={
            data.kpis?.doses_por_crie == null
              ? "—"
              : String(data.kpis.doses_por_crie)
          }
        />
        <Kpi
          label="% fora CRIE"
          value={
            data.kpis?.pct_fora_crie == null ? "—" : fmtPct(data.kpis.pct_fora_crie)
          }
        />
      </div>

      {(data.qualidade?.sies_nota || data.sies_resumo?.nota) && (
        <div className="card p-4 text-xs text-[var(--muted)]">
          {data.qualidade?.sies_nota || data.sies_resumo?.nota}
          {data.sies_resumo?.por_classe_insumo ? (
            <div className="mt-2 font-mono">
              {Object.entries(data.sies_resumo.por_classe_insumo)
                .map(([k, v]) => `${k}: ${v}`)
                .join(" · ")}
            </div>
          ) : null}
        </div>
      )}

      <div className="card table-wrap p-2">
        <table className="data">
          <thead>
            <tr>
              <th>UF</th>
              <th>Distribuídas</th>
              <th>Aplicadas</th>
              <th>Dist÷Aplic</th>
              <th>CRIEs</th>
              <th>Doses/CRIE</th>
              <th>% fora CRIE</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.uf}>
                <td className="font-bold">{r.uf}</td>
                <td className="kpi-value">{fmtInt(r.distribuidas)}</td>
                <td className="kpi-value text-[var(--accent)]">{fmtInt(r.aplicadas)}</td>
                <td className="kpi-value">{r.razao_dist_aplic ?? "—"}</td>
                <td className="kpi-value">{r.n_cries_seed ?? "—"}</td>
                <td className="kpi-value">{r.doses_por_crie ?? "—"}</td>
                <td className="kpi-value">
                  {r.pct_fora_crie == null ? "—" : fmtPct(r.pct_fora_crie)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
