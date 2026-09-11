import { basePath } from "~/env";
import {
  areaCollectionSchema,
  elementsFileSchema,
  metaSchema,
  monumentCollectionSchema,
  sourcesFileSchema,
  statsSchema,
  toponymCollectionSchema,
  toponymDetailSchema,
  type AreaCollection,
  type ElementsFile,
  type Meta,
  type MonumentCollection,
  type Source,
  type Stats,
  type ToponymCollection,
  type ToponymDetail,
} from "~/lib/dataset/schema";

/**
 * ビルド時に backend が frontend/public/data へ書き出した静的ファイルを読む。
 * Backend API ではなく自サイトの静的アセットなので Orval は介さない。
 */

const dataUrl = (path: string): string => {
  const base = basePath.endsWith("/") ? basePath : `${basePath}/`;
  return `${base}data/${path}`;
};

const cache = new Map<string, Promise<unknown>>();

const fetchJson = (path: string): Promise<unknown> => {
  const cached = cache.get(path);
  if (cached) return cached;

  const pending = fetch(dataUrl(path)).then(async (response) => {
    if (!response.ok) {
      throw new Error(
        `データを読み込めませんでした: ${path} (${response.status})`,
      );
    }
    return (await response.json()) as unknown;
  });
  cache.set(path, pending);
  return pending.catch((error: unknown) => {
    cache.delete(path);
    throw error;
  });
};

export const fetchToponyms = async (): Promise<ToponymCollection> =>
  toponymCollectionSchema.parse(await fetchJson("toponyms.geojson"));

export const fetchCandidates = async (
  prefCode: string,
): Promise<ToponymCollection> =>
  toponymCollectionSchema.parse(
    await fetchJson(`candidates/${prefCode}.geojson`),
  );

export const fetchAreas = async (prefCode: string): Promise<AreaCollection> =>
  areaCollectionSchema.parse(await fetchJson(`areas/${prefCode}.geojson`));

export const fetchMonuments = async (): Promise<MonumentCollection> =>
  monumentCollectionSchema.parse(await fetchJson("monuments.geojson"));

export const fetchToponymDetail = async (id: string): Promise<ToponymDetail> =>
  toponymDetailSchema.parse(await fetchJson(`details/${id}.json`));

export const fetchElements = async (): Promise<ElementsFile> =>
  elementsFileSchema.parse(await fetchJson("elements.json"));

export const fetchSources = async (): Promise<Source[]> =>
  sourcesFileSchema.parse(await fetchJson("sources.json")).sources;

export const fetchStats = async (): Promise<Stats> =>
  statsSchema.parse(await fetchJson("stats.json"));

export const fetchMeta = async (): Promise<Meta> =>
  metaSchema.parse(await fetchJson("meta.json"));
