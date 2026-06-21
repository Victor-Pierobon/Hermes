/* lógica do painel do motorista — funciona tanto em motorista.html quanto em demo.html */

(function () {
  const EXPIRE_MS = 90_000;
  const FADE_MS   = 10_000;

  const alertsArea = document.getElementById("alerts-area");
  const noAlerts   = document.getElementById("no-alerts");

  const socket = io();

  socket.on("new_boarding_request", (payload) => {
    _removeNoAlerts();
    _createCard(payload);
    _beep();
  });

  socket.on("request_resolved", ({ id }) => _markCard(id, "resolved"));
  socket.on("request_cancelled", ({ id }) => _removeCard(id));

  // ── criar cartão ───────────────────────────────────────────────
  function _createCard(p) {
    const time = new Date(p.timestamp).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    const card = document.createElement("div");
    card.className = "alert-card";
    card.dataset.id = p.id;
    card.setAttribute("role", "alert");
    card.innerHTML = `
      <div class="alert-route">♿ Embarque assistido</div>
      <div class="alert-stop">${_esc(p.stop_name)}</div>
      <div class="alert-meta">
        <span class="badge badge-pending" data-badge>Pendente</span>
        <span class="badge ${p.origin === 'rfid' ? 'badge-rfid' : 'badge-button'}">${p.origin === 'rfid' ? 'RFID' : 'Parada'}</span>
        <span class="badge" style="background:rgba(245,166,35,.15);color:var(--accent)">${_esc(p.route_name)}</span>
        <span class="alert-time">${time}</span>
      </div>
      <button class="btn-confirm" data-confirm="${_esc(p.id)}">Confirmar atendimento</button>
    `;

    card.querySelector("[data-confirm]").addEventListener("click", () => {
      socket.emit("resolve_request", { id: p.id });
    });

    alertsArea.prepend(card);

    // expiração automática
    const expireTimer = setTimeout(() => _markCard(p.id, "expired"), EXPIRE_MS);
    card.dataset.expireTimer = expireTimer;
  }

  // ── estados do cartão ──────────────────────────────────────────
  function _markCard(id, state) {
    const card = _findCard(id);
    if (!card) return;

    clearTimeout(Number(card.dataset.expireTimer));
    card.classList.add(state);

    const badge = card.querySelector("[data-badge]");
    if (badge) {
      badge.className = `badge badge-${state}`;
      badge.textContent = state === "resolved" ? "Atendido" : "Expirado";
    }

    const btn = card.querySelector("[data-confirm]");
    if (btn) btn.disabled = true;

    if (state === "expired") {
      setTimeout(() => _removeCard(id), FADE_MS);
    }
  }

  function _removeCard(id) {
    const card = _findCard(id);
    if (!card) return;
    clearTimeout(Number(card.dataset.expireTimer));
    card.remove();
    if (!alertsArea.querySelector(".alert-card")) _addNoAlerts();
  }

  // ── helpers ────────────────────────────────────────────────────
  function _findCard(id) {
    return alertsArea.querySelector(`[data-id="${id}"]`);
  }

  function _removeNoAlerts() {
    if (noAlerts) noAlerts.remove();
  }

  function _addNoAlerts() {
    if (!alertsArea.querySelector(".no-alerts")) {
      const el = document.createElement("p");
      el.className = "no-alerts";
      el.id = "no-alerts";
      el.textContent = "Nenhuma solicitação ativa.";
      alertsArea.appendChild(el);
    }
  }

  function _esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ── bipe via Web Audio API ─────────────────────────────────────
  function _beep() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.25);
    } catch (_) {}
  }
})();
