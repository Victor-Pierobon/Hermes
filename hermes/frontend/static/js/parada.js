/* lógica da tela da parada — funciona tanto em parada.html quanto em demo.html */

(function () {
  const STOP_ID = "parada_w3_sul_502";
  const DEFAULT_ROUTE = "110_UNB";

  let activeRequestId = null;

  const selectEl   = document.getElementById("route-select");
  const btnRequest = document.getElementById("btn-request");
  const btnCancel  = document.getElementById("btn-cancel");
  const statusEl   = document.getElementById("status-parada");

  // ── popular select com linhas ──────────────────────────────────
  fetch("/api/data")
    .then(r => r.json())
    .then(data => {
      data.routes.forEach(route => {
        const opt = document.createElement("option");
        opt.value = route.route_id;
        opt.textContent = `${route.route_short_name} — ${route.route_long_name}`;
        if (route.route_id === DEFAULT_ROUTE) opt.selected = true;
        selectEl.appendChild(opt);
      });

      // modo demo: pré-seleciona sem interação
      const params = new URLSearchParams(window.location.search);
      if (params.get("demo") === "true") {
        selectEl.value = DEFAULT_ROUTE;
      }
    });

  // ── socket ─────────────────────────────────────────────────────
  const socket = io();

  socket.on("request_resolved", ({ id }) => {
    if (id === activeRequestId) _setResolved();
  });

  socket.on("request_cancelled", ({ id }) => {
    if (id === activeRequestId) _resetState();
  });

  // ── botão solicitar ────────────────────────────────────────────
  btnRequest.addEventListener("click", () => {
    const route_id = selectEl.value || DEFAULT_ROUTE;
    socket.emit("button_request", { route_id, stop_id: STOP_ID });
    _speak(`Embarque assistido solicitado. Linha ${selectEl.options[selectEl.selectedIndex]?.text ?? ""}.`);
  });

  socket.on("new_boarding_request", (payload) => {
    if (payload.origin !== "button") return;
    activeRequestId = payload.id;
    _setPending();
  });

  // ── botão cancelar ─────────────────────────────────────────────
  btnCancel.addEventListener("click", () => {
    if (!activeRequestId) return;
    socket.emit("cancel_request", { id: activeRequestId });
    _speak("Solicitação cancelada.");
    _resetState();
  });

  // ── estado ─────────────────────────────────────────────────────
  function _setPending() {
    btnRequest.disabled = true;
    btnCancel.classList.add("visible");
    _showStatus("Aguardando atendimento…", "pending");
  }

  function _setResolved() {
    activeRequestId = null;
    btnRequest.disabled = false;
    btnCancel.classList.remove("visible");
    _showStatus("Atendimento confirmado pelo motorista.", "resolved");
    setTimeout(() => statusEl.classList.remove("visible"), 4000);
  }

  function _resetState() {
    activeRequestId = null;
    btnRequest.disabled = false;
    btnCancel.classList.remove("visible");
    statusEl.classList.remove("visible");
  }

  function _showStatus(msg, type) {
    statusEl.textContent = msg;
    statusEl.className = `status-parada visible ${type}`;
  }

  // ── Web Speech API ─────────────────────────────────────────────
  function _speak(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = "pt-BR";
    utt.rate = 0.95;
    window.speechSynthesis.speak(utt);
  }
})();
