# SPEC — HERMES (protótipo hackathon)

Quebra técnica de tudo que precisa ser construído.
Cada item é uma tarefa atômica: pode ser feita, testada e marcada como concluída de forma independente.

---

## Estrutura de pastas a criar

```
hermes/
├── backend/
│   └── app.py
├── frontend/
│   ├── demo.html
│   ├── parada.html
│   ├── motorista.html
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       ├── parada.js
│   │       └── motorista.js
├── rfid/
│   └── rfid_reader.py
├── data/
│   └── transit_data.json
├── requirements.txt
└── SPEC.md
```

---

## Marco 1 — Fluxo mínimo com botão ✅

> Critério de conclusão: clicar o botão na tela da parada e ver o alerta aparecer no painel do motorista, sem recarregar página.

### 1.1 Ambiente e dependências

- [x] Criar a pasta `hermes/` e subpastas conforme estrutura acima
- [x] Criar e ativar virtualenv Python (`python -m venv venv`)
- [x] Instalar dependências: `flask flask-socketio` (async_mode threading, sem eventlet)
- [x] Criar `requirements.txt` com as versões fixadas (`pip freeze > requirements.txt`)

### 1.2 Servidor (`backend/app.py`)

- [x] Subir Flask com Flask-SocketIO
- [x] Rota `GET /` → serve `frontend/parada.html`
- [x] Rota `GET /motorista` → serve `frontend/motorista.html`
- [x] Rota `GET /demo` → serve `frontend/demo.html` (tela unificada para o pitch)
- [x] Rota `POST /api/rfid` → recebe `{ uid }`, gera solicitação e emite evento SocketIO
- [x] Evento SocketIO `button_request` → recebe `{ route_id, stop_id }`, monta payload e emite `new_boarding_request` para todos os clientes
- [x] Payload de `new_boarding_request`:
  ```json
  {
    "id": "<uuid>",
    "route_id": "110_UNB",
    "route_name": "110 — UnB / Rodoviária",
    "stop_id": "parada_w3_sul_502",
    "stop_name": "W3 Sul 502",
    "origin": "button",
    "timestamp": "<ISO8601>"
  }
  ```
- [x] Confirmar que o servidor sobe sem erro em `localhost:5000`

### 1.3 Dados estáticos (`data/transit_data.json`)

- [x] Criar JSON com 4 linhas reais do DF no formato GTFS-friendly
- [x] Linhas: 110 (UnB), 0.111 (Circular Asa Sul), 107 (Asa Norte), 160 (Ceilândia)
- [x] Servidor carrega esse JSON na inicialização e o expõe via `GET /api/data`

### 1.4 Tela da parada (`frontend/`)

- [x] `<select>` populado com as linhas vindas de `/api/data`
- [x] Botão grande "Solicitar Embarque Assistido"
- [x] Ao clicar: emitir evento `button_request` via SocketIO com `route_id` e `stop_id` fixo da demo
- [x] Desabilitar o botão enquanto a solicitação está ativa (evitar spam)

### 1.5 Tela do motorista (`frontend/`)

- [x] Área de alertas inicialmente vazia com texto placeholder "Nenhuma solicitação ativa"
- [x] Ao receber `new_boarding_request`: criar um cartão de alerta com `route_name`, `stop_name` e horário
- [x] Remover o placeholder quando o primeiro alerta chegar

### 1.6 Tela unificada para o pitch (`frontend/demo.html`)

- [x] Layout lado a lado: parada à esquerda, painel do motorista à direita
- [x] Reutiliza a mesma lógica de `parada.js` e `motorista.js` (sem duplicar código)
- [x] Label visual distinguindo os dois lados ("Parada — W3 Sul 502" / "Painel do Motorista")

---

## Marco 2 — Acessibilidade (alma da ideia) ✅

> Critério: a demo conta a história sozinha, mesmo sem explicar em voz alta.

### 2.1 Áudio na parada (Web Speech API)

- [x] Ao solicitar embarque, falar via `speechSynthesis` (idioma `pt-BR`):
  `"Embarque assistido solicitado. Linha [nome da linha]."`
- [x] Garantir que o áudio só dispara após interação do usuário (requisito do browser para autoplay)
- [x] Ao cancelar solicitação, falar: `"Solicitação cancelada."`

### 2.2 Bipe de atenção no painel do motorista

- [x] Gerar um tom curto (~200ms, ~880Hz) via Web Audio API quando um alerta chega
- [x] Não usar arquivo de áudio externo — gerar programaticamente (sem dependência)

### 2.3 Rótulo neutro (LGPD)

- [x] O cartão de alerta exibe apenas `"Embarque assistido"` — nunca diagnóstico, deficiência ou condição
- [x] Nome do passageiro: não exibir. A associação UID → perfil fica só no servidor
- [x] Informações no cartão: linha, parada, horário da solicitação, origem (`Parada` ou `RFID`)

### 2.4 Acessibilidade da própria interface

- [x] Foco visível no teclado em todos os elementos interativos (`:focus-visible`)
- [x] Contraste mínimo WCAG AA — paleta escura com texto #f0f0f0 sobre #0d0d0d
- [x] `aria-live="polite"` na área de confirmação da parada
- [x] `aria-live="assertive"` na área de alertas do motorista
- [x] Botão de solicitar com `aria-label` descritivo

