import { Kpi, fmtInt, fmtPct } from "@/components/Kpi";
import { getRespiratoryDashboard } from "@/lib/data";

function FreshnessBadge({ status }: { status?: string }) {
  const cls =
    status === "atual"
      ? "badge-sit1"
      : status === "atencao"
        ? "badge-warn"
        : status === "desatualizado"
          ? "badge-danger"
          : "badge-warn";
  return <span className={`badge ${cls}`}>{status || "desconhecido"}</span>;
}

export default async function RespiratorioPage() {
  const data = await getRespiratoryDashboard();

  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Imunização respiratória</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            VVSR materna · nirsevimabe · influenza · covid-19
          </p>
        </div>
        <div className="card p-6">
          <h2 className="text-lg font-semibold">Sem carga respiratória disponível</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            O módulo está configurado, mas ainda não há mart respiratório gerado. Execute o ETL
            respiratório em ambiente autorizado para produzir os agregados.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
            python etl/respiratory_etl.py
          </pre>
          <p className="mt-3 text-xs text-[var(--muted)]">
            O painel não fabrica cobertura ou oportunidade na ausência de denominadores clínicos
            compatíveis.
          </p>
        </div>
      </div>
    );
  }

  const v = data.vvsr_materna;
  const n = data.nirsevimab;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Imunização respiratória</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Indicadores observados de VVSR materna e nirsevimabe. Influenza e covid-19 permanecem em
          onboarding normativo e de dados.
        </p>
      </div>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">VVSR materna</h2>
          <FreshnessBadge status={v.provenance?.freshness?.status} />
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <Kpi label="Doses administradas" value={fmtInt(v.total_doses)} />
          <Kpi label="Gestantes vacinadas" value={fmtInt(v.total_pessoas)} />
          <Kpi label="Competência" value={v.reference_period || "—"} />
          <Kpi
            label="Idade do dado"
            value={
              v.provenance?.freshness?.age_days == null
                ? "—"
                : `${v.provenance.freshness.age_days} dias`
            }
          />
        </div>

        <div className="card table-wrap p-2">
          <h3 className="px-2 py-2 text-sm font-semibold">Top UFs por doses</h3>
          <table className="data">
            <thead>
              <tr>
                <th>UF</th>
                <th>Doses</th>
                <th>Pessoas</th>
              </tr>
            </thead>
            <tbody>
              {[...v.por_uf]
                .sort((a, b) => b.doses - a.doses)
                .slice(0, 10)
                .map((row) => (
                  <tr key={row.uf}>
                    <td>{row.uf}</td>
                    <td className="kpi-value">{fmtInt(row.doses)}</td>
                    <td className="kpi-value">{fmtInt(row.pessoas)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="card p-4 text-xs text-[var(--muted)]">
          Cobertura por gestação, oportunidade a partir da 28ª semana e administração precoce
          dependem de idade gestacional e gestação corrente em fonte compatível. Esses indicadores
          não são inferidos apenas do PNI/RNDS.
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">Nirsevimabe</h2>
          <FreshnessBadge status={n.provenance?.freshness?.status} />
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <Kpi label="Administrações" value={fmtInt(n.total_doses)} />
          <Kpi label="Crianças distintas" value={fmtInt(n.total_pessoas)} />
          <Kpi label="P/T1" value={fmtInt(n.pt1_doses)} hint="Uma unidade/seringa" />
          <Kpi label="P/T2" value={fmtInt(n.pt2_doses)} hint="Duas unidades/seringas" />
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <Kpi label="Estratégia SUS" value={fmtInt(n.sus_doses)} />
          <Kpi label="Serviço privado" value={fmtInt(n.private_doses)} />
          <Kpi
            label="Participação privada"
            value={fmtPct(n.private_share_pct)}
            hint="Estratégia 8 entre registros 2/8"
          />
        </div>

        <div className="card table-wrap p-2">
          <h3 className="px-2 py-2 text-sm font-semibold">Top UFs por administrações</h3>
          <table className="data">
            <thead>
              <tr>
                <th>UF</th>
                <th>Doses</th>
                <th>Pessoas</th>
              </tr>
            </thead>
            <tbody>
              {[...n.por_uf]
                .sort((a, b) => b.doses - a.doses)
                .slice(0, 10)
                .map((row) => (
                  <tr key={row.uf}>
                    <td>{row.uf}</td>
                    <td className="kpi-value">{fmtInt(row.doses)}</td>
                    <td className="kpi-value">{fmtInt(row.pessoas)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="card table-wrap p-2">
          <h3 className="px-2 py-2 text-sm font-semibold">Grupos de atendimento registrados</h3>
          <table className="data">
            <thead>
              <tr>
                <th>Código</th>
                <th>Registros</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(n.grupos_atendimento)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .map(([code, value]) => (
                  <tr key={code}>
                    <td className="font-mono text-xs">{code}</td>
                    <td className="kpi-value">{fmtInt(value)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="card p-4 text-xs text-[var(--muted)]">
          Cobertura em elegíveis ainda não é exibida. Prematuridade e comorbidades exigem fonte
          clínica compatível ou proxy explicitamente classificado, com deduplicação válida.
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Qualidade e proveniência</h2>
        <div className="mt-3 grid gap-3 text-xs md:grid-cols-2">
          <div>
            <div className="font-medium">VVSR materna</div>
            <div className="mt-1 text-[var(--muted)]">
              source_id: {v.provenance?.source_id || "—"} · run_id:{" "}
              {v.provenance?.run_id || "—"}
            </div>
          </div>
          <div>
            <div className="font-medium">Nirsevimabe</div>
            <div className="mt-1 text-[var(--muted)]">
              source_id: {n.provenance?.source_id || "—"} · run_id:{" "}
              {n.provenance?.run_id || "—"}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
