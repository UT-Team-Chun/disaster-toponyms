import { createEnv } from "@t3-oss/env-core";
import { z } from "zod";

const viteEnv = createEnv({
  emptyStringAsUndefined: true,
  runtimeEnv: import.meta.env,
  server: {
    // t3のviteプリセットが動かないのでここで定義
    // https://vite.dev/guide/env-and-mode
    BASE_URL: z.string(),
    MODE: z.string(),
    DEV: z.boolean(),
    PROD: z.boolean(),
    SSR: z.boolean(),
  },
});

// 静的サイトとして配信するため、閲覧時に Backend API は呼ばない。
// API を追加する場合はここに VITE_ 接頭辞の変数を定義する。
export const env = createEnv({
  emptyStringAsUndefined: true,
  runtimeEnv: import.meta.env,
  clientPrefix: "VITE",
  client: {},
  extends: [viteEnv],
});

/**
 * デプロイ先のベースパス。Vite の base 設定がそのまま入る。
 * GitHub Pages では "/disaster-toponyms/"、ローカル開発では "/"。
 * 静的データの URL を組み立てるのに使う。
 */
export const basePath: string = import.meta.env.BASE_URL;
