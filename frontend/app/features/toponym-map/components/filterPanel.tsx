import { RotateCcw, Search } from "lucide-react";

import { Badge } from "~/components/ui/badge";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Separator } from "~/components/ui/separator";
import {
  BASE_MAPS,
  HAZARD_LAYERS,
  type BaseMapId,
  type HazardLayerId,
} from "~/features/toponym-map/lib/mapStyle";
import { toggleValue, type Filters } from "~/lib/dataset/filtering";
import {
  EVIDENCE_LEVEL_DESCRIPTIONS,
  EVIDENCE_LEVEL_LABELS,
  HAZARD_COLORS,
  HAZARD_LABELS,
  HAZARD_ORDER,
  PREFECTURES,
  STATUS_LABELS,
} from "~/lib/dataset/labels";
import type {
  ElementsFile,
  HazardType,
  Stats,
  ToponymStatus,
} from "~/lib/dataset/schema";

type Props = {
  filters: Filters;
  stats: Stats | null;
  elements: ElementsFile | null;
  baseMap: BaseMapId;
  hazardLayers: HazardLayerId[];
  showCandidates: boolean;
  showMonuments: boolean;
  showAreas: boolean;
  areasAvailable: boolean;
  visibleCount: number;
  onFiltersChange: (next: Filters) => void;
  onBaseMapChange: (id: BaseMapId) => void;
  onHazardLayersChange: (ids: HazardLayerId[]) => void;
  onShowCandidatesChange: (value: boolean) => void;
  onShowMonumentsChange: (value: boolean) => void;
  onShowAreasChange: (value: boolean) => void;
  onReset: () => void;
};

