import { Kpi, fmtInt } from "@/components/Kpi";
import { getImmunobiologicCatalog } from "@/lib/data";

function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "ok" | "warn" | "danger" | "neutral";
}) {
  const cls =
    tone === "ok"
      ? "badge-sit1"
      : tone === "warn"
        ? "badge-warn"
        : tone === "danger"
          ? "badge-danger"
          : "";
  return <span className={`badge ${cls}`}>{children}</span>;
}

function typeLabel(type: string) {
  if (type === "vaccine") return "Vacina";
  if (type === "monoclonal_antibody") return "Anticorpo monoclonal";
  if (type === "immunoglobulin") return "Imunoglobulina";
  return type || "Outro";
}

export default async function ImmunobiologicosPage() {
  const catalog = await getImmunobiologicCatalog();
  const items = catalog.items;

  const activeRuleItems = items.filter((item) => item.active_rules.length > 0).length;
  const monitored = items.filter((item) => item.monitored).length;
  const mapped = items.filter((item) => item.data_mapping === "mapped").length;
  const pending = items.filter((item) => item.data_mapping === "pending").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Catálogo de imunobiológicos</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Estado normativo, mapeamento de dados e monitoramento derivados dos registros canônicos
          do PREVNAR.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Kpi label="Imunobiológicos" value={fmtInt(items.length)} />
        <Kpi label="Com regra ativa" value={fmtInt(activeRuleItems)} />
        <Kpi label="Monitorados" value={fmtInt(monitored)} />
        <Kpi
          label="Mapeamento pendente"
          value={fmtInt(pending)}
          tone={pending > 0 ? "warn" : undefined}
        />
      </div>

      <div className="card p-4 text-xs text-[var(--muted)]">
        <strong className="text-[var(--fg)]">Leitura correta:</strong> regra ativa, código PNI
        conhecido e monitoramento são dimensões diferentes. Uma entidade pode possuir regra
        clínica ativa sem ter ainda coleta automatizada, ou possuir código conhecido sem estar
        pronta para decisão clínica.
      </div>

      <div className="card table-wrap p-2">
        <table className="data">
          <thead>
            <tr>
              <th>Imunobiológico</th>
              <th>Tipo</th>
              <th>Regra</th>
              <th>Dados</th>
              <th>Monitoramento</th>
              <th>Códigos PNI</th>
              <th>Regras ativas</th>
              <th>Drafts</th>
              <th>Onboarding</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.immunobiologic_id}>
                <td>
                  <div className="font-medium">{item.display || item.name}</div>
                  <div className="font-mono text-[10px] text-[var(--muted)]">
                    {item.immunobiologic_id}
                  </div>
                </td>
                <td className="text-xs">{typeLabel(item.type)}</td>
                <td>
                  {item.rule_readiness === "active" ? (
                    <Badge tone="ok">ativa</Badge>
                  ) : item.rule_readiness === "draft" ? (
                    <Badge tone="warn">draft</Badge>
                  ) : (
                    <Badge>sem regra</Badge>
                  )}
                </td>
                <td>
                  {item.data_mapping === "mapped" ? (
                    <Badge tone="ok">mapeado</Badge>
                  ) : item.data_mapping === "partial" ? (
                    <Badge tone="warn">parcial</Badge>
                  ) : (
                    <Badge tone="danger">pendente</Badge>
                  )}
                </td>
                <td>
                  <Badge tone={item.monitored ? "ok" : "neutral"}>
                    {item.monitored ? "sim" : "não"}
                  </Badge>
                </td>
                <td className="font-mono text-xs">
                  {item.pni_codes?.length ? item.pni_codes.join(", ") : "—"}
                </td>
                <td className="kpi-value">{fmtInt(item.active_rules.length)}</td>
                <td className="kpi-value">{fmtInt(item.draft_rules.length)}</td>
                <td className="max-w-xs text-xs">
                  {item.onboarding_status || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {items
          .filter((item) => item.active_rules.length > 0)
          .map((item) => (
            <section key={item.immunobiologic_id} className="card p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold">{item.display || item.name}</h2>
                <Badge tone="ok">{item.active_rules.length} regra(s) ativa(s)</Badge>
              </div>
              <div className="mt-3 space-y-2">
                {item.active_rules.map((rule) => (
                  <div key={rule.rule_id} className="rounded-lg border border-[var(--border)] p-3">
                    <div className="font-mono text-xs">{rule.rule_id}</div>
                    <div className="mt-1 flex flex-wrap gap-2 text-[11px]">
                      <Badge>{rule.rule_context || rule.rule_type}</Badge>
                      <Badge>
                        {rule.geographic_scope?.type || "escopo desconhecido"}
                      </Badge>
                      {rule.effective_from ? <Badge>desde {rule.effective_from}</Badge> : null}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          ))}
      </div>

      <div className="card p-4 text-xs text-[var(--muted)]">
        Catálogo gerado no build a partir de <code>immunobiologic_registry.json</code> e{" "}
        <code>normative_rules.json</code>. Não há configuração duplicada na interface.
      </div>
    </div>
  );
}
