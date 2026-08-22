import { marked } from "marked";
import readmeRaw from "../../README.md?raw";
import { el, clear } from "./helpers";

export function renderInfoTab(container: HTMLElement): void {
  clear(container);
  const body = el("div", { className: "markdown-body" });
  body.innerHTML = marked.parse(readmeRaw, { async: false }) as string;
  const card = el("div", { className: "card" }, [
    el("div", { className: "card-title", text: "About this tool" }),
    el("div", { className: "card-subtitle", text: "The project README, rendered here so it's always in reach." }),
    body,
  ]);
  container.append(card);
}
