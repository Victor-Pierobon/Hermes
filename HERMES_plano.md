# Plano de Implementação: Sistema de Acessibilidade e Integração de Dados do Transporte Público do DF

## 1. Resumo Executivo

Este documento apresenta a especificação técnica e o plano de implantação do **Sistema de Acessibilidade por Proximidade e Integração de Dados (SAPID) codinome: HERMES** para o transporte público do Distrito Federal. O projeto utiliza o direito constitucional à acessibilidade universal (Lei nº 13.146/2015 — Lei Brasileira de Inclusão) como vetor de modernização tecnológica para impulsionar a reestruturação da infraestrutura de software, processamento e distribuição de dados de mobilidade do DF.

O HERMES ataca o gargalo histórico de autonomia de idosos e pessoas com deficiência visual e motora no embarque. Hoje, a sinalização de embarque é essencialmente visual: o passageiro enxerga o ônibus chegando e faz sinal com a mão. Para quem tem deficiência visual, esse é exatamente o ponto que quebra — a pessoa não identifica qual linha está chegando para sinalizar, e o motorista não tem como saber que aquela pessoa precisa daquela linha específica. O SAPID inverte essa lógica: em vez de o passageiro sinalizar para o motorista, o **sistema informa ao motorista** que há uma solicitação de embarque assistido naquela parada.

A proposta apoia-se em uma arquitetura baseada em dados em tempo real, algoritmos de grafos, Internet das Coisas (IoT) e roteamento dinâmico. Vale destacar que a base de dados necessária já existe parcialmente — o DFTrans já opera rastreamento de frota por GPS — e que a publicação de dados em padrão GTFS deixou de ser opcional: a Lei Distrital nº 7.836/2025 passou a exigir a disponibilização das informações de transporte público em formato de dados abertos e no padrão GTFS, o que fortalece juridicamente a tese central deste projeto.

## 2. Arquitetura Geral do Sistema (System Overview)

A arquitetura do HERMES é dividida em quatro camadas interdependentes, organizadas sob o paradigma de microsserviços, garantindo desacoplamento, escalabilidade e tolerância a falhas:

| Camada | Tecnologias Primárias | Responsabilidade Técnica |
|--------|----------------------|--------------------------|
| **1. Captura & Borda (Edge)** | RFID (Mifare/NFC), BLE Beacons, GPS de Borda (Automotivo) | Identificação do usuário na parada, geolocalização da frota e interface tátil/sonora nos abrigos. |
| **2. Ingestão & Streaming** | Apache Kafka, Protocolo GTFS-Realtime, Protobuf | Consumo de telemetria em tempo real (frequência de ~1Hz) enviada por ônibus e trens do Metrô-DF. |
| **3. Processamento & Inteligência** | Neo4j (Graph DB), Python (Scikit-Learn/NetworkX), PostgreSQL/PostGIS | Roteamento dinâmico, processamento espacial, cálculo de matriz Origem-Destino e cruzamento de dados de demanda. |
| **4. Distribuição (APIs & Apps)** | REST/GraphQL, JSON/Protobuf, Mobile Headless (iOS/Android) | Consumo por aplicativos de acessibilidade, painéis dos motoristas e barramento de dados abertos para terceiros. |

## 3. Detalhamento dos Componentes Tecnológicos

### 3.1. O Gatilho de Acessibilidade (RFID, NFC e BLE)

O subsistema de acessibilidade inverte a lógica de sinalização de embarque. Em vez de exigir que o passageiro identifique e sinalize visualmente o ônibus, é o sistema que comunica ao motorista a existência de uma solicitação. O usuário interage de duas formas:

- **Hardware Físico (RFID/NFC):** utilização dos cartões atuais do Passe Livre Especial e Sênior, equipados com chips RFID. Ao aproximar o cartão de um totem físico no abrigo de ônibus, o validador reconhece o ID do usuário (anonimizado em conformidade com a LGPD) e ativa um menu de áudio local para seleção da linha desejada.
- **Hardware Virtual (BLE/Beacons):** instalação de Beacons Bluetooth Low Energy nos abrigos das paradas. O smartphone do usuário (com leitor de tela ativado) detecta o abrigo a até ~15 metros, permitindo a solicitação de embarque de forma remota via app, sem necessidade de deslocamento até o totem.

Uma vez acionada a solicitação, um evento é publicado no broker de mensageria central, contendo o `Stop_ID` (identificador da parada) e o `Route_ID` (identificador da linha desejada).

