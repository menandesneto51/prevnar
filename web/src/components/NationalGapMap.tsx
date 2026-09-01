"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { GapMapRow } from "@/components/GapChoroplethMap";
import { GAP_SCALE, fmtGapShort } from "@/lib/mapColors";
import type { MunResumo, UfResumo } from "@/lib/types";

const GapChoroplethMap = dynamic(() => import("@/components/GapChoroplethMap"), {
  ssr: false,
  loading: () => (
    <div className="map-canvas map-placeholder" role="status">
      Carregando mapa…
    </div>
  ),
});

type Props = {
  porUf: UfResumo[];
  porMunicipio?: MunResumo[];
  ufNomes?: Record<string, string>;
};

export function NationalGapMap({ porUf, porMunicipio = [], ufNomes = {} }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const ufFromUrl = (searchParams.get("uf") || "").toUpperCase();

  const [selectedUf, setSelectedUf] = useState<string | null>(
    ufFromUrl.length === 2 ? ufFromUrl : null,
  );
  const [selectedMun, setSelectedMun] = useState<{ code: string; name: string } | null>(
    null,
  );
  const [munCount, setMunCount] = useState<number | null>(null);

  const syncUrl = useCallback(
    (uf: string | null) => {
      const params = new URLSearchParams(searchParams.toString());
      if (uf) params.set("uf", uf);
      else params.delete("uf");
      const q = params.toString();
      router.replace(q ? `${pathname}?${q}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  useEffect(() => {
    if (ufFromUrl.length === 2 && ufFromUrl !== selectedUf) {
      setSelectedUf(ufFromUrl);
      setSelectedMun(null);
      setMunCount(null);
    }
  }, [ufFromUrl]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && selectedUf) {
        setSelectedUf(null);
        setSelectedMun(null);
        setMunCount(null);
        syncUrl(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selectedUf, syncUrl]);

  const ufRows: GapMapRow[] = useMemo(
    () =>
      porUf.map((u) => ({
        code: u.uf,
        name: ufNomes[u.uf] ?? u.uf,
        gap: u.gap,
        elegiveis: u.elegiveis,
        vacinados: u.pessoas_vacinadas_consolidado ?? u.pessoas_vacinadas,
      })),
    [porUf, ufNomes],
  );

  const munRows: GapMapRow[] = useMemo(() => {
    if (!selectedUf) return [];
    return porMunicipio
      .filter((m) => m.uf === selectedUf)
      .map((m) => ({
        code: m.municipio_ibge,
        name: m.nome || m.municipio_ibge,
        gap: null,
        vacinados: m.pessoas_vacinadas,
        doses: m.doses ?? m.pessoas_vacinadas,
      }));
  }, [porMunicipio, selectedUf]);

  const ufMap = useMemo(() => new Map(porUf.map((u) => [u.uf, u])), [porUf]);
  const active = selectedUf ? ufMap.get(selectedUf) : null;
  const munComDado = munRows.filter((m) => (m.vacinados ?? 0) > 0).length;

  const goBrasil = () => {
    setSelectedUf(null);
    setSelectedMun(null);
    setMunCount(null);
    syncUrl(null);
  };

  const goUf = (code: string) => {
    const uf = code.toUpperCase();
    setSelectedUf(uf);
    setSelectedMun(null);
    setMunCount(null);
    syncUrl(uf);
  };

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold">Mapa de oportunidade (gap)</h2>
          <p className="text-xs text-[var(--muted)]">
            {selectedUf
              ? `Municípios de ${selectedUf}${munCount != null ? ` · ${munCount.toLocaleString("pt-BR")} polígonos` : ""}${munComDado ? ` · ${munComDado} com vacinado` : ""} · Esc ou ← Brasil`
              : "Clique em uma UF para abrir os municípios"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {selectedUf ? (
            <button
              type="button"
              className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs hover:border-[var(--primary)]"
              onClick={goBrasil}
            >
              ← Brasil
            </button>
          ) : null}
          {selectedUf ? (
            <Link
              href={`/ufs/${selectedUf}`}
              className="rounded-lg bg-[var(--primary)] px-3 py-1.5 text-xs font-semibold text-white"
            >
              Ficha {selectedUf}
            </Link>
          ) : null}
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_220px]">
        <div className="min-h-[360px] p-2 sm:p-3">
          {selectedUf ? (
            <GapChoroplethMap
              level="municipio"
              uf={selectedUf}
              rows={munRows}
              metric="vacinados"
              selectedCode={selectedMun?.code}
              onSelect={(code, name) => setSelectedMun({ code, name })}
              onBack={goBrasil}
              onLayerReady={({ featureCount }) => setMunCount(featureCount)}
            />
          ) : (
            <GapChoroplethMap
              level="uf"
              rows={ufRows}
              metric="gap"
              selectedCode={undefined}
              onSelect={(code) => goUf(code)}
            />
          )}
        </div>

        <aside className="map-legend border-t border-[var(--border)] p-4 lg:border-l lg:border-t-0">
          <div className="mb-3 text-[10px] uppercase tracking-wider text-[var(--muted)]">
            {selectedUf ? "Legenda (vacinados no município)" : "Legenda (gap relativo UF)"}
          </div>
          <ul className="mb-4 space-y-1.5">
            {selectedUf ? (
              <>
                <li className="flex items-center gap-2 text-xs">
                  <span className="inline-block h-2.5 w-5 rounded-sm bg-[#d5dde8]" /> Sem vacinado
                </li>
                {GAP_SCALE.slice(1).map((item) => (
                  <li key={item.color} className="flex items-center gap-2 text-xs">
                    <span
                      className="inline-block h-2.5 w-5 rounded-sm"
                      style={{ background: item.color }}
                    />
                    {item.label}
                  </li>
                ))}
              </>
            ) : (
              GAP_SCALE.slice(1).map((item) => (
                <li key={item.color} className="flex items-center gap-2 text-xs">
                  <span
                    className="inline-block h-2.5 w-5 rounded-sm"
                    style={{ background: item.color }}
                  />
                  {item.label}
                </li>
              ))
            )}
          </ul>

          {active ? (
            <div className="space-y-2 text-sm">
              <div className="font-semibold">
                {ufNomes[active.uf] ?? active.uf} ({active.uf})
              </div>
              <div className="text-xs text-[var(--muted)]">Elegíveis (UF)</div>
              <div className="kpi-value text-lg">{active.elegiveis.toLocaleString("pt-BR")}</div>
              <div className="text-xs text-[var(--muted)]">Vacinados (UF)</div>
              <div className="kpi-value text-lg text-[var(--accent)]">
                {(active.pessoas_vacinadas_consolidado ?? active.pessoas_vacinadas).toLocaleString(
                  "pt-BR",
                )}
              </div>
              <div className="text-xs text-[var(--muted)]">Gap (UF)</div>
              <div className="kpi-value text-lg text-[var(--warn)]">
                {fmtGapShort(active.gap)}
              </div>
              {selectedMun ? (
                <div className="mt-3 rounded-lg border border-[var(--border)] p-2 text-xs">
                  <div className="font-medium">{selectedMun.name}</div>
                  <div className="mt-1 text-[var(--muted)]">
                    IBGE {selectedMun.code}.{" "}
                    {(() => {
                      const row = munRows.find(
                        (m) =>
                          m.code === selectedMun.code ||
                          m.code === selectedMun.code.slice(0, 6) ||
                          selectedMun.code.startsWith(m.code),
                      );
                      const v = row?.vacinados ?? 0;
                      return v > 0
                        ? `${v.toLocaleString("pt-BR")} pessoa(s) vacinada(s) VPC20 na amostra.`
                        : "Sem vacinado VPC20 na amostra atual.";
                    })()}
                  </div>
                </div>
              ) : (
                <p className="mt-3 text-[11px] leading-relaxed text-[var(--muted)]">
                  Cor do município = vacinados VPC20 (numerador). Cinza = zero na amostra. Gap
                  absoluto continua só no nível UF (sem denominador municipal).
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs leading-relaxed text-[var(--muted)]">
              Coroplético UF por gap. No drill municipal, a cor muda por vacinados (não herda mais o
              gap da UF).
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}
