const thread = document.getElementById("thread");
const form = document.getElementById("ask-form");
const input = document.getElementById("chat-input");
const sendButton = document.getElementById("send-button");

function nowLabel() {
  return new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function linkify(text) {
  return escapeHtml(text).replace(
    /https?:\/\/\S+/g,
    (url) => `<a class="underline break-all" href="${url}" target="_blank" rel="noopener">${url}</a>`
  );
}

function addUser(question) {
  const block = document.createElement("section");
  block.className = "flex justify-end";
  block.innerHTML = `
    <div class="max-w-[85%] sm:max-w-[70%] bg-inverse-surface text-inverse-on-surface rounded-xl rounded-br-[4px] px-4 py-2 shadow-sm">
      <p class="text-sm">${escapeHtml(question)}</p>
      <div class="mt-1 flex items-center justify-end gap-1 text-[11px] font-semibold opacity-80">
        <span>${nowLabel()}</span>
        <span class="material-symbols-outlined text-[13px]">done_all</span>
      </div>
    </div>`;
  thread.appendChild(block);
  block.scrollIntoView({ block: "end" });
}

function addLoading() {
  const block = document.createElement("section");
  block.id = "loading";
  block.className = "flex items-start gap-3";
  block.innerHTML = `
    <div class="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center shrink-0">
      <span class="material-symbols-outlined text-primary text-[18px]">sync</span>
    </div>
    <div class="bg-white rounded-xl rounded-bl-[4px] px-4 py-2 shadow-sm flex items-center gap-2">
      <span class="text-[11px] font-semibold text-outline">Checking the scheme documents</span>
      <span class="w-2.5 h-2.5 rounded-full bg-primary-container animate-pulse"></span>
      <span class="w-2.5 h-2.5 rounded-full bg-primary-container animate-pulse"></span>
      <span class="w-2.5 h-2.5 rounded-full bg-primary-container animate-pulse"></span>
    </div>`;
  thread.appendChild(block);
  block.scrollIntoView({ block: "end" });
}

function sourceUrl(data) {
  const match = (data.text || "").match(/https?:\/\/\S+/);
  if (match) return match[0].replace(/[).,]+$/, "");
  const chunk = (data.chunks || []).find((item) => item.url);
  return chunk ? chunk.url : "";
}

function sourcesList(chunks) {
  if (!chunks || !chunks.length) return "<p class=\"text-sm text-on-surface-variant\">No chunks were retrieved.</p>";
  return chunks.map((chunk) => `
    <div class="py-2 border-t border-surface-container first:border-0">
      <div class="text-sm font-semibold">${chunk.rank}. ${escapeHtml(chunk.scheme || "")}</div>
      ${chunk.url ? `<a class="text-xs break-all text-primary" href="${escapeHtml(chunk.url)}" target="_blank" rel="noopener">${escapeHtml(chunk.url)}</a>` : ""}
      <p class="text-xs text-on-surface-variant mt-1">${escapeHtml(chunk.preview || "")}</p>
    </div>`).join("");
}

function addAnswer(data) {
  document.getElementById("loading")?.remove();
  const advice = data.kind === "advice" || data.kind === "returns";
  const url = sourceUrl(data);
  const updated = (data.text.match(/Last updated from sources:\s*\S+/) || [""])[0];
  const body = data.text.replace(updated, "").trim();
  const resolved = data.question && data.question !== data.asked
    ? `<p class="text-xs text-outline">Understood as: ${escapeHtml(data.question)}</p>`
    : "";
  const block = document.createElement("section");
  block.className = "flex items-start gap-3";
  block.innerHTML = `
    <div class="w-8 h-8 rounded-full bg-surface-container-high flex items-center justify-center shrink-0 mt-1">
      <span class="material-symbols-outlined ${advice ? "text-secondary" : "text-primary"} text-[18px]">${advice ? "policy" : "verified"}</span>
    </div>
    <div class="flex-1 ${advice ? "bg-surface-container-low" : "bg-white"} rounded-xl rounded-bl-[4px] p-4 shadow-sm flex flex-col gap-3">
      ${advice ? `<div class="flex items-center gap-1 text-secondary text-sm font-semibold"><span class="material-symbols-outlined text-[18px]">info</span><span>Advice boundary notice</span></div>` : `<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-primary-fixed/30 text-on-primary-fixed-variant text-[11px] font-semibold w-fit"><span class="w-1.5 h-1.5 rounded-full bg-primary"></span>Official scheme fact</span>`}
      ${resolved}
      <div class="text-sm leading-relaxed">${linkify(body).replaceAll("\n", "<br>")}</div>
      <div class="flex flex-wrap items-center justify-between gap-2">
        ${url ? `<a class="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container text-[11px] font-semibold" href="${escapeHtml(url)}" target="_blank" rel="noopener"><span class="material-symbols-outlined text-[16px] text-primary">description</span><span>Source document</span><span class="material-symbols-outlined text-[14px]">open_in_new</span></a>` : ""}
        <span class="text-xs text-outline">${escapeHtml(updated)}</span>
      </div>
      <details class="text-sm">
        <summary class="cursor-pointer text-[11px] font-semibold text-on-surface-variant">Sources</summary>
        <div class="mt-2">${sourcesList(data.chunks)}</div>
      </details>
    </div>`;
  thread.appendChild(block);
  block.scrollIntoView({ block: "end" });
}

async function ask(question) {
  const trimmed = question.trim();
  if (!trimmed || sendButton.disabled) return;
  input.value = "";
  addUser(trimmed);
  addLoading();
  sendButton.disabled = true;
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: trimmed }),
    });
    const data = await response.json();
    data.asked = trimmed;
    addAnswer(data);
  } catch (error) {
    addAnswer({ text: "The answer service failed. No answer was generated.", kind: "error", chunks: [], asked: trimmed });
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  ask(input.value);
});

document.querySelectorAll(".prompt").forEach((button) => {
  button.addEventListener("click", () => ask(button.dataset.q));
});

document.querySelectorAll(".nav-link").forEach((button) => {
  button.addEventListener("click", () => {
    if (button.dataset.topic === "assistant") {
      input.focus();
      return;
    }
    addUser(button.textContent.trim());
    addAnswer({
      text: "This demo only answers factual questions from the loaded scheme documents. It does not calculate SIPs or compare returns.",
      kind: "advice",
      chunks: [],
      asked: button.textContent.trim(),
    });
  });
});

document.getElementById("clear-chat").addEventListener("click", async () => {
  await fetch("/api/clear", { method: "POST" });
  thread.replaceChildren();
  input.value = "";
  input.focus();
});