### 3.2. Sinalização ao Motorista (Embarque Assistido)

Para que o evento gerado na parada seja útil, o sistema precisa saber exatamente onde estão os ônibus daquela linha específica. O projeto adota a unificação das frotas de todas as concessionárias do DF sob o padrão internacional **GTFS (General Transit Feed Specification)** e sua extensão **GTFS-Realtime** — caminho já amparado pela exigência legal da Lei Distrital nº 7.836/2025.

O microsserviço de *geofencing* calcula continuamente a distância dos veículos em relação às paradas com solicitações ativas. Quando um veículo da linha selecionada cruza o raio de aproximação (ex.: 500 metros) da parada correspondente, o sistema emite um **alerta de embarque assistido** no terminal de bordo do motorista — sonoro e visual.

**Princípio de desenho:** o alerta é informativo, não impositivo. O sistema não força parada obrigatória nem sobrescreve a decisão operacional do motorista; ele apenas enriquece o contexto que o motorista já tem, indicando que há alguém aguardando aquela linha e que se trata de um embarque que demanda atenção redobrada. A decisão de parar e o cumprimento dos procedimentos de acessibilidade permanecem com o motorista. Essa abordagem reduz drasticamente o atrito regulatório e contratual com as concessionárias, porque não altera regras de operação nem de tempo de ciclo das linhas.

**Privacidade e não-estigmatização (LGPD):** a condição de deficiência é um dado pessoal sensível. Por isso, o alerta apresentado ao motorista é deliberadamente neutro — algo como *"solicitação de embarque assistido na linha X"* — sem expor diagnóstico ou rótulo clínico. O motorista recebe a informação necessária para prestar o atendimento adequado, sem que a condição de saúde do passageiro seja explicitada. Para o usuário com deficiência visual, o que importa é que o ônibus pare e, idealmente, anuncie a linha em áudio.

**Ciclo de vida do alerta:** para evitar fadiga de alertas, cada solicitação tem ciclo de vida definido — o alerta expira automaticamente após o veículo atender ou passar pela parada, pode ser cancelado pelo próprio usuário caso desista, e admite confirmação de atendimento pelo motorista. Isso mantém o painel limpo e os avisos confiáveis.

Exemplo ilustrativo de evento no padrão GTFS-Realtime (alerta de serviço):

```json
{
  "id": "alert-alert_id_9921",
  "alert": {
    "active_period": { "start": 1779958320 },
    "informed_entity": [{
      "route_id": "110_UNB",
      "stop_id": "parada_w3_sul_502"
    }],
    "header_text": {
      "translation": [{
        "language": "pt-br",
        "text": "Solicitacao de embarque assistido na proxima parada."
      }]
    },
    "effect": "ACCESSIBILITY_ISSUE"
  }
}
```

### 3.3. Roteamento Dinâmico e Despacho Inteligente

Com a malha rodoviária e metroviária trafegando dados em tempo real sob o mesmo ecossistema, o HERMES implementa uma camada de Despacho Dinâmico. Modelos preditivos de *Machine Learning* analisam o fluxo histórico de tráfego de vias críticas (Estrutural, EPTG, EPTM, Epia) em conjunto com a densidade de passageiros coletada nas catracas eletrônicas.

Se o algoritmo detecta um atraso em cascata superior a 15 minutos em uma rota que possui solicitações de embarque assistido ativas, o sistema aciona automaticamente alertas para o Centro de Controle Operacional, sugerindo o envio de veículos reserva ou o redirecionamento de linhas alimentadoras para mitigar o tempo de espera do usuário vulnerável.

### 3.4. Análise de Malha por Banco de Dados de Grafos

A unificação dos dados de bilhetagem e das solicitações de acessibilidade permite estruturar a rede de transporte do DF como um grande **Grafo Direcionado** (nós = paradas/estações; arestas = trajetos/linhas de ônibus). Utilizando o banco de dados Neo4j, o sistema gera a matriz de Origem-Destino em janelas de near real-time.

Isso permite identificar matematicamente falhas de conexão intermodal (ex.: passageiros que desembarcam do metrô e aguardam tempos excessivos por um ônibus circular). A engenharia de transporte do DF passa a planejar novas linhas e horários com base no comportamento exato do fluxo populacional, eliminando linhas ociosas e reforçando trajetos sobrecarregados.

