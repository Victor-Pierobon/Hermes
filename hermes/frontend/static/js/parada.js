/* lógica da tela da parada — funciona tanto em parada.html quanto em demo.html */

(function () {
  const STOP_ID = "parada_w3_sul_502";
  const DEFAULT_ROUTE = "110_UNB";

  let activeRequestId = null;
  let activeRouteName = "";

  const selectEl   = document.getElementById("route-select");
  const btnRequest = document.getElementById("btn-request");
  const btnCancel  = document.getElementById("btn-cancel");
  const statusEl   = document.getElementById("status-parada");

  // ── Controle da Tela de Login e Portal ──────────────────────────
  const btnLogin = document.getElementById("btn-login");
  const loginContainer = document.getElementById("login-container");
  const dashboardContainer = document.getElementById("dashboard-container");
  const paradaTitle = document.getElementById("parada-title");
  const cardSelector = document.getElementById("card-selector");
  const appFooter = document.getElementById("app-footer");
  const appChatBubble = document.getElementById("app-chat-bubble");

  if (btnLogin && loginContainer && dashboardContainer) {
    btnLogin.addEventListener("click", () => {
      loginContainer.style.display = "none";
      dashboardContainer.style.display = "block";
      if (paradaTitle) paradaTitle.style.display = "flex";
      if (cardSelector) cardSelector.style.display = "flex";
      if (appFooter) appFooter.style.display = "flex";
      if (appChatBubble) appChatBubble.style.display = "flex";
    });
  } else {
    // Se não houver tela de login (como na página parada.html isolada), mostra direto
    if (dashboardContainer) dashboardContainer.style.display = "block";
    if (paradaTitle) paradaTitle.style.display = "flex";
    if (appFooter) appFooter.style.display = "flex";
    if (appChatBubble) appChatBubble.style.display = "flex";
  }

  // ── Toggle do Saldo (Mostrar/Ocultar) ──────────────────────────
  const btnToggleBalance = document.getElementById("btn-toggle-balance");
  const balanceValue = document.getElementById("balance-value");
  const eyeIcon = document.getElementById("eye-icon");

  let balanceHidden = true;

  if (btnToggleBalance && balanceValue && eyeIcon) {
    btnToggleBalance.addEventListener("click", () => {
      balanceHidden = !balanceHidden;
      if (balanceHidden) {
        balanceValue.textContent = "R$ •••,••";
        eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />`;
      } else {
        balanceValue.textContent = "R$ 388,40";
        eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />`;
      }
    });
  }

  // ── popular select com linhas ──────────────────────────────────
  if (selectEl) {
    fetch("/api/data")
      .then(r => r.json())
      .then(data => {
        data.routes.forEach(route => {
          const opt = document.createElement("option");
          opt.value = route.route_id;
          opt.textContent = `${route.route_short_name} - ${route.route_long_name}`;
          if (route.route_id === DEFAULT_ROUTE) opt.selected = true;
          selectEl.appendChild(opt);
        });

        // modo demo: pré-seleciona sem interação
        const params = new URLSearchParams(window.location.search);
        if (params.get("demo") === "true") {
          selectEl.value = DEFAULT_ROUTE;
        }
      });
  }

  // ── socket ─────────────────────────────────────────────────────
  const socket = io();

  socket.on("request_resolved", ({ id }) => {
    if (id === activeRequestId) _setResolved();
  });

  socket.on("request_cancelled", ({ id }) => {
    if (id === activeRequestId) _resetState();
  });

  // ── botão solicitar ────────────────────────────────────────────
  if (btnRequest && selectEl) {
    btnRequest.addEventListener("click", () => {
      const route_id = selectEl.value || DEFAULT_ROUTE;
      activeRouteName = selectEl.options[selectEl.selectedIndex]?.text ?? "";
      socket.emit("button_request", { route_id, stop_id: STOP_ID });
      _speak(`Embarque assistido solicitado. Linha ${selectEl.options[selectEl.selectedIndex]?.text ?? ""}.`);
    });
  }

  socket.on("new_boarding_request", (payload) => {
    if (payload.origin !== "button") return;
    activeRequestId = payload.id;
    activeRouteName = payload.route_name;
    _setPending();
  });

  // ── botão cancelar ─────────────────────────────────────────────
  if (btnCancel) {
    btnCancel.addEventListener("click", () => {
      if (!activeRequestId) return;
      socket.emit("cancel_request", { id: activeRequestId });
      _speak("Solicitação cancelada.");
      _resetState();
    });
  }

  // ── estado ─────────────────────────────────────────────────────
  function _setPending() {
    if (btnRequest) btnRequest.disabled = true;
    if (btnCancel) btnCancel.classList.add("visible");
    _showStatus("Aguardando atendimento…", "pending");
  }

  function _setResolved() {
    activeRequestId = null;
    if (btnRequest) btnRequest.disabled = false;
    if (btnCancel) btnCancel.classList.remove("visible");
    _showStatus("Atendimento confirmado pelo motorista.", "resolved");

    const boardingInCtx = document.getElementById("boarding-in-progress");
    if (boardingInCtx) {
      const shortName = activeRouteName ? activeRouteName.split("—")[0].split("-")[0].trim() : "";
      
      // Calcular horário de chegada fictício (+5 min do horário atual)
      const now = new Date();
      const etaTime = new Date(now.getTime() + 5 * 60000);
      const etaString = etaTime.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

      boardingInCtx.querySelector(".boarding-title").textContent = `Embarque em andamento - Linha ${shortName}`;
      boardingInCtx.querySelector(".boarding-eta").textContent = `Previsão de chegada: ${etaString}`;
      boardingInCtx.style.display = "flex";
    }

    setTimeout(() => {
      if (statusEl) statusEl.classList.remove("visible");
    }, 4000);
  }

  function _resetState() {
    activeRequestId = null;
    if (btnRequest) btnRequest.disabled = false;
    if (btnCancel) btnCancel.classList.remove("visible");
    if (statusEl) statusEl.classList.remove("visible");

    const boardingInCtx = document.getElementById("boarding-in-progress");
    if (boardingInCtx) boardingInCtx.style.display = "none";
  }

  function _showStatus(msg, type) {
    if (statusEl) {
      statusEl.textContent = msg;
      statusEl.className = `status-parada visible ${type}`;
    }
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
