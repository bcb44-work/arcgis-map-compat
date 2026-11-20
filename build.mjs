import { build } from "esbuild";

await build({
  entryPoints: ["src/arcgis_map_compat/frontend/widgets/map_widget.tsx"],
  outfile: "src/arcgis_map_compat/static/map_widget.js",
  bundle: true,
  minify: true,
  format: "esm",
  jsx: "automatic",
  define: { "process.env.NODE_ENV": '"production"' },
});
