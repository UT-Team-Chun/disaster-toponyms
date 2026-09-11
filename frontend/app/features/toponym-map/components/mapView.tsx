import maplibregl, {
  type GeoJSONSource,
  type LngLatLike,
  type MapGeoJSONFeature,
  type MapMouseEvent,
  type RasterTileSource,
} from "maplibre-gl";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  BASE_MAPS,
  buildMapStyle,
  hazardLayerId,
  HAZARD_LAYERS,
  INITIAL_VIEW,
  type BaseMapId,
  type HazardLayerId,
} from "~/features/toponym-map/lib/mapStyle";
import { hazardColor } from "~/lib/dataset/labels";
import type {
  AreaFeature,
  MonumentCollection,
  ToponymFeature,
} from "~/lib/dataset/schema";

const TOPONYM_SOURCE = "toponyms";
const CANDIDATE_SOURCE = "candidates";
const MONUMENT_SOURCE = "monuments";
const TOPONYM_LAYER = "toponyms-circle";
const TOPONYM_SELECTED_LAYER = "toponyms-selected";
const TOPONYM_DISPUTED_LAYER = "toponyms-disputed";
const CANDIDATE_LAYER = "candidates-circle";
const MONUMENT_LAYER = "monuments-circle";
const AREA_SOURCE = "areas";
const AREA_FILL_LAYER = "areas-fill";
const AREA_LINE_LAYER = "areas-line";
const AREA_SELECTED_LAYER = "areas-selected";
const NO_SELECTION = "__none__";

const emptyCollection = { type: "FeatureCollection", features: [] } as const;

type Props = {
  toponyms: ToponymFeature[];
  candidates: ToponymFeature[];
  areas: AreaFeature[];
  monuments: MonumentCollection | null;
  selectedId: string | null;
  selectedAreaKey: string | null;
  showAreas: boolean;
  baseMap: BaseMapId;
  hazardLayers: HazardLayerId[];
  showMonuments: boolean;
  onSelect: (id: string | null) => void;
  onViewChange: (
    zoom: number,
    bounds: [number, number, number, number],
  ) => void;
  onMapReady: (map: maplibregl.Map) => void;
};

/** 描画用に色と半径を付けた GeoJSON へ変換する。 */
const toRenderCollection = (features: ToponymFeature[]) => ({
  type: "FeatureCollection" as const,
  features: features.map((feature) => ({
    ...feature,
    properties: {
      ...feature.properties,
      color: hazardColor(feature.properties.hazardTypes),
      // 根拠が強いものほど大きく描く
      radius: 3.5 + feature.properties.evidenceLevel * 1.6,
    },
  })),
});

const escapeHtml = (value: string): string =>
  value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

