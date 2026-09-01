import { fmtInt } from "@/lib/data";
import { getNacional } from "@/lib/data";
import { readFile } from "fs/promises";
import path from "path";

type MesRow = {
  ano_mes: string;
  doses_mes: number;
  pessoas_mes: number;
  doses_acumuladas: number;
  pessoas_acumuladas: number;
};

type TimelinePayload = {
  atualizado_em?: string;
  fonte?: string;
  fonte_arquivos?: string[];
  periodo?: { inicio?: string; fim?: string; meses?: number; arquivos?: string[] };
  linha_tempo?: MesRow[];
  total_doses?: number;
  total_pessoas?: number;
  nota?: string;
};

async function getTimeline(): Promise<TimelinePayload> {
  try {
    const raw = await readFile(
      path.join(process.cwd(), "public", "data", "vpc20_timeline.json"),
      "utf-8",
    );
    return JSON.parse(raw) as TimelinePayload;
  } catch {
    const n = (await getNacional()) as { linha_tempo_vpc20?: MesRow[]; periodo_vpc20?: object };
    return {
      linha_tempo: n.linha_tempo_vpc20 || [],
      periodo: n.periodo_vpc20 as TimelinePayload["periodo"],
    };
  }
}

function fmtMes(anoMes: string): string {
  const [y, m] = anoMes.split("-");
  const names = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  return `${names[Number(m)] || m}/${y}`;
}

export default async function TimelinePage() {
  const data = await getTimeline();
  const rows = data.linha_tempo || [];
  const maxDoses = Math.max(...rows.map((r) => r.doses_mes), 1);
  const last = rows[rows.length - 1];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Linha do tempo · VPC20</h1>
        <p className="mt-1 max-w-3xl text-sm text-[var(--muted)]">
          Doses aplicadas por mês (PNI CKAN) e acumulado da campanha. Filtros: código{" "}
          <strong>107</strong> (VPC20), idade ≥ 5 anos, data ≥ início da campanha (
          {data.periodo?.inicio || "2026-05-01"}). Fonte: {data.fonte || "—"}.
        </p>
      </div>

      {rows.length === 0 ? (
        <div className="card p-4 text-sm text-[var(--warn)]">
          Sem série mensal no mart. Rode{" "}
          <code className="text-[var(--accent)]">etl/run_ckan_pipeline.py</code> para baixar
          mai/jun/jul e regenerar.
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="kpi-card">
              <div className="text-xs font-semibold uppercase text-[var(--muted)]">Meses</div>
              <div className="kpi-value mt-2 text-2xl">{rows.length}</div>
            </div>
            <div className="kpi-card">
              <div className="text-xs font-semibold uppercase text-[var(--muted)]">
                Doses acumuladas
              </div>
              <div className="kpi-value mt-2 text-2xl text-[var(--accent)]">
                {fmtInt(last?.doses_acumuladas)}
              </div>
            </div>
            <div className="kpi-card">
              <div className="text-xs font-semibold uppercase text-[var(--muted)]">
                Pessoas acumuladas
              </div>
              <div className="kpi-value mt-2 text-2xl">{fmtInt(last?.pessoas_acumuladas)}</div>
            </div>
            <div className="kpi-card">
              <div className="text-xs font-semibold uppercase text-[var(--muted)]">
                Último mês
              </div>
              <div className="kpi-value mt-2 text-2xl">{last ? fmtMes(last.ano_mes) : "—"}</div>
            </div>
          </div>

          <div className="card p-4">
            <h2 className="text-sm font-semibold">Doses por mês</h2>
            <div className="mt-4 space-y-3">
              {rows.map((r) => (
                <div key={r.ano_mes} className="grid grid-cols-[72px_1fr_auto] items-center gap-3">
                  <span className="font-mono text-xs text-[var(--muted)]">{fmtMes(r.ano_mes)}</span>
                  <div className="h-6 overflow-hidden rounded bg-[var(--border)]/30">
                    <div
                      className="h-full rounded bg-[var(--accent)]"
                      style={{ width: `${Math.max(4, (100 * r.doses_mes) / maxDoses)}%` }}
                    />
                  </div>
                  <span className="kpi-value text-sm tabular-nums">
                    {fmtInt(r.doses_mes)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="card table-wrap p-2">
            <table className="data text-sm">
              <thead>
                <tr>
                  <th>Mês</th>
                  <th>Doses no mês</th>
                  <th>Pessoas no mês</th>
                  <th>Doses acum.</th>
                  <th>Pessoas acum.</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.ano_mes}>
                    <td className="font-mono">{r.ano_mes}</td>
                    <td className="kpi-value text-[var(--accent)]">{fmtInt(r.doses_mes)}</td>
                    <td className="kpi-value">{fmtInt(r.pessoas_mes)}</td>
                    <td className="kpi-value">{fmtInt(r.doses_acumuladas)}</td>
                    <td className="kpi-value">{fmtInt(r.pessoas_acumuladas)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {data.fonte_arquivos?.length ? (
        <div className="text-xs text-[var(--muted)]">
          Arquivos: {data.fonte_arquivos.join(", ")} · Atualizado: {data.atualizado_em || "—"}
        </div>
      ) : null}

      <div className="card p-4 text-xs text-[var(--muted)]">
        <strong className="text-[var(--primary-deep)]">Como ampliar:</strong> baixe ZIPs mensais
        do OpenDataSUS (PNI 2026), filtre VPC20 com{" "}
        <code>extract_ckan_pni.py</code>, depois{" "}
        <code>numerador.py --source csv</code> + <code>build_mart.py</code>. O pipeline{" "}
        <code>run_ckan_pipeline.py</code> faz tudo (mai→jul). Cada push no GitHub atualiza o
        painel publicado.
      </div>
    </div>
  );
}
