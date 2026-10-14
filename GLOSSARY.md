# Glossário

Vocabulário da aula e do código. Cada termo tem uma definição de conceito e, quando
ajuda, a distinção que costuma ser confundida. Termos em **negrito** dentro de uma
definição estão definidos aqui também.

## Camadas de dados

**camada (raw / trusted / refined)** — os três estágios por que um dado passa, cada um
com um catálogo e um contrato próprios.

- **raw** — o dado como chegou da origem. Sem regra de negócio, sem limpeza; existe
  para que a origem possa ser reprocessada sem voltar à fonte.
- **trusted** — o dado já padronizado: nomes de coluna, tipos, deduplicação, filtros de
  sanidade. Ainda *como na origem*, linha a linha, sem agregação.
- **refined** — **modelo dimensional** (ver adiante): o dado pronto para análise,
  organizado em **fato** e **dimensões**. É o que a **camada semântica** lê.

Promover dado de uma camada para a seguinte é responsabilidade da transformação; o
consumidor nunca escolhe a camada, escolhe a **métrica**.

## Modelo dimensional

**modelo dimensional** — forma de organizar os dados refinados em um **fato** cercado de
**dimensões**, em vez de uma tabela larga única. É o oposto de "uma tabela com tudo":
existe para que **métricas** tenham denominador correto e para que fatiar seja uma
escolha, não uma reescrita de SQL.

**fato** — tabela no grão do evento ou da entidade que se quer medir, guardando as
medidas no nível mais fino disponível. Um fato "largo" (com atributos descritivos
embutidos) é justamente o que o modelo dimensional evita.

**grão** — o que **uma linha do fato representa**. É a primeira decisão da modelagem e a
que define se uma contagem faz sentido: "um título", "uma venda", "um dia por loja".
Métricas sobre um grão confuso somam a mesma coisa duas vezes.

**dimensão** — atributo pelo qual um **fato** pode ser fatiado (tempo, tipo, categoria).
Tem valor único por linha do fato, ou é resolvida por **tabela de ponte** quando não tem.

**atributo multi-valor** — atributo que pode assumir vários valores para a mesma linha
do fato (um título tem vários gêneros, vários países). Não cabe em uma coluna da
tabela larga sem duplicar ou concatenar; é o que contamina qualquer agregação feita
direto sobre ela.

**tabela de ponte** (*bridge*) — tabela que resolve um **atributo multi-valor**: uma
linha por par (fato, valor), em vez de N colunas ou listas concatenadas. Existe para que
"nota média por gênero" conte cada título exatamente uma vez, por mais gêneros que ele
tenha; quem atravessa a ponte precisa saber voltar ao **grão** do fato.

## Camada semântica

**modelo semântico** — a definição, versionada como código, das **métricas** e
**dimensões** que o negócio usa: nomes, fórmulas, agregações e a que colunas dos dados
elas correspondem. É o *artefato* — o "o quê" da linguagem analítica.

**camada semântica** — o *serviço* que publica o **modelo semântico** para consumo:
recebe um pedido em termos de métricas e dimensões e devolve o número já agregado,
pela mesma definição, para qualquer cliente (BI, agente, SQL). Modelo semântico é a
definição; camada semântica é o que a serve.

**métrica** — grandeza de negócio com fórmula e agregação declaradas (quantidade de
títulos, nota média, total de votos). Definida **uma vez**, no modelo semântico, e
consumida por nome por todos os clientes — em vez de recalculada em cada consulta.
Uma métrica não é "uma consulta salva": é a definição que todos concordam em usar.

**medida** — o valor numérico que uma **métrica** assume para um recorte específico (a
nota média *de 2020*, *no Japão*). Métrica é a definição; medida é o número resultante.

**dimensão governada** — o atributo exposto pela **camada semântica** como opção de
fatiamento, com nome e tipo estáveis, independentemente de como está armazenado no
**refined** (coluna, ponte, ano derivado). Fatiar por uma dimensão multi-valor não
infla as métricas — esse é o contrato que a camada semântica garante.

**consumo governado** — consultar pela **camada semântica** (métrica + dimensão + filtro)
em vez de escrever SQL livre contra as tabelas. É o que faz dois consumidores diferentes
mostrarem o mesmo número.

## Context engineering

**context engineering** — decidir *o que* o agente enxerga como vocabulário de trabalho,
em vez de dar a ele acesso irrestrito aos dados. Aqui: o agente recebe as **métricas** e
**dimensões governadas** como ferramentas, descobre o que existe antes de perguntar, e
não escreve SQL — assim ele não inventa uma métrica, não erra o **grão** e não depende de
conhecer o esquema físico. Um agente com acesso a SQL livre *pode* acertar; um agente
com **consumo governado** não consegue errar a definição.

**MCP** (*Model Context Protocol*) — o protocolo pelo qual essas ferramentas são
entregues ao agente: um catálogo de funções com nome, argumentos e formato de retorno.
É o meio; o **context engineering** é a decisão de quais funções existem.
