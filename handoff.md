# Handoff — HERMES

Estado do projeto ao fim da sessão de desenvolvimento inicial.

---

## O que foi construído

Marcos 1–3, 5, 7, 8 e 9 completos. O software roda 100% no notebook, sem hardware.
**110 testes passando** (`pytest tests/ -v`).

### Arquivos do projeto

| Arquivo | O que faz |
|---|---|
| `backend/app.py` | Flask + SocketIO. 5 rotas HTML, 1 endpoint REST (`/api/rfid`), 3 eventos SocketIO. |
| `frontend/demo.html` | **Tela do pitch**: parada à esquerda, motorista à direita. Carrega `parada.js` + `motorista.js`. |
| `frontend/parada.html` | Tela isolada da parada (projeção separada). |
| `frontend/motorista.html` | Painel isolado do motorista (projeção separada). |
| `frontend/versus.html` | **Comparação animada** (canvas 12s loop): acessibilidade antes/depois + bunching vs headway GTFS-RT. |
| `frontend/demanda.html` | **Mapa de demanda de pico** (canvas 30s loop, não-linear): rotas do DF com ônibus, barras de demanda, overflow vs despacho HERMES. |
| `frontend/static/css/style.css` | Paleta escura alto contraste, cartões de alerta, estados, animação slide-in. |
| `frontend/static/js/parada.js` | Botão solicitar, cancelar, Web Speech API (`pt-BR`), estados da UI. |
| `frontend/static/js/motorista.js` | Criar/resolver/cancelar cartões, bipe Web Audio API, expiração 90s, confirmar. |
| `data/transit_data.json` | 4 linhas reais do DF (110/0.111/107/160), 3 paradas, formato GTFS-friendly. |
| `tests/conftest.py` | Fixtures: `app`, `client`, `socket_client`, `two_socket_clients`. |
| `tests/test_routes.py` | 35 testes — rotas HTTP, páginas HTML, `/api/rfid`, `/versus`, `/demanda`. |
| `tests/test_events.py` | 27 testes — eventos SocketIO, broadcast para 2 clientes, RFID via POST. |
| `tests/test_helpers.py` | 25 testes — `_find_stop_name`, `_build_payload` (UUID, ISO8601, fallback). |
| `tests/test_data.py` | 23 testes — integridade do JSON, IDs únicos, campos obrigatórios. |
| `requirements.txt` | Dependências fixadas com versões exatas (`pip freeze`). |
| `.gitignore` | Ignora `venv/`, `__pycache__/`, `.env`, `.DS_Store`, `.pytest_cache/`. |

---

## Decisões técnicas

**`async_mode="threading"` em vez de `eventlet`**
O eventlet foi marcado como deprecated na versão atual. Threading resolve para a demo local.

**`allow_unsafe_werkzeug=True`**
Flask-SocketIO 5.x exige essa flag para o servidor de desenvolvimento. Em produção se usaria gunicorn.

**Socket.io via CDN**
`https://cdn.socket.io/4.7.5/socket.io.min.js` — sem build step, sem npm. A demo roda com `python app.py`.

**Um único par de JS (`parada.js` / `motorista.js`)**
Carregados tanto nas telas isoladas quanto na `demo.html`. Zero duplicação de lógica.

**UIDs RFID desconhecidos → linha 110 por padrão**
Evita falha se o leitor pegar um cartão não cadastrado no palco.

**Expiração de alertas no cliente (não no servidor)**
`setTimeout` 90s em `motorista.js`. Servidor stateless para alertas.

**Canvas animations: tempo derivado de `performance.now()`, nunca de `setTimeout`**
Garante que `t` avance suavemente a 60fps sem drift. Toda lógica de estado é função pura de `t`.

**`/versus`: ciclo de 12s, mapeamento linear**
Animação curta e contínua. Adequada para a cena de acessibilidade (pessoa/ônibus) + bunching.

**`/demanda`: ciclo de 30s, mapeamento não-linear**
60% do ciclo (18.9s) gasto no pico 7h–9h para dar tempo de leitura. Apenas pico da manhã — narrativa limpa.

**`drawStopWithDemand`: separação visual entre parada e demanda**
Parada = círculo fixo pequeno (5px, para os ônibus aparecerem). Demanda = barra vertical separada com trilho de fundo + linha de capacidade tracejada + glow pulsante no overflow.

