import type maplibregl from "maplibre-gl";
import { ListFilter, PanelLeftClose, PanelLeftOpen, Rows3 } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { BottomSheet } from "~/components/ui/bottomSheet";
import { Button } from "~/components/ui/button";
import { SiteHeader } from "~/components/ui/siteHeader";
import { DetailPanel } from "~/features/toponym-map/components/detailPanel";
import { FilterPanel } from "~/features/toponym-map/components/filterPanel";
import { MapView } from "~/features/toponym-map/components/mapView";
import { ResultList } from "~/features/toponym-map/components/resultList";
import { useViewState } from "~/features/toponym-map/hooks/useFilters";
import {
  useIsDesktop,
  useIsWide,
} from "~/features/toponym-map/hooks/useMediaQuery";
import {
  useAreas,
  useCandidates,
  useMonuments,
  useToponymData,
} from "~/features/toponym-map/hooks/useToponymData";
import { AREA_MIN_ZOOM } from "~/features/toponym-map/lib/mapStyle";
import { fetchSources } from "~/lib/dataset/client";
import { applyFilters } from "~/lib/dataset/filtering";
import type { Source, ToponymFeature } from "~/lib/dataset/schema";

/** 狭い画面で開いているシート。詳細が選ばれているときは詳細が優先される。 */
type Sheet = "filters" | "list" | null;

/**
 * 表示範囲に重なる都道府県コードを、読み込み済みの地点の分布から求める。
 * 候補は全国にあるため、範囲ポリゴンの読み込み対象を絞るのに使える。
 */
const prefCodesInBounds = (
  features: ToponymFeature[],
  bounds: [number, number, number, number] | null,
): string[] => {
  if (!bounds) return [];
  const [west, south, east, north] = bounds;
  const codes = new Set<string>();
  for (const feature of features) {
    const [lon, lat] = feature.geometry.coordinates;
    if (lon >= west && lon <= east && lat >= south && lat <= north) {
      if (feature.properties.prefCode) codes.add(feature.properties.prefCode);
    }
  }
  return [...codes].sort();
};

