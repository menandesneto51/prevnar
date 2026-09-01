import type { DashboardData, GapLinha } from "./types";
import { readFile } from "fs/promises";
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
