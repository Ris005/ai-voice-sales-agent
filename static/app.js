// ---------------------------------------------------------------------------
// AI Voice Sales Agent — front-end controller
// ---------------------------------------------------------------------------
const $ = (sel) => document.querySelector(sel);
const api = async (path, opts) => {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
};

let CONFIG = { agent: "Aria", company: "Nimbus CRM", backend: "rule-based" };
let session = null;      // { id, leadId }
let timerInt = null;
let seconds = 0;
let voice = null;        // chosen SpeechSynthesis voice
let recog = null;        // SpeechRecognition instance
let listening = false;

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
async function boot() {
  try {
    CONFIG = await api("/api/config");
    $("#brandName").textContent = CONFIG.company;
    $("#agentName").textContent = CONFIG.agent;
    $("#backendName").textContent = CONFIG.backend;
    $("#callAvatar").textContent = CONFIG.agent[0] || "A";
  } catch (e) { /* keep defaults */ }
  await loadLeads();
  loadKnowledge();
  setupVoice();
  wireNav();
  wireCallControls();
}

// ---------------------------------------------------------------------------
// Leads + stats
// ---------------------------------------------------------------------------
async function loadLeads() {
  const { leads, stats } = await api("/api/leads");
  renderStats(stats);
  renderLeads(leads);
}

function renderStats(s) {
  const cards = [
    { n: s.total, l: "Total leads" },
    { n: s.pending, l: "Pending", cls: "" },
    { n: s.completed, l: "Completed" },
    { n: s.booked, l: "Meetings booked", cls: "accent" },
    { n: s.opted_out, l: "Opted out", cls: "hot" },
  ];
  $("#stats").innerHTML = cards
    .map((c) => `<div class="stat ${c.cls || ""}"><div class="n">${c.n}</div><div class="l">${c.l}</div></div>`)
    .join("");
}

const statusPill = (v) => {
  const k = (v || "").toLowerCase();
  if (k === "pending") return `<span class="pill pill-pending">pending</span>`;
  if (k === "completed") return `<span class="pill pill-completed">completed</span>`;
  if (k === "opted-out") return `<span class="pill pill-opted">opted-out</span>`;
  return `<span class="pill pill-muted">${v || "—"}</span>`;
};
const qualPill = (v) => {
  const k = (v || "").toLowerCase();
  if (k === "hot") return `<span class="pill pill-hot">hot</span>`;
  if (k === "warm") return `<span class="pill pill-warm">warm</span>`;
  if (k === "cold") return `<span class="pill pill-cold">cold</span>`;
  if (k === "unqualified") return `<span class="pill pill-muted">unqualified</span>`;
  return `<span class="muted">—</span>`;
};

function renderLeads(leads) {
  $("#leadsBody").innerHTML = leads
    .map((l) => {
      const pending = (l["Status"] || "").toLowerCase() === "pending";
      const optedOut = (l["Status"] || "").toLowerCase() === "opted-out";
      const btn = optedOut
        ? `<button class="btn-call" disabled>Do not call</button>`
        : `<button class="btn-call" data-id="${l["Lead ID"]}">📞 ${pending ? "Call" : "Recall"}</button>`;
      return `<tr>
        <td><div class="lead-name">${l["Name"] || "—"}</div><div class="lead-id">${l["Lead ID"] || ""}</div></td>
        <td>${l["Company"] || "—"}</td>
        <td class="muted">${l["Phone"] || "—"}</td>
        <td>${statusPill(l["Status"])}</td>
        <td>${l["Call Status"] ? `<span class="pill pill-muted">${l["Call Status"]}</span>` : `<span class="muted">—</span>`}</td>
        <td>${qualPill(l["Lead Qualification"])}</td>
        <td style="text-align:right">${btn}</td>
      </tr>`;
    })
    .join("");
  $("#leadsBody").querySelectorAll(".btn-call[data-id]").forEach((b) =>
    b.addEventListener("click", () => startCall(b.dataset.id))
  );
}

async function loadKnowledge() {
  try {
    const { knowledge } = await api("/api/knowledge");
    $("#kbContent").textContent = knowledge;
  } catch { $("#kbContent").textContent = "Could not load knowledge base."; }
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
function wireNav() {
  document.querySelectorAll(".nav-item").forEach((item) =>
    item.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
      item.classList.add("active");
      document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
      $("#view-" + item.dataset.view).classList.remove("hidden");
    })
  );
  $("#refreshBtn").addEventListener("click", loadLeads);
}

// ---------------------------------------------------------------------------
// Voice: text-to-speech + speech recognition
// ---------------------------------------------------------------------------
function setupVoice() {
  if ("speechSynthesis" in window) {
    const pick = () => {
      const voices = window.speechSynthesis.getVoices();
      voice =
        voices.find((v) => /female|samantha|aria|jenny|zira|google uk english female/i.test(v.name)) ||
        voices.find((v) => v.lang && v.lang.startsWith("en")) ||
        voices[0];
    };
    pick();
    window.speechSynthesis.onvoiceschanged = pick;
  }

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SR) {
    recog = new SR();
    recog.lang = "en-US";
    recog.interimResults = false;
    recog.maxAlternatives = 1;
    recog.onresult = (e) => {
      const text = e.results[0][0].transcript;
      $("#replyInput").value = text;
      sendReply();
    };
    recog.onend = () => setListening(false);
    recog.onerror = () => setListening(false);
  } else {
    $("#micLabel").textContent = "Mic n/a";
  }
}

