import { ToponymMap } from "~/features/toponym-map/toponymMap";

export function meta() {
  return [
    { title: "警鐘地名マップ | 先人が地名に残した災害の記録" },
    {
      name: "description",
      content:
        "日本の警鐘地名（災害地名）を、地名考・地誌・伝承・災害記録という出典に基づいて地図上に集約したデータセット。",
    },
  ];
}

export default function Index() {
  return <ToponymMap />;
}
