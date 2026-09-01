import Link from "next/link";
import { BrazilUfGrid } from "@/components/BrazilUfGrid";
import { fmtInt } from "@/components/Kpi";
import { getDashboard } from "@/lib/data";

export default async function UfsPage() {
  const data = await getDashboard();
  const nomes = Object.fromEntries(data.ufs.map((u) => [u.uf, u.nome]));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Por UF</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Gap agregado das condições com denominador disponível. Clique na UF para o drill-down.
        </p>
      </div>

      <BrazilUfGrid data={data.por_uf} />

      <div className="card table-wrap p-2">
        <table className="data">
          <thead>
            <tr>
              <th>UF</th>
              <th>Nome</th>
              <th>Elegíveis</th>
              <th>Vacinados*</th>
              <th>Gap</th>
              <th>Pendências Sit.1</th>
            </tr>
          </thead>
          <tbody>
            {data.por_uf.map((u) => (
              <tr key={u.uf}>
                <td>
                  <Link href={`/ufs/${u.uf}`} className="font-bold hover:text-[var(--accent)]">
                    {u.uf}
                  </Link>
                </td>
                <td>{nomes[u.uf] ?? u.uf}</td>
                <td className="kpi-value">{fmtInt(u.elegiveis)}</td>
                <td className="kpi-value text-[var(--accent)]">
                  {fmtInt(u.pessoas_vacinadas_consolidado ?? u.pessoas_vacinadas)}
                </td>
                <td className="kpi-value text-[var(--warn)]">{fmtInt(u.gap)}</td>
                <td>{u.pendencias || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="px-3 pb-3 text-[10px] text-[var(--muted)]">
          * Quando disponível, usa total consolidado COUNT DISTINCT por UF (sem dupla-contagem por
          CID).
        </p>
      </div>
    </div>
  );
}
