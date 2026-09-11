import { SourceList } from "~/features/sources/sourceList";

export function meta() {
  return [
    { title: "出典一覧 | 警鐘地名マップ" },
    {
      name: "description",
      content:
        "警鐘地名マップが引用している地名考・学術文献・官公庁データの一覧。",
    },
  ];
}

export default function SourcesRoute() {
  return <SourceList />;
}
