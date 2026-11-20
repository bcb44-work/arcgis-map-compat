import React, { useEffect, useRef, useState } from "react";
import { createRender, useModelState } from "@anywidget/react";
import { arcgisImport, configureArcGisCdn } from "../shared/arcgis-cdn";
import type { DictionaryState, MapViewState } from "../shared/types";
import "../widget.css";

type WebMapCtor = typeof import("@arcgis/core/WebMap.js").default;

const MapWidgetView: React.FC = () => {
  const [jsApiPath] = useModelState<string>("js_api_path");
  const [webmapDict] = useModelState<DictionaryState>("_webmap_dict");
  const [viewState, setViewState] = useModelState<MapViewState>("_view_state");
  const mapElementRef = useRef<HTMLArcgisMapElement | null>(null);
  const suppressNextEffect = useRef(false);
  const [viewReadyCount, setViewReadyCount] = useState(0);

  useEffect(() => {
    configureArcGisCdn(jsApiPath);
  }, []);

  // Retain the existing widget's WebMap.fromJSON state path.
  useEffect(() => {
    if (!mapElementRef.current) return;
    const controller = new AbortController();
    void applyWebMapChange(mapElementRef.current, webmapDict, controller.signal);
    return () => controller.abort();
  }, [webmapDict]);

  useEffect(() => {
    const mapElement = mapElementRef.current;
    if (!mapElement?.ready) return;
    if (suppressNextEffect.current) {
      suppressNextEffect.current = false;
      return;
    }
    if (
      mapElement.zoom === viewState.zoom &&
      mapElement.center.latitude === viewState.center[0] &&
      mapElement.center.longitude === viewState.center[1]
    ) return;

    void mapElement.goTo({
      center: [viewState.center[1], viewState.center[0]],
      zoom: viewState.zoom,
    }, { animate: false }).catch((error: Error) => {
      if (error.name !== "AbortError") console.error(error);
    });
  }, [viewState, viewReadyCount]);

  return (
    <arcgis-map
      className="map-container calcite-mode-light"
      ref={mapElementRef}
      attributionMode="light"
      onarcgisViewReadyChange={() => setViewReadyCount((count) => count + 1)}
      onarcgisViewChange={(event) => {
        if (!event.target.stationary || !event.target.ready) return;
        suppressNextEffect.current = true;
        const { extent, zoom, center, scale } = event.target;
        setViewState({
          extent: extent.toJSON(),
          zoom: Math.round(zoom),
          center: [center.latitude ?? 0, center.longitude ?? 0],
          scale,
        });
      }}
    >
      <arcgis-zoom slot="top-left" />
    </arcgis-map>
  );
};

async function applyWebMapChange(
  mapElement: HTMLArcgisMapElement,
  definition: DictionaryState,
  signal: AbortSignal,
): Promise<void> {
  const [WebMap] = await arcgisImport<[WebMapCtor]>(["@arcgis/core/WebMap.js"]);
  if (!signal.aborted) mapElement.map = WebMap.fromJSON(definition);
}

const render = createRender(MapWidgetView);
export default { render };
