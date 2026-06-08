import ply.yacc as yacc

# Importa os tokens do lexer (obrigatório para o PLY)
from B_lexer import tokens

# Importa os nós da AST
from F_ast_nodes import (
    ProgramaNode, AutomacaoNode,
    GatilhoEstadoNode, GatilhoHorarioNode,
    CondicaoNode, ExpressaoNode,
    AcaoLigarNode, AcaoDesligarNode, AcaoEsperarNode,
    AcaoNotificarNode, AcaoDefinirNode, AcaoChamarNode,
    BlocoSeNode,
)

# Armazenamento de erros para relatório final
erros_sintaticos = []

def _tempo_para_segundos(tempo_raw):
    # Converte '10s', '5min', '1h', '500ms' para segundos (float).
    if tempo_raw.endswith('ms'):
        return float(tempo_raw[:-2]) / 1000.0
    elif tempo_raw.endswith('min'):
        return float(tempo_raw[:-3]) * 60.0
    elif tempo_raw.endswith('h'):
        return float(tempo_raw[:-1]) * 3600.0
    elif tempo_raw.endswith('s'):
        return float(tempo_raw[:-1])
    return 0.0

# REGRAS DE PRODUÇÃO (Gramática SLR(1))
# Cada função p_* (production *) constrói o nó AST correspondente.
# p[0] é sempre a expressão mais à esquerda da regra.
# p[1], p[2], etc. são os tokens ou regras à direita da regra.
# No começo de cada função, sepre precisa ter '''resultado : parte1 parte2 parte3...'''

# R1: programa -> lista_automacoes
def p_programa(p):
    '''programa : lista_automacoes''' # p[0] = programa / p[1] = lista_automacoes
    p[0] = ProgramaNode(automacoes=p[1])

# R2-R3: lista_automacoes -> lista_automacoes PONTO_VIRGULA automacao | automacao
def p_lista_automacoes_mult(p):
    '''lista_automacoes : lista_automacoes PONTO_VIRGULA automacao'''
    p[0] = p[1] + [p[3]]

def p_lista_automacoes_unica(p):
    '''lista_automacoes : automacao'''
    p[0] = [p[1]]

# R4: automacao -> AUTOMACAO STRING gatilho_bloco condicao_opt ENTAO lista_acoes modo_opt FIM
def p_automacao(p):
    '''automacao : AUTOMACAO STRING gatilho_bloco condicao_opt ENTAO lista_acoes modo_opt FIM'''
    p[0] = AutomacaoNode(  # Cria um nó "AutomacaoNode", inserindo os 't.value' dos tokens recebidos na AST em cada campo do nó
        alias=p[2],
        gatilhos=p[3],
        condicoes=p[4],
        acoes=p[6],
        modo=p[7],
        linha=p.lineno(1),
    )

# R5: gatilho_bloco -> QUANDO lista_gatilhos
def p_gatilho_bloco(p):
    '''gatilho_bloco : QUANDO lista_gatilhos'''
    p[0] = p[2]

# R6-R7: lista_gatilhos -> lista_gatilhos OU gatilho | gatilho
def p_lista_gatilhos_mult(p):
    '''lista_gatilhos : lista_gatilhos OU gatilho'''
    p[0] = p[1] + [p[3]] # como tem recursão, precisa ser [p[3]] para criar uma lista, e ir aumentando ela

def p_lista_gatilhos_unico(p):
    '''lista_gatilhos : gatilho'''
    p[0] = [p[1]]

# R8: gatilho -> ENTIDADE_ID MUDAR PARA expressao
def p_gatilho_estado(p):
    '''gatilho : ENTIDADE_ID MUDAR PARA expressao'''
    p[0] = GatilhoEstadoNode(
        entidade_id=p[1],
        expressao=p[4],
        linha=p.lineno(1),
    )