---

## Marco 3 — Ciclo de vida do alerta ✅

> Critério: o painel do motorista não acumula alertas eternamente; cada um tem estado claro.

### 3.1 Estados de um alerta

- [x] Definir 3 estados: `pendente` (laranja) → `atendido` (verde) → `expirado` (cinza)
- [x] Cada estado tem cor de borda e badge distintos

### 3.2 Confirmação pelo motorista

- [x] Botão "Confirmar atendimento" em cada cartão de alerta
- [x] Ao clicar: emitir `resolve_request` com `{ id }` via SocketIO
- [x] Servidor emite `request_resolved` com `{ id }` para todos os clientes
- [x] Tela da parada recebe `request_resolved` e libera o botão de solicitar novamente

### 3.3 Expiração automática

- [x] Após 90 segundos sem confirmação, o alerta passa para estado `expirado`
- [x] Implementado com `setTimeout` no cliente
- [x] Alerta expirado some após mais 10 segundos (removido do DOM)

### 3.4 Cancelamento pelo passageiro

- [x] Botão "Cancelar" na tela da parada enquanto há solicitação ativa
- [x] Emite `cancel_request` com `{ id }` para o servidor
- [x] Servidor emite `request_cancelled` para todos; alerta no painel é removido
- [x] Áudio: `"Solicitação cancelada."`

---

## Marco 4 — Raspberry Pi + RC522 (hardware físico)

> Critério: encostar o cartão no leitor dispara o mesmo alerta que o botão. O botão continua funcionando se o Pi falhar.

### 4.1 Setup do Raspberry Pi

- [ ] Gravar Raspberry Pi OS com Desktop pelo Raspberry Pi Imager (configurar wi-fi e SSH no Imager)
- [ ] `sudo apt update && sudo apt full-upgrade`
- [ ] Habilitar SPI: `sudo raspi-config` → Interface Options → SPI

### 4.2 Conexão física RC522

- [ ] Conectar RC522 ao Pi conforme pinout (SDA→GPIO8, SCK→GPIO11, MOSI→GPIO10, MISO→GPIO9, GND→GND, RST→GPIO25, 3.3V→3.3V)
- [ ] Verificar conexão antes de instalar software

### 4.3 Script do Pi (`rfid/rfid_reader.py`)

- [ ] Instalar `mfrc522` e `RPi.GPIO` e `requests` no Pi
- [ ] Ler UID do cartão em loop (somente leitura — nunca escrever no cartão)
- [ ] `SERVER_URL` configurável por variável de ambiente ou constante no topo do arquivo
- [ ] Ao ler UID: fazer `POST /api/rfid` com `{ uid, stop_id: "parada_w3_sul_502" }`
- [ ] Log no terminal: `[RFID] UID lido: XXXX → POST enviado`
- [ ] Aguardar 2 segundos após leitura antes de aceitar novo cartão (debounce)

### 4.4 Servidor — endpoint `/api/rfid` ✅

- [x] Receber `{ uid, stop_id }`
- [x] Mapear UID para linha padrão (qualquer UID desconhecido assume linha 110 — UnB)
- [x] Montar o mesmo payload de `new_boarding_request`, com `origin: "rfid"`
- [x] Emitir o evento para todos os clientes via SocketIO

### 4.5 Rede

- [ ] Testar Pi e notebook na mesma rede (hotspot do notebook como fallback)
- [ ] Testar leitura 20 vezes seguidas antes do dia da apresentação
- [ ] Documentar IP fixo ou hostname do notebook para o script do Pi

**Próximo passo:** criar `rfid/rfid_reader.py` e conectar o hardware.

---

## Marco 5 — Polimento visual e dados ✅

> Critério: a tela é apresentável; juiz vê cuidado no detalhe.

### 5.1 Visual geral