## 4. Cronograma de Execução e Fases do Projeto

*(Aplicável a um projeto real; para fins de hackathon, este cronograma é referencial.)*

| Fase | Duração | Entregáveis Principais |
|------|---------|------------------------|
| **Fase 1: Infraestrutura de Dados** | Meses 01 a 03 | Unificação dos feeds GPS das concessionárias; publicação das APIs GTFS e GTFS-Realtime públicas; configuração do broker Kafka. |
| **Fase 2: Hardware e Validação** | Meses 04 a 06 | Desenvolvimento do firmware dos totens RFID/NFC; instalação piloto de BLE Beacons; homologação dos cartões de Passe Livre Especial. |
| **Fase 3: Integração de Borda (Frota)** | Meses 07 a 09 | Atualização do software dos terminais de bordo dos ônibus; implementação do módulo de geofencing e do alerta de embarque assistido ao motorista. |
| **Fase 4: Inteligência e Analytics** | Meses 10 a 12 | Modelagem do grafo da malha de transporte no Neo4j; entrada em produção dos algoritmos de despacho dinâmico; lançamento do app headless. |

## 5. Considerações Finais e Próximos Passos

O HERMES transforma o investimento em acessibilidade em um investimento de modernização sistêmica. Ao ancorar o projeto na inclusão social e nos direitos das pessoas com deficiência — e aproveitando o momento regulatório favorável criado pela Lei Distrital nº 7.836/2025 —, criam-se os mecanismos jurídicos e orçamentários necessários para superar o atraso tecnológico histórico na gestão da mobilidade urbana do Distrito Federal.

O diferencial do desenho proposto está em entregar autonomia ao usuário sem impor mudanças operacionais às concessionárias: o sistema informa, o motorista decide. Isso entrega um sistema previsível, inteligente e verdadeiramente integrado para toda a população, mantendo-se juridicamente defensável e operacionalmente viável.

**Próximos passos sugeridos:** definir o protótipo a ser demonstrado no hackathon (sugestão: simular o fluxo solicitação → geofencing → alerta no painel do motorista), consumindo ou simulando um feed GTFS-Realtime.

---

## 6. Estudo de Viabilidade e Custo — Implantação Real no DF

> Estimativas em valores de mercado brasileiro (2026). Custos exatos de hardware
> são definidos em licitação; aqui usamos faixas de mercado com premissas explícitas.

### 6.1. Protótipo vs. sistema em produção

O que está no repositório (`hermes/`) é um **protótipo de demonstração** completo: o fluxo
`parada → servidor → motorista` em tempo real (Flask-SocketIO), acessibilidade (Web Speech,
LGPD, aria-live), ciclo de vida do alerta, RFID físico via Raspberry Pi e três telas de pitch
(`/demo`, `/versus`, `/demanda`). Isso prova o **conceito** — mas é ~1% do esforço de um sistema
em produção, que exige integrações com a frota, com as concessionárias e com a infraestrutura
do DFTrans.

A boa notícia para a viabilidade: **a parte mais cara do plano original já existe no DF.**

| Camada do plano | Já existe no DF? |
|---|---|
| GPS em tempo real da frota | ✅ Sim — o app **DF no Ponto** já mostra posição por GPS |
| Bilhetagem eletrônica / cartões RFID | ✅ Sim — Passe Livre Especial e Sênior já usam chip RFID |
| Terminal embarcado no ônibus | ✅ Parcial — frota já tem validador/MDT com tela |
| Publicação GTFS / dados abertos | ⚠️ Obrigatória pela Lei Distrital 7.836/2025, mas ainda imatura |
| Alerta de embarque assistido ao motorista | ❌ Não existe — **é a inovação do HERMES** |
| Totem de acionamento na parada | ❌ Não existe |

**Conclusão:** o HERMES não constrói a infraestrutura de dados do zero — acopla-se a uma base
que o DF já tem (GPS + bilhetagem + app) e que a lei agora obriga a abrir. Isso muda o projeto
de "obra de R$ centenas de milhões" para "camada de software + hardware de borda seletivo".
Tecnicamente é **viável**; o risco real é **institucional/contratual** (acordo com concessionárias
e DFTrans), não técnico.

### 6.2. Dimensionamento do DF

- **Frota:** ~2.689 ônibus
- **Paradas:** ~4.774 dentro do DF (5.434 no total da rede)
- **Terminais:** 26 + Rodoviária do Plano Piloto

