import Link from "next/link";
import { Suspense } from "react";
import { BrazilUfGrid } from "@/components/BrazilUfGrid";
import { EvidenceBadge, Kpi, SituacaoBadge, fmtInt, fmtPct } from "@/components/Kpi";
import { NationalGapMap } from "@/components/NationalGapMap";
import { getDashboard } from "@/lib/data";

export default async function HomePage() {
  const data = await getDashboard();
  const n = data.nacional;
  const topGap = data.por_condicao.slice(0, 8);
  const ufNomes = Object.fromEntries(data.ufs.map((u) => [u.uf, u.nome]));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Visão nacional</h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--muted)]">
            Oportunidades estimadas por condição · pessoas vacinadas · qualidade da evidência.
            A soma de elegíveis pode conter a mesma pessoa em mais de uma condição e não representa
            pessoas únicas elegíveis.
          </p>
        </div>
        <div className="text-right text-xs text-[var(--muted)]">
          Atualizado: {new Date(data.atualizado_em).toLocaleString("pt-BR")}
          {n.fixture ? (
            <div className="mt-1">
              <span className="badge badge-warn">Numerador demonstrativo</span>
            </div>
          ) : n.fonte_tipo === "api" ? (
            <div className="mt-1">
              <span className="badge badge-sit1">API PNI 2026</span>
              {n.sem_cid_na_fonte ? (
                <span className="badge badge-warn ml-1">sem CID</span>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi
          label="Oportunidades estimadas"
          value={fmtInt(n.oportunidades_estimadas ?? n.elegiveis)}
          hint="Soma por condição; pode haver sobreposição de pessoas"
        />
        <Kpi
          label="Pessoas vacinadas"
          value={fmtInt(n.pessoas_vacinadas)}
          hint="COUNT DISTINCT (anti dupla-contagem)"
          tone="accent"
        />
        <Kpi
          label="Gap de pessoas únicas"
          value={n.gap_pessoas_disponivel ? fmtInt(n.gap_pessoas) : "não disponível"}
          hint="Exige denominador deduplicado compatível"
          tone="warn"
        />
        <Kpi
          label="CID preenchido"
          value={fmtPct((n.taxa_cid_preenchido ?? 0) * 100)}
          hint="Qualidade do numerador RNDS"
          tone={(n.taxa_cid_preenchido ?? 0) < 0.8 ? "danger" : "default"}
        />
      </div>

      <div className="card p-4 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium">Evidência do numerador por condição:</span>
          <EvidenceBadge
            level={n.evidence_level_clinical_breakdown}
            decisionGrade={n.decision_grade_clinical_breakdown}
          />
        </div>
        <p className="mt-2 text-xs text-[var(--muted)]">
          {n.nota_oportunidades || "A classificação por condição deve ser interpretada conforme a fonte e o nível de evidência."}
        </p>
      </div>

      <div className="flex flex-wrap gap-2 text-sm">
        <Link href="/indicadores" className="rounded-lg border border-[var(--border)] px-3 py-1.5 hover:border-[var(--accent)]">
          Catálogo de indicadores
        </Link>
        <Link href="/regioes" className="rounded-lg border border-[var(--border)] px-3 py-1.5 hover:border-[var(--accent)]">
          Gap por região de saúde
        </Link>
        <Link href="/serie" className="rounded-lg border border-[var(--border)] px-3 py-1.5 hover:border-[var(--accent)]">
          Série / transição pneumocócica
        </Link>
        <Link href="/monitoramento" className="rounded-lg border border-[var(--border)] px-3 py-1.5 hover:border-[var(--accent)]">
          Monitoramento SINAN/SIH
        </Link>
        <Link href="/estoque" className="rounded-lg border border-[var(--border)] px-3 py-1.5 hover:border-[var(--accent)]">
          Estoque SIES
        </Link>
        <Link href="/custo" className="rounded-lg border border-[var(--border)] px-3 py-1.5 hover:border-[var(--accent)]">
          Custo do gap
        </Link>
      </div>

      {data.qualidade.sanity_alerta ? (
        <div className="card border-[var(--danger)] p-4 text-sm text-[var(--danger)]">
          Sanity check: divergência de doses &gt; 5% vs referência PNI/SVSA. Revisar filtros do
          numerador.
        </div>
      ) : null}

      <Suspense
        fallback={
          <div className="card map-canvas map-placeholder" role="status">
            Carregando mapa…
          </div>
        }
      >
        <NationalGapMap
          porUf={data.por_uf}
          porMunicipio={data.por_municipio || []}
          ufNomes={ufNomes}
        />
      </Suspense>

      <div className="grid gap-4 lg:grid-cols-2">
        <BrazilUfGrid data={data.por_uf} />

        <div className="card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Maiores oportunidades estimadas por condição</h2>
            <Link href="/condicoes" className="text-xs text-[var(--accent)] hover:underline">
              Ver todas
            </Link>
          </div>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Condição</th>
                  <th>Sit.</th>
                  <th>Oportunidade*</th>
                  <th>Vacinados</th>
                </tr>
              </thead>
              <tbody>
                {topGap.map((c) => (
                  <tr key={c.condicao_id}>
                    <td>
                      <Link
                        href={`/condicoes/${c.condicao_id}`}
                        className="font-medium hover:text-[var(--accent)]"
                      >
                        {c.condicao_nt52}
                      </Link>
                      {c.carga_pendente ? (
                        <div className="text-[10px] text-[var(--warn)]">carga pendente</div>
                      ) : null}
                    </td>
                    <td>
                      <SituacaoBadge n={c.situacao_denominador} />
                    </td>
                    <td className="kpi-value font-medium text-[var(--warn)]">
                      <div>{c.gap === null ? "—" : fmtInt(c.gap)}</div>
                      <div className="mt-1">
                        <EvidenceBadge
                          level={c.gap_evidence_level}
                          decisionGrade={c.gap_decision_grade}
                        />
                      </div>
                    </td>
                    <td className="kpi-value">{fmtInt(c.pessoas_vacinadas)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
