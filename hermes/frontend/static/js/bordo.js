/* painel de bordo (demo.html): botão plano B, contador de passageiros e mapa da rota.
   Os cartões de alerta continuam sendo criados por motorista.js. */

(function () {
  const STOP_ID  = "parada_w3_sul_502";
  const ROUTE_ID = "110_UNB";
  const CAPACITY = 44;

  const socket = io();

  // ── Plano B: solicitar embarque pelo PC se o RFID falhar ─────────
  const btnPlanB = document.getElementById("btn-plan-b");
  if (btnPlanB) {
    btnPlanB.addEventListener("click", () => {
      socket.emit("button_request", { route_id: ROUTE_ID, stop_id: STOP_ID });
    });
  }

  // ── Contador de passageiros a bordo ──────────────────────────────
  const paxCountEl      = document.getElementById("pax-count");
  const priorityCountEl = document.getElementById("priority-count");
  const paxBarEl        = document.getElementById("pax-bar");
  const paxPctEl        = document.getElementById("pax-pct");
  const assistEl        = document.getElementById("assist-count");

  let pax = 24;        // ocupação inicial plausível
  let priority = 5;    // passageiros prioritários a bordo (idosos, gestantes, PcD…)
  let assisted = 0;    // embarques assistidos atendidos nesta sessão

  function renderPax() {
    const pct = Math.round((pax / CAPACITY) * 100);
    if (paxCountEl)      paxCountEl.textContent = pax;
    if (priorityCountEl) priorityCountEl.textContent = priority;
    if (paxBarEl)        paxBarEl.style.width = Math.min(100, pct) + "%";
    if (paxPctEl)        paxPctEl.textContent = pct + "%";
    if (assistEl)        assistEl.textContent = assisted;
  }

  function _pop(el) {
    if (!el) return;
    el.classList.remove("count-pop");
    void el.offsetWidth;       // reinicia a animação
    el.classList.add("count-pop");
  }

  function bumpPax() {
    if (pax < CAPACITY) pax++;
    priority++;          // embarque assistido = passageiro prioritário
    assisted++;
    renderPax();
    _pop(paxCountEl);
    _pop(priorityCountEl);
  }

  renderPax();

  // quando o motorista confirma o atendimento, o passageiro embarca
  socket.on("request_resolved", bumpPax);

  // ── Navegação: seta seguindo o trajeto + interface estilo Waze ───
  const routePath   = document.getElementById("route-path");
  const traveled    = document.getElementById("route-traveled");
  const navPos      = document.getElementById("nav-pos");
  const navArrow    = document.getElementById("nav-arrow-rot");
  const targetStop  = document.getElementById("target-stop");

  const banner   = document.getElementById("nav-banner");
  const navDist  = document.getElementById("nav-dist");
  const navIcon  = document.getElementById("nav-icon");
  const navInstr = document.getElementById("nav-instr");
  const navSub   = document.getElementById("nav-sub");
  const navMin   = document.getElementById("nav-eta-min");
  const navKm    = document.getElementById("nav-eta-km");
  const navArr   = document.getElementById("nav-eta-arrival");
  const navSpeed = document.getElementById("nav-speed");

  // ícones do banner (marcador padrão / acessibilidade)
  const ICON_MARKER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>';
  const ICON_ACCESS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="4" r="1"></circle><path d="M18 19h-4a2 2 0 0 1-2-2v-4a2 2 0 0 0-2-2H6"></path><circle cx="8" cy="19" r="2"></circle><path d="M12 13a4 4 0 0 1 4 4"></path></svg>';

  if (routePath && navPos) {
    const TOTAL_KM = 3.2;
    const TARGET   = [194, 150];           // posição do pino W3 Sul 502
    const MPP      = 7;                     // metros por unidade do viewBox (escala)
    const L        = routePath.getTotalLength();

    // horário de chegada fixo (agora + 8 min)
    const arrival = new Date(Date.now() + 8 * 60000);
    if (navArr) navArr.textContent = arrival.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

    const DUR = 17000;
    const start = performance.now();
    let alertShown = null;                  // evita reescrever o DOM a cada frame

    function frame(now) {
      const p   = ((now - start) % DUR) / DUR;
      const len = p * L;
      const pt  = routePath.getPointAtLength(len);
      const pt2 = routePath.getPointAtLength(Math.min(L, len + 1.5));
      const ang = Math.atan2(pt2.y - pt.y, pt2.x - pt.x) * 180 / Math.PI;

      navPos.setAttribute("transform", `translate(${pt.x.toFixed(2)},${pt.y.toFixed(2)})`);
      if (navArrow) navArrow.setAttribute("transform", `rotate(${ang.toFixed(1)})`);
      if (traveled) traveled.style.strokeDasharray = `${len.toFixed(1)} ${L.toFixed(1)}`;

      // alerta ativo no painel?
      const pending = !!document.querySelector(".alert-card:not(.resolved):not(.expired)");
      if (targetStop) targetStop.classList.toggle("active", pending);
      if (banner)     banner.classList.toggle("alert", pending);

      // distância até a parada monitorada
      const meters = Math.max(0, Math.round(Math.hypot(TARGET[0] - pt.x, TARGET[1] - pt.y) * MPP / 10) * 10);
      if (navDist) navDist.textContent = meters >= 1000
        ? (meters / 1000).toFixed(1).replace(".", ",") + " km"
        : meters + " m";

      // texto do banner (só atualiza quando o estado muda)
      if (pending !== alertShown) {
        alertShown = pending;
        if (navIcon)  navIcon.innerHTML = pending ? ICON_ACCESS : ICON_MARKER;
        if (navInstr) navInstr.textContent = pending ? "Embarque assistido solicitado" : "Parada monitorada à frente";
        if (navSub)   navSub.textContent = pending ? "W3 Sul 502 · atenção redobrada" : "W3 Sul 502 · Linha 110";
      }

      // ETA dinâmico
      if (navMin) navMin.textContent = Math.max(1, Math.round(8 * (1 - p)));
      if (navKm)  navKm.textContent = (TOTAL_KM * (1 - p)).toFixed(1).replace(".", ",") + " km";
      if (navSpeed) navSpeed.textContent = Math.round(36 + 6 * Math.sin(now / 650));

      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
})();
