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


export type ImmunobiologicCatalogItem = {
  immunobiologic_id: string;
  type: string;
  name: string;
  display?: string;
  active?: boolean;
  monitored?: boolean;
  onboarding_status?: string;
  pni_codes?: string[];
  normative_acts?: string[];
  note?: string;
  active_rules: Array<{
    rule_id: string;
    rule_type: string;
    rule_context?: string;
    geographic_scope?: { type?: string; codes?: string[] };
    effective_from?: string | null;
    effective_until?: string | null;
  }>;
  draft_rules: Array<{
    rule_id: string;
    rule_type: string;
    rule_context?: string;
  }>;
  rule_readiness: "active" | "draft" | "none";
  data_mapping: "mapped" | "partial" | "pending";
};

export type ImmunobiologicCatalog = {
  generated_at: string;
  items: ImmunobiologicCatalogItem[];
};

export async function getImmunobiologicCatalog(): Promise<ImmunobiologicCatalog> {
  const root = path.join(process.cwd(), "..");
  const registryRaw = await readFile(
    path.join(root, "data", "reference", "immunobiologic_registry.json"),
    "utf-8",
  );
  const rulesRaw = await readFile(
    path.join(root, "data", "reference", "normative_rules.json"),
    "utf-8",
  );

  const registry = JSON.parse(registryRaw) as {
    immunobiologics: Array<Record<string, unknown>>;
  };
  const rulesPayload = JSON.parse(rulesRaw) as {
    rules: Array<Record<string, unknown>>;
  };

  const items: ImmunobiologicCatalogItem[] = registry.immunobiologics.map((raw) => {
    const immunobiologicId = String(raw.immunobiologic_id || "");
    const relatedRules = rulesPayload.rules.filter(
      (rule) =>
        String(rule.immunobiologic_id || rule.vaccine_id || "") === immunobiologicId,
    );
    const activeRules = relatedRules
      .filter((rule) => rule.status === "active")
      .map((rule) => ({
        rule_id: String(rule.rule_id || ""),
        rule_type: String(rule.rule_type || ""),
        rule_context: rule.rule_context ? String(rule.rule_context) : undefined,
        geographic_scope:
          rule.geographic_scope && typeof rule.geographic_scope === "object"
            ? (rule.geographic_scope as { type?: string; codes?: string[] })
            : undefined,
        effective_from: rule.effective_from ? String(rule.effective_from) : null,
        effective_until: rule.effective_until ? String(rule.effective_until) : null,
      }));
    const draftRules = relatedRules
      .filter((rule) => rule.status === "draft")
      .map((rule) => ({
        rule_id: String(rule.rule_id || ""),
        rule_type: String(rule.rule_type || ""),
        rule_context: rule.rule_context ? String(rule.rule_context) : undefined,
      }));

    const pniCodes = Array.isArray(raw.pni_codes)
      ? raw.pni_codes.map((x) => String(x))
      : [];
    const onboardingStatus = raw.onboarding_status
      ? String(raw.onboarding_status)
      : undefined;
    const monitored = Boolean(raw.monitored);

    const dataMapping: ImmunobiologicCatalogItem["data_mapping"] =
      pniCodes.length > 0 && monitored
        ? "mapped"
        : pniCodes.length > 0
          ? "partial"
          : "pending";

    return {
      immunobiologic_id: immunobiologicId,
      type: String(raw.type || ""),
      name: String(raw.name || immunobiologicId),
      display: raw.display ? String(raw.display) : undefined,
      active: Boolean(raw.active),
      monitored,
      onboarding_status: onboardingStatus,
      pni_codes: pniCodes,
      normative_acts: Array.isArray(raw.normative_acts)
        ? raw.normative_acts.map((x) => String(x))
        : [],
      note: raw.note ? String(raw.note) : undefined,
      active_rules: activeRules,
      draft_rules: draftRules,
      rule_readiness:
        activeRules.length > 0 ? "active" : draftRules.length > 0 ? "draft" : "none",
      data_mapping: dataMapping,
    };
  });

  return {
    generated_at: new Date().toISOString(),
    items: items.sort((a, b) =>
      (a.display || a.name).localeCompare(b.display || b.name, "pt-BR"),
    ),
  };
}
