# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

import os
import base64
from decimal import Decimal as D
from pytz import (datetime, timezone, tzinfo, UTC)
from datetime import datetime as datetime_sem_fuso
from dateutil.parser import parse as parse_datetime
from ...base import tira_acentos
from ..participante import (Participante, REGIME_TRIBUTARIO_SIMPLES, REGIME_TRIBUTARIO_SIMPLES_EXCESSO)
from ...ibge import (Municipio, Estado, Pais, MUNICIPIO_ESTADO_NOME, MUNICIPIO_IBGE, MUNICIPIO_SIAFI, ESTADO_IBGE, ESTADO_SIGLA, PAIS_BACEN, PAIS_NOME, PAIS_BRASIL, PAIS_ISO_3166_2, PAIS_ISO_3166_3)
from ...ncm import (Servicos, SERVICOS_CODIGO)
from ...data import mes_por_extenso
from ...valor import formata_valor, valor_por_extenso_unidade


CURDIR = os.path.dirname(os.path.abspath(__file__))
#
# Horário de Brasília
#
HB = timezone('America/Sao_Paulo')


TIPO_RPS_RPS = 0
TIPO_RPS_NF_CONJUGADA = 1
TIPO_RPS_CUPOM_FISCAL = 2

TIPO_RPS = [
    TIPO_RPS_RPS,
    TIPO_RPS_NF_CONJUGADA,
    TIPO_RPS_CUPOM_FISCAL
]


class RPS(object):
    def __init__(self):
        self.numero = 0
        self.serie = ''
        self.fuso_horario = HB
        self.data_hora_emissao = datetime.datetime.now(tz=HB)
        self.tipo = TIPO_RPS_RPS

    @property
    def fuso_horario(self):
        return self._fuso_horario

    @fuso_horario.setter
    def fuso_horario(self, valor):
        if isinstance(valor, tzinfo.tzinfo):
            self._fuso_horario = valor
        elif isinstance(valor, str):
            self.fuso_horario = valor.decode('utf-8')
        elif isinstance(valor, unicode):
            try:
                self.fuso_horario = timezone(valor)
            except:
                pass

    @property
    def numero_formatado(self):
        if self.numero:
            return formata_valor(self.numero, casas_decimais=0)
        else:
            return ''

    @property
    def data_hora_emissao(self):
        return self.fuso_horario.normalize(self._data_hora_emissao)

    @data_hora_emissao.setter
    def data_hora_emissao(self, valor):
        if isinstance(valor, datetime.datetime):
            if not valor.tzinfo:
                valor = self.fuso_horario.localize(valor)

            self._data_hora_emissao = UTC.normalize(valor)

        elif isinstance(valor, datetime_sem_fuso):
            self.data_hora_emissao = self.fuso_horario.localize(valor)

        elif isinstance(valor, (str, unicode)):
            dh = parse_datetime(valor)
            self.data_hora_emissao = dh

    @property
    def data_hora_emissao_formatada(self):
        return self.data_hora_emissao.strftime(b'%d/%m/%Y %H:%M:%S')

    @property
    def data_hora_emissao_iso(self):
        return self.data_hora_emissao.strftime(b'%Y-%m-%dT%H:%M:%S')

    @property
    def data_hora_emissao_iso_utc(self):
        return self.data_hora_emissao.strftime(b'%Y-%m-%dT%H:%M:%S%z')

    @property
    def data_emissao(self):
        return self.data_hora_emissao.date()

    @property
    def data_emissao_formatada(self):
        return self.data_emissao.strftime(b'%d/%m/%Y')

    @property
    def data_emissao_iso(self):
        return self.data_emissao.strftime(b'%Y-%m-%d')

    @property
    def hora_emissao(self):
        return self.data_hora_emissao.date()

    @property
    def hora_emissao_formatada(self):
        return self.hora_emissao.strftime(b'%H:%M:%S')

    @property
    def hora_emissao_iso(self):
        return self.hora_emissao.strftime(b'%H:%M:%S')


