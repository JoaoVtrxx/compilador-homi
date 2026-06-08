import os
import sys
import json
import io
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Servidor HTTP local nativo para a interface web do compilador.
# Desenvolvido para rodar sem dependências externas adicionais.

# Adiciona o diretório pai ao sys.path para podermos importar o compilador
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class CompileHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Desabilita o log padrão de requisições no terminal para manter a saída limpa
        pass

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.serve_file('index.html', 'text/html')
        elif parsed_path.path == '/api/examples':
            self.list_examples()
        elif parsed_path.path == '/api/example':
            query = urllib.parse.parse_qs(parsed_path.query)
            name = query.get('name', [None])[0]
            self.get_example(name)
        else:
            # Filtro simples de segurança para evitar directory traversal
            filename = parsed_path.path.lstrip('/')
            if filename in ['index.html']:
                self.serve_file(filename, 'text/html')
            else:
                self.send_error(404, 'Arquivo Não Encontrado')

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == '/api/compile':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                code = data.get('code', '')
                self.compile_code(code)
            except Exception as e:
                self.send_json({'error': f"Erro no corpo da requisição: {str(e)}"}, status=400)
        else:
            self.send_error(404, 'API Endpoint Não Encontrado')

    def serve_file(self, filename, content_type):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(dir_path, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', f'{content_type}; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except Exception as e:
                self.send_error(500, f'Erro Interno no Servidor: {str(e)}')
        else:
            self.send_error(404, f'Arquivo {filename} Não Encontrado')

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def list_examples(self):
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        examples_dir = os.path.join(parent_dir, 'exemplos')
        if not os.path.exists(examples_dir):
            self.send_json([])
            return
        
        files = [f for f in os.listdir(examples_dir) if f.endswith('.homi')]
        self.send_json(sorted(files))

    def get_example(self, name):
        if not name:
            self.send_json({'error': 'Parâmetro name ausente'}, status=400)
            return
        
        # Remove partes de diretórios por segurança
        name = os.path.basename(name)
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        file_path = os.path.join(parent_dir, 'exemplos', name)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_json({'name': name, 'content': content})
            except Exception as e:
                self.send_json({'error': str(e)}, status=500)
        else:
            self.send_json({'error': 'Exemplo não encontrado'}, status=404)

    def compile_code(self, code):
        # Redireciona o stdout e stderr para capturar o log completo da compilação
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_buf = io.StringIO()
        sys.stderr = stderr_buf = io.StringIO()

        tokens_list = []
        ast_serialized = None
        erros_sintaticos = []
        erros_semanticos = []
        avisos_semanticos = []
        tabela_simbolos = {}
        yaml_saida = ''
        success = False

        try:
            # 1. Análise Léxica
            from B_lexer import lexer
            lexer.input(code)
            lexer.lineno = 1
            try:
                for tok in lexer:
                    tokens_list.append({
                        'line': tok.lineno,
                        'type': tok.type,
                        'value': str(tok.value)
                    })
            except Exception as e:
                print(f"Erro Léxico Fatal: {str(e)}")

            # 2. Análise Sintática
            from C_parser import parse
            ast, erros_sintaticos = parse(code)

            # 3. Análise Semântica
            if ast and not erros_sintaticos:
                from D_semantic import AnalisadorSemantico
                analisador = AnalisadorSemantico()
                erros_semanticos, avisos_semanticos = analisador.analisar(ast)
                
                # Formata tabela de símbolos para melhor exibição no frontend
                for k, v in analisador.tabela_simbolos.items():
                    tabela_simbolos[k] = {
                        'dominio': v.get('dominio', '-'),
                        'tipo': v.get('tipo', '-'),
                        'linha': v.get('linha_primeira_ref', '-')
                    }
                
                ast_serialized = self.serialize_node(ast)

                # 4. Geração de Código
                if not erros_semanticos:
                    from E_codegen import GeradorYAML
                    gerador = GeradorYAML()
                    yaml_saida = gerador.gerar(ast)
                    success = True

        except Exception as e:
            print(f"Erro Crítico durante compilação: {str(e)}")
            import traceback
            traceback.print_exc()

        # Restaura a saída padrão do sistema
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        logs = stdout_buf.getvalue() + stderr_buf.getvalue()

        # Constrói resposta unificada
        res = {
            'success': success,
            'tokens': tokens_list,
            'ast': ast_serialized,
            'syntax_errors': erros_sintaticos,
            'semantic_errors': erros_semanticos,
            'semantic_warnings': avisos_semanticos,
            'symbol_table': tabela_simbolos,
            'yaml': yaml_saida,
            'logs': logs
        }
        self.send_json(res)

    def serialize_node(self, node):
        """Transforma recursivamente nós da AST (dataclasses) em dicionários para JSON."""
        if node is None:
            return None
        if isinstance(node, list):
            return [self.serialize_node(x) for x in node]
        if hasattr(node, '__dict__'):
            res = {'node_type': node.__class__.__name__}
            for k, v in node.__dict__.items():
                # Remove atributos privados
                if not k.startswith('_'):
                    res[k] = self.serialize_node(v)
            return res
        # Converte valores literais não serializáveis em string se necessário
        return node

def main():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, CompileHandler)
    print("=" * 65)
    print(f" Servidor da interface grafica iniciado!")
    print(f" Abra no seu navegador: http://localhost:{port}")
    print("=" * 65)
    print(" Para parar o servidor: pressione Ctrl+C neste terminal.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n Servidor finalizado com sucesso.")
        sys.exit(0)

if __name__ == '__main__':
    main()
