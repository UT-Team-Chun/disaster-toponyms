import type {
  HazardType,
  LocationPrecision,
  ToponymStatus,
} from "~/lib/dataset/schema";

/** 災害種別の日本語ラベル。backend の HAZARD_LABELS_JA と対応。 */
export const HAZARD_LABELS: Record<HazardType, string> = {
  landslide: "地すべり",
  debris_flow: "土石流",
  rockfall: "落石",
  slope_failure: "崖崩れ・斜面崩壊",
  flood: "洪水・河川氾濫",
  inundation: "浸水・内水・低湿",
  tsunami: "津波",
  storm_surge: "高潮",
  soft_ground: "軟弱地盤・液状化",
  avalanche: "雪崩",
  erosion: "侵食",
  volcanic: "火山",
  earthquake: "地震",
  wind: "強風",
  other: "その他",
};

/** 地図で色分けする際の主要災害種別の並び順。 */
export const HAZARD_ORDER: HazardType[] = [
  "debris_flow",
  "slope_failure",
  "landslide",
  "rockfall",
  "avalanche",
  "flood",
  "inundation",
  "tsunami",
  "storm_surge",
  "soft_ground",
  "erosion",
  "volcanic",
  "earthquake",
  "wind",
  "other",
];

/** 災害種別ごとの色。地形災害は暖色、水災害は寒色で系統を分ける。 */
export const HAZARD_COLORS: Record<HazardType, string> = {
  debris_flow: "#b45309",
  slope_failure: "#c2410c",
  landslide: "#a16207",
  rockfall: "#78350f",
  avalanche: "#7c3aed",
  flood: "#1d4ed8",
  inundation: "#0369a1",
  tsunami: "#0f766e",
  storm_surge: "#0e7490",
  soft_ground: "#4d7c0f",
  erosion: "#9a3412",
  volcanic: "#be123c",
  earthquake: "#9f1239",
  wind: "#525252",
  other: "#525252",
};

export const EVIDENCE_LEVEL_LABELS: Record<number, string> = {
  0: "字面のみ（候補）",
  1: "地形由来の記載あり",
  2: "災害由来・替字の明記",
  3: "災害記録・伝承との対応",
};

export const EVIDENCE_LEVEL_DESCRIPTIONS: Record<number, string> = {
  0: "要素辞書に表記が一致するだけの候補。出典による裏づけは未確認。",
  1: "地名辞典や地誌が地形（崖・窪地・低湿地など）由来と記載している。",
  2: "地方史・地名考・自治体資料などが災害由来、または替字であることを明記している。",
  3: "年号を伴う実際の災害、伝承碑、口承と結びついている。",
};

export const STATUS_LABELS: Record<ToponymStatus, string> = {
  current: "現存",
  historical: "旧地名（小字など）",
  renamed: "改称",
};

export const PRECISION_LABELS: Record<LocationPrecision, string> = {
  point: "地点",
  koaza: "小字",
  oaza: "大字・町丁目",
  municipality: "市区町村",
  prefecture: "都道府県",
  unknown: "不明",
};

/** ハザード区域フラグの日本語ラベル。 */
export const ZONE_LABELS: Record<string, string> = {
  debris_flow_zone: "土砂災害警戒区域（土石流）",
  steep_slope_zone: "土砂災害警戒区域（急傾斜地の崩壊）",
  landslide_zone: "土砂災害警戒区域（地すべり）",
  flood_zone: "洪水浸水想定区域",
  tsunami_zone: "津波浸水想定",
  storm_surge_zone: "高潮浸水想定区域",
  avalanche_risk: "雪崩危険箇所",
};

export const EVIDENCE_KIND_LABELS: Record<string, string> = {
  pattern: "表記の一致",
  gazetteer: "地名辞典",
  local_history: "地方史・地名考",
  legend: "伝承",
  academic: "学術文献",
  official: "自治体・官公庁資料",
  news: "報道",
  monument: "伝承碑",
  manual: "人手調査",
};

/** 都道府県コードと名称。 */
export const PREFECTURES: { code: string; name: string }[] = [
  { code: "01", name: "北海道" },
  { code: "02", name: "青森県" },
  { code: "03", name: "岩手県" },
  { code: "04", name: "宮城県" },
  { code: "05", name: "秋田県" },
  { code: "06", name: "山形県" },
  { code: "07", name: "福島県" },
  { code: "08", name: "茨城県" },
  { code: "09", name: "栃木県" },
  { code: "10", name: "群馬県" },
  { code: "11", name: "埼玉県" },
  { code: "12", name: "千葉県" },
  { code: "13", name: "東京都" },
  { code: "14", name: "神奈川県" },
  { code: "15", name: "新潟県" },
  { code: "16", name: "富山県" },
  { code: "17", name: "石川県" },
  { code: "18", name: "福井県" },
  { code: "19", name: "山梨県" },
  { code: "20", name: "長野県" },
  { code: "21", name: "岐阜県" },
  { code: "22", name: "静岡県" },
  { code: "23", name: "愛知県" },
  { code: "24", name: "三重県" },
  { code: "25", name: "滋賀県" },
  { code: "26", name: "京都府" },
  { code: "27", name: "大阪府" },
  { code: "28", name: "兵庫県" },
  { code: "29", name: "奈良県" },
  { code: "30", name: "和歌山県" },
  { code: "31", name: "鳥取県" },
  { code: "32", name: "島根県" },
  { code: "33", name: "岡山県" },
  { code: "34", name: "広島県" },
  { code: "35", name: "山口県" },
  { code: "36", name: "徳島県" },
  { code: "37", name: "香川県" },
  { code: "38", name: "愛媛県" },
  { code: "39", name: "高知県" },
  { code: "40", name: "福岡県" },
  { code: "41", name: "佐賀県" },
  { code: "42", name: "長崎県" },
  { code: "43", name: "熊本県" },
  { code: "44", name: "大分県" },
  { code: "45", name: "宮崎県" },
  { code: "46", name: "鹿児島県" },
  { code: "47", name: "沖縄県" },
];

/** 地図で色を決めるための主要災害種別を選ぶ。 */
export const primaryHazard = (hazardTypes: HazardType[]): HazardType => {
  for (const hazard of HAZARD_ORDER) {
    if (hazardTypes.includes(hazard)) return hazard;
  }
  return "other";
};

export const hazardColor = (hazardTypes: HazardType[]): string =>
  HAZARD_COLORS[primaryHazard(hazardTypes)];