---

## Fluxo de eventos (o coração do sistema)

```
[Parada]                    [Servidor]               [Motorista]
  |                              |                        |
  |-- button_request ----------->|                        |
  |   { route_id, stop_id }      |-- new_boarding_req --->|
  |                              |   { id, route_name,    |  ← cartão aparece
  |<-- new_boarding_req ---------|     stop_name,          |  ← bipe toca
  |   (origin: "button")         |     origin, timestamp } |
  |   → desabilita botão         |                        |
  |   → fala o nome da linha     |                        |
  |                              |                        |
  |                         POST /api/rfid                 |
  |                    { uid, stop_id }                    |
  |                              |-- new_boarding_req --->|
  |                              |   (origin: "rfid")     |  ← mesmo cartão
  |                              |                        |
  |                              |<-- resolve_request -----|
  |                              |    { id }               |
  |<-- request_resolved ---------|                        |
  |   → libera botão             |-- request_resolved --->|  ← cartão vira verde
  |   → mostra "atendido"        |                        |
```

---

## Como rodar agora

```bash
cd /home/victor/Projects/Hermes/hermes
source venv/bin/activate
python backend/app.py
```

| URL | Usar quando |
|---|---|
| `http://localhost:5000/versus` | Problema humano (0:00–1:00) |
| `http://localhost:5000/demanda` | Virada da ideia (1:00–1:30) |
| `http://localhost:5000/demo?demo=true` | Demo ao vivo (1:30–2:30) |

O servidor está com virtualenv criado e dependências instaladas.

---

## O que falta

### Marco 4 — Hardware Raspberry Pi + RC522

O **endpoint `/api/rfid` já existe e funciona** — testado via `curl`. O Pi só precisa fazer o POST.

Criar `rfid/rfid_reader.py`:
```python
import time, requests
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

SERVER_URL = "http://<IP_DO_NOTEBOOK>:5000/api/rfid"
reader = SimpleMFRC522()

while True:
    uid, _ = reader.read()
    requests.post(SERVER_URL, json={"uid": str(uid), "stop_id": "parada_w3_sul_502"})
    print(f"[RFID] UID={uid} enviado")
    time.sleep(2)  # debounce
```

Pinout RC522 → Pi: `SDA→GPIO8, SCK→GPIO11, MOSI→GPIO10, MISO→GPIO9, GND→GND, RST→GPIO25, 3.3V→3.3V`

Testar 20 leituras seguidas antes do dia da apresentação.

### Marco 6 — Pitch e blindagem

1. **Vídeo de backup** — gravar screencast da demo completa (com RFID). Abrir em aba separada antes de subir ao palco.
2. **Roteiro** — escrever palavra a palavra, cronometrar nos 3 minutos exatos.
3. **Slides de visão** — geofencing 500m, GTFS-Realtime feed real, grafo Neo4j/matriz O-D, despacho ML.
4. **Ensaiar 3+ vezes** cronometrado.

---

## Pontos de atenção para o pitch

- Abrir 3 abas antes de subir: `/versus`, `/demanda`, `/demo?demo=true`
- `speechSynthesis` e `AudioContext` exigem interação prévia do browser — clicar qualquer coisa nas 3 páginas antes de subir ao palco
- Se o Pi não responder em ~2s: clicar o botão e continuar sem comentar
- `/demanda` tem ciclo de 30s — abrir com antecedência para chegar no pico na hora certa da apresentação

---

## Estado do repositório

Nenhum commit foi feito ainda. Todos os arquivos em `hermes/` são untracked.
Os arquivos de planejamento na raiz (`HERMES_plano.md`, `PLANEJAMENTO_HERMES.md`, `README.md`, `SPEC.md`) também estão untracked.

---

## Marcos 7 e 8 concluídos

- `/versus` implementado: comparação de acessibilidade (canvas 230px) + seção GTFS-Realtime/bunching (canvas 165px). 105 testes passando.
- `.gitignore` criado na raiz.

---

## Próxima sessão — Marco 9: Mapa de Demanda em Horário de Pico (`/demanda`)

### O que é e por que existe

