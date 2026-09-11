import { z } from "zod";

/**
 * 警鐘地名データセットのスキーマ。
 * backend/packages/alg/alg/models/toponym.py と対応させる。
 */

export const hazardTypeSchema = z.enum([
  "landslide",
  "debris_flow",
  "rockfall",
  "slope_failure",
  "flood",
  "inundation",
  "tsunami",
  "storm_surge",
  "soft_ground",
  "avalanche",
  "erosion",
  "volcanic",
  "earthquake",
  "wind",
  "other",
]);
export type HazardType = z.infer<typeof hazardTypeSchema>;

export const toponymStatusSchema = z.enum(["current", "historical", "renamed"]);
export type ToponymStatus = z.infer<typeof toponymStatusSchema>;

export const locationPrecisionSchema = z.enum([
  "point",
  "koaza",
  "oaza",
  "village",
  "feature",
  "municipality",
  "prefecture",
  "unknown",
]);

/** 記録された災害と地名の関係。 */
export const disasterRelationSchema = z.enum([
  "named_after",
  "same_place_record",
  "nearby_record",
]);
export type DisasterRelation = z.infer<typeof disasterRelationSchema>;
export type LocationPrecision = z.infer<typeof locationPrecisionSchema>;

/** 地図のピンが持つ軽量プロパティ。詳細は details/{id}.json から取得する。 */
export const toponymPropertiesSchema = z.object({
  id: z.string(),
  name: z.string(),
  reading: z.string().nullable().optional(),
  pref: z.string().nullable().optional(),
  prefCode: z.string().nullable().optional(),
  municipality: z.string().nullable().optional(),
  hazardTypes: z.array(hazardTypeSchema).default([]),
  evidenceLevel: z.number().int().min(0).max(3),
  /** 出典が地名の由来について述べている強さ。災害記録との対応は含まない。 */
  originLevel: z.number().int().min(0).max(2).default(0),
  /** この場所で起きた災害の記録があるか。根拠レベルとは別の軸。 */
  hasRecord: z.boolean().default(false),
  recordRelation: disasterRelationSchema.nullable().optional(),
  status: toponymStatusSchema,
  disputed: z.boolean().default(false),
  precision: locationPrecisionSchema,
  elements: z.array(z.string()).default([]),
  summary: z.string().default(""),
  zones: z.array(z.string()).default([]),
  dataset: z.string().default(""),
  /** この地名が属する町丁・字等の e-Stat KEY_CODE。範囲ポリゴンとの対応に使う。 */
  areaKey: z.string().nullable().optional(),
});
export type ToponymProperties = z.infer<typeof toponymPropertiesSchema>;

const pointGeometrySchema = z.object({
  type: z.literal("Point"),
  coordinates: z.tuple([z.number(), z.number()]),
});

export const toponymFeatureSchema = z.object({
  type: z.literal("Feature"),
  geometry: pointGeometrySchema,
  properties: toponymPropertiesSchema,
});
export type ToponymFeature = z.infer<typeof toponymFeatureSchema>;

export const toponymCollectionSchema = z.object({
  type: z.literal("FeatureCollection"),
  features: z.array(toponymFeatureSchema),
});
export type ToponymCollection = z.infer<typeof toponymCollectionSchema>;

const polygonGeometrySchema = z.object({
  type: z.literal("Polygon"),
  coordinates: z.array(z.array(z.tuple([z.number(), z.number()]))),
});

/** 地名がカバーする範囲（国勢調査の町丁・字等）。 */
export const areaPropertiesSchema = z.object({
  key: z.string(),
  name: z.string(),
  pref: z.string().nullable().optional(),
  prefCode: z.string().nullable().optional(),
  municipality: z.string().nullable().optional(),
  areaM2: z.number().nullable().optional(),
  population: z.number().nullable().optional(),
  toponymIds: z.array(z.string()).default([]),
});
export type AreaProperties = z.infer<typeof areaPropertiesSchema>;

