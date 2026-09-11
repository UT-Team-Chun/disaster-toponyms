import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router";

import {
  filtersFromSearchParams,
  filtersToSearchParams,
  type Filters,
} from "~/lib/dataset/filtering";
import type {
  BaseMapId,
  HazardLayerId,
} from "~/features/toponym-map/lib/mapStyle";

export type ViewState = {
  filters: Filters;
  selectedId: string | null;
  baseMap: BaseMapId;
  hazardLayers: HazardLayerId[];
  showCandidates: boolean;
  showMonuments: boolean;
  showAreas: boolean;
};

const BASE_MAP_IDS: BaseMapId[] = ["pale", "std", "relief", "photo"];

const parseBaseMap = (value: string | null): BaseMapId =>
  BASE_MAP_IDS.includes(value as BaseMapId) ? (value as BaseMapId) : "pale";

const splitParam = (value: string | null): string[] =>
  value ? value.split(",").filter((part) => part.length > 0) : [];

/**
 * 絞り込みと表示状態を URL のクエリに保存する。
 * 共有したリンクを開くと同じ画面が再現される。
 */
export const useViewState = (): {
  view: ViewState;
  setFilters: (next: Filters) => void;
  setSelectedId: (id: string | null) => void;
  setBaseMap: (id: BaseMapId) => void;
  setHazardLayers: (ids: HazardLayerId[]) => void;
  setShowCandidates: (value: boolean) => void;
  setShowMonuments: (value: boolean) => void;
  setShowAreas: (value: boolean) => void;
  reset: () => void;
} => {
  const [searchParams, setSearchParams] = useSearchParams();

  const view = useMemo<ViewState>(
    () => ({
      filters: filtersFromSearchParams(searchParams),
      selectedId: searchParams.get("sel"),
      baseMap: parseBaseMap(searchParams.get("base")),
      hazardLayers: splitParam(searchParams.get("hazard")) as HazardLayerId[],
      // 候補と範囲は既定で表示する（全国を見渡せるようにするため）
      showCandidates: searchParams.get("cand") !== "0",
      showMonuments: searchParams.get("mon") === "1",
      showAreas: searchParams.get("area") !== "0",
    }),
    [searchParams],
  );

  const write = useCallback(
    (next: Partial<ViewState>) => {
      const merged: ViewState = { ...view, ...next };
      const params = filtersToSearchParams(merged.filters, {
        sel: merged.selectedId ?? undefined,
        base: merged.baseMap === "pale" ? undefined : merged.baseMap,
        hazard: merged.hazardLayers.length
          ? merged.hazardLayers.join(",")
          : undefined,
        cand: merged.showCandidates ? undefined : "0",
        mon: merged.showMonuments ? "1" : undefined,
        area: merged.showAreas ? undefined : "0",
      });
      setSearchParams(params, { replace: true, preventScrollReset: true });
    },
    [view, setSearchParams],
  );

  return {
    view,
    setFilters: useCallback((filters: Filters) => write({ filters }), [write]),
    setSelectedId: useCallback(
      (selectedId: string | null) => write({ selectedId }),
      [write],
    ),
    setBaseMap: useCallback(
      (baseMap: BaseMapId) => write({ baseMap }),
      [write],
    ),
    setHazardLayers: useCallback(
      (hazardLayers: HazardLayerId[]) => write({ hazardLayers }),
      [write],
    ),
    setShowCandidates: useCallback(
      (showCandidates: boolean) => write({ showCandidates }),
      [write],
    ),
    setShowMonuments: useCallback(
      (showMonuments: boolean) => write({ showMonuments }),
      [write],
    ),
    setShowAreas: useCallback(
      (showAreas: boolean) => write({ showAreas }),
      [write],
    ),
    reset: useCallback(() => {
      setSearchParams(new URLSearchParams(), {
        replace: true,
        preventScrollReset: true,
      });
    }, [setSearchParams]),
  };
};
