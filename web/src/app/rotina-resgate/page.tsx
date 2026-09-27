import { Kpi, fmtInt } from "@/components/Kpi";
import { getRoutineRescueDashboard } from "@/lib/data";

function ProductBlock({
  title,
  totalDoses,
  totalPessoas,
  referencePeriod,
  extra,
  rows,
}: {
  title: string;
  totalDoses: number;
  totalPessoas: number;
  referencePeriod: string | null;
  extra?: React.ReactNode;
  rows: Array<{ uf: string; doses: number; pessoas: number }>;
}) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="grid gap-3 md:grid-cols-4">
        <Kpi label="Doses observadas" value={fmtInt(totalDoses)} />
        <Kpi label="Pessoas distintas" value={fmtInt(totalPessoas)} />
        <Kpi label="Competência" value={referencePeriod || "—"} />
        <Kpi label="Cobertura" value="não calculada" hint="Exige denominador compatível" />
      </div>
      {extra}
      <div className="card table-wrap p-2">
        <h3 className="px-2 py-2 text-sm font-semibold">Top UFs por doses</h3>
        <table className="data">
          <thead>
            <tr><th>UF</th><th>Doses</th><th>Pessoas</th></tr>
          </thead>
          <tbody>
            {[...rows].sort((a,b)=>b.doses-a.doses).slice(0,10).map((r)=>(
              <tr key={r.uf}>
                <td>{r.uf}</td>
                <td className="kpi-value">{fmtInt(r.doses)}</td>
                <td className="kpi-value">{fmtInt(r.pessoas)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default async function RotinaResgatePage() {
  const data = await getRoutineRescueDashboard();

  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Rotina e resgate</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            MenACWY · febre amarela · tríplice viral · HPV4
          </p>
        </div>
        <div className="card p-6">
          <h2 className="text-lg font-semibold">Sem carga disponível</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Execute o ETL de rotina/resgate para gerar agregados observacionais.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
            python etl/routine_rescue_etl.py
          </pre>
          <p className="mt-3 text-xs text-[var(--muted)]">
            HPV4 permanece bloqueado para ingestão automática até confirmação inequívoca do código PNI.
          </p>
        </div>
      </div>
    );
  }

  const m = data.menacwy;
  const y = data.febre_amarela;
  const t = data.triplice_viral;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Rotina e resgate</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Registros observados no PNI/RNDS, com contextos confirmados mantidos separados da cobertura.
        </p>
      </div>

      <ProductBlock
        title="MenACWY"
        totalDoses={m.total_doses}
        totalPessoas={m.total_pessoas}
        referencePeriod={m.reference_period}
        rows={m.por_uf}
        extra={
          <div className="card p-4 text-sm">
            <span className="font-medium">Rotina/reforço conhecido:</span>{" "}
            {fmtInt(m.known_routine_booster_records)} registros
            <div className="mt-1 text-xs text-[var(--muted)]">
              Código 74 + estratégia 1 + dose 38, contado linha a linha.
            </div>
          </div>
        }
      />

      <ProductBlock
        title="Febre amarela"
        totalDoses={y.total_doses}
        totalPessoas={y.total_pessoas}
        referencePeriod={y.reference_period}
        rows={y.por_uf}
        extra={
          <div className="grid gap-3 md:grid-cols-2">
            <Kpi label="Doses com código conhecido" value={fmtInt(y.known_dose_records)} />
            <Kpi label="Outros códigos de dose" value={fmtInt(y.unknown_dose_records)} />
          </div>
        }
      />

      <ProductBlock
        title="Tríplice viral"
        totalDoses={t.total_doses}
        totalPessoas={t.total_pessoas}
        referencePeriod={t.reference_period}
        rows={t.por_uf}
        extra={
          <div className="grid gap-3 md:grid-cols-2">
            <Kpi label="Bloqueio confirmado" value={fmtInt(t.blockade_records)} />
            <Kpi label="Intensificação confirmada" value={fmtInt(t.intensification_records)} />
          </div>
        }
      />

      <section className="card p-4">
        <h2 className="text-sm font-semibold">HPV4</h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Status: <span className="font-mono">{data.hpv4_status}</span>. A regra clínica nacional já
          está estruturada, mas o PREVNAR não iniciará ingestão automática sem código PNI oficial
          inequivocamente confirmado.
        </p>
      </section>

      <section className="card p-4 text-xs text-[var(--muted)]">
        Doses observadas não equivalem a cobertura, oportunidade ou esquema completo. Esses
        indicadores exigem denominadores, histórico e metodologia compatíveis.
      </section>
    </div>
  );
}