NAT_OP_TRIBUTADA_NO_MUNICIPIO = 0
NAT_OP_TRIBUTADA_FORA_MUNICIPIO = 1
NAT_OP_ISENTA = 2
NAT_OP_IMUNE = 3
NAT_OP_SUSPENSA_DECISAO_JUDICIAL = 4
NAT_OP_SUSPENSA_PROCEDIMENTO_ADMINISTRATIVO = 5

REG_ESP_NENHUM = 0
REG_ESP_MICROEMPRESA_MUNICIPAL = 1
REG_ESP_ESTIMATIVA = 2
REG_ESP_SOCIEDADE_PROFISSIONAIS = 3
REG_ESP_COOPERATIVA = 4
REG_ESP_MEI = 5
REG_ESP_ME_EPP = 6


class Prestador(Participante):
    def __init__(self, **kwargs):
        super(Prestador, self).__init__(**kwargs)
        self.incentivador_cultural = False

    @property
    def optante_simples_nacional(self):
        return self.regime_tributario in [REGIME_TRIBUTARIO_SIMPLES, REGIME_TRIBUTARIO_SIMPLES_EXCESSO]


class Tomador(Prestador):
    pass


class _Calcula(object):
    def calcula(self, bc, al):
        bc = D(str(bc))
        al = D(str(al))
        vr = bc * al / D('100.00')
        vr = vr.quantize(D('0.01'))
        return vr


class Retencao(_Calcula):
    def __init__(self):
        self.al_pis = 0
        self.pis = 0
        self.al_cofins = 0
        self.cofins = 0
        self.al_inss = 0
        self.inss = 0
        self.al_ir = 0
        self.ir = 0
        self.al_csll = 0
        self.csll = 0
        self.outras = 0
        self.iss = 0

    @property
    def al_pis_formatado(self):
        return 'PIS (' + formata_valor(self.al_pis) + '%)'

    @property
    def al_cofins_formatado(self):
        return 'COFINS (' + formata_valor(self.al_cofins) + '%)'

    @property
    def al_inss_formatado(self):
        return 'INSS (' + formata_valor(self.al_inss) + '%)'

    @property
    def al_ir_formatado(self):
        return 'IR (' + formata_valor(self.al_ir) + '%)'

    @property
    def al_csll_formatado(self):
        return 'CSLL (' + formata_valor(self.al_csll) + '%)'

    @property
    def pis_formatado(self):
        return formata_valor(self.pis)

    @property
    def cofins_formatado(self):
        return formata_valor(self.cofins)

    @property
    def inss_formatado(self):
        return formata_valor(self.inss)

    @property
    def ir_formatado(self):
        return formata_valor(self.ir)

    @property
    def csll_formatado(self):
        return formata_valor(self.csll)

    @property
    def outras_formatado(self):
        return formata_valor(self.outras)

    @property
    def iss_formatado(self):
        return formata_valor(self.iss)


class Valores(_Calcula):
    def __init__(self):
        self.servico = 0
        self.deducao = 0
        self.desconto_condicionado = 0
        self.bc_iss = 0
        self.al_iss = 0
        self.vr_iss = 0
        self.desconto_incondicionado = 0
        self.justificativa_deducoes = ''
        self.retido = Retencao()
        self.liquido = 0

    @property
    def servico_formatado(self):
        return formata_valor(self.servico)

    @property
    def servico_extenso(self):
        return valor_por_extenso_unidade(self.servico)

    @property
    def deducao_formatado(self):
        return formata_valor(self.deducao)

    @property
    def bc_iss_formatado(self):
        return formata_valor(self.bc_iss)

    @property
    def al_iss_formatado(self):
        return formata_valor(self.al_iss)

    @property
    def vr_iss_formatado(self):
        return formata_valor(self.vr_iss)

    @property
    def desconto_condicionado_formatado(self):
        return formata_valor(self.desconto_condicionado)

    @property
    def desconto_incondicionado_formatado(self):
        return formata_valor(self.desconto_incondicionado)

    @property
    def liquido_formatado(self):
        return formata_valor(self.liquido)

    @property
    def liquido_extenso(self):
        return valor_por_extenso_unidade(self.liquido)


