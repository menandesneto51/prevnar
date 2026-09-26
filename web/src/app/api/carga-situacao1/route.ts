import { mkdir, rename, writeFile } from "fs/promises";
import path from "path";
import { NextRequest, NextResponse } from "next/server";

import { resolveRepoRoot } from "@/lib/serverRuntime";
import { authorizeMutableRequest } from "@/lib/serverSecurity";

const ALLOWED = new Set(["1", "2", "3", "4", "8", "12_dialise"]);
const VALID_UFS = new Set([
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
  "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
  "SP", "SE", "TO",
]);
const MAX_UPLOAD_BYTES = 2 * 1024 * 1024;
const MAX_ROWS = 10_000;

function validateCsv(text: string): string | null {
  if (text.includes("\0")) return "Arquivo contém bytes inválidos.";

  const lines = text
    .replace(/^\uFEFF/, "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) return "CSV sem linhas de dados.";
  if (lines.length - 1 > MAX_ROWS) return `CSV excede ${MAX_ROWS} linhas.`;

  const header = lines[0].split(",").map((v) => v.trim().toLowerCase());
  const ufIndex = header.indexOf("uf");
  const elegIndex = header.indexOf("elegiveis");
  if (ufIndex < 0 || elegIndex < 0) {
    return "Cabeçalho inválido. Esperado CSV com colunas uf,elegiveis.";
  }

  const seen = new Set<string>();
  for (let i = 1; i < lines.length; i += 1) {
    const cols = lines[i].split(",").map((v) => v.trim());
    const uf = (cols[ufIndex] || "").toUpperCase();
    const elegiveis = cols[elegIndex] || "";

    if (!VALID_UFS.has(uf)) return `UF inválida na linha ${i + 1}: ${uf || "vazia"}.`;
    if (seen.has(uf)) return `UF duplicada na linha ${i + 1}: ${uf}.`;
    seen.add(uf);

    if (!/^\d+$/.test(elegiveis)) {
      return `Elegíveis deve ser inteiro não negativo na linha ${i + 1}.`;
    }
    const value = Number(elegiveis);
    if (!Number.isSafeInteger(value) || value < 0) {
      return `Valor de elegíveis inválido na linha ${i + 1}.`;
    }
  }
  return null;
}

export async function POST(req: NextRequest) {
  const denied = authorizeMutableRequest(req);
  if (denied) return denied;

  try {
    const form = await req.formData();
    const key = String(form.get("key") || "");
    const file = form.get("file");

    if (!ALLOWED.has(key)) {
      return NextResponse.json({ error: "Chave inválida" }, { status: 400 });
    }
    if (!(file instanceof File)) {
      return NextResponse.json({ error: "Arquivo ausente" }, { status: 400 });
    }
    if (!file.name.toLowerCase().endsWith(".csv")) {
      return NextResponse.json({ error: "Somente arquivos CSV são aceitos." }, { status: 400 });
    }
    if (file.size <= 0 || file.size > MAX_UPLOAD_BYTES) {
      return NextResponse.json(
        { error: `Tamanho inválido. Limite: ${MAX_UPLOAD_BYTES / 1024 / 1024} MB.` },
        { status: 400 },
      );
    }

    const buf = Buffer.from(await file.arrayBuffer());
    const text = buf.toString("utf-8");
    const validationError = validateCsv(text);
    if (validationError) {
      return NextResponse.json({ error: validationError }, { status: 400 });
    }

    const root = resolveRepoRoot();
    const dir = path.join(root, "data", "manual", "situacao1");
    await mkdir(dir, { recursive: true });

    const dest = path.join(dir, `${key}.csv`);
    const temp = path.join(dir, `.${key}.${process.pid}.tmp`);
    await writeFile(temp, buf, { flag: "w" });
    await rename(temp, dest);

    return NextResponse.json({
      message: `Carga validada e salva como data/manual/situacao1/${key}.csv. Recalcule o mart.`,
      rows: text.replace(/^\uFEFF/, "").split(/\r?\n/).filter((line) => line.trim()).length - 1,
    });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erro no upload" },
      { status: 500 },
    );
  }
}
