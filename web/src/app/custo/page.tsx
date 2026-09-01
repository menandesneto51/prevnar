import { Kpi } from "@/components/Kpi";
import { fmtBRL, fmtInt, getNacional } from "@/lib/data";

type Row = {
  uf: string;
  gap: number;
  custo_gap_brl: number;
  siops_per_capita: number | null;
  pressao_fiscal_indice: number | null;
};

export default async function CustoPage() {
  const data = (await getNacional()) as {
    kpis?: {
      custo_gap_brl?: number;
      preco_bps_vpc20?: number;
      preco_bps_nominal?: number;
      ipca_fator_acumulado?: number;
      ipca_referencia_bps?: string;
      gap_absoluto?: number;
      ipca_ultimo?: { data?: string; valor?: string };
    };
    custo_uf?: Row[];
  };
  const k = data.kpis || {};
  const rows = data.custo_uf || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Custo do gap</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          gap × preço BPS atualizado pelo IPCA acumulado desde {k.ipca_referencia_bps || "ref. BPS"}.
          Pressão fiscal = custo / (SIOPS per capita × pop).
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Kpi label="Gap pessoas" value={fmtInt(k.gap_absoluto)} tone="warn" />
        <Kpi label="Preço BPS nominal" value={fmtBRL(k.preco_bps_nominal ?? k.preco_bps_vpc20)} />
        <Kpi
          label="Preço deflacionado IPCA"
          value={fmtBRL(k.preco_bps_vpc20)}
          hint={`fator ${k.ipca_fator_acumulado ?? "—"}`}
        />
        <Kpi label="Custo do gap" value={fmtBRL(k.custo_gap_brl)} tone="danger" />
        <Kpi
          label="IPCA último"
          value={k.ipca_ultimo?.valor ? `${k.ipca_ultimo.valor}%` : "—"}
          hint={k.ipca_ultimo?.data}
        />
      </div>

      <div className="card table-wrap p-2">
        <table className="data">
          <thead>
            <tr>
              <th>UF</th>
              <th>Gap</th>
              <th>Custo gap</th>
              <th>SIOPS R$/hab</th>
              <th>Pressão fiscal</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 27).map((r) => (
              <tr key={r.uf}>
                <td className="font-bold">{r.uf}</td>
                <td className="kpi-value">{fmtInt(r.gap)}</td>
                <td className="kpi-value text-[var(--warn)]">{fmtBRL(r.custo_gap_brl)}</td>
                <td className="kpi-value">{r.siops_per_capita ?? "—"}</td>
                <td className="kpi-value">
                  {r.pressao_fiscal_indice != null
                    ? r.pressao_fiscal_indice.toExponential(2)
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
