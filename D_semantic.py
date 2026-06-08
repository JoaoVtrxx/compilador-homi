from F_ast_nodes import (
    ProgramaNode, AutomacaoNode,
    GatilhoEstadoNode, GatilhoHorarioNode,
    CondicaoNode, ExpressaoNode,
    AcaoLigarNode, AcaoDesligarNode, AcaoEsperarNode,
    AcaoNotificarNode, AcaoDefinirNode, AcaoChamarNode,
    BlocoSeNode,
)

# Tabela de Símbolos: Domínios conhecidos e seus tipos/capacidades
DOMINIOS = {
    'light':                 {'tipo': 'atuador',  'acoes': ['ligar', 'desligar', 'definir']}, # ex.: LIGAR light.luz_cozinha
    'switch':                {'tipo': 'atuador',  'acoes': ['ligar', 'desligar']},  # ex.: DESLIGAR switch.switch_1
    'cover':                 {'tipo': 'atuador',  'acoes': ['ligar', 'desligar']},  
    'media_player':          {'tipo': 'atuador',  'acoes': ['ligar', 'desligar', 'definir']},
    'fan':                   {'tipo': 'atuador',  'acoes': ['ligar', 'desligar', 'definir']}, # ex.: DEFINIR fan.ventilador_cozinha "high"
    'sensor':                {'tipo': 'sensor',   'acoes': []},
    'binary_sensor':         {'tipo': 'sensor',   'acoes': []},
    'weather':               {'tipo': 'sensor',   'acoes': []},
    'alarm_control_panel':   {'tipo': 'painel',   'acoes': ['ligar', 'desligar']},
    'timer':                 {'tipo': 'auxiliar',  'acoes': ['chamar']}, # Não serve pra nada a ação 'chamar' aqui, só pra documentação
    'input_boolean':         {'tipo': 'auxiliar',  'acoes': ['ligar', 'desligar']},
    'input_number':          {'tipo': 'auxiliar',  'acoes': ['definir']},
    'input_text':            {'tipo': 'auxiliar',  'acoes': ['definir']},
    'automation':            {'tipo': 'auxiliar',  'acoes': ['chamar']}, # Não serve pra nada a ação 'chamar' aqui, só pra documentação
    'notify':                {'tipo': 'servico',  'acoes': ['notificar']},  # Não serve pra nada a ação 'notificar' aqui, só pra documentação
    'script':                {'tipo': 'auxiliar',  'acoes': ['chamar']}, # Não serve pra nada a ação 'chamar' aqui, só pra documentação
    'scene':                 {'tipo': 'auxiliar',  'acoes': ['chamar']}, # Não serve pra nada a ação 'chamar' aqui, só pra documentação
}

# Serviços válidos por domínio (para a ação CHAMAR)
SERVICOS_VALIDOS = {
    'light':        ['turn_on', 'turn_off', 'toggle'],   # ex.: CHAMAR light.turn_on light.luz_cozinha 
    'switch':       ['turn_on', 'turn_off', 'toggle'],   # ex.: CHAMAR switch.turn_off switch.smart_switch_1
    'cover':        ['open_cover', 'close_cover', 'toggle', 'stop_cover'],
    'media_player': ['turn_on', 'turn_off', 'volume_set', 'play_media', 'media_pause'], # ex.: CHAMAR media_player.media_pause media_player.tv_sala
    'fan':          ['turn_on', 'turn_off', 'toggle', 'set_speed'], # ex.: CHAMAR fan.set_speed fan.ventilador "high"
    'timer':        ['start', 'cancel', 'finish'], # ex.: CHAMAR timer.start  timer.meu_cronometro_da_cozinha
    'automation':   ['trigger', 'turn_on', 'turn_off'], # ex.: CHAMAR automation.trigger automation.cozinha_ligar_luzes
    'notify':       ['mobile_app_*', 'send_message'],
    'input_boolean':['turn_on', 'turn_off', 'toggle'],
    'input_number': ['set_value'],
    'input_text':   ['set_value'],
    'script':       ['turn_on'],
    'scene':        ['turn_on'],
    'tts':          ['speak'],
    'alexa_devices':['send_text_command', 'send_sound'],
}

# Se o serviço está aqui, a expressão é OBRIGATÓRIA no CHAMAR
SERVICO_COM_EXPRESSAO = {
    'volume_set':         'volume_level',    # ex.: chamar media_player.volume_set media_player.tv 0.09
    'set_speed':          'speed',           # ex.: chamar fan.set_speed fan.ventilador "high"
    'set_value':          'value',           # ex.: chamar input_number.set_value input_number.brilho 80
    'speak':              'message',         # ex.: chamar tts.speak tts.google "ola mundo"
    'send_text_command':  'text_command',    # ex.: chamar alexa_devices.send_text_command alexa_devices.echo "desligar tela"
    'send_sound':         'sound',           # ex.: chamar alexa_devices.send_sound alexa_devices.echo "amzn_sfx_doorbell_chime_01"
    'play_media':         'media_content_id', # ex.: chamar media_player.play_media media_player.tv "https://..."
}

