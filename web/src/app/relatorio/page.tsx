import { fmtInt, fmtBRL } from "@/lib/data";
import { assetUrl } from "@/lib/basePath";
import { PrintButton } from "@/components/PrintButton";
import { getNacional } from "@/lib/data";
import Link from "next/link";

type StatusRow = {
  id: string;
  nome?: string;
  familia?: string;
  status: string;
  valor?: string | number | null;
  unidade?: string;
};

const STATUS_PT: Record<string, string> = {
  ok: "Implementado",
  parcial: "Parcial",
  sem_dado: "Sem dado",
  planejado: "Pendente",
};

const PENDENTE = [
  ["CKAN jun/jul 2026", "Ampliar numerador além de mai/2026", "etl/run_ckan_pipeline.py"],
  ["Cadastros Situação 1", "Substituir seeds por extratos oficiais", "data/manual/situacao1/"],
  ["CNES CRIE definitivo", "Seed não bate API; % fora CRIE = 100%", "cnes_crie.json"],
  ["Mapa municipal", "Vacinados por município ainda vazio", "numerador CKAN"],
  ["SINAN/SIH/SIM FTP", "Automatizar DATASUS (hoje seeds)", "extract_nacional.py"],
  ["SIES VPC20", "API não discrimina VPC20", "extract_sies"],
  ["ESAVI completo", "API vazia; seed manual", "esavi_template.csv"],
] as const;

const INVIAVEL = [
  [
    "CID motivo_indicacao (PNI 2026)",
    "CSV CKAN 2026 não traz CID; REST também não. Cobertura Sit.1 definitiva por condição clínica exige cadastros/proxy.",
  ],
  [
    "Denominador Sit.1 universal",
    "Não há API única com elegíveis por condição NT52; depende de SICLOM, ABTO, REBRAFC, etc.",
  ],
  [
    "Causalidade desfecho",
    "SINAN/SIH/SIM/SRAG são ecológicos — sem inferência individual.",
  ],
  [
    "Numerador 100% CRIE via PNI aberto",
    "Maioria VPC20 em grupo Faixa Etária (000210), fora do recorte CRIE estrito.",
  ],
  [
    "SIES dose VPC20",
    "OpenDataSUS agrega pneumo; VPC20 não confiável na API.",
  ],
] as const;

export default async function RelatorioPage() {
  const data = (await getNacional()) as {
    kpis?: Record<string, unknown>;
    indicadores_status?: StatusRow[];
    atualizado_em?: string;
  };
  const rows = data.indicadores_status || [];
  const ok = rows.filter((r) => r.status === "ok").length;
  const parcial = rows.filter((r) => r.status === "parcial").length;
  const sem = rows.filter((r) => r.status === "sem_dado").length;

  return (
    <div className="space-y-8 print:space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Relatório de implementação</h1>
          <p className="mt-1 max-w-3xl text-sm text-[var(--muted)]">
            Comparativo entre o escopo inicial (
            <code className="text-[var(--accent)]">plano_extracao_nacional.json</code> +{" "}
            <code className="text-[var(--accent)]">indicadores_nacionais.json</code>) e o estado
            atual do painel. PDF:{" "}
            <code className="text-[var(--accent)]">docs/relatorio_implementacao_prevnar.pdf</code>
          </p>
        </div>
        <div className="flex gap-2 print:hidden">
          <PrintButton />
          <a
            href={assetUrl("/relatorio/relatorio_implementacao_prevnar.pdf")}
            className="rounded-md border border-[var(--border)] px-4 py-2 text-sm"
            download
          >
            Baixar PDF
          </a>
          <Link
            href="/"
            className="rounded-md border border-[var(--border)] px-4 py-2 text-sm"
          >
            Voltar ao painel
          </Link>
        </div>
      </div>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">KPIs atuais</h2>
        <dl className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3 text-sm">
          <div>
            <dt className="text-[var(--muted)]">Elegíveis</dt>
            <dd className="kpi-value">{fmtInt(data.kpis?.elegiveis as number)}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Vacinados VPC20</dt>
            <dd className="kpi-value text-[var(--accent)]">
              {fmtInt(data.kpis?.pessoas_vacinadas_vpc20 as number)}
            </dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Gap</dt>
            <dd className="kpi-value text-[var(--warn)]">
              {fmtInt(data.kpis?.gap_absoluto as number)}
            </dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Custo do gap</dt>
            <dd className="kpi-value">{fmtBRL(data.kpis?.custo_gap_brl as number)}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Fonte numerador</dt>
            <dd>{String(data.kpis?.fonte_numerador || "—")}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Atualizado</dt>
            <dd className="text-xs">{data.atualizado_em || "—"}</dd>
          </div>
        </dl>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">
          Indicadores ({ok} ok · {parcial} parcial · {sem} sem dado)
        </h2>
        <div className="table-wrap mt-3">
          <table className="data text-sm">
            <thead>
              <tr>
                <th>Indicador</th>
                <th>Família</th>
                <th>Status</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="font-medium">{r.nome}</div>
                    <div className="font-mono text-xs text-[var(--muted)]">{r.id}</div>
                  </td>
                  <td>{r.familia}</td>
                  <td>
                    <span
                      className={
                        r.status === "ok"
                          ? "text-[var(--accent)]"
                          : r.status === "parcial"
                            ? "text-[var(--warn)]"
                            : "text-[var(--muted)]"
                      }
                    >
                      {STATUS_PT[r.status] || r.status}
                    </span>
                  </td>
                  <td className="kpi-value">
                    {r.valor}
                    {r.unidade ? ` ${r.unidade}` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-[var(--warn)]">Pendente</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {PENDENTE.map(([t, d, ref]) => (
              <li key={t}>
                <strong>{t}</strong> — {d}
                <div className="font-mono text-xs text-[var(--muted)]">{ref}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="card p-4">
          <h2 className="text-sm font-semibold text-[var(--muted)]">
            Limitações / inviável
          </h2>
          <ul className="mt-3 space-y-2 text-sm">
            {INVIAVEL.map(([t, d]) => (
              <li key={t}>
                <strong>{t}</strong> — {d}
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
