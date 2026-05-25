import ply.lex as lex

# 1. Lista de Tokens
tokens = (
    'QUANDO', 'SE', 'ENTAO', 'LIGAR', 'DESLIGAR', 'MUDAR', 'PARA',
    'ENTIDADE_ID', 'TEMPO', 'NUMERO', 'STRING',
    'MAIOR', 'MENOR', 'IGUAL',
)

# 2. Palavras Reservadas (Dicionário para facilitar)
reserved = {
    'quando': 'QUANDO',
    'se': 'SE',
    'entao': 'ENTAO',
    'ligar': 'LIGAR',
    'desligar': 'DESLIGAR',
    'mudar': 'MUDAR',
    'para': 'PARA'
}

# 3. Regras de Expressões Regulares para Tokens Simples
t_MAIOR = r'>'
t_MENOR = r'<'
t_IGUAL = r'=='

# 4. Regras Complexas (Com funções)

# Entidades do Home Assistant (ex: sensor.temperatura_sala, light.luz_teto)
def t_ENTIDADE_ID(t):
    r'[a-z_]+ \. [a-z0-9_]+'
    return t

# Unidades de Tempo (ex: 10s, 5min, 1h)
def t_TEMPO(t):
    r'\d+(s|min|h|ms)'
    return t

# Números
def t_NUMERO(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

# Strings (texto entre aspas)
def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value[1:-1] # Remove as aspas
    return t

# Identificadores e Palavras Reservadas
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value.lower(), 'ID') # Checa se é palavra reservada
    if t.type == 'ID':
        # Se não for reservada e não bater com ENTIDADE_ID, é um erro de sintaxe na linguagem Homi
        t_error(t)
    return t

# Regra para ignorar comentários (iniciados com #)
def t_COMENTARIO(t):
    r'\#.*'
    pass # Ignora o token

# Rastreador de número de linhas (exigência para detecção de erros)
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Ignora espaços e tabs
t_ignore  = ' \t'

# Tratamento de Erros Léxicos
def t_error(t):
    print(f"Erro Léxico: Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# Constrói o Lexer
lexer = lex.lex()

# ==========================================
# Teste Local do Lexer
# ==========================================
if __name__ == '__main__':
    data = '''
    # Teste de automação Homi
    quando sensor.temperatura mudar para "quente"
    se sensor.temperatura > 25
    entao ligar light.luz_sala
    '''
    
    lexer.input(data)
    print("Tokens reconhecidos:")
    for tok in lexer:
        print(tok)