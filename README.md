# HERMES — Protótipo de Demonstração

Sistema de Acessibilidade por Proximidade e Integração de Dados — transporte público do DF.

Protótipo enxuto para o pitch (3 minutos) e base do projeto de faculdade.
O foco da demo é **um único momento**: o passageiro se identifica na parada (cartão RFID ou toque)
e o painel do motorista acende **em tempo real** com um alerta de embarque assistido.

---

## Arquitetura da demo

Um único evento de solicitação de embarque, com duas origens possíveis:

| Origem | Como | Papel |
|---|---|---|
| `button` | clique na tela da parada | plano B infalível |
| `rfid` | leitura do cartão no Raspberry Pi | caminho de impacto |

O servidor trata as duas igual. Se o RFID falhar no palco, você clica e ninguém percebe.

---

## Como rodar

```bash
cd hermes
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python backend/app.py
```

| URL | O que é |
|---|---|
| `http://localhost:5000/demo` | **Tela do pitch** — parada à esquerda, motorista à direita |
| `http://localhost:5000/versus` | **Comparação animada** — sistema atual vs HERMES (loop automático) |
| `http://localhost:5000/demanda` | **Mapa de demanda** — horário de pico, despacho dinâmico vs escala fixa |
| `http://localhost:5000/` | Tela da parada (isolada) |
| `http://localhost:5000/motorista` | Painel do motorista (isolado) |
| `http://localhost:5000/api/data` | JSON com linhas e paradas |

**Dica para o pitch:** abra `/demo?demo=true` — a linha 110 já vem pré-selecionada.

---

## Como ligar o Raspberry Pi (RC522)

No Raspberry Pi (não na sua máquina):

```bash
sudo raspi-config        # Interface Options → SPI → habilitar
pip3 install mfrc522 RPi.GPIO requests
```

1. Descubra o IP do notebook: `ip addr` ou `ifconfig`
2. Edite `rfid/rfid_reader.py` → constante `SERVER_URL` com esse IP
3. Rode no Pi: `python3 rfid/rfid_reader.py`
4. Encoste o cartão — o alerta aparece no painel do motorista no notebook

**Pinout RC522 → Pi:** SDA→GPIO8, SCK→GPIO11, MOSI→GPIO10, MISO→GPIO9, GND→GND, RST→GPIO25, 3.3V→3.3V

**Rede:** Pi e notebook na MESMA rede. Não confie no wi-fi do evento —
leve um roteador próprio ou use o notebook como hotspot.

---

## Estrutura

```
hermes/
├── backend/
│   └── app.py                    # Flask + SocketIO — 5 rotas HTTP, 1 endpoint REST, 3 eventos
├── frontend/
│   ├── demo.html                 # tela do pitch (parada + motorista lado a lado)
│   ├── parada.html               # tela isolada da parada
│   ├── motorista.html            # painel isolado do motorista
│   ├── versus.html               # comparação animada: acessibilidade + bunching vs HERMES
│   ├── demanda.html              # mapa de demanda: horário de pico vs despacho dinâmico
│   └── static/
│       ├── css/style.css         # paleta alto contraste, animações, estados dos alertas
│       └── js/
│           ├── parada.js         # botão, cancelar, Web Speech API
│           └── motorista.js      # cartões, bipe Web Audio, expiração, confirmar
├── rfid/
│   └── rfid_reader.py            # script do Raspberry Pi (RC522) — a criar no Marco 4
├── data/
│   └── transit_data.json         # 4 linhas reais do DF, formato GTFS-friendly
├── tests/
│   ├── conftest.py               # fixtures Flask + SocketIO test client
│   ├── test_routes.py            # rotas HTTP e páginas HTML
│   ├── test_events.py            # eventos SocketIO (button, resolve, cancel, rfid)
│   ├── test_helpers.py           # funções internas (_build_payload, _find_stop_name)
│   └── test_data.py              # integridade do transit_data.json
└── requirements.txt
```

---

## Páginas visuais (para o pitch)

| Página | Quando usar no pitch | O que mostra |
|---|---|---|
| `/demo?demo=true` | **Demo ao vivo (1:30–2:30)** | Parada + painel do motorista, fluxo RFID/botão em tempo real |
| `/versus` | **Problema (0:00–1:00)** | Acessibilidade: ônibus que passa vs HERMES que para + bunching vs headway regulado |
| `/demanda` | **Virada da ideia (1:00–1:30)** | Mapa de rotas do DF: pico sem GTFS-RT vs despacho dinâmico |

---

## O que é real x o que é visão

| Componente | Na demo | Visão (slide) |
|---|---|---|
| Solicitação na parada | ✅ botão web | hardware embarcado nos abrigos |
| Solicitação via RFID | ✅ endpoint pronto; falta script Pi | leitores NFC nos totens |
| Áudio de acessibilidade | ✅ Web Speech API (`pt-BR`) | — |
| Alerta em tempo real | ✅ Flask-SocketIO | terminal de bordo real |
| Rótulo neutro (LGPD) | ✅ "Embarque assistido" | — |
| Ciclo de vida do alerta | ✅ confirmar / cancelar / expirar | — |
| Visualização acessibilidade | ✅ `/versus` canvas animado | — |
| Visualização bunching | ✅ `/versus` seção GTFS-RT | — |
| Visualização demanda de pico | ✅ `/demanda` mapa animado | — |
| Geofencing (raio 500m) | slide | GPS real da frota |
| GTFS-Realtime feed real | slide | feed unificado das concessionárias |
| Despacho dinâmico / ML | slide | fase futura |
| Grafo Neo4j / matriz O-D | slide | fase futura |

---

## Testes

```bash
cd hermes && source venv/bin/activate
pytest tests/ -v          # 110 testes, todos devem passar
```

Cobertura: rotas HTTP, eventos SocketIO (broadcast para 2 clientes), helpers internos, integridade do JSON de dados.

---

## Checklist do dia da apresentação

- [ ] Servidor rodando (`python backend/app.py`)
- [ ] Abas abertas em tela cheia: `/versus`, `/demanda`, `/demo?demo=true`
- [ ] Som do notebook ligado (áudio Web Speech é parte do impacto)
- [ ] Pi conectado e testado **antes** de subir ao palco (5 leituras de teste)
- [ ] Vídeo/GIF de backup da demo funcionando, aberto em outra aba
- [ ] Se o Pi não responder em ~2s: clicar o botão e seguir sem comentar
