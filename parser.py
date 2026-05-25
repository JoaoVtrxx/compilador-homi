import ply.yacc as yacc

# Importa a lista de tokens do arquivo lexer.py que criamos
from lexer import tokens

# Regra inicial (A automação completa)
def p_automacao(p):
    '''automacao : QUANDO gatilho condicao_opt ENTAO acao'''
    print("Sucesso: Script Homi validado sintaticamente!")
    # p[0] = ... (No futuro, aqui vocês vão montar a Árvore Sintática / AST)

def p_gatilho(p):
    '''gatilho : ENTIDADE_ID MUDAR PARA estado'''
    pass

# A condição é opcional, então tem a regra vazia (empty)
def p_condicao_opt(p):
    '''condicao_opt : SE ENTIDADE_ID operador_logico valor
                    | empty'''
    pass

def p_empty(p):
    'empty :'
    pass

def p_acao(p):
    '''acao : comando ENTIDADE_ID'''
    pass

def p_estado(p):
    '''estado : STRING
              | NUMERO'''
    pass

def p_operador_logico(p):
    '''operador_logico : MAIOR
                       | MENOR
                       | IGUAL'''
    pass

def p_comando(p):
    '''comando : LIGAR
               | DESLIGAR'''
    pass

def p_valor(p):
    '''valor : NUMERO
             | STRING'''
    pass

# Tratamento de Erros Sintáticos (Modo Pânico exigido no trabalho)
def p_error(p):
    if p:
        print(f"Erro de Sintaxe: O token '{p.value}' (tipo {p.type}) na linha {p.lineno} não era esperado aqui.")
        
        # TODO BAGGIO: Implementar aqui a lógica de Modo Pânico
        # A ideia é pedir pro parser pular tokens (p.lexer.token()) até encontrar 
        # um ponto e vírgula ';' ou quebra de linha para poder continuar analisando o resto do arquivo.
        
    else:
        print("Erro de Sintaxe: Fim de arquivo inesperado (EOF).")

# Constrói o parser
parser = yacc.yacc()

# ==========================================
# Teste Local do Sintático
# ==========================================
if __name__ == '__main__':
    # Opcional: Importar o lexer apenas para o teste rodar direto
    from lexer import lexer
    
    data = '''
    quando sensor.temperatura mudar para "quente"
    se sensor.temperatura > 25
    entao ligar light.luz_sala
    '''
    
    print("Iniciando análise sintática...")
    parser.parse(data, lexer=lexer)