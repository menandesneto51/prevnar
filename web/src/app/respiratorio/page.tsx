import { CovidTransitionPanel } from "@/components/CovidTransitionPanel";
import { Kpi, fmtInt, fmtPct } from "@/components/Kpi";
import {
  getCovidOperationalStatus,
  getInfluenzaDashboard,
  getRespiratoryDashboard,
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

export default async function RespiratorioPage() {
  const [data, influenza, covid] = await Promise.all([
    getRespiratoryDashboard(),
    getInfluenzaDashboard(),
    getCovidOperationalStatus(),
  ]);

  if (!data) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Imunização respiratória</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            VVSR materna · nirsevimabe · influenza · covid-19
          </p>
        </div>
        <div className="card p-6">
          <h2 className="text-lg font-semibold">Sem carga respiratória disponível</h2>
          <p className="mt-2 text-sm text-[var(--muted)]">
            O módulo está configurado, mas ainda não há mart respiratório gerado. Execute o ETL
            respiratório em ambiente autorizado para produzir os agregados.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-black/5 p-3 text-xs">
            python etl/respiratory_etl.py
          </pre>
          <p className="mt-3 text-xs text-[var(--muted)]">
            O painel não fabrica cobertura ou oportunidade na ausência de denominadores clínicos
            compatíveis.
          </p>
        </div>
      </div>
    );
  }

  const v = data.vvsr_materna;
  const n = data.nirsevimab;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Imunização respiratória</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Indicadores observados de VVSR materna e nirsevimabe. Influenza e covid-19 permanecem em
          onboarding normativo e de dados.
        </p>
      </div>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">VVSR materna</h2>
          <FreshnessBadge status={v.provenance?.freshness?.status} />
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <Kpi label="Doses administradas" value={fmtInt(v.total_doses)} />
          <Kpi label="Gestantes vacinadas" value={fmtInt(v.total_pessoas)} />
          <Kpi label="Competência" value={v.reference_period || "—"} />
          <Kpi
            label="Idade do dado"
            value={
              v.provenance?.freshness?.age_days == null
                ? "—"
                : `${v.provenance.freshness.age_days} dias`
            }
          />
        </div>

        <div className="card table-wrap p-2">
          <h3 className="px-2 py-2 text-sm font-semibold">Top UFs por doses</h3>
          <table className="data">
            <thead>
              <tr>
                <th>UF</th>
                <th>Doses</th>
                <th>Pessoas</th>
              </tr>
            </thead>
            <tbody>
              {[...v.por_uf]
                .sort((a, b) => b.doses - a.doses)
                .slice(0, 10)
                .map((row) => (
                  <tr key={row.uf}>
                    <td>{row.uf}</td>
                    <td className="kpi-value">{fmtInt(row.doses)}</td>
                    <td className="kpi-value">{fmtInt(row.pessoas)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="card p-4 text-xs text-[var(--muted)]">
          Cobertura por gestação, oportunidade a partir da 28ª semana e administração precoce
          dependem de idade gestacional e gestação corrente em fonte compatível. Esses indicadores
          não são inferidos apenas do PNI/RNDS.
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">Nirsevimabe</h2>
          <FreshnessBadge status={n.provenance?.freshness?.status} />
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <Kpi label="Administrações" value={fmtInt(n.total_doses)} />
          <Kpi label="Crianças distintas" value={fmtInt(n.total_pessoas)} />
          <Kpi label="P/T1" value={fmtInt(n.pt1_doses)} hint="Uma unidade/seringa" />
          <Kpi label="P/T2" value={fmtInt(n.pt2_doses)} hint="Duas unidades/seringas" />
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <Kpi label="Estratégia SUS" value={fmtInt(n.sus_doses)} />
          <Kpi label="Serviço privado" value={fmtInt(n.private_doses)} />
          <Kpi
            label="Participação privada"
            value={fmtPct(n.private_share_pct)}
            hint="Estratégia 8 entre registros 2/8"
          />
        </div>

        <div className="card table-wrap p-2">
          <h3 className="px-2 py-2 text-sm font-semibold">Top UFs por administrações</h3>
          <table className="data">
            <thead>
              <tr>
                <th>UF</th>
                <th>Doses</th>
                <th>Pessoas</th>
              </tr>
            </thead>
            <tbody>
              {[...n.por_uf]
                .sort((a, b) => b.doses - a.doses)
                .slice(0, 10)
                .map((row) => (
                  <tr key={row.uf}>
                    <td>{row.uf}</td>
                    <td className="kpi-value">{fmtInt(row.doses)}</td>
                    <td className="kpi-value">{fmtInt(row.pessoas)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="card table-wrap p-2">
          <h3 className="px-2 py-2 text-sm font-semibold">Grupos de atendimento registrados</h3>
          <table className="data">
            <thead>
              <tr>
                <th>Código</th>
                <th>Registros</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(n.grupos_atendimento)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .map(([code, value]) => (
                  <tr key={code}>
                    <td className="font-mono text-xs">{code}</td>
                    <td className="kpi-value">{fmtInt(value)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="card p-4 text-xs text-[var(--muted)]">
          Cobertura em elegíveis ainda não é exibida. Prematuridade e comorbidades exigem fonte
          clínica compatível ou proxy explicitamente classificado, com deduplicação válida.
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold">Influenza 2026</h2>
            <p className="mt-1 text-xs text-[var(--muted)]">
              NT 24/2026 · códigos 33/77/110 · rotina, especial e serviço privado separados
            </p>
          </div>
          {influenza ? (
            <FreshnessBadge status={influenza.provenance?.freshness?.status} />
          ) : (
            <span className="badge badge-warn">sem carga</span>
          )}
        </div>

        {influenza ? (
          <>
            <div className="grid gap-3 md:grid-cols-4">
              <Kpi label="Registros observados" value={fmtInt(influenza.observed_code_hits)} />
              <Kpi
                label="Contextos confirmados"
                value={fmtInt(influenza.confirmed_context_doses)}
                hint={`${fmtPct(influenza.confirmed_share_pct)} dos registros observados`}
              />
              <Kpi label="SUS confirmado" value={fmtInt(influenza.sus_confirmed_doses)} />
              <Kpi
                label="Privado confirmado"
                value={fmtInt(influenza.private_confirmed_doses)}
                hint={`Participação privada: ${fmtPct(influenza.private_share_pct)}`}
              />
            </div>

            <div className="grid gap-3 xl:grid-cols-2">
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
                    {Object.entries(influenza.contextos_confirmados)
                      .sort((a, b) => b[1] - a[1])
                      .map(([key, value]) => (
                        <tr key={key}>
                          <td className="font-mono text-xs">{key}</td>
                          <td className="kpi-value">{fmtInt(value)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>

              <div className="card table-wrap p-2">
                <h3 className="px-2 py-2 text-sm font-semibold">Top UFs</h3>
                <table className="data">
                  <thead>
                    <tr>
                      <th>UF</th>
                      <th>Observados</th>
                      <th>Confirmados</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...influenza.por_uf]
                      .sort((a, b) => b.observed_doses - a.observed_doses)
                      .slice(0, 10)
                      .map((row) => (
                        <tr key={row.uf}>
                          <td>{row.uf}</td>
                          <td className="kpi-value">{fmtInt(row.observed_doses)}</td>
                          <td className="kpi-value">{fmtInt(row.confirmed_doses)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card p-4 text-xs text-[var(--muted)]">
              {influenza.interpretation} A vacinação escolar para pessoas ≤14 anos usa a
              estratégia 14 conforme orientação oficial específica de registro. O ValueSet FHIR
              BREstrategiaVacinacao 1.1.0 publicado ainda não lista esse conceito. Cobertura só
              deve ser calculada para grupos com denominador metodologicamente compatível.
            </div>
          </>
        ) : (
          <div className="card p-4 text-sm text-[var(--muted)]">
            O mapeamento oficial está estruturado, mas ainda não existe carga agregada. Execute{" "}
            <code>python etl/influenza_etl.py</code>.
          </div>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Covid-19 2026</h2>
            <p className="mt-1 text-xs text-[var(--muted)]">
              Regras clínicas selecionadas + perfil operacional Comirnaty LP.8.1
            </p>
          </div>
          <span className="badge badge-warn">PNI 87 · detalhes pendentes</span>
        </div>

        {covid ? (
          <>
            <div className="grid gap-3 md:grid-cols-4">
              <Kpi
                label="Gestante"
                value="1 dose/gestação"
                hint="Intervalo mínimo de 6 meses quando houver dose anterior"
              />
              <Kpi
                label="≥60 anos"
                value="Semestral"
                hint="Uma dose a cada 6 meses"
              />
              <Kpi
                label="Mapeamento PNI"
                value={covid.pni_codes.length ? covid.pni_codes.join(", ") : "Pendente"}
                tone="warn"
                hint={covid.code_mapping_status || undefined}
              />
              <Kpi
                label="Monitoramento de doses"
                value={covid.monitored ? "Ativo" : "Bloqueado"}
                tone={covid.monitored ? "accent" : "warn"}
                hint="Código 87 confirmado; ETL aguarda estratégia, dose e grupos"
              />
            </div>

            {covid.product ? (
              <div className="card p-4">
                <h3 className="text-sm font-semibold">{covid.product.name}</h3>
                <div className="mt-3 grid gap-3 text-sm md:grid-cols-4">
                  <div>
                    <div className="text-xs text-[var(--muted)]">Faixa do produto</div>
                    <div className="font-semibold">≥ {covid.product.min_age_years ?? "—"} anos</div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--muted)]">Dose</div>
                    <div className="font-semibold">
                      {covid.product.dose_ml ?? "—"} mL · {covid.product.dose_mcg ?? "—"} mcg
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--muted)]">Frasco</div>
                    <div className="font-semibold">{covid.product.doses_per_vial ?? "—"} doses</div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--muted)]">Conservação</div>
                    <div className="font-semibold">
                      {covid.product.storage_celsius_min ?? "—"}–{covid.product.storage_celsius_max ?? "—"} °C
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--muted)]">Via</div>
                    <div className="font-semibold">{covid.product.route || "—"}</div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--muted)]">Diluição</div>
                    <div className="font-semibold">
                      {covid.product.dilution_required === false ? "Não" : "Verificar"}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--muted)]">Após abertura</div>
                    <div className="font-semibold">
                      até {covid.product.max_hours_after_opening ?? "—"} h
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--muted)]">Anvisa</div>
                    <div className="font-mono text-xs">
                      {covid.product.anvisa_registration || "—"}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            <CovidTransitionPanel />

            <div className="grid gap-3 xl:grid-cols-2">
              <div className="card table-wrap p-2">
                <h3 className="px-2 py-2 text-sm font-semibold">Transição: itens a monitorar</h3>
                <table className="data">
                  <thead>
                    <tr>
                      <th>Item</th>
                      <th>Fonte candidata</th>
                      <th>Granularidade</th>
                    </tr>
                  </thead>
                  <tbody>
                    {covid.transition_management.monitor.map((row) => (
                      <tr key={row.id}>
                        <td className="font-mono text-xs">{row.id}</td>
                        <td>{row.source_candidate || "—"}</td>
                        <td className="text-xs">{row.grain || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="card p-4">
                <h3 className="text-sm font-semibold">Alertas candidatos</h3>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm">
                  {covid.transition_management.recommended_alerts.map((alert) => (
                    <li key={alert} className="font-mono text-xs">{alert}</li>
                  ))}
                </ul>
                <div className="mt-4 text-xs text-[var(--muted)]">
                  Estes são gates operacionais de estoque/transição; não representam alertas
                  clínicos individuais.
                </div>
              </div>
            </div>

            <div className="card p-4 text-xs text-[var(--muted)]">
              Caminhos clínicos ativos: {covid.clinical_automation.active_pathways.join(", ")}.
              Pendentes: {covid.clinical_automation.pending_pathways.join(", ")}.
              O código PNI 87 está confirmado; estratégia, dose e grupos de atendimento ainda
              precisam ser consolidados antes da ativação dos indicadores de doses.
            </div>
          </>
        ) : (
          <div className="card p-4 text-sm text-[var(--muted)]">
            O perfil operacional ainda não pôde ser carregado no build atual.
          </div>
        )}
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold">Qualidade e proveniência</h2>
        <div className="mt-3 grid gap-3 text-xs md:grid-cols-2">
          <div>
            <div className="font-medium">VVSR materna</div>
            <div className="mt-1 text-[var(--muted)]">
              source_id: {v.provenance?.source_id || "—"} · run_id:{" "}
              {v.provenance?.run_id || "—"}
            </div>
          </div>
          <div>
            <div className="font-medium">Nirsevimabe</div>
            <div className="mt-1 text-[var(--muted)]">
              source_id: {n.provenance?.source_id || "—"} · run_id:{" "}
              {n.provenance?.run_id || "—"}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
