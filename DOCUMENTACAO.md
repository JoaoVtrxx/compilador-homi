# 📘 Documentação do Compilador Homi — Guia Completo de Arquitetura

## Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Mapa de Arquivos](#2-mapa-de-arquivos)
3. [O Pipeline de Compilação](#3-o-pipeline-de-compilação)
4. [Arquivos de Código-Fonte (o que VOCÊ escreve)](#4-arquivos-de-código-fonte)
   - 4.1 [GLC.txt — A Gramática Livre de Contexto](#41-glctxt--a-gramática-livre-de-contexto)
   - 4.2 [ast_nodes.py — Definição da Árvore Sintática](#42-ast_nodespy--definição-da-árvore-sintática)
   - 4.3 [lexer.py — O Analisador Léxico (Scanner)](#43-lexerpy--o-analisador-léxico-scanner)
   - 4.4 [parser.py — O Analisador Sintático (Parser SLR)](#44-parserpy--o-analisador-sintático-parser-slr)
   - 4.5 [semantic.py — O Analisador Semântico](#45-semanticpy--o-analisador-semântico)
   - 4.6 [codegen.py — O Gerador de Código (YAML)](#46-codegenpy--o-gerador-de-código-yaml)
   - 4.7 [main.py — O Orquestrador (Pipeline)](#47-mainpy--o-orquestrador-pipeline)
5. [Arquivos Gerados Automaticamente (NÃO editar)](#5-arquivos-gerados-automaticamente-não-editar)
   - 5.1 [parsetab.py — A Tabela de Parsing (cache)](#51-parsetabpy--a-tabela-de-parsing-cache)
   - 5.2 [parser.out — Relatório de Debug do Parser](#52-parserout--relatório-de-debug-do-parser)
   - 5.3 [\_\_pycache\_\_/ — Cache de bytecode Python](#53-__pycache__--cache-de-bytecode-python)
6. [Arquivos de Entrada e Saída](#6-arquivos-de-entrada-e-saída)
   - 6.1 [exemplos/*.homi — Scripts da Linguagem Homi](#61-exemploshomi--scripts-da-linguagem-homi)
   - 6.2 [exemplos/*.yaml — YAML Gerado](#62-exemplosyaml--yaml-gerado)
   - 6.3 [automations_homi.yaml — Referência do Home Assistant](#63-automations_homiyaml--referência-do-home-assistant)
7. [Dependências Externas](#7-dependências-externas)
8. [Como Executar](#8-como-executar)
9. [Diagrama de Fluxo de Dados](#9-diagrama-de-fluxo-de-dados)

---

## 1. Visão Geral do Projeto

O **compilador Homi** é um tradutor que transforma scripts escritos na linguagem Homi (`.homi`) em arquivos YAML compatíveis com o **Home Assistant** — a plataforma de automação residencial.

A ideia é que uma pessoa leiga possa escrever algo assim:

```
automacao "Ligar luz do corredor"
    quando sensor.movimento mudar para "on"
    entao
        ligar light.corredor
    fim
```

E o compilador transforma isso automaticamente em um YAML de automação do Home Assistant:

```yaml
- id: '1779898267036'
  alias: Ligar luz do corredor
  triggers:
  - entity_id:
    - sensor.movimento
    to: 'on'
    trigger: state
  conditions: []
  actions:
  - action: light.turn_on
    target:
      entity_id: light.corredor
  mode: single
```

O compilador segue as **fases clássicas** da teoria de compiladores:

```
Código Fonte (.homi)
    │
    ▼
┌──────────────────┐
│ 1. Análise Léxica│   lexer.py      → Quebra o texto em tokens
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 2. Análise       │   parser.py     → Verifica a estrutura gramatical
│    Sintática     │                    e monta a Árvore (AST)
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 3. Análise       │   semantic.py   → Verifica significado e coerência
│    Semântica     │
└────────┬─────────┘
         ▼
┌──────────────────┐
│ 4. Geração de    │   codegen.py    → Traduz a AST para YAML
│    Código        │
└────────┬─────────┘
         ▼
    Código Alvo (.yaml)
```

---

## 2. Mapa de Arquivos

```
compilador-homi/
│
├── 📄 GLC.txt                    ← DOCUMENTAÇÃO: Gramática formal da linguagem
├── 📄 DOCUMENTACAO.md            ← DOCUMENTAÇÃO: Este arquivo (você está aqui)
│
├── 📦 ast_nodes.py               ← CÓDIGO-FONTE: Define as estruturas da AST
├── 📦 lexer.py                   ← CÓDIGO-FONTE: Analisador Léxico (Scanner/DFA)
├── 📦 parser.py                  ← CÓDIGO-FONTE: Analisador Sintático (SLR)
├── 📦 semantic.py                ← CÓDIGO-FONTE: Analisador Semântico
├── 📦 codegen.py                 ← CÓDIGO-FONTE: Gerador de código YAML
├── 📦 main.py                    ← CÓDIGO-FONTE: Pipeline (ponto de entrada)
│
├── ⚙️ parsetab.py                ← AUTO-GERADO: Tabela SLR serializada (cache)
├── ⚙️ parser.out                 ← AUTO-GERADO: Relatório de debug do parser
├── ⚙️ __pycache__/               ← AUTO-GERADO: Bytecode Python compilado
│
├── 📁 exemplos/
│   ├── 📝 exemplo1.homi          ← ENTRADA: Script simples
│   ├── 📝 exemplo2.homi          ← ENTRADA: Com condição e delay
│   ├── 📝 exemplo3.homi          ← ENTRADA: Múltiplas automações
│   ├── 📝 exemplo4_erros.homi    ← ENTRADA: Teste de erros sintáticos
│   ├── 📝 exemplo5_semantic.homi ← ENTRADA: Teste de erros semânticos
│   ├── 📤 saida2.yaml            ← SAÍDA: YAML gerado do exemplo2
│   └── 📤 saida3.yaml            ← SAÍDA: YAML gerado do exemplo3
│
└── 📋 automations_homi.yaml      ← REFERÊNCIA: Automações reais do Home Assistant
```

---

## 3. O Pipeline de Compilação

Quando você executa `python3 main.py exemplo.homi`, acontece isto:

### Passo 1 — Leitura do arquivo
O `main.py` abre o arquivo `.homi` e lê todo o texto.

### Passo 2 — Análise Léxica (`lexer.py`)
O texto bruto é quebrado em **tokens**. Por exemplo, o texto:
```
quando sensor.temperatura > 25
```
Vira a sequência de tokens:
```
QUANDO | ENTIDADE_ID("sensor.temperatura") | MAIOR(">") | NUMERO(25)
```

### Passo 3 — Análise Sintática (`parser.py`)
Os tokens são organizados em uma **árvore** (AST) seguindo as regras da gramática (GLC).
Se a sequência de tokens não "encaixar" em nenhuma regra, é um **erro de sintaxe**.

### Passo 4 — Análise Semântica (`semantic.py`)
A árvore é percorrida para verificar se tudo **faz sentido**. Por exemplo:
- Não faz sentido `ligar sensor.temperatura` (sensor não é um atuador)
- Não faz sentido `se sensor.x > "texto"` (operador `>` precisa de número)

### Passo 5 — Geração de Código (`codegen.py`)
A árvore validada é percorrida novamente, desta vez para gerar o **YAML final**.

---

## 4. Arquivos de Código-Fonte

Estes são os arquivos que você escreve e modifica. Cada um tem uma responsabilidade clara.

---

### 4.1 GLC.txt — A Gramática Livre de Contexto

| Campo | Detalhe |
|-------|---------|
| **Responsabilidade** | Especificação formal da linguagem Homi |
| **Tipo** | Documentação (não é código executável) |
| **Fase do compilador** | Nenhuma — é a **especificação teórica** |
| **Quem usa** | O programador humano, para implementar o `parser.py` |

#### O que é uma GLC?

Uma **Gramática Livre de Contexto** é a definição formal de uma linguagem. Ela diz quais sequências de tokens são "frases válidas". Composta por:

- **Terminais** (tokens): os átomos da linguagem, como `QUANDO`, `LIGAR`, `ENTIDADE_ID`, `NUMERO`. São as "palavras" que o lexer reconhece.
- **Não-terminais**: categorias abstratas como `automacao`, `gatilho`, `acao`. Não existem no texto — são conceitos que agrupam terminais.
- **Regras de produção**: definem como cada não-terminal se decompõe. Exemplo:

```
acao → LIGAR ENTIDADE_ID
```

Isso diz: "uma ação pode ser a palavra `ligar` seguida de uma entidade".

#### Relação com os outros arquivos

O `GLC.txt` é o "contrato" que o `parser.py` implementa. Cada regra de produção no GLC vira uma função `p_*` no parser. Se você mudar a gramática, precisa mudar o parser para corresponder.

---

### 4.2 ast_nodes.py — Definição da Árvore Sintática

| Campo | Detalhe |
|-------|---------|
| **Responsabilidade** | Definir as **estruturas de dados** da AST |
| **Tipo** | Código-fonte (definição de classes) |
| **Fase do compilador** | Estrutura intermediária (usada pelas fases 2, 3 e 4) |
| **Quem usa** | `parser.py` (cria), `semantic.py` (lê), `codegen.py` (lê) |

#### O que é uma AST?

A **Árvore Sintática Abstrata** (Abstract Syntax Tree) é a representação estruturada do programa. Enquanto o texto bruto é uma sequência linear de caracteres, a AST organiza tudo em uma **hierarquia de nós**, como uma árvore genealógica.

#### O que há neste arquivo?

São **dataclasses Python** — basicamente "fichas" que guardam informação:

```python
@dataclass
class AcaoLigarNode:
    entidade_id: str    # ex: "light.sala"
    linha: int = 0      # linha onde apareceu (para erros)
```

Os nós se encaixam assim:

```
ProgramaNode
 └── AutomacaoNode (alias="Corredor")
      ├── GatilhoEstadoNode (entidade="sensor.motion", estado="on")
      ├── CondicaoNode (entidade="sensor.temp", operador=">", valor=25)
      └── [lista de ações]
           ├── AcaoLigarNode (entidade="light.corredor")
           ├── AcaoEsperarNode (tempo="2min", segundos=120.0)
           └── AcaoDesligarNode (entidade="light.corredor")
```

#### Por que existe como arquivo separado?

Porque a AST é um **contrato** entre o parser (que a monta) e o semântico/codegen (que a leem). Separar em um arquivo próprio garante que todos concordem sobre a estrutura dos dados, sem dependência circular entre módulos.

---

### 4.3 lexer.py — O Analisador Léxico (Scanner)

| Campo | Detalhe |
|-------|---------|
| **Responsabilidade** | **Fase 1** — Análise Léxica |
| **Tipo** | Código-fonte + definição do DFA |
| **Tecnologia** | PLY (Python Lex-Yacc), módulo `ply.lex` |
| **Entrada** | Texto bruto (string do arquivo `.homi`) |
| **Saída** | Sequência de tokens |

#### O que faz a análise léxica?

Ela é o "olho" do compilador. Lê o texto caractere por caractere e agrupa em **tokens** — as unidades mínimas com significado. É como ler uma frase em português e identificar cada palavra.

#### Como funciona internamente?

O PLY usa **expressões regulares** (regex) para definir cada token. Cada regex descreve o padrão de caracteres que um token pode ter:

```python
# Um ENTIDADE_ID é: letras minúsculas/underscore, ponto, letras/números/underscore
# Exemplo: sensor.temperatura_sala, light.luz_teto
def t_ENTIDADE_ID(t):
    r'[a-z_]+\.[a-z0-9_]+'
    return t
```

Por baixo dos panos, o PLY combina todas essas regex em um **DFA** (Autômato Finito Determinístico) — uma máquina de estados que consome um caractere por vez e decide qual token reconheceu.

#### Conceitos importantes no arquivo

1. **`tokens` (tupla)**: lista de TODOS os nomes de tokens. Obrigatória — o parser importa essa variável.

2. **`reserved` (dicionário)**: mapeia palavras-chave como `"quando" → QUANDO`. Sem isso, "quando" seria um identificador genérico.

3. **Funções `t_*` (regras de token)**:
   - `t_ENTIDADE_ID(t)` — função com regex na docstring
   - `t_MAIOR = r'>'` — variável simples para tokens de um caractere
   - **A ORDEM das funções importa!** O PLY processa tokens por função na ordem de comprimento da regex (mais longa primeiro). Funções vêm antes de variáveis.

4. **`t_error(t)`**: chamada quando o lexer encontra um caractere que não casa com nenhum padrão. Imprime o erro e pula o caractere.

5. **`t_COMENTARIO(t)`**: reconhece `#...` mas retorna `pass` — ou seja, descarta o token. Comentários são lidos mas nunca chegam ao parser.

6. **`t_newline(t)`**: conta as quebras de linha para que as mensagens de erro possam dizer "erro na linha X".

#### Prioridade de tokens

Quando dois padrões podem casar o mesmo texto, o PLY usa regras de prioridade:
- **Funções** têm prioridade sobre **variáveis** (strings)
- Entre funções, regex **mais longas** primeiro
- Isso garante que `>=` é reconhecido como `MAIOR_IGUAL` e não como `MAIOR` + `=`

---

### 4.4 parser.py — O Analisador Sintático (Parser SLR)

| Campo | Detalhe |
|-------|---------|
| **Responsabilidade** | **Fase 2** — Análise Sintática |
| **Tipo** | Código-fonte + definição da gramática |
| **Tecnologia** | PLY `ply.yacc`, método **SLR(1)** |
| **Entrada** | Sequência de tokens (do lexer) |
| **Saída** | Árvore Sintática Abstrata (AST) |
| **Gera automaticamente** | `parsetab.py` e `parser.out` |

#### O que faz a análise sintática?

Ela verifica se a sequência de tokens forma uma "frase" válida de acordo com a gramática. É como verificar se uma frase em português respeita sujeito-verbo-objeto.

Por exemplo, a sequência `LIGAR ENTIDADE_ID` é válida (regra R23: `acao → LIGAR ENTIDADE_ID`). Mas `LIGAR LIGAR` não é — não existe regra pra isso.

#### O que é SLR(1)?

**SLR** = **Simple LR** (Left-to-right, Rightmost derivation). É um método **bottom-up** (de baixo para cima) de análise sintática:

- **Bottom-up**: começa pelos tokens individuais e vai agrupando em não-terminais cada vez maiores, até chegar ao símbolo inicial (`programa`).
- **LR**: lê a entrada da **L**eft (esquerda para direita) e constrói a derivação **R**ightmost (mais à direita).
- **(1)**: usa 1 token de **lookahead** — olha o próximo token para decidir o que fazer.

A alternativa seria **top-down** (como LL(1)), que começa do símbolo inicial e tenta expandir até chegar nos tokens. O SLR é mais poderoso que LL(1) porque consegue reconhecer mais gramáticas.

#### Como funciona o algoritmo SLR?

O parser usa duas operações:
1. **Shift** (empilha): lê o próximo token da entrada e coloca na pilha
2. **Reduce** (reduz): quando o topo da pilha casa com o lado direito de uma regra, substitui pelo lado esquerdo

Exemplo para `ligar light.sala`:

```
Pilha                    | Entrada restante    | Ação
─────────────────────────|─────────────────────|──────────
                         | LIGAR ENTIDADE_ID $ | shift
LIGAR                    | ENTIDADE_ID $       | shift
LIGAR ENTIDADE_ID        | $                   | reduce (acao → LIGAR ENTIDADE_ID)
acao                     | $                   | reduce (lista_acoes → acao)
lista_acoes              | $                   | aceito!
```

A decisão entre shift e reduce é feita consultando a **tabela SLR** — que é gerada automaticamente pelo PLY e armazenada no `parsetab.py`.

#### Como o código implementa isso?

Cada regra de produção da GLC é uma função `p_*`:

```python
# Regra R23: acao → LIGAR ENTIDADE_ID
def p_acao_ligar(p):
    '''acao : LIGAR ENTIDADE_ID'''
    p[0] = AcaoLigarNode(entidade_id=p[2], linha=p.lineno(1))
```

- A **docstring** (`'''acao : LIGAR ENTIDADE_ID'''`) define a regra gramatical
- `p[1]` = valor do primeiro símbolo (LIGAR), `p[2]` = valor do segundo (ENTIDADE_ID)
- `p[0]` = o resultado — o nó AST que representa essa regra reduzida

O PLY lê todas essas funções, extrai as regras da docstring, e gera a tabela SLR automaticamente.

#### Modo Pânico (recuperação de erros)

Quando o parser encontra um token inesperado, em vez de abortar:

1. Registra o erro com a linha e o token
2. **Pula tokens** da entrada até encontrar um `;` (ponto-e-vírgula) ou `FIM` — esses são chamados **tokens de sincronização**
3. Chama `parser.restart()` para limpar a pilha
4. Tenta continuar analisando o restante do arquivo

Isso permite reportar **múltiplos erros** em uma única execução, em vez de parar no primeiro.

#### O que o parser NÃO faz

O parser apenas verifica a **estrutura**. Ele aceita `ligar sensor.temperatura` sem reclamar, porque sintaticamente `LIGAR ENTIDADE_ID` está correto. Quem verifica se "ligar um sensor" faz sentido é o **analisador semântico**.

---

### 4.5 semantic.py — O Analisador Semântico

| Campo | Detalhe |
|-------|---------|
| **Responsabilidade** | **Fase 3** — Análise Semântica |
| **Tipo** | Código-fonte |
| **Entrada** | AST (do parser) |
| **Saída** | AST validada + erros/avisos |

#### O que faz a análise semântica?

Ela verifica se o programa, que já tem a estrutura correta (sintaxe OK), **faz sentido**. É a diferença entre:

- ✅ "O gato comeu o peixe" — sintaxe e semântica OK
- ❌ "O peixe comeu o avião" — sintaxe OK, mas sem sentido

#### Tabela de Símbolos

É um dicionário que registra **todas as entidades** mencionadas no programa:

```
{
    "sensor.temperatura":   { domínio: "sensor",       tipo: "sensor"   },
    "light.sala":           { domínio: "light",        tipo: "atuador"  },
    "switch.ventilador":    { domínio: "switch",       tipo: "atuador"  },
}
```

A tabela é construída conforme o analisador percorre a AST. Ela serve para consultar se uma entidade é do tipo certo para a operação pedida.

#### Verificações realizadas

| Verificação | Exemplo de erro | Explicação |
|-------------|----------------|------------|
| **Ação vs. domínio** | `ligar sensor.temperatura` | Sensores não são atuadores — não podem ser "ligados" |
| **Tipo do operador** | `se sensor.x > "texto"` | O operador `>` exige um NUMERO, não STRING |
| **Serviço válido** | `chamar light.explodir ...` | Não existe o serviço "explodir" no domínio "light" |
| **Compatibilidade serviço/alvo** | `chamar switch.turn_on light.sala` | Serviço de `switch` aplicado a entidade de `light` |
| **Formato de horário** | `horario "25:99:00"` | Formato inválido (aviso) |
| **Nomes duplicados** | Duas automações com mesmo alias | Aviso de nome duplicado |

#### Erros vs. Avisos

- **Erros**: impedem a compilação (ex: ligar um sensor)
- **Avisos**: apenas alertam, mas a compilação continua (ex: domínio desconhecido)

---

### 4.6 codegen.py — O Gerador de Código (YAML)

| Campo | Detalhe |
|-------|---------|
| **Responsabilidade** | **Fase 4** — Geração de Código Intermediário |
| **Tipo** | Código-fonte |
| **Tecnologia** | PyYAML (biblioteca `yaml`) |
| **Entrada** | AST validada |
| **Saída** | String YAML (automação do Home Assistant) |

#### O que faz?

Percorre a AST nó por nó e traduz cada elemento para o formato YAML do Home Assistant. É como um "intérprete" que traduz de Homi para a linguagem que o Home Assistant entende.

#### Mapeamento AST → YAML

| Nó da AST | Estrutura YAML gerada |
|-----------|----------------------|
| `AutomacaoNode` | Bloco raiz com `id`, `alias`, `triggers`, `conditions`, `actions`, `mode` |
| `GatilhoEstadoNode` | `trigger: state` com `entity_id` e `to` |
| `GatilhoHorarioNode` | `trigger: time` com `at` |
| `CondicaoNode (==)` | `condition: state` |
| `CondicaoNode (>, <)` | `condition: numeric_state` com `above`/`below` |
| `CondicaoNode (!=)` | `condition: template` com Jinja2 |
| `AcaoLigarNode` | `action: <domínio>.turn_on` + `target.entity_id` |
| `AcaoDesligarNode` | `action: <domínio>.turn_off` + `target.entity_id` |
| `AcaoEsperarNode` | `delay: { hours, minutes, seconds, milliseconds }` |
| `AcaoNotificarNode` | `action: notify.<destino>` + `data.message` |
| `AcaoDefinirNode` | `action: input_number.set_value` (ou similar) |
| `AcaoChamarNode` | `action: <serviço>` + `target.entity_id` |
| `BlocoSeNode` | Bloco `if/then/else` |

#### Por que usar PyYAML?

O YAML tem regras rígidas de indentação (igual ao Python). Gerar YAML manualmente concatenando strings seria extremamente propenso a erros. O PyYAML garante que a indentação e as aspas estejam sempre corretas.

---

### 4.7 main.py — O Orquestrador (Pipeline)

| Campo | Detalhe |
|-------|---------|
| **Responsabilidade** | Ponto de entrada — orquestra as 4 fases |
| **Tipo** | Código-fonte |
| **Entrada** | Arquivo `.homi` (via linha de comando) |
| **Saída** | Arquivo `.yaml` (via `-o`) ou stdout |

#### O que faz?

É o **único arquivo que você executa**. Ele:

1. Lê o arquivo `.homi`
2. Chama o `lexer.py` (Fase 1)
3. Chama o `parser.py` (Fase 2)
4. Chama o `semantic.py` (Fase 3)
5. Chama o `codegen.py` (Fase 4)
6. Escreve o YAML na saída

Se qualquer fase encontrar erros, ele **para** e mostra as mensagens. Não gera YAML se houver erros.

#### Argumentos de linha de comando

```bash
python3 main.py <arquivoX.homi>                             # compila e mostra YAML no terminal
python3 main.py <arquivoX.homi> -o <saidaY.yaml>            # salva o YAML em arquivo
python3 main.py <arquivoX.homi> -o <saidaY.yaml> --verbose  # mostra todos os tokens e tabela de símbolos
```

---

## 5. Arquivos Gerados Automaticamente (NÃO editar)

Estes arquivos são **criados por código**. Se você editá-los manualmente, eles serão sobrescritos na próxima execução. Podem ser deletados sem problema — serão recriados automaticamente.

---

### 5.1 parsetab.py — A Tabela de Parsing (cache)

| Campo | Detalhe |
|-------|---------|
| **Gerado por** | `parser.py` (via PLY `ply.yacc`) |
| **Quando é gerado** | Na primeira execução do parser, ou quando a gramática muda |
| **Conteúdo** | Tabela SLR(1) serializada em Python |
| **Pode deletar?** | ✅ Sim — será recriado na próxima execução |

#### O que é a Tabela SLR?

Quando o PLY lê as regras `p_*` do `parser.py`, ele:

1. Extrai todas as regras de produção
2. Calcula os **conjuntos FIRST e FOLLOW** de cada não-terminal
3. Constrói os **itens LR(0)** e o **autômato de estados** do parser
4. Monta a **tabela ACTION/GOTO** que decide, para cada par (estado, token), se deve **shift** ou **reduce**

Esse processo é computacionalmente caro, então o resultado é salvo em `parsetab.py` como cache. Nas execuções seguintes, o PLY apenas carrega essa tabela, sendo muito mais rápido.

#### O que há dentro do arquivo?

```python
_lr_method = 'SLR'                    # Método usado
_lr_signature = 'AUTOMACAO CHAMAR...' # Assinatura da gramática
_lr_action_items = {...}              # Tabela ACTION (shift/reduce)
_lr_goto_items = {...}                # Tabela GOTO (transições de estado)
_lr_productions = [...]               # Lista de produções
```

A `_lr_signature` é um hash da gramática. Se você mudar qualquer regra no `parser.py`, a assinatura muda e o PLY regenera a tabela.

---

### 5.2 parser.out — Relatório de Debug do Parser

| Campo | Detalhe |
|-------|---------|
| **Gerado por** | `parser.py` (via PLY `ply.yacc`) |
| **Quando é gerado** | Sempre que `parsetab.py` é regenerado |
| **Conteúdo** | Relatório legível do parser: gramática, estados, conflitos |
| **Pode deletar?** | ✅ Sim |

#### O que há dentro?

Este arquivo é **essencial para debug**. Contém:

1. **Todas as regras numeradas**:
   ```
   Rule 0     S' -> programa
   Rule 1     programa -> lista_automacoes
   Rule 24    acao -> LIGAR ENTIDADE_ID
   ```

2. **Lista de terminais e onde aparecem**:
   ```
   ENTIDADE_ID : 8 13 24 25 28 29 29
   ```
   (aparece nas regras 8, 13, 24, 25, 28, e duas vezes na 29)

3. **Método de parsing**: `Parsing method: SLR`

4. **Todos os estados do autômato** com seus itens LR(0):
   ```
   state 17
       (4) automacao -> AUTOMACAO STRING gatilho_bloco condicao_opt . ENTAO lista_acoes FIM
       ENTAO    shift and go to state 23
   ```
   Cada estado diz: "estou neste ponto da análise. Se o próximo token for X, faço Y."

5. **Conflitos** (se houver): se a gramática for ambígua, conflitos shift/reduce ou reduce/reduce aparecem aqui. Nossa gramática não tem conflitos.

---

## 6. Arquivos de Entrada e Saída

---

### 6.1 exemplos/*.homi — Scripts da Linguagem Homi

| Arquivo | Descrição | Recursos demonstrados |
|---------|-----------|----------------------|
| `exemplo1.homi` | Automação mínima | 1 gatilho, 1 ação, sem condição |
| `exemplo2.homi` | Com condição e delay | Condição numérica, `esperar`, `notificar` |
| `exemplo3.homi` | 4 automações | Múltiplos gatilhos com `ou`, blocos `se/senao`, `definir`, `chamar`, `horario` |
| `exemplo4_erros.homi` | Erros sintáticos | Testa o Modo Pânico (falta `fim`) |
| `exemplo5_semantic.homi` | Erros semânticos | Ligar sensor, tipo errado, serviço inválido |

#### Sintaxe dos arquivos `.homi`

```
automacao "<nome>"                    # Cabeçalho com nome
    quando <gatilho>                  # Obrigatório: pelo menos 1 gatilho
        [ou <gatilho>]               # Opcional: gatilhos adicionais
    [se <condição>]                  # Opcional: condição
    entao                             # Início do bloco de ações
        <ação>                        # 1 ou mais ações
        [<ação>]
    fim                               # Fim da automação
[;]                                   # Separador entre automações
```

### 6.2 exemplos/*.yaml — YAML Gerado

Estes são os **arquivos de saída** do compilador. Gerados pelo `codegen.py`, representam automações válidas para o Home Assistant.

### 6.3 automations_homi.yaml — Referência do Home Assistant

Arquivo com **automações reais** do Home Assistant de uma casa. Serviu como referência para o design da linguagem Homi — as construções da linguagem foram projetadas para cobrir os padrões mais comuns encontrados nessas automações (triggers por estado, condições, delays, notificações, blocos if/else).

---

## 7. Dependências Externas

| Biblioteca | Versão | Instalação | Usada por |
|-----------|--------|------------|-----------|
| **PLY** (Python Lex-Yacc) | 3.11 | `pip install ply` | `lexer.py`, `parser.py` |
| **PyYAML** | 6.0+ | `pip install PyYAML` | `codegen.py` |

### PLY — O que é e por que usar?

PLY é uma implementação em Python das ferramentas clássicas **Lex** (gerador de analisadores léxicos) e **Yacc** (Yet Another Compiler Compiler). Em vez de gerar código C como as ferramentas originais, o PLY funciona nativamente em Python:

- **`ply.lex`**: constrói o DFA (autômato) a partir das regex definidas nas funções `t_*`
- **`ply.yacc`**: constrói a tabela de parsing (SLR ou LALR) a partir das regras `p_*`

O PLY gera automaticamente os arquivos `parsetab.py` e `parser.out`.

---

## 8. Como Executar

```bash
# Instalar dependências
pip install ply PyYAML

# Compilar um exemplo
python3 main.py exemplos/exemplo1.homi

# Compilar com saída em arquivo
python3 main.py exemplos/exemplo3.homi -o saida.yaml

# Compilar com detalhes (tokens + tabela de símbolos)
python3 main.py exemplos/exemplo3.homi --verbose

# Testar apenas o lexer isoladamente
python3 lexer.py

# Testar apenas o parser isoladamente
python3 parser.py

# Testar apenas o analisador semântico
python3 semantic.py
```

---

## 9. Diagrama de Fluxo de Dados

```
                    ┌────────────────────────────────────────────────────┐
                    │              ARQUIVOS DO PROJETO                   │
                    └────────────────────────────────────────────────────┘

 ┌──────────┐            ┌─────────────┐
 │ GLC.txt  │            │ ast_nodes.py│
 │(document)│            │ (classes)   │
 └─────┬────┘            └──────┬──────┘
       │ humano                 │ importa
       │ implementa             │
       │                ┌───────┴───────┬───────────────┐
       ▼                ▼               ▼               ▼
 ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐
 │ lexer.py │    │ parser.py│    │semantic.py│    │codegen.py│
 │ (DFA)    │    │ (SLR)    │    │ (tabela)  │    │  (YAML)  │
 └─────┬────┘    └─────┬────┘    └─────┬─────┘    └────┬─────┘
       │               │               │               │
       │ tokens        │ AST           │ AST válida    │ YAML
       │               │               │               │
       │        gera ──┤               │               │
       │        auto   ▼               │               │
       │        ┌────────────────────┐ │               │
       │        │ parsetab.py (cache)│ │               │
       │        │ parser.out  (cache)│ │               │
       │        └────────────────────┘ │               │
       │                               │               │
 ┌─────┴───────────────────────────────┴───────────────┴────┐
 │                        main.py                           │
 │                    (orquestrador)                        │
 │                                                          │
 │   Fase 1         Fase 2         Fase 3         Fase 4    │
 │  lexer.py ──→  parser.py ──→ semantic.py ──→ codegen.py  │
 │   tokens         AST         AST válida       YAML       │
 └─────┬───────────────────────────────────────────────┬────┘
       │                                               │
       ▼                                               ▼
 ┌──────────┐                                   ┌──────────┐
 │ .homi    │                                   │ .yaml    │
 │ (entrada)│                                   │ (saída)  │
 └──────────┘                                   └──────────┘
```