Uma página nova (`/demanda`) com dois canvas lado a lado mostrando um mapa esquemático da malha de ônibus do DF (Rodoviária central + 4 rotas irradiando: Asa Norte, Asa Sul, Ceilândia, Sobradinho). Um relógio avança de 6h a 22h em loop. Durante os horários de pico (7h–9h e 17h–19h), a demanda cresce nas paradas.

- **Esquerda (hoje):** frota fixa. No pico, barras de demanda ultrapassam a capacidade → ícones de overflow (pessoas em vermelho), contador "Aguardando: N passageiros".
- **Direita (HERMES):** `drawDispatchPulse` sai do hub; ônibus extras aparecem nas rotas; barras sempre verdes; contador "Frota: 4 → 8 ônibus".

**Argumento no pitch (30s da virada):** "Hoje a escala de frota é feita semanas antes em planilha. Com GTFS-Realtime o HERMES sabe, em tempo real, onde a demanda está crescendo — e despacha ônibus antes que o overflow aconteça."

### Ordem de execução (TDD obrigatório)

**Passo 1 — 5 testes, nova classe `TestDemandaPage`** em `test_routes.py`:
```python
def test_demanda_returns_200(self, client)
def test_demanda_contains_before_canvas(self, client)   # id="c-demand-before"
def test_demanda_contains_after_canvas(self, client)    # id="c-demand-after"
def test_demanda_contains_peak_concept(self, client)    # "pico"
def test_demanda_contains_gtfs_reference(self, client)  # "GTFS"
```
Rodar → 5 falhas (red).

**Passo 2 — Rota em `app.py`:**
```python
@app.route("/demanda")
def demanda():
    return send_from_directory(FRONTEND_DIR, "demanda.html")
```

**Passo 3 — HTML mínimo** (só para testes passarem):
Criar `demanda.html` com os dois `<canvas>` ids, as palavras "pico" e "GTFS" no HTML. Rodar → 5 green.

**Passo 4 — HTML completo:**
Completar com header, layout 3 colunas, stats, cards de métrica (vermelho / verde).

**Passo 5 — Constantes e helpers JS** (nesta ordem):
```javascript
const ROUTES = [
  { label: 'Asa Norte', angle: -75, color: '#4a9eff' },
  { label: 'Asa Sul',   angle: 105, color: '#a855f7' },
  { label: 'Ceilândia', angle: 195, color: '#f97316' },
  { label: 'Sobradinho',angle:  15, color: '#06b6d4' },
];
const STOP_DISTS  = [65, 115, 160];
const DEMAND_CAP  = 4;
const CYCLE_DEMANDA = 14000;

function smoothstep(edge0, edge1, x) { /* fórmula cúbica */ }
function getHour(t) { return 6 + t * 16; }
function peakIntensity(hour) { /* morn + eve usando smoothstep */ }
function stopPos(cx, cy, angleDeg, dist) { /* cos/sin → {x,y} */ }
```

**Passo 6 — 8 funções de desenho** (na ordem do SPEC §9.5):
1. `drawMapBackground` → fundo + tint âmbar proporcional ao pico
2. `drawHub` → círculo central com label "Rodoviária"
3. `drawRouteLines` → linhas do hub para última parada
4. `drawStop` → círculo pequeno na posição da parada
5. `drawDemandBar` → barra de demanda + overflow icon se before+excedido
6. `drawBusOnRoute` → mini ônibus animado ao longo da rota
7. `drawClock` → relógio digital + label "HORÁRIO DE PICO"
8. `drawDispatchPulse` → pulso do hub para a rota (AFTER only)
9. `drawFleetCounter` e `drawOverflowCounter` → contadores de canto

**Passo 7 — `renderDemandBefore(canvas, t)`:**
- Calcular `hour = getHour(t)`, `peakI = peakIntensity(hour)`
- Chamar `drawMapBackground`, `drawHub`, `drawRouteLines`
- Para cada rota: `drawStop` × 3, `drawDemandBar` (variant='before'), `drawBusOnRoute`
- `drawClock`, `drawOverflowCounter`

**Passo 8 — `renderDemandAfter(canvas, t)`:**
- Mesma base
- Quando `peakI > 0.3`: `drawDispatchPulse` + segundo `drawBusOnRoute` com `progress+0.5`
- `drawDemandBar` com `variant='after'` (nunca overflow)
- `drawFleetCounter` com valor dinâmico