export function MapView(props: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const readyRef = useRef(false);
  // レイヤー追加は load 後なので、それを待って各 effect を再実行させる
  const [ready, setReady] = useState(false);
  const onSelectRef = useRef(props.onSelect);
  const onViewChangeRef = useRef(props.onViewChange);
  const onMapReadyRef = useRef(props.onMapReady);

  // 地図インスタンスは一度だけ作るため、コールバックは ref 越しに最新を渡す
  useEffect(() => {
    onSelectRef.current = props.onSelect;
    onViewChangeRef.current = props.onViewChange;
    onMapReadyRef.current = props.onMapReady;
  });

  const toponymData = useMemo(
    () => toRenderCollection(props.toponyms),
    [props.toponyms],
  );
  const candidateData = useMemo(
    () => toRenderCollection(props.candidates),
    [props.candidates],
  );
  const areaData = useMemo(
    () => ({ type: "FeatureCollection" as const, features: props.areas }),
    [props.areas],
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container || mapRef.current) return;

    const map = new maplibregl.Map({
      container,
      style: buildMapStyle("pale"),
      center: INITIAL_VIEW.center,
      zoom: INITIAL_VIEW.zoom,
      minZoom: INITIAL_VIEW.minZoom,
      maxZoom: INITIAL_VIEW.maxZoom,
      attributionControl: false,
    });
    mapRef.current = map;

    map.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      "top-right",
    );
    map.addControl(
      new maplibregl.AttributionControl({ compact: true }),
      "bottom-right",
    );
    map.addControl(
      new maplibregl.ScaleControl({ unit: "metric" }),
      "bottom-left",
    );

    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 12,
      maxWidth: "260px",
    });

    const reportView = () => {
      const bounds = map.getBounds();
      onViewChangeRef.current(map.getZoom(), [
        bounds.getWest(),
        bounds.getSouth(),
        bounds.getEast(),
        bounds.getNorth(),
      ]);
    };

    map.on("load", () => {
      map.addSource(TOPONYM_SOURCE, { type: "geojson", data: emptyCollection });
      map.addSource(CANDIDATE_SOURCE, {
        type: "geojson",
        data: emptyCollection,
      });
      map.addSource(MONUMENT_SOURCE, {
        type: "geojson",
        data: emptyCollection,
      });

      map.addSource(AREA_SOURCE, { type: "geojson", data: emptyCollection });

      map.addLayer({
        id: AREA_FILL_LAYER,
        type: "fill",
        source: AREA_SOURCE,
        layout: { visibility: "none" },
        paint: { "fill-color": "#1f2937", "fill-opacity": 0.07 },
      });

      map.addLayer({
        id: AREA_LINE_LAYER,
        type: "line",
        source: AREA_SOURCE,
        layout: { visibility: "none" },
        paint: {
          "line-color": "#334155",
          "line-width": 0.8,
          "line-opacity": 0.5,
        },
      });

      map.addLayer({
        id: AREA_SELECTED_LAYER,
        type: "fill",
        source: AREA_SOURCE,
        filter: ["==", ["get", "key"], NO_SELECTION],
        paint: {
          "fill-color": "#b45309",
          "fill-opacity": 0.22,
          "fill-outline-color": "#7c2d12",
        },
      });

      map.addLayer({
        id: CANDIDATE_LAYER,
        type: "circle",
        source: CANDIDATE_SOURCE,
        paint: {
          "circle-radius": 3,
          "circle-color": "#ffffff",
          "circle-opacity": 0.55,
          "circle-stroke-width": 1,
          "circle-stroke-color": ["get", "color"],
          "circle-stroke-opacity": 0.85,
        },
      });

      map.addLayer({
        id: MONUMENT_LAYER,
        type: "circle",
        source: MONUMENT_SOURCE,
        layout: { visibility: "none" },
        paint: {
          "circle-radius": 4,
          "circle-color": "#1f2937",
          "circle-opacity": 0.75,
          "circle-stroke-width": 1.2,
          "circle-stroke-color": "#f8fafc",
        },
      });

      map.addLayer({
        id: TOPONYM_LAYER,
        type: "circle",
        source: TOPONYM_SOURCE,
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            4,
            ["*", ["get", "radius"], 0.7],
            10,
            ["get", "radius"],
            15,
            ["*", ["get", "radius"], 1.8],
          ],
          "circle-color": ["get", "color"],
          "circle-opacity": 0.85,
          "circle-stroke-width": 1.2,
          "circle-stroke-color": "#ffffff",
        },
      });

      map.addLayer({
        id: TOPONYM_DISPUTED_LAYER,
        type: "circle",
        source: TOPONYM_SOURCE,
        filter: ["==", ["get", "disputed"], true],
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            4,
            ["+", ["*", ["get", "radius"], 0.7], 3],
            15,
            ["+", ["*", ["get", "radius"], 1.8], 4],
          ],
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-width": 1.4,
          "circle-stroke-color": "#dc2626",
          "circle-stroke-opacity": 0.9,
        },
      });

      map.addLayer({
        id: TOPONYM_SELECTED_LAYER,
        type: "circle",
        source: TOPONYM_SOURCE,
        filter: ["==", ["get", "id"], NO_SELECTION],
        paint: {
          "circle-radius": 15,
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-width": 3,
          "circle-stroke-color": "#111827",
        },
      });

      readyRef.current = true;
      setReady(true);
      onMapReadyRef.current(map);
      reportView();
    });

    const showPopup = (
      event: MapMouseEvent & { features?: MapGeoJSONFeature[] },
    ) => {
      const feature = event.features?.[0];
      if (!feature) return;
      map.getCanvas().style.cursor = "pointer";
      const properties = feature.properties as Record<string, unknown>;
      const name = escapeHtml(String(properties.name ?? ""));
      const reading = properties.reading
        ? escapeHtml(String(properties.reading))
        : "";
      const place = escapeHtml(
        [properties.pref, properties.municipality].filter(Boolean).join(""),
      );
      const level = Number(properties.evidenceLevel ?? 0);
      popup
        .setLngLat(event.lngLat as LngLatLike)
        .setHTML(
          `<div style="font-size:12px;line-height:1.6">` +
            `<div style="font-weight:600;font-size:13px">${name}` +
            (reading
              ? `<span style="margin-left:4px;font-weight:400;opacity:.7">${reading}</span>`
              : "") +
            `</div><div style="opacity:.8">${place}</div>` +
            `<div style="opacity:.8">根拠レベル ${level}</div></div>`,
        )
        .addTo(map);
    };

    const hidePopup = () => {
      map.getCanvas().style.cursor = "";
      popup.remove();
    };

    const handleClick = (
      event: MapMouseEvent & { features?: MapGeoJSONFeature[] },
    ) => {
      const feature = event.features?.[0];
      if (!feature) return;
      const id = (feature.properties as Record<string, unknown>).id;
      if (typeof id === "string") onSelectRef.current(id);
    };

    for (const layer of [TOPONYM_LAYER, CANDIDATE_LAYER]) {
      map.on("mousemove", layer, showPopup);
      map.on("mouseleave", layer, hidePopup);
      map.on("click", layer, handleClick);
    }

    map.on("click", (event) => {
      const layers = [TOPONYM_LAYER, CANDIDATE_LAYER].filter((id) =>
        map.getLayer(id),
      );
      if (layers.length === 0) return;
      if (map.queryRenderedFeatures(event.point, { layers }).length === 0) {
        onSelectRef.current(null);
      }
    });

    map.on("moveend", reportView);

    return () => {
      popup.remove();
      map.remove();
      mapRef.current = null;
      readyRef.current = false;
      setReady(false);
    };
  }, []);

  // 背景地図はスタイルを作り直さず、ラスタソースのタイルURLだけ差し替える
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    const definition =
      BASE_MAPS.find((item) => item.id === props.baseMap) ?? BASE_MAPS[0];
    const source = map.getSource("base") as RasterTileSource | undefined;
    source?.setTiles([definition.url]);
  }, [props.baseMap, ready]);

  useEffect(() => {
    const map = mapRef.current;
    const source = map?.getSource(TOPONYM_SOURCE) as GeoJSONSource | undefined;
    source?.setData(toponymData as never);
  }, [toponymData, ready]);

  useEffect(() => {
    const map = mapRef.current;
    const source = map?.getSource(CANDIDATE_SOURCE) as
      | GeoJSONSource
      | undefined;
    source?.setData(candidateData as never);
  }, [candidateData, ready]);

  useEffect(() => {
    const map = mapRef.current;
    const source = map?.getSource(MONUMENT_SOURCE) as GeoJSONSource | undefined;
    if (props.monuments) source?.setData(props.monuments as never);
  }, [props.monuments, ready]);

  useEffect(() => {
    const map = mapRef.current;
    const source = map?.getSource(AREA_SOURCE) as GeoJSONSource | undefined;
    source?.setData(areaData as never);
  }, [areaData, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.getLayer(AREA_FILL_LAYER)) return;
    const visibility = props.showAreas ? "visible" : "none";
    map.setLayoutProperty(AREA_FILL_LAYER, "visibility", visibility);
    map.setLayoutProperty(AREA_LINE_LAYER, "visibility", visibility);
  }, [props.showAreas, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.getLayer(AREA_SELECTED_LAYER)) return;
    map.setFilter(AREA_SELECTED_LAYER, [
      "==",
      ["get", "key"],
      props.selectedAreaKey ?? NO_SELECTION,
    ]);
  }, [props.selectedAreaKey, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.getLayer(MONUMENT_LAYER)) return;
    map.setLayoutProperty(
      MONUMENT_LAYER,
      "visibility",
      props.showMonuments ? "visible" : "none",
    );
  }, [props.showMonuments, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    for (const layer of HAZARD_LAYERS) {
      const id = hazardLayerId(layer.id);
      if (!map.getLayer(id)) continue;
      map.setLayoutProperty(
        id,
        "visibility",
        props.hazardLayers.includes(layer.id) ? "visible" : "none",
      );
    }
  }, [props.hazardLayers, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.getLayer(TOPONYM_SELECTED_LAYER)) return;
    map.setFilter(TOPONYM_SELECTED_LAYER, [
      "==",
      ["get", "id"],
      props.selectedId ?? NO_SELECTION,
    ]);
  }, [props.selectedId, ready]);

  // maplibre-gl.css はレイヤー外のため .maplibregl-map の position が Tailwind の
  // ユーティリティに勝ってしまう。位置と大きさはインラインスタイルで確定させる。
  return (
    <div
      ref={containerRef}
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
    />
  );
}
