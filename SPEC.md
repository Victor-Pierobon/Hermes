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

## Marco 1 — Fluxo mínimo com botão

> Critério de conclusão: clicar o botão na tela da parada e ver o alerta aparecer no painel do motorista, sem recarregar página.

### 1.1 Ambiente e dependências

- [ ] Criar a pasta `hermes/` e subpastas conforme estrutura acima
- [ ] Criar e ativar virtualenv Python (`python -m venv venv`)
- [ ] Instalar dependências: `flask flask-socketio eventlet`
- [ ] Criar `requirements.txt` com as versões fixadas (`pip freeze > requirements.txt`)

### 1.2 Servidor (`backend/app.py`)

- [ ] Subir Flask com Flask-SocketIO
- [ ] Rota `GET /` → serve `frontend/parada.html` (ou `demo.html` no modo unificado)
- [ ] Rota `GET /motorista` → serve `frontend/motorista.html`
- [ ] Rota `GET /demo` → serve `frontend/demo.html` (tela unificada para o pitch)
- [ ] Rota `POST /api/rfid` → recebe `{ uid }`, gera solicitação e emite evento SocketIO (para o Marco 4)
- [ ] Evento SocketIO `button_request` → recebe `{ route_id, stop_id }`, monta payload e emite `new_boarding_request` para todos os clientes
- [ ] Payload de `new_boarding_request`:
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
- [ ] Confirmar que o servidor sobe sem erro em `localhost:5000`

### 1.3 Dados estáticos (`data/transit_data.json`)

- [ ] Criar JSON com 4 linhas reais do DF no formato GTFS-friendly:
  ```json
  {
    "routes": [
      { "route_id": "110_UNB", "route_short_name": "110", "route_long_name": "UnB / Rodoviária" },
      ...
    ],
    "stops": [
      { "stop_id": "parada_w3_sul_502", "stop_name": "W3 Sul 502" },
      ...
    ]
  }
  ```
- [ ] Linhas sugeridas: 110 (UnB), 0.111 (Circular Asa Sul), 107 (Asa Norte), 160 (Ceilândia)
- [ ] Servidor carrega esse JSON na inicialização e o expõe via `GET /api/data`

### 1.4 Tela da parada (`frontend/`)

- [ ] `<select>` populado com as linhas vindas de `/api/data`
- [ ] Botão grande "Solicitar Embarque Assistido"
- [ ] Ao clicar: emitir evento `button_request` via SocketIO com `route_id` e `stop_id` fixo da demo
- [ ] Desabilitar o botão enquanto a solicitação está ativa (evitar spam)

### 1.5 Tela do motorista (`frontend/`)

- [ ] Área de alertas inicialmente vazia com texto placeholder "Nenhuma solicitação ativa"
- [ ] Ao receber `new_boarding_request`: criar um cartão de alerta com `route_name`, `stop_name` e horário
- [ ] Remover o placeholder quando o primeiro alerta chegar

### 1.6 Tela unificada para o pitch (`frontend/demo.html`)

- [ ] Layout lado a lado: parada à esquerda, painel do motorista à direita
- [ ] Reutiliza a mesma lógica de `parada.js` e `motorista.js` (não duplicar código)
- [ ] Label visual distinguindo os dois lados ("Parada — W3 Sul 502" / "Painel do Motorista")

**Teste de conclusão do Marco 1:** abrir `/demo` em duas abas, clicar o botão numa, ver o alerta aparecer na outra em < 1 segundo.

---

## Marco 2 — Acessibilidade (alma da ideia)

> Critério: a demo conta a história sozinha, mesmo sem explicar em voz alta.

### 2.1 Áudio na parada (Web Speech API)

- [ ] Ao solicitar embarque, falar via `speechSynthesis` (idioma `pt-BR`):
  `"Embarque assistido solicitado. Linha [nome da linha]."`
- [ ] Garantir que o áudio só dispara após interação do usuário (requisito do browser para autoplay)
- [ ] Ao cancelar solicitação, falar: `"Solicitação cancelada."`

### 2.2 Bipe de atenção no painel do motorista

- [ ] Gerar um tom curto (~200ms, ~880Hz) via Web Audio API quando um alerta chega
- [ ] Não usar arquivo de áudio externo — gerar programaticamente (sem dependência)

### 2.3 Rótulo neutro (LGPD)

- [ ] O cartão de alerta exibe apenas `"Embarque assistido"` — nunca diagnóstico, deficiência ou condição
- [ ] Nome do passageiro: não exibir. A associação UID → perfil fica só no servidor
- [ ] Informações no cartão: linha, parada, horário da solicitação, origem (`Parada` ou `RFID`)

### 2.4 Acessibilidade da própria interface

- [ ] Foco visível no teclado em todos os elementos interativos
- [ ] Contraste mínimo WCAG AA (razão 4.5:1) nos textos principais
- [ ] `aria-live="polite"` na área de confirmação da parada (anuncia para leitores de tela)
- [ ] `aria-live="assertive"` na área de alertas do motorista
- [ ] Botão de solicitar com `role="button"` e label descritivo

