import { About } from "~/features/about/about";

export function meta() {
  return [
    { title: "この地図について | 警鐘地名マップ" },
    {
      name: "description",
      content:
        "根拠レベルの定義、俗説への注意、現在のハザードマップとの関係、データの作り方。",
    },
  ];
}

export default function AboutRoute() {
  return <About />;
}
