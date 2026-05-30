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
