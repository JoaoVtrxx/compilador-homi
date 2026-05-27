# ast_nodes.py
# Definição dos nós da Árvore Sintática Abstrata (AST) para a linguagem Homi.
# Cada classe corresponde a um não-terminal da GLC.

from dataclasses import dataclass, field
from typing import List, Optional, Union


# ============================================================
# Expressões (folhas da árvore)
# ============================================================

@dataclass
class ExpressaoNode:
    """Representa um valor literal: NUMERO ou STRING."""
    tipo: str          # 'NUMERO' ou 'STRING'
    valor: Union[int, float, str]
    linha: int = 0


# ============================================================
# Gatilhos (triggers)
# ============================================================

@dataclass
class GatilhoEstadoNode:
    """Gatilho de mudança de estado: ENTIDADE_ID MUDAR PARA expressao"""
    entidade_id: str
    expressao: ExpressaoNode
    linha: int = 0


@dataclass
class GatilhoHorarioNode:
    """Gatilho de horário: HORARIO STRING"""
    horario: str       # ex: "05:00:00"
    linha: int = 0


# ============================================================
# Condições
# ============================================================

@dataclass
class CondicaoNode:
    """Condição: ENTIDADE_ID operador expressao"""
    entidade_id: str
    operador: str      # '>', '<', '==', '>=', '<=', '!='
    expressao: ExpressaoNode
    linha: int = 0


# ============================================================
# Ações
# ============================================================

@dataclass
class AcaoLigarNode:
    """Ação: LIGAR ENTIDADE_ID"""
    entidade_id: str
    linha: int = 0


@dataclass
class AcaoDesligarNode:
    """Ação: DESLIGAR ENTIDADE_ID"""
    entidade_id: str
    linha: int = 0


@dataclass
class AcaoEsperarNode:
    """Ação: ESPERAR TEMPO"""
    tempo_raw: str     # ex: "10s", "5min", "1h", "500ms"
    segundos: float    # valor convertido para segundos
    linha: int = 0


@dataclass
class AcaoNotificarNode:
    """Ação: NOTIFICAR STRING PARA STRING"""
    mensagem: str
    destino: str       # ex: "mobile_app_zfold4"
    linha: int = 0


@dataclass
class AcaoDefinirNode:
    """Ação: DEFINIR ENTIDADE_ID expressao"""
    entidade_id: str
    expressao: ExpressaoNode
    linha: int = 0


@dataclass
class AcaoChamarNode:
    """Ação: CHAMAR ENTIDADE_ID(servico) ENTIDADE_ID(alvo)"""
    servico: str       # ex: "light.turn_on"
    entidade_id: str   # ex: "light.luz_sala"
    linha: int = 0


@dataclass
class BlocoSeNode:
    """Bloco condicional dentro de ações: SE condicao ENTAO acoes [SENAO acoes] FIM"""
    condicao: CondicaoNode
    acoes_entao: list       # List[AcaoNode]
    acoes_senao: list       # List[AcaoNode] ou lista vazia
    linha: int = 0


# Tipo união para qualquer ação
AcaoNode = Union[
    AcaoLigarNode,
    AcaoDesligarNode,
    AcaoEsperarNode,
    AcaoNotificarNode,
    AcaoDefinirNode,
    AcaoChamarNode,
    BlocoSeNode,
]

# Tipo união para qualquer gatilho
GatilhoNode = Union[GatilhoEstadoNode, GatilhoHorarioNode]


# ============================================================
# Automação (nó principal)
# ============================================================

@dataclass
class AutomacaoNode:
    """Uma automação completa."""
    alias: str                                 # Nome da automação (STRING)
    gatilhos: List[GatilhoNode]                # Lista de gatilhos (1 ou mais)
    condicao: Optional[CondicaoNode]           # Condição opcional
    acoes: List[AcaoNode]                      # Lista de ações (1 ou mais)
    linha: int = 0


# ============================================================
# Programa (raiz da AST)
# ============================================================

@dataclass
class ProgramaNode:
    """Nó raiz: lista de automações."""
    automacoes: List[AutomacaoNode] = field(default_factory=list)
