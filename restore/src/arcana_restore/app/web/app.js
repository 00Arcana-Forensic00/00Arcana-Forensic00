/* Arcalume front end. Talks only to the local back end (pywebview bridge); no network. */
"use strict";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

// ---------------------------------------------------------------- bridge
const bridge = {
  ready: new Promise((resolve) => {
    if (window.pywebview && window.pywebview.api) return resolve();
    window.addEventListener("pywebviewready", () => resolve());
    if (window.__ARCALUME_TEST_BRIDGE__) resolve();
  }),
  async call(name, ...args) {
    await this.ready;
    if (window.pywebview && window.pywebview.api) return window.pywebview.api[name](...args);
    // Test harness only: the same methods served by a local test server.
    const r = await fetch("/__api/" + name, { method: "POST", body: JSON.stringify(args) });
    const j = await r.json();
    if (j.__error__) throw new Error(j.__error__);
    return j.result;
  },
};

// ---------------------------------------------------------------- state
const state = {
  info: null,
  docs: [],          // {id, name, width, height, thumb, status?}
  current: null,     // id
  result: null,      // last recover() result for current
  busy: false,
  lastFocus: null,
};

// ---------------------------------------------------------------- announcements
let toastTimer = 0;
function announce(msg, { assertive = false, toast = true } = {}) {
  // Screen readers get the message from a live region; sighted users from the toast.
  const live = assertive ? $("#alert") : $("#live");
  live.textContent = "";
  // Clearing first makes screen readers repeat identical messages.
  requestAnimationFrame(() => { live.textContent = msg; });
  if (toast || assertive) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), Math.max(4000, msg.length * 70));
  }
}
function errorText(e) { return (e && (e.message || e.toString())) || "Something went wrong."; }

// ---------------------------------------------------------------- text size
const TEXT_STEPS = [87.5, 100, 112.5, 125, 150, 175, 200];
let textStep = 1;
try { textStep = Math.min(TEXT_STEPS.length - 1, Math.max(0, +localStorage.getItem("arcalume.text") || 1)); } catch (_) {}
function applyText() {
  document.documentElement.style.fontSize = TEXT_STEPS[textStep] + "%";
  try { localStorage.setItem("arcalume.text", String(textStep)); } catch (_) {}
  $("#text-smaller").disabled = textStep === 0;
  $("#text-larger").disabled = textStep === TEXT_STEPS.length - 1;
}
function textSize(delta) {
  textStep = Math.min(TEXT_STEPS.length - 1, Math.max(0, textStep + delta));
  applyText();
  announce(`Text size ${TEXT_STEPS[textStep]}%`, { toast: false });
}

// ---------------------------------------------------------------- tabs
function selectTab(tab, focus = true) {
  $$('[role="tab"]').forEach((t) => {
    const on = t === tab;
    t.setAttribute("aria-selected", on);
    t.tabIndex = on ? 0 : -1;
    $("#" + t.getAttribute("aria-controls")).hidden = !on;
  });
  if (focus) tab.focus();
  document.title = `${tab.textContent} · ${state.info ? state.info.name : "Arcalume"}`;
}
function initTabs() {
  const tabs = $$('[role="tab"]');
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => selectTab(t));
    t.addEventListener("keydown", (e) => {
      let j = null;
      if (e.key === "ArrowRight") j = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft") j = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") j = 0;
      else if (e.key === "End") j = tabs.length - 1;
      if (j !== null) { e.preventDefault(); selectTab(tabs[j]); }
    });
  });
}

// ---------------------------------------------------------------- dialogs
function openDialog(d) {
  state.lastFocus = document.activeElement;
  d.showModal();
  const first = $("input:not([type=hidden]):not([readonly]), button.primary, button", d);
  if (first) first.focus();
}
function closeDialog(d) {
  d.close();
  if (state.lastFocus && document.contains(state.lastFocus)) state.lastFocus.focus();
}
document.addEventListener("close", (e) => {
  if (e.target.tagName === "DIALOG" && state.lastFocus && document.contains(state.lastFocus)) state.lastFocus.focus();
}, true);

