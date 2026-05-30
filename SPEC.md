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

- [ ] `test_versus_returns_200` — `GET /versus` responde 200
- [ ] `test_versus_contains_before_canvas` — HTML contém `id="c-before"`
- [ ] `test_versus_contains_after_canvas` — HTML contém `id="c-after"`
- [ ] `test_versus_contains_comparison_title` — HTML contém a palavra "Compara"

---

### 7.1 Rota no servidor (`backend/app.py`)

- [ ] Adicionar `GET /versus` → `send_from_directory(FRONTEND_DIR, "versus.html")`
- [ ] Confirmar que os 4 testes do 7.0 passam

---

### 7.2 Estrutura HTML (`frontend/versus.html`)

Arquivo auto-contido (CSS inline + JS inline). Nenhuma dependência externa além de `style.css`.

- [ ] Header: logo `HERMES` + título "Comparação: Sistema Atual vs HERMES" + link `← Demo ao vivo` para `/demo`
- [ ] Layout de 3 colunas: `[painel esquerdo] [divisor VS] [painel direito]`
- [ ] Painel esquerdo: tag `Hoje` (cinza), título, `<canvas id="c-before" width="560" height="300">`, bloco de stats, card de métrica vermelha ("~32 min espera")
- [ ] Painel direito: tag `HERMES` (âmbar), título, `<canvas id="c-after" width="560" height="300">`, bloco de stats, card de métrica verde ("< 2 min resposta")
- [ ] Divisor central: badge circular "VS"

---

### 7.3 CSS adicional (inline em `versus.html`)

- [ ] `.comparison-layout` — `display: grid; grid-template-columns: 1fr auto 1fr`
- [ ] `.panel-comp` — padding interno
- [ ] `.panel-tag` — pequeno badge colorido acima do título
  - `.tag-before` — cinza
  - `.tag-after` — âmbar (usando `var(--accent)`)
- [ ] `.key-metric` — card com borda colorida e valor grande
  - `.metric-before` — borda/texto vermelho
  - `.metric-after` — borda/texto verde
- [ ] `.vs-badge` — círculo com "VS" no divisor
- [ ] `canvas` — `width: 100%; height: auto; border-radius: 8px; background: #0a0c14`

---

### 7.4 Constantes e helpers JS

- [ ] `CYCLE = 12000` — duração do ciclo em ms
- [ ] `ROAD_TOP_FRAC = 0.60` — road começa a 60% da altura do canvas
- [ ] `SIDE_TOP_FRAC = 0.48` — calçada começa a 48%
- [ ] `STOP_X_FRAC = 0.32` — ponto de parada a 32% da largura
- [ ] `BUS_W = 100, BUS_H = 50` — dimensões do ônibus em px
- [ ] `function lerp(a, b, t)` — interpolação linear com clamping
- [ ] `function easeOut(t)` — `1 - (1-t)²` (desacelera ao final)
- [ ] `function easeIn(t)` — `t²` (acelera ao final)
- [ ] `function fadeIn(t, start, end)` — alpha 0→1 entre dois pontos do ciclo
- [ ] `function fadeOut(t, start, end)` — alpha 1→0 entre dois pontos do ciclo

---

### 7.5 Funções de desenho no canvas

Cada função recebe `(ctx, W, H, ...)` — sem estado global de desenho.

- [ ] **`drawBackground(ctx, W, H)`**
  - Gradiente escuro (céu): `y=0` a `y=H*SIDE_TOP_FRAC`
  - 8 estrelas fixas (pontos brancos 1px)
  - Calçada cinza escuro: `y=H*SIDE_TOP_FRAC` a `y=H*ROAD_TOP_FRAC`
  - Pista cinza médio: `y=H*ROAD_TOP_FRAC` a `y=H`
  - Linha tracejada branca no centro da pista
  - Linha de meio-fio separando calçada e pista

- [ ] **`drawBusStop(ctx, W, H, glowAlpha)`**
  - Poste vertical: da calçada até `poleTopY`
  - Teto do abrigo: retângulo no topo do poste
  - Banco: retângulo + duas pernas
  - Texto "BUS / STOP" no alto do poste
  - Quando `glowAlpha > 0`: tudo fica âmbar; halo radial atrás do abrigo

