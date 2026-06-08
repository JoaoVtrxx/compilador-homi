import ply.lex as lex

# Lista de Tokens
tokens = (
    # Palavras reservadas
    'AUTOMACAO', 'FIM', 'QUANDO', 'SE', 'SENAO', 'ENTAO',
    'LIGAR', 'DESLIGAR', 'ESPERAR', 'NOTIFICAR', 'DEFINIR', 'CHAMAR',
    'MUDAR', 'PARA', 'HORARIO', 'OU', 'E', 'MODO', 'ATE',
    # Literais e valores
    'ENTIDADE_ID', 'TEMPO', 'NUMERO', 'STRING',
    # Operadores relacionais
    'MAIOR', 'MENOR', 'IGUAL', 'MAIOR_IGUAL', 'MENOR_IGUAL', 'DIFERENTE',
    # Delimitadores
    'PONTO_VIRGULA',
)

# Palavras reservadas (mapeamento: minúsculas -> token)
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
    'e':         'E',
    'modo':      'MODO',
    'ate':       'ATE',
}

# Ordem importa no PLY, pois ele lê as regras de cima para baixo e para quando encontra uma correspondência.

# Regras para Tokens de Operadores
# Operadores compostos primeiro (>=, <=). Não precisava, pois PLY já orneda internamente, para os maiores virem primeiro.
t_MAIOR_IGUAL   = r'>='
t_MENOR_IGUAL   = r'<='
t_DIFERENTE     = r'!='
t_IGUAL         = r'=='
t_MAIOR         = r'>'
t_MENOR         = r'<'
t_PONTO_VIRGULA = r';'

# Regras Complexas

# Entidades do Home Assistant (ex: sensor.temperatura_sala, light.luz_teto)
def t_ENTIDADE_ID(t):
    r'[a-z_]+\.[a-z0-9_]+'
    return t

# Unidades de Tempo (ex: 10s, 5min, 1h, 500ms)
# Deve vir antes de t_NUMERO para capturar "10s" ao invés de "10"
def t_TEMPO(t):
    r'\d+(ms|min|s|h)'
    return t

# Números inteiros e decimais
def t_NUMERO(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)  # Transforma esse atributo de String para Float ou Int já.
    return t

# Strings (texto entre aspas duplas, suportando escape com \)
def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'   # Lê qualquer simbolo sem ser '\' ou '\n', e, se tiver '\', ele já lê o próximo, para poder colocar aspas
    t.value = t.value[1:-1]  # Remove as aspas externas
    return t

# Palavras Reservadas
def t_ID(t):
    r'[a-zA-ZÀ-ÿ_][a-zA-ZÀ-ÿ_0-9]*' # Isso aqui pega "qualquer coisa" que comece com letra ou underscore
    t.type = reserved.get(t.value.lower(), 'ID') # Busca nas reservadas a String lida. Se não encontrar, devolve "ID"
    if t.type == 'ID':
        # Identificadores soltos não são válidos.
        print(f"Erro Léxico: Identificador desconhecido '{t.value}' na linha {t.lexer.lineno}")
        return None  # Descarta o token inválido
    return t

# Comentários (ignorados)
def t_COMENTARIO(t):
    r'\#.*'
    pass  # Ignora o token

# Qubras de linha. São ignoradas, não fazem diferença.
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Ignora espaços e tabs. São ignorados, não fazem diferença. Identação é só visual.
t_ignore = ' \t'

# Tratamento de Erros Léxicos
def t_error(t):
    print(f"Erro Léxico: Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

lexer = lex.lex() # Procura todas as variáveis e funções que começam com 't_' dentro desse arquivo, extraindo
                  # todas as regexes no formato "  r'{regex}'  " definidas na variável ou na primeira linha da função.
                  # O t.type sempre é preenchido com o nome da função que vem após o 't_'.
                  # O t.value é a string recebida. O t.lineno é a linha e o t.lexpos é a posição que encontrou o token.