function speak(text, onDone) {
  if (!("speechSynthesis" in window)) { onDone && onDone(); return; }
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  if (voice) u.voice = voice;
  u.rate = 1.02;
  u.pitch = 1.02;
  setState("speaking", "Agent speaking…");
  u.onend = () => { setState("idle", "Your turn"); onDone && onDone(); };
  window.speechSynthesis.speak(u);
}

function setListening(on) {
  listening = on;
  $("#micBtn").classList.toggle("active", on);
  $("#micLabel").textContent = on ? "Listening…" : "Speak";
  if (on) setState("listening", "Listening to prospect…");
}

function setState(cls, label) {
  const orb = $("#orb");
  orb.className = "orb " + (cls === "idle" ? "" : cls);
  $("#callState").textContent = label;
}

// ---------------------------------------------------------------------------
// Call lifecycle
// ---------------------------------------------------------------------------
async function startCall(leadId) {
  try {
    const data = await api("/api/call/start", { method: "POST", body: JSON.stringify({ lead_id: leadId }) });
    session = { id: data.session_id, leadId };
    openOverlay(data.lead);
    addBubble("agent", data.reply);
    speak(data.reply);
    startTimer();
  } catch (e) { toast(e.message); }
}

function openOverlay(lead) {
  $("#transcript").innerHTML = "";
  $("#outcome").classList.add("hidden");
  $("#outcome").innerHTML = "";
  $("#callName").textContent = lead["Name"] || "Lead";
  $("#callCompany").textContent = `${lead["Company"] || ""} · ${lead["Phone"] || ""}`;
  $("#callAvatar").textContent = (CONFIG.agent || "A")[0];
  $("#replyInput").value = "";
  $(".call-controls").classList.remove("hidden");
  $("#callOverlay").classList.remove("hidden");
  setState("idle", "Connecting…");
  setTimeout(() => $("#replyInput").focus(), 300);
}

function addBubble(who, text) {
  const el = document.createElement("div");
  el.className = "bubble " + who;
  el.innerHTML = `<div class="who">${who === "agent" ? CONFIG.agent : "Prospect"}</div>${escapeHtml(text)}`;
  $("#transcript").appendChild(el);
  $("#transcript").scrollTop = $("#transcript").scrollHeight;
}

async function sendReply() {
  const input = $("#replyInput");
  const text = input.value.trim();
  if (!text || !session) return;
  input.value = "";
  addBubble("prospect", text);
  setState("idle", "Thinking…");
  try {
    const data = await api("/api/call/turn", { method: "POST", body: JSON.stringify({ session_id: session.id, text }) });
    addBubble("agent", data.reply);
    speak(data.reply);
  } catch (e) { toast(e.message); }
}

async function endCall() {
  if (!session) { closeOverlay(); return; }
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  if (listening && recog) recog.stop();
  stopTimer();
  setState("idle", "Wrapping up…");
  try {
    const data = await api("/api/call/end", { method: "POST", body: JSON.stringify({ session_id: session.id }) });
    showOutcome(data.outcome);
    loadLeads();
  } catch (e) { toast(e.message); closeOverlay(); }
  session = null;
}

function showOutcome(o) {
  $(".call-controls").classList.add("hidden");
  setState("idle", "Call ended");
  const rows = [
    ["Call Status", o["Call Status"]],
    ["Qualification", o["Lead Qualification"]],
    ["Meeting", o["Meeting Date & Time"]],
    ["Follow-up", o["Follow-up Date"]],
    ["Requirements", o["Customer Requirements"], true],
    ["Objections", o["Objections Raised"], true],
    ["Summary", o["Conversation Summary"], true],
  ];
  const items = rows
    .map(([k, v, full]) =>
      `<div class="o-item ${full ? "full" : ""}"><div class="k">${k}</div><div class="v">${escapeHtml(v || "—")}</div></div>`
    )
    .join("");
  const el = $("#outcome");
  el.innerHTML = `<h3>✅ Saved to Excel CRM</h3><div class="outcome-grid">${items}</div>
    <button class="done-btn" id="doneBtn">Done</button>`;
  el.classList.remove("hidden");
  $("#doneBtn").addEventListener("click", closeOverlay);
  $("#transcript").scrollTop = $("#transcript").scrollHeight;
}

function closeOverlay() {
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  if (listening && recog) { try { recog.stop(); } catch {} }
  stopTimer();
  $("#callOverlay").classList.add("hidden");
  session = null;
}

// ---------------------------------------------------------------------------
// Controls wiring
// ---------------------------------------------------------------------------
function wireCallControls() {
  $("#sendBtn").addEventListener("click", sendReply);
  $("#replyInput").addEventListener("keydown", (e) => { if (e.key === "Enter") sendReply(); });
  $("#endBtn").addEventListener("click", endCall);
  $("#callClose").addEventListener("click", closeOverlay);
  $("#micBtn").addEventListener("click", () => {
    if (!recog) { toast("Speech recognition needs Chrome/Edge. Type the reply instead."); return; }
    if (listening) { recog.stop(); setListening(false); return; }
    try { window.speechSynthesis.cancel(); recog.start(); setListening(true); }
    catch { setListening(false); }
  });
}

// ---------------------------------------------------------------------------
// Timer + helpers
// ---------------------------------------------------------------------------
function startTimer() {
  seconds = 0;
  $("#callTimer").textContent = "00:00";
  timerInt = setInterval(() => {
    seconds++;
    const m = String(Math.floor(seconds / 60)).padStart(2, "0");
    const s = String(seconds % 60).padStart(2, "0");
    $("#callTimer").textContent = `${m}:${s}`;
  }, 1000);
}
function stopTimer() { clearInterval(timerInt); }

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

let toastT = null;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(toastT);
  toastT = setTimeout(() => t.classList.add("hidden"), 3200);
}

boot();
