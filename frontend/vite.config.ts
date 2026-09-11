import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";
import devtoolsJson from "vite-plugin-devtools-json";

export default defineConfig({
  // react-router.config.ts の basename と必ず同じ値にする
  base: process.env.VITE_BASE_PATH ?? "/",
  plugins: [devtoolsJson(), tailwindcss(), reactRouter(), tsconfigPaths()],
});