export const areaFeatureSchema = z.object({
  type: z.literal("Feature"),
  geometry: polygonGeometrySchema,
  properties: areaPropertiesSchema,
});
export type AreaFeature = z.infer<typeof areaFeatureSchema>;

export const areaCollectionSchema = z.object({
  type: z.literal("FeatureCollection"),
  features: z.array(areaFeatureSchema),
});
export type AreaCollection = z.infer<typeof areaCollectionSchema>;

export const monumentPropertiesSchema = z.object({
  id: z.string(),
  name: z.string(),
  erectedYear: z.string().nullable().optional(),
  address: z.string().nullable().optional(),
  disasterName: z.string().nullable().optional(),
  disasterKind: z.string().nullable().optional(),
  lore: z.string().nullable().optional(),
});
export type MonumentProperties = z.infer<typeof monumentPropertiesSchema>;

export const monumentCollectionSchema = z.object({
  type: z.literal("FeatureCollection"),
  features: z.array(
    z.object({
      type: z.literal("Feature"),
      geometry: pointGeometrySchema,
      properties: monumentPropertiesSchema,
    }),
  ),
});
export type MonumentCollection = z.infer<typeof monumentCollectionSchema>;

export const evidenceSchema = z.object({
  kind: z.string(),
  stance: z.enum(["supports", "disputes"]).default("supports"),
  source_id: z.string(),
  locator: z.string().nullable().optional(),
  quote: z.string().nullable().optional(),
  claim: z.string(),
  level: z.number().int().min(0).max(3),
  extracted_by: z.string().default("human"),
  quote_verified: z.boolean().default(false),
  /** 引用を突き合わせた相手。ocr は原本の版面ではなく OCR テキストとの一致。 */
  quote_medium: z.enum(["text", "ocr"]).default("text"),
});
export type Evidence = z.infer<typeof evidenceSchema>;

/** その場所で実際に起きたと記録されている災害。 */
export const disasterRecordSchema = z.object({
  relation: disasterRelationSchema,
  name: z.string(),
  date_text: z.string().nullable().optional(),
  hazard_types: z.array(hazardTypeSchema).default([]),
  source_id: z.string().nullable().optional(),
  locator: z.string().nullable().optional(),
  quote: z.string().nullable().optional(),
  quote_verified: z.boolean().default(false),
  quote_medium: z.enum(["text", "ocr"]).default("text"),
  match_method: z
    .enum(["entry_text", "monument_place_name", "distance", "curated"])
    .default("curated"),
  distance_km: z.number().nullable().optional(),
  extracted_by: z.string().default("human"),
});
export type DisasterRecord = z.infer<typeof disasterRecordSchema>;

