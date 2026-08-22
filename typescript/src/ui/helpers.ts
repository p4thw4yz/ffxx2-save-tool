export function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  opts: { className?: string; text?: string; attrs?: Record<string, string> } = {},
  children: (Node | string)[] = [],
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (opts.className) node.className = opts.className;
  if (opts.text !== undefined) node.textContent = opts.text;
  if (opts.attrs) for (const [k, v] of Object.entries(opts.attrs)) node.setAttribute(k, v);
  for (const child of children) node.append(child);
  return node;
}

export function clear(node: Element): void {
  node.replaceChildren();
}

export function alertBox(message: string, kind: "info" | "success" | "error" = "info"): HTMLElement {
  return el("div", { className: `alert alert-${kind}`, text: message });
}

export function formatInt(n: number): string {
  return Math.trunc(n).toLocaleString("en-US");
}

export function formatHms(totalSeconds: number): string {
  const s = Math.trunc(totalSeconds || 0);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return `${h}h ${m}m`;
}

export function fieldValueToString(value: number | boolean): string {
  if (typeof value === "boolean") return value ? "true" : "false";
  return String(value);
}

export function downloadBytes(data: Uint8Array, filename: string): void {
  const blob = new Blob([data.buffer as ArrayBuffer], { type: "application/octet-stream" });
  const url = URL.createObjectURL(blob);
  const a = el("a", { attrs: { href: url, download: filename } });
  document.body.append(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
