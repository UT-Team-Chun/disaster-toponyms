import { ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "~/components/ui/badge";
import { SiteHeader } from "~/components/ui/siteHeader";
import { fetchMeta, fetchSources } from "~/lib/dataset/client";
import type { Meta, Source } from "~/lib/dataset/schema";

const TYPE_LABELS: Record<string, string> = {
  book: "書籍",
  paper: "論文",
  web: "ウェブ",
  gov: "官公庁",
  db: "データセット",
  pdf: "PDF資料",
  monument: "伝承碑",
  news: "報道",
  map: "地図",
};

export function SourceList() {
  const [sources, setSources] = useState<Source[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [loadedSources, loadedMeta] = await Promise.all([
          fetchSources(),
          fetchMeta(),
        ]);
        if (cancelled) return;
        setSources(loadedSources);
        setMeta(loadedMeta);
      } catch (loadError: unknown) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "出典一覧を読み込めませんでした",
          );
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <SiteHeader builtAt={meta?.builtAt ?? null} />
      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-6">
        <h1 className="text-xl font-semibold">出典一覧</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          この地図が引用している資料です。書籍については書誌情報と短い引用のみを収録し、
          本文は再配布していません。
        </p>

        {error ? (
          <p className="mt-4 text-sm text-destructive">{error}</p>
        ) : null}

        <ul className="mt-4 space-y-3">
          {sources.map((source) => (
            <li
              key={source.id}
              className="rounded-lg border border-border bg-card p-3"
            >
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                <Badge variant="outline" className="text-[10px]">
                  {TYPE_LABELS[source.type] ?? source.type}
                </Badge>
                <h2 className="text-sm font-semibold">{source.title}</h2>
              </div>
              <p className="mt-1 text-[11px] text-muted-foreground">
                {[
                  source.author,
                  source.publisher,
                  source.year ? String(source.year) : null,
                ]
                  .filter(Boolean)
                  .join("／")}
              </p>
              {source.note ? (
                <p className="mt-1.5 text-xs leading-relaxed">{source.note}</p>
              ) : null}
              <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
                {source.license ? (
                  <span>ライセンス: {source.license}</span>
                ) : null}
                {source.accessed ? (
                  <span>参照日: {source.accessed}</span>
                ) : null}
                {source.doi ? (
                  <a
                    href={source.doi}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-0.5 text-primary underline underline-offset-2"
                  >
                    DOI
                    <ExternalLink className="size-2.5" />
                  </a>
                ) : null}
                {source.url ? (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-0.5 break-all text-primary underline underline-offset-2"
                  >
                    {source.url}
                    <ExternalLink className="size-2.5 shrink-0" />
                  </a>
                ) : null}
              </div>
            </li>
          ))}
        </ul>

        {meta && meta.attribution.length > 0 ? (
          <section className="mt-8">
            <h2 className="text-sm font-semibold">データの出典表記</h2>
            <ul className="mt-2 list-disc space-y-0.5 pl-5 text-xs text-muted-foreground">
              {meta.attribution.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </main>
    </div>
  );
}
