import { Kpi, fmtInt, fmtPct } from "@/components/Kpi";
import {
  getRoutineRescueDashboard,
  type RoutineRescueMart,
} from "@/lib/data";

function FreshnessBadge({ status }: { status?: string }) {
  const cls =
    status === "atual"
      ? "badge-sit1"
      : status === "atencao"
        ? "badge-warn"
        : status === "desatualizado"
          ? "badge-danger"
          : "badge-warn";
  return <span className={`badge ${cls}`}>{status || "desconhecido"}</span>;
}

function MappingBadge({ confirmedShare }: { confirmedShare: number | null }) {
  if (confirmedShare == null) {
    return <span className="badge badge-warn">sem registros</span>;
  }
  if (confirmedShare >= 95) {
    return <span className="badge badge-sit1">{fmtPct(confirmedShare)} confirmado</span>;
  }
  return <span className="badge badge-warn">{fmtPct(confirmedShare)} confirmado</span>;
}

function TopUfTable({ mart }: { mart: RoutineRescueMart }) {
  return (
    <div className="card table-wrap p-2">
      <h3 className="px-2 py-2 text-sm font-semibold">Top UFs por registros observados</h3>
      <table className="data">
        <thead>
          <tr>
            <th>UF</th>
            <th>Observados</th>
            <th>Contexto confirmado</th>
            <th>Pessoas confirmadas</th>
          </tr>
        </thead>
        <tbody>
          {[...mart.por_uf]
            .sort((a, b) => b.observed_doses - a.observed_doses)
            .slice(0, 10)
            .map((row) => (
              <tr key={row.uf}>
                <td>{row.uf}</td>
                <td className="kpi-value">{fmtInt(row.observed_doses)}</td>
                <td className="kpi-value">{fmtInt(row.confirmed_doses)}</td>
                <td className="kpi-value">{fmtInt(row.confirmed_people)}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

function ContextTable({ mart }: { mart: RoutineRescueMart }) {
  const contexts = Object.entries(mart.contextos_confirmados).sort((a, b) => b[1] - a[1]);
  return (
    <div className="card table-wrap p-2">
      <h3 className="px-2 py-2 text-sm font-semibold">Contextos confirmados</h3>
      <table className="data">
        <thead>
          <tr>
            <th>Contexto</th>
            <th>Registros</th>
          </tr>
        </thead>
        <tbody>
          {contexts.length ? (
            contexts.map(([key, value]) => (
              <tr key={key}>
                <td className="font-mono text-xs">{key}</td>
                <td className="kpi-value">{fmtInt(value)}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={2} className="text-[var(--muted)]">
                Nenhum contexto confirmado na carga atual.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function QualityCard({ mart }: { mart: RoutineRescueMart }) {
  const outside = mart.mismatches?.code_hit_outside_confirmed_context || 0;
  const missing = mart.mismatches?.missing_patient_or_date || 0;
  return (
    <div className="card p-4 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="font-semibold">Qualidade do mapeamento</div>
        <FreshnessBadge status={mart.provenance?.freshness?.status} />
      </div>
      <div className="mt-3 grid gap-2 md:grid-cols-2">
        <div>
          <span className="text-[var(--muted)]">Fora do contexto confirmado:</span>{" "}
          <strong>{fmtInt(outside)}</strong>
        </div>
        <div>
          <span className="text-[var(--muted)]">Sem paciente/data válida:</span>{" "}
          <strong>{fmtInt(missing)}</strong>
        </div>
        <div>
          <span className="text-[var(--muted)]">source_id:</span>{" "}
          <span className="font-mono">{mart.provenance?.source_id || "—"}</span>
        </div>
        <div>
          <span className="text-[var(--muted)]">run_id:</span>{" "}
          <span className="font-mono">{mart.provenance?.run_id || "—"}</span>
        </div>
      </div>
    </div>
  );
}

function VaccineSection({
  title,
  subtitle,
  mart,
}: {
  title: string;
  subtitle: string;
  mart: RoutineRescueMart;
}) {
  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">{subtitle}</p>
        </div>
        <MappingBadge confirmedShare={mart.confirmed_share_pct} />
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <Kpi
          label="Registros observados"
          value={fmtInt(mart.observed_code_hits)}
          hint="Todos os registros com o código do imunobiológico"
        />
        <Kpi
          label="Pessoas observadas"
          value={fmtInt(mart.observed_people)}
          hint="Deduplicadas na carga"
        />
        <Kpi
          label="Contexto confirmado"
          value={fmtInt(mart.confirmed_context_doses)}
          tone="accent"
          hint="Somente estratégia/dose já mapeadas oficialmente"
        />
        <Kpi
          label="Pessoas confirmadas"
          value={fmtInt(mart.confirmed_context_people)}
          tone="accent"
          hint={mart.reference_period ? `Competência: ${mart.reference_period}` : undefined}
        />
      </div>

      <div className="card p-4 text-xs text-[var(--muted)]">
        {mart.interpretation}
      </div>

      <div className="grid gap-3 xl:grid-cols-2">
        <TopUfTable mart={mart} />
        <ContextTable mart={mart} />
      </div>

      <QualityCard mart={mart} />
    </section>
  );
}

export default async function RotinaResgatePage() {
  const data = await getRoutineRescueDashboard();

  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Rotina, resgate e resposta</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            MenACWY · febre amarela · tríplice viral · HPV4
          </p>
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold">Sem carga de rotina/resgate disponível</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            O módulo normativo e o ETL estão configurados, mas o mart ainda não foi gerado no
            ambiente atual.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
            python etl/routine_rescue_etl.py
          </pre>
          <p className="mt-3 text-xs text-[var(--muted)]">
            O PREVNAR não transforma registros de código de vacina em cobertura automaticamente.
            Apenas combinações de contexto oficialmente mapeadas são apresentadas como confirmadas.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-semibold">Rotina, resgate e resposta</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Monitoramento conservador de MenACWY, febre amarela e tríplice viral. HPV4 permanece em
          mapeamento parcial.
        </p>
      </div>

      <section className="card p-5">
        <div className="grid gap-3 md:grid-cols-4">
          <Kpi label="Páginas processadas" value={fmtInt(data.pages)} />
          <Kpi label="Registros varridos" value={fmtInt(data.scanned)} />
          <Kpi label="Versão do mapeamento" value={data.mapping_plan_version || "—"} />
          <Kpi
            label="HPV4"
            value="Mapeamento parcial"
            tone="warn"
            hint={`Código ${data.hpv4.immunobiologic_codes?.join(", ") || "—"} confirmado; estratégia/dose/grupos pendentes`}
          />
        </div>
      </section>

      <VaccineSection
        title="MenACWY"
        subtitle="Código 74. Contexto decisório atual: reforço de rotina estratégia 1 / dose 38."
        mart={data.menacwy}
      />

      <VaccineSection
        title="Febre amarela"
        subtitle="Código 14. Contextos confirmados atuais utilizam doses de cobertura 1, 9 e 36."
        mart={data.febre_amarela}
      />

      <VaccineSection
        title="Tríplice viral"
        subtitle="Código 24. Bloqueio (estratégia 3) e intensificação (estratégia 4) permanecem separados da rotina."
        mart={data.triplice_viral}
      />

      <section className="card p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold">HPV4</h2>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Código nacional 67 confirmado no CodeSystem do Ministério da Saúde.
            </p>
          </div>
          <span className="badge badge-warn">ETL bloqueado por mapeamento parcial</span>
        </div>
        <p className="mt-3 text-sm text-[var(--muted)]">
          O PREVNAR ainda não coleta HPV4 neste módulo porque estratégia, códigos de dose e grupos
          de atendimento da regra de entrada vigente não foram consolidados. A regra clínica de
          rotina continua disponível no motor normativo, mas a camada de monitoramento permanece
          separada.
        </p>
      </section>

      <section className="card p-5 text-xs text-[var(--muted)]">
        <strong className="text-[var(--text)]">Interpretação:</strong> registros observados indicam
        presença do código do imunobiológico na fonte. Contextos confirmados indicam apenas
        combinações estratégia/dose explicitamente mapeadas nesta versão. Nenhum dos dois, por si
        só, representa cobertura populacional.
      </section>
    </div>
  );
}
