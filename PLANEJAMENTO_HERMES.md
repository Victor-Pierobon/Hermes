# Planejamento de Desenvolvimento — HERMES (versão hackathon / faculdade)

Guia para você construir o protótipo **passo a passo, aprendendo no caminho**.
Não é código pronto: é o mapa. Cada etapa diz *o que* fazer, *por que*, e deixa
as decisões e a implementação com você. Quando travar num ponto específico,
volte aqui, releia o "por quê", e só então procure ajuda pontual.

---

## 0. Antes de escrever qualquer linha — entenda o alvo

**A demo inteira existe para entregar UM momento, ao vivo, em ~1 minuto:**

> O passageiro se identifica na parada (encosta o cartão RFID, ou toca um botão).
> Um áudio confirma. E o painel do motorista, em outra tela, **acende na hora**
> com um alerta de embarque assistido.

Tudo o que você construir deve servir esse momento. Se algo não aparece nesse
minuto, não merece código agora — vira slide de "visão".

**Princípio de arquitetura que protege a apresentação:** existe **um único
evento** de "solicitação de embarque", com **duas origens** possíveis — o botão
e o RFID. O servidor trata as duas igual. Construa o botão primeiro (é o seu
plano B infalível); o RFID entra depois como a mesma coisa por outro gatilho.

**Stack escolhida e por quê:**
- **Flask** — você já conhece (sovereign-quarrel), curva zero.
- **Flask-SocketIO** — para o "aparece na hora na outra tela" sem ficar
  perguntando ao servidor de tempos em tempos (polling). É o coração técnico.
- **HTML/CSS/JS puro** — sem framework, sem build, sem perder tempo.
- **Web Speech API** (nativa do navegador) — áudio de acessibilidade de graça.
- **Raspberry Pi OS + RC522** — só na fase final, e opcional para a ideia funcionar.

---

## Marco 1 — O fluxo mínimo, só com botão (o coração)

> Meta: clicar um botão numa tela e ver um alerta aparecer **em tempo real**
> noutra tela. Quando isso funcionar, 70% do valor da demo está garantido.

### 1.1 Ambiente
- [ ] Crie a pasta do projeto e um ambiente virtual Python (`python -m venv venv`).
      **Por quê:** isola as dependências; é boa prática que você vai levar pra vida.
- [ ] Instale `flask` e `flask-socketio`. Anote tudo num `requirements.txt`.
- [ ] **Aprendizado do dia:** leia 10 minutos sobre o que é WebSocket e por que
      ele difere de uma requisição HTTP normal. Isso explica *por que* o alerta
      consegue ser empurrado do servidor para a tela sem a tela pedir.

### 1.2 Servidor esqueleto
- [ ] Faça um `app.py` que sobe um Flask com SocketIO e serve uma página em `/`.
- [ ] Confirme que abre no navegador. Não avance enquanto isso não funcionar.

### 1.3 As duas telas
- [ ] Decida o layout: o mais forte para o pitch é **uma página só** com a parada
      à esquerda e o painel do motorista à direita, lado a lado. (Você também
      pode fazer duas páginas separadas depois, mas comece com a única.)
- [ ] Lado parada: um seletor de linha + um botão grande "Solicitar embarque".
- [ ] Lado motorista: uma área vazia que vai receber os alertas.

### 1.4 O evento viajando de um lado ao outro
- [ ] No JS da parada: ao clicar o botão, **emita** um evento via socket para o
      servidor (algo como `button_request`) levando a linha escolhida.
- [ ] No servidor: **escute** esse evento. Ao recebê-lo, monte um "payload" com
      os dados da solicitação (id único, linha, parada, hora) e **emita de volta**
      um evento (`new_boarding_request`) para todos os clientes conectados.
- [ ] No JS do motorista: **escute** `new_boarding_request` e crie um cartão de
      alerta na tela.
- [ ] **Ponto de aprendizado central:** repare no ciclo
      `cliente emite → servidor escuta → servidor emite → cliente escuta`.
      Esse ida-e-volta é o conceito que sustenta o projeto inteiro. Entenda-o
      bem antes de seguir; o resto são variações disso.

✅ **Fim do Marco 1:** você clica de um lado e o alerta nasce do outro, na hora.
Esse é o seu plano B já pronto. Comemore — o risco técnico maior morreu aqui.

---

## Marco 2 — Acessibilidade de verdade (o que dá alma à ideia)

> Meta: o fluxo deixar de ser "dois botões" e virar "isso resolve um problema
> real de uma pessoa que não enxerga o ônibus chegar".

### 2.1 Áudio na parada
- [ ] Use a **Web Speech API** (`speechSynthesis`) para falar, ao solicitar:
      a linha escolhida e a confirmação ("Embarque assistido solicitado").
