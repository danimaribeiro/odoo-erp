# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from ..inscricao import (valida_cnpj, valida_cpf, formata_cnpj, formata_cpf, limpa_formatacao)
from .pessoa import Beneficiario, Funcionario




class Holerite(object):
    def __init__(self, **kwargs):        
        self.tipo_comprovante = ''
        self.mes_referencia = ''
        self.data_liberacao = None        
        self.funcionario = Funcionario()
        self.holerite_informacao = Holerite_Informacao()
        self.holerite_detalhe = []
        self.sequencia_arquivo = 0
        

class Holerite_Detalhe(object):
    def __init__(self, **kwargs):
        self.codigo_lancamento = ''
        self.descricao_lancamento = ''
        self.valor_lancamento = 0
        self.identificador_lancamento = 0
        self.sequencia_arquivo = 0

class Holerite_Informacao(object):
    def __init__(self, **kwargs):        
        self.data_pagamemto = None        
        self.qtd_dep_irrf = 0
        self.qtd_dep_salario_familia = 0
        self.qtd_horas_trabalhadas = 0
        self.vr_salario_base = 0
        self.qtd_falta_ferias = 0
        self.data_inicio_periodo_aquisitivo = None
        self.data_fim_periodo_aquisitivo = None
        self.data_inicio_periodo_gozo = None
        self.data_fim_periodo_gozo = None
        self.vr_base_inss = 0
        self.vr_base_inss_13 = 0
        self.vr_base_irrf_salario = 0
        self.vr_base_irrf_13 = 0
        self.vr_base_irrf_ferias = 0
        self.vr_base_irrf_ppr = 0
        self.vr_base_fgts = 0
        self.vr_fgts = 0        
        self.sequencia_arquivo = 0