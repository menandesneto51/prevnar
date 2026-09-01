import { fmtPct, fmtInt } from "@/components/Kpi";
import { getDashboard, getNacional } from "@/lib/data";

type NacionalQ = {
  kpis?: {
    atraso_rnds_mediana_dias?: number | null;
    pct_fora_crie?: number | null;
    doses_por_crie?: number | null;
    esavi_por_100k_doses?: number | null;
    esavi_total?: number | null;
  };
  qualidade?: {
    atraso_rnds_dias?: { mediana?: number | null; p90?: number | null; n?: number };
    sim_nota?: string;
  };
  qualidade_oferta?: {
    fonte?: string;
    doses_vpc20_ge5?: number;
    doses_em_cnes_crie?: number;
    n_cries_seed?: number;
  };
  oferta_uf?: Array<{
    uf: string;
    doses_vpc20_ge5: number;
    doses_em_cnes_crie: number;
    n_cries_seed: number;
    doses_por_crie: number | null;
    pct_fora_crie: number | null;
  }>;
};

export default async function QualidadePage() {
  const data = await getDashboard();
  const nac = (await getNacional()) as NacionalQ;
  const q = data.qualidade;
  const unmapped = Object.entries(q.cids_nao_mapeados || {}).sort((a, b) => b[1] - a[1]);
  const atr = nac.qualidade?.atraso_rnds_dias || {};
  const oferta = nac.oferta_uf || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Qualidade dos dados</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          CID, atraso RNDS, adesão CRIE e ESAVI. Sem CID, a dose não entra no breakdown por
          condição.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
        <div className="card p-4">
          <div className="text-xs uppercase text-[var(--muted)]">Taxa CID preenchido</div>
          <div className="mt-1 text-2xl font-semibold kpi-value">
            {fmtPct((q.taxa_cid_preenchido ?? 0) * 100)}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-xs uppercase text-[var(--muted)]">Atraso RNDS (mediana)</div>
          <div className="mt-1 text-2xl font-semibold kpi-value">
            {atr.mediana == null ? "—" : `${atr.mediana} d`}
          </div>
          <div className="mt-1 text-xs text-[var(--muted)]">
            p90 {atr.p90 ?? "—"} · n={atr.n ?? 0}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-xs uppercase text-[var(--muted)]">% fora CRIE</div>
          <div className="mt-1 text-2xl font-semibold kpi-value">
            {nac.kpis?.pct_fora_crie == null ? "—" : fmtPct(nac.kpis.pct_fora_crie)}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-xs uppercase text-[var(--muted)]">Doses / CRIE</div>
          <div className="mt-1 text-2xl font-semibold kpi-value">
            {nac.kpis?.doses_por_crie ?? "—"}
          </div>
          <div className="mt-1 text-xs text-[var(--muted)]">
            {fmtInt(nac.qualidade_oferta?.n_cries_seed)} CRIEs seed
          </div>
        </div>
        <div className="card p-4">
          <div className="text-xs uppercase text-[var(--muted)]">ESAVI / 100k doses</div>
          <div className="mt-1 text-2xl font-semibold kpi-value">
            {nac.kpis?.esavi_por_100k_doses ?? "—"}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-xs uppercase text-[var(--muted)]">Sanity vs PNI/SVSA</div>
          <div className="mt-1 text-2xl font-semibold kpi-value">
            {q.sanity_divergencia_pct == null
              ? "—"
              : `${q.sanity_divergencia_pct.toFixed(1)}%`}
          </div>
          {q.sanity_alerta ? (
            <div className="mt-2 badge badge-danger">alerta &gt; 5%</div>
          ) : (
            <div className="mt-2 badge badge-sit1">ok</div>
          )}
        </div>
      </div>

      {q.sem_cid_na_fonte ? (
        <div className="card border-[var(--warn)] p-4 text-sm text-[var(--warn)]">
          Fonte do numerador sem CID ({q.fonte_tipo || "desconhecida"}). Breakdown por condição
          indisponível — totais nacionais/UF usam COUNT DISTINCT consolidado.
        </div>
      ) : null}

      {q.nota_numerador ? (
        <div className="card border-[var(--warn)] p-4 text-sm text-[var(--warn)]">
          {q.nota_numerador}
        </div>
      ) : null}

      {oferta.length > 0 ? (
        <div className="card table-wrap p-2">
          <h2 className="px-2 py-2 text-sm font-semibold">Oferta por UF · doses / CRIE</h2>
          <p className="px-2 pb-2 text-xs text-[var(--muted)]">
            {nac.qualidade_oferta?.fonte || "cache PNI + CNES CRIE"}
          </p>
          <table className="data">
            <thead>
              <tr>
                <th>UF</th>
                <th>Doses ≥5a</th>
                <th>Em CNES CRIE</th>
                <th>CRIEs</th>
                <th>Doses/CRIE</th>
                <th>% fora CRIE</th>
              </tr>
            </thead>
            <tbody>
              {oferta.map((r) => (
                <tr key={r.uf}>
                  <td className="font-bold">{r.uf}</td>
                  <td className="kpi-value">{fmtInt(r.doses_vpc20_ge5)}</td>
                  <td className="kpi-value">{fmtInt(r.doses_em_cnes_crie)}</td>
                  <td className="kpi-value">{fmtInt(r.n_cries_seed)}</td>
                  <td className="kpi-value">{r.doses_por_crie ?? "—"}</td>
                  <td className="kpi-value">
                    {r.pct_fora_crie == null ? "—" : fmtPct(r.pct_fora_crie)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">CIDs não mapeados</h2>
          {unmapped.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">Nenhum CID fora do mapa na carga atual.</p>
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>CID</th>
                    <th>Ocorrências</th>
                  </tr>
                </thead>
                <tbody>
                  {unmapped.map(([cid, n]) => (
                    <tr key={cid}>
                      <td className="font-mono">{cid}</td>
                      <td className="kpi-value">{n}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card p-4">
          <h2 className="mb-3 text-sm font-semibold">Situação 1 — cadastros</h2>
          <p className="mb-2 text-xs text-[var(--muted)]">
            Carregados: {q.situacao1.carregados.join(", ") || "nenhum"}
          </p>
          <p className="mb-3 text-xs text-[var(--muted)]">
            Pendentes: {q.situacao1.pendentes.join(", ") || "nenhum"}
          </p>
          <ul className="space-y-1 text-sm">
            {["1", "2", "3", "4", "8"].map((k) => {
              const ok = q.situacao1.carregados.includes(k);
              const labels: Record<string, string> = {
                "1": "HIV (SICLOM)",
                "2": "Oncológicos (SIA/APAC)",
                "3": "Transplantes (ABTO)",
                "4": "TCTH (ABTO)",
                "8": "Fibrose cística (REBRAFC)",
              };
              return (
                <li
                  key={k}
                  className="flex items-center justify-between rounded-lg bg-[var(--navy-900)] px-3 py-2"
                >
                  <span>{labels[k]}</span>
                  <span className={`badge ${ok ? "badge-sit1" : "badge-warn"}`}>
                    {ok ? "carregado" : "pendente"}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}
