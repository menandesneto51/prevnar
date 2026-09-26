import { spawn } from "child_process";
import path from "path";
import { NextRequest, NextResponse } from "next/server";

import { resolvePythonExecutable, resolveRepoRoot } from "@/lib/serverRuntime";
import { authorizeMutableRequest } from "@/lib/serverSecurity";

export const maxDuration = 120;

const MAX_LOG_CHARS = 100_000;

function boundedAppend(current: string, chunk: unknown): string {
  const next = current + String(chunk);
  return next.length > MAX_LOG_CHARS ? next.slice(-MAX_LOG_CHARS) : next;
}

export async function POST(req: NextRequest) {
  const denied = authorizeMutableRequest(req);
  if (denied) return denied;

  const root = resolveRepoRoot();
  const py = resolvePythonExecutable(root);
  const script = path.join(root, "etl", "build_mart.py");

  return new Promise<NextResponse>((resolve) => {
    const child = spawn(py, [script], {
      cwd: path.join(root, "etl"),
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      shell: false,
    });

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => {
      stdout = boundedAppend(stdout, d);
    });
    child.stderr.on("data", (d) => {
      stderr = boundedAppend(stderr, d);
    });

    child.on("close", (code) => {
      if (code !== 0) {
        resolve(
          NextResponse.json(
            {
              error: "Falha ao recalcular o mart.",
              detail: (stderr || stdout || `exit ${code}`).slice(-2000),
            },
            { status: 500 },
          ),
        );
        return;
      }
      resolve(
        NextResponse.json({
          message: "Mart recalculado. Recarregue as páginas do painel.",
          log: stdout.slice(-2000),
        }),
      );
    });

    child.on("error", (err) => {
      resolve(
        NextResponse.json(
          { error: "Falha ao iniciar o ETL.", detail: err.message },
          { status: 500 },
        ),
      );
    });
  });
}