**Teste de conclusão do Marco 2:** mostrar a demo para alguém sem explicar nada; a pessoa deve entender o problema e a solução só assistindo.

---

## Marco 3 — Ciclo de vida do alerta

> Critério: o painel do motorista não acumula alertas eternamente; cada um tem estado claro.

### 3.1 Estados de um alerta

- [ ] Definir 3 estados: `pendente` (amarelo/laranja) → `atendido` (verde) → `expirado` (cinza)
- [ ] Cada estado tem cor e ícone distintos

### 3.2 Confirmação pelo motorista

- [ ] Botão "Confirmar atendimento" em cada cartão de alerta
- [ ] Ao clicar: emitir `resolve_request` com `{ id }` via SocketIO
- [ ] Servidor emite `request_resolved` com `{ id }` para todos os clientes
- [ ] Tela da parada recebe `request_resolved` e libera o botão de solicitar novamente

### 3.3 Expiração automática

- [ ] Após 90 segundos sem confirmação, o alerta passa para estado `expirado`
- [ ] Implementar com `setTimeout` no cliente (não precisa de lógica no servidor)
- [ ] Alerta expirado some após mais 10 segundos (fade-out)

### 3.4 Cancelamento pelo passageiro

- [ ] Botão "Cancelar" na tela da parada enquanto há solicitação ativa
- [ ] Emite `cancel_request` com `{ id }` para o servidor
- [ ] Servidor emite `request_cancelled` para todos; alerta no painel é removido
- [ ] Áudio: `"Solicitação cancelada."`

**Teste de conclusão do Marco 3:** fazer 3 solicitações seguidas; confirmar uma, cancelar outra, deixar a terceira expirar. Todos os estados devem funcionar corretamente.

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

### 4.4 Servidor — endpoint `/api/rfid`

- [ ] Receber `{ uid, stop_id }`
- [ ] Mapear UID para linha padrão (qualquer UID desconhecido assume linha 110 — UnB)
- [ ] Montar o mesmo payload de `new_boarding_request`, com `origin: "rfid"`
- [ ] Emitir o evento para todos os clientes via SocketIO

### 4.5 Rede

- [ ] Testar Pi e notebook na mesma rede (hotspot do notebook como fallback)
- [ ] Testar leitura 20 vezes seguidas antes do dia da apresentação
- [ ] Documentar IP fixo ou hostname do notebook para o script do Pi

**Teste de conclusão do Marco 4:** encostar o cartão 5 vezes seguidas; todas as 5 devem aparecer no painel do motorista. Clicar o botão após isso também deve funcionar.

---

## Marco 5 — Polimento visual e dados

> Critério: a tela é apresentável; juiz vê cuidado no detalhe.

### 5.1 Visual geral

- [ ] Paleta de alto contraste (fundo escuro ou branco puro, sem cinza médio)
- [ ] Tipografia forte e grande (mínimo 16px corpo, 24px+ títulos)
- [ ] Botão "Solicitar" impossível de ignorar (grande, cor de destaque)
- [ ] Logo/nome "HERMES" discreto no topo

### 5.2 Cartão de alerta do motorista

- [ ] Ícone de acessibilidade (♿ ou similar) no cartão
- [ ] Linha em destaque (maior, negrito)
- [ ] Parada + horário em tamanho menor
- [ ] Badge de origem (`Parada` ou `RFID`) — diferencia as origens visualmente
- [ ] Animação de entrada (slide-in ou fade-in simples, sem biblioteca)

### 5.3 Dados reais do DF

- [ ] Confirmar nomes e códigos das 4 linhas em gtfs.dfmob.df.gov.br ou DFTrans
- [ ] Parada da demo: W3 Sul 502 (plausível para o contexto do pitch)
- [ ] Pré-selecionar linha 110 — UnB no `<select>` da parada

### 5.4 Modo demo

- [ ] Parâmetro `?demo=true` na URL carrega a linha pré-selecionada automaticamente
- [ ] Evita perder tempo escolhendo linha no palco

**Teste de conclusão do Marco 5:** mostrar a tela para alguém externo ao projeto; deve parecer produto, não protótipo escolar.

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

## Ordem de execução sugerida

```
Semana 1 (dias 1-7):   Marcos 1, 2, 3  →  software 100% funcional só no notebook
Semana 2 (dias 8-11):  Marco 4          →  hardware Pi + RFID
Semana 2 (dias 12-14): Marcos 5, 6      →  polimento + pitch
```

---

## Armadilhas para não cair

- Não codificar geofencing, mapa animado ou grafo — vira slide
- Não remover o botão — é o plano B; se a demo só funciona com RFID, um problema de rede te derruba
- Não escrever no cartão RFID — somente leitura do UID
- Não testar o hardware só na véspera
- Não subir ao palco sem o vídeo de backup gravado e aberto
