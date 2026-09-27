import { Kpi, fmtInt } from "@/components/Kpi";
import {
  getNormativeBacklog,
  getNormativeMatrix,
  type NormativeMatrixItem,
  type NormativeRuleRow,
} from "@/lib/data";

function StatusBadge({ active, label }: { active: boolean; label: string }) {
  return <span className={`badge ${active ? "badge-sit1" : "badge-warn"}`}>{label}</span>;
}

function ScopeLabel({ rule }: { rule: NormativeRuleRow }) {
  const type = rule.geographic_scope?.type || "não definido";
  const codes = rule.geographic_scope?.codes || [];
  return codes.length ? `${type}: ${codes.join(", ")}` : type;
}

function RuleTable({ item }: { item: NormativeMatrixItem }) {
  return (
    <div className="card table-wrap p-2">
      <h3 className="px-2 py-2 text-sm font-semibold">Regras estruturadas</h3>
      <table className="data">
        <thead>
          <tr>
            <th>Regra</th>
            <th>Status</th>
            <th>Contexto</th>
            <th>Vigência</th>
            <th>Escopo</th>
          </tr>
        </thead>
        <tbody>
          {item.rules.length ? (
            item.rules.map((rule) => (
              <tr key={rule.rule_id || JSON.stringify(rule)}>
                <td>
                  <div className="font-mono text-xs">{rule.rule_id || "—"}</div>
                  {rule.note ? (
                    <div className="mt-1 max-w-xl text-xs text-[var(--muted)]">{rule.note}</div>
                  ) : null}
                </td>
                <td>
                  <StatusBadge
                    active={rule.active_on_as_of}
                    label={rule.active_on_as_of ? "ativa" : rule.status || "—"}
                  />
                </td>
                <td>{rule.rule_context || rule.rule_type || "—"}</td>
                <td>
                  <div>{rule.effective_from || "—"}</div>
                  {rule.effective_until ? (
                    <div className="text-xs text-[var(--muted)]">até {rule.effective_until}</div>
                  ) : null}
                </td>
                <td><ScopeLabel rule={rule} /></td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={5} className="text-[var(--muted)]">
                Nenhuma regra estruturada.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function ActsTable({ item }: { item: NormativeMatrixItem }) {
  return (
    <div className="card table-wrap p-2">
      <h3 className="px-2 py-2 text-sm font-semibold">Base normativa</h3>
      <table className="data">
        <thead>
          <tr>
            <th>Ato</th>
            <th>Tipo</th>
            <th>Publicação</th>
            <th>Fonte</th>
          </tr>
        </thead>
        <tbody>
          {item.normative_acts.length ? (
            item.normative_acts.map((act) => (
              <tr key={act.id}>
                <td>
                  <div className="font-medium">{act.number || act.id}</div>
                  <div className="mt-1 font-mono text-xs text-[var(--muted)]">{act.id}</div>
                </td>
                <td>{act.type || "—"}</td>
                <td>{act.published_at || "—"}</td>
                <td>
                  {act.official_url ? (
                    <a
                      href={act.official_url}
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium text-[var(--primary)] underline"
                    >
                      Fonte oficial
                    </a>
                  ) : (
                    <span className="badge badge-danger">referência sem URL</span>
                  )}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={4} className="text-[var(--muted)]">
                Nenhum ato normativo registrado.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default async function NormasPage() {
  const [data, backlog] = await Promise.all([
    getNormativeMatrix(),
    getNormativeBacklog(),
  ]);

  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Normas e rastreabilidade</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Regras, vigência, escopo territorial, atos oficiais e maturidade de dados.
          </p>
        </div>
        <div className="card p-6">
          <h2 className="text-lg font-semibold">Matriz normativa ainda não gerada</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Execute o gerador para consolidar os registros normativos canônicos.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
            python etl/build_normative_matrix.py
          </pre>
        </div>
      </div>
    );
  }

  const unresolved = data.summary.unresolved_legal_references || [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Normas e rastreabilidade</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Matriz auditável em {data.as_of}. Regra ativa, disponibilidade de dado e capacidade de
          cálculo são dimensões distintas.
        </p>
      </div>

      <section className="grid gap-3 md:grid-cols-4">
        <Kpi label="Imunobiológicos" value={fmtInt(data.summary.immunobiologics)} />
        <Kpi label="Regras ativas" value={fmtInt(data.summary.active_rules)} tone="accent" />
        <Kpi label="Regras em draft" value={fmtInt(data.summary.draft_rules)} />
        <Kpi
          label="Referências legais não resolvidas"
          value={fmtInt(unresolved.length)}
          tone={unresolved.length ? "danger" : "accent"}
        />
      </section>

      {unresolved.length ? (
        <section className="card border border-[var(--danger)] p-4">
          <h2 className="font-semibold text-[var(--danger)]">Referências legais não resolvidas</h2>
          <div className="mt-2 font-mono text-xs">{unresolved.join(", ")}</div>
        </section>
      ) : (
        <section className="card p-4 text-sm">
          <span className="badge badge-sit1">Integridade legal</span>
          <span className="ml-2 text-[var(--muted)]">
            Todas as referências normativas da matriz resolvem para o registro legal atual.
          </span>
        </section>
      )}

      <section className="card p-4 text-xs text-[var(--muted)]">{data.interpretation}</section>

      {backlog ? (
        <section className="space-y-3">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Pendências de governança</h2>
              <p className="mt-1 text-xs text-[var(--muted)]">{backlog.interpretation}</p>
            </div>
            <div className="flex gap-2">
              {Object.entries(backlog.summary.by_priority).map(([priority, count]) => (
                <span
                  key={priority}
                  className={`badge ${priority === "P1" ? "badge-danger" : "badge-warn"}`}
                >
                  {priority}: {count}
                </span>
              ))}
            </div>
          </div>
          <div className="card table-wrap p-2">
            <table className="data">
              <thead>
                <tr>
                  <th>Prioridade</th>
                  <th>Imunobiológico</th>
                  <th>Categoria</th>
                  <th>Pendência</th>
                  <th>Próximo gate</th>
                </tr>
              </thead>
              <tbody>
                {backlog.items.slice(0, 20).map((row, index) => (
                  <tr key={`${row.immunobiologic_id}-${row.category}-${index}`}>
                    <td>
                      <span className={`badge ${row.priority === "P1" ? "badge-danger" : "badge-warn"}`}>
                        {row.priority}
                      </span>
                    </td>
                    <td>{row.display}</td>
                    <td className="font-mono text-xs">{row.category}</td>
                    <td className="text-xs">{row.message}</td>
                    <td className="text-xs text-[var(--muted)]">{row.next_gate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {data.immunobiologics.map((item) => (
        <section key={item.immunobiologic_id} className="space-y-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">{item.display}</h2>
              <p className="mt-1 text-xs text-[var(--muted)]">
                {item.immunobiologic_id} · {item.type || "tipo não definido"}
                {item.pni_codes.length ? ` · código(s): ${item.pni_codes.join(", ")}` : ""}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge active={item.active_rule_count > 0} label={`${item.active_rule_count} ativa(s)`} />
              {item.draft_rule_count ? (
                <span className="badge badge-warn">{item.draft_rule_count} draft</span>
              ) : null}
              <span className={`badge ${item.monitored ? "badge-sit1" : "badge-warn"}`}>
                {item.monitored ? "monitorado" : "não monitorado"}
              </span>
            </div>
          </div>

          <div className="card p-4 text-xs">
            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <span className="text-[var(--muted)]">Onboarding:</span>{" "}
                <span className="font-mono">{item.onboarding_status || "não definido"}</span>
              </div>
              <div>
                <span className="text-[var(--muted)]">Mapeamento:</span>{" "}
                <span className="font-mono">{item.code_mapping_status || "—"}</span>
              </div>
            </div>
          </div>

          <RuleTable item={item} />
          <ActsTable item={item} />
        </section>
      ))}
    </div>
  );
}