class ItemNFSe(_Calcula):
    def __init__(self):
        super(ItemNFSe, self).__init__()
        self.codigo = ''
        self.descricao = ''
        self.quantidade = 0
        self.vr_unitario = 0
        self.vr_servico = 0
        self.bc_iss = 0
        self.al_iss = 0
        self.vr_iss = 0
        self.vr_deducao = 0
        self.vr_desconto_condicionado = 0
        self.vr_desconto_incondicionado = 0
        self.tributavel = True
        self.iss_retido = False

    @property
    def quantidade_formatado(self):
        return formata_valor(self.quantidade)  # , casas_decimais=4)

    @property
    def vr_unitario_formatado(self):
        return formata_valor(self.vr_unitario)  # , casas_decimais=4)

    @property
    def vr_servico_formatado(self):
        return formata_valor(self.vr_servico)

    @property
    def tributavel_formatado(self):
        if self.tributavel:
            return 'SIM'
        else:
            return 'NÃO'

    @property
    def iss_retido_formatado(self):
        if self.iss_retido:
            return 'SIM'
        else:
            return 'NÃO'


class Parcela(object):
    def __init__(self):
        self.numero = 0
        self.data_vencimento = datetime.datetime.now(tz=HB).date()
        self.valor = D(0)

    @property
    def data_vencimento_formatada(self):
        return self.data_vencimento.strftime(b'%d/%m/%Y')

    @property
    def data_vencimento_iso(self):
        return self.data_vencimento.strftime(b'%Y-%m-%d')


