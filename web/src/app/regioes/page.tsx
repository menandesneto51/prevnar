import { Kpi, fmtInt } from "@/components/Kpi";
import { getNacional } from "@/lib/data";

type Row = {
  codigo_regiao_saude: string;
  regiao_saude?: string;
  uf: string;
  macrorregiao_saude?: string;
  n_municipios?: number;
  pop_ibge_2022?: number;
  elegiveis_rateados: number;
  pessoas_vacinadas: number;
  gap: number;
};

export default async function RegioesPage() {
  const data = (await getNacional()) as {
    kpis?: { regioes_saude?: number; municipios_vac_com_rs?: number };
    gap_regiao_saude?: Row[];
    qualidade?: { regiao_saude_nota?: string; regiao_saude_fonte?: string };
  };
  const rows = data.gap_regiao_saude || [];
  const top = rows.slice(0, 50);
  const gapTotal = rows.reduce((a, r) => a + r.gap, 0);
  const vacTotal = rows.reduce((a, r) => a + r.pessoas_vacinadas, 0);
  const comVac = rows.filter((r) => r.pessoas_vacinadas > 0).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Gap por região de saúde</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Elegíveis da UF rateados pela população IBGE 2022 da região; vacinados VPC20 via
          município→RS (OpenDataSUS). Ecológico — sem denominador municipal próprio.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Regiões de saúde" value={fmtInt(data.kpis?.regioes_saude ?? rows.length)} />
        <Kpi label="Com vacinado VPC20" value={fmtInt(comVac)} tone="accent" />
        <Kpi label="Vacinados (soma RS)" value={fmtInt(vacTotal)} tone="accent" />
        <Kpi label="Gap rateado (soma)" value={fmtInt(gapTotal)} tone="warn" />
      </div>

      {(data.qualidade?.regiao_saude_nota || data.qualidade?.regiao_saude_fonte) && (
        <div className="card p-4 text-xs text-[var(--muted)]">
          {data.qualidade?.regiao_saude_nota}
          {data.qualidade?.regiao_saude_fonte ? (
            <div className="mt-1 font-mono">{data.qualidade.regiao_saude_fonte}</div>
          ) : null}
          <div className="mt-1">
            Municípios do numerador com match RS: {data.kpis?.municipios_vac_com_rs ?? "—"}
          </div>
        </div>
      )}

      <div className="card table-wrap p-2">
        <h2 className="px-2 py-2 text-sm font-semibold">Top 50 por gap</h2>
        <table className="data">
          <thead>
            <tr>
              <th>UF</th>
              <th>Região de saúde</th>
              <th>Macrorregião</th>
              <th>Mun.</th>
              <th>Pop. 2022</th>
              <th>Elegíveis*</th>
              <th>Vacinados</th>
              <th>Gap</th>
            </tr>
          </thead>
          <tbody>
            {top.map((r) => (
              <tr key={r.codigo_regiao_saude}>
                <td className="font-bold">{r.uf}</td>
                <td>
                  <div>{r.regiao_saude}</div>
                  <div className="font-mono text-xs text-[var(--muted)]">
                    {r.codigo_regiao_saude}
                  </div>
                </td>
                <td className="text-xs">{r.macrorregiao_saude || "—"}</td>
                <td className="kpi-value">{r.n_municipios ?? "—"}</td>
                <td className="kpi-value">{fmtInt(r.pop_ibge_2022)}</td>
                <td className="kpi-value">{fmtInt(r.elegiveis_rateados)}</td>
                <td className="kpi-value text-[var(--accent)]">
                  {fmtInt(r.pessoas_vacinadas)}
                </td>
                <td className="kpi-value text-[var(--warn)]">{fmtInt(r.gap)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