// ---------------------------------------------------------------- license
function renderLicense() {
  const lic = state.info.license;
  const pro = lic.plan === "pro";
  document.body.dataset.plan = lic.plan;
  $("#plan-btn").dataset.plan = lic.plan;
  $("#plan-label").textContent = pro ? "Pro" : "Free";
  $("#plan-btn").setAttribute("aria-label", `Plan: ${pro ? "Pro" : "Free"}. Open License section`);
  $("#seal-pro").hidden = pro;
  $("#free-note").hidden = pro;
  let text;
  if (!pro) text = "You're on Free. Recovering, comparing, opening vaults and checking logs are included.";
  else if (lic.source === "store") text = "Pro, purchased through the app store. Thank you!";
  else text = `Pro, licensed to ${lic.licensee || "you"}${lic.expires ? `, valid until ${lic.expires}` : ""}.`;
  $("#lic-status").textContent = text;
  $("#lic-remove").hidden = lic.source !== "key";
  $("#lic-form .field").hidden = lic.source === "store";
  $("#lic-form button[type=submit]").hidden = lic.source === "store";
  $("#buy-link").hidden = pro;
}
function upgrade(reason) {
  $("#up-text").textContent = `${reason} Pro also removes the watermark from saved copies and handles several pages at once.`;
  openDialog($("#upgrade-dialog"));
}

// ---------------------------------------------------------------- opening files
function addDocs(res) {
  for (const d of res.docs) state.docs.push(d);
  for (const err of res.errors || []) announce(`${err.name} couldn't be opened: ${err.error}`, { assertive: true });
  if (res.docs.length) {
    renderPages();
    showWorkspace(true);
    selectDoc(res.docs[0].id);
    announce(res.docs.length === 1 ? `Opened ${res.docs[0].name}` : `Opened ${res.docs.length} pages`);
  }
}
async function chooseFiles() {
  try { addDocs(await bridge.call("pick_images")); } catch (e) { announce(errorText(e), { assertive: true }); }
}
async function loadSample() {
  try { addDocs(await bridge.call("load_sample")); } catch (e) { announce(errorText(e), { assertive: true }); }
}
function readAsBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",", 2)[1] || "");
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
}
async function openDropped(files) {
  const list = [...files].filter((f) => f.size > 0);
  if (!list.length) return;
  announce(`Opening ${list.length} file${list.length > 1 ? "s" : ""}…`, { toast: false });
  for (const f of list) {
    if (f.size > 100 * 1024 * 1024) { announce(`${f.name} is over 100 MB.`, { assertive: true }); continue; }
    try { addDocs(await bridge.call("open_bytes", f.name, await readAsBase64(f))); }
    catch (e) { announce(`${f.name}: ${errorText(e)}`, { assertive: true }); }
  }
}
function initDrop() {
  let depth = 0;
  // Stop the window from navigating to a dropped file.
  window.addEventListener("dragenter", (e) => { e.preventDefault(); depth++; document.body.classList.add("dragging"); });
  window.addEventListener("dragleave", () => { if (--depth <= 0) { depth = 0; document.body.classList.remove("dragging"); } });
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => {
    e.preventDefault(); depth = 0; document.body.classList.remove("dragging");
    if (e.dataTransfer && e.dataTransfer.files) openDropped(e.dataTransfer.files);
  });
  const drop = $("#drop");
  // Mouse convenience only; the buttons inside are the keyboard and screen-reader path.
  drop.addEventListener("click", (e) => { if (!e.target.closest("button")) chooseFiles(); });
}

// ---------------------------------------------------------------- page list (listbox)
const STATUS_WORDS = { stable: "No damage found", enhanced: "Lighting corrected", repaired: "Recovered",
  detected_not_repaired: "Not changed", skipped_damage_too_extensive: "Too damaged to change" };