**Passo 9 — Loop próprio:**
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

**Passo 10 — README:** adicionar `/demanda` na tabela de URLs.

### Armadilhas

- `smoothstep` é crítico para a transição suave do pico; sem ela o overflow aparece e desaparece abruptamente, parecendo bug
- Verificar visualmente os 4 ângulos: stop3 de cada rota deve ficar dentro do canvas 560×380
- O segundo ônibus no AFTER usa `(progress + 0.5) % 1` para ficar no meio oposto da rota — nunca sobreposto ao primeiro
- `CYCLE_DEMANDA` tem seu próprio `startDem` e `requestAnimationFrame` separados do `/versus` — não compartilhar variáveis globais entre páginas

---

## Marco 7 concluído

A página `/versus` está implementada com dois canvas animados (acessibilidade: antes/depois). 101 testes passando. Detalhes no SPEC.md §7.

---

## Próxima sessão — Marco 8: Seção GTFS-Realtime na `/versus`

### O que é e por que existe

Uma segunda seção dentro da página `/versus`, abaixo da comparação de acessibilidade já existente. Dois canvas menores (520×165px) mostrando uma visão aérea de uma linha de ônibus.

**Ponto de venda:** o HERMES não resolve só o embarque assistido — resolve o bunching (acúmulo de ônibus) que afeta todos os passageiros de todas as linhas. É o argumento para o DFTrans inteiro, não só para usuários com deficiência.

**Bunching** é um fenômeno conhecido: sem dados em tempo real, ônibus naturalmente se agrupam (o atrasado fica mais atrasado porque encontra mais passageiros, o adiantado chega mais rápido porque encontra menos). Com GTFS-Realtime + despacho dinâmico, o HERMES detecta e corrige antes que piore.

### O que muda nos arquivos

Apenas `frontend/versus.html` é modificado. Nenhuma mudança em `app.py`, nenhuma nova rota, nenhum novo teste de evento. Só HTML + CSS + JS no mesmo arquivo.

### Ordem de execução (TDD obrigatório)

**Passo 1 — 4 testes novos em `tests/test_routes.py`** (classe `TestVersusPage`, todos vão falhar):
```python
def test_versus_contains_route_before_canvas(self, client)  # id="c-route-before"
def test_versus_contains_route_after_canvas(self, client)   # id="c-route-after"
def test_versus_contains_gtfs_section(self, client)         # "GTFS" no HTML
def test_versus_contains_bunching_concept(self, client)     # "bunching" no HTML
```
Rodar → confirmar 4 falhas (red).

**Passo 2 — HTML da nova seção**

Inserir ao final de `versus.html`, antes de `</body>`:
- `<div class="eff-section">` com `eff-header` (título + subtítulo)
- `<div class="eff-panels">` com grid 3 colunas (igual ao `.versus-layout`)
- Canvas `id="c-route-before"` width=520 height=165
- Canvas `id="c-route-after"` width=520 height=165
- Tags `v-tag-before` / `v-tag-after`
- Cards de métrica `.eff-metric-before` / `.eff-metric-after`
- Texto "GTFS" e "bunching" presentes para os testes passarem

Rodar testes → 4 novos passam (green). Suite completa continua 101+4 = 105 passando.

**Passo 3 — CSS**

Adicionar ao `<style>` do `versus.html`:
- `.eff-section` — `padding: 0 24px 16px; border-top: 1px solid var(--border)`
- `.eff-header` / `.eff-header h3` / `.eff-header p` — padding e tipografia compactos
- `.eff-panels` — `display: grid; grid-template-columns: 1fr auto 1fr`
- `.eff-panel` — `padding: 0 12px`
- `.eff-metric`, `.eff-metric-before`, `.eff-metric-after` — cards coloridos (vermelho / verde)

**Passo 4 — Constantes e helpers (JS)**

Constantes novas (adicionar junto com as existentes):
```javascript
const STOPS_X     = [55, 148, 240, 333, 425];
const ROUTE_YFRAC = 0.56;
const MBUS_W = 30, MBUS_H = 18;
```
Helpers já existem (`lerp`, `easeOut`, `easeIn`, `fadeIn`, `fadeOut`).

**Passo 5 — Funções de desenho (implementar nessa ordem)**

