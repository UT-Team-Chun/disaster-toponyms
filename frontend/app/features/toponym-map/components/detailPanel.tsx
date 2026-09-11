import { ExternalLink, Quote, TriangleAlert, X } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "~/components/ui/badge";
import { Button } from "~/components/ui/button";
import { Separator } from "~/components/ui/separator";
import { fetchToponymDetail } from "~/lib/dataset/client";
import {
  EVIDENCE_KIND_LABELS,
  EVIDENCE_LEVEL_DESCRIPTIONS,
  EVIDENCE_LEVEL_LABELS,
  HAZARD_COLORS,
  HAZARD_LABELS,
  MATCH_METHOD_LABELS,
  PRECISION_LABELS,
  RECORD_RELATION_LABELS,
  STATUS_LABELS,
  ZONE_LABELS,
  primaryHazard,
} from "~/lib/dataset/labels";
import type {
  DisasterRecord,
  Evidence,
  Source,
  ToponymDetail,
  ToponymFeature,
} from "~/lib/dataset/schema";

type Props = {
  feature: ToponymFeature;
  sources: Record<string, Source>;
  onClose: () => void;
  /** 下からのシートで開くときは、シート側に閉じるボタンがある。 */
  hideHeaderClose?: boolean;
};

const gsiMapUrl = (lat: number, lon: number): string =>
  `https://maps.gsi.go.jp/#15/${lat}/${lon}/&base=pale&ls=pale%7C05_dosekiryukeikaikuiki&disp=11&vs=c1j0h0k0l0u0t0z0r0s0m0f1`;

const EvidenceCard = ({
  evidence,
  source,
}: {
  evidence: Evidence;
  source: Source | undefined;
}) => {
  const disputes = evidence.stance === "disputes";
  return (
    <div
      className={[
        "rounded-md border p-2.5",
        disputes
          ? "border-destructive/40 bg-destructive/5"
          : "border-border bg-card",
      ].join(" ")}
    >
      <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
        <Badge
          variant={disputes ? "destructive" : "secondary"}
          className="text-[10px]"
        >
          {disputes ? "反証" : `レベル${evidence.level}`}
        </Badge>
        <Badge variant="outline" className="text-[10px]">
          {EVIDENCE_KIND_LABELS[evidence.kind] ?? evidence.kind}
        </Badge>
        {evidence.quote_verified ? (
          <Badge variant="outline" className="text-[10px] text-emerald-700">
            {evidence.quote_medium === "ocr"
              ? "OCR転写と一致（原本未確認）"
              : "原文一致を検証済み"}
          </Badge>
        ) : null}
        {evidence.extracted_by.startsWith("llm:") ? (
          <Badge variant="outline" className="text-[10px]">
            LLM抽出（{evidence.extracted_by.slice(4)}）
          </Badge>
        ) : null}
      </div>

      <p className="text-xs leading-relaxed text-foreground">
        {evidence.claim}
      </p>

      {evidence.quote ? (
        <blockquote className="mt-2 flex gap-1.5 border-l-2 border-border pl-2 text-[11px] leading-relaxed text-muted-foreground">
          <Quote className="mt-0.5 size-3 shrink-0 opacity-50" />
          <span>{evidence.quote}</span>
        </blockquote>
      ) : null}

      <div className="mt-2 text-[10px] leading-snug text-muted-foreground">
        {source ? (
          <span>
            {source.author
              ? `${source.author}『${source.title}』`
              : source.title}
            {source.publisher ? `／${source.publisher}` : ""}
            {source.year ? `（${source.year}）` : ""}
          </span>
        ) : (
          <span>{evidence.source_id}</span>
        )}
        {evidence.locator ? (
          <span className="ml-1">
            {evidence.locator.startsWith("http") ? (
              <a
                href={evidence.locator}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-0.5 text-primary underline underline-offset-2"
              >
                出典を開く
                <ExternalLink className="size-2.5" />
              </a>
            ) : (
              evidence.locator
            )}
          </span>
        ) : null}
      </div>
    </div>
  );
};

const RecordCard = ({
  record,
  source,
}: {
  record: DisasterRecord;
  source: Source | undefined;
}) => (
  <div className="rounded-md border border-border bg-card p-2.5">
    <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
      <Badge variant="secondary" className="text-[10px]">
        {RECORD_RELATION_LABELS[record.relation] ?? record.relation}
      </Badge>
      {record.date_text ? (
        <span className="font-mono text-[10px] text-muted-foreground">
          {record.date_text}
        </span>
      ) : null}
    </div>
    <p className="text-xs leading-relaxed">{record.name}</p>
    {record.quote ? (
      <blockquote className="mt-1.5 flex gap-1.5 border-l-2 border-border pl-2 text-[11px] leading-relaxed text-muted-foreground">
        <Quote className="mt-0.5 size-3 shrink-0 opacity-50" />
        <span>{record.quote}</span>
      </blockquote>
    ) : null}
    <p className="mt-1.5 text-[10px] leading-snug text-muted-foreground">
      {MATCH_METHOD_LABELS[record.match_method] ?? record.match_method}
      {record.distance_km !== null && record.distance_km !== undefined
        ? `／地点まで約${record.distance_km.toFixed(1)}km`
        : ""}
      {source ? `／${source.title}` : ""}
    </p>
  </div>
);