### 6.3. Os três blocos de custo

**Bloco A — Hardware na parada (totem de acionamento).** A parte mais cara e a que mais escala
com o nº de paradas. Duas estratégias:

| Opção | O que é | Custo unitário instalado | Observação |
|---|---|---|---|
| **Totem físico** | Leitor NFC + áudio + botão tátil + modem 4G + energia solar + gabinete antivandalismo | **R$ 8.000 – 15.000** | Caro, mas inclui quem não tem smartphone |
| **Beacon BLE** | Etiqueta Bluetooth; acionamento pelo app do passageiro | **R$ 150 – 400** | Baratíssimo, mas exige smartphone com leitor de tela |

Recomendação: **híbrido** — totens nas paradas prioritárias, beacons no restante.

**Bloco B — Alerta no ônibus (lado do motorista).**
- Integração por **software** ao validador/MDT que a frota já tem → custo quase zero de hardware.
- Display dedicado, se necessário → R$ 1.500 – 3.000/ônibus.

**Bloco C — Plataforma de software + nuvem.**
- Desenvolvimento da plataforma SAPID (backend de eventos, geofencing, APIs GTFS-RT, painel de
  gestão): squad de ~6 pessoas por ~12 meses → **R$ 2,5 – 4 milhões** no ano 1.
- Nuvem/operação (Kafka, PostGIS, Neo4j, APIs): **R$ 15k – 40k/mês** → R$ 200k – 500k/ano.
- Conectividade dos totens (SIM 4G/IoT): ~R$ 20–40/totem/mês.

### 6.4. Cenários de custo

**Cenário 1 — Piloto real (1 corredor, ex.: W3 Sul / Eixo).** ~50 paradas-chave, ~100 ônibus.

| Item | Cálculo | Custo |
|---|---|---|
| 50 totens físicos | 50 × R$ 10k | R$ 500.000 |
| Integração nos 100 ônibus (software) | — | R$ 150.000 |
| Desenvolvimento da plataforma (MVP) | squad reduzido, 6 meses | R$ 1.000.000 |
| Nuvem + conectividade (1 ano) | — | R$ 150.000 |
| **Total piloto (CAPEX ano 1)** | | **≈ R$ 1,8 milhão** |

**Cenário 2 — Rollout DF (estratégia híbrida, realista).** ~800 paradas prioritárias com totem
+ beacons no restante + frota toda.

| Item | Cálculo | Custo |
|---|---|---|
| 800 totens físicos | 800 × R$ 10k | R$ 8.000.000 |
| ~4.000 beacons BLE | 4.000 × R$ 300 | R$ 1.200.000 |
| Integração nos 2.689 ônibus (software) | — | R$ 800.000 |
| Plataforma completa (geofencing, GTFS-RT, grafo, ML) | squad, 12 meses | R$ 3.500.000 |
| Nuvem + integração concessionárias (ano 1) | — | R$ 600.000 |
| **Total CAPEX** | | **≈ R$ 14 milhões** |
| **OPEX recorrente/ano** (conectividade, nuvem, suporte, manutenção) | | **≈ R$ 2 – 3 milhões/ano** |

**Cenário 3 — "Tudo totem" (todas as ~4.774 paradas).** Mostra por que **não** se faz assim:
4.774 × R$ 10k = **~R$ 48 milhões só em hardware de parada** — argumento de por que a estratégia
híbrida é a correta.

### 6.5. Veredito (DF)

| Dimensão | Avaliação |
|---|---|
| **Viabilidade técnica** | ✅ Alta. Nada exige tecnologia inédita; tudo é integração de peças que já existem. |
| **Viabilidade financeira** | ✅ Razoável. Piloto < R$ 2M; rollout ~R$ 14M CAPEX — pequeno frente ao orçamento de mobilidade do DF. |
| **Viabilidade regulatória** | ✅ Favorável. Lei 7.836/2025 (GTFS obrigatório) e Lei 13.146/2015 (acessibilidade) dão base jurídica e orçamentária. |
| **Maior risco** | ⚠️ **Institucional**, não técnico: acordo operacional com concessionárias e acesso ao feed GPS/bilhetagem do DFTrans. |

**Recomendação:** o caminho de menor risco é o **Cenário 1 (piloto de ~R$ 1,8M em um corredor)**,
usado para provar adesão e medir impacto antes de pedir o investimento de R$ 14M do rollout.

---

