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
