import "server-only";

import { existsSync } from "fs";
import path from "path";

export function resolveRepoRoot(): string {
  const cwd = process.cwd();
  return path.basename(cwd).toLowerCase() === "web" ? path.dirname(cwd) : cwd;
}

export function resolvePythonExecutable(repoRoot: string): string {
  const configured = (process.env.PREVNAR_PYTHON || "").trim();
  if (configured) return configured;

  const candidates = [
    path.join(repoRoot, ".venv", "Scripts", "python.exe"),
    path.join(repoRoot, ".venv", "bin", "python"),
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate)) return candidate;
  }

  // Fallback para PATH do sistema; erro de spawn será devolvido pela rota.
  return process.platform === "win32" ? "python" : "python3";
}