export function ToponymMap() {
  const data = useToponymData();
  const isDesktop = useIsDesktop();
  const isWide = useIsWide();
  const {
    view,
    setFilters,
    setSelectedId,
    setBaseMap,
    setHazardLayers,
    setShowCandidates,
    setShowMonuments,
    setShowAreas,
    reset,
  } = useViewState();

  const mapRef = useRef<maplibregl.Map | null>(null);
  const centeredRef = useRef(false);
  const [mapReady, setMapReady] = useState(false);
  const [zoom, setZoom] = useState(4.4);
  const [bounds, setBounds] = useState<[number, number, number, number] | null>(
    null,
  );
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sheet, setSheet] = useState<Sheet>(null);
  const [sources, setSources] = useState<Record<string, Source>>({});

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const list = await fetchSources();
        if (cancelled) return;
        setSources(
          Object.fromEntries(list.map((source) => [source.id, source])),
        );
      } catch {
        // 出典が読めなくても地図は使える
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const monuments = useMonuments(view.showMonuments);

  const candidatesEnabled = view.showCandidates;
  const areasEnabled = view.showAreas && zoom >= AREA_MIN_ZOOM;

  // 候補は全国にあるため、都道府県を問わず読み込む。
  // gzip 後で 0.4MB 程度なので、初期表示から全国を見渡せる。
  const candidatePrefCodes = useMemo(() => {
    if (view.filters.prefCodes.length > 0) return view.filters.prefCodes;
    const codes = Object.keys(data.stats?.candidatesByPrefecture ?? {});
    return codes.length > 0 ? codes.sort() : [];
  }, [view.filters.prefCodes, data.stats]);

  const { candidates } = useCandidates(candidatePrefCodes, candidatesEnabled);

  // 範囲ポリゴンは重いので、画面内の都道府県だけに絞る
  const visiblePrefCodes = useMemo(
    () => prefCodesInBounds([...data.toponyms, ...candidates], bounds),
    [data.toponyms, candidates, bounds],
  );
  const areaPrefCodes = useMemo(() => {
    if (view.filters.prefCodes.length > 0) return view.filters.prefCodes;
    return visiblePrefCodes;
  }, [view.filters.prefCodes, visiblePrefCodes]);

  const { areas } = useAreas(areaPrefCodes, areasEnabled);

  const filteredToponyms = useMemo(
    () => applyFilters(data.toponyms, view.filters),
    [data.toponyms, view.filters],
  );
  const filteredCandidates = useMemo(
    () => applyFilters(candidates, view.filters),
    [candidates, view.filters],
  );

  const visibleAreaKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const feature of filteredToponyms) {
      if (feature.properties.areaKey) keys.add(feature.properties.areaKey);
    }
    for (const feature of filteredCandidates) {
      if (feature.properties.areaKey) keys.add(feature.properties.areaKey);
    }
    return keys;
  }, [filteredToponyms, filteredCandidates]);

  // 絞り込みで消えた地名の範囲までは描かない
  const visibleAreas = useMemo(
    () => areas.filter((area) => visibleAreaKeys.has(area.properties.key)),
    [areas, visibleAreaKeys],
  );

  const selectedFeature = useMemo(() => {
    if (!view.selectedId) return null;
    return (
      filteredToponyms.find(
        (feature) => feature.properties.id === view.selectedId,
      ) ??
      data.toponyms.find(
        (feature) => feature.properties.id === view.selectedId,
      ) ??
      candidates.find((feature) => feature.properties.id === view.selectedId) ??
      null
    );
  }, [view.selectedId, filteredToponyms, data.toponyms, candidates]);

  const handleSelect = useCallback(
    (id: string | null) => {
      setSelectedId(id);
      if (!id) return;
      setSheet(null);
      centeredRef.current = true;
      const feature =
        data.toponyms.find((item) => item.properties.id === id) ??
        candidates.find((item) => item.properties.id === id);
      if (feature && mapRef.current) {
        mapRef.current.flyTo({
          center: feature.geometry.coordinates,
          zoom: Math.max(mapRef.current.getZoom(), 12),
          duration: 700,
        });
      }
    },
    [setSelectedId, data.toponyms, candidates],
  );

  const handleViewChange = useCallback(
    (nextZoom: number, nextBounds: [number, number, number, number]) => {
      setZoom(nextZoom);
      setBounds(nextBounds);
    },
    [],
  );

  const handleMapReady = useCallback((map: maplibregl.Map) => {
    mapRef.current = map;
    setMapReady(true);
  }, []);

  // 共有リンクを開いたときは、選択された地名まで一度だけ寄せる
  useEffect(() => {
    if (!mapReady || centeredRef.current || !view.selectedId) return;
    const feature = data.toponyms.find(
      (item) => item.properties.id === view.selectedId,
    );
    if (!feature) return;
    centeredRef.current = true;
    mapRef.current?.jumpTo({ center: feature.geometry.coordinates, zoom: 13 });
  }, [mapReady, view.selectedId, data.toponyms]);

  // タブレットの幅で絞り込みと詳細を同時に開くと地図が読めなくなるので、
  // 詳細を開いている間は絞り込みを畳む。
  const showSidebar =
    isDesktop && sidebarOpen && (isWide || selectedFeature === null);

  const visibleCount = filteredToponyms.length + filteredCandidates.length;
  const resultRows = useMemo(
    () => [...filteredToponyms, ...filteredCandidates],
    [filteredToponyms, filteredCandidates],
  );

  const filterPanel = (
    <FilterPanel
      filters={view.filters}
      stats={data.stats}
      elements={data.elements}
      baseMap={view.baseMap}
      hazardLayers={view.hazardLayers}
      showCandidates={view.showCandidates}
      showMonuments={view.showMonuments}
      showAreas={view.showAreas}
      areasAvailable={areasEnabled}
      visibleCount={visibleCount}
      onFiltersChange={setFilters}
      onBaseMapChange={setBaseMap}
      onHazardLayersChange={setHazardLayers}
      onShowCandidatesChange={setShowCandidates}
      onShowMonumentsChange={setShowMonuments}
      onShowAreasChange={setShowAreas}
      onReset={reset}
    />
  );

  return (
    <div className="flex h-dvh flex-col bg-background">
      <SiteHeader builtAt={data.meta?.builtAt ?? null} />

      <div className="relative flex min-h-0 flex-1">
        {showSidebar ? (
          <aside className="flex w-[19rem] shrink-0 flex-col border-r border-border bg-sidebar">
            <div className="min-h-0 flex-1 overflow-y-auto">
              {filterPanel}
              <div className="border-t border-border">
                <h3 className="px-3 py-2 text-xs font-semibold">結果一覧</h3>
                <ResultList
                  features={resultRows}
                  selectedId={view.selectedId}
                  onSelect={handleSelect}
                />
              </div>
            </div>
          </aside>
        ) : null}

        <div className="relative min-w-0 flex-1">
          <MapView
            toponyms={filteredToponyms}
            candidates={filteredCandidates}
            areas={visibleAreas}
            monuments={monuments}
            selectedId={view.selectedId}
            selectedAreaKey={selectedFeature?.properties.areaKey ?? null}
            showAreas={areasEnabled}
            baseMap={view.baseMap}
            hazardLayers={view.hazardLayers}
            showMonuments={view.showMonuments}
            onSelect={handleSelect}
            onViewChange={handleViewChange}
            onMapReady={handleMapReady}
          />

          {isDesktop ? (
            <Button
              variant="secondary"
              size="icon-sm"
              className="absolute top-2 left-2 z-10 cursor-pointer shadow-sm"
              onClick={() => setSidebarOpen((open) => !open)}
              aria-label={showSidebar ? "パネルを閉じる" : "パネルを開く"}
            >
              {showSidebar ? (
                <PanelLeftClose className="size-4" />
              ) : (
                <PanelLeftOpen className="size-4" />
              )}
            </Button>
          ) : null}

          {data.loading ? (
            <div className="pointer-events-none absolute inset-x-0 top-2 z-10 flex justify-center">
              <span className="rounded-md bg-card px-2 py-1 text-xs shadow-sm">
                データを読み込んでいます…
              </span>
            </div>
          ) : null}

          {data.error ? (
            <div className="absolute inset-x-0 top-2 z-10 flex justify-center px-4">
              <p className="rounded-md bg-destructive px-2 py-1 text-xs text-white shadow-sm">
                {data.error}
              </p>
            </div>
          ) : null}

          {view.showAreas && !areasEnabled ? (
            <div className="pointer-events-none absolute inset-x-0 bottom-16 z-10 flex justify-center px-4 md:bottom-10">
              <span className="rounded-md bg-card/95 px-2 py-1 text-center text-[11px] shadow-sm">
                地名がカバーする範囲は、拡大すると表示されます
              </span>
            </div>
          ) : null}

          {/* 狭い画面では、地図を隠さずに絞り込みと一覧を開けるようにする */}
          {!isDesktop ? (
            <div className="absolute inset-x-0 bottom-0 z-20 flex gap-2 px-3 pt-2 pb-[calc(env(safe-area-inset-bottom)+0.75rem)]">
              <Button
                variant="secondary"
                className="h-11 flex-1 cursor-pointer shadow-lg"
                onClick={() => setSheet("filters")}
              >
                <ListFilter className="size-4" />
                絞り込み
              </Button>
              <Button
                variant="secondary"
                className="h-11 flex-1 cursor-pointer shadow-lg"
                onClick={() => setSheet("list")}
              >
                <Rows3 className="size-4" />
                一覧 {visibleCount}
              </Button>
            </div>
          ) : null}
        </div>

        {selectedFeature && isDesktop ? (
          <aside className="w-[21rem] shrink-0 border-l border-border bg-card">
            <DetailPanel
              feature={selectedFeature}
              sources={sources}
              onClose={() => setSelectedId(null)}
            />
          </aside>
        ) : null}

        {!isDesktop ? (
          <>
            <BottomSheet
              title="絞り込みと表示"
              open={sheet === "filters" && !selectedFeature}
              onClose={() => setSheet(null)}
            >
              {filterPanel}
            </BottomSheet>
            <BottomSheet
              title={`結果一覧（${visibleCount}件）`}
              open={sheet === "list" && !selectedFeature}
              onClose={() => setSheet(null)}
            >
              <ResultList
                features={resultRows}
                selectedId={view.selectedId}
                onSelect={handleSelect}
              />
            </BottomSheet>
            <BottomSheet
              title="地名の詳細"
              open={Boolean(selectedFeature)}
              heightClass="h-[78dvh]"
              onClose={() => setSelectedId(null)}
            >
              {selectedFeature ? (
                <DetailPanel
                  feature={selectedFeature}
                  sources={sources}
                  onClose={() => setSelectedId(null)}
                  hideHeaderClose
                />
              ) : null}
            </BottomSheet>
          </>
        ) : null}
      </div>
    </div>
  );
}