export function DetailPanel(props: Props) {
  const { feature } = props;
  const [detail, setDetail] = useState<ToponymDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const props_ = feature.properties;

  useEffect(() => {
    let cancelled = false;
    // 候補（レベル0）にも、被災記録が結びついたものには詳細がある
    if (props_.evidenceLevel === 0 && !props_.hasRecord) return;
    const load = async () => {
      try {
        const loaded = await fetchToponymDetail(props_.id);
        if (cancelled) return;
        setDetail(loaded);
        setError(null);
      } catch (loadError: unknown) {
        if (cancelled) return;
        setError(
          loadError instanceof Error
            ? loadError.message
            : "詳細を読み込めませんでした",
        );
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [props_.id, props_.evidenceLevel, props_.hasRecord]);

  // 選択が切り替わった直後は前の詳細が残るため、id が一致するときだけ使う
  const shown = detail?.id === props_.id ? detail : null;
  const [lon, lat] = feature.geometry.coordinates;
  const supporting = (shown?.evidence ?? []).filter(
    (item) => item.stance === "supports",
  );
  const disputing = (shown?.evidence ?? []).filter(
    (item) => item.stance === "disputes",
  );

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-start justify-between gap-2 border-b border-border p-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-baseline gap-x-2">
            <h2 className="text-lg leading-tight font-semibold break-words">
              {props_.name}
            </h2>
            {props_.reading ? (
              <span className="text-xs text-muted-foreground">
                {props_.reading}
              </span>
            ) : null}
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {[props_.pref, props_.municipality].filter(Boolean).join("")}
            {shown?.admin.oaza ? ` ${shown.admin.oaza}` : ""}
          </p>
          {shown?.admin.province ? (
            <p className="text-[11px] text-muted-foreground">
              資料上の所在: {shown.admin.province}
              {shown.admin.district ?? ""}
            </p>
          ) : null}
          {shown?.admin.historical_village ? (
            <p className="text-[11px] text-muted-foreground">
              旧村: {shown.admin.historical_village}
            </p>
          ) : null}
        </div>
        {props.hideHeaderClose ? null : (
          <Button
            variant="ghost"
            size="icon-sm"
            className="shrink-0 cursor-pointer"
            onClick={props.onClose}
            aria-label="閉じる"
          >
            <X className="size-4" />
          </Button>
        )}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-3">
        <div className="flex flex-wrap gap-1.5">
          <Badge
            variant="secondary"
            className="text-[10px]"
            title={EVIDENCE_LEVEL_DESCRIPTIONS[props_.evidenceLevel]}
          >
            根拠レベル {props_.evidenceLevel}・
            {EVIDENCE_LEVEL_LABELS[props_.evidenceLevel]}
          </Badge>
          <Badge variant="outline" className="text-[10px]">
            {STATUS_LABELS[props_.status]}
          </Badge>
          <Badge variant="outline" className="text-[10px]">
            位置精度: {PRECISION_LABELS[props_.precision]}
          </Badge>
          {props_.hasRecord ? (
            <Badge variant="outline" className="text-[10px]">
              被災記録あり
            </Badge>
          ) : null}
          {props_.disputed ? (
            <Badge variant="destructive" className="text-[10px]">
              <TriangleAlert className="size-2.5" />
              異説あり
            </Badge>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {props_.hazardTypes.map((hazard) => (
            <span
              key={hazard}
              className="inline-flex items-center gap-1 rounded-md border border-border px-1.5 py-0.5 text-[10px]"
            >
              <span
                aria-hidden
                className="size-2 rounded-full"
                style={{ backgroundColor: HAZARD_COLORS[hazard] }}
              />
              {HAZARD_LABELS[hazard]}
            </span>
          ))}
        </div>

        {props_.summary ? (
          <p className="text-xs leading-relaxed">{props_.summary}</p>
        ) : null}

        {shown?.renamed_to ? (
          <p className="text-xs leading-relaxed">
            現在の地名: <span className="font-medium">{shown.renamed_to}</span>
          </p>
        ) : null}

        {shown && shown.variants.length > 0 ? (
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            別表記: {shown.variants.join("・")}
          </p>
        ) : null}

        {shown?.dispute_note ? (
          <div className="rounded-md border border-destructive/40 bg-destructive/5 p-2.5">
            <p className="mb-1 flex items-center gap-1 text-[11px] font-semibold text-destructive">
              <TriangleAlert className="size-3" />
              由来に異説がある
            </p>
            <p className="text-[11px] leading-relaxed">{shown.dispute_note}</p>
          </div>
        ) : null}

        {shown && shown.elements.length > 0 ? (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold">地名要素</h3>
            <ul className="space-y-1">
              {shown.elements.map((element) => (
                <li
                  key={`${element.element_id}-${element.surface}`}
                  className="text-[11px] leading-relaxed"
                >
                  <span className="font-medium">{element.surface}</span>
                  {element.meaning ? (
                    <span className="text-muted-foreground">
                      {" — "}
                      {element.meaning}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {props_.evidenceLevel === 0 ? (
          <div className="rounded-md border border-border bg-muted/40 p-2.5 text-[11px] leading-relaxed">
            これは全国の住所データで表記が要素辞書に一致した候補です。出典による裏づけは
            確認していないため、災害履歴を示すとは限りません。
            {props_.hasRecord
              ? "この場所の被災記録は見つかっていますが、地名の由来を説明する資料は確認できていません。"
              : ""}
          </div>
        ) : null}

        {supporting.length > 0 ? (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold">根拠</h3>
            <div className="space-y-2">
              {supporting.map((evidence, index) => (
                <EvidenceCard
                  key={`${evidence.source_id}-${index}`}
                  evidence={evidence}
                  source={props.sources[evidence.source_id]}
                />
              ))}
            </div>
          </div>
        ) : null}

        {disputing.length > 0 ? (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold text-destructive">
              反証・注意
            </h3>
            <div className="space-y-2">
              {disputing.map((evidence, index) => (
                <EvidenceCard
                  key={`${evidence.source_id}-dis-${index}`}
                  evidence={evidence}
                  source={props.sources[evidence.source_id]}
                />
              ))}
            </div>
          </div>
        ) : null}

        {shown && shown.disaster_records.length > 0 ? (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold">記録された災害</h3>
            <p className="mb-1.5 text-[10px] leading-snug text-muted-foreground">
              この場所で実際に起きたと資料が記す災害。地名の由来とは別の事実として扱っている。
            </p>
            <div className="space-y-2">
              {shown.disaster_records.map((record, index) => (
                <RecordCard
                  key={`${record.source_id}-${record.locator}-${index}`}
                  record={record}
                  source={
                    record.source_id
                      ? props.sources[record.source_id]
                      : undefined
                  }
                />
              ))}
            </div>
          </div>
        ) : null}

        {props_.areaKey ? (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold">
              この地名がカバーする範囲
            </h3>
            <p className="text-[11px] leading-relaxed text-muted-foreground">
              地図上に
              <span className="font-medium text-foreground">
                {shown?.admin.oaza ?? props_.municipality}
              </span>
              の範囲を重ねています。小字の境界は全国では公開されていないため、
              国勢調査の町丁・字等（{PRECISION_LABELS.oaza}
              ）の単位で示しています。
              点は範囲の代表点であり、地名が指す場所そのものではありません。
            </p>
          </div>
        ) : null}

        {props_.zones.length > 0 ? (
          <div>
            <h3 className="mb-1.5 text-xs font-semibold">現在のハザード指定</h3>
            <p className="mb-1.5 text-[10px] leading-snug text-muted-foreground">
              地名の由来とは別に、今のハザードマップがこの地点をどう評価しているか。
            </p>
            <ul className="space-y-0.5">
              {props_.zones.map((zone) => (
                <li key={zone} className="text-[11px] leading-relaxed">
                  {ZONE_LABELS[zone] ?? zone}
                </li>
              ))}
            </ul>
          </div>
        ) : shown?.hazard_corroboration.sampled_at ? (
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            現在のハザードマップでは、この地点は警戒区域・浸水想定区域に含まれていません。
          </p>
        ) : null}

        {shown && shown.hazard_corroboration.nearest_monument_ids.length > 0 ? (
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            近隣に自然災害伝承碑が
            {shown.hazard_corroboration.nearest_monument_ids.length}基あります。
            「重ねる情報」で伝承碑レイヤーを表示してください。
          </p>
        ) : null}

        {shown?.review.note ? (
          <p className="text-[10px] leading-relaxed text-muted-foreground">
            調査メモ: {shown.review.note}
          </p>
        ) : null}

        {error ? <p className="text-[11px] text-destructive">{error}</p> : null}

        <Separator />

        <div className="flex flex-wrap gap-2 pb-2">
          <a
            href={gsiMapUrl(lat, lon)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-[11px] text-primary underline underline-offset-2"
          >
            地理院地図で開く
            <ExternalLink className="size-2.5" />
          </a>
          <span className="text-[11px] text-muted-foreground">
            {lat.toFixed(5)}, {lon.toFixed(5)}
          </span>
        </div>
      </div>

      <div
        aria-hidden
        className="h-1 w-full"
        style={{
          backgroundColor: HAZARD_COLORS[primaryHazard(props_.hazardTypes)],
        }}
      />
    </div>
  );
}
