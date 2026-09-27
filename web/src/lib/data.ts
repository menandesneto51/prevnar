import type { DashboardData, GapLinha } from "./types";
import { readFile } from "fs/promises";
import { existsSync } from "fs";
import path from "path";

const dataDir = path.join(process.cwd(), "public", "data");

export async function getDashboard(): Promise<DashboardData> {
  const raw = await readFile(path.join(dataDir, "dashboard.json"), "utf-8");
  return JSON.parse(raw) as DashboardData;
}

export async function getGapLinhas(): Promise<GapLinha[]> {
  const raw = await readFile(path.join(dataDir, "mart_gap_condicao_uf.json"), "utf-8");
  const parsed = JSON.parse(raw) as { linhas: GapLinha[] };
  return parsed.linhas;
}

export async function getNacional<T = Record<string, unknown>>(): Promise<T> {
  const raw = await readFile(path.join(dataDir, "nacional.json"), "utf-8");
  return JSON.parse(raw) as T;
}

export function fmtInt(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("pt-BR");
}

export function fmtPct(n: number | null | undefined, digits = 1): string {
  if (n === null || n === undefined) return "—";
  return `${n.toFixed(digits)}%`;
}

export function fmtBRL(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
}


export type RespiratoryMart = {
  immunobiologic_id: string;
  total_doses: number;
  total_pessoas: number;
  por_uf: Array<{ uf: string; doses: number; pessoas: number }>;
  por_municipio: Array<{ municipio_ibge: string; doses: number; pessoas: number }>;
  linha_tempo: Array<{ ano_mes: string; doses: number; pessoas: number }>;
  estrategias: Record<string, number>;
  doses_codigos: Record<string, number>;
  grupos_atendimento: Record<string, number>;
  apresentacoes: Record<string, number>;
  invalid_mapping: Record<string, number>;
  reference_period: string | null;
  private_share_pct?: number | null;
  sus_doses?: number;
  private_doses?: number;
  pt1_doses?: number;
  pt2_doses?: number;
  provenance?: {
    run_id?: string;
    source_id?: string;
    reference_period?: string | null;
    retrieved_at?: string;
    freshness?: {
      status?: string;
      age_days?: number | null;
      critical_for_decision?: boolean;
    };
  };
};

export type RespiratoryDashboard = {
  generated_at: string;
  pages: number;
  scanned: number;
  vvsr_materna: RespiratoryMart;
  nirsevimab: RespiratoryMart;
};

export async function getRespiratoryDashboard(): Promise<RespiratoryDashboard | null> {
  const candidates = [
    path.join(dataDir, "respiratory_dashboard.json"),
    path.join(process.cwd(), "..", "data", "mart", "respiratory_dashboard.json"),
  ];
  const file = candidates.find((candidate) => existsSync(candidate));
  if (!file) return null;
  const raw = await readFile(file, "utf-8");
  return JSON.parse(raw) as RespiratoryDashboard;
}


export type RoutineRescueMart = {
  immunobiologic_id: string;
  observed_code_hits: number;
  observed_people: number;
  confirmed_context_doses: number;
  confirmed_context_people: number;
  confirmed_share_pct: number | null;
  por_uf: Array<{
    uf: string;
    observed_doses: number;
    observed_people: number;
    confirmed_doses: number;
    confirmed_people: number;
  }>;
  linha_tempo: Array<{
    ano_mes: string;
    observed_doses: number;
    confirmed_doses: number;
  }>;
  estrategias: Record<string, number>;
  doses_codigos: Record<string, number>;
  grupos_atendimento: Record<string, number>;
  contextos_confirmados: Record<string, number>;
  mismatches: Record<string, number>;
  reference_period: string | null;
  interpretation: string;
  provenance?: {
    run_id?: string;
    source_id?: string;
    reference_period?: string | null;
    retrieved_at?: string;
    freshness?: {
      status?: string;
      age_days?: number | null;
      critical_for_decision?: boolean;
    };
  };
};

export type RoutineRescueDashboard = {
  generated_at: string;
  pages: number;
  scanned: number;
  mapping_plan_version: string;
  hpv4: {
    status: string;
    reason: string;
    immunobiologic_codes: string[];
  };
  menacwy: RoutineRescueMart;
  febre_amarela: RoutineRescueMart;
  triplice_viral: RoutineRescueMart;
};

export async function getRoutineRescueDashboard(): Promise<RoutineRescueDashboard | null> {
  const candidates = [
    path.join(dataDir, "routine_rescue_dashboard.json"),
    path.join(process.cwd(), "..", "data", "mart", "routine_rescue_dashboard.json"),
  ];
  const file = candidates.find((candidate) => existsSync(candidate));
  if (!file) return null;
  const raw = await readFile(file, "utf-8");
  return JSON.parse(raw) as RoutineRescueDashboard;
}


