"use client";

export function PrintButton() {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className="rounded-md bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white"
    >
      Imprimir / PDF
    </button>
  );
}