export const toponymDetailSchema = z.object({
  id: z.string(),
  name: z.string(),
  reading: z.string().nullable().optional(),
  variants: z.array(z.string()).default([]),
  status: toponymStatusSchema,
  renamed_to: z.string().nullable().optional(),
  admin: z.object({
    pref: z.string().nullable().optional(),
    pref_code: z.string().nullable().optional(),
    municipality: z.string().nullable().optional(),
    oaza: z.string().nullable().optional(),
    koaza: z.string().nullable().optional(),
    province: z.string().nullable().optional(),
    district: z.string().nullable().optional(),
    historical_village: z.string().nullable().optional(),
  }),
  location: z
    .object({
      lat: z.number(),
      lon: z.number(),
      precision: locationPrecisionSchema,
      geocode_source: z.string().nullable().optional(),
    })
    .nullable()
    .optional(),
  area_key: z.string().nullable().optional(),
  hazard_types: z.array(hazardTypeSchema).default([]),
  hazardLabels: z.array(z.string()).default([]),
  elements: z
    .array(
      z.object({
        element_id: z.string(),
        surface: z.string(),
        reading: z.string().nullable().optional(),
        meaning: z.string().nullable().optional(),
      }),
    )
    .default([]),
  etymology_summary: z.string().default(""),
  evidence: z.array(evidenceSchema).default([]),
  disaster_records: z.array(disasterRecordSchema).default([]),
  origin_level: z.number().int().min(0).max(2).default(0),
  evidence_level: z.number().int().min(0).max(3),
  evidenceLevelLabel: z.string().default(""),
  disputed: z.boolean().default(false),
  dispute_note: z.string().nullable().optional(),
  hazard_corroboration: z.object({
    debris_flow_zone: z.boolean().nullable().optional(),
    steep_slope_zone: z.boolean().nullable().optional(),
    landslide_zone: z.boolean().nullable().optional(),
    flood_zone: z.boolean().nullable().optional(),
    tsunami_zone: z.boolean().nullable().optional(),
    storm_surge_zone: z.boolean().nullable().optional(),
    avalanche_risk: z.boolean().nullable().optional(),
    nearest_monument_ids: z.array(z.string()).default([]),
    sampled_at: z.string().nullable().optional(),
  }),
  review: z.object({
    status: z.enum(["auto", "reviewed", "rejected"]).default("auto"),
    reviewer: z.string().nullable().optional(),
    note: z.string().nullable().optional(),
  }),
  dataset: z.string().default(""),
});
export type ToponymDetail = z.infer<typeof toponymDetailSchema>;

export const elementSchema = z.object({
  id: z.string(),
  label: z.string(),
  surfaces: z.array(z.string()).default([]),
  readings: z.array(z.string()).default([]),
  meaning: z.string(),
  hazard_types: z.array(hazardTypeSchema).default([]),
  specificity: z.number(),
  substitution_of: z.string().nullable().optional(),
  source_ids: z.array(z.string()).default([]),
  note: z.string().nullable().optional(),
});
export type ToponymElement = z.infer<typeof elementSchema>;

export const elementsFileSchema = z.object({
  elements: z.array(elementSchema),
  hazardLabels: z.record(z.string(), z.string()),
  evidenceLevelLabels: z.record(z.string(), z.string()),
});
export type ElementsFile = z.infer<typeof elementsFileSchema>;

export const sourceSchema = z.object({
  id: z.string(),
  type: z.string(),
  title: z.string(),
  author: z.string().nullable().optional(),
  year: z.number().nullable().optional(),
  publisher: z.string().nullable().optional(),
  url: z.string().nullable().optional(),
  doi: z.string().nullable().optional(),
  license: z.string().nullable().optional(),
  accessed: z.string().nullable().optional(),
  note: z.string().nullable().optional(),
});
export type Source = z.infer<typeof sourceSchema>;

export const sourcesFileSchema = z.object({ sources: z.array(sourceSchema) });

export const statsSchema = z.object({
  toponymsTotal: z.number(),
  candidatesTotal: z.number(),
  monumentsTotal: z.number(),
  disputedTotal: z.number(),
  byLevel: z.record(z.string(), z.number()),
  byHazard: z.record(z.string(), z.number()),
  byPrefecture: z.record(
    z.string(),
    z.object({
      total: z.number(),
      documented: z.number(),
      level3: z.number().default(0),
    }),
  ),
  byElement: z.record(z.string(), z.number()),
  candidatesByPrefecture: z.record(z.string(), z.number()),
  areasTotal: z.number().default(0),
  areasByPrefecture: z.record(z.string(), z.number()).default({}),
  withAreaTotal: z.number().default(0),
  withDisasterRecord: z.number().default(0),
  candidatesWithRecord: z.number().default(0),
  l3ByRelation: z.record(z.string(), z.number()).default({}),
});
export type Stats = z.infer<typeof statsSchema>;

export const metaSchema = z.object({
  builtAt: z.string(),
  datasets: z.array(z.string()).default([]),
  attribution: z.array(z.string()).default([]),
});
export type Meta = z.infer<typeof metaSchema>;
