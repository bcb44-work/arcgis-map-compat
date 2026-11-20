export type DictionaryState = Record<string, unknown>;

// The current widget uses [latitude, longitude] for the Python-facing center.
export interface MapViewState {
  center: [number, number];
  zoom: number;
  extent?: DictionaryState;
  scale?: number;
}