1. `drawRouteBackground(ctx, W, H)` — fundo escuro, linha de rota, 5 postes de parada
2. `drawPassengersAtStop(ctx, sx, routeY, count, color)` — círculos empilhados acima do poste, até 6 + contador "+N"
3. `drawMiniBus(ctx, x, routeY, bodyColor, accentColor, label, badgeText)` — retângulo 30×18 com janelas, rótulo A/B/C, badge âmbar opcional
4. `drawHeadwayLabel(ctx, x1, x2, routeY, text, color)` — label de headway no meio do gap, tracejado nas bordas
5. `drawGtfsPulse(ctx, W, H, routeY)` — pulso baseado em `performance.now()` (independe de `t`), linhas pulsantes acima dos postes

**Passo 6 — Render do BEFORE (bunching)**

```javascript
function renderRouteBefore(canvas, t) {
  const bAx = lerp(510, -35, t);
  const bBx = lerp(400, -35, t * 1.18);  // mais rápido → alcança A
  const bCx = lerp(210, -35, t * 0.78);  // mais lento → gap cresce
  // demanda por stop: alta no gap B-C, baixa perto do bunching A-B
  // headway labels: calculados a partir das posições reais
  // label de diagnóstico: "Bunching: ônibus se acumulam"
}
```

**Passo 7 — Render do AFTER (dispatch HERMES)**

```javascript
function renderRouteAfter(canvas, t) {
  const bAx = lerp(510, -35, t);
  if (t < 0.22) {
    // leve bunching antes do HERMES intervir
    bBx = lerp(390, -35, t * 1.08);
    bCx = lerp(220, -35, t * 0.92);
  } else {
    // após dispatch: espaçamento fixo ~145px
    bBx = bAx - 145;
    bCx = bAx - 290;
  }
  // badge "⚡ adj" no ônibus B quando t ∈ [0.22, 0.42]
  // label âmbar "HERMES: ajuste de headway detectado"
  // demanda: sempre baixa (1-2), cor verde
  // headway labels: sempre "~10 min"
  // drawGtfsPulse sempre visível
}
```

**Passo 8 — Atualizar `tick()`**

```javascript
const cRouteBefore = document.getElementById('c-route-before');
const cRouteAfter  = document.getElementById('c-route-after');
// dentro de tick():
renderRouteBefore(cRouteBefore, t);
renderRouteAfter(cRouteAfter, t);
```

### Armadilhas

- `lineDashOffset` — resetar para `0` imediatamente após `drawHeadwayLabel`; senão corrompe outros strokes do mesmo frame
- A demanda dos passageiros deve ser calculada a partir de `bAx`/`bBx`/`bCx` em tempo real, não hardcoded — garante coerência visual com os ônibus
- O ônibus B **também começa bunching no AFTER** (0.00–0.22) — é intencional para mostrar que o HERMES intervém antes de piorar, não que a situação começa diferente
- `performance.now()` no pulso GTFS cria um batimento visual independente do ciclo de 12s — aparência de "feed ativo", não de animação de apresentação
- Canvas 165px de altura — não aumentar; é compacto de propósito para caber na tela sem scroll no pitch

---

## Próxima sessão — Marco 7: Tela de Comparação `/versus`

### O que é e por que existe

Uma página com dois canvas animados em loop side-by-side. Esquerda: sistema atual (ônibus passa sem parar, pessoa acena sem resposta, relógio mostra 32 min de espera). Direita: HERMES (pessoa toca cartão, sinal viaja até o ônibus, ônibus desacelera e para, pessoa embarca, confirmação verde).

Usado no pitch durante o segmento "problema humano" (0:00–1:00). O juiz vê a diferença sem precisar de uma palavra.

### Ordem de execução (TDD obrigatório)

**Passo 1 — Testes primeiro** (4 testes, vão falhar de propósito)

Adicionar em `tests/test_routes.py`, classe `TestVersusPage`:
```python
def test_versus_returns_200(self, client)
def test_versus_contains_before_canvas(self, client)   # id="c-before"
def test_versus_contains_after_canvas(self, client)    # id="c-after"
def test_versus_contains_comparison_title(self, client) # "Compara"
```

Rodar `pytest tests/test_routes.py::TestVersusPage` → confirmar 4 falhas (red).

