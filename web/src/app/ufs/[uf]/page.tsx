import Link from "next/link";
import { notFound } from "next/navigation";
import { Kpi, SituacaoBadge, fmtInt, fmtPct } from "@/components/Kpi";
import { UfMunicipalityMap } from "@/components/UfMunicipalityMap";
import { getDashboard, getGapLinhas } from "@/lib/data";

export default async function UfDetailPage({
  params,
}: {
  params: Promise<{ uf: string }>;
}) {
  const { uf: raw } = await params;
  const uf = raw.toUpperCase();
  const [data, gaps] = await Promise.all([getDashboard(), getGapLinhas()]);
  const meta = data.ufs.find((u) => u.uf === uf);
  const resumo = data.por_uf.find((u) => u.uf === uf);
  if (!meta || !resumo) notFound();

  const linhas = gaps
    .filter((g) => g.uf === uf)
    .sort((a, b) => (b.gap ?? 0) - (a.gap ?? 0));

  return (
    <div className="space-y-6">
      <div>
        <Link href="/ufs" className="text-xs text-[var(--accent)] hover:underline">
          ← UFs
        </Link>
        <h1 className="mt-2 text-2xl font-semibold">
          {meta.nome} <span className="text-[var(--muted)]">({uf})</span>
        </h1>
        <p className="text-sm text-[var(--muted)]">{meta.regiao}</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Kpi label="Elegíveis (soma condições)" value={fmtInt(resumo.elegiveis)} />
        <Kpi
          label="Vacinados"
          value={fmtInt(resumo.pessoas_vacinadas_consolidado ?? resumo.pessoas_vacinadas)}
          tone="accent"
        />
        <Kpi label="Gap" value={fmtInt(resumo.gap)} tone="warn" />
      </div>

      <UfMunicipalityMap
        uf={uf}
        nome={meta.nome}
        parentGap={resumo.gap}
        municipios={data.por_municipio || []}
      />

      <div className="card table-wrap p-2">
        <table className="data">
          <thead>
            <tr>
              <th>Condição</th>
              <th>Sit.</th>
              <th>Elegíveis</th>
              <th>Vacinados</th>
              <th>Gap</th>
              <th>Cobertura</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((r) => (
              <tr key={r.condicao_id}>
                <td>
                  <Link
                    href={`/condicoes/${r.condicao_id}`}
                    className="font-medium hover:text-[var(--accent)]"
                  >
                    {r.condicao_nt52}
                  </Link>
                </td>
                <td>
                  <SituacaoBadge n={r.situacao_denominador} />
                </td>
                <td className="kpi-value">{r.elegiveis_display}</td>
                <td className="kpi-value">{fmtInt(r.pessoas_vacinadas)}</td>
                <td className="kpi-value text-[var(--warn)]">
                  {r.gap === null ? "—" : fmtInt(r.gap)}
                </td>
                <td>{r.exibe_cobertura ? fmtPct(r.cobertura_pct) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