function renderPages() {
  const ul = $("#page-list");
  ul.innerHTML = "";
  state.docs.forEach((d, i) => {
    const li = document.createElement("li");
    li.id = "page-" + d.id;
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", d.id === state.current);
    li.dataset.id = d.id;
    const img = document.createElement("img");
    img.src = d.thumb; img.alt = "";
    const span = document.createElement("span");
    span.className = "pname";
    span.textContent = d.name;
    const st = document.createElement("span");
    st.className = "pstat";
    st.textContent = d.status ? STATUS_WORDS[d.status] || d.status : `Page ${i + 1}`;
    span.appendChild(st);
    li.append(img, span);
    li.addEventListener("click", () => selectDoc(d.id));
    ul.appendChild(li);
  });
  if (state.current) ul.setAttribute("aria-activedescendant", "page-" + state.current);
}
function initPageList() {
  const ul = $("#page-list");
  ul.addEventListener("keydown", (e) => {
    const i = state.docs.findIndex((d) => d.id === state.current);
    let j = null;
    if (e.key === "ArrowDown") j = Math.min(state.docs.length - 1, i + 1);
    else if (e.key === "ArrowUp") j = Math.max(0, i - 1);
    else if (e.key === "Home") j = 0;
    else if (e.key === "End") j = state.docs.length - 1;
    else if (e.key === "Delete" && i >= 0) { e.preventDefault(); removeDoc(state.current); return; }
    if (j !== null && j !== i) { e.preventDefault(); selectDoc(state.docs[j].id); }
  });
  ul.addEventListener("focus", () => { const li = $("#page-" + state.current); if (li) li.classList.add("active-desc"); });
  ul.addEventListener("blur", () => $$("#page-list li").forEach((li) => li.classList.remove("active-desc")));
}
async function removeDoc(id) {
  const d = state.docs.find((x) => x.id === id);
  await bridge.call("close_doc", id);
  state.docs = state.docs.filter((x) => x.id !== id);
  announce(`Closed ${d ? d.name : "page"}`);
  if (!state.docs.length) { state.current = null; showWorkspace(false); $("#choose-btn").focus(); return; }
  renderPages();
  selectDoc(state.docs[0].id);
}
function showWorkspace(on) {
  $("#workspace").hidden = !on;
  $("#empty").hidden = on;
}

