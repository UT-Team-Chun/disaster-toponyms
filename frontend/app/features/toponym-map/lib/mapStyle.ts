import type { StyleSpecification } from "maplibre-gl";

/** 背景地図の選択肢。すべて地理院タイル。 */
export type BaseMapId = "pale" | "std" | "relief" | "photo";

type BaseMapDefinition = {
  id: BaseMapId;
  label: string;
  url: string;
  attribution: string;
  maxzoom: number;
};

const GSI_ATTRIBUTION =
  '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noreferrer">地理院タイル</a>';

export const BASE_MAPS: BaseMapDefinition[] = [
  {
    id: "pale",
    label: "淡色地図",
    url: "https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png",
    attribution: GSI_ATTRIBUTION,
    maxzoom: 18,
  },
  {
    id: "std",
    label: "標準地図",
    url: "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
    attribution: GSI_ATTRIBUTION,
    maxzoom: 18,
  },
  {
    id: "relief",
    label: "陰影起伏図",
    url: "https://cyberjapandata.gsi.go.jp/xyz/hillshademap/{z}/{x}/{y}.png",
    attribution: GSI_ATTRIBUTION,
    maxzoom: 16,
  },
  {
    id: "photo",
    label: "航空写真",
    url: "https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg",
    attribution: GSI_ATTRIBUTION,
    maxzoom: 18,
  },
];

/** 重ねるハザードマップのオープンデータ配信タイル。 */
export type HazardLayerId =
  | "debris_flow"
  | "steep_slope"
  | "landslide"
  | "flood"
  | "tsunami"
  | "storm_surge";

type HazardLayerDefinition = {
  id: HazardLayerId;
  label: string;
  directory: string;
  minzoom: number;
};

const HAZARD_ATTRIBUTION =
  '<a href="https://disaportal.gsi.go.jp/hazardmap/copyright/opendata.html" target="_blank" rel="noreferrer">重ねるハザードマップ（国土交通省）</a>';

export const HAZARD_LAYERS: HazardLayerDefinition[] = [
  {
    id: "debris_flow",
    label: "土砂災害警戒区域（土石流）",
    directory: "05_dosekiryukeikaikuiki",
    minzoom: 2,
  },
  {
    id: "steep_slope",
    label: "土砂災害警戒区域（急傾斜地の崩壊）",
    directory: "05_kyukeishakeikaikuiki",
    minzoom: 2,
  },
  {
    id: "landslide",
    label: "土砂災害警戒区域（地すべり）",
    directory: "05_jisuberikeikaikuiki",
    minzoom: 2,
  },
  {
    id: "flood",
    label: "洪水浸水想定区域（想定最大規模）",
    directory: "01_flood_l2_shinsuishin_data",
    minzoom: 2,
  },
  {
    id: "tsunami",
    label: "津波浸水想定",
    directory: "04_tsunami_newlegend_data",
    minzoom: 2,
  },
  {
    id: "storm_surge",
    label: "高潮浸水想定区域",
    directory: "03_hightide_l2_shinsuishin_data",
    minzoom: 2,
  },
];

export const hazardSourceId = (id: HazardLayerId): string => `hazard-${id}`;
export const hazardLayerId = (id: HazardLayerId): string =>
  `hazard-layer-${id}`;

/** 空のスタイルから始めて、背景とハザードのラスタソースを組み立てる。 */
export const buildMapStyle = (baseMapId: BaseMapId): StyleSpecification => {
  const base = BASE_MAPS.find((item) => item.id === baseMapId) ?? BASE_MAPS[0];

  const style: StyleSpecification = {
    version: 8,
    sources: {
      base: {
        type: "raster",
        tiles: [base.url],
        tileSize: 256,
        maxzoom: base.maxzoom,
        attribution: base.attribution,
      },
    },
    layers: [
      {
        id: "background",
        type: "background",
        paint: { "background-color": "#eef1f5" },
      },
      {
        id: "base-layer",
        type: "raster",
        source: "base",
        paint: { "raster-opacity": 1 },
      },
    ],
  };

  for (const layer of HAZARD_LAYERS) {
    style.sources[hazardSourceId(layer.id)] = {
      type: "raster",
      tiles: [
        `https://disaportaldata.gsi.go.jp/raster/${layer.directory}/{z}/{x}/{y}.png`,
      ],
      tileSize: 256,
      minzoom: layer.minzoom,
      maxzoom: 17,
      attribution: HAZARD_ATTRIBUTION,
    };
    style.layers.push({
      id: hazardLayerId(layer.id),
      type: "raster",
      source: hazardSourceId(layer.id),
      layout: { visibility: "none" },
      paint: { "raster-opacity": 0.55 },
    });
  }

  return style;
};

/** 日本全体が入る初期表示。 */
export const INITIAL_VIEW = {
  center: [137.5, 37.0] as [number, number],
  zoom: 4.4,
  minZoom: 3.5,
  maxZoom: 17.5,
};

/** 地名がカバーする範囲（ポリゴン）を読み込み始めるズーム。点より重いので絞る。 */
export const AREA_MIN_ZOOM = 9;