export type NormativeActRow = {
  id: string;
  resolved: boolean;
  type?: string | null;
  number?: string | null;
  scope?: string | null;
  published_at?: string | null;
  effective_from?: string | null;
  official_url?: string | null;
  topic?: string[];
};

export type NormativeRuleRow = {
  rule_id?: string | null;
  rule_type?: string | null;
  rule_context?: string | null;
  status?: string | null;
  active_on_as_of: boolean;
  effective_from?: string | null;
  effective_until?: string | null;
  geographic_scope: {
    type?: string | null;
    codes: string[];
  };
  normative_acts: string[];
  note?: string | null;
};

export type NormativeMatrixItem = {
  immunobiologic_id: string;
  display: string;
  name?: string | null;
  type?: string | null;
  active_entity: boolean;
  monitored: boolean;
  onboarding_status?: string | null;
  pni_codes: string[];
  code_mapping_status?: string | null;
  active_rule_count: number;
  draft_rule_count: number;
  rules: NormativeRuleRow[];
  normative_acts: NormativeActRow[];
};

export type NormativeMatrix = {
  schema_version: string;
  generated_at: string;
  as_of: string;
  registry_version?: string | null;
  rules_version?: string | null;
  legal_updated_at?: string | null;
  summary: {
    immunobiologics: number;
    active_rules: number;
    draft_rules: number;
    monitored_immunobiologics: number;
    types: Record<string, number>;
    onboarding_status: Record<string, number>;
    unresolved_legal_references: string[];
  };
  immunobiologics: NormativeMatrixItem[];
  interpretation: string;
};

export async function getNormativeMatrix(): Promise<NormativeMatrix | null> {
  const candidates = [
    path.join(dataDir, "normative_matrix.json"),
    path.join(process.cwd(), "..", "data", "mart", "normative_matrix.json"),
  ];
  const file = candidates.find((candidate) => existsSync(candidate));
  if (!file) return null;
  const raw = await readFile(file, "utf-8");
  return JSON.parse(raw) as NormativeMatrix;
}


export type NormativeBacklogItem = {
  priority: string;
  category: string;
  immunobiologic_id: string;
  display: string;
  message: string;
  next_gate: string;
};

export type NormativeBacklog = {
  schema_version: string;
  as_of: string;
  summary: {
    total: number;
    by_priority: Record<string, number>;
  };
  items: NormativeBacklogItem[];
  interpretation: string;
};

export async function getNormativeBacklog(): Promise<NormativeBacklog | null> {
  const candidates = [
    path.join(dataDir, "normative_backlog.json"),
    path.join(process.cwd(), "..", "data", "mart", "normative_backlog.json"),
  ];
  const file = candidates.find((candidate) => existsSync(candidate));
  if (!file) return null;
  const raw = await readFile(file, "utf-8");
  return JSON.parse(raw) as NormativeBacklog;
}


export type InfluenzaDashboard = {
  immunobiologic_id: string;
  scanned: number;
  observed_code_hits: number;
  observed_people: number;
  confirmed_context_doses: number;
  confirmed_context_people: number;
  confirmed_share_pct: number | null;
  sus_confirmed_doses: number;
  private_confirmed_doses: number;
  private_share_pct: number | null;
  contextos_confirmados: Record<string, number>;
  estrategias: Record<string, number>;
  doses_codigos: Record<string, number>;
  apresentacoes: Record<string, number>;
  por_uf: Array<{
    uf: string;
    observed_doses: number;
    observed_people: number;
    confirmed_doses: number;
    confirmed_people: number;
  }>;
  linha_tempo: Array<{
    ano_mes: string;
    observed_doses: number;
    confirmed_doses: number;
  }>;
  mismatches: Record<string, number>;
  reference_period: string | null;
  pending_contexts: Array<{ id: string; reason: string }>;
  interpretation: string;
  pages?: number;
  generated_at?: string;
  provenance?: {
    run_id?: string;
    source_id?: string;
    reference_period?: string | null;
    retrieved_at?: string;
    freshness?: {
      status?: string;
      age_days?: number | null;
      critical_for_decision?: boolean;
    };
  };
};

export async function getInfluenzaDashboard(): Promise<InfluenzaDashboard | null> {
  const candidates = [
    path.join(dataDir, "influenza_2026_dashboard.json"),
    path.join(process.cwd(), "..", "data", "mart", "influenza_2026_dashboard.json"),
  ];
  const file = candidates.find((candidate) => existsSync(candidate));
  if (!file) return null;
  const raw = await readFile(file, "utf-8");
  return JSON.parse(raw) as InfluenzaDashboard;
}