const Section = ({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: React.ReactNode;
}) => (
  <div className="space-y-2">
    <div>
      <h3 className="text-xs font-semibold tracking-wide text-foreground">
        {title}
      </h3>
      {hint ? (
        <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
    {children}
  </div>
);

const Chip = ({
  active,
  onClick,
  children,
  title,
  dotColor,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  title?: string;
  dotColor?: string;
}) => (
  <button
    type="button"
    onClick={onClick}
    title={title}
    aria-pressed={active}
    className={[
      "inline-flex cursor-pointer items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] transition-colors",
      active
        ? "border-primary bg-primary text-primary-foreground"
        : "border-border bg-background text-foreground hover:bg-accent",
    ].join(" ")}
  >
    {dotColor ? (
      <span
        aria-hidden
        className="size-2 rounded-full ring-1 ring-white/60"
        style={{ backgroundColor: dotColor }}
      />
    ) : null}
    {children}
  </button>
);

export function FilterPanel(props: Props) {
  const { filters, stats, elements } = props;
  const update = (next: Partial<Filters>) =>
    props.onFiltersChange({ ...filters, ...next });

  const elementCounts = stats?.byElement ?? {};
  const rankedElements = (elements?.elements ?? [])
    .filter((element) => (elementCounts[element.id] ?? 0) > 0)
    .sort(
      (left, right) =>
        (elementCounts[right.id] ?? 0) - (elementCounts[left.id] ?? 0),
    )
    .slice(0, 24);

  const prefsWithData = PREFECTURES.filter(
    ({ code }) =>
      (stats?.byPrefecture[code]?.total ?? 0) > 0 ||
      (stats?.candidatesByPrefecture[code] ?? 0) > 0,
  );

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto p-3">
      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={filters.query}
          onChange={(event) => update({ query: event.target.value })}
          placeholder="地名・読み・市区町村で検索"
          className="pl-8"
          aria-label="地名を検索"
        />
      </div>

      <div className="flex items-center justify-between text-[11px] text-muted-foreground">
        <span>
          表示中{" "}
          <span className="font-semibold text-foreground">
            {props.visibleCount}
          </span>{" "}
          件
        </span>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 cursor-pointer px-1.5 text-[11px]"
          onClick={props.onReset}
        >
          <RotateCcw className="size-3" />
          条件をリセット
        </Button>
      </div>

      <Separator />

      <Section
        title="根拠レベル"
        hint="出典が何を述べているかで分けている。0は表記が一致するだけの候補。"
      >
        <div className="flex flex-wrap gap-1.5">
          {[3, 2, 1, 0].map((level) => {
            const count =
              level === 0
                ? (stats?.candidatesTotal ?? 0)
                : (stats?.byLevel[String(level)] ?? 0);
            return (
              <Chip
                key={level}
                active={filters.levels.includes(level)}
                title={EVIDENCE_LEVEL_DESCRIPTIONS[level]}
                onClick={() =>
                  update({ levels: toggleValue(filters.levels, level) })
                }
              >
                <span className="font-mono">{level}</span>
                <span>{EVIDENCE_LEVEL_LABELS[level]}</span>
                <span className="opacity-60">{count}</span>
              </Chip>
            );
          })}
        </div>
      </Section>

      <Section title="災害種別">
        <div className="flex flex-wrap gap-1.5">
          {HAZARD_ORDER.filter(
            (hazard) => (stats?.byHazard[hazard] ?? 0) > 0,
          ).map((hazard: HazardType) => (
            <Chip
              key={hazard}
              active={filters.hazardTypes.includes(hazard)}
              dotColor={HAZARD_COLORS[hazard]}
              onClick={() =>
                update({
                  hazardTypes: toggleValue(filters.hazardTypes, hazard),
                })
              }
            >
              {HAZARD_LABELS[hazard]}
              <span className="opacity-60">{stats?.byHazard[hazard] ?? 0}</span>
            </Chip>
          ))}
        </div>
      </Section>

      <Section title="地名の状態">
        <div className="flex flex-wrap gap-1.5">
          {(["current", "historical", "renamed"] as ToponymStatus[]).map(
            (status) => (
              <Chip
                key={status}
                active={filters.statuses.includes(status)}
                onClick={() =>
                  update({ statuses: toggleValue(filters.statuses, status) })
                }
              >
                {STATUS_LABELS[status]}
              </Chip>
            ),
          )}
          <Chip
            active={filters.onlyDisputed}
            onClick={() => update({ onlyDisputed: !filters.onlyDisputed })}
            title="出典自身が由来に疑義を示しているもの"
          >
            異説あり
            <span className="opacity-60">{stats?.disputedTotal ?? 0}</span>
          </Chip>
          <Chip
            active={filters.onlyInHazardZone}
            onClick={() =>
              update({ onlyInHazardZone: !filters.onlyInHazardZone })
            }
            title="現在のハザードマップで警戒区域・浸水想定区域に入るもの"
          >
            現行ハザード区域内
          </Chip>
        </div>
      </Section>

      {rankedElements.length > 0 ? (
        <Section
          title="地名要素"
          hint="替字（梅＝埋 など）を含む、災害を示す形態素で絞り込む。"
        >
          <div className="flex flex-wrap gap-1.5">
            {rankedElements.map((element) => (
              <Chip
                key={element.id}
                active={filters.elementIds.includes(element.id)}
                title={element.meaning}
                onClick={() =>
                  update({
                    elementIds: toggleValue(filters.elementIds, element.id),
                  })
                }
              >
                {element.label}
                <span className="opacity-60">{elementCounts[element.id]}</span>
              </Chip>
            ))}
          </div>
        </Section>
      ) : null}

      {prefsWithData.length > 0 ? (
        <Section title="都道府県">
          <div className="flex flex-wrap gap-1.5">
            {prefsWithData.map(({ code, name }) => (
              <Chip
                key={code}
                active={filters.prefCodes.includes(code)}
                onClick={() =>
                  update({ prefCodes: toggleValue(filters.prefCodes, code) })
                }
              >
                {name}
                <span className="opacity-60">
                  {stats?.byPrefecture[code]?.total ?? 0}
                </span>
              </Chip>
            ))}
          </div>
        </Section>
      ) : null}

      <Separator />

      <Section title="重ねる情報">
        <div className="flex flex-wrap gap-1.5">
          <Chip
            active={props.showAreas}
            onClick={() => props.onShowAreasChange(!props.showAreas)}
            title="地名が属する町丁・字等の範囲。小字の境界は全国では公開されていないため、この単位で示す。"
          >
            地名がカバーする範囲
            {props.showAreas && !props.areasAvailable ? (
              <span className="opacity-60">拡大で表示</span>
            ) : null}
          </Chip>
          <Chip
            active={props.showCandidates}
            onClick={() => props.onShowCandidatesChange(!props.showCandidates)}
            title="根拠レベル0の候補。表記が要素辞典に一致するだけで、出典の裏づけは未確認。"
          >
            候補（レベル0）
            <span className="opacity-60">{stats?.candidatesTotal ?? 0}</span>
          </Chip>
          <Chip
            active={props.showMonuments}
            onClick={() => props.onShowMonumentsChange(!props.showMonuments)}
            title="国土地理院の自然災害伝承碑 2,469 基"
          >
            自然災害伝承碑
            <span className="opacity-60">{stats?.monumentsTotal ?? 0}</span>
          </Chip>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {HAZARD_LAYERS.map((layer) => (
            <Chip
              key={layer.id}
              active={props.hazardLayers.includes(layer.id)}
              onClick={() =>
                props.onHazardLayersChange(
                  toggleValue(props.hazardLayers, layer.id),
                )
              }
            >
              {layer.label}
            </Chip>
          ))}
        </div>
      </Section>

      <Section title="背景地図">
        <div className="flex flex-wrap gap-1.5">
          {BASE_MAPS.map((base) => (
            <Chip
              key={base.id}
              active={props.baseMap === base.id}
              onClick={() => props.onBaseMapChange(base.id)}
            >
              {base.label}
            </Chip>
          ))}
        </div>
      </Section>

      <Separator />

      <div className="space-y-1 text-[10px] leading-relaxed text-muted-foreground">
        <p className="flex flex-wrap items-center gap-1">
          <Badge variant="outline" className="text-[10px]">
            出典
          </Badge>
          地理院タイル・重ねるハザードマップ（国土地理院）／自然災害伝承碑（国土地理院）／
          Geolonia 住所データ（CC BY 4.0）
        </p>
      </div>
    </div>
  );
}