- [ ] **`drawPerson(ctx, W, H, state, animT)`**
  - Sombra elíptica nos pés
  - Cabeça: círculo
  - Corpo: linha vertical
  - Pernas: duas linhas para os pés
  - Braços variam conforme `state`:
    - `'waiting'` — braços caídos, rosto neutro
    - `'waving'` — braço direito oscila com `Math.sin(now * 8)`, rosto neutro
    - `'sad'` — braços caídos, boca curva para baixo, lágrimas azuis
    - `'tap'` — braço direito estendido ao poste (âmbar), cartão RFID na mão, rosto feliz
    - `'boarding'` — `globalAlpha` decresce com `animT` (some gradualmente)

- [ ] **`drawBus(ctx, W, H, busX, variant, alertAlpha)`**
  - Sai se `busX > W+10` ou `busX < -BUS_W-10` (fora da tela)
  - Sombra elíptica sob as rodas
  - Carroceria arredondada (`roundRect`)
  - 3 janelas laterais + 1 para-brisa
  - Farol dianteiro (branco) + lanterna traseira (vermelho)
  - 2 rodas com aro + centro
  - Plaquinha de linha "110 UnB" no teto
  - Cor da carroceria: cinza escuro para `'before'`, azul escuro para `'after'`
  - Badge de alerta (quando `alertAlpha > 0`):
    - Fundo âmbar `roundRect` acima da carroceria
    - Texto `"♿ Embarque"`
    - Linha tracejada apontando para o ônibus
    - Halo radial ao redor do badge

- [ ] **`drawRipple(ctx, x, y, progress)`**
  - 3 anéis concêntricos, cada um com delay de `0.15` no `progress`
  - Raio máximo = 35px; alpha decresce conforme o anel expande
  - Cor âmbar `rgba(245, 166, 35, α)`

- [ ] **`drawSignalPulse(ctx, fromX, toX, y, t)`**
  - Linha tracejada animada (usando `lineDashOffset`)
  - Cor âmbar, avança de `fromX` até `fromX + totalDist * min(1, t*2)`

- [ ] **`drawLabel(ctx, W, H, text, yPos, color, alpha)`**
  - Texto centralizado, tamanho 13px bold
  - Respeita `alpha` via `globalAlpha`

- [ ] **`drawWaitClock(ctx, W, H, alpha)`**
  - Relógio analógico simples (círculo + dois ponteiros)
  - Texto `"+32min"` e `"espera"` abaixo
  - Cor vermelha, posicionado no canto superior direito

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

- [ ] `startTime = performance.now()` na inicialização
- [ ] Função `tick()` chamada via `requestAnimationFrame`
- [ ] Dentro de `tick()`: calcular `t = ((now - startTime) % CYCLE) / CYCLE`
- [ ] Chamar `renderBefore(canvasBefore, t)` e `renderAfter(canvasAfter, t)`
- [ ] Nenhum estado global mutável além de `startTime` — as funções de render são puras em relação ao tempo

---

### 7.8 Atualizar README

- [ ] Adicionar `/versus` na tabela de URLs

---

## Progresso atual

```
Marco 1 ██████████ 100% — fluxo botão → alerta em tempo real
Marco 2 ██████████ 100% — áudio, bipe, LGPD, aria-live
Marco 3 ██████████ 100% — confirmar, cancelar, expirar
Marco 4 ████░░░░░░  40% — endpoint /api/rfid pronto; falta hardware + script Pi
Marco 5 ██████████ 100% — visual, animações, dados DF
Marco 6 ░░░░░░░░░░   0% — depende do hardware estar pronto
Marco 7 ░░░░░░░░░░   0% — tela de comparação visual /versus (planejado)
```

---

## Armadilhas para não cair

- Não codificar geofencing, mapa animado ou grafo — vira slide
- Não remover o botão — é o plano B; se a demo só funciona com RFID, um problema de rede te derruba
- Não escrever no cartão RFID — somente leitura do UID
- Não testar o hardware só na véspera
- Não subir ao palco sem o vídeo de backup gravado e aberto
