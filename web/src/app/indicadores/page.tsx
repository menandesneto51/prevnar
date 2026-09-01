import { fmtInt, fmtPct } from "@/components/Kpi";
import { fmtBRL, getNacional } from "@/lib/data";

type StatusRow = {
  id: string;
  nome?: string;
  familia?: string;
  status: string;
  valor?: string | number | null;
  unidade?: string;
};

type Nacional = {
  atualizado_em?: string;
  kpis?: Record<string, unknown>;
  indicadores_status?: StatusRow[];
  cobertura_sit1?: Array<{
    condicao_id: string;
    condicao_nt52: string;
    elegiveis?: number;
    pessoas_vacinadas?: number;
    cobertura_pct?: number | null;
    carga_pendente?: boolean;
  }>;
};

const statusClass: Record<string, string> = {
  ok: "badge-sit1",
  parcial: "badge-warn",
  planejado: "badge-warn",
  sem_dado: "badge-danger",
};

function fmtValor(r: StatusRow): string {
  const v = r.valor;
  if (v === null || v === undefined) return "—";
  if (typeof v === "string") return v;
  const u = (r.unidade || "").toLowerCase();
  if (u.includes("%")) return fmtPct(Number(v));
  if (u.includes("r$") || u.includes("brl") || r.id === "custo_gap") return fmtBRL(Number(v));
  if (Number.isInteger(v)) return fmtInt(v);
  return String(v);
}

export default async function IndicadoresPage() {
  const data = (await getNacional()) as Nacional;
  const rows = data.indicadores_status || [];
  const byFam = rows.reduce<Record<string, StatusRow[]>>((acc, r) => {
    const f = r.familia || "outros";
    (acc[f] ||= []).push(r);
    return acc;
  }, {});
  const cob = data.cobertura_sit1 || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Catálogo de indicadores</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Status operacional do painel nacional. Atualizado:{" "}
          {data.atualizado_em
            ? new Date(data.atualizado_em).toLocaleString("pt-BR")
            : "—"}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-4">
        {(["ok", "parcial", "planejado", "sem_dado"] as const).map((st) => (
          <div key={st} className="card p-4">
            <div className="text-xs uppercase text-[var(--muted)]">{st}</div>
            <div className="mt-1 text-3xl font-semibold kpi-value">
              {rows.filter((r) => r.status === st).length}
            </div>
          </div>
        ))}
      </div>

      {Object.entries(byFam).map(([fam, items]) => (
        <div key={fam} className="card table-wrap p-2">
          <h2 className="px-2 py-2 text-sm font-semibold capitalize">{fam}</h2>
          <table className="data">
            <thead>
              <tr>
                <th>Indicador</th>
                <th>Valor</th>
                <th>Unidade</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="font-medium">{r.nome || r.id}</div>
                    <div className="font-mono text-xs text-[var(--muted)]">{r.id}</div>
                  </td>
                  <td className="kpi-value">{fmtValor(r)}</td>
                  <td className="text-xs text-[var(--muted)]">{r.unidade || "—"}</td>
                  <td>
                    <span className={`badge ${statusClass[r.status] || "badge-warn"}`}>
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      {cob.length > 0 ? (
        <div className="card table-wrap p-2">
          <h2 className="px-2 py-2 text-sm font-semibold">Cobertura % · Situação 1</h2>
          <table className="data">
            <thead>
              <tr>
                <th>Condição</th>
                <th>Elegíveis</th>
                <th>Vacinados</th>
                <th>Cobertura</th>
                <th>Carga</th>
              </tr>
            </thead>
            <tbody>
              {cob.map((c) => (
                <tr key={c.condicao_id}>
                  <td>{c.condicao_nt52}</td>
                  <td className="kpi-value">{fmtInt(c.elegiveis)}</td>
                  <td className="kpi-value text-[var(--accent)]">
                    {fmtInt(c.pessoas_vacinadas)}
                  </td>
                  <td className="kpi-value">
                    {c.cobertura_pct == null ? "—" : fmtPct(c.cobertura_pct)}
                  </td>
                  <td>
                    <span className={`badge ${c.carga_pendente ? "badge-warn" : "badge-sit1"}`}>
                      {c.carga_pendente ? "pendente" : "ok"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