// ---------------------------------------------------------------- recovery + viewer
function options() {
  return { flatten: $("#opt-flatten").checked, fill_shadow: $("#opt-fill-shadow").checked };
}
async function selectDoc(id) {
  state.current = id;
  $$("#page-list li").forEach((li) => li.setAttribute("aria-selected", li.dataset.id === id));
  $("#page-list").setAttribute("aria-activedescendant", "page-" + id);
  const li = $("#page-" + id);
  if (li && document.activeElement === $("#page-list")) { $$("#page-list li").forEach((x) => x.classList.remove("active-desc")); li.classList.add("active-desc"); li.scrollIntoView({ block: "nearest" }); }
  await runRecover();
}
async function runRecover() {
  const id = state.current;
  if (!id) return;
  setWorking(true);
  try {
    const r = await bridge.call("recover", id, options());
    if (state.current !== id) return;  // user moved on
    state.result = r;
    const d = state.docs.find((x) => x.id === id);
    if (d) d.status = r.status;
    renderResult(r);
    renderPages();
    announce(`${r.name}: ${STATUS_WORDS[r.status] || r.status}. ${r.findings.length} findings.`, { toast: false });
  } catch (e) {
    announce(errorText(e), { assertive: true });
  } finally {
    setWorking(false);
  }
}
function setWorking(on) {
  state.busy = on;
  $("#working").hidden = !on;
  $("#stage").setAttribute("aria-busy", on);
}
const ICONS = {
  ok: '<svg viewBox="0 0 20 20" aria-hidden="true" focusable="false"><circle cx="10" cy="10" r="8.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M6 10.5l2.7 2.7L14.5 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  warn: '<svg viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path d="M10 2.5L18.5 17H1.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M10 8v4.2M10 14.6v.1" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
  info: '<svg viewBox="0 0 20 20" aria-hidden="true" focusable="false"><circle cx="10" cy="10" r="8.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 9v5M10 6.2v.1" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
};
const LEVEL_WORDS = { ok: "Done", warn: "Check", info: "Note" };
function renderResult(r) {
  const stage = $("#stage");
  const showMask = $("#show-mask").checked;
  $("#img-after").src = showMask ? r.overlay : r.after;
  $("#img-before").src = r.before;
  $("#img-after").alt = `${r.name}, after recovery${showMask ? ", with filled areas hatched in magenta" : ""}`;
  $("#img-before").alt = `${r.name}, original photo`;
  $("#mask-legend").hidden = !showMask;
  // reading order overlay (decorative; the same order is in the technical report)
  const svg = $("#order-layer");
  svg.setAttribute("viewBox", `0 0 ${r.width} ${r.height}`);
  svg.setAttribute("preserveAspectRatio", "none");
  const scale = Math.max(1, r.width / 900);
  svg.innerHTML = r.reading_order.map((n) =>
    `<rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}"/>` +
    `<text x="${n.x + 3 * scale}" y="${n.y + 14 * scale}" style="font-size:${14 * scale}px">${n.order + 1}</text>`).join("");
  stage.classList.toggle("show-order", $("#show-order").checked);
  // findings
  const ul = $("#findings");
  ul.innerHTML = "";
  for (const f of r.findings) {
    const li = document.createElement("li");
    li.dataset.level = f.level;
    li.innerHTML = ICONS[f.level] || ICONS.info;
    const p = document.createElement("span");
    const word = document.createElement("span");
    word.className = "sr-only";
    word.textContent = (LEVEL_WORDS[f.level] || "Note") + ": ";
    p.append(word, document.createTextNode(f.text));
    li.appendChild(p);
    ul.appendChild(li);
  }
  // technical summary
  const dl = $("#tech-summary");
  dl.innerHTML = "";
  const rows = [
    ["Status", r.status], ["Size", `${r.width} × ${r.height}`],
    ["Glare regions", r.stats.glare_regions], ["Black regions", r.stats.shadow_regions],
    ["Filled", `${(r.stats.filled_fraction * 100).toFixed(2)}% of pixels`], ["Text blocks", r.stats.blocks],
  ];
  for (const [k, v] of rows) {
    const dt = document.createElement("dt"); dt.textContent = k;
    const dd = document.createElement("dd"); dd.textContent = v;
    dl.append(dt, dd);
  }
  $("#report-json").textContent = JSON.stringify(r.report, null, 2);
  document.title = `${r.name} · ${state.info.name}`;
  setZoom($("#zoom").value);
}
function setMode(mode) {
  $("#stage").dataset.mode = mode;
  $("#split-control").hidden = mode !== "split";
  const radio = $(`#view-mode input[value="${mode}"]`);
  if (radio) radio.checked = true;
}
function setSplit(v) {
  v = Math.max(0, Math.min(100, Math.round(v)));
  $("#split").value = v;
  $("#split").setAttribute("aria-valuetext", `${v}% original, ${100 - v}% recovered`);
  $("#stage").style.setProperty("--split", v + "%");
}
function setZoom(z) {
  const stage = $("#stage");
  if (z === "fit") {
    // Whole page visible: as wide as the viewer allows, but no taller than the viewer.
    const r = state.result;
    const maxH = $("#stage-wrap").clientHeight || window.innerHeight * 0.72;
    stage.style.width = r ? `min(100%, ${Math.floor(maxH * r.width / r.height)}px)` : "100%";
    return;
  }
  const w = state.result ? Math.min(state.result.width, 1600) : 1000;
  stage.style.width = Math.round(w * parseFloat(z)) + "px";
}
function initViewer() {
  setMode("split"); setSplit(50);
  $$('#view-mode input').forEach((r) => r.addEventListener("change", () => setMode(r.value)));
  $("#split").addEventListener("input", (e) => setSplit(+e.target.value));
  $("#show-mask").addEventListener("change", () => { if (state.result) renderResult(state.result); });
  $("#show-order").addEventListener("change", () => $("#stage").classList.toggle("show-order", $("#show-order").checked));
  $("#zoom").addEventListener("change", (e) => setZoom(e.target.value));
  window.addEventListener("resize", () => setZoom($("#zoom").value));
  const stage = $("#stage");
  let dragging = false;
  const move = (e) => {
    const rect = stage.getBoundingClientRect();
    setSplit(((e.clientX - rect.left) / rect.width) * 100);
  };
  stage.addEventListener("pointerdown", (e) => {
    if (stage.dataset.mode !== "split") return;
    dragging = true; stage.setPointerCapture(e.pointerId); move(e);
  });
  stage.addEventListener("pointermove", (e) => { if (dragging) move(e); });
  stage.addEventListener("pointerup", () => { dragging = false; });
  for (const id of ["#opt-flatten", "#opt-fill-shadow"]) $(id).addEventListener("change", runRecover);
}

