import type maplibregl from "maplibre-gl";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Button } from "~/components/ui/button";
import { SiteHeader } from "~/components/ui/siteHeader";
import { DetailPanel } from "~/features/toponym-map/components/detailPanel";
import { FilterPanel } from "~/features/toponym-map/components/filterPanel";
import { MapView } from "~/features/toponym-map/components/mapView";
import { ResultList } from "~/features/toponym-map/components/resultList";
import { useViewState } from "~/features/toponym-map/hooks/useFilters";
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

  return (
    <div className="flex h-dvh flex-col bg-background">
      <SiteHeader builtAt={data.meta?.builtAt ?? null} />

      <div className="relative flex min-h-0 flex-1">
        {sidebarOpen ? (
          <aside className="flex w-[19rem] shrink-0 flex-col border-r border-border bg-sidebar">
            <div className="min-h-0 flex-1 overflow-y-auto">
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
                visibleCount={
                  filteredToponyms.length + filteredCandidates.length
                }
                onFiltersChange={setFilters}
                onBaseMapChange={setBaseMap}
                onHazardLayersChange={setHazardLayers}
                onShowCandidatesChange={setShowCandidates}
                onShowMonumentsChange={setShowMonuments}
                onShowAreasChange={setShowAreas}
                onReset={reset}
              />
              <div className="border-t border-border">
                <h3 className="px-3 py-2 text-xs font-semibold">結果一覧</h3>
                <ResultList
                  features={[...filteredToponyms, ...filteredCandidates]}
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

          <Button
            variant="secondary"
            size="icon-sm"
            className="absolute top-2 left-2 z-10 cursor-pointer shadow-sm"
            onClick={() => setSidebarOpen((open) => !open)}
            aria-label={sidebarOpen ? "パネルを閉じる" : "パネルを開く"}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="size-4" />
            ) : (
              <PanelLeftOpen className="size-4" />
            )}
          </Button>

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
            <div className="pointer-events-none absolute bottom-10 left-1/2 z-10 -translate-x-1/2">
              <span className="rounded-md bg-card/95 px-2 py-1 text-[11px] shadow-sm">
                地名がカバーする範囲は、拡大すると表示されます
              </span>
            </div>
          ) : null}
        </div>

        {selectedFeature ? (
          <aside className="absolute inset-y-0 right-0 z-20 w-[21rem] max-w-[calc(100%-2rem)] border-l border-border bg-card shadow-lg md:relative md:shadow-none">
            <DetailPanel
              feature={selectedFeature}
              sources={sources}
              onClose={() => setSelectedId(null)}
            />
          </aside>
        ) : null}
      </div>
    </div>
  );
}