- [ ] Defina o idioma como `pt-BR`.
- [ ] **Por quê isso importa no pitch:** o som faz o juiz *sentir* a experiência
      de quem usa leitor de tela. É barato de implementar e alto de impacto.

### 2.2 Som de atenção no painel do motorista
- [ ] Quando um alerta chega, toque um bipe curto. Pode ser um arquivo de áudio
      ou um tom gerado via Web Audio API. Pesquise "Web Audio API beep" e implemente.
- [ ] **Por quê:** o motorista pode não estar olhando a tela; o som chama atenção.

### 2.3 Rótulo neutro (decisão de privacidade — bom no pitch)
- [ ] O alerta mostrado ao motorista **não deve** dizer o diagnóstico da pessoa.
      Mostre algo neutro como "Embarque assistido". A condição é dado sensível (LGPD).
- [ ] **Aprendizado/discussão:** pense sobre por que separar "o que o sistema sabe"
      de "o que o motorista vê". Isso é um argumento forte na apresentação.

### 2.4 Acessibilidade básica da própria interface
- [ ] Garanta foco visível no teclado, alto contraste e que o botão seja grande.
- [ ] Pesquise "aria-live" e aplique na região onde aparecem confirmações, para
      que leitores de tela anunciem as mudanças.

✅ **Fim do Marco 2:** a demo já conta a história sozinha, mesmo sem hardware.

---

## Marco 3 — Ciclo de vida do alerta (mostra maturidade de produto)

> Meta: o alerta não fica eternamente na tela. Ele tem começo, meio e fim.

- [ ] Adicione um botão "Confirmar atendimento" em cada alerta do motorista.
- [ ] Ao clicar: emita um evento ao servidor (`resolve_request` com o id) e, de
      volta, marque aquele alerta como atendido (mude a cor, desabilite o botão).
- [ ] **Por quê:** sem isso, o painel vira uma pilha infinita de avisos e o
      motorista ignora tudo ("fadiga de alerta"). Mostrar que você pensou nisso
      diferencia você de quem só fez a tela bonita.
- [ ] (Opcional) Expiração automática após X segundos.

✅ **Fim do Marco 3:** o software está completo para a ideia. Daqui pra frente é
hardware (opcional), polimento e pitch.

---

## Marco 4 — O Raspberry Pi e o RFID (impacto físico, mas com rede de segurança)

> Meta: encostar um cartão físico no lugar de clicar o botão. **Regra de ouro:
> o botão continua existindo e fazendo a mesma coisa.** Se o Pi falhar no palco,
> você clica e ninguém percebe.

### 4.1 Preparar o Pi (primeira vez com Raspberry — vá com calma)
- [ ] Sistema: **Raspberry Pi OS com Desktop**, gravado pelo **Raspberry Pi Imager**.
- [ ] No Imager, nas configurações avançadas (engrenagem), pré-configure
      **wi-fi, SSH e usuário/senha**. Isso permite usar o Pi sem monitor, por SSH.
- [ ] Primeira inicialização: `sudo apt update && sudo apt full-upgrade`.
- [ ] Habilite o SPI: `sudo raspi-config` → Interface Options → SPI.
      **Por quê:** o leitor RC522 (o azul) conversa com o Pi pelo barramento SPI.

### 4.2 Ligar o leitor RC522
- [ ] Pesquise "RC522 Raspberry Pi pinout" e conecte os fios conforme o diagrama.
      Confira duas vezes — fio trocado é o erro nº 1 e não queima nada, só não lê.
- [ ] Instale a biblioteca de leitura (procure `mfrc522` no PyPI). Em Raspberry Pi
      OS recente, o pip pode reclamar de "externally-managed-environment"; nesse
      caso use um venv ou instale via apt. **Aprendizado:** entenda por que sistemas
      novos protegem o Python do sistema.

### 4.3 Ler o cartão — SOMENTE LEITURA (requisito do professor)
- [ ] Use **apenas a leitura do UID** do cartão (procure `read_id` na biblioteca).
      **Nunca** escreva no cartão. O UID é o número de série de fábrica, imutável;
      ler não altera nada e o cartão continua reutilizável.
- [ ] A associação "qual UID = qual perfil de passageiro" mora **no seu servidor**,
      nunca no cartão. Isso atende o professor E é o modelo correto de privacidade.
- [ ] **Decisão para a demo:** faça o servidor aceitar qualquer UID (assumindo o
      perfil padrão "deficiência visual") para não correr o risco de o leitor pegar
      um cartão não cadastrado no meio da apresentação. Cadastro fino fica opcional.

