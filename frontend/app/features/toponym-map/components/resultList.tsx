import { HAZARD_COLORS, primaryHazard } from "~/lib/dataset/labels";
import type { ToponymFeature } from "~/lib/dataset/schema";

const MAX_ROWS = 300;

type Props = {
  features: ToponymFeature[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function ResultList(props: Props) {
  const rows = props.features
    .slice()
    .sort(
      (left, right) =>
        right.properties.evidenceLevel - left.properties.evidenceLevel ||
        left.properties.name.localeCompare(right.properties.name, "ja"),
    )
    .slice(0, MAX_ROWS);

  if (rows.length === 0) {
    return (
      <p className="p-3 text-[11px] text-muted-foreground">
        条件に合う地名がありません。
      </p>
    );
  }

  return (
    <div>
      <ul className="divide-y divide-border">
        {rows.map((feature) => {
          const item = feature.properties;
          const active = item.id === props.selectedId;
          return (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => props.onSelect(item.id)}
                aria-current={active}
                className={[
                  "flex w-full cursor-pointer items-start gap-2 px-3 py-2 text-left transition-colors",
                  active ? "bg-accent" : "hover:bg-accent/60",
                ].join(" ")}
              >
                <span
                  aria-hidden
                  className="mt-1 size-2 shrink-0 rounded-full ring-1 ring-white/70"
                  style={{
                    backgroundColor:
                      HAZARD_COLORS[primaryHazard(item.hazardTypes)],
                  }}
                />
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-baseline gap-x-1.5">
                    <span className="text-xs font-medium break-words">
                      {item.name}
                    </span>
                    {item.reading ? (
                      <span className="text-[10px] text-muted-foreground">
                        {item.reading}
                      </span>
                    ) : null}
                    {item.disputed ? (
                      <span className="text-[10px] text-destructive">異説</span>
                    ) : null}
                  </span>
                  <span className="block truncate text-[10px] text-muted-foreground">
                    {[item.pref, item.municipality].filter(Boolean).join("")}
                  </span>
                </span>
                <span className="mt-0.5 shrink-0 font-mono text-[10px] text-muted-foreground">
                  L{item.evidenceLevel}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {props.features.length > MAX_ROWS ? (
        <p className="px-3 py-2 text-[10px] text-muted-foreground">
          {props.features.length}件のうち先頭{MAX_ROWS}件を表示しています。
          検索や絞り込みで件数を減らしてください。
        </p>
      ) : null}
    </div>
  );
}
