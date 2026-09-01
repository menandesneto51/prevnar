"use client";

import type { Feature, FeatureCollection, GeoJsonObject, Geometry } from "geojson";
import L from "leaflet";
import type { Layer, PathOptions } from "leaflet";
import { useEffect, useMemo, useRef, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";

import "leaflet/dist/leaflet.css";

import { fmtGapShort, gapFill } from "@/lib/mapColors";

export type GapMapRow = {
  code: string;
  name?: string;
  gap: number | null;
  elegiveis?: number | null;
  vacinados?: number | null;
  doses?: number | null;
};

type Props = {
  level: "uf" | "municipio" | "regiao";
  uf?: string;
  rows: GapMapRow[];
  selectedCode?: string;
  onSelect?: (code: string, name: string) => void;
  onBack?: () => void;
  parentGap?: number | null;
  onLayerReady?: (info: { featureCount: number; level: string }) => void;
  showTiles?: boolean;
  /** Municipal choropleth: vacinados (default) | gap | doses */
  metric?: "vacinados" | "gap" | "doses";
};

const STROKE = "#ffffff";
const STROKE_MUN = "#e8eef5";
const STROKE_SEL = "#252f49";
const FETCH_TIMEOUT_MS = 20_000;

function FitBounds({
  data,
  maxZoom,
}: {
  data: FeatureCollection;
  maxZoom: number;
}) {
  const map = useMap();
  useEffect(() => {
    if (!data.features.length) return;
    const layer = L.geoJSON(data as GeoJsonObject);
    const bounds = layer.getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [20, 20], maxZoom });
    }
    const t = window.setTimeout(() => map.invalidateSize({ animate: false }), 80);
    return () => window.clearTimeout(t);
  }, [data, map, maxZoom]);
  return null;
}

/** Same pattern as VSR NationalUfMap — Leaflet often mounts at 0 size. */
function InvalidateSizeWhenVisible() {
  const map = useMap();
  useEffect(() => {
    const container = map.getContainer();
    const refresh = () => map.invalidateSize({ animate: false });
    const timers = [50, 250, 600].map((ms) => window.setTimeout(refresh, ms));
    const ro =
      typeof ResizeObserver !== "undefined" ? new ResizeObserver(() => refresh()) : null;
    ro?.observe(container);
    if (container.parentElement) ro?.observe(container.parentElement);

    let node: HTMLElement | null = container;
    const hiddenParents: HTMLElement[] = [];
    while (node) {
      if (node.hasAttribute("hidden") || node.getAttribute("data-active") === "false") {
        hiddenParents.push(node);
      }
      node = node.parentElement;
    }
    const mo =
      typeof MutationObserver !== "undefined"
        ? new MutationObserver(() => refresh())
        : null;
    for (const parent of hiddenParents) {
      mo?.observe(parent, {
        attributes: true,
        attributeFilter: ["hidden", "data-active", "style", "class"],
      });
    }
    const onVis = () => {
      if (document.visibilityState === "visible") refresh();
    };
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("resize", refresh);
    return () => {
      timers.forEach(clearTimeout);
      ro?.disconnect();
      mo?.disconnect();
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("resize", refresh);
    };
  }, [map]);
  return null;
}

type FeatProps = {
  code: string;
  name: string;
  gap: number | null;
  elegiveis: number | null;
  vacinados: number | null;
  doses: number | null;
  hasMetric: boolean;
};

function featureCode(level: Props["level"], p: Record<string, unknown> | null): string {
  if (level === "uf") return String(p?.uf ?? "").toUpperCase();
  if (level === "regiao") {
    return String(p?.name ?? p?.regiao ?? p?.NM_REGIAO ?? "").toUpperCase();
  }
  return String(p?.municipality_code ?? p?.CD_MUN ?? "");
}

function featureName(level: Props["level"], p: Record<string, unknown> | null, code: string): string {
  if (level === "uf") return String(p?.name ?? code);
  if (level === "regiao") return String(p?.name ?? p?.regiao ?? code);
  return String(p?.municipality_name ?? p?.NM_MUN ?? code);
}

async function fetchGeoJson(
  url: string,
  signal: AbortSignal,
): Promise<FeatureCollection> {
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as FeatureCollection;
}

