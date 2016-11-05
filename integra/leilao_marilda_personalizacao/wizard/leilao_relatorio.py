# -*- encoding: utf-8 -*-

import os
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, formata_data
import base64
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado
from relatorio import *
from finan.wizard.finan_relatorio import Report
import csv
from pybrasil.base import DicionarioBrasil


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')



class leilao_relatorio(osv.Model):
    _name = 'leilao.relatorio'
    _description = 'leilao.relatorio'

    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'data_hora_id': fields.many2one('data.hora.leilao', u'Horario'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 120, readonly=True),
        'arquivo_csv': fields.binary(u'Arquivo CSV', readonly=True),
    }

    _defaults = {
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
    }

    def gera_fechamento_leilao(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for rel_obj in self.browse(cr, uid, ids):
            if rel_obj.data_hora_id.id:
                data = rel_obj.data_hora_id.id
            else:
                data = '%'
            data_inicial = parse_datetime(rel_obj.data_inicial).date()
            data_final = parse_datetime(rel_obj.data_final).date()

            rel = Report('Relatório de Fechamento Leilão', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'fechamento_leilao.jrxml')
            rel.parametros['DATA'] = str(data)
            rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
            rel.parametros['DATA_FINAL'] = str(data_final)[:10]

            pdf, formato = rel.execute()

            dados = {
                'nome': u'fechamento_leialo_' + str(data_final) + '_.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            rel_obj.write(dados)
            return True

leilao_relatorio()

