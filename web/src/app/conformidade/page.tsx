import { Kpi, fmtInt } from "@/components/Kpi";
import { getRegulatoryCompliance } from "@/lib/data";

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; cls: string }> = {
    within_benchmark: { label: "na janela", cls: "badge-sit1" },
    benchmark_exceeded_mapping_pending: {
      label: "benchmark excedido · pendente",
      cls: "badge-danger",
    },
    benchmark_exceeded_mapping_complete: {
      label: "benchmark excedido · mapeado",
      cls: "badge-warn",
    },
    date_unavailable: { label: "data indisponível", cls: "badge-warn" },
  };
  const current = config[status] || { label: status, cls: "badge-warn" };
  return <span className={`badge ${current.cls}`}>{current.label}</span>;
}

export default async function ConformidadePage() {
  const data = await getRegulatoryCompliance();

  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Conformidade regulatória</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Benchmark interno para mudanças nas regras vacinais e interoperabilidade.
          </p>
        </div>
        <div className="card p-6">
          <h2 className="text-lg font-semibold">Benchmark ainda não gerado</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Execute o gerador para consolidar o estado regulatório atual.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
            python etl/regulatory_compliance.py
          </pre>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Conformidade regulatória</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Benchmark interno em {data.as_of} · janela de {data.benchmark_days} dias para
          acompanhamento de revisões técnicas.
        </p>
      </div>

      <section className="grid gap-3 md:grid-cols-4">
        <Kpi label="Atos rastreados" value={fmtInt(data.summary.tracked_acts)} />
        <Kpi
          label="Na janela interna"
          value={fmtInt(data.summary.within_benchmark)}
          tone="accent"
        />
        <Kpi
          label="Prazo interno excedido · pendente"
          value={fmtInt(data.summary.benchmark_exceeded_mapping_pending)}
          tone={data.summary.benchmark_exceeded_mapping_pending ? "danger" : "accent"}
        />
        <Kpi
          label="Prazo interno excedido · mapeado"
          value={fmtInt(data.summary.benchmark_exceeded_mapping_complete)}
          tone="warn"
        />
      </section>

      <section className="card p-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge badge-warn">Aplicabilidade jurídica</span>
          <span className="text-sm text-[var(--muted)]">
            {data.applicability?.prevnar_treatment || "internal_regulatory_benchmark"}
          </span>
        </div>
        <p className="mt-3 text-sm">
          {data.applicability?.direct_legal_scope ||
            "A Portaria se aplica aos sistemas e atores definidos no art. 312-A."}
        </p>
        <p className="mt-2 text-xs text-[var(--muted)]">
          {data.applicability?.warning ||
            "Este painel não declara automaticamente conformidade ou infração jurídica."}
        </p>
      </section>

      <section className="card p-4 text-xs text-[var(--muted)]">
        {data.interpretation}
      </section>

      <section className="card table-wrap p-2">
        <h2 className="px-2 py-2 text-sm font-semibold">Mudanças regulatórias rastreadas</h2>
        <table className="data">
          <thead>
            <tr>
              <th>Ato</th>
              <th>Publicação</th>
              <th>Marco interno</th>
              <th>Status</th>
              <th>Imunobiológico</th>
              <th>Pendência de mapeamento</th>
              <th>Fonte</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((row) => (
              <tr key={row.act_id}>
                <td>
                  <div className="font-medium">{row.number || row.act_id}</div>
                  <div className="mt-1 font-mono text-xs text-[var(--muted)]">
                    {row.act_id}
                  </div>
                </td>
                <td>{row.published_at || "—"}</td>
                <td>
                  <div>{row.benchmark_deadline || "—"}</div>
                  {row.days_to_benchmark_deadline != null ? (
                    <div className="mt-1 text-xs text-[var(--muted)]">
                      {row.days_to_benchmark_deadline >= 0
                        ? `${row.days_to_benchmark_deadline} dia(s) restantes`
                        : `${Math.abs(row.days_to_benchmark_deadline)} dia(s) após o benchmark`}
                    </div>
                  ) : null}
                </td>
                <td>
                  <StatusBadge status={row.benchmark_status} />
                </td>
                <td className="font-mono text-xs">
                  {row.immunobiologic_ids.length
                    ? row.immunobiologic_ids.join(", ")
                    : "—"}
                </td>
                <td className="font-mono text-xs">
                  {row.mapping_pending_immunobiologic_ids.length
                    ? row.mapping_pending_immunobiologic_ids.join(", ")
                    : "—"}
                </td>
                <td>
                  {row.official_url ? (
                    <a
                      href={row.official_url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-[var(--primary)] underline"
                    >
                      Fonte oficial
                    </a>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card p-4 text-xs text-[var(--muted)]">
        Base principal: Portaria GM/MS nº 5.663/2024. O prazo de 15 dias é reproduzido
        como referência regulatória e utilizado pelo PREVNAR como benchmark interno de
        atualização. A classificação acima não substitui análise jurídica de aplicabilidade.
      </section>
    </div>
  );
}