export type CovidOperationalStatus = {
  immunobiologic_id: string;
  onboarding_status?: string | null;
  code_mapping_status?: string | null;
  monitored: boolean;
  pni_codes: string[];
  product: {
    product_variant_id: string;
    name: string;
    manufacturer?: string | null;
    technology?: string | null;
    min_age_years?: number | null;
    dose_ml?: number | null;
    dose_mcg?: number | null;
    doses_per_vial?: number | null;
    dilution_required?: boolean | null;
    route?: string | null;
    anvisa_registration?: string | null;
    storage_celsius_min?: number | null;
    storage_celsius_max?: number | null;
    must_not_freeze?: boolean | null;
    max_hours_after_opening?: number | null;
  } | null;
  transition_management: {
    monitor: Array<{
      id: string;
      source_candidate?: string | null;
      grain?: string | null;
    }>;
    recommended_alerts: string[];
  };
  clinical_automation: {
    active_pathways: string[];
    pending_pathways: string[];
  };
  data_mapping: {
    pni_product_codes_status?: string | null;
    rule?: string | null;
  };
};

export async function getCovidOperationalStatus(): Promise<CovidOperationalStatus | null> {
  const referenceCandidates = [
    path.join(process.cwd(), "..", "data", "reference"),
    path.join(process.cwd(), "data", "reference"),
  ];
  const referenceDir = referenceCandidates.find((candidate) =>
    existsSync(path.join(candidate, "covid19_2026_operational_plan.json")),
  );
  if (!referenceDir) return null;

  const [planRaw, registryRaw] = await Promise.all([
    readFile(path.join(referenceDir, "covid19_2026_operational_plan.json"), "utf-8"),
    readFile(path.join(referenceDir, "immunobiologic_registry.json"), "utf-8"),
  ]);

  const plan = JSON.parse(planRaw) as {
    immunobiologic_id: string;
    product_variant_id: string;
    transition_management: CovidOperationalStatus["transition_management"];
    clinical_automation: CovidOperationalStatus["clinical_automation"];
    data_mapping: CovidOperationalStatus["data_mapping"];
  };
  const registry = JSON.parse(registryRaw) as {
    immunobiologics: Array<{
      immunobiologic_id: string;
      onboarding_status?: string | null;
      code_mapping_status?: string | null;
      monitored?: boolean;
      pni_codes?: string[];
      product_variants?: Array<CovidOperationalStatus["product"]>;
    }>;
  };
  const item = registry.immunobiologics.find(
    (row) => row.immunobiologic_id === plan.immunobiologic_id,
  );
  if (!item) return null;

  const variants = (item.product_variants || []).filter(Boolean) as NonNullable<
    CovidOperationalStatus["product"]
  >[];
  const product =
    variants.find((row) => row.product_variant_id === plan.product_variant_id) || null;

  return {
    immunobiologic_id: item.immunobiologic_id,
    onboarding_status: item.onboarding_status,
    code_mapping_status: item.code_mapping_status,
    monitored: Boolean(item.monitored),
    pni_codes: item.pni_codes || [],
    product,
    transition_management: plan.transition_management,
    clinical_automation: plan.clinical_automation,
    data_mapping: plan.data_mapping,
  };
}


export type CovidTransitionAlert = {
  territory_code: string;
  facility_cnes?: string | null;
  product_variant_id: string;
  lot: string;
  expiry_date: string;
  alert_id: string;
  severity: string;
  reason: string;
};

export type CovidTransitionDashboard = {
  schema_version: string;
  source_id: string;
  generated_at: string;
  reference_period: string | null;
  record_count: number;
  totals: {
    stock_available_doses: number;
    doses_administered_30d: number;
    physical_losses_30d: number;
    technical_losses_30d: number;
    lots: number;
    territories: number;
    critical_alerts: number;
    attention_alerts: number;
  };
  by_territory: Array<{
    territory_code: string;
    stock_available_doses: number;
    doses_administered_30d: number;
    physical_losses_30d: number;
    technical_losses_30d: number;
    lots: number;
    critical_alerts: number;
    attention_alerts: number;
  }>;
  alerts: CovidTransitionAlert[];
  interpretation: string;
  provenance?: {
    run_id?: string;
    source_id?: string;
    retrieved_at?: string;
    reference_period?: string | null;
    freshness?: {
      status?: string;
      age_days?: number | null;
      critical_for_decision?: boolean;
    };
    input_files?: Array<{
      name?: string;
      size_bytes?: number;
      sha256?: string;
    }>;
  };
};

export async function getCovidTransitionDashboard(): Promise<CovidTransitionDashboard | null> {
  const candidates = [
    path.join(dataDir, "covid19_transition_dashboard.json"),
    path.join(process.cwd(), "..", "data", "mart", "covid19_transition_dashboard.json"),
  ];
  const file = candidates.find((candidate) => existsSync(candidate));
  if (!file) return null;
  const raw = await readFile(file, "utf-8");
  return JSON.parse(raw) as CovidTransitionDashboard;
}
