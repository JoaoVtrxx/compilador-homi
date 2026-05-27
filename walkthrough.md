# Walkthrough — Compilador Homi

## Resumo

Reescrita completa do compilador Homi: de um protótipo que apenas imprimia "sucesso" para um **pipeline de 4 fases** que compila scripts `.homi` em YAML do Home Assistant.

---

## Arquivos Modificados

### [GLC.txt]
- Gramática formal completa com **32 regras de produção**
- Listagem explícita de todos os **terminais** (21 tokens) e **não-terminais** (14 símbolos)
- Unificou `estado` e `valor` em `expressao` (eliminando redundância)

### [lexer.py]
- **Corrigido** regex de `ENTIDADE_ID` (espaço antes do ponto)
- **Corrigido** `t_ID` que chamava `t_error` indevidamente
- **Adicionados** 12 novos tokens: `AUTOMACAO`, `FIM`, `SENAO`, `ESPERAR`, `NOTIFICAR`, `DEFINIR`, `CHAMAR`, `HORARIO`, `OU`, `MAIOR_IGUAL`, `MENOR_IGUAL`, `DIFERENTE`

### [parser.py]
- Parser **SLR(1)** (`method='SLR'` no PLY) — sem conflitos
- **Construção completa da AST** em cada regra de produção
- **Modo Pânico** implementado: sincroniza em `;` e `fim`
- Suporte a múltiplos gatilhos com `ou`, blocos `se/senao` em ações

## Arquivos Novos

### [ast_nodes.py]
- 12 classes `@dataclass`: `ProgramaNode`, `AutomacaoNode`, `GatilhoEstadoNode`, `GatilhoHorarioNode`, `CondicaoNode`, `ExpressaoNode`, `AcaoLigarNode`, `AcaoDesligarNode`, `AcaoEsperarNode`, `AcaoNotificarNode`, `AcaoDefinirNode`, `AcaoChamarNode`, `BlocoSeNode`

### [semantic.py]
- **Tabela de símbolos**: registra todas as entidades referenciadas e seus domínios
- **Verificações**: domínio válido, tipo compatível (ex: sensor ≠ ligar), operadores numéricos requerem NUMERO, serviços existem para o domínio

### [codegen.py]
- Gera YAML compatível com Home Assistant usando PyYAML
- Mapeia: gatilhos → `triggers`, condições → `conditions` (state/numeric_state/template), ações → `actions` (turn_on/turn_off/delay/notify/if-then-else/call-service)

### [main.py]
- Pipeline: `arquivo.homi` → Léxico → Sintático (SLR) → Semântico → YAML
- Flags: `-o saida.yaml` e `--verbose` (mostra tokens e tabela de símbolos)

### Exemplos
- [exemplo1.homi]
- [exemplo2.homi]
- [exemplo3.homi]
- [exemplo4_erros.homi]
- [exemplo5_errosemantico.homi]

---

