"use client";

import { useState } from "react";

const FILES = [
  { key: "1", label: "HIV/AIDS — SICLOM" },
  { key: "2", label: "Oncológicos — SIA/APAC" },
  { key: "3", label: "Transplantes órgãos sólidos — ABTO" },
  { key: "4", label: "TCTH — ABTO" },
  { key: "8", label: "Fibrose cística — REBRAFC" },
  { key: "12_dialise", label: "Diálise crônica — SBN (overlay)" },
];

export default function CargaPage() {
  const [status, setStatus] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function onUpload(key: string, file: File | null) {
    if (!file) return;
    setBusy(true);
    setStatus(`Enviando ${file.name}…`);
    try {
      const fd = new FormData();
      fd.append("key", key);
      fd.append("file", file);
      const res = await fetch("/api/carga-situacao1", { method: "POST", body: fd });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "Falha no upload");
      setStatus(json.message || "OK. Rode o ETL para recalcular o mart.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Erro");
    } finally {
      setBusy(false);
    }
  }

  async function rebuild() {
    setBusy(true);
    setStatus("Recalculando mart…");
    try {
      const res = await fetch("/api/rebuild-mart", { method: "POST" });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || "Falha");
      setStatus(json.message || "Mart atualizado. Recarregue as páginas.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Erro");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Carga Situação 1</h1>
        <p className="mt-1 max-w-2xl text-sm text-[var(--muted)]">
          Envie CSVs com colunas <code className="text-[var(--accent)]">uf,elegiveis</code>. Os
          arquivos ficam em <code>data/manual/situacao1/</code>. Há seed provisório (27 UFs) para
          HIV, oncológicos, transplante, TCTH, fibrose e diálise — substitua pelos extratos oficiais
          e clique em recalcular o mart (ou rode{" "}
          <code>.venv\Scripts\python etl\build_mart.py</code>).
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {FILES.map((f) => (
          <label key={f.key} className="card flex cursor-pointer flex-col gap-2 p-4 hover:border-[var(--accent)]">
            <div className="text-sm font-medium">{f.label}</div>
            <div className="text-xs text-[var(--muted)]">Arquivo: {f.key}.csv</div>
            <input
              type="file"
              accept=".csv,text/csv"
              disabled={busy}
              className="text-xs file:mr-3 file:rounded-md file:border-0 file:bg-[var(--accent)] file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-[var(--navy-950)]"
              onChange={(e) => onUpload(f.key, e.target.files?.[0] ?? null)}
            />
          </label>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={busy}
          onClick={rebuild}
          className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-[var(--navy-950)] disabled:opacity-50"
        >
          Recalcular mart
        </button>
        <a
          href="/templates/situacao1_template.csv"
          className="text-sm text-[var(--accent)] hover:underline"
        >
          Baixar template CSV
        </a>
      </div>

      {status ? <div className="card p-4 text-sm">{status}</div> : null}
    </div>
  );
}
