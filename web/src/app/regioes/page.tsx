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
  oportunidades_estimadas_rateadas?: number;
  pessoas_vacinadas: number;
  gap: number | null;
  gap_pessoas?: number | null;
};

export default async function RegioesPage() {
  const data = (await getNacional()) as {
    kpis?: { regioes_saude?: number; municipios_vac_com_rs?: number };
    gap_regiao_saude?: Row[];
    qualidade?: { regiao_saude_nota?: string; regiao_saude_fonte?: string };
  };
  const rows = data.gap_regiao_saude || [];
  const top = rows.slice(0, 50);
  const oportunidadesTotal = rows.reduce(
    (a, r) => a + (r.oportunidades_estimadas_rateadas ?? r.elegiveis_rateados),
    0,
  );
  const vacTotal = rows.reduce((a, r) => a + r.pessoas_vacinadas, 0);
  const comVac = rows.filter((r) => r.pessoas_vacinadas > 0).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Oportunidades estimadas por região de saúde</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Oportunidades da UF rateadas pela população IBGE 2022 da região; vacinados VPC20 via
          município→RS. O rateio é ecológico e não representa pessoas únicas elegíveis.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Regiões de saúde" value={fmtInt(data.kpis?.regioes_saude ?? rows.length)} />
        <Kpi label="Com vacinado VPC20" value={fmtInt(comVac)} tone="accent" />
        <Kpi label="Vacinados (soma RS)" value={fmtInt(vacTotal)} tone="accent" />
        <Kpi
          label="Oportunidades estimadas (soma)"
          value={fmtInt(oportunidadesTotal)}
          tone="warn"
        />
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
        <h2 className="px-2 py-2 text-sm font-semibold">Top 50 por oportunidades estimadas</h2>
        <table className="data">
          <thead>
            <tr>
              <th>UF</th>
              <th>Região de saúde</th>
              <th>Macrorregião</th>
              <th>Mun.</th>
              <th>Pop. 2022</th>
              <th>Oportunidades*</th>
              <th>Vacinados</th>
              <th>Gap pessoas</th>
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
                <td className="kpi-value">
                  {fmtInt(r.oportunidades_estimadas_rateadas ?? r.elegiveis_rateados)}
                </td>
                <td className="kpi-value text-[var(--accent)]">
                  {fmtInt(r.pessoas_vacinadas)}
                </td>
                <td className="kpi-value text-[var(--warn)]">
                  {r.gap_pessoas == null ? "não disponível" : fmtInt(r.gap_pessoas)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
