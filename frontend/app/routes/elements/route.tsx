import { Glossary } from "~/features/glossary/glossary";

export function meta() {
  return [
    { title: "地名要素辞典 | 警鐘地名マップ" },
    {
      name: "description",
      content:
        "災害を示す地名の形態素と替字（梅＝埋など）の一覧。意味・災害種別・出典つき。",
    },
  ];
}

export default function ElementsRoute() {
  return <Glossary />;
}