## 7. Estimativa Estendida — DF + Entorno (RIDE-DF)

### 7.1. O que o Entorno acrescenta (e por que é diferente)

O Entorno **não é "mais DFTrans"** — é outro sistema, com outro regulador e outra geografia:

| Fator | DF (DFTrans/Semob) | Entorno (RIDE-DF) |
|---|---|---|
| Regulador | Semob / DFTrans | **AGR-GO** (Goiás) + municípios + (3 cidades em MG) |
| Tipo de serviço | Urbano | **Semiurbano / intermunicipal** (linhas longas, BR-040, BR-060) |
| Abrangência | 1 ente | **33 municípios** (DF + 30 GO + 3 MG) |
| Densidade de paradas | Alta, urbana | Baixa, rodoviária e dispersa |
| Cobertura 4G | Boa | Irregular (trechos rurais) |

**Escala do Entorno:**
- **~1,5 milhão** de habitantes (era 960 mil em 2007, em forte crescimento)
- **~1.000 ônibus/dia** cruzam a divisa do DF (frota intermunicipal estimada em ~1.200–1.500 veículos)
- **33 municípios** na RIDE-DF (30 em Goiás, 3 em Minas Gerais)

Consequência prática: o fator que domina o custo do Entorno **não é hardware, é governança** —
exige acordo entre Semob/DFTrans, AGR-GO, prefeituras e duas UFs além do DF. **DF e Goiás já
estudam um consórcio para integrar o transporte do Entorno** — esse consórcio é o veículo
jurídico que tornaria o HERMES regional possível.

### 7.2. Incremento de custo do Entorno (sobre o rollout do DF)

Premissas: estratégia híbrida, ~500 paradas prioritárias, ~1.500 ônibus intermunicipais,
conectividade pior.

| Item | Cálculo | Custo |
|---|---|---|
| ~500 totens físicos (paradas-chave dos 33 municípios) | 500 × R$ 10k | R$ 5.000.000 |
| ~3.000 beacons BLE | 3.000 × R$ 300 | R$ 900.000 |
| Integração da frota intermunicipal (mais hardware: muitos veículos sem MDT moderno) | ~1.500 ônibus, mix software + display | R$ 1.500.000 |
| Camada de governança/integração (federar AGR-GO + DFTrans + municípios + GTFS multi-operador) | desenvolvimento + projeto | R$ 1.500.000 |
| Conectividade rural reforçada (ano 1) | — | R$ 400.000 |
| **Subtotal Entorno (CAPEX)** | | **≈ R$ 9,3 milhões** |

### 7.3. Total consolidado DF + Entorno

| Escopo | CAPEX (implantação) | OPEX (recorrente/ano) |
|---|---|---|
| Piloto (1 corredor) | R$ 1,8 milhão | incluído |
| **Rollout DF completo** | R$ 14 milhões | R$ 2 – 3 milhões |
| **+ Entorno (RIDE-DF)** | R$ 9,3 milhões | R$ 1,5 – 2 milhões |
| **TOTAL DF + Entorno** | **≈ R$ 23 milhões** | **≈ R$ 3,5 – 5 milhões/ano** |

> Faixa de planejamento honesta (contingência de 20–30% para licitação, reajuste e imprevistos
> de campo): **R$ 23 – 30 milhões de CAPEX** e **R$ 4 – 5 milhões/ano de OPEX**.

### 7.4. Cobertura total: híbrido vs. totem em todas as paradas

**Atenção:** os ~R$ 23–30 milhões acima **não** colocam totem físico em *todas* as paradas.
Esse número usa a **estratégia híbrida** de propósito — totem só nas paradas prioritárias
(~800 no DF + ~500 no Entorno) e **beacon BLE barato** no restante. A cobertura para o usuário
é a mesma (ele aciona o embarque assistido em qualquer parada); muda só o hardware.

Se a exigência for **um totem físico em cada parada**, o custo sobe de patamar:

| Item | Cálculo | Custo |
|---|---|---|
| DF — ~4.774 paradas | 4.774 × R$ 10k | ~R$ 47,7 milhões |
| Entorno — ~3.000 paradas (estimado) | 3.000 × R$ 10k | ~R$ 30 milhões |
| **Só hardware de totem** | | **~R$ 78 milhões** |
| + Plataforma, integração da frota, nuvem, governança | (igual ao rollout) | ~R$ 8 milhões |
| **CAPEX total "tudo totem"** | | **~R$ 86 milhões** |
| Com contingência 20–30% | | **R$ 90 – 110 milhões** |