class AnalisadorSemantico:
    # Percorre a AST e realiza verificações semânticas:
    # - Validação de domínio (entidades pertencem a domínios conhecidos)
    # - Verificação de tipos (ações compatíveis com tipo do domínio)
    # - Consistência de serviços (serviço existe para o domínio)

    def __init__(self):
        self.erros = []      # Lista de erros semânticos (impedem compilação)
        self.avisos = []     # Lista de avisos (não impedem compilação)
        self.tabela_simbolos = {}  # entidade_id -> {dominio, tipo, linha_decl}

    def _extrair_dominio(self, entidade_id):
        # Extrai o domínio de um entity_id (ex: 'sensor' de 'sensor.temperatura').
        partes = entidade_id.split('.', 1)
        return partes[0] if len(partes) == 2 else None

    def _registrar_entidade(self, entidade_id, linha):
        # Registra uma entidade na tabela de símbolos.
        if entidade_id not in self.tabela_simbolos:
            dominio = self._extrair_dominio(entidade_id)
            self.tabela_simbolos[entidade_id] = {
                'dominio': dominio,                                            # ex.: light
                'tipo': DOMINIOS.get(dominio, {}).get('tipo', 'desconhecido'), # ex.: atuador
                'linha_primeira_ref': linha,
            }

    def _validar_dominio(self, entidade_id, linha):
        # Verifica se o domínio da entidade é conhecido.
        dominio = self._extrair_dominio(entidade_id)
        if dominio and dominio not in DOMINIOS:
            self.avisos.append(
                f"Aviso (linha {linha}): Domínio '{dominio}' da entidade "
                f"'{entidade_id}' não é um domínio padrão do Home Assistant."
            )

    def _validar_acao_entidade(self, acao_nome, entidade_id, linha):
        # Verifica se a ação é compatível com o domínio da entidade.
        dominio = self._extrair_dominio(entidade_id)
        if dominio and dominio in DOMINIOS:
            acoes_permitidas = DOMINIOS[dominio]['acoes']
            if acao_nome not in acoes_permitidas:
                tipo_dom = DOMINIOS[dominio]['tipo']
                self.erros.append(
                    f"Erro Semântico (linha {linha}): Não é possível executar "
                    f"'{acao_nome}' na entidade '{entidade_id}' - domínio "
                    f"'{dominio}' (tipo: {tipo_dom}) não suporta esta ação."
                )

    def _validar_servico(self, servico_str, entidade_alvo, expressao, linha):
        # Verifica se o serviço chamado é válido para o domínio.
        partes = servico_str.split('.', 1)
        if len(partes) != 2:
            self.erros.append(
                f"Erro Semântico (linha {linha}): Serviço '{servico_str}' "
                f"deve estar no formato 'dominio.servico'."
            )
            return

        dom_servico, nome_servico = partes
        if dom_servico in SERVICOS_VALIDOS:
            servicos = SERVICOS_VALIDOS[dom_servico]
            # Verifica match exato ou wildcard (mobile_app_*)
            match = any(
                nome_servico == s or (s.endswith('*') and nome_servico.startswith(s[:-1]))
                for s in servicos
            )
            if not match:
                self.erros.append(
                    f"Erro Semântico (linha {linha}): Serviço '{nome_servico}' "
                    f"não é válido para o domínio '{dom_servico}'. "
                    f"Serviços aceitos: {servicos}"
                )

        # Verifica se o serviço requer valor (expressão)
        if nome_servico in SERVICO_COM_EXPRESSAO:
            if expressao is None:
                data_key = SERVICO_COM_EXPRESSAO[nome_servico]
                self.erros.append(
                    f"Erro Semântico (linha {linha}): Serviço '{servico_str}' "
                    f"requer um valor ('{data_key}'). "
                    f"Ex.: chamar {servico_str} {entidade_alvo} <valor>"
                )
        else:
            if expressao is not None:
                self.avisos.append(
                    f"Aviso (linha {linha}): Serviço '{servico_str}' "  # Só ignora o valor, mas não ocorre erro
                    f"normalmente não recebe um valor, mas foi fornecido "
                    f"'{expressao.valor}'. O valor será incluído como 'value' no YAML."
                )

        # Verifica compatibilidade domínio serviço vs domínio entidade alvo
        dom_alvo = self._extrair_dominio(entidade_alvo)
        if dom_alvo and dom_servico != dom_alvo and dom_servico not in ('automation', 'script', 'scene'): # 'CHAMAR script.piscar_luz light.luz_da_sala' não precisa estar no mesmo domínio, passa luz_da_sala como argumento do script
            self.avisos.append(
                f"Aviso (linha {linha}): Serviço '{servico_str}' é do domínio " # É só um aviso para não bloquear coisas que funcionam mas são mais específicas
                f"'{dom_servico}', mas a entidade alvo '{entidade_alvo}' é do " # ex.: CHAMAR homeassistant.turn_on light.luz_da_sala
                f"domínio '{dom_alvo}'."
            )

    # Visitação recursiva da AST
    def analisar(self, programa):
        # Ponto de entrada: analisa o programa inteiro.
        if not isinstance(programa, ProgramaNode):
            self.erros.append("Erro Semântico: AST inválida (raiz não é ProgramaNode).")
            return self.erros, self.avisos

        # Verificar nomes duplicados de automações
        nomes_vistos = {}
        for auto in programa.automacoes:
            if auto.alias in nomes_vistos:
                self.avisos.append(
                    f"Aviso (linha {auto.linha}): Automação com nome duplicado "
                    f"'{auto.alias}' (primeira ocorrência na linha {nomes_vistos[auto.alias]})."
                )
            else:
                nomes_vistos[auto.alias] = auto.linha

            self._analisar_automacao(auto)

        return self.erros, self.avisos

    def _analisar_automacao(self, auto):
        # Analisa uma automação.
        # Verificar gatilhos
        for gatilho in auto.gatilhos:
            self._analisar_gatilho(gatilho)

        # Verificar condições (lista)
        for condicao in auto.condicoes:
            self._analisar_condicao(condicao)

        # Verificar ações
        for acao in auto.acoes:
            self._analisar_acao(acao)

    def _analisar_gatilho(self, gatilho):
        # Analisa um gatilho.
        if isinstance(gatilho, GatilhoEstadoNode):
            self._registrar_entidade(gatilho.entidade_id, gatilho.linha)
            self._validar_dominio(gatilho.entidade_id, gatilho.linha)
        elif isinstance(gatilho, GatilhoHorarioNode):
            # Validar formato de horário (HH:MM:SS)
            import re
            if not re.match(r'^\d{2}:\d{2}:\d{2}$', gatilho.horario):
                self.avisos.append(
                    f"Aviso (linha {gatilho.linha}): Formato de horário "
                    f"'{gatilho.horario}' pode não ser válido. "
                    f"Use o formato HH:MM:SS."
                )

    def _analisar_condicao(self, condicao):
        # Analisa uma condição.
        self._registrar_entidade(condicao.entidade_id, condicao.linha)
        self._validar_dominio(condicao.entidade_id, condicao.linha)

        # Verificação de tipos: operadores numéricos (>, <, >=, <=) só com NUMERO
        if condicao.operador in ('>', '<', '>=', '<='):
            if condicao.expressao.tipo != 'NUMERO':
                self.erros.append(
                    f"Erro Semântico (linha {condicao.linha}): Operador "
                    f"'{condicao.operador}' requer um valor numérico, mas "
                    f"recebeu STRING '{condicao.expressao.valor}'."
                )

    def _analisar_acao(self, acao):
        # Analisa uma ação.
        if isinstance(acao, AcaoLigarNode):
            self._registrar_entidade(acao.entidade_id, acao.linha)
            self._validar_dominio(acao.entidade_id, acao.linha)
            self._validar_acao_entidade('ligar', acao.entidade_id, acao.linha) # Verifica se o dominio da entidade aceita 'ligar'

        elif isinstance(acao, AcaoDesligarNode):
            self._registrar_entidade(acao.entidade_id, acao.linha)
            self._validar_dominio(acao.entidade_id, acao.linha)
            self._validar_acao_entidade('desligar', acao.entidade_id, acao.linha) # Verifica se o dominio da entidade aceita 'desligar'

        elif isinstance(acao, AcaoEsperarNode):
            if acao.segundos <= 0:
                self.avisos.append(
                    f"Aviso (linha {acao.linha}): Tempo de espera "
                    f"'{acao.tempo_raw}' resulta em 0 ou valor negativo."
                )

        elif isinstance(acao, AcaoNotificarNode):
            pass  # Notificações são sempre válidas sintaticamente

        elif isinstance(acao, AcaoDefinirNode):
            self._registrar_entidade(acao.entidade_id, acao.linha)
            self._validar_dominio(acao.entidade_id, acao.linha)
            self._validar_acao_entidade('definir', acao.entidade_id, acao.linha) # Verifica se o dominio da entidade aceita 'definir'

        elif isinstance(acao, AcaoChamarNode):
            self._registrar_entidade(acao.entidade_id, acao.linha)
            self._validar_dominio(acao.entidade_id, acao.linha)
            self._validar_servico(acao.servico, acao.entidade_id, acao.expressao, acao.linha) # Verifica se o serviço é válido para o domínio

        elif isinstance(acao, BlocoSeNode):
            for cond in acao.condicoes:
                self._analisar_condicao(cond)
            for sub_acao in acao.acoes_entao:
                self._analisar_acao(sub_acao)
            for sub_acao in acao.acoes_senao:
                self._analisar_acao(sub_acao)

    # Relatório da Tabela de Símbolos
    def imprimir_tabela_simbolos(self): # so pra verbose
        # Imprime a tabela de símbolos de forma formatada.
        print("\n" + "-" * 70)
        print("  TABELA DE SÍMBOLOS")
        print("-" * 70)
        print(f"  {'Entidade':<40s} {'Domínio':<20s} {'Tipo':<15s}")
        print("-" * 70)
        for entidade, info in sorted(self.tabela_simbolos.items()):
            print(f"  {entidade:<40s} {info['dominio']:<20s} {info['tipo']:<15s}")
        print("-" * 70)