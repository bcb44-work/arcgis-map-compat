// Isolate the SDK from notebook AMD loaders. Only static code goes into srcdoc.
function mount(model) {
  document.body.style.margin = "0";
  const container = document.createElement("div");
  container.style.height = "600px";
  const status = document.createElement("div");
  status.setAttribute("role", "status");
  status.textContent = "Waiting for the Python kernel...";
  document.body.append(status, container);

  let disposed = false;
  let view;
  let map;
  let sdk;

  function loadSdk() {
    return new Promise((resolve, reject) => {
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = "https://js.arcgis.com/5.1/esri/themes/light/main.css";
      document.head.append(css);
      const script = document.createElement("script");
      script.type = "module";
      script.src = "https://js.arcgis.com/5.1/core.js";
      const timeout = setTimeout(() => reject(new Error("SDK timeout")), 60000);
      script.onload = () => {
        clearTimeout(timeout);
        resolve(Promise.resolve().then(() => window.$arcgis.import([
          "@arcgis/core/WebMap.js", "@arcgis/core/views/MapView.js",
          "@arcgis/core/identity/IdentityManager.js", "@arcgis/core/config.js",
        ])));
      };
      script.onerror = () => {
        clearTimeout(timeout);
        reject(new Error("SDK unavailable"));
      };
      document.head.append(script);
    });
  }

  async function apply(message) {
    if (disposed) return;
    status.textContent = "Loading map...";
    sdk ??= loadSdk();
    const [WebMap, MapView, identity, config] = await sdk;
    if (disposed) return;
    for (const credential of message.credentials) identity.registerToken(credential);
    if (message.portal_url) config.portalUrl = message.portal_url;
    map = WebMap.fromJSON(message.definition);
    await map.load();
    if (disposed) return;
    view = new MapView({container, map});
    await view.when();
    if (disposed) return;
    const results = await Promise.allSettled(
      map.layers.toArray().map(layer => view.whenLayerView(layer)),
    );
    if (!disposed) {
      status.textContent = results.some(result => result.status === "rejected")
        ? "A layer could not load. Check access, URL expiry, CORS, and Parquet format."
        : "";
    }
  }

  function receive(message) {
    if (message.type !== "map" || disposed) return;
    model.off("msg:custom", receive);
    void apply(message).catch(() => {
      if (!disposed) status.textContent = "Map could not load. Check network access and credentials.";
    });
  }
  model.on("msg:custom", receive);
  model.send({type: "ready"});
  return () => {
    disposed = true;
    model.off("msg:custom", receive);
    view?.destroy();
    map?.destroy();
    sdk?.then(([, , identity]) => identity.destroyCredentials()).catch(() => {});
  };
}

function render({model, el}) {
  const frame = document.createElement("iframe");
  frame.title = "ArcGIS map";
  frame.style.cssText = "display:block;border:0;width:100%;height:630px";
  frame.srcdoc = `<!doctype html><html><head><meta charset="utf-8"></head>
    <body><script>window.mount = ${mount.toString()};<\/script></body></html>`;
  let cleanup;
  frame.onload = () => { cleanup = frame.contentWindow.mount(model); };
  el.append(frame);
  return () => {
    frame.onload = null;
    cleanup?.();
    frame.remove();
  };
}

export {render};
export default {render};
