import { arcgisImport } from "./arcgis-cdn";

import type { DictionaryState, MapContext2D } from "./types";
import type Renderer from "@arcgis/core/renderers/Renderer.js";
import type MapView from "@arcgis/core/views/MapView.js";
import type Layer from "@arcgis/core/layers/Layer";
import type FeatureLayer from "@arcgis/core/layers/FeatureLayer";
import type CSVLayer from "@arcgis/core/layers/CSVLayer";
import type GeoJSONLayer from "@arcgis/core/layers/GeoJSONLayer";
import type WFSLayer from "@arcgis/core/layers/WFSLayer";
import type OGCFeatureLayer from "@arcgis/core/layers/OGCFeatureLayer";
import type StreamLayer from "@arcgis/core/layers/StreamLayer";
import type OrientedImageryLayer from "@arcgis/core/layers/OrientedImageryLayer";

type RelationshipRendererModule =
  typeof import("@arcgis/core/smartMapping/renderers/relationship.js");
type UnivariateColorSizeRendererModule =
  typeof import("@arcgis/core/smartMapping/renderers/univariateColorSize.js");
type HeatmapRendererModule =
  typeof import("@arcgis/core/smartMapping/renderers/heatmap.js");
type DotDensityRendererModule =
  typeof import("@arcgis/core/smartMapping/renderers/dotDensity.js");
type PieChartRendererModule =
  typeof import("@arcgis/core/smartMapping/renderers/pieChart.js");
type PredominanceRendererModule =
  typeof import("@arcgis/core/smartMapping/renderers/predominance.js");
type SizeRendererModule =
  typeof import("@arcgis/core/smartMapping/renderers/size.js");
type ColorRendererModule =
  typeof import("@arcgis/core/smartMapping/renderers/color.js");
type TypeRendererModule =
  typeof import("@arcgis/core/smartMapping/renderers/type.js");

// Defines the expected parameters for each smart mapping renderer type, based on the ArcGIS API documentation.
type RelationshipRendererParams = Parameters<
  RelationshipRendererModule["createRenderer"]
>[0];
type UnivariateColorSizeRendererParams = Parameters<
  UnivariateColorSizeRendererModule["createContinuousRenderer"]
>[0];
type HeatmapRendererParams = Parameters<
  HeatmapRendererModule["createRenderer"]
>[0];
type DotDensityRendererParams = Parameters<
  DotDensityRendererModule["createRenderer"]
>[0];
type PieChartRendererParams = Parameters<
  PieChartRendererModule["createRenderer"]
>[0];
type PredominanceRendererParams = Parameters<
  PredominanceRendererModule["createRenderer"]
>[0];
type SizeClassBreaksRendererParams = Parameters<
  SizeRendererModule["createClassBreaksRenderer"]
>[0];
type ColorClassBreaksRendererParams = Parameters<
  ColorRendererModule["createClassBreaksRenderer"]
>[0];
type UniqueValuesRendererParams = Parameters<
  TypeRendererModule["createRenderer"]
>[0];

const supportedLayerTypes = [
  "feature",
  "csv",
  "geojson",
  "wfs",
  "ogc-feature",
  "stream",
  "oriented-imagery",
];

type SupportedLayer =
  | FeatureLayer
  | CSVLayer
  | GeoJSONLayer
  | WFSLayer
  | OGCFeatureLayer
  | StreamLayer
  | OrientedImageryLayer;

export async function applySmartMapping(
  { map, view }: MapContext2D,
  smartMappingParams: DictionaryState,
  setSMRenderer: (renderer: DictionaryState) => void,
  signal: AbortSignal,
): Promise<void> {
  if (!view || !map) {
    console.error("Smart Mapping: View or Map is not ready");
    return;
  }

  const layer = map.findLayerById(String(smartMappingParams.layerId ?? ""));
  if (!layer) {
    console.error("Smart Mapping: Layer not found");
    return;
  }
  if (!isSupportedSmartMappingLayer(layer)) {
    console.error(`Smart Mapping: Unsupported layer type "${layer.type}".`);
    return;
  }

  try {
    const renderer = await createSmartMappingRenderer(
      smartMappingParams,
      view,
      layer,
      signal
    );
    if (signal.aborted) return;
    layer.renderer = renderer;
    setSMRenderer(renderer.toJSON());
  } catch (error) {
    console.error("Error creating renderer:", error);
  }
}

function isSupportedSmartMappingLayer(layer: Layer): layer is SupportedLayer {
  return supportedLayerTypes.includes(layer.type);
}