# R9: gatilho -> HORARIO STRING
def p_gatilho_horario(p):
    '''gatilho : HORARIO STRING'''
    p[0] = GatilhoHorarioNode(
        horario=p[2],
        linha=p.lineno(1),
    )

# R10-R11: condicao_opt -> SE lista_condicoes | e
def p_condicao_opt_presente(p):
    '''condicao_opt : SE lista_condicoes'''
    p[0] = p[2]

def p_condicao_opt_vazia(p):
    '''condicao_opt : empty'''
    p[0] = []

# R12-R13: lista_condicoes -> lista_condicoes E condicao | condicao
def p_lista_condicoes_mult(p):
    '''lista_condicoes : lista_condicoes E condicao'''
    p[0] = p[1] + [p[3]]

def p_lista_condicoes_unica(p):
    '''lista_condicoes : condicao'''
    p[0] = [p[1]]

def p_empty(p):
    '''empty :'''
    pass

# R14: condicao -> ENTIDADE_ID operador expressao
def p_condicao(p):
    '''condicao : ENTIDADE_ID operador expressao'''
    p[0] = CondicaoNode(
        entidade_id=p[1],
        operador=p[2],
        expressao=p[3],
        linha=p.lineno(1),
    )

# R15-R20: operador -> MAIOR | MENOR | IGUAL | MAIOR_IGUAL | MENOR_IGUAL | DIFERENTE
def p_operador(p):
    '''operador : MAIOR
                | MENOR
                | IGUAL
                | MAIOR_IGUAL
                | MENOR_IGUAL
                | DIFERENTE'''
    p[0] = p[1]

# R21-R22: expressao -> NUMERO | STRING
def p_expressao_numero(p):
    '''expressao : NUMERO'''
    p[0] = ExpressaoNode(tipo='NUMERO', valor=p[1], linha=p.lineno(1))

def p_expressao_string(p):
    '''expressao : STRING'''
    p[0] = ExpressaoNode(tipo='STRING', valor=p[1], linha=p.lineno(1))

# R23-R24: lista_acoes -> lista_acoes acao | acao
def p_lista_acoes_mult(p):
    '''lista_acoes : lista_acoes acao'''
    p[0] = p[1] + [p[2]]

def p_lista_acoes_unica(p):
    '''lista_acoes : acao'''
    p[0] = [p[1]]

# R25: acao -> LIGAR ENTIDADE_ID
def p_acao_ligar(p):
    '''acao : LIGAR ENTIDADE_ID'''
    p[0] = AcaoLigarNode(entidade_id=p[2], linha=p.lineno(1))

# R26: acao -> DESLIGAR ENTIDADE_ID
def p_acao_desligar(p):
    '''acao : DESLIGAR ENTIDADE_ID'''
    p[0] = AcaoDesligarNode(entidade_id=p[2], linha=p.lineno(1))

# R27: acao -> ESPERAR TEMPO
def p_acao_esperar(p):
    '''acao : ESPERAR TEMPO'''
    p[0] = AcaoEsperarNode(
        tempo_raw=p[2],
        segundos=_tempo_para_segundos(p[2]),
        linha=p.lineno(1),
    )

# R28: acao -> NOTIFICAR STRING PARA STRING
def p_acao_notificar(p):
    '''acao : NOTIFICAR STRING PARA STRING'''
    p[0] = AcaoNotificarNode(mensagem=p[2], destino=p[4], linha=p.lineno(1))

# R29: acao -> DEFINIR ENTIDADE_ID expressao
def p_acao_definir(p):
    '''acao : DEFINIR ENTIDADE_ID expressao'''
    p[0] = AcaoDefinirNode(entidade_id=p[2], expressao=p[3], linha=p.lineno(1))

# R30: acao -> CHAMAR ENTIDADE_ID ENTIDADE_ID expressao
def p_acao_chamar_com_expressao(p):
    '''acao : CHAMAR ENTIDADE_ID ENTIDADE_ID expressao'''
    p[0] = AcaoChamarNode(servico=p[2], entidade_id=p[3], expressao=p[4], linha=p.lineno(1))

