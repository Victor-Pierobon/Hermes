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
| `http://localhost:5000/rfid/<arquivo>` | download dos arquivos do leitor para o Pi (sem SSH) |

**Dica para o pitch:** abra `/demo?demo=true` — a linha 110 já vem pré-selecionada.

---

## Como ligar o Raspberry Pi (RC522)

> O setup de hardware (gravar o SD, ligar o RC522, primeira leitura) e o registro
> da integração estão resumidos no [`handoff.md`](handoff.md) → "Marco 4".
> Esta seção é o **fluxo de software**: levar o leitor ao Pi e conectá-lo ao servidor.

**Pré-requisitos no Pi** (uma vez): SPI habilitado (`sudo raspi-config` → Interface
Options → SPI), e um venv em `~/hermes` com as libs:
```bash
mkdir -p ~/hermes && cd ~/hermes
python3 -m venv venv && source venv/bin/activate
pip install mfrc522 RPi.GPIO requests
```

### 1. Subir o servidor no PC e liberar a porta
```bash
cd hermes && source venv/bin/activate && python backend/app.py   # escuta em 0.0.0.0:5000
sudo ufw allow 5000/tcp                                           # se houver firewall (ufw/firewalld)
```
Descubra o IP do PC na rede: `hostname -I` (ex.: na nossa montagem foi `10.116.31.40`).

### 2. Levar os arquivos ao Pi — **sem SSH**
O próprio servidor serve os arquivos do leitor em `/rfid/<arquivo>`. No **Pi**:
```bash
cd ~/hermes
curl -fsSL http://<IP_DO_PC>:5000/rfid/rfid_reader.py    -o rfid_reader.py
curl -fsSL http://<IP_DO_PC>:5000/rfid/instalar_no_pi.sh -o instalar_no_pi.sh
```
> Use `curl -fsSL ... -o arquivo` (não `wget`): evita que o log do download
> acabe gravado dentro do arquivo. Confira com `head -3 rfid_reader.py`.

### 3a. Teste rápido (rodando à mão)
```bash
source venv/bin/activate
SERVER_URL=http://<IP_DO_PC>:5000/api/rfid python3 rfid_reader.py
```
Encoste o cartão — o terminal mostra `✔ solicitação enviada` e o painel do
motorista (`/demo?demo=true` no PC) acende com **"Embarque assistido"**.

### 3b. Autostart no boot (para o dia da apresentação) — **sem teclado/tela**
```bash
bash instalar_no_pi.sh http://<IP_DO_PC>:5000/api/rfid
```
Instala um serviço systemd (`hermes-rfid`) que sobe o leitor sozinho a cada boot,
reinicia se cair e fica reenviando sem travar se o servidor ainda não estiver no ar.
Depois disso, no dia: **liga o Pi na tomada e pronto** — nenhum terminal abre, é
em segundo plano. Verifique com:
```bash
systemctl status hermes-rfid          # deve estar "active (running)"
journalctl -u hermes-rfid -f          # acompanha as leituras
```

**Pinout RC522 → Pi (pinos físicos):** SDA→24, SCK→23, MOSI→19, MISO→21,
RST→22, GND→6, 3.3V→1. IRQ não conecta. ⚠️ Alimente em **3.3V**, nunca 5V.

### Rede — o ponto mais crítico
Pi e PC na MESMA rede. Não confie no wi-fi do evento — **use o PC como hotspot,
um roteador próprio, ou roteie pelo celular** (foi o que usamos: hotspot do celular,
ambos em `10.116.31.0/24`).

- **Endereço do servidor:** prefira o **IP** do PC (`SERVER_URL=http://<IP>:5000/api/rfid`).
  O nome mDNS `nitrov.local` (default do script) só é confiável se resolver por
  IPv4 — em hotspot de celular ele costuma vir só por IPv6, e o servidor escuta
  apenas IPv4, então o IP direto é mais garantido.
- **IP estável:** enquanto o PC ficar conectado, mantém o mesmo IP. Para blindar
  contra o PC reiniciar e mudar de IP, fixe um IP estático no PC para esse hotspot
  (NetworkManager → conexão → IPv4 manual).
- **Plano B infalível:** se o Pi/rede falhar no palco, o **botão da tela** dispara
  o mesmo alerta. Clique e siga sem comentar.

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
│   ├── rfid_reader.py            # script do Raspberry Pi (RC522): lê o UID e faz POST /api/rfid
│   └── instalar_no_pi.sh         # instala o autostart no boot (serviço systemd hermes-rfid)
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
| Solicitação via RFID | ✅ Raspberry Pi + RC522, autostart no boot | leitores NFC nos totens |
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

- [ ] Hotspot ligado (mesmo nome/senha de sempre); PC e Pi conectados nele
- [ ] Servidor rodando (`python backend/app.py`) e porta 5000 liberada no firewall
- [ ] Conferir o IP do PC (`hostname -I`) e que bate com o `SERVER_URL` do Pi
- [ ] Pi alimentado (fonte 5V/2.5A ou power bank) — serviço sobe sozinho no boot
- [ ] Abas abertas em tela cheia: `/versus`, `/demanda`, `/demo?demo=true`
- [ ] Som do notebook ligado (áudio Web Speech é parte do impacto)
- [ ] Testar **antes** de subir ao palco (5 leituras de cartão de verdade)
- [ ] Vídeo/GIF de backup da demo funcionando, aberto em outra aba
- [ ] Se o Pi não responder em ~2s: clicar o botão e seguir sem comentar
