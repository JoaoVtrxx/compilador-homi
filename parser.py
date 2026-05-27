import ply.yacc as yacc

# Importa os tokens do lexer (obrigatório para o PLY)
from lexer import tokens

# Importa os nós da AST
from ast_nodes import (
    ProgramaNode, AutomacaoNode,
    GatilhoEstadoNode, GatilhoHorarioNode,
    CondicaoNode, ExpressaoNode,
    AcaoLigarNode, AcaoDesligarNode, AcaoEsperarNode,
    AcaoNotificarNode, AcaoDefinirNode, AcaoChamarNode,
    BlocoSeNode,
)

# ============================================================
# Armazenamento de erros para relatório final
# ============================================================
erros_sintaticos = []

# ============================================================
# Função auxiliar: converte string de tempo para segundos
# ============================================================
def _tempo_para_segundos(tempo_raw):
    """Converte '10s', '5min', '1h', '500ms' para segundos (float)."""
    if tempo_raw.endswith('ms'):
        return float(tempo_raw[:-2]) / 1000.0
    elif tempo_raw.endswith('min'):
        return float(tempo_raw[:-3]) * 60.0
    elif tempo_raw.endswith('h'):
        return float(tempo_raw[:-1]) * 3600.0
    elif tempo_raw.endswith('s'):
        return float(tempo_raw[:-1])
    return 0.0

# ============================================================
# REGRAS DE PRODUÇÃO (Gramática SLR(1))
# Cada função p_* constrói o nó AST correspondente.
# ============================================================

# R1: programa → lista_automacoes
def p_programa(p):
    '''programa : lista_automacoes'''
    p[0] = ProgramaNode(automacoes=p[1])

# R2-R3: lista_automacoes → lista_automacoes PONTO_VIRGULA automacao | automacao
def p_lista_automacoes_mult(p):
    '''lista_automacoes : lista_automacoes PONTO_VIRGULA automacao'''
    p[0] = p[1] + [p[3]]

def p_lista_automacoes_unica(p):
    '''lista_automacoes : automacao'''
    p[0] = [p[1]]

# R4: automacao → AUTOMACAO STRING gatilho_bloco condicao_opt ENTAO lista_acoes FIM
def p_automacao(p):
    '''automacao : AUTOMACAO STRING gatilho_bloco condicao_opt ENTAO lista_acoes FIM'''
    p[0] = AutomacaoNode(
        alias=p[2],
        gatilhos=p[3],
        condicao=p[4],
        acoes=p[6],
        linha=p.lineno(1),
    )

# R5: gatilho_bloco → QUANDO lista_gatilhos
def p_gatilho_bloco(p):
    '''gatilho_bloco : QUANDO lista_gatilhos'''
    p[0] = p[2]

# R6-R7: lista_gatilhos → lista_gatilhos OU gatilho | gatilho
def p_lista_gatilhos_mult(p):
    '''lista_gatilhos : lista_gatilhos OU gatilho'''
    p[0] = p[1] + [p[3]]

def p_lista_gatilhos_unico(p):
    '''lista_gatilhos : gatilho'''
    p[0] = [p[1]]

# R8: gatilho → ENTIDADE_ID MUDAR PARA expressao
def p_gatilho_estado(p):
    '''gatilho : ENTIDADE_ID MUDAR PARA expressao'''
    p[0] = GatilhoEstadoNode(
        entidade_id=p[1],
        expressao=p[4],
        linha=p.lineno(1),
    )

# R9: gatilho → HORARIO STRING
def p_gatilho_horario(p):
    '''gatilho : HORARIO STRING'''
    p[0] = GatilhoHorarioNode(
        horario=p[2],
        linha=p.lineno(1),
    )

# R10-R11: condicao_opt → SE condicao | ε
def p_condicao_opt_presente(p):
    '''condicao_opt : SE condicao'''
    p[0] = p[2]

def p_condicao_opt_vazia(p):
    '''condicao_opt : empty'''
    p[0] = None

def p_empty(p):
    '''empty :'''
    pass

# R12: condicao → ENTIDADE_ID operador expressao
def p_condicao(p):
    '''condicao : ENTIDADE_ID operador expressao'''
    p[0] = CondicaoNode(
        entidade_id=p[1],
        operador=p[2],
        expressao=p[3],
        linha=p.lineno(1),
    )

# R13-R18: operador → MAIOR | MENOR | IGUAL | MAIOR_IGUAL | MENOR_IGUAL | DIFERENTE
def p_operador(p):
    '''operador : MAIOR
                | MENOR
                | IGUAL
                | MAIOR_IGUAL
                | MENOR_IGUAL
                | DIFERENTE'''
    p[0] = p[1]

# R19-R20: expressao → NUMERO | STRING
def p_expressao_numero(p):
    '''expressao : NUMERO'''
    p[0] = ExpressaoNode(tipo='NUMERO', valor=p[1], linha=p.lineno(1))

def p_expressao_string(p):
    '''expressao : STRING'''
    p[0] = ExpressaoNode(tipo='STRING', valor=p[1], linha=p.lineno(1))

# R21-R22: lista_acoes → lista_acoes acao | acao
def p_lista_acoes_mult(p):
    '''lista_acoes : lista_acoes acao'''
    p[0] = p[1] + [p[2]]

