import { useEffect, useState } from "react";
import { Link } from "react-router";

import { Badge } from "~/components/ui/badge";
import { Input } from "~/components/ui/input";
import { SiteHeader } from "~/components/ui/siteHeader";
import { fetchElements, fetchSources, fetchStats } from "~/lib/dataset/client";
import { HAZARD_COLORS, HAZARD_LABELS } from "~/lib/dataset/labels";
import type { ElementsFile, Source, Stats } from "~/lib/dataset/schema";

const normalize = (value: string): string => value.replace(/[\s\u3000]+/g, "");

export function Glossary() {
  const [elements, setElements] = useState<ElementsFile | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [sources, setSources] = useState<Record<string, Source>>({});
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [loadedElements, loadedStats, loadedSources] = await Promise.all([
          fetchElements(),
          fetchStats(),
          fetchSources(),
        ]);
        if (cancelled) return;
        setElements(loadedElements);
        setStats(loadedStats);
        setSources(
          Object.fromEntries(
            loadedSources.map((source) => [source.id, source]),
          ),
        );
      } catch (loadError: unknown) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "辞典を読み込めませんでした",
          );
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const needle = normalize(query);
  const rows = (elements?.elements ?? [])
    .filter((element) => {
      if (!needle) return true;
      const haystack = normalize(
        [
          element.label,
          element.meaning,
          element.substitution_of ?? "",
          ...element.surfaces,
          ...element.readings,
        ].join(" "),
      );
      return haystack.includes(needle);
    })
    .sort((left, right) => right.specificity - left.specificity);

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <SiteHeader />
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-6">
        <h1 className="text-xl font-semibold">地名要素辞典</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          地名を構成する形態素と、その地形・災害上の意味。
          「梅＝埋」のように災害を示す字が無難な字に置き換えられた
          <strong className="font-medium text-foreground">替字（換字）</strong>
          を含みます。字面だけで判断できない地名を拾うための鍵になります。
        </p>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          「特異度」はその表記だけで災害履歴を示唆する強さです。
          久保や沢のように全国に無数にある要素は低く、蛇抜や押出のように
          ほぼ災害由来のものは高くしています。0.55 以上の要素だけを
          全国の住所データからの候補抽出に使っています。
        </p>

        {error ? (
          <p className="mt-4 text-sm text-destructive">{error}</p>
        ) : null}

        <div className="mt-4 max-w-sm">
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="要素・表記・読み・意味で検索"
            aria-label="地名要素を検索"
          />
        </div>

        <p className="mt-2 text-xs text-muted-foreground">
          {rows.length} / {elements?.elements.length ?? 0} 件
        </p>

        <ul className="mt-4 space-y-3">
          {rows.map((element) => {
            const count = stats?.byElement[element.id] ?? 0;
            return (
              <li
                key={element.id}
                className="rounded-lg border border-border bg-card p-3"
              >
                <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                  <h2 className="text-sm font-semibold">{element.label}</h2>
                  {element.substitution_of ? (
                    <Badge variant="secondary" className="text-[10px]">
                      替字（本来は「{element.substitution_of}」）
                    </Badge>
                  ) : null}
                  <span className="text-[11px] text-muted-foreground">
                    特異度 {element.specificity.toFixed(2)}
                  </span>
                  {count > 0 ? (
                    <Link
                      to={`/?el=${element.id}`}
                      className="text-[11px] text-primary underline underline-offset-2"
                    >
                      地図で{count}件を見る
                    </Link>
                  ) : null}
                </div>

                <p className="mt-1.5 text-xs leading-relaxed">
                  {element.meaning}
                </p>

                <div className="mt-2 flex flex-wrap gap-1.5">
                  {element.hazard_types.map((hazard) => (
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

                <dl className="mt-2 space-y-0.5 text-[11px] leading-relaxed text-muted-foreground">
                  {element.surfaces.length > 0 ? (
                    <div className="flex gap-1.5">
                      <dt className="shrink-0 font-medium">表記</dt>
                      <dd>{element.surfaces.join("・")}</dd>
                    </div>
                  ) : null}
                  {element.readings.length > 0 ? (
                    <div className="flex gap-1.5">
                      <dt className="shrink-0 font-medium">読み</dt>
                      <dd>{element.readings.join("・")}</dd>
                    </div>
                  ) : null}
                  {element.source_ids.length > 0 ? (
                    <div className="flex gap-1.5">
                      <dt className="shrink-0 font-medium">出典</dt>
                      <dd>
                        {element.source_ids
                          .map((id) => sources[id]?.title ?? id)
                          .join("／")}
                      </dd>
                    </div>
                  ) : null}
                </dl>
              </li>
            );
          })}
        </ul>
      </main>
    </div>
  );
}
