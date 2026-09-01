import Link from "next/link";
import { SituacaoBadge, fmtInt, fmtPct } from "@/components/Kpi";
import { getDashboard } from "@/lib/data";

export default async function CondicoesPage() {
  const data = await getDashboard();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Por condição</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          20 condições NT 52/2026 (prematuros fora do v1). Cobertura % apenas na Situação 1 com
          cadastro carregado.
          {data.nacional.sem_cid_na_fonte ? (
            <>
              {" "}
              API sem CID: vacinados por condição usam proxy{" "}
              <code className="text-[var(--accent)]">grupo_atendimento</code> (parcial). Para
              cobertura Sit.1 definitiva, rode{" "}
              <code className="text-[var(--accent)]">etl/extract_ckan_pni.py</code> no ZIP CKAN
              (~3&nbsp;GB/mês).
            </>
          ) : null}
        </p>
      </div>

      <div className="card table-wrap p-2">
        <table className="data">
          <thead>
            <tr>
              <th>#</th>
              <th>Condição</th>
              <th>Denominador</th>
              <th>Elegíveis</th>
              <th>Vacinados</th>
              <th>Gap</th>
              <th>Cobertura</th>
            </tr>
          </thead>
          <tbody>
            {data.por_condicao.map((c) => (
              <tr key={c.condicao_id}>
                <td className="text-[var(--muted)]">{c.condicao_id}</td>
                <td>
                  <Link
                    href={`/condicoes/${c.condicao_id}`}
                    className="font-medium hover:text-[var(--accent)]"
                  >
                    {c.condicao_nt52}
                  </Link>
                </td>
                <td>
                  <SituacaoBadge n={c.situacao_denominador} />
                </td>
                <td className="kpi-value">{c.elegiveis_display}</td>
                <td className="kpi-value text-[var(--accent)]">{fmtInt(c.pessoas_vacinadas)}</td>
                <td className="kpi-value text-[var(--warn)]">
                  {c.gap === null ? "—" : fmtInt(c.gap)}
                </td>
                <td>
                  {c.exibe_cobertura ? (
                    <span className="kpi-value">{fmtPct(c.cobertura_pct)}</span>
                  ) : (
                    <span className="badge badge-muted">não exibida</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