### 4.4 Conectar Pi → servidor
- [ ] O script do Pi, ao ler um cartão, faz um POST HTTP para um endpoint do seu
      servidor (ex.: `/api/rfid`) com o UID. Esse endpoint dispara **o mesmo**
      evento de solicitação que o botão dispara. **É aqui que a "origem única,
      gatilhos múltiplos" se paga.**
- [ ] **Rede — o ponto que mais derruba demos:** Pi e notebook precisam estar na
      mesma rede e enxergar um ao outro. **Não confie no wi-fi do evento.** Leve um
      roteador próprio, ou transforme o notebook em hotspot e conecte o Pi nele.
      Descubra o IP do notebook (`ip addr`) e coloque no script do Pi.
- [ ] Teste a leitura **20 vezes seguidas** para conhecer o tempo de resposta e os
      modos de falha *antes* do dia da apresentação.

✅ **Fim do Marco 4:** encostar o cartão dispara o alerta, e o botão continua como
backup silencioso.

---

## Marco 5 — Polimento visual e dados

> Meta: deixar apresentável. O juiz vê a tela; capricho aqui rende.

- [ ] Dados: crie um arquivo (JSON) com 3-4 linhas reais do DF e a parada da demo
      (ex.: W3 Sul). Use nomes/códigos de linha plausíveis — pesquise no DFTrans.
      **Dica:** estruture os campos parecidos com o padrão **GTFS** (route_id,
      stop_id, etc.). Custa pouco e te dá um argumento de "já nascemos no padrão
      que a Lei 7.836/2025 exige".
- [ ] Visual: alto contraste (combina com o tema acessibilidade), tipografia forte,
      um botão de "solicitar" impossível de ignorar. Evite o visual genérico.
- [ ] Pré-selecione a linha da demo para não perder tempo escolhendo no palco.

---

## Marco 6 — Pitch e blindagem (o que de fato ganha hackathon)

> Você tem **3 minutos**. Distribuição sugerida: ~60s problema · ~30s a virada
> da ideia · ~60s demo ao vivo · ~30s visão e fechamento.

- [ ] **Roteiro escrito**, palavra por palavra, e cronometrado. Ensaie 3+ vezes.
- [ ] **Backup obrigatório:** grave um vídeo/GIF da demo funcionando (com o RFID).
      Se tudo falhar no palco, você roda o vídeo e segue. Sem isso, não suba.
- [ ] Ensaie a frase mental: "se o Pi não responder em ~2 segundos, eu clico o
      botão e continuo, sem comentar". Naturalidade no plano B é o que separa
      uma demo tranquila de um desastre.
- [ ] Slides curtos para a parte "visão" (o que NÃO está no protótipo):
      geofencing por GPS, despacho dinâmico/ML, grafo Neo4j com matriz O-D.
      Apresente como roadmap, não como promessa de que já existe.
- [ ] Abra o pitch pelo **problema humano**: hoje a sinalização de embarque é
      visual; quem não enxerga não sabe qual ônibus chegou para fazer sinal, e o
      motorista não sabe que aquela pessoa precisa daquela linha. O SAPID inverte:
      o sistema avisa o motorista. Essa frase é o seu gancho.

---

## Ordem realista nas 2 semanas

- **Semana 1:** Marcos 1 a 3 (todo o software). Termine a semana com a demo
  rodando 100% só no notebook. Esse é o maior risco; mate cedo.
- **Início da semana 2:** Marco 4 (Pi + RFID). É o que pode dar trabalho por ser
  hardware e rede; reserve folga.
- **Fim da semana 2:** Marcos 5 e 6 (polimento, vídeo de backup, pitch ensaiado).

---

## Armadilhas comuns (leia antes de cada marco)

- Querer construir o mapa/geofencing animado porque é "legal". Não cabe no minuto
  de demo e consome dias. Vire slide.
- Deixar o RFID virar dependência: se a demo *só* funciona com o cartão, um
  problema de rede te derruba. O botão sempre existe.
- Testar o hardware só na véspera. Teste cedo e muitas vezes.
- Escrever no cartão "para personalizar". Nunca. Só leitura do UID.
- Pitch não ensaiado. Protótipo robusto mal apresentado perde para ideia simples
  bem contada. O ensaio é parte do projeto, não um extra.

---

## Conceitos que você vai aprender (e levar pra vida)

- WebSockets e comunicação em tempo real (o coração do projeto).
- Arquitetura de "evento único, múltiplos gatilhos" (desacoplamento).
- Web Speech API e fundamentos de acessibilidade web (aria-live, foco, contraste).
- Comunicação entre dispositivos numa rede local (Pi → servidor via HTTP).
- Noções de SPI e leitura de RFID com Raspberry Pi.
- Por que separar dado sensível (no servidor) da identificação (o UID do cartão).
- O padrão GTFS e seu papel no transporte público — útil muito além deste projeto.
