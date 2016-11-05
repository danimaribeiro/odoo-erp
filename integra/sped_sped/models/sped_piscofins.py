# -*- coding: utf-8 -*-

#from __future__ import division, print_function, unicode_literals

from osv import osv, fields
from pybrasil.data import parse_datetime, hoje, agora, UTC
from sped_piscofins_gerar import SPEDContribuicoes
import base64
from pybrasil.valor.decimal import Decimal as D


class sped_sped_piscofins(osv.Model):
    _name = 'sped.sped_piscofins'
    _description = 'SPED PIS-COFINS'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'finalidade': fields.char(u'Finalidade', size=1),
        'perfil': fields.char(u'Perfil', size=1),
        'tipo_atividade': fields.char(u'Atividade', size=1),

        'nome_arquivo': fields.char(u'Nome arquivo', size=60),
        'data': fields.datetime(u'Data do Arquivo'),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),
    }

    _defaults = {
        'finalidade': '0',
        'perfil': 'A',
        'tipo_atividade': '0',
    }

    def gera_arquivo(self, cr, uid, ids, context={}):
        if not ids:
            return

        for sf_obj in self.browse(cr, uid, ids):
            sped = SPEDContribuicoes()
            sped.cr = cr
            sped.filial = sf_obj.company_id.partner_id
            sped.al_pis = D(sf_obj.company_id.al_pis_cofins_id.al_pis)
            sped.data_inicial = parse_datetime(sf_obj.data_inicial).date()
            sped.data_final = parse_datetime(sf_obj.data_final).date()
            sped.finalidade = sf_obj.finalidade
            sped.perfil = sf_obj.perfil
            sped.tipo_atividade = sf_obj.tipo_atividade
            sped.gera_arquivo()

            dados = {
                'nome_arquivo': 'sped_contribuicoes.txt',
                'data': str(UTC.normalize(agora()))[:19],
                'arquivo_texto': sped.arquivo.decode('iso-8859-1').encode('utf-8'),
                'arquivo': base64.encodestring(sped.arquivo),
            }

            sf_obj.write(dados)

        return ids


sped_sped_piscofins()
