import Link from "next/link";
import { notFound } from "next/navigation";
import { EvidenceBadge, Kpi, SituacaoBadge, fmtInt, fmtPct } from "@/components/Kpi";
import { UfMunicipalityMap } from "@/components/UfMunicipalityMap";
import { getDashboard, getGapLinhas } from "@/lib/data";

export async function generateStaticParams() {
  const data = await getDashboard();
  return data.ufs.map((u) => ({ uf: u.uf.toLowerCase() }));
}

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
        <Kpi
          label="Oportunidades estimadas"
          value={fmtInt(resumo.oportunidades_estimadas ?? resumo.elegiveis)}
          hint="Soma por condição; pode haver sobreposição"
        />
        <Kpi
          label="Vacinados"
          value={fmtInt(resumo.pessoas_vacinadas_consolidado ?? resumo.pessoas_vacinadas)}
          tone="accent"
        />
        <Kpi
          label="Gap de pessoas únicas"
          value={resumo.gap_pessoas == null ? "não disponível" : fmtInt(resumo.gap_pessoas)}
          hint="Exige denominador deduplicado"
          tone="warn"
        />
      </div>

      <UfMunicipalityMap
        uf={uf}
        nome={meta.nome}
        parentGap={resumo.oportunidades_estimadas ?? resumo.elegiveis}
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
              <th>Oportunidade*</th>
              <th>Evidência</th>
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
                <td>
                  <EvidenceBadge
                    level={
                      r.gap_evidence_level ??
                      data.nacional.evidence_level_clinical_breakdown ??
                      (data.nacional.sem_cid_na_fonte ? "E2" : "E1")
                    }
                    decisionGrade={r.gap_decision_grade ?? false}
                  />
                </td>
                <td>{r.exibe_cobertura ? fmtPct(r.cobertura_pct) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-[var(--muted)]">
        * Valor por condição. Se o numerador clínico for proxy ou o denominador for estimado,
        interpretar conforme o nível de evidência; não equivale ao gap de pessoas únicas da UF.
      </p>
    </div>
  );
}