E o **OPEX dispara junto**: ~7.800 totens × conectividade 4G + manutenção (bateria/solar,
vandalismo, reparo) ≈ **R$ 5 – 8 milhões/ano**.

| Abordagem | CAPEX | OPEX/ano | Cobre todas as paradas? |
|---|---|---|---|
| **Híbrida** (totem prioritário + beacon) | R$ 23 – 30 M | R$ 4 – 5 M | ✅ Sim — beacon onde não há totem |
| **Totem em tudo** | R$ 90 – 110 M | R$ 5 – 8 M | ✅ Sim — mas ~4× mais caro |

**Conclusão:** as duas abordagens cobrem 100% das paradas. A híbrida entrega a mesma cobertura
por ~¼ do preço — nas paradas de menor movimento, o acionamento é por beacon BLE (R$ 150–400)
via app em vez de um totem de R$ 10 mil. Os ~R$ 60–80 milhões economizados não compram
acessibilidade adicional; só trocariam um beacon que funciona por um totem caro em parada de
baixo movimento. **Recomendação: não fazer "totem em tudo".**

### 7.5. Sequência recomendada (faseamento reduz risco e custo de entrada)

| Fase | Escopo | CAPEX | Objetivo |
|---|---|---|---|
| **1. Piloto** | 1 corredor no DF (W3/Eixo) | ~R$ 1,8 M | Provar adesão e medir impacto |
| **2. Rollout DF** | Toda a rede DFTrans | ~R$ 14 M | Escala urbana, ancorada na Lei 7.836/2025 |
| **3. Entorno** | RIDE-DF via consórcio DF–GO | ~R$ 9,3 M | Integração metropolitana |

Fazer o Entorno **antes** do consórcio DF–GO estar formalizado seria o erro clássico: gastar em
hardware que esbarra em impasse regulatório entre estados. A Fase 3 deve ser destravada pela
governança, não pela engenharia.

### 7.6. Veredito do escopo regional

- **Custo da visão completa (DF + Entorno): ~R$ 23–30 milhões CAPEX + ~R$ 4–5 M/ano.** Para uma
  região metropolitana de ~4,5 milhões de pessoas, é investimento modesto — equivale ao custo de
  poucos quilômetros de via ou de um punhado de ônibus novos.
- **Risco técnico:** baixo (o mesmo do DF, replicado).
- **Risco dominante:** **interfederativo** — alinhar DF, Goiás (AGR), Minas e municípios. O
  consórcio já em estudo é o caminho; sem ele, a Fase 3 não anda por mais barata que seja.

### 7.7. Fontes consultadas

- Frota e paradas do DF — [Mapeando o Transporte Público Rodoviário do DF](https://medium.com/@kandebonfim/transporte-publico-do-distrito-federal-e8e1b18a7d6f)
- GPS em tempo real — [DF no Ponto (Semob)](https://dfnoponto.semob.df.gov.br/) · [DFTrans](https://dftrans.df.gov.br/aplicativo-permite-consultar-horarios-de-onibus-e-tracar-rotas-em-tempo-real/)
- Custos de energia solar — [Portal Solar (2026)](https://www.portalsolar.com.br/painel-solar-precos-custos-de-instalacao.html)
- Sistemas tecnológicos de transporte — [ANTP, Caderno Técnico nº 30](https://files.antp.org.br/2025/11/10/caderno-tecnico-n-30_v9-web-2.pdf)
- Consórcio DF–GO no Entorno — [Metrópoles](https://www.metropoles.com/distrito-federal/entorno/df-e-goias-estudam-consorcio-para-integrar-transporte-no-entorno)
- Composição da RIDE-DF — [Wikipédia](https://pt.wikipedia.org/wiki/Regi%C3%A3o_Integrada_de_Desenvolvimento_do_Distrito_Federal_e_Entorno) · [Agência Brasília](https://www.agenciabrasilia.df.gov.br/2018/06/15/ampliada-ride-tem-32-municipios/)
- Transporte intermunicipal de Goiás — [AGR](https://goias.gov.br/agr/61-linhas-do-transporte-intermunicipal/)
- População do Entorno — [Microregion of Entorno do DF (Wikipedia)](https://en.wikipedia.org/wiki/Microregion_of_Entorno_do_Distrito_Federal)
