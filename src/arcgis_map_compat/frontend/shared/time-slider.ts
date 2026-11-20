import { arcgisImport } from "./arcgis-cdn";

import type Map from "@arcgis/core/Map.js";
import type { MapContext } from "./types";

type TimeExtentCtor = typeof import("@arcgis/core/time/TimeExtent.js").default;
type TimeIntervalCtor =
  typeof import("@arcgis/core/time/TimeInterval.js").default;
type TimeIntervalProps = NonNullable<
  ConstructorParameters<TimeIntervalCtor>[0]
>;

/** Configuration object produced by buildTimeSliderConfig, ready to be spread
 * as JSX props onto <arcgis-time-slider>. */
export interface TimeSliderConfig {
  mode:
    | "time-window"
    | "instant"
    | "cumulative-from-start"
    | "cumulative-from-end";
  fullTimeExtent: InstanceType<TimeExtentCtor>;
  timeExtent: InstanceType<TimeExtentCtor>;
  stops: { interval: InstanceType<TimeIntervalCtor> };
}

export type TimeSliderSyncContext = {
  showTimeSlider: boolean;
  timeSliderLayer: number;
  timeSliderFullExtent: Record<string, number>;
  timeSliderTimeInterval: Record<string, number | string>;
  setTimeSliderConfig: (config: TimeSliderConfig | null) => void;
  signal: AbortSignal;
};

export async function syncTimeSliderConfig(
  { map }: MapContext,
  {
    showTimeSlider,
    timeSliderLayer,
    timeSliderFullExtent,
    timeSliderTimeInterval,
    setTimeSliderConfig,
    signal,
  }: TimeSliderSyncContext,
): Promise<void> {
  if (!map) return;

  if (!showTimeSlider) {
    if (!signal.aborted) setTimeSliderConfig(null);
    return;
  }

  const config = await buildTimeSliderConfig(
    map,
    timeSliderLayer,
    timeSliderFullExtent,
    timeSliderTimeInterval,
    signal,
  );

  if (!signal.aborted) setTimeSliderConfig(config);
}

/**
 * Pure async function — computes a TimeSliderConfig from Python model values
 * and ArcGIS layer info, then returns it for React to store in state and pass
 * declaratively as JSX props. Returns null when no valid time extent can be
 * determined.
 *
 * Interval priority: custom Python-provided interval -> layer's own interval ->
 * 10-hour default.
 */
async function buildTimeSliderConfig(
  map: Map,
  timeSliderLayer: number,
  fullExtent: Record<string, number>,
  timeInterval: Record<string, number | string>,
  signal: AbortSignal,
): Promise<TimeSliderConfig | null> {
  const [TimeExtent, TimeInterval] = await arcgisImport<
    [TimeExtentCtor, TimeIntervalCtor]
  >(["@arcgis/core/time/TimeExtent.js", "@arcgis/core/time/TimeInterval.js"]);

  if (signal.aborted) return null;

  const layer = map.layers?.getItemAt(timeSliderLayer) as {
    timeInfo?: {
      fullTimeExtent?: { start: Date; end: Date };
      interval?: unknown;
    };
  } | null;

  let mode: TimeSliderConfig["mode"] = "time-window";
  let newExtent: InstanceType<TimeExtentCtor> | null = null;

  if ("start" in fullExtent && "end" in fullExtent) {
    newExtent = new TimeExtent({
      start: new Date(fullExtent.start * 1000),
      end: new Date(fullExtent.end * 1000),
    });
    mode = fullExtent.start === fullExtent.end ? "instant" : "time-window";
  } else if ("end" in fullExtent) {
    mode = "cumulative-from-start";
    newExtent = new TimeExtent({
      start: undefined,
      end: new Date(fullExtent.end * 1000),
    });
  } else if ("start" in fullExtent) {
    mode = "cumulative-from-end";
    newExtent = new TimeExtent({
      start: new Date(fullExtent.start * 1000),
      end: undefined,
    });
  } else if (layer?.timeInfo?.fullTimeExtent) {
    const { start, end } = layer.timeInfo.fullTimeExtent;
    mode = start === end ? "instant" : "time-window";
    newExtent = new TimeExtent({ start, end });
  }

  if (!newExtent) return null;

  const { value, unit } = timeInterval;
  let stops: TimeSliderConfig["stops"];
  if (typeof value === "number" && typeof unit === "string") {
    stops = {
      interval: new TimeInterval({
        value: value as TimeIntervalProps["value"],
        unit: unit as TimeIntervalProps["unit"],
      }),
    };
  } else if (
    layer?.timeInfo?.interval !== null &&
    layer?.timeInfo?.interval !== undefined
  ) {
    stops = {
      interval: layer.timeInfo.interval as InstanceType<TimeIntervalCtor>,
    };
  } else {
    stops = { interval: new TimeInterval({ value: 10, unit: "hours" }) };
  }

  return { mode, fullTimeExtent: newExtent, timeExtent: newExtent, stops };
}
