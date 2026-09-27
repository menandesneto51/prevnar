import { Kpi, fmtInt } from "@/components/Kpi";
import { getCovidTransitionDashboard } from "@/lib/data";

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

export async function CovidTransitionPanel() {
  const data = await getCovidTransitionDashboard();

  if (!data) {
    return (
      <div className="card border border-[var(--warn)] p-4 text-xs text-[var(--muted)]">
        Nenhum extrato institucional de estoque foi carregado. Use o template autorizado e
        execute <code>python etl/sies_transition_adapter.py arquivo.csv</code>. O endpoint
        público do SIES informa distribuição e não substitui o saldo de estoque por lote.
      </div>
    );
  }

  const losses =
    data.totals.physical_losses_30d + data.totals.technical_losses_30d;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">Estoque institucional · SIES/DW</h3>
        <FreshnessBadge status={data.provenance?.freshness?.status} />
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Kpi
          label="Saldo disponível"
          value={fmtInt(data.totals.stock_available_doses)}
          hint="Agregado por lote no extrato institucional"
        />
        <Kpi
          label="Aplicadas · 30 dias"
          value={fmtInt(data.totals.doses_administered_30d)}
        />
        <Kpi
          label="Perdas · 30 dias"
          value={fmtInt(losses)}
          tone={losses > 0 ? "warn" : "default"}
        />
        <Kpi
          label="Alertas críticos"
          value={fmtInt(data.totals.critical_alerts)}
          tone={data.totals.critical_alerts > 0 ? "danger" : "accent"}
          hint={`${data.totals.attention_alerts} em atenção`}
        />
      </div>

      <div className="grid gap-3 xl:grid-cols-2">
        <div className="card table-wrap p-2">
          <h3 className="px-2 py-2 text-sm font-semibold">Territórios</h3>
          <table className="data">
            <thead>
              <tr>
                <th>Território</th>
                <th>Saldo</th>
                <th>Aplicadas 30d</th>
                <th>Críticos</th>
              </tr>
            </thead>
            <tbody>
              {[...data.by_territory]
                .sort((a, b) => b.stock_available_doses - a.stock_available_doses)
                .slice(0, 12)
                .map((row) => (
                  <tr key={row.territory_code}>
                    <td className="font-mono text-xs">{row.territory_code}</td>
                    <td className="kpi-value">{fmtInt(row.stock_available_doses)}</td>
                    <td className="kpi-value">{fmtInt(row.doses_administered_30d)}</td>
                    <td className="kpi-value">{fmtInt(row.critical_alerts)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="card table-wrap p-2">
          <h3 className="px-2 py-2 text-sm font-semibold">Alertas prioritários</h3>
          <table className="data">
            <thead>
              <tr>
                <th>Severidade</th>
                <th>Território</th>
                <th>Lote</th>
                <th>Alerta</th>
              </tr>
            </thead>
            <tbody>
              {data.alerts.slice(0, 12).map((alert, index) => (
                <tr
                  key={`${alert.territory_code}-${alert.lot}-${alert.alert_id}-${index}`}
                >
                  <td>
                    <span
                      className={`badge ${
                        alert.severity === "critical" ? "badge-danger" : "badge-warn"
                      }`}
                    >
                      {alert.severity}
                    </span>
                  </td>
                  <td className="font-mono text-xs">{alert.territory_code}</td>
                  <td className="font-mono text-xs">{alert.lot}</td>
                  <td className="text-xs">{alert.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card p-4 text-xs text-[var(--muted)]">
        {data.interpretation} source_id:{" "}
        <span className="font-mono">
          {data.provenance?.source_id || data.source_id}
        </span>{" "}
        · competência: {data.reference_period || "—"}.
      </div>
    </div>
  );
}