def p_lista_acoes_unica(p):
    '''lista_acoes : acao'''
    p[0] = [p[1]]

# R23: acao → LIGAR ENTIDADE_ID
def p_acao_ligar(p):
    '''acao : LIGAR ENTIDADE_ID'''
    p[0] = AcaoLigarNode(entidade_id=p[2], linha=p.lineno(1))

# R24: acao → DESLIGAR ENTIDADE_ID
def p_acao_desligar(p):
    '''acao : DESLIGAR ENTIDADE_ID'''
    p[0] = AcaoDesligarNode(entidade_id=p[2], linha=p.lineno(1))

# R25: acao → ESPERAR TEMPO
def p_acao_esperar(p):
    '''acao : ESPERAR TEMPO'''
    p[0] = AcaoEsperarNode(
        tempo_raw=p[2],
        segundos=_tempo_para_segundos(p[2]),
        linha=p.lineno(1),
    )

# R26: acao → NOTIFICAR STRING PARA STRING
def p_acao_notificar(p):
    '''acao : NOTIFICAR STRING PARA STRING'''
    p[0] = AcaoNotificarNode(mensagem=p[2], destino=p[4], linha=p.lineno(1))

# R27: acao → DEFINIR ENTIDADE_ID expressao
def p_acao_definir(p):
    '''acao : DEFINIR ENTIDADE_ID expressao'''
    p[0] = AcaoDefinirNode(entidade_id=p[2], expressao=p[3], linha=p.lineno(1))

# R28: acao → CHAMAR ENTIDADE_ID ENTIDADE_ID
def p_acao_chamar(p):
    '''acao : CHAMAR ENTIDADE_ID ENTIDADE_ID'''
    p[0] = AcaoChamarNode(servico=p[2], entidade_id=p[3], linha=p.lineno(1))

# R29: acao → bloco_se
def p_acao_bloco_se(p):
    '''acao : bloco_se'''
    p[0] = p[1]

# R30: bloco_se → SE condicao ENTAO lista_acoes bloco_senao_opt FIM
def p_bloco_se(p):
    '''bloco_se : SE condicao ENTAO lista_acoes bloco_senao_opt FIM'''
    p[0] = BlocoSeNode(
        condicao=p[2],
        acoes_entao=p[4],
        acoes_senao=p[5],
        linha=p.lineno(1),
    )

# R31-R32: bloco_senao_opt → SENAO lista_acoes | ε
def p_bloco_senao_opt_presente(p):
    '''bloco_senao_opt : SENAO lista_acoes'''
    p[0] = p[2]

def p_bloco_senao_opt_vazia(p):
    '''bloco_senao_opt : empty'''
    p[0] = []

# ============================================================
# TRATAMENTO DE ERROS — MODO PÂNICO
# ============================================================
def p_error(p):
    """
    Modo Pânico: ao encontrar um erro sintático, o parser
    pula tokens até encontrar um ponto de sincronização
    (PONTO_VIRGULA ou FIM) e tenta continuar a análise.
    """
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


# ============================================================
# Construção do Parser — Método SLR(1)
# ============================================================
parser = yacc.yacc(method='SLR')


# ============================================================
# Funções de interface pública
# ============================================================
def parse(data, lexer_instance=None):
    """
    Analisa sintaticamente um script Homi.
    Retorna (ProgramaNode, lista_de_erros).
    """
    global erros_sintaticos
    erros_sintaticos = []

    from lexer import lexer as default_lexer
    lex_to_use = lexer_instance or default_lexer
    lex_to_use.lineno = 1  # Reseta contagem de linhas

    resultado = parser.parse(data, lexer=lex_to_use)

    if erros_sintaticos:
        print(f"\n>>> {len(erros_sintaticos)} erro(s) sintático(s) encontrado(s).")

    return resultado, erros_sintaticos


# ============================================================
# Teste Local do Sintático
# ============================================================
if __name__ == '__main__':
    from lexer import lexer

    data = '''
    automacao "Corredor - movimento"
        quando sensor.corredor_motion mudar para "on"
            ou binary_sensor.porta mudar para "on"
        se sensor.temperatura > 25
        entao
            ligar light.corredor
            esperar 2min
            desligar light.corredor
            notificar "Luz desligada!" para "mobile_app_zfold4"
            se switch.modo_noturno == "off" entao
                chamar light.turn_on light.led_noturno
            senao
                desligar light.led_noturno
            fim
        fim
    ;

    automacao "Sala - desligar LED"
        quando horario "05:00:00"
        entao
            desligar light.led_sanca
        fim
    '''

    print("=" * 60)
    print("  ANÁLISE SINTÁTICA — Parser SLR(1)")
    print("=" * 60)

    resultado, erros = parse(data, lexer)

    if resultado and not erros:
        print("\n✓ Script Homi validado sintaticamente com sucesso!")
        print(f"  Total de automações: {len(resultado.automacoes)}")
        for i, auto in enumerate(resultado.automacoes, 1):
            print(f"  [{i}] \"{auto.alias}\" — "
                  f"{len(auto.gatilhos)} gatilho(s), "
                  f"{len(auto.acoes)} ação(ões)")
    elif resultado:
        print(f"\n⚠ Script analisado com {len(erros)} erro(s).")
    else:
        print("\n✗ Falha na análise sintática.")