export default function GapChoroplethMap({
  level,
  uf,
  rows,
  selectedCode,
  onSelect,
  onBack,
  parentGap = null,
  onLayerReady,
  showTiles = true,
  metric = "vacinados",
}: Props) {
  const [mounted, setMounted] = useState(false);
  const [baseGeo, setBaseGeo] = useState<FeatureCollection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const geoLayerRef = useRef<L.GeoJSON | null>(null);
  const onReadyRef = useRef(onLayerReady);
  onReadyRef.current = onLayerReady;

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    setBaseGeo(null);
    setError(null);
    setLoading(true);

    if (level === "municipio" && (!uf || uf.length !== 2)) {
      setError("UF inválida para malha municipal.");
      setLoading(false);
      window.clearTimeout(timer);
      return;
    }

    (async () => {
      try {
        let payload: FeatureCollection;
        if (level === "uf") {
          try {
            payload = await fetchGeoJson("/geo/br-uf-2024.geojson", controller.signal);
          } catch {
            payload = await fetchGeoJson(
              "/geo/br-uf-simplified.geojson",
              controller.signal,
            );
          }
        } else if (level === "regiao") {
          payload = await fetchGeoJson("/geo/br-regioes-2024.geojson", controller.signal);
        } else {
          payload = await fetchGeoJson(
            `/geo/municipios/${uf!.toUpperCase()}.geojson`,
            controller.signal,
          );
        }

        if (controller.signal.aborted) return;
        if (!payload.features?.length) {
          setError("Malha vazia.");
        } else {
          setBaseGeo(payload);
          onReadyRef.current?.({ featureCount: payload.features.length, level });
        }
        setLoading(false);
      } catch (err) {
        if (controller.signal.aborted) return;
        const aborted =
          (err instanceof DOMException && err.name === "AbortError") ||
          (err instanceof Error && /abort/i.test(err.message));
        setError(
          aborted
            ? `Timeout ao carregar a malha${uf ? ` de ${uf}` : ""}.`
            : err instanceof Error
              ? err.message
              : "Falha ao carregar GeoJSON.",
        );
        setLoading(false);
      } finally {
        window.clearTimeout(timer);
      }
    })();

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [level, uf]);

  const byCode = useMemo(() => {
    const m = new Map<string, GapMapRow>();
    for (const r of rows) {
      const raw = String(r.code || "").replace(/\D/g, "");
      if (!raw) continue;
      m.set(raw, r);
      m.set(raw.toUpperCase(), r);
      // API 6 dígitos ↔ malha 7 dígitos
      if (raw.length === 7) m.set(raw.slice(0, 6), r);
      if (raw.length === 6) m.set(raw, r);
    }
    return m;
  }, [rows]);

  const maxMetric = useMemo(() => {
    if (level === "municipio" && metric !== "gap") {
      const vals = rows
        .map((r) => (metric === "doses" ? r.doses : r.vacinados) ?? 0)
        .filter((g) => g > 0);
      return vals.length ? Math.max(...vals) : 1;
    }
    const vals = rows.map((r) => r.gap ?? 0).filter((g) => g > 0);
    if (vals.length) return Math.max(...vals);
    return parentGap && parentGap > 0 ? parentGap : 1;
  }, [rows, parentGap, level, metric]);

  const lookupMun = (code: string): GapMapRow | undefined => {
    const digits = code.replace(/\D/g, "");
    return (
      byCode.get(digits) ||
      byCode.get(digits.slice(0, 6)) ||
      (digits.length === 6 ? byCode.get(digits) : undefined)
    );
  };

  const data = useMemo(() => {
    if (!baseGeo) return null;
    return {
      type: "FeatureCollection" as const,
      features: baseGeo.features.map((feature) => {
        const p = feature.properties as Record<string, unknown> | null;
        const code = featureCode(level, p);
        const name = featureName(level, p, code);
        const stats =
          level === "municipio"
            ? lookupMun(code)
            : byCode.get(code.toUpperCase()) || byCode.get(code);
        const hasMetric = Boolean(
          stats &&
            (level === "municipio"
              ? (stats.vacinados != null && stats.vacinados > 0) ||
                (stats.doses != null && stats.doses > 0) ||
                (stats.gap != null && metric === "gap")
              : stats.gap != null),
        );
        const gap =
          level === "municipio"
            ? hasMetric
              ? stats!.gap
              : null
            : stats?.gap ?? null;
        return {
          ...feature,
          properties: {
            code,
            name,
            gap,
            elegiveis: stats?.elegiveis ?? null,
            vacinados: stats?.vacinados ?? (level === "municipio" ? 0 : null),
            doses: stats?.doses ?? null,
            hasMetric,
          } satisfies FeatProps,
        };
      }),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [baseGeo, byCode, level, metric]);

  const styleFn = useMemo(
    () => (feature?: Feature<Geometry, FeatProps>) => {
      const props = feature?.properties;
      const selected = Boolean(props?.code && selectedCode && props.code === selectedCode);
      let fill: string;
      if (level === "municipio") {
        const value =
          metric === "doses"
            ? props?.doses ?? 0
            : metric === "gap"
              ? props?.gap ?? 0
              : props?.vacinados ?? 0;
        const has = (value ?? 0) > 0;
        fill = has ? gapFill(value, maxMetric) : "#d5dde8";
      } else {
        fill = gapFill(props?.gap ?? null, maxMetric);
      }
      return {
        fillColor: fill,
        weight: selected ? 2.6 : level === "municipio" ? 0.5 : 1,
        opacity: 1,
        color: selected ? STROKE_SEL : level === "municipio" ? STROKE_MUN : STROKE,
        fillOpacity: level === "municipio" && !(props?.vacinados || props?.doses) ? 0.35 : 0.78,
      } satisfies PathOptions;
    },
    [selectedCode, maxMetric, level, metric],
  );

  // Keep selection highlight in sync without remounting the whole layer (VSR remounts via key).
  useEffect(() => {
    const layer = geoLayerRef.current;
    if (!layer) return;
    layer.eachLayer((child) => {
      const feat = (child as L.Path & { feature?: Feature<Geometry, FeatProps> }).feature;
      if (feat) (child as L.Path).setStyle(styleFn(feat));
    });
  }, [styleFn, selectedCode]);

  const onEachFeature = (feature: Feature<Geometry, FeatProps>, layer: Layer) => {
    const props = feature.properties;
    if (!props) return;
    const path = layer as L.Path;
    path.options.className = "map-poly";
    const vac = props.vacinados ?? 0;
    const gapLabel =
      level === "municipio"
        ? vac > 0
          ? `${vac.toLocaleString("pt-BR")} vacinado(s)`
          : "sem vacinado VPC20 na amostra"
        : props.gap == null
          ? "—"
          : fmtGapShort(props.gap);
    layer.bindTooltip(
      `<strong>${level === "uf" ? props.code + " — " : ""}${props.name}</strong>` +
        (level === "municipio" ? `<br/>IBGE ${props.code}` : "") +
        `<br/>${level === "municipio" ? gapLabel : `Gap ${gapLabel}`}` +
        (level === "uf" && props.vacinados != null
          ? `<br/>Vacinados ${props.vacinados.toLocaleString("pt-BR")}`
          : "") +
        (level === "uf" ? "<br/><em>Clique para municípios</em>" : ""),
      { sticky: true },
    );
    layer.on({
      click: (e) => {
        L.DomEvent.stopPropagation(e);
        onSelect?.(props.code, props.name);
      },
      mouseover: (e) => {
        const target = e.target as L.Path;
        target.setStyle({ weight: 2.2, color: STROKE_SEL });
        try {
          target.bringToFront();
        } catch {
          /* ignore */
        }
      },
      mouseout: (e) => {
        (e.target as L.Path).setStyle(styleFn(feature));
      },
    });
  };

  if (!mounted) {
    return (
      <div className="map-canvas map-placeholder" role="status">
        Carregando mapa…
      </div>
    );
  }

  if (loading && !baseGeo) {
    return (
      <div className="map-canvas map-placeholder" role="status">
        {level === "municipio"
          ? `Carregando municípios de ${uf ?? "…"}…`
          : level === "regiao"
            ? "Carregando regiões…"
            : "Carregando mapa…"}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="map-canvas map-placeholder text-[var(--danger)]" role="alert">
        {error ?? "Mapa indisponível"}
        {onBack ? (
          <button type="button" className="ml-2 underline" onClick={onBack}>
            Voltar
          </button>
        ) : null}
      </div>
    );
  }

  const mapKey = `${level}-${(uf || "br").toUpperCase()}`;
  const fitMaxZoom = level === "municipio" ? 11 : level === "regiao" ? 5 : 6;

  return (
    <div className="map-shell">
      {onBack ? (
        <button type="button" className="map-back-btn" onClick={onBack}>
          ← Brasil (UFs)
        </button>
      ) : null}
      <MapContainer
        key={mapKey}
        center={[-14.2, -51.9]}
        zoom={4}
        minZoom={3}
        maxZoom={12}
        scrollWheelZoom
        className="map-canvas"
        style={{ background: "#dfe7f2", zIndex: 0 }}
        attributionControl={showTiles}
      >
        {showTiles ? (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        ) : null}
        <InvalidateSizeWhenVisible />
        <FitBounds data={data} maxZoom={fitMaxZoom} />
        <GeoJSON
          key={`${mapKey}-layer-${data.features.length}-${maxMetric}-${metric}`}
          data={data as GeoJsonObject}
          style={styleFn}
          onEachFeature={onEachFeature}
          eventHandlers={{
            add: (e) => {
              geoLayerRef.current = e.target as L.GeoJSON;
            },
          }}
        />
      </MapContainer>
    </div>
  );
}
