import { Kpi, fmtInt } from "@/components/Kpi";
import { getNacional } from "@/lib/data";

type Row = {
  uf: string;
  pop: number;
  pessoas_vacinadas_vpc20: number;
  sinan_casos: number;
  sih_internacoes: number;
  sim_obitos?: number;
  srag_casos?: number;
  sinan_100k: number | null;
  sih_100k: number | null;
  sim_100k?: number | null;
  srag_100k?: number | null;
  razao_doses_casos: number | null;
};

export default async function MonitoramentoPage() {
  const data = (await getNacional()) as {
    monitoramento_uf?: Row[];
    qualidade?: {
      sinan_nota?: string;
      sih_nota?: string;
      sim_nota?: string;
      srag_nota?: string;
    };
  };
  const rows = data.monitoramento_uf || [];
  const sinan = rows.reduce((a, r) => a + r.sinan_casos, 0);
  const sih = rows.reduce((a, r) => a + r.sih_internacoes, 0);
  const sim = rows.reduce((a, r) => a + (r.sim_obitos || 0), 0);
  const srag = rows.reduce((a, r) => a + (r.srag_casos || 0), 0);
  const vac = rows.reduce((a, r) => a + r.pessoas_vacinadas_vpc20, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Monitoramento · desfecho ecológico</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          SINAN meningite + SIH pneumocócico + SIM óbitos + SRAG, lado a lado com vacinados VPC20.
          Sem inferência causal.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
        <Kpi label="Vacinados VPC20" value={fmtInt(vac)} tone="accent" />
        <Kpi label="SINAN meningite" value={fmtInt(sinan)} />
        <Kpi label="SIH internações" value={fmtInt(sih)} tone="warn" />
        <Kpi label="SIM óbitos" value={fmtInt(sim)} />
        <Kpi label="SRAG (amostra)" value={fmtInt(srag)} />
        <Kpi
          label="Razão doses÷casos"
          value={
            rows.length
              ? (
                  rows.reduce((a, r) => a + (r.razao_doses_casos || 0), 0) / rows.length
                ).toFixed(2)
              : "—"
          }
          hint="SINAN+SIH · ecológico"
        />
      </div>

      <div className="card p-4">
        <h2 className="mb-2 text-sm font-semibold">Indicadores desta aba</h2>
        <ul className="list-disc space-y-1 pl-5 text-xs text-[var(--muted)]">
          <li>sinan_meningite_100k · sih_pneumo_100k · sim_pneumo_100k · srag_casos_100k</li>
          <li>razao_doses_casos — vacinados ÷ (SINAN+SIH) por UF</li>
        </ul>
      </div>

      {(data.qualidade?.sinan_nota ||
        data.qualidade?.sih_nota ||
        data.qualidade?.sim_nota ||
        data.qualidade?.srag_nota) && (
        <div className="card p-4 text-xs text-[var(--muted)]">
          {[
            data.qualidade?.sinan_nota,
            data.qualidade?.sih_nota,
            data.qualidade?.sim_nota,
            data.qualidade?.srag_nota,
          ]
            .filter(Boolean)
            .join(" · ")}
        </div>
      )}

      <div className="card table-wrap p-2">
        <table className="data">
          <thead>
            <tr>
              <th>UF</th>
              <th>Vacinados</th>
              <th>SINAN</th>
              <th>SIH</th>
              <th>SIM</th>
              <th>SRAG</th>
              <th>SRAG/100k</th>
              <th>Doses÷casos</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.uf}>
                <td className="font-bold">{r.uf}</td>
                <td className="kpi-value text-[var(--accent)]">
                  {fmtInt(r.pessoas_vacinadas_vpc20)}
                </td>
                <td className="kpi-value">{fmtInt(r.sinan_casos)}</td>
                <td className="kpi-value">{fmtInt(r.sih_internacoes)}</td>
                <td className="kpi-value">{fmtInt(r.sim_obitos || 0)}</td>
                <td className="kpi-value">{fmtInt(r.srag_casos || 0)}</td>
                <td className="kpi-value">{r.srag_100k ?? "—"}</td>
                <td className="kpi-value">{r.razao_doses_casos ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
