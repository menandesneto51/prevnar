import Link from "next/link";
import { notFound } from "next/navigation";
import { Kpi, SituacaoBadge, fmtInt, fmtPct } from "@/components/Kpi";
import { getDashboard, getGapLinhas } from "@/lib/data";

export async function generateStaticParams() {
  const data = await getDashboard();
  return data.por_condicao.map((c) => ({ id: String(c.condicao_id) }));
}

export default async function CondicaoDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const cid = Number(id);
  if (!Number.isFinite(cid)) notFound();

  const [data, gaps] = await Promise.all([getDashboard(), getGapLinhas()]);
  const resumo = data.por_condicao.find((c) => c.condicao_id === cid);
  if (!resumo) notFound();

  const linhas = gaps
    .filter((g) => g.condicao_id === cid)
    .sort((a, b) => (b.gap ?? 0) - (a.gap ?? 0));

  return (
    <div className="space-y-6">
      <div>
        <Link href="/condicoes" className="text-xs text-[var(--accent)] hover:underline">
          ← Condições
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">{resumo.condicao_nt52}</h1>
        <div className="mt-2 flex flex-wrap gap-2">
          <SituacaoBadge n={resumo.situacao_denominador} />
          {resumo.raro ? <span className="badge badge-warn">condição rara</span> : null}
          {resumo.carga_pendente ? (
            <span className="badge badge-warn">carga Situação 1 pendente</span>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label="Elegíveis" value={resumo.elegiveis_display} />
        <Kpi label="Vacinados" value={fmtInt(resumo.pessoas_vacinadas)} tone="accent" />
        <Kpi
          label="Gap"
          value={resumo.gap === null ? "—" : fmtInt(resumo.gap)}
          tone="warn"
        />
        <Kpi
          label="Cobertura"
          value={resumo.exibe_cobertura ? fmtPct(resumo.cobertura_pct) : "não exibida"}
        />
      </div>

      <div className="card table-wrap p-2">
        <table className="data">
          <thead>
            <tr>
              <th>UF</th>
              <th>Elegíveis</th>
              <th>Vacinados</th>
              <th>Gap</th>
              <th>Cobertura</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((r) => (
              <tr key={r.uf}>
                <td>
                  <Link href={`/ufs/${r.uf}`} className="font-medium hover:text-[var(--accent)]">
                    {r.uf}
                  </Link>
                </td>
                <td className="kpi-value">{r.elegiveis_display}</td>
                <td className="kpi-value">{fmtInt(r.pessoas_vacinadas)}</td>
                <td className="kpi-value text-[var(--warn)]">
                  {r.gap === null ? "—" : fmtInt(r.gap)}
                </td>
                <td>
                  {r.exibe_cobertura ? fmtPct(r.cobertura_pct) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
