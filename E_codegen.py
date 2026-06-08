import yaml
import uuid
import time

from F_ast_nodes import (
    ProgramaNode, AutomacaoNode,
    GatilhoEstadoNode, GatilhoHorarioNode,
    CondicaoNode,
    AcaoLigarNode, AcaoDesligarNode, AcaoEsperarNode,
    AcaoNotificarNode, AcaoDefinirNode, AcaoChamarNode,
    BlocoSeNode,
)

from D_semantic import SERVICO_COM_EXPRESSAO

class GeradorYAML: # Gerador de Código Intermediário: AST -> YAML (Home Assistant)
    # Percorre a AST e gera uma lista de automações no formato YAML

    def __init__(self):
        self._id_counter = int(time.time() * 1000)

    def _gerar_id(self):
        # Gera um ID numérico único para a automação. Pseudoaleatório baseado no time com incremento. O que importa é ele ser unico
        self._id_counter += 1
        return str(self._id_counter)

    def _extrair_dominio(self, entidade_id):
        # Extrai o domínio de um entity_id. ex.: light de light.luz_cozinha
        partes = entidade_id.split('.', 1)
        return partes[0] if len(partes) == 2 else 'switch'

    # Geração de Gatilhos (Triggers)
    def _gerar_gatilho(self, gatilho):
        # Converte um GatilhoNode para dict YAML de trigger.
        if isinstance(gatilho, GatilhoEstadoNode):
            trigger = {
                'entity_id': [gatilho.entidade_id],
                'to': str(gatilho.expressao.valor),
                'trigger': 'state',
            }
            return trigger

        elif isinstance(gatilho, GatilhoHorarioNode):
            return {
                'trigger': 'time',
                'at': gatilho.horario,
            }

    # Geração de Condições
    def _gerar_condicao(self, condicao):
        # Converte uma CondicaoNode para dict YAML de condition.

        # Se o operador é == ou !=, usamos condition: state
        if condicao.operador in ('==', '!='):
            cond = {
                'condition': 'state',
                'entity_id': condicao.entidade_id,
                'state': str(condicao.expressao.valor),
            }
            # Para !=, não há suporte direto. usamos template
            if condicao.operador == '!=':
                cond = {
                    'condition': 'template',
                    'value_template': (
                        f"{{{{ states('{condicao.entidade_id}') "
                        f"!= '{condicao.expressao.valor}' }}}}"
                    ),
                }
            return cond

        # Para operadores numéricos (>, <, >=, <=), usamos numeric_state
        cond = {
            'condition': 'numeric_state',
            'entity_id': condicao.entidade_id,
        }
        valor = condicao.expressao.valor

        if condicao.operador == '>':
            cond['above'] = valor
        elif condicao.operador == '>=':
            cond['above'] = valor - (0.001 if isinstance(valor, float) else 1)
        elif condicao.operador == '<':
            cond['below'] = valor
        elif condicao.operador == '<=':
            cond['below'] = valor + (0.001 if isinstance(valor, float) else 1)

        return cond

    def _gerar_condicoes(self, condicoes):
        # Converte uma lista de CondicaoNode para lista de dicts YAML.
        return [self._gerar_condicao(c) for c in condicoes]

    # Geração de Ações
    def _gerar_acao(self, acao):
        # Converte um AcaoNode para dict YAML de action.

        if isinstance(acao, AcaoLigarNode):
            dominio = self._extrair_dominio(acao.entidade_id)
            return {
                'action': f'{dominio}.turn_on',
                'metadata': {},
                'data': {},
                'target': {
                    'entity_id': acao.entidade_id,
                },
            }

        elif isinstance(acao, AcaoDesligarNode):
            dominio = self._extrair_dominio(acao.entidade_id)
            return {
                'action': f'{dominio}.turn_off',
                'metadata': {},
                'data': {},
                'target': {
                    'entity_id': acao.entidade_id,
                },
            }

        elif isinstance(acao, AcaoEsperarNode):
            segundos = acao.segundos
            horas = int(segundos // 3600)
            segs_rest = segundos % 3600
            minutos = int(segs_rest // 60)
            segundos = int(segs_rest % 60)
            milissegundos = int(round((segundos - int(segundos)) * 1000))

            return {
                'delay': {
                    'hours': horas,
                    'minutes': minutos,
                    'seconds': segundos,
                    'milliseconds': milissegundos,
                },
            }

        elif isinstance(acao, AcaoNotificarNode):
            return {
                'action': f'notify.{acao.destino}',
                'metadata': {},
                'data': {
                    'message': acao.mensagem,
                },
            }

        elif isinstance(acao, AcaoDefinirNode):
            dominio = self._extrair_dominio(acao.entidade_id)
            # Escolhe o serviço baseado no domínio
            if dominio == 'input_number':
                servico = 'input_number.set_value'
                data = {'value': acao.expressao.valor}
            elif dominio == 'input_text':
                servico = 'input_text.set_value'
                data = {'value': str(acao.expressao.valor)}
            elif dominio == 'light':
                servico = 'light.turn_on'
                data = {'brightness_pct': acao.expressao.valor}
            else:
                servico = f'{dominio}.set_value'
                data = {'value': acao.expressao.valor}

            return {
                'action': servico,
                'metadata': {},
                'data': data,
                'target': {
                    'entity_id': acao.entidade_id,
                },
            }

        elif isinstance(acao, AcaoChamarNode):
            data = {}
            if acao.expressao is not None:
                partes = acao.servico.split('.', 1)
                nome_servico = partes[1] if len(partes) == 2 else ''  # ex.: 'volume_set' de 'media_player.volume_set'
                data_key = SERVICO_COM_EXPRESSAO.get(nome_servico, 'value') # pega a chave associado ao 'volume_set', 'volume_level', com padrão value
                data[data_key] = acao.expressao.valor
            return {                                 # ex.: CHAMAR media_player.volume_set media_player.tv_da_sala 0.5
                'action': acao.servico,              # 'media_player.volume_set'
                'metadata': {},
                'data': data,                        # 'volume_level: 0.5' (mapeado pelo SERVICO_COM_EXPRESSAO)
                'target': {
                    'entity_id': acao.entidade_id,   # 'media_player.tv_da_sala'
                },
            }

        elif isinstance(acao, BlocoSeNode):
            bloco = {
                'if': self._gerar_condicoes(acao.condicoes),
                'then': [self._gerar_acao(a) for a in acao.acoes_entao],
            }
            if acao.acoes_senao:
                bloco['else'] = [self._gerar_acao(a) for a in acao.acoes_senao]
            return bloco

    # Geração de Automação completa
    def _gerar_automacao(self, auto):
        # Converte uma AutomacaoNode para dict YAML completo.
        automacao = {
            'id': self._gerar_id(),
            'alias': auto.alias,
            'description': '',
            'triggers': [self._gerar_gatilho(g) for g in auto.gatilhos],
            'conditions': self._gerar_condicoes(auto.condicoes),
            'actions': [self._gerar_acao(a) for a in auto.acoes],
            'mode': auto.modo,
        }
        return automacao

    def gerar(self, programa):
        # Gera o YAML completo a partir de um ProgramaNode.
        automacoes = [self._gerar_automacao(a) for a in programa.automacoes]
        return yaml.dump( # Retorna a string YAML formatada.
            automacoes,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )