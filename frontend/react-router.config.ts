import type { Config } from "@react-router/dev/config";

// GitHub Pages ではリポジトリ名がパスの先頭に付くため、ビルド時に
// VITE_BASE_PATH で basename を渡す。ローカル開発では "/" のまま。
export default {
  ssr: false,
  basename: process.env.VITE_BASE_PATH ?? "/",
} satisfies Config;