// ---------------------------------------------------------------- save / seal
async function saveCopy() {
  if (!state.current) return announce("Open a page first.", { assertive: true });
  try {
    const r = await bridge.call("export", state.current);
    if (r.cancelled) return;
    if (!r.ok) return announce(r.error || "Could not save.", { assertive: true });
    announce(`Saved to ${r.path}${r.watermarked ? " (with Free watermark)" : ""}.`);
  } catch (e) { announce(errorText(e), { assertive: true }); }
}
function passStrength(pw) {
  const min = state.info.min_passphrase;
  if (!pw) return [0, `At least ${min} characters. A few unrelated words work well.`];
  if (pw.length < min) return [1, `Too short: ${pw.length} of ${min} characters.`];
  const kinds = [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((r) => r.test(pw)).length;
  const words = pw.trim().split(/\s+/).length;
  if (pw.length >= 20 || (words >= 4 && pw.length >= 16)) return [4, "Strong."];
  if (pw.length >= 14 && kinds >= 2) return [3, "Good."];
  return [2, "OK. Longer is stronger."];
}
function openSeal() {
  if (!state.current) return announce("Open a page first.", { assertive: true });
  const lic = state.info.license;
  if (!lic.seal) return upgrade("Sealing pages into an encrypted vault with a custody log is part of Pro.");
  const n = state.docs.length;
  $("#seal-what").textContent = n > 1 && lic.batch
    ? `All ${n} open pages will be sealed, each with its untouched original, recovered copy and fill map.`
    : `${state.result ? state.result.name : "This page"} will be sealed with its untouched original, recovered copy and fill map.`;
  $("#seal-form").hidden = false;
  $("#seal-done").hidden = true;
  $("#sd-error").textContent = "";
  $("#sd-pass").value = ""; $("#sd-pass2").value = ""; $("#sd-ack").checked = false;
  updateStrength();
  openDialog($("#seal-dialog"));
}
function updateStrength() {
  const [score, text] = passStrength($("#sd-pass").value);
  $("#sd-meter").value = score;
  $("#sd-strength").textContent = text;
}
async function doSeal(e) {
  e.preventDefault();
  const err = $("#sd-error");
  err.textContent = "";
  const dir = $("#sd-dir").value.trim();
  const pw = $("#sd-pass").value, pw2 = $("#sd-pass2").value;
  const fail = (msg, el) => { err.textContent = msg; if (el) { el.setAttribute("aria-invalid", "true"); el.focus(); } };
  $$("#seal-form [aria-invalid]").forEach((x) => x.removeAttribute("aria-invalid"));
  if (!dir) return fail("Choose a vault folder.", $("#sd-dir"));
  if (pw.length < state.info.min_passphrase) return fail(`Use at least ${state.info.min_passphrase} characters.`, $("#sd-pass"));
  if (pw !== pw2) return fail("The two passphrases don't match.", $("#sd-pass2"));
  if (!$("#sd-ack").checked) return fail("Please confirm you understand a lost passphrase can't be recovered.", $("#sd-ack"));
  const ids = state.info.license.batch ? state.docs.map((d) => d.id) : [state.current];
  $("#sd-go").disabled = true;
  $("#sd-go").textContent = "Sealing…";
  announce(`Sealing ${ids.length} page${ids.length > 1 ? "s" : ""}…`, { toast: false });
  try {
    const r = await bridge.call("seal", ids, dir, pw, pw2);
    $("#sd-pass").value = ""; $("#sd-pass2").value = "";
    if (r.upgrade) { closeDialog($("#seal-dialog")); return upgrade(r.error); }
    if (!r.results) return fail(r.error || "Could not seal.");
    const ok = r.results.filter((x) => x.ok).length;
    const bad = r.results.filter((x) => !x.ok).map((x) => `${x.name}: ${x.error}`);
    $("#seal-form").hidden = true;
    $("#seal-done").hidden = false;
    $("#seal-done-text").textContent = `${ok} of ${r.results.length} sealed into ${r.vault_dir}. The custody log has ${r.ledger_entries} entr${r.ledger_entries === 1 ? "y" : "ies"} and checks out.` + (bad.length ? ` Not sealed: ${bad.join("; ")}` : "");
    $("#sd-head").value = r.ledger_head;
    state.sealedDir = r.vault_dir;
    $("#lg-dir").value = r.vault_dir;
    $("#seal-done-h").focus();
    announce(`${ok} of ${r.results.length} sealed.`, { toast: false });
  } catch (e2) {
    fail(errorText(e2));
  } finally {
    $("#sd-go").disabled = false;
    $("#sd-go").textContent = "Seal";
  }
}

// ---------------------------------------------------------------- vaults panel
function box(el, ok, title, detail) {
  el.innerHTML = "";
  const div = document.createElement("div");
  div.className = "box " + (ok ? "ok" : "bad");
  const s = document.createElement("strong");
  s.textContent = (ok ? "✓ " : "✕ ") + title;
  div.appendChild(s);
  if (detail) { const p = document.createElement("span"); p.textContent = detail; div.appendChild(p); }
  el.appendChild(div);
}
async function doOpenVault(e) {
  e.preventDefault();
  const out = $("#ov-result");
  const f = $("#ov-file").value.trim(), pw = $("#ov-pass").value, dir = $("#ov-out").value.trim();
  if (!f || !dir) return box(out, false, "Choose the sealed file and a folder to save to.");
  box(out, true, "Opening…");
  try {
    const r = await bridge.call("open_vault", f, pw, dir);
    $("#ov-pass").value = "";
    if (!r.ok) return box(out, false, "Couldn't open it.", r.error);
    box(out, true, "Opened and verified.", `${r.written.length} files saved to ${r.out_dir}. Every file matched its recorded fingerprint.`);
  } catch (e2) { box(out, false, "Couldn't open it.", errorText(e2)); }
}
async function doVerify(e) {
  e.preventDefault();
  const out = $("#lg-result");
  const dir = $("#lg-dir").value.trim();
  if (!dir) return box(out, false, "Choose a vault folder.");
  try {
    const r = await bridge.call("verify_ledger", dir, $("#lg-head").value);
    if (r.ok) box(out, true, "The custody log checks out.", `${r.entries} entries. Current fingerprint: ${r.head}`);
    else box(out, false, "The custody log does not check out.", `${r.message}. ${r.entries} entries read.`);
  } catch (e2) { box(out, false, "Couldn't check the log.", errorText(e2)); }
}
async function pickInto(input, method, ...args) {
  try { const p = await bridge.call(method, ...args); if (p) { $(input).value = p; $(input).focus(); } }
  catch (e) { announce(errorText(e), { assertive: true }); }
}

// ---------------------------------------------------------------- license form
async function doActivate(e) {
  e.preventDefault();
  const out = $("#lic-result");
  const key = $("#lic-key").value.trim();
  if (!key) return box(out, false, "Paste your license key first.");
  const r = await bridge.call("activate_license", key);
  if (!r.ok) return box(out, false, "That key didn't work.", r.error);
  state.info.license = r.license;
  $("#lic-key").value = "";
  renderLicense();
  box(out, true, "Pro is active. Thank you!");
}
async function doRemove() {
  const r = await bridge.call("deactivate_license");
  state.info.license = r.license;
  renderLicense();
  box($("#lic-result"), true, "License key removed from this device.");
}

// ---------------------------------------------------------------- keyboard shortcuts
function initShortcuts() {
  document.addEventListener("keydown", (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (mod && !e.altKey && (e.key === "o" || e.key === "O")) { e.preventDefault(); chooseFiles(); }
    else if (mod && (e.key === "s" || e.key === "S")) { e.preventDefault(); saveCopy(); }
    else if (mod && (e.key === "e" || e.key === "E")) { e.preventDefault(); openSeal(); }
    else if (mod && (e.key === "+" || e.key === "=")) { e.preventDefault(); textSize(1); }
    else if (mod && e.key === "-") { e.preventDefault(); textSize(-1); }
    else if (mod && e.key === "0") { e.preventDefault(); textStep = 1; applyText(); }
    else if (e.altKey && !mod && ["1", "2", "3"].includes(e.key)) { e.preventDefault(); setMode(["before", "split", "after"][+e.key - 1]); }
    else if (e.altKey && !mod && (e.key === "m" || e.key === "M" || e.code === "KeyM")) {
      e.preventDefault(); const c = $("#show-mask"); c.checked = !c.checked; c.dispatchEvent(new Event("change"));
      announce(c.checked ? "Showing filled areas" : "Hiding filled areas", { toast: false });
    }
    else if (e.key === "F1") { e.preventDefault(); openDialog($("#help-dialog")); }
  });
}

// ---------------------------------------------------------------- wiring
async function init() {
  applyText();
  initTabs(); initDrop(); initPageList(); initViewer(); initShortcuts();
  $("#text-smaller").addEventListener("click", () => textSize(-1));
  $("#text-larger").addEventListener("click", () => textSize(1));
  $("#help-btn").addEventListener("click", () => openDialog($("#help-dialog")));
  $("#help-close").addEventListener("click", () => closeDialog($("#help-dialog")));
  $("#plan-btn").addEventListener("click", () => selectTab($("#tab-license")));
  $("#choose-btn").addEventListener("click", (e) => { e.stopPropagation(); chooseFiles(); });
  $("#sample-btn").addEventListener("click", (e) => { e.stopPropagation(); loadSample(); });
  $("#add-btn").addEventListener("click", chooseFiles);
  $("#save-btn").addEventListener("click", saveCopy);
  $("#seal-btn").addEventListener("click", openSeal);
  $("#upgrade-link").addEventListener("click", (e) => { e.preventDefault(); selectTab($("#tab-license")); });
  $("#up-close").addEventListener("click", () => closeDialog($("#upgrade-dialog")));
  $("#up-go").addEventListener("click", () => { $("#upgrade-dialog").close(); selectTab($("#tab-license")); });
  $("#seal-form").addEventListener("submit", doSeal);
  $("#sd-cancel").addEventListener("click", () => closeDialog($("#seal-dialog")));
  $("#sd-close").addEventListener("click", () => closeDialog($("#seal-dialog")));
  $("#sd-pass").addEventListener("input", updateStrength);
  $("#sd-dir-btn").addEventListener("click", () => pickInto("#sd-dir", "pick_folder", "vault"));
  $("#sd-copy").addEventListener("click", async () => {
    const v = $("#sd-head").value;
    try { await navigator.clipboard.writeText(v); announce("Fingerprint copied."); }
    catch (_) { $("#sd-head").select(); announce("Selected. Press Ctrl+C to copy."); }
  });
  $("#sd-show").addEventListener("click", () => state.sealedDir && bridge.call("reveal", state.sealedDir));
  $$(".reveal-pass").forEach((b) => b.addEventListener("click", () => {
    const input = $("#" + b.getAttribute("aria-controls"));
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    b.setAttribute("aria-pressed", show);
    b.textContent = show ? "Hide" : "Show";
  }));
  $("#open-form").addEventListener("submit", doOpenVault);
  $("#ledger-form").addEventListener("submit", doVerify);
  $("#ov-file-btn").addEventListener("click", () => pickInto("#ov-file", "pick_vault_file"));
  $("#ov-out-btn").addEventListener("click", () => pickInto("#ov-out", "pick_folder", "output"));
  $("#lg-dir-btn").addEventListener("click", () => pickInto("#lg-dir", "pick_folder", "vault"));
  $("#lic-form").addEventListener("submit", doActivate);
  $("#lic-remove").addEventListener("click", doRemove);

  state.info = await bridge.call("app_info");
  $("#app-name").textContent = state.info.name;
  $("#tagline").textContent = state.info.tagline;
  $("#buy-link").href = state.info.buy_url;
  $("#sd-pass-hint").textContent = `At least ${state.info.min_passphrase} characters. It is never stored.`;
  if (state.info.defaults) {
    $("#sd-dir").value = state.info.defaults.vault_dir || "";
    $("#ov-out").value = state.info.defaults.out_dir || "";
    $("#lg-dir").value = state.info.defaults.vault_dir || "";
  }
  renderLicense();
  document.title = state.info.name;
  document.body.dataset.ready = "1";
}
init().catch((e) => announce(errorText(e), { assertive: true }));