**Passo 2 — Rota no servidor**

Em `backend/app.py`, adicionar abaixo da rota `/demo`:
```python
@app.route("/versus")
def versus():
    return send_from_directory(FRONTEND_DIR, "versus.html")
```

Criar `frontend/versus.html` com a estrutura HTML mínima (apenas os `id`s e o título). Rodar os testes → devem passar (green).

**Passo 3 — HTML e CSS**

Completar o `versus.html` com:
- Header com link de volta para `/demo`
- Layout 3 colunas: `[painel-before] [VS] [painel-after]`
- Dois `<canvas>` com `id="c-before"` e `id="c-after"`, ambos `width="560" height="300"`
- Dois blocos de stats (texto estático por enquanto)
- Dois cards de métrica: vermelho "~32 min espera" / verde "< 2 min resposta"
- CSS inline usando as variáveis de `style.css`

**Passo 4 — Funções de desenho (canvas)**

Implementar no `<script>` do `versus.html`, na seguinte ordem:

1. Constantes (`CYCLE`, `ROAD_TOP_FRAC`, `SIDE_TOP_FRAC`, `STOP_X_FRAC`, `BUS_W`, `BUS_H`)
2. Helpers (`lerp`, `easeOut`, `easeIn`, `fadeIn`, `fadeOut`)
3. `drawBackground(ctx, W, H)` — céu + estrelas + calçada + pista + marcações
4. `drawBusStop(ctx, W, H, glowAlpha)` — poste + teto + banco; muda para âmbar se `glowAlpha > 0`
5. `drawPerson(ctx, W, H, state, animT)` — boneco palito, 5 estados: `waiting / waving / sad / tap / boarding`
6. `drawBus(ctx, W, H, busX, variant, alertAlpha)` — carroceria + janelas + rodas + plaquinha + badge âmbar opcional
7. `drawRipple(ctx, x, y, progress)` — 3 anéis expandindo do ponto de toque
8. `drawSignalPulse(ctx, fromX, toX, y, t)` — linha tracejada animada com `lineDashOffset`
9. `drawLabel(ctx, W, H, text, yPos, color, alpha)` — texto centralizado com fade
10. `drawWaitClock(ctx, W, H, alpha)` — relógio analógico + "+32 min"

**Passo 5 — Renders principais**

11. `renderBefore(canvas, t)` — orquestra as funções para o painel esquerdo conforme a timeline
12. `renderAfter(canvas, t)` — orquestra as funções para o painel direito conforme a timeline

**Passo 6 — Loop**

13. `tick()` com `requestAnimationFrame`, calcula `t`, chama os dois renders

**Passo 7 — Atualizar README**

Adicionar `/versus` na tabela de URLs.

### Timelines resumidas

```
BEFORE (t = 0.0 → 1.0, 12s):
  0.00 pessoa aguarda, relógio de horário fixo
  0.08 ônibus entra pela direita, velocidade constante
  0.40 ônibus próximo → pessoa acena
  0.54 ônibus saiu → pessoa triste, relógio "+32min" aparece
  0.90 fade out, reset

AFTER (t = 0.0 → 1.0, 12s):
  0.00 pessoa aguarda
  0.06 pessoa toca cartão → ripple no poste, parada fica âmbar
  0.18 pulso de sinal viaja para a direita
  0.35 ônibus entra com badge "♿ Embarque" visível
  0.60 ônibus para no ponto (easeOut — desaceleração visível)
  0.72 pessoa embarca (some gradualmente)
  0.80 label verde "✓ Embarque assistido confirmado"
  0.75 ônibus parte (easeIn — aceleração visível)
  0.95 fade out, reset
```

### Armadilhas desta feature

- `canvas.roundRect` — disponível Chrome 99+, Safari 15.4+, Firefox 112+. Para o hackathon em 2026 é seguro.
- `lineDashOffset` para animação de pulso — resetar para `0` após cada uso ou afetará outros desenhos.
- `globalAlpha` — sempre restaurar para `1.0` ao final de qualquer função que o altere.
- O canvas NÃO usa SocketIO — é puramente local, sem estado de servidor. Nenhuma modificação no `app.py` além da rota.
- Não adicionar interatividade (botões, cliques no canvas) — a animação é passiva, loop automático. Simplicidade é o objetivo.
