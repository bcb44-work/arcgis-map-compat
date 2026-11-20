/**
 * The ArcGIS CDN injects a global $arcgis object that provides an import() function for loading modules.
 * Defines this global and related types for TypeScript, as well as utility functions for loading the CDN
 * script and importing modules.
 */
declare global {
  interface Window {
    $arcgis?: {
      import: <T = unknown>(modules: string | readonly string[]) => Promise<T>;
    };
    /**
     * URL associated with $arcgisCdnPromise. Both must be page-global because
     * separate widget bundles and module evaluations share the same SDK.
     */
    $arcgisCdnBaseUrl?: string;
    /**
     * Promise that resolves when the ArcGIS CDN script has finished loading.
     * Used to ensure the script is only loaded once and to coordinate multiple calls to
     * arcgisImport() that may occur before the script has loaded.
     */
    $arcgisCdnPromise?: Promise<void>;
  }
}

console.log("***** ArcGIS CDN module loaded *****", new Date().toISOString());

/**
 * To be updated to the latest version of the ArcGIS JS API as needed.
 * Testing is required when changing the default version.
 * Despite semantic versioning, breaking changes can involuntarily occur in minor versions.
 */
const DEFAULT_ARCGIS_CDN_BASE_URL = "https://js.arcgis.com/5.1/index.js";

/**
 * Sets the ArcGIS CDN base URL and immediately begins loading the CDN script.
 * The first call wins — subsequent calls (e.g. from a second widget in the same notebook)
 * are no-ops, warning only for a different normalized URL.
 * window.$arcgisCdnPromise acts as the "already started" guard.
 */
export function configureArcGisCdn(baseUrl: string): void {
  if (window.$arcgisCdnPromise) {
    const normalizedUrl = normalizeArcGisBaseUrl(baseUrl);
    const configuredBaseUrl = getArcGisCdnBaseUrl();
    if (normalizedUrl !== configuredBaseUrl) {
      console.warn(
        `ArcGIS CDN: js_api_path "${normalizedUrl}" ignored — already configured with "${configuredBaseUrl}". ` +
        `Only the first js_api_path value is used.`,
      );
    }
    return;
  }
  window.$arcgisCdnBaseUrl = normalizeArcGisBaseUrl(baseUrl);
  void loadArcGisCdn();
}

/**
 * Returns the page-wide ArcGIS CDN base URL, or the default before configuration.
 */
export function getArcGisCdnBaseUrl(): string {
  return window.$arcgisCdnBaseUrl ?? DEFAULT_ARCGIS_CDN_BASE_URL;
}

/**
 * Normalizes the provided URL by trimming whitespace, resolving directory URLs to their
 * "index.js" entry point, and falling back to the default CDN for empty or root-like values.
 */
function normalizeArcGisBaseUrl(baseUrl?: string): string {
  const input = (baseUrl ?? "").trim();

  if (!input || input === "/" || input === "." || input === "./") {
    return DEFAULT_ARCGIS_CDN_BASE_URL;
  }

  const withoutTrailingSlash = input.replace(/\/+$/, "");
  if (!withoutTrailingSlash) {
    return DEFAULT_ARCGIS_CDN_BASE_URL;
  }

  if (/\/index\.js$/i.test(withoutTrailingSlash)) {
    return withoutTrailingSlash;
  }

  return `${withoutTrailingSlash}/index.js`;
}

/**
 * Loads the ArcGIS CDN script using the configured base URL.
 * Returns a promise that resolves when the script is loaded.
 */
function loadArcGisCdn(): Promise<void> {
  if (typeof window === "undefined" || typeof document === "undefined") {
    throw new Error("ArcGIS CDN loading requires a browser environment");
  }

  if (window.$arcgisCdnPromise) {
    console.log(
      "***** Found existing CDN load promise *****",
      new Date().toISOString(),
    );
    return window.$arcgisCdnPromise;
  }

  const configuredBaseUrl = getArcGisCdnBaseUrl();
  window.$arcgisCdnBaseUrl = configuredBaseUrl;

  if (window.$arcgis) {
    console.log(
      "***** Found existing $arcgis object *****",
      new Date().toISOString(),
    );
    window.$arcgisCdnPromise = Promise.resolve();
    return window.$arcgisCdnPromise;
  }

  console.log(
    "***** Creating new CDN load promise *****",
    new Date().toISOString(),
  );

  window.$arcgisCdnPromise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>(
      `script[data-arcgis-cdn="${configuredBaseUrl}"]`,
    );

    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(), { once: true });
      existingScript.addEventListener(
        "error",
        () => reject(new Error("Failed to load ArcGIS CDN script")),
        { once: true },
      );
      return;
    }

    const script = document.createElement("script");
    script.type = "module";
    script.src = configuredBaseUrl;
    script.dataset.arcgisCdn = configuredBaseUrl;
    script.addEventListener("load", () => resolve(), { once: true });
    script.addEventListener(
      "error",
      () =>
        reject(
          new Error(
            `Failed to load ArcGIS CDN script from ${configuredBaseUrl}`,
          ),
        ),
      { once: true },
    );
    document.head.appendChild(script);
  });

  return window.$arcgisCdnPromise;
}

/**
 * Wraps the global $arcgis.import() function, ensuring the CDN script is loaded first.
 * The module or constructors specified in the modules parameter are typed as unknown and must be cast by the caller.
 * Example usage:
 *   const [Map, MapView] = await arcgisImport<[typeof import("@arcgis/core/Map.js").default, typeof import("@arcgis/core/views/MapView.js").default]>([
 *     "@arcgis/core/Map.js",
 *     "@arcgis/core/views/MapView.js",
 *   ]);
 */
export async function arcgisImport<T = unknown>(
  modules: string | readonly string[],
): Promise<T> {
  await loadArcGisCdn();

  if (!window.$arcgis) {
    throw new Error("$arcgis is not available after the CDN script loaded");
  }

  return window.$arcgis.import<T>(modules);
}
