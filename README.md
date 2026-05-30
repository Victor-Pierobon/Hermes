# HERMES — Protótipo de Demonstração

Sistema de Acessibilidade por Proximidade e Integração de Dados -codinome: HERMES- — transporte público do DF.

Este é o protótipo enxuto para o pitch (3 minutos) e base do projeto de faculdade.
O foco da demo é **um único momento**: o passageiro se identifica na parada (cartão RFID
ou toque) e o painel do motorista acende **em tempo real** com um alerta de embarque assistido.

## Arquitetura da demo (o ponto importante)

Existe **um único evento** de solicitação de embarque, com **duas origens possíveis**:

- `button` — clique na tela da parada → **caminho seguro / plano B**
- `rfid` — leitura do cartão no Raspberry Pi → **caminho de impacto**

O servidor trata as duas igual. Se o RFID falhar no palco, você clica e ninguém percebe.
Construa e confie no botão primeiro; o RFID é a cereja do bolo.

## Como rodar (no notebook)

```bash
pip install -r requirements.txt
cd backend
python app.py
```

Abra a tela do pitch: **http://localhost:5000/demo**
(Tela única com a parada à esquerda e o painel do motorista à direita, lado a lado.)

Telas separadas, se quiser projetar em dois lugares:
- Parada:     http://localhost:5000/
- Motorista:  http://localhost:5000/motorista

## Como ligar o Raspberry Pi (RC522)

No Raspberry (não na sua máquina):

```bash
sudo raspi-config        # Interface Options -> SPI -> habilitar
pip3 install mfrc522 RPi.GPIO requests
```

1. Descubra o IP do notebook (`ip addr` / `ifconfig`).
2. Edite `rfid/rfid_reader.py` → `SERVER_URL` com esse IP.
3. Rode no Pi: `python3 rfid/rfid_reader.py`
4. Encoste o cartão. Deve aparecer no painel do motorista no notebook.

**Rede:** Pi e notebook na MESMA rede. Não confie no wi-fi do evento —
leve um roteador próprio ou use o notebook como hotspot.

## Checklist da demo (dia da apresentação)

- [ ] Servidor rodando e tela `/demo` aberta em tela cheia
- [ ] Som do notebook ligado (o áudio de acessibilidade é parte do impacto)
- [ ] Pi conectado e testado **antes** de subir ao palco (encostar o cartão ~5x)
- [ ] Vídeo/GIF de backup da demo funcionando, aberto em outra aba
- [ ] Se o Pi não responder em ~2s: clicar o botão e seguir sem comentar
- [ ] Linha pré-selecionada (110 — UnB) para não perder tempo escolhendo

## O que é real x o que é visão (para o pitch)

| Componente | Na demo | Visão (slide) |
|---|---|---|
| Solicitação na parada | ✅ RFID real + botão | hardware embarcado nos abrigos |
| Áudio de acessibilidade | ✅ Web Speech API | — |
| Alerta em tempo real ao motorista | ✅ SocketIO | terminal de bordo real |
| Rótulo neutro (LGPD) | ✅ "Embarque assistido" | — |
| Geofencing (raio 500m) | slide | GPS real da frota |
| GTFS-Realtime | formato presente no código | feed unificado das concessionárias |
| Despacho dinâmico / ML | — | fase futura |
| Grafo Neo4j / matriz O-D | — | fase futura |

## Estrutura

```
sapid/
├── backend/app.py            # servidor Flask + SocketIO (evento único, 2 origens)
├── frontend/
│   ├── demo.html             # tela do pitch (parada + motorista lado a lado)
│   └── static/{css,js}/      # estilo e lógica
├── rfid/rfid_reader.py       # script do Raspberry Pi (RC522)
├── data/transit_data.json    # linhas, paradas, cartões (formato GTFS-friendly)
└── requirements.txt
```