# R31: acao -> CHAMAR ENTIDADE_ID ENTIDADE_ID
def p_acao_chamar_sem_expressao(p):
    '''acao : CHAMAR ENTIDADE_ID ENTIDADE_ID'''
    p[0] = AcaoChamarNode(servico=p[2], entidade_id=p[3], linha=p.lineno(1))

# R32: acao -> bloco_se
def p_acao_bloco_se(p):
    '''acao : bloco_se'''
    p[0] = p[1]

# R33: bloco_se -> SE lista_condicoes ENTAO lista_acoes bloco_senao_opt FIM
def p_bloco_se(p):
    '''bloco_se : SE lista_condicoes ENTAO lista_acoes bloco_senao_opt FIM'''
    p[0] = BlocoSeNode(
        condicoes=p[2],
        acoes_entao=p[4],
        acoes_senao=p[5],
        linha=p.lineno(1),
    )

# R34-R35: bloco_senao_opt -> SENAO lista_acoes | e
def p_bloco_senao_opt_presente(p):
    '''bloco_senao_opt : SENAO lista_acoes'''
    p[0] = p[2]

def p_bloco_senao_opt_vazia(p):
    '''bloco_senao_opt : empty'''
    p[0] = []          # É bem melhor retornar lista vazia, pois assim o "BloseSeNode" sempre terá uma lista nas acoes_senao (mesmo que vazia).

# R36-R37: modo_opt -> MODO STRING | e  (Modo de execução opcional)
def p_modo_opt_presente(p):
    '''modo_opt : MODO STRING'''
    modo_raw = p[2].lower().strip()
    modos_validos = {
        'unico': 'single',
        'único': 'single',
        'single': 'single',
        'reiniciar': 'restart',
        'restart': 'restart',
        'fila': 'queued',
        'queued': 'queued',
    }
    if modo_raw in modos_validos:
        p[0] = modos_validos[modo_raw]
    else:
        print(f"Aviso de Sintaxe: Modo '{p[2]}' não reconhecido na linha {p.lineno(1)}. Usando 'single'.")
        p[0] = 'single'

def p_modo_opt_vazio(p):
    '''modo_opt : empty'''
    p[0] = 'single'

# TRATAMENTO DE ERROS (MODO PÂNICO)
def p_error(p):
    # Modo Pânico: ao encontrar um erro sintático, o parser pula tokens até encontrar um ponto de sincronização
    # (PONTO_VIRGULA ou FIM) e tenta continuar a análise.

    global erros_sintaticos
    if p:
        msg = (f"Erro de Sintaxe: Token inesperado '{p.value}' "
               f"(tipo {p.type}) na linha {p.lineno}.")
        print(msg)
        erros_sintaticos.append(msg)

        # Modo Pânico: descarta tokens até encontrar ';' ou 'fim'
        while True:
            tok = p.lexer.token()
            if not tok:
                break  # EOF
            if tok.type in ('PONTO_VIRGULA', 'FIM'):
                break
        # Indica que o parser pode tentar retomar
        parser.restart()
    else:
        msg = "Erro de Sintaxe: Fim de arquivo inesperado (EOF)."
        print(msg)
        erros_sintaticos.append(msg)

# Construção do Parser - Método SLR(1)
parser = yacc.yacc(method='SLR')

# Funções de interface pública
def parse(data, lexer_instance=None):
    # Retorna (ProgramaNode, lista_de_erros).

    global erros_sintaticos
    erros_sintaticos = []

    from B_lexer import lexer
    lexer.lineno = 1  # Reseta contagem de linhas

    resultado = parser.parse(data, lexer=lexer)

    if erros_sintaticos:
        print(f"\n>>> {len(erros_sintaticos)} erro(s) sintático(s) encontrado(s).")

    return resultado, erros_sintaticos