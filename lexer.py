import ply.lex as lex

# ============================================================
# 1. Lista de Tokens
# ============================================================
tokens = (
    # Palavras reservadas
    'AUTOMACAO', 'FIM', 'QUANDO', 'SE', 'SENAO', 'ENTAO',
    'LIGAR', 'DESLIGAR', 'ESPERAR', 'NOTIFICAR', 'DEFINIR', 'CHAMAR',
    'MUDAR', 'PARA', 'HORARIO', 'OU',
    # Valores e identificadores
    'ENTIDADE_ID', 'TEMPO', 'NUMERO', 'STRING',
    # Operadores relacionais
    'MAIOR', 'MENOR', 'IGUAL', 'MAIOR_IGUAL', 'MENOR_IGUAL', 'DIFERENTE',
    # Delimitadores
    'PONTO_VIRGULA',
)

# ============================================================
# 2. Palavras Reservadas (mapeamento minúsculas -> token)
# ============================================================
reserved = {
    'automacao': 'AUTOMACAO',
    'fim':       'FIM',
    'quando':    'QUANDO',
    'se':        'SE',
    'senao':     'SENAO',
    'entao':     'ENTAO',
    'ligar':     'LIGAR',
    'desligar':  'DESLIGAR',
    'esperar':   'ESPERAR',
    'notificar': 'NOTIFICAR',
    'definir':   'DEFINIR',
    'chamar':    'CHAMAR',
    'mudar':     'MUDAR',
    'para':      'PARA',
    'horario':   'HORARIO',
    'ou':        'OU',
}

# ============================================================
# 3. Regras para Tokens de Operadores (strings fixas)
#    Ordem: operadores compostos primeiro (>=, <=, !=, ==)
# ============================================================
t_MAIOR_IGUAL   = r'>='
t_MENOR_IGUAL   = r'<='
t_DIFERENTE     = r'!='
t_IGUAL         = r'=='
t_MAIOR         = r'>'
t_MENOR         = r'<'
t_PONTO_VIRGULA = r';'

# ============================================================
# 4. Regras Complexas (funções — ordem importa no PLY)
# ============================================================

# Entidades do Home Assistant (ex: sensor.temperatura_sala, light.luz_teto)
# ATENÇÃO: deve vir ANTES de t_TEMPO e t_NUMERO para ter prioridade
def t_ENTIDADE_ID(t):
    r'[a-z_]+\.[a-z0-9_]+'
    return t

# Unidades de Tempo (ex: 10s, 5min, 1h, 500ms)
# Deve vir antes de t_NUMERO para capturar "10s" inteiro ao invés de "10"
def t_TEMPO(t):
    r'\d+(ms|min|s|h)'
    return t

# Números inteiros e decimais
def t_NUMERO(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

# Strings (texto entre aspas duplas, suportando escape com \)
def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value[1:-1]  # Remove as aspas externas
    return t

# Identificadores e Palavras Reservadas
def t_ID(t):
    r'[a-zA-ZÀ-ÿ_][a-zA-ZÀ-ÿ_0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID')
    if t.type == 'ID':
        # Na linguagem Homi, identificadores soltos não são válidos.
        # Apenas palavras reservadas e ENTIDADE_ID são aceitos.
        print(f"Erro Léxico: Identificador desconhecido '{t.value}' na linha {t.lexer.lineno}")
        return None  # Descarta o token inválido
    return t

# ============================================================
# 5. Comentários (ignorados)
# ============================================================
def t_COMENTARIO(t):
    r'\#.*'
    pass  # Ignora o token

# ============================================================
# 6. Rastreador de linhas e caracteres ignorados
# ============================================================
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Ignora espaços e tabs
t_ignore = ' \t'

# ============================================================
# 7. Tratamento de Erros Léxicos
# ============================================================
def t_error(t):
    print(f"Erro Léxico: Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# ============================================================
# Construção do Lexer
# ============================================================
lexer = lex.lex()

# ============================================================
# Teste Local do Lexer
# ============================================================
if __name__ == '__main__':
    data = '''
    # Automação de teste Homi
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
    ;
    '''

    lexer.input(data)
    print("=" * 60)
    print("  ANÁLISE LÉXICA — Tokens Reconhecidos")
    print("=" * 60)
    for tok in lexer:
        print(f"  Linha {tok.lineno:3d} | {tok.type:15s} | {tok.value!r}")
    print("=" * 60)