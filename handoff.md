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
