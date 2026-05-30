# Handoff — HERMES

Estado do projeto ao fim da sessão de desenvolvimento inicial.

---

## O que foi construído

Marcos 1, 2, 3 e 5 estão completos. O software roda 100% no notebook, sem hardware.

### Arquivos criados

| Arquivo | O que faz |
|---|---|
| `backend/app.py` | Servidor Flask + SocketIO. 3 rotas HTTP, 1 endpoint REST, 3 eventos SocketIO. |
| `frontend/demo.html` | Tela do pitch: parada à esquerda, motorista à direita, lado a lado. |
| `frontend/parada.html` | Tela isolada da parada (para projeção em tela separada). |
| `frontend/motorista.html` | Painel isolado do motorista (para projeção em tela separada). |
| `frontend/static/css/style.css` | Paleta escura alto contraste, cartões de alerta, estados, animação slide-in. |
| `frontend/static/js/parada.js` | Botão solicitar, cancelar, Web Speech API (`pt-BR`), estados da UI. |
| `frontend/static/js/motorista.js` | Criar/resolver/cancelar cartões, bipe Web Audio API, expiração automática. |
| `data/transit_data.json` | 4 linhas reais do DF no formato GTFS-friendly, 3 paradas. |
| `requirements.txt` | Dependências fixadas (`pip freeze`). |

---

## Decisões técnicas tomadas

**`async_mode="threading"` em vez de `eventlet`**
O eventlet foi marcado como deprecated na versão atual. Threading resolve para uma demo local sem nenhum custo de refatoração.

**`allow_unsafe_werkzeug=True` no `socketio.run()`**
Flask-SocketIO 5.x exige essa flag para rodar o servidor de desenvolvimento do Werkzeug. Em produção real se usaria gunicorn, mas para a demo local é o caminho correto.

**Socket.io via CDN**
`https://cdn.socket.io/4.7.5/socket.io.min.js` — sem build step, sem npm, sem Webpack. A demo roda com `python app.py` e ponto final.

**Um único par de JS (`parada.js` / `motorista.js`)**
Os dois scripts são carregados tanto nas telas isoladas quanto na `demo.html`. Zero duplicação de lógica.

**Qualquer UID RFID assume linha 110 — UnB**
No endpoint `/api/rfid`, UIDs desconhecidos recebem a linha padrão da demo. Evita falha caso o leitor pegue um cartão não cadastrado no palco.

**Expiração de alertas no cliente, não no servidor**
`setTimeout` em `motorista.js` com 90s. O servidor é stateless para alertas — ele só repassa eventos. Simplifica muito e é suficiente para a demo.

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
# → http://localhost:5000/demo
```

O servidor já está com o virtualenv criado e as dependências instaladas.

---

## O que falta

### Marco 4 — Hardware (próxima sessão)

1. Criar `rfid/rfid_reader.py` com:
   - Loop de leitura do UID via biblioteca `mfrc522`
   - `POST /api/rfid` ao servidor com `{ uid, stop_id }`
   - Debounce de 2 segundos entre leituras
   - `SERVER_URL` como constante no topo do arquivo
2. Conectar RC522 ao Pi (pinout documentado no README)
3. Testar 20 leituras seguidas antes do dia

O endpoint `/api/rfid` no servidor **já existe e já funciona** — testado via `curl`. O Pi só precisa fazer o POST.

### Marco 6 — Pitch

1. Gravar vídeo de backup da demo funcionando
2. Escrever roteiro palavra a palavra e cronometrar
3. Criar slides de visão (geofencing, GTFS-Realtime, Neo4j)
4. Ensaiar 3+ vezes

---

## Pontos de atenção para o pitch

- Abrir `/demo?demo=true` — a linha 110 já vem pré-selecionada, não perde tempo no palco
- O áudio (`speechSynthesis`) exige que o usuário tenha interagido com a página antes — clicar qualquer coisa antes de subir ao palco resolve
- O bipe do motorista usa `AudioContext` — mesma restrição de interação prévia do browser
- Se o Pi não responder em ~2 segundos: clicar o botão e seguir sem comentar

---

## Estado do repositório

Nenhum commit foi feito ainda. Todos os arquivos em `hermes/` são untracked.
Os arquivos de planejamento na raiz (`HERMES_plano.md`, `PLANEJAMENTO_HERMES.md`, `README.md`, `SPEC.md`) também estão untracked.

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