class NFSe(object):
    def __init__(self):
        self.rps = RPS()
        self.nfse_substituida = RPS()
        self.prestador = Prestador()
        self.tomador = Tomador()
        self.intermediario = Participante()
        self.numero = 0
        self.serie = ''
        self.data_hora_emissao = datetime.datetime.now(tz=HB)
        self.data_hora_fato_gerador = datetime.datetime.now(tz=HB)
        self.data_hora_cancelamento = None
        self.itens = []
        self.valor = Valores()
        self.municipio_fato_gerador = None
        self.obs = ''
        self.servico = None
        self.codigo_verificacao = ''
        self.descricao = ''
        self.link_verificacao = ''
        self.natureza_operacao = NAT_OP_TRIBUTADA_NO_MUNICIPIO
        self.cancelada = False
        self.fuso_horario = HB
        self.condicao_pagamento = 'A VISTA'
        self.parcelas = []

    @property
    def fuso_horario(self):
        return self._fuso_horario

    @fuso_horario.setter
    def fuso_horario(self, valor):
        if isinstance(valor, tzinfo.tzinfo):
            self._fuso_horario = valor
            self.rps.fuso_horario = valor
        elif isinstance(valor, str):
            self.fuso_horario = valor.decode('utf-8')
        elif isinstance(valor, unicode):
            try:
                self.fuso_horario = timezone(valor)
            except:
                pass

    @property
    def obs_impressao(self):
        obs = self.obs.replace('\r\n', '\n')
        obs = obs.replace('\n\r', '\n')
        obs = obs.replace('\n', '<br/>')
        return obs

    @property
    def descricao_impressao(self):
        obs = self.descricao.replace('\r\n', '\n')
        obs = obs.replace('\n\r', '\n')
        obs = obs.replace('\n', '<br/>')
        return obs

    @property
    def obs_impressao_curta(self):
        obs = self.obs.replace('\r\n', '\n')
        obs = obs.replace('\n\r', '\n')
        obs = obs.replace('\n', ' | ')
        return obs

    @property
    def descricao_impressao_curta(self):
        obs = self.descricao.replace('\r\n', '\n')
        obs = obs.replace('\n\r', '\n')
        obs = obs.replace('\n', ' | ')
        return obs

    @property
    def servico(self):
        return self._servico

    @servico.setter
    def servico(self, valor):
        if isinstance(valor, Servicos):
            self._servico = valor

        elif isinstance(valor, (str, unicode)):
            if valor in SERVICOS_CODIGO:
                self.servico = SERVICOS_CODIGO[valor]
            elif valor[0] == '0' and valor[1:] in SERVICOS_CODIGO:
                self.servico = SERVICOS_CODIGO[valor[1:]]

        else:
            self._servico = Servicos()

    @property
    def competencia(self):
        return mes_por_extenso(self.data_fato_gerador) + '/' + unicode(self.data_fato_gerador.year)

    @property
    def numero_formatado(self):
        return formata_valor(self.numero, casas_decimais=0)

    @property
    def data_hora_emissao(self):
        return self.fuso_horario.normalize(self._data_hora_emissao)

    @data_hora_emissao.setter
    def data_hora_emissao(self, valor):
        if isinstance(valor, datetime.datetime):
            if not valor.tzinfo:
                valor = self.fuso_horario.localize(valor)

            self._data_hora_emissao = UTC.normalize(valor)

        elif isinstance(valor, datetime_sem_fuso):
            self.data_hora_emissao = self.fuso_horario.localize(valor)

        elif isinstance(valor, (str, unicode)):
            dh = parse_datetime(valor)
            self.data_hora_emissao = dh

    @property
    def data_hora_emissao_formatada(self):
        return self.data_hora_emissao.strftime(b'%d/%m/%Y %H:%M:%S')

    @property
    def data_hora_emissao_iso(self):
        return self.data_hora_emissao.strftime(b'%Y-%m-%dT%H:%M:%S')

    @property
    def data_hora_emissao_iso_utc(self):
        return self.data_hora_emissao.strftime(b'%Y-%m-%dT%H:%M:%S%z')

    @property
    def data_emissao(self):
        return self.data_hora_emissao.date()

    @property
    def data_emissao_formatada(self):
        return self.data_emissao.strftime(b'%d/%m/%Y')

    @property
    def data_emissao_iso(self):
        return self.data_emissao.strftime(b'%Y-%m-%d')

    @property
    def hora_emissao(self):
        return self.data_hora_emissao.date()

    @property
    def hora_emissao_formatada(self):
        return self.hora_emissao.strftime(b'%H:%M:%S')

    @property
    def hora_emissao_iso(self):
        return self.hora_emissao.strftime(b'%H:%M:%S')

    @property
    def data_hora_fato_gerador(self):
        return self.fuso_horario.normalize(self._data_hora_fato_gerador)

    @data_hora_fato_gerador.setter
    def data_hora_fato_gerador(self, valor):
        if isinstance(valor, datetime.datetime):
            if not valor.tzinfo:
                valor = self.fuso_horario.localize(valor)

            self._data_hora_fato_gerador = UTC.normalize(valor)

        elif isinstance(valor, datetime_sem_fuso):
            self.data_hora_fato_gerador = self.fuso_horario.localize(valor)

        elif isinstance(valor, (str, unicode)):
            dh = parse_datetime(valor)
            self.data_hora_fato_gerador = dh

    @property
    def data_hora_fato_gerador_formatada(self):
        return self.data_hora_fato_gerador.strftime(b'%d/%m/%Y %H:%M:%S')

    @property
    def data_hora_fato_gerador_iso(self):
        return self.data_hora_fato_gerador.strftime(b'%Y-%m-%dT%H:%M:%S')

    @property
    def data_hora_fato_gerador_iso_utc(self):
        return self.data_hora_fato_gerador.strftime(b'%Y-%m-%dT%H:%M:%S%z')

    @property
    def data_fato_gerador(self):
        return self.data_hora_fato_gerador.date()

    @property
    def data_fato_gerador_formatada(self):
        return self.data_fato_gerador.strftime(b'%d/%m/%Y')

    @property
    def data_fato_gerador_iso(self):
        return self.data_fato_gerador.strftime(b'%Y-%m-%d')

    @property
    def hora_fato_gerador(self):
        return self.data_hora_fato_gerador.date()

    @property
    def hora_fato_gerador_formatada(self):
        return self.hora_fato_gerador.strftime(b'%H:%M:%S')

    @property
    def hora_fato_gerador_iso(self):
        return self.hora_fato_gerador.strftime(b'%H:%M:%S')

    @property
    def data_hora_cancelamento(self):
        return self.fuso_horario.normalize(self._data_hora_cancelamento)

    @data_hora_cancelamento.setter
    def data_hora_cancelamento(self, valor):
        if isinstance(valor, datetime.datetime):
            if not valor.tzinfo:
                valor = self.fuso_horario.localize(valor)

            self._data_hora_cancelamento = UTC.normalize(valor)

        elif isinstance(valor, datetime_sem_fuso):
            self.data_hora_cancelamento = self.fuso_horario.localize(valor)

        elif isinstance(valor, (str, unicode)):
            dh = parse_datetime(valor)
            self.data_hora_cancelamento = dh

    @property
    def data_hora_cancelamento_formatada(self):
        return self.data_hora_cancelamento.strftime(b'%d/%m/%Y %H:%M:%S')

    @property
    def data_hora_cancelamento_iso(self):
        return self.data_hora_cancelamento.strftime(b'%Y-%m-%dT%H:%M:%S')

    @property
    def data_hora_cancelamento_iso_utc(self):
        return self.data_hora_cancelamento.strftime(b'%Y-%m-%dT%H:%M:%S%z')

    @property
    def data_cancelamento(self):
        return self.data_hora_cancelamento.date()

    @property
    def data_cancelamento_formatada(self):
        return self.data_cancelamento.strftime(b'%d/%m/%Y')

    @property
    def data_cancelamento_iso(self):
        return self.data_cancelamento.strftime(b'%Y-%m-%d')

    @property
    def hora_cancelamento(self):
        return self.data_hora_cancelamento.date()

    @property
    def hora_cancelamento_formatada(self):
        return self.hora_cancelamento.strftime(b'%H:%M:%S')

    @property
    def hora_cancelamento_iso(self):
        return self.hora_cancelamento.strftime(b'%H:%M:%S')

    @property
    def arquivo_logo(self):
        nome_arq = self.prestador.municipio.estado.sigla + '-'
        nome_arq += self.prestador.municipio.nome.replace(' ', '_')
        nome_arq = tira_acentos(nome_arq).lower() + '.jpeg'
        print(nome_arq, 'arquivo_logo')
        arquivo_logo = os.path.join(CURDIR, 'logotipo_prefeitura', nome_arq)
        self._arquivo_logo = arquivo_logo

        if os.path.exists(self._arquivo_logo):
            return self._arquivo_logo

    @property
    def logo(self):
        if os.path.exists(self.arquivo_logo):
            return base64.b64encode(open(self.arquivo_logo, 'rb').read())

    @property
    def prefeitura(self):
        return 'Prefeitura de ' + self.prestador.municipio.nome + ' - ' + self.prestador.municipio.estado.sigla

    @property
    def municipio_fato_gerador(self):
        return self._municipio_fato_gerador

    @municipio_fato_gerador.setter
    def municipio_fato_gerador(self, valor):
        if isinstance(valor, Municipio):
            self._municipio_fato_gerador = valor
            #self.estado = self._municipio_fato_gerador.estado
            #self.pais = self._municipio_fato_gerador.pais

        elif isinstance(valor, (list, tuple)) and len(valor) == 2:
            estado = unicode(valor[0]).upper()
            municipio_fato_gerador = unicode(valor[1]).upper()
            municipio_fato_gerador = tira_acentos(municipio_fato_gerador)
            if estado in MUNICIPIO_ESTADO_NOME:
                if municipio_fato_gerador in MUNICIPIO_ESTADO_NOME[estado]:
                    self.municipio_fato_gerador = MUNICIPIO_ESTADO_NOME[estado][municipio_fato_gerador]

        elif isinstance(valor, (str, unicode)):
            if valor in MUNICIPIO_IBGE:
                self.municipio_fato_gerador = MUNICIPIO_IBGE[valor]
            elif valor in MUNICIPIO_SIAFI:
                self.municipio_fato_gerador = MUNICIPIO_SIAFI[valor]

        else:
            self._municipio_fato_gerador = Municipio()
