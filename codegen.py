# codegen.py
# Gerador de Código Intermediário: AST -> YAML (Home Assistant)
# Traduz a árvore sintática para automações YAML compatíveis com Home Assistant.

import yaml
import uuid
import time

from ast_nodes import (
    ProgramaNode, AutomacaoNode,
    GatilhoEstadoNode, GatilhoHorarioNode,
    CondicaoNode,
    AcaoLigarNode, AcaoDesligarNode, AcaoEsperarNode,
    AcaoNotificarNode, AcaoDefinirNode, AcaoChamarNode,
    BlocoSeNode,
)


class GeradorYAML:
    """
    Percorre a AST e gera uma lista de automações no formato YAML
    compatível com o Home Assistant.
    """

    def __init__(self):
        self._id_counter = int(time.time() * 1000)

    def _gerar_id(self):
        """Gera um ID numérico único para a automação."""
        self._id_counter += 1
        return str(self._id_counter)

    def _extrair_dominio(self, entidade_id):
        """Extrai o domínio de um entity_id."""
        partes = entidade_id.split('.', 1)
        return partes[0] if len(partes) == 2 else 'switch'

    # ============================================================
    # Geração de Gatilhos (Triggers)
    # ============================================================

    def _gerar_gatilho(self, gatilho):
        """Converte um GatilhoNode para dict YAML de trigger."""
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

    # ============================================================
    # Geração de Condições
    # ============================================================

    def _gerar_condicao(self, condicao):
        """Converte uma CondicaoNode para dict YAML de condition."""
        if condicao is None:
            return []

        # Se o operador é == ou !=, usamos condition: state
        if condicao.operador in ('==', '!='):
            cond = {
                'condition': 'state',
                'entity_id': condicao.entidade_id,
                'state': str(condicao.expressao.valor),
            }
            # Para !=, não há suporte direto - usamos template
            if condicao.operador == '!=':
                cond = {
                    'condition': 'template',
                    'value_template': (
                        f"{{{{ states('{condicao.entidade_id}') "
                        f"!= '{condicao.expressao.valor}' }}}}"
                    ),
                }
            return [cond]

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

        return [cond]

    # ============================================================
    # Geração de Ações
    # ============================================================

    def _gerar_acao(self, acao):
        """Converte um AcaoNode para dict YAML de action."""

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
            segs = acao.segundos
            horas = int(segs // 3600)
            segs_rest = segs % 3600
            minutos = int(segs_rest // 60)
            segundos = int(segs_rest % 60)
            milissegundos = int(round((segs - int(segs)) * 1000))

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
            return {
                'action': acao.servico,
                'metadata': {},
                'data': {},
                'target': {
                    'entity_id': acao.entidade_id,
                },
            }

        elif isinstance(acao, BlocoSeNode):
            bloco = {
                'if': self._gerar_condicao(acao.condicao),
                'then': [self._gerar_acao(a) for a in acao.acoes_entao],
            }
            if acao.acoes_senao:
                bloco['else'] = [self._gerar_acao(a) for a in acao.acoes_senao]
            return bloco

    # ============================================================
    # Geração de Automação completa
    # ============================================================

    def _gerar_automacao(self, auto):
        """Converte uma AutomacaoNode para dict YAML completo."""
        automacao = {
            'id': self._gerar_id(),
            'alias': auto.alias,
            'description': '',
            'triggers': [self._gerar_gatilho(g) for g in auto.gatilhos],
            'conditions': self._gerar_condicao(auto.condicao),
            'actions': [self._gerar_acao(a) for a in auto.acoes],
            'mode': 'single',
        }
        return automacao

    # ============================================================
    # Ponto de entrada: gera YAML a partir de ProgramaNode
    # ============================================================

    def gerar(self, programa):
        """
        Gera o YAML completo a partir de um ProgramaNode.
        Retorna a string YAML formatada.
        """
        automacoes = [self._gerar_automacao(a) for a in programa.automacoes]
        return yaml.dump(
            automacoes,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )


# ============================================================
# Teste Local
# ============================================================
if __name__ == '__main__':
    from ast_nodes import ExpressaoNode

    # Construir AST de teste manualmente
    programa = ProgramaNode(automacoes=[
        AutomacaoNode(
            alias="Corredor - movimento",
            gatilhos=[
                GatilhoEstadoNode("sensor.corredor_motion", ExpressaoNode('STRING', 'on'), 1),
                GatilhoEstadoNode("binary_sensor.porta", ExpressaoNode('STRING', 'on'), 2),
            ],
            condicao=CondicaoNode("sensor.temperatura", ">", ExpressaoNode('NUMERO', 25), 3),
            acoes=[
                AcaoLigarNode("light.corredor", 4),
                AcaoEsperarNode("2min", 120.0, 5),
                AcaoDesligarNode("light.corredor", 6),
                AcaoNotificarNode("Luz desligada!", "mobile_app_zfold4", 7),
                BlocoSeNode(
                    condicao=CondicaoNode("switch.modo_noturno", "==", ExpressaoNode('STRING', 'off'), 8),
                    acoes_entao=[AcaoChamarNode("light.turn_on", "light.led_noturno", 9)],
                    acoes_senao=[AcaoDesligarNode("light.led_noturno", 10)],
                    linha=8,
                ),
            ],
            linha=1,
        ),
        AutomacaoNode(
            alias="Sala - desligar LED",
            gatilhos=[GatilhoHorarioNode("05:00:00", 12)],
            condicao=None,
            acoes=[AcaoDesligarNode("light.led_sanca", 13)],
            linha=12,
        ),
    ])

    gerador = GeradorYAML()
    yaml_saida = gerador.gerar(programa)
    print("=" * 60)
    print("  YAML GERADO")
    print("=" * 60)
    print(yaml_saida)
