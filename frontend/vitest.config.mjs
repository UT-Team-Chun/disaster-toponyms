import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config.ts";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      globals: true,
      includeSource: ["app/**/*.{js,ts}"],
    },
    // Production Buildでは除外する
    define: {
      "import.meta.vitest": "undefined",
    },
  }),
);
