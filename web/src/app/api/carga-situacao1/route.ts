import { NextRequest, NextResponse } from "next/server";
import { writeFile, mkdir } from "fs/promises";
import path from "path";

const ALLOWED = new Set(["1", "2", "3", "4", "8", "12_dialise"]);

export async function POST(req: NextRequest) {
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
    const buf = Buffer.from(await file.arrayBuffer());
    const root = path.join(process.cwd(), "..");
    const dir = path.join(root, "data", "manual", "situacao1");
    await mkdir(dir, { recursive: true });
    const dest = path.join(dir, `${key}.csv`);
    await writeFile(dest, buf);
    return NextResponse.json({
      message: `Salvo em data/manual/situacao1/${key}.csv. Clique em Recalcular mart.`,
      path: dest,
    });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Erro no upload" },
      { status: 500 },
    );
  }
}
