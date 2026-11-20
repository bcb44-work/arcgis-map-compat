// Run the existing renderer in its own realm so notebook AMD loaders do not
// interfere with the ArcGIS CDN. The original anywidget model is passed through.
async function mountWidget(source, css, context) {
  const style = document.createElement("style");
  style.textContent = css;
  document.head.append(style);
  document.body.style.margin = "0";

  const url = URL.createObjectURL(new Blob([source], { type: "text/javascript" }));
  try {
    const { default: widget } = await import(url);
    return await widget.render({ ...context, el: document.body });
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function render(context) {
  const { model, el, signal } = context;
  const frame = document.createElement("iframe");
  frame.title = "ArcGIS map";
  Object.assign(frame.style, {
    display: "block",
    border: "0",
    width: "100%",
    height: "600px",
  });
  frame.srcdoc = `<!doctype html><html><head><meta charset="utf-8"></head>
    <body><script>window.mountWidget = ${mountWidget.toString()};<\/script></body></html>`;

  let cleanup;
  function dispose() {
    cleanup?.();
    cleanup = undefined;
    frame.remove();
  }

  const loaded = new Promise((resolve) => {
    frame.addEventListener("load", resolve, { once: true });
    signal.addEventListener("abort", resolve, { once: true });
  });
  signal.addEventListener("abort", dispose, { once: true });
  el.append(frame);
  await loaded;
  if (signal.aborted) return;

  cleanup = await frame.contentWindow.mountWidget(
    model.get("_renderer_esm"), model.get("_css"), context,
  );
  if (signal.aborted) dispose();
  return dispose;
}

export default { render };
