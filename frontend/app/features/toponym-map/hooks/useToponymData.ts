import { useEffect, useMemo, useRef, useState } from "react";

import {
  fetchAreas,
  fetchCandidates,
  fetchElements,
  fetchMeta,
  fetchMonuments,
  fetchStats,
  fetchToponyms,
} from "~/lib/dataset/client";
import type {
  AreaFeature,
  ElementsFile,
  Meta,
  MonumentCollection,
  Stats,
  ToponymFeature,
} from "~/lib/dataset/schema";

export type DatasetState = {
  loading: boolean;
  error: string | null;
  toponyms: ToponymFeature[];
  /** 伝承碑は 1.6MB あるため、レイヤーを表示するまで読み込まない。 */
  monuments: MonumentCollection | null;
  elements: ElementsFile | null;
  stats: Stats | null;
  meta: Meta | null;
};

const initialState: DatasetState = {
  loading: true,
  error: null,
  toponyms: [],
  monuments: null,
  elements: null,
  stats: null,
  meta: null,
};

/** 地図が最初に必要とする静的データをまとめて読み込む。 */
export const useToponymData = (): DatasetState => {
  const [state, setState] = useState<DatasetState>(initialState);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [toponyms, elements, stats, meta] = await Promise.all([
          fetchToponyms(),
          fetchElements(),
          fetchStats(),
          fetchMeta(),
        ]);
        if (cancelled) return;
        setState({
          loading: false,
          error: null,
          toponyms: toponyms.features,
          monuments: null,
          elements,
          stats,
          meta,
        });
      } catch (error: unknown) {
        if (cancelled) return;
        setState({
          ...initialState,
          loading: false,
          error:
            error instanceof Error
              ? error.message
              : "データの読み込みに失敗しました",
        });
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
};

/**
 * 根拠レベル0の候補は件数が多いため、表示中の都道府県のぶんだけ読み込む。
 * 一度読んだ都道府県はメモリに残す。
 */
export const useCandidates = (
  prefCodes: string[],
  enabled: boolean,
): { candidates: ToponymFeature[] } => {
  const [byPref, setByPref] = useState<Record<string, ToponymFeature[]>>({});
  const inFlight = useRef<Set<string>>(new Set());

  const key = prefCodes.join(",");

  useEffect(() => {
    if (!enabled) return;
    const codes = key ? key.split(",") : [];
    const missing = codes.filter(
      (code) => byPref[code] === undefined && !inFlight.current.has(code),
    );
    if (missing.length === 0) return;
    for (const code of missing) inFlight.current.add(code);

    let cancelled = false;
    const load = async () => {
      const loaded: Record<string, ToponymFeature[]> = {};
      await Promise.all(
        missing.map(async (code) => {
          try {
            const collection = await fetchCandidates(code);
            loaded[code] = collection.features;
          } catch {
            // その都道府県に候補ファイルが無い場合は空として扱う
            loaded[code] = [];
          }
        }),
      );
      for (const code of missing) inFlight.current.delete(code);
      if (cancelled) return;
      setByPref((current) => ({ ...current, ...loaded }));
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [key, enabled, byPref]);

  const candidates = useMemo(() => {
    if (!enabled) return [];
    const codes = key ? key.split(",") : [];
    return codes.flatMap((code) => byPref[code] ?? []);
  }, [key, enabled, byPref]);

  return { candidates };
};

/** 伝承碑レイヤーを表示したときだけ読み込む。 */
export const useMonuments = (enabled: boolean): MonumentCollection | null => {
  const [monuments, setMonuments] = useState<MonumentCollection | null>(null);

  useEffect(() => {
    if (!enabled || monuments) return;
    let cancelled = false;
    const load = async () => {
      try {
        const collection = await fetchMonuments();
        if (!cancelled) setMonuments(collection);
      } catch {
        // 伝承碑レイヤーは補助情報なので、失敗しても地図は動かす
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [enabled, monuments]);

  return monuments;
};

/**
 * 地名がカバーする範囲（町丁・字等のポリゴン）を、表示中の都道府県だけ読み込む。
 * 点の位置は代表点にすぎないため、範囲を重ねると読み取れることが増える。
 */
export const useAreas = (
  prefCodes: string[],
  enabled: boolean,
): { areas: AreaFeature[] } => {
  const [byPref, setByPref] = useState<Record<string, AreaFeature[]>>({});
  const inFlight = useRef<Set<string>>(new Set());

  const key = prefCodes.join(",");

  useEffect(() => {
    if (!enabled) return;
    const codes = key ? key.split(",") : [];
    const missing = codes.filter(
      (code) => byPref[code] === undefined && !inFlight.current.has(code),
    );
    if (missing.length === 0) return;
    for (const code of missing) inFlight.current.add(code);

    let cancelled = false;
    const load = async () => {
      const loaded: Record<string, AreaFeature[]> = {};
      await Promise.all(
        missing.map(async (code) => {
          try {
            const collection = await fetchAreas(code);
            loaded[code] = collection.features;
          } catch {
            // その都道府県に範囲データが無い場合は空として扱う
            loaded[code] = [];
          }
        }),
      );
      for (const code of missing) inFlight.current.delete(code);
      if (cancelled) return;
      setByPref((current) => ({ ...current, ...loaded }));
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [key, enabled, byPref]);

  const areas = useMemo(() => {
    if (!enabled) return [];
    const codes = key ? key.split(",") : [];
    return codes.flatMap((code) => byPref[code] ?? []);
  }, [key, enabled, byPref]);

  return { areas };
};
