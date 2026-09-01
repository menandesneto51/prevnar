import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const maxDuration = 120;

export async function POST() {
  const root = path.join(process.cwd(), "..");
  const py = path.join(root, ".venv", "Scripts", "python.exe");
  const script = path.join(root, "etl", "build_mart.py");

  return new Promise<NextResponse>((resolve) => {
    const child = spawn(py, [script], {
      cwd: path.join(root, "etl"),
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => {
      stdout += d.toString();
    });
    child.stderr.on("data", (d) => {
      stderr += d.toString();
    });
    child.on("close", (code) => {
      if (code !== 0) {
        resolve(
          NextResponse.json(
            { error: stderr || stdout || `exit ${code}` },
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
      resolve(NextResponse.json({ error: err.message }, { status: 500 }));
    });
  });
}