- [x] Paleta de alto contraste (fundo #0d0d0d, texto #f0f0f0, destaque âmbar)
- [x] Tipografia forte e grande (17px corpo, 22px títulos)
- [x] Botão "Solicitar" impossível de ignorar (largura total, 20px, bold)
- [x] Logo/nome "HERMES" no topo das telas individuais

### 5.2 Cartão de alerta do motorista

- [x] Ícone ♿ no cartão
- [x] Linha em destaque (badge âmbar)
- [x] Parada + horário em tamanho menor
- [x] Badge de origem (`Parada` ou `RFID`) com cores distintas
- [x] Animação de entrada `slide-in` via CSS puro

### 5.3 Dados reais do DF

- [x] 4 linhas com nomes e códigos plausíveis (formato GTFS: `route_id`, `route_short_name`, `route_long_name`)
- [x] Parada da demo: W3 Sul 502
- [x] Linha 110 — UnB pré-selecionada no `<select>`

### 5.4 Modo demo

- [x] Parâmetro `?demo=true` na URL pré-seleciona linha 110 automaticamente

---

## Marco 6 — Pitch e blindagem

> Critério: a apresentação pode falhar em qualquer ponto técnico e ainda assim ser entregue.

### 6.1 Vídeo de backup

- [ ] Gravar screencast da demo completa funcionando (com RFID se possível)
- [ ] Abrir o vídeo em aba separada antes de subir ao palco
- [ ] Se tudo falhar: roda o vídeo e segue o roteiro normalmente

### 6.2 Roteiro do pitch (3 minutos)

- [ ] Escrever palavra por palavra; cronometrar
- [ ] **0:00–1:00** — problema humano: sinalização de embarque é visual; quem não enxerga não sabe qual ônibus chegou; o motorista não sabe que aquela pessoa precisa daquela linha
- [ ] **1:00–1:30** — a virada: o HERMES inverte a lógica; o sistema avisa o motorista
- [ ] **1:30–2:30** — demo ao vivo: encostar o cartão → áudio → alerta aparece
- [ ] **2:30–3:00** — visão: geofencing, GTFS-Realtime, grafo, Lei 7.836/2025
- [ ] Ensaiar 3+ vezes cronometrado

### 6.3 Slides de visão (o que NÃO está no protótipo)

- [ ] Slide: fluxo completo (parada → servidor → frota via GTFS-Realtime → motorista)
- [ ] Slide: geofencing — raio de 500m, alerta quando ônibus se aproxima
- [ ] Slide: grafo da malha (Neo4j) e matriz Origem-Destino
- [ ] Slide: despacho dinâmico / ML para atrasos em cascata
- [ ] Apresentar como roadmap, não como promessa

### 6.4 Checklist do dia

- [ ] Servidor rodando e `/demo` aberta em tela cheia
- [ ] Som do notebook ligado
- [ ] Pi testado antes de subir ao palco (5 leituras de teste)
- [ ] Vídeo de backup aberto em outra aba
- [ ] Linha 110 pré-selecionada

---

## Marco 7 — Tela de Comparação Visual (`/versus`)

> Critério: abrir `/versus` e ver duas animações lado a lado, em loop, contando a história do problema e da solução sem nenhuma palavra ser dita.

**Objetivo no pitch:** usar durante o "problema humano" (0:00–1:00) — o juiz vê ao vivo o ônibus passando sem parar vs. o sistema avisando o motorista.

---

### 7.0 Testes (escrever ANTES da implementação — TDD)

- [x] `test_versus_returns_200` — `GET /versus` responde 200
- [x] `test_versus_contains_before_canvas` — HTML contém `id="c-before"`
- [x] `test_versus_contains_after_canvas` — HTML contém `id="c-after"`
- [x] `test_versus_contains_comparison_title` — HTML contém a palavra "Compara"

---

### 7.1 Rota no servidor (`backend/app.py`)

- [x] Adicionar `GET /versus` → `send_from_directory(FRONTEND_DIR, "versus.html")`
- [x] Confirmar que os 4 testes do 7.0 passam

---

### 7.2 Estrutura HTML (`frontend/versus.html`)

Arquivo auto-contido (CSS inline + JS inline). Nenhuma dependência externa além de `style.css`.

- [x] Header: logo `HERMES` + título "Comparação: Sistema Atual vs HERMES" + link `← Demo ao vivo` para `/demo`
- [x] Layout de 3 colunas: `[painel esquerdo] [divisor VS] [painel direito]`
- [x] Painel esquerdo: tag `Hoje` (cinza), título, `<canvas id="c-before" width="560" height="230">`, bloco de stats, card de métrica vermelha ("~32 min espera")
- [x] Painel direito: tag `HERMES` (âmbar), título, `<canvas id="c-after" width="560" height="230">`, bloco de stats, card de métrica verde ("< 2 min resposta")
- [x] Divisor central: badge circular "VS"

---

### 7.3 CSS adicional (inline em `versus.html`)

- [x] `.comparison-layout` — `display: grid; grid-template-columns: 1fr auto 1fr`
- [x] `.panel-comp` — padding interno
- [x] `.panel-tag` — pequeno badge colorido acima do título
  - `.tag-before` — cinza
  - `.tag-after` — âmbar (usando `var(--accent)`)
- [x] `.key-metric` — card com borda colorida e valor grande
  - `.metric-before` — borda/texto vermelho
  - `.metric-after` — borda/texto verde
- [x] `.vs-badge` — círculo com "VS" no divisor
- [x] `canvas` — `width: 100%; height: auto; border-radius: 8px; background: #0a0c14`

---

### 7.4 Constantes e helpers JS

- [x] `CYCLE = 12000` — duração do ciclo em ms
- [x] `ROAD_TOP_FRAC = 0.60` — road começa a 60% da altura do canvas
- [x] `SIDE_TOP_FRAC = 0.48` — calçada começa a 48%
- [x] `STOP_X_FRAC = 0.32` — ponto de parada a 32% da largura
- [x] `BUS_W = 100, BUS_H = 50` — dimensões do ônibus em px
- [x] `function lerp(a, b, t)` — interpolação linear com clamping
- [x] `function easeOut(t)` — `1 - (1-t)²` (desacelera ao final)
- [x] `function easeIn(t)` — `t²` (acelera ao final)
- [x] `function fadeIn(t, start, end)` — alpha 0→1 entre dois pontos do ciclo
- [x] `function fadeOut(t, start, end)` — alpha 1→0 entre dois pontos do ciclo

---

### 7.5 Funções de desenho no canvas

Cada função recebe `(ctx, W, H, ...)` — sem estado global de desenho.

- [x] **`drawBackground(ctx, W, H)`** — céu + estrelas + calçada + pista + marcações
- [x] **`drawBusStop(ctx, W, H, glowAlpha)`** — poste + teto + banco; âmbar quando ativado
- [x] **`drawPerson(ctx, W, H, state, animT)`** — 5 estados: waiting/waving/sad/tap/boarding
- [x] **`drawBus(ctx, W, H, busX, variant, alertAlpha)`** — carroceria + janelas + rodas + badge ♿
- [x] **`drawRipple(ctx, x, y, progress)`** — 3 anéis âmbar expandindo do ponto de toque
- [x] **`drawSignalPulse(ctx, fromX, toX, y, t)`** — linha tracejada animada com `lineDashOffset`
- [x] **`drawLabel(ctx, W, H, text, yPos, color, alpha)`** — texto centralizado com fade
- [x] **`drawWaitClock(ctx, W, H, alpha)`** — relógio analógico + "+32 min"

---

### 7.6 Timelines de animação

Ciclo de 12 segundos. `t` vai de `0.0` a `1.0`.

**`renderBefore(canvas, t)` — painel esquerdo:**

| t (fração) | O que acontece |
|---|---|
| 0.00 – 0.08 | Cena parada: pessoa na calçada, relógio de horário fixo visível |
| 0.08 – 0.62 | Ônibus entra pela direita e atravessa em velocidade constante (`lerp` linear) |
| 0.40 – 0.54 | Ônibus está perto da parada → `state = 'waving'` (pessoa acena) |
| 0.54 – 0.75 | Ônibus saiu → `state = 'sad'` (pessoa sozinha, chateada) |
| 0.68 – 0.90 | `drawWaitClock` aparece (fade in/out) |
| 0.54 – 0.85 | Label vermelho: `"✗ Ônibus passou sem identificar solicitação"` |
| 0.90 – 1.00 | Fade out geral para o reset |

**`renderAfter(canvas, t)` — painel direito:**

| t (fração) | O que acontece |
|---|---|
| 0.00 – 0.06 | Cena parada: pessoa aguardando |
| 0.06 – 0.20 | `state = 'tap'` → pessoa toca o cartão → `drawRipple` no poste |
| 0.18 – 0.38 | `drawSignalPulse` viaja da parada para a direita (onde o ônibus virá) |
| 0.35 – 0.60 | Ônibus entra pela direita com `alertAlpha` crescendo → badge âmbar visível |
| 0.12 – 0.60 | Posição do ônibus: `lerp(W+20, stopX - BUS_W/2, easeOut(...))` (desacelera ao chegar) |
| 0.60 – 0.72 | Ônibus parado no ponto (`busX = stopX - BUS_W/2`) |
| 0.70 – 0.82 | `state = 'boarding'` → pessoa some gradualmente |
| 0.75 – 0.95 | Ônibus parte: `lerp(stopX - BUS_W/2, -BUS_W-20, easeIn(...))` (acelera ao sair) |
| 0.80 – 0.96 | Label verde: `"✓ Embarque assistido concluído"` |
| 0.95 – 1.00 | Fade out geral para o reset |

---

### 7.7 Loop de animação

- [x] `startTime = performance.now()` na inicialização
- [x] Função `tick()` chamada via `requestAnimationFrame`
- [x] `t = ((now - startTime) % CYCLE) / CYCLE`
- [x] Chamar `renderBefore` e `renderAfter`, depois `renderRouteBefore` e `renderRouteAfter`
- [x] Nenhum estado global mutável além de `startTime`

---

### 7.8 Atualizar README

- [x] Adicionar `/versus` na tabela de URLs

---

## Marco 8 — Seção de Eficiência Operacional GTFS-Realtime na `/versus`

> Critério: a seção de eficiência abaixo da comparação de acessibilidade mostra claramente o problema de bunching vs. headway regulado — sem precisar de explicação verbal.

**Objetivo no pitch:** reforçar que o HERMES não é só acessibilidade — é modernização de toda a operação. O ponto de venda principal para a gestão do DFTrans.

**Onde:** nova seção adicionada ao final de `frontend/versus.html`, abaixo da comparação de acessibilidade já existente. Nenhuma nova rota necessária.

---

### 8.0 Testes (escrever ANTES — TDD)

Adicionar na classe `TestVersusPage` em `tests/test_routes.py`:

- [x] `test_versus_contains_route_before_canvas` — HTML contém `id="c-route-before"`
- [x] `test_versus_contains_route_after_canvas` — HTML contém `id="c-route-after"`
- [x] `test_versus_contains_gtfs_section` — HTML contém `"GTFS"`
- [x] `test_versus_contains_bunching_concept` — HTML contém `"bunching"`

---

### 8.1 HTML — nova seção em `versus.html`

Inserir abaixo do `</div>` que fecha `.versus-layout`:

```html
<div class="eff-section">
  <div class="eff-header">
    <h3>Eficiência Operacional — GTFS-Realtime</h3>
    <p>O HERMES elimina o <strong>bunching</strong> (acúmulo de ônibus) e distribui a frota
       dinamicamente com base em demanda real</p>
  </div>
  <div class="eff-panels">
    <div class="eff-panel">
      <span class="v-tag v-tag-before">Sem GTFS-Realtime</span>
      <canvas id="c-route-before" width="520" height="165"></canvas>
      <div class="eff-metric eff-metric-before">
        Headway irregular — gap de até 35 min num corredor de 12 min
      </div>
    </div>
    <div class="v-divider" style="padding-top:56px"><div class="vs-badge">VS</div></div>
    <div class="eff-panel">
      <span class="v-tag v-tag-after">Com HERMES + GTFS-Realtime</span>
      <canvas id="c-route-after" width="520" height="165"></canvas>
      <div class="eff-metric eff-metric-after">
        Headway regulado dinamicamente — intervalo médio de ~10 min
      </div>
    </div>
  </div>
</div>
```

---

### 8.2 CSS adicional (inline em `versus.html`)

- [ ] `.eff-section` — `padding: 0 24px 16px; border-top: 1px solid var(--border)`
- [ ] `.eff-header` — `padding: 14px 12px 10px`; `h3` 15px bold; `p` 12px `var(--text-muted)`
- [ ] `.eff-panels` — `display: grid; grid-template-columns: 1fr auto 1fr`
- [ ] `.eff-panel` — `padding: 0 12px`
- [ ] `.eff-metric` — `margin-top: 8px; font-size: 12px; padding: 8px 12px; border-radius: 6px`
- [ ] `.eff-metric-before` — fundo vermelho translúcido, borda vermelha, texto `#ef4444`
- [ ] `.eff-metric-after` — fundo verde translúcido, borda verde, texto `var(--green)`

---

### 8.3 Constantes da rota (JS)

```javascript
const STOPS_X    = [55, 148, 240, 333, 425];  // x das 5 paradas
const ROUTE_YFRAC = 0.56;                      // rota a 56% da altura do canvas
const MBUS_W = 30, MBUS_H = 18;               // mini ônibus
```

---

### 8.4 Funções de desenho da rota (JS)

- [ ] **`drawRouteBackground(ctx, W, H)`**
  - Fundo `#080b12`
  - Linha de rota horizontal em `H * ROUTE_YFRAC`, cor `#303038`, espessura 2px
  - Faixa de "asfalto" abaixo da linha (retângulo `#1a1a1e`)
  - Para cada stop em `STOPS_X`: poste vertical (18px para cima) + capelo (rect 12x4px no topo)

- [ ] **`drawPassengersAtStop(ctx, stopX, routeY, count, color)`**
  - Até 6 círculos de raio 4px, empilhados acima do capelo do poste
  - Layout: 3 colunas × 2 linhas, offset `stopX ± 10`, separação vertical 12px
  - Se `count > 6`: texto `+N` acima

- [ ] **`drawMiniBus(ctx, x, routeY, bodyColor, accentColor, label, badgeText)`**
  - Sair se `x > W+12` ou `x < -MBUS_W-12`
  - Sombra elíptica em `routeY`
  - Carroceria `roundRect` com borda `accentColor`
  - 2 janelas retangulares na parte superior
  - Rótulo (`'A'`, `'B'`, `'C'`) abaixo da carroceria, 7px monospace
  - Badge âmbar acima quando `badgeText` não é null: `roundRect` âmbar + texto preto 8px

- [ ] **`drawHeadwayLabel(ctx, x1, x2, routeY, text, color)`**
  - Não desenhar se `x2 <= x1` ou ambos fora da tela
  - Linha tracejada `setLineDash([3,3])` nos dois lados do gap, cor `color + '88'`
  - Badge centralizado no meio do gap: rect arredondado com `color` translúcido + texto

- [ ] **`drawGtfsPulse(ctx, W, H, routeY)`**
  - Pulso independente de `t`, baseado em `performance.now()`: `pulse = (sin(now/300)+1)/2`
  - Para cada stop: linha vertical acima do poste (30px) com `rgba(245,166,35, pulse*0.3)`
  - Ponto pulsante no topo de cada linha
  - Label `"● GTFS-Realtime ativo"` no canto superior esquerdo, cor interpolada âmbar↔verde

---

### 8.5 `renderRouteBefore(canvas, t)` — bunching

**Posições dos ônibus:**

| Ônibus | x inicial | velocidade relativa | efeito |
|---|---|---|---|
| A | 510 | 1.0× (referência) | lidera |
| B | 400 | 1.18× | mais rápido → alcança A (bunching) |
| C | 210 | 0.78× | mais lento → cai para trás (gap) |

```javascript
const bAx = lerp(510, -35, t);
const bBx = lerp(400, -35, t * 1.18);
const bCx = lerp(210, -35, t * 0.78);
```

**Cálculo de demanda nos stops:**
- Para cada stop `sx`: verificar se está entre `bCx + 30` e `bBx - 30` (no gap)
  - Se no gap: `demand = min(6, round(t * gapSize / 65))` — cresce com o gap
  - Se perto do bunching (`sx < bBx + 60 && sx > bAx - 30`): `demand = round(t * 1.5)` — baixo, recém atendido
  - Caso contrário: `demand = min(3, round(t * 2))`
- Cor dos passageiros: verde `count ≤ 1`, âmbar `count ≤ 3`, laranja `count ≤ 5`, vermelho `count > 5`

**Headway labels:**
- Gap A-B: `round((bAx - bBx) / 570 * 35)` minutos → cor vermelha quando < 5 min
- Gap B-C: `round((bBx - bCx) / 570 * 35)` minutos → cor vermelha quando > 20 min

**Label de diagnóstico:** `"Bunching: ônibus se acumulam"` canto superior esquerdo

---

### 8.6 `renderRouteAfter(canvas, t)` — dispatch HERMES

**Fases:**

| t | O que acontece |
|---|---|
| 0.00 – 0.22 | Tendência inicial de bunching (leve) — mesma situação que o BEFORE |
| 0.22 – 0.40 | HERMES detecta → badge `"⚡ adj"` no ônibus B; label "HERMES: ajuste de headway detectado" |
| 0.40 – 1.00 | Espaçamento normalizado — todos os gaps ~130px |

**Posições dos ônibus:**
```javascript
const bAx = lerp(510, -35, t);
let bBx, bCx;

if (t < 0.22) {
  // leve bunching antes do dispatch
  bBx = lerp(390, -35, t * 1.08);
  bCx = lerp(220, -35, t * 0.92);
} else {
  // após dispatch: espaçamento fixo com A
  bBx = bAx - 145;
  bCx = bAx - 290;
}
```

**Passageiros:** `demand = min(2, round(t * 1.5))` para todos os stops — cor sempre verde

**Dispatch badge:** `showDispatch = t > 0.22 && t < 0.42`

**GTFS pulse:** `drawGtfsPulse(ctx, W, H, routeY)` — sempre visível

**Headway labels:** sempre `"~10 min"`, cor verde

**Label de dispatch:** texto âmbar `"⚡ HERMES: ajuste de headway detectado"`, centralizado, alpha = `fadeIn(t,0.22,0.30) * fadeOut(t,0.36,0.44)`

---

### 8.7 Atualizar `tick()`

```javascript
const cRouteBefore = document.getElementById('c-route-before');
const cRouteAfter  = document.getElementById('c-route-after');

function tick() {
  const t = ((performance.now() - startTime) % CYCLE) / CYCLE;
  renderBefore(cBefore, t);
  renderAfter(cAfter, t);
  renderRouteBefore(cRouteBefore, t);   // ← novo
  renderRouteAfter(cRouteAfter, t);     // ← novo
  requestAnimationFrame(tick);
}
```

---

### 8.8 Armadilhas específicas desta seção

- **`lineDashOffset`** — sempre resetar para `0` após `drawHeadwayLabel`; se não, afeta o próximo stroke do mesmo canvas
- **Demanda calculada a partir das posições dos ônibus** — não hardcodado; é mais robusto e visualmente coerente com a animação real
- **`performance.now()` no `drawGtfsPulse`** — cria batimento independente do `t` do ciclo; é intencional (representa o feed sempre ativo), não é um bug
- **Altura do canvas de rota (165px)** — compacto de propósito; não aumentar para não quebrar o layout de tela cheia no pitch
- **Ônibus B começa a fazer bunching no AFTER também** — é intencional no período 0.00–0.22, mostra que o problema existe; o ponto é que o HERMES intervém antes que piore

---

## Marco 9 — Mapa de Demanda em Horário de Pico (`/demanda`)

> Critério: abrir `/demanda` e ver um mapa animado de rotas do DF com relógio avançando pelo dia — durante o pico, o painel esquerdo mostra passageiros sendo deixados para trás; o painel direito mostra o HERMES despachando ônibus extras e zerando o overflow.

**Argumento de venda:** GTFS-Realtime permite saber em tempo real onde a demanda está crescendo. Hoje a escala de frota é feita semanas antes por planilha. Com HERMES, a frota responde ao dia real.

**Onde:** nova página `/demanda`, novo arquivo `frontend/demanda.html`, nova rota em `app.py`.

---

### 9.0 Testes (escrever ANTES — TDD)

Nova classe `TestDemandaPage` em `tests/test_routes.py`:

- [x] `test_demanda_returns_200`
- [x] `test_demanda_contains_before_canvas` — `id="c-demand-before"`
- [x] `test_demanda_contains_after_canvas` — `id="c-demand-after"`
- [x] `test_demanda_contains_peak_concept` — palavra `"pico"` no HTML
- [x] `test_demanda_contains_gtfs_reference` — palavra `"GTFS"` no HTML

---

### 9.1 Rota no servidor

```python
@app.route("/demanda")
def demanda():
    return send_from_directory(FRONTEND_DIR, "demanda.html")
```

---

### 9.2 Estrutura HTML (`frontend/demanda.html`)

Mesma estrutura de `versus.html` como base:

- Header: logo + `"Mapa de Demanda — Horário de Pico"` + link `← Comparação` para `/versus`
- Layout 3 colunas: `[painel-before] [VS] [painel-after]`
- Canvas `id="c-demand-before"` width=560 height=380
- Canvas `id="c-demand-after"` width=560 height=380
- Tags: `"Hoje — Escala Fixa"` (cinza) / `"Com HERMES + GTFS-Realtime"` (âmbar)
- Stats:
  - Before: `"Frota fixa independente de horário"` / `"Pico: capacidade excedida"`
  - After:  `"Demanda monitorada em tempo real"` / `"Frota ajustada dinamicamente"`
- Cards de métrica:
  - Before: vermelho — `"~45% dos passageiros aguardam o próximo ônibus no pico"`
  - After:  verde   — `"Frota +80% no pico — capacidade alinhada à demanda"`

---

### 9.3 Dados das rotas (JS)

```javascript
const ROUTES = [
  { label: 'Asa Norte',    angle: -75, color: '#4a9eff' },
  { label: 'Asa Sul',      angle: 105, color: '#a855f7' },
  { label: 'Ceilândia',    angle: 195, color: '#f97316' },
  { label: 'Sobradinho',   angle:  15, color: '#06b6d4' },
];
const HUB_LABEL   = 'Rodoviária';
const STOP_DISTS  = [65, 115, 160];   // px do hub a cada parada
const DEMAND_CAP  = 4;                // capacidade máxima sem overflow
const CYCLE_DEMANDA = 14000;          // ms por ciclo (6h→22h)
```

---

### 9.4 Relógio e intensidade de pico (JS)

```javascript
function getHour(t) { return 6 + t * 16; }   // 6h a 22h

function peakIntensity(hour) {
  // pico manhã: 7h–9h
  const morn = smoothstep(6.5, 7.0, hour) * (1 - smoothstep(9.0, 9.5, hour));
  // pico tarde: 17h–19h
  const eve  = smoothstep(16.5, 17.0, hour) * (1 - smoothstep(19.0, 19.5, hour));
  return Math.max(morn, eve);
}

function smoothstep(edge0, edge1, x) {
  const t = Math.max(0, Math.min(1, (x - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
}
```

---

### 9.5 Funções de desenho (JS)

- [ ] **`drawMapBackground(ctx, W, H, peakI)`**
  - Fundo `#080b12`
  - Quando `peakI > 0`: tint âmbar suave no fundo — `rgba(245,166,35, peakI * 0.06)`
  - Grade pontilhada leve (`rgba(255,255,255,0.03)`)

- [ ] **`drawHub(ctx, cx, cy)`**
  - Círculo preenchido `#1a1a2a`, borda `#3a3a5a`, raio 22px
  - Halo pulsante opcional (igual ao `drawGtfsPulse`)
  - Texto `"Rodoviária"` centralizado abaixo

- [ ] **`drawRouteLines(ctx, cx, cy)`**
  - Para cada rota: linha do hub até a parada mais distante, cor da rota com alpha 0.5

- [ ] **`drawStop(ctx, x, y, routeColor)`**
  - Círculo `r=5`, preenchido com a cor da rota

- [ ] **`drawDemandBar(ctx, x, y, demand, cap, variant)`**
  - Barra vertical acima da parada
  - Altura proporcional à demanda (máx 35px para `demand = cap`)
  - Cor: verde se `demand ≤ cap`, laranja se `demand > cap * 0.7`, vermelho se `demand > cap`
  - Para `variant = 'before'` e `demand > cap`: adicionar ícone de overflow (pessoa em vermelho com "✗")
  - Para `variant = 'after'`: barra sempre verde, sem overflow

- [ ] **`drawBusOnRoute(ctx, cx, cy, angle, progress, routeColor, size)`**
  - Posição: `x = cx + cos(angle°) * maxDist * progress`; `y = cy + sin(angle°) * maxDist * progress`
  - Retângulo `12×8px`, borda da cor da rota
  - Sai se `progress < 0` ou `progress > 1`

- [ ] **`drawClock(ctx, W, H, hour, peakI)`**
  - Posicionado no canto superior direito do canvas
  - Fundo `#111`, borda âmbar quando `peakI > 0.3`
  - Texto digital: `"07:30h"` (derivado de `hour`)
  - Quando `peakI > 0.5`: label `"HORÁRIO DE PICO"` em âmbar abaixo

- [ ] **`drawDispatchPulse(ctx, cx, cy, angle, alpha)`**
  - Pulso animado saindo do hub em direção à rota
  - Arco/linha âmbar com `alpha`
  - Sinaliza que HERMES está despachando ônibus extra

- [ ] **`drawFleetCounter(ctx, W, H, count, color)`**
  - Canto inferior esquerdo: `"Frota ativa: N ônibus"`
  - Tamanho 13px, cor variável

- [ ] **`drawOverflowCounter(ctx, W, H, count)`**
  - Canto inferior esquerdo (BEFORE): `"Aguardando: N passageiros"` em vermelho
  - Aparece durante pico, cresce com `peakI`

---

### 9.6 Posições das paradas (JS)

Calculadas a partir do hub `(cx, cy)`, ângulo da rota e `STOP_DISTS`:

```javascript
function stopPos(cx, cy, angleDeg, dist) {
  const rad = angleDeg * Math.PI / 180;
  return { x: cx + Math.cos(rad) * dist, y: cy + Math.sin(rad) * dist };
}
```

Hub recomendado: `cx = W * 0.50`, `cy = H * 0.50`

Verificação de fronteiras com canvas 560×380 (hub ≈ 280, 190):
- Asa Norte (−75°) stop3: x≈321, y≈36 ✓
- Asa Sul (105°) stop3: x≈239, y≈344 ✓
- Ceilândia (195°) stop3: x≈126, y≈149 ✓
- Sobradinho (15°) stop3: x≈434, y≈231 ✓

---

### 9.7 `renderDemandBefore(canvas, t)` — escala fixa

**Lógica de ônibus:**
- 1 ônibus visível por rota em todo momento (frequência fixa)
- `busProgress(t, routeIdx) = (t * 1.2 + routeIdx * 0.25) % 1`

**Lógica de demanda:**
- `demand(hour, stopIdx) = 1 + (DEMAND_CAP + 2) * peakIntensity(hour) * (1 + stopIdx * 0.3)`
  - Paradas mais distantes têm mais demanda no pico (regiões residenciais)

**Overflow:**
- `overflow = max(0, demand - DEMAND_CAP)`
- Mostrado como ícones de pessoas em vermelho acima das barras
- `overflowTotal = sum de overflow em todas as paradas`
- `drawOverflowCounter(ctx, W, H, overflowTotal)` durante pico

**Tint de fundo:**
- `drawMapBackground(ctx, W, H, peakIntensity(hour))`

---

### 9.8 `renderDemandAfter(canvas, t)` — despacho HERMES

**Fases:**

| t (fração) | hora | O que acontece |
|---|---|---|
| 0.00 – 0.06 | 6h–7h | 1 ônibus/rota, demanda baixa |
| 0.06 – 0.19 | 7h–9h | Pico manhã: `drawDispatchPulse` ativo; 2 ônibus/rota visíveis; demanda atendida |
| 0.19 – 0.44 | 9h–16.5h | Normaliza: 1 ônibus/rota, demanda baixa |
| 0.44 – 0.81 | 16.5h–19.5h | Pico tarde: mesma lógica do manhã |
| 0.81 – 1.00 | 19.5h–22h | Normaliza, reset |

**Ônibus extras:**
- Quando `peakI > 0.3`: segundo bus por rota com `busProgress2 = (busProgress1 + 0.5) % 1`
- `drawDispatchPulse` para cada rota onde ônibus extra está ativo

**Demanda:**
- Idêntica ao BEFORE (mesma demanda real), mas `variant = 'after'` → nunca mostra overflow
- Barra sempre verde porque a capacidade foi aumentada

**Fleet counter:**
- Off-peak: `"Frota ativa: 4 ônibus"` (1 por rota)
- On-peak: `"Frota ativa: 8 ônibus (+80%)"` em verde

---

### 9.9 Loop de animação

```javascript
const cDemBefore = document.getElementById('c-demand-before');
const cDemAfter  = document.getElementById('c-demand-after');
const startDem   = performance.now();

function tickDemanda() {
  const t = ((performance.now() - startDem) % CYCLE_DEMANDA) / CYCLE_DEMANDA;
  renderDemandBefore(cDemBefore, t);
  renderDemandAfter(cDemAfter, t);
  requestAnimationFrame(tickDemanda);
}
requestAnimationFrame(tickDemanda);
```

---

### 9.10 Atualizar README

- [ ] Adicionar `/demanda` na tabela de URLs

---

### 9.11 Armadilhas específicas

- **`smoothstep`** — garante transição suave no pico; sem ela, demanda salta abruptamente
- **Verificação de fronteiras do canvas** — `stopPos` pode sair da tela se ângulo/distância forem maiores que calculado; testar visualmente com todos os 4 ângulos
- **Dois ônibus no AFTER usam o mesmo `busProgress` base** — o segundo usa `(base + 0.5) % 1`, sempre na metade oposta da rota
- **`drawOverflowCounter` só no BEFORE** — nunca no AFTER; confundiria a narrativa
- **`CYCLE_DEMANDA = 30000`** (30s) com mapeamento não-linear — passa 63% do ciclo na janela 7h–9h (pico)
- **`getHour(t)` não-linear** — 0.00–0.12 = 6h–7h, 0.12–0.75 = 7h–9h (pico), 0.75–1.00 = recuperação
- **`drawStopWithDemand`** — parada = círculo fixo pequeno (5px); demanda = barra vertical separada que cresce até 38px; trilho de fundo + linha de capacidade tracejada + glow pulsante no overflow
- **Não usar `setTimeout` para o relógio** — o avanço do tempo é derivado de `t`; garante sincronismo visual perfeito

---

## Progresso atual

```
Marco 1 ██████████ 100% — fluxo botão → alerta em tempo real
Marco 2 ██████████ 100% — áudio, bipe, LGPD, aria-live
Marco 3 ██████████ 100% — confirmar, cancelar, expirar
Marco 4 ████░░░░░░  40% — endpoint /api/rfid pronto; falta hardware + script Pi
Marco 5 ██████████ 100% — visual, animações, dados DF
Marco 6 ░░░░░░░░░░   0% — depende do hardware estar pronto
Marco 7 ██████████ 100% — /versus: acessibilidade animada (canvas 230px)
Marco 8 ██████████ 100% — /versus: seção bunching vs headway GTFS-Realtime (canvas 165px)
Marco 9 ██████████ 100% — /demanda: mapa de pico com despacho dinâmico (30s ciclo)
```

**Testes:** 110 passando (pytest tests/ -v)

---

## Armadilhas para não cair

- Não codificar geofencing, mapa animado ou grafo — vira slide
- Não remover o botão — é o plano B; se a demo só funciona com RFID, um problema de rede te derruba
- Não escrever no cartão RFID — somente leitura do UID
- Não testar o hardware só na véspera
- Não subir ao palco sem o vídeo de backup gravado e aberto
