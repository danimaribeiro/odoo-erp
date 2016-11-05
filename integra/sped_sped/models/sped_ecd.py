# -*- coding: utf-8 -*-

#from __future__ import division, print_function, unicode_literals

from osv import osv, fields
from pybrasil.data import parse_datetime, hoje, agora, UTC, formata_data, mes_passado, primeiro_dia_mes, ultimo_dia_mes
from sped_ecd_gerar import SPEDEcd
import base64
from dateutil.relativedelta import relativedelta
from sped.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D
from pybrasil.inscricao import limpa_formatacao


FINALIDADE = (
    ('0', u'0 - Normal (Início no primeiro dia do ano ou do mês)'),
    ('1', u'1 - Abertura'),
    ('2', u'2 - Resultante de cisão/fusão ou remanescente de cisão, ou realizou incorporação '),
    ('3', u'3 - Início de obrigatoriedade da entrega da ECD no curso do ano calendário'),
)


class sped_sped_ecd(osv.Model):
    _name = 'sped.sped.ecd'
    _description = 'SPED ECD'
    _order = 'data desc'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa', ondelete='restrict'),
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'finalidade': fields.selection(FINALIDADE, u'Finalidade'),        
        'nome_arquivo': fields.char(u'Nome arquivo', size=60),
        'data': fields.datetime(u'Data do Arquivo'),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'), 
        'numero_livro': fields.integer(u'Nº Livro de Escrituração'),              
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sped.sped_ecd', context=c),
        'finalidade': '0',
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        
    }

    def gera_arquivo(self, cr, uid, ids, context={}):
        if not ids:
            return

        for sc_obj in self.browse(cr, uid, ids):
            sped = SPEDEcd()            
            sped.cr = cr
            sped.filial = sc_obj.company_id.partner_id
            sped.data_inicial = parse_datetime(sc_obj.data_inicial).date()
            sped.data_final = parse_datetime(sc_obj.data_final).date()
            sped.finalidade = sc_obj.finalidade
            sped.numero_livro = sc_obj.numero_livro
            
            sped.gera_arquivo()

            dados = {
                'nome_arquivo': 'ECD_' + limpa_formatacao(sc_obj.company_id.cnpj_cpf) + '_' + formata_data(agora()) + '.txt',
                'data': str(UTC.normalize(agora()))[:19],
                'arquivo_texto': sped.arquivo.decode('iso-8859-1').encode('utf-8'),
                'arquivo': base64.encodestring(sped.arquivo),
            }

            
            sc_obj.write(dados)

        return ids

sped_sped_ecd()