async function createSmartMappingRenderer(
  smartMappingParams: DictionaryState,
  view: MapView,
  layer: SupportedLayer,
  signal: AbortSignal,
): Promise<Renderer> {
  // We are casting the rendererParams
  // This is fragile and relies on the caller to pass the correct parameters based on the type specified in smartMappingParams.type
  const rendererParams = { ...smartMappingParams, view, layer, signal };

  switch (smartMappingParams.type) {
    case "relationship":
      return createRelationshipRenderer(
        rendererParams as RelationshipRendererParams,
      );

    case "univariateColorSize":
      return createUnivariateColorSizeRenderer(
        rendererParams as UnivariateColorSizeRendererParams,
      );

    case "heatmap":
      return createHeatmapRenderer(rendererParams as HeatmapRendererParams);

    case "dotDensity":
      return createDotDensityRenderer(
        rendererParams as DotDensityRendererParams,
      );

    case "pieChart":
      return createPieChartRenderer(rendererParams as PieChartRendererParams);

    case "predominance":
      return createPredominanceRenderer(
        rendererParams as PredominanceRendererParams,
      );

    case "classBreaksSize":
      return createSizeClassBreaksRenderer(
        rendererParams as SizeClassBreaksRendererParams,
      );

    case "classBreaksColor":
      return createColorClassBreaksRenderer(
        rendererParams as ColorClassBreaksRendererParams,
      );

    case "uniqueValues":
      return createUniqueValuesRenderer(
        rendererParams as UniqueValuesRendererParams,
      );

    default:
      throw new Error(`Unsupported renderer type: ${smartMappingParams.type}`);
  }
}

async function createRelationshipRenderer(
  rendererParams: RelationshipRendererParams,
): Promise<Renderer> {
  const [relationshipRenderer] = await arcgisImport<
    [RelationshipRendererModule]
  >(["@arcgis/core/smartMapping/renderers/relationship.js"]);

  const { renderer } =
    await relationshipRenderer.createRenderer(rendererParams);
  return renderer;
}

async function createUnivariateColorSizeRenderer(
  rendererParams: UnivariateColorSizeRendererParams,
): Promise<Renderer> {
  const [univariateColorSizeRenderer] = await arcgisImport<
    [UnivariateColorSizeRendererModule]
  >(["@arcgis/core/smartMapping/renderers/univariateColorSize.js"]);

  const { renderer } =
    await univariateColorSizeRenderer.createContinuousRenderer(rendererParams);
  return renderer;
}

async function createHeatmapRenderer(
  rendererParams: HeatmapRendererParams,
): Promise<Renderer> {
  const [heatmapRenderer] = await arcgisImport<[HeatmapRendererModule]>([
    "@arcgis/core/smartMapping/renderers/heatmap.js",
  ]);

  const { renderer } = await heatmapRenderer.createRenderer(rendererParams);
  return renderer;
}

async function createDotDensityRenderer(
  rendererParams: DotDensityRendererParams,
): Promise<Renderer> {
  const [dotDensityRenderer] = await arcgisImport<[DotDensityRendererModule]>([
    "@arcgis/core/smartMapping/renderers/dotDensity.js",
  ]);

  const { renderer } = await dotDensityRenderer.createRenderer(rendererParams);
  return renderer;
}

async function createPieChartRenderer(
  rendererParams: PieChartRendererParams,
): Promise<Renderer> {
  const [pieChartRenderer] = await arcgisImport<[PieChartRendererModule]>([
    "@arcgis/core/smartMapping/renderers/pieChart.js",
  ]);

  const { renderer } = await pieChartRenderer.createRenderer(rendererParams);
  return renderer;
}

async function createPredominanceRenderer(
  rendererParams: PredominanceRendererParams,
): Promise<Renderer> {
  const [predominanceRenderer] = await arcgisImport<
    [PredominanceRendererModule]
  >(["@arcgis/core/smartMapping/renderers/predominance.js"]);

  const { renderer } =
    await predominanceRenderer.createRenderer(rendererParams);
  return renderer;
}

async function createSizeClassBreaksRenderer(
  rendererParams: SizeClassBreaksRendererParams,
): Promise<Renderer> {
  const [sizeRenderer] = await arcgisImport<[SizeRendererModule]>([
    "@arcgis/core/smartMapping/renderers/size.js",
  ]);

  const { renderer } =
    await sizeRenderer.createClassBreaksRenderer(rendererParams);
  return renderer;
}

async function createColorClassBreaksRenderer(
  rendererParams: ColorClassBreaksRendererParams,
): Promise<Renderer> {
  const [colorRenderer] = await arcgisImport<[ColorRendererModule]>([
    "@arcgis/core/smartMapping/renderers/color.js",
  ]);

  const { renderer } =
    await colorRenderer.createClassBreaksRenderer(rendererParams);
  return renderer;
}

async function createUniqueValuesRenderer(
  rendererParams: UniqueValuesRendererParams,
): Promise<Renderer> {
  const [typeRenderer] = await arcgisImport<[TypeRendererModule]>([
    "@arcgis/core/smartMapping/renderers/type.js",
  ]);

  const { renderer } = await typeRenderer.createRenderer(rendererParams);
  return renderer;
}
