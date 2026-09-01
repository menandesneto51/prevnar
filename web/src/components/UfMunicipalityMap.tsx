"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useMemo, useState } from "react";

import type { GapMapRow } from "@/components/GapChoroplethMap";
import type { MunResumo } from "@/lib/types";

const GapChoroplethMap = dynamic(() => import("@/components/GapChoroplethMap"), {
  ssr: false,
  loading: () => (
    <div className="map-canvas map-placeholder" role="status">
      Carregando mapa…
    </div>
  ),
});

type Props = {
  uf: string;
  nome: string;
  parentGap: number;
  municipios?: MunResumo[];
};

export function UfMunicipalityMap({ uf, nome, parentGap, municipios = [] }: Props) {
  const [selected, setSelected] = useState<{ code: string; name: string } | null>(null);
  const [count, setCount] = useState<number | null>(null);

  const rows: GapMapRow[] = useMemo(
    () =>
      municipios
        .filter((m) => m.uf === uf)
        .map((m) => ({
          code: m.municipio_ibge,
          name: m.nome || m.municipio_ibge,
          gap: null,
          vacinados: m.pessoas_vacinadas,
          doses: m.doses ?? m.pessoas_vacinadas,
        })),
    [municipios, uf],
  );
  const comDado = rows.filter((r) => (r.vacinados ?? 0) > 0).length;

  return (
    <div className="card overflow-hidden p-3">
      <div className="mb-2 flex flex-wrap items-end justify-between gap-2 px-1">
        <div>
          <h2 className="text-sm font-semibold">Municípios — {nome}</h2>
          <p className="text-xs text-[var(--muted)]">
            Cor = vacinados VPC20
            {count != null ? ` · ${count.toLocaleString("pt-BR")} polígonos` : ""}
            {comDado ? ` · ${comDado} com vacinado` : ""}. Gap absoluto só no nível UF.
          </p>
        </div>
        <Link href={`/?uf=${uf}`} className="text-xs text-[var(--primary)] hover:underline">
          Abrir no mapa nacional
        </Link>
      </div>
      <GapChoroplethMap
        level="municipio"
        uf={uf}
        rows={rows}
        metric="vacinados"
        parentGap={parentGap}
        selectedCode={selected?.code}
        onSelect={(code, name) => setSelected({ code, name })}
        onLayerReady={({ featureCount }) => setCount(featureCount)}
      />
      {selected ? (
        <div className="mt-2 rounded-lg border border-[var(--border)] px-3 py-2 text-xs">
          <strong>{selected.name}</strong> · IBGE {selected.code}
          {(() => {
            const row = rows.find(
              (m) =>
                m.code === selected.code ||
                m.code === selected.code.slice(0, 6) ||
                selected.code.startsWith(m.code),
            );
            const v = row?.vacinados ?? 0;
            return v > 0
              ? ` · ${v.toLocaleString("pt-BR")} vacinado(s)`
              : " · sem vacinado na amostra";
          })()}
        </div>
      ) : null}
    </div>
  );
}
