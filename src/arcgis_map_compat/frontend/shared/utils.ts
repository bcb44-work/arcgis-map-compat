import { arcgisImport } from "./arcgis-cdn";

type EsriConfigModule = typeof import("@arcgis/core/config.js").default;
type IdentityManagerModule =
  typeof import("@arcgis/core/identity/IdentityManager.js").default;
type PortalCtor = typeof import("@arcgis/core/portal/Portal.js").default;
type UrlUtilsModule = typeof import("@arcgis/core/core/urlUtils.js");

export async function initEsriConfig(portalRestUrl: string): Promise<void> {
  const [esriConfig] = await arcgisImport<[EsriConfigModule]>([
    "@arcgis/core/config.js",
  ]);
  esriConfig.portalUrl = portalRestUrl;
  // trustedServers enables credentialed requests. The ArcGIS CDN should not be
  // trusted, otherwise locale/json fetches can fail due to CORS + credentials.
  // Trust only the portal host used for authenticated org requests.
  const portalHost = safeOrigin(portalRestUrl);
  if (
    portalHost &&
    esriConfig.request?.trustedServers &&
    !esriConfig.request.trustedServers.includes(portalHost)
  ) {
    esriConfig.request.trustedServers.push(portalHost);
  }
}

function safeOrigin(url: string): string | null {
  try {
    return new URL(url).origin;
  } catch {
    return null;
  }
}

/**
 * Initializes authentication by registering tokens and proxy rules with the
 * ArcGIS API. Called once at startup and does not react to changes in its
 * parameters.
 */
export async function initAuth(
  authMode: string,
  portalRestUrl: string,
  portalToken: string,
  username: string,
  proxyRule: Record<string, string>,
): Promise<void> {
  const [IdentityManager, Portal, urlUtils] = await arcgisImport<
    [IdentityManagerModule, PortalCtor, UrlUtilsModule]
  >([
    "@arcgis/core/identity/IdentityManager.js",
    "@arcgis/core/portal/Portal.js",
    "@arcgis/core/core/urlUtils.js",
  ]);

  if (authMode === "tokenBased") {
    IdentityManager.registerToken({
      server: portalRestUrl,
      token: portalToken,
      userId: username,
    });
    new Portal({ authMode: "immediate", url: portalRestUrl })
      .load()
      .catch(() => {});
  } else {
    new Portal({ authMode: "anonymous" }).load().catch(() => {});
  }

  if (proxyRule && Object.keys(proxyRule).length > 0) {
    for (const [key, value] of Object.entries(proxyRule)) {
      urlUtils.addProxyRule({ proxyUrl: value, urlPrefix: key });
    }
  }
}
