# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from copy import copy
from pybrasil.valor.decimal import Decimal as D
from sped.constante_tributaria import *

VIA_TRANSPORTE_INTER = (
    ('1', u'Marítima'),
    ('2',  u'Fluvial'),
    ('3', u'Lacustre'),
    ('4', u'Aérea'),
    ('5', u'Postal'),
    ('6', u'Ferroviária'),
    ('7', u'Rodoviária'),
    ('8', u'Conduto / Rede Transmissão'),
    ('9', u'Meios Próprios'),
    ('10', u'Entrada / Saída ficta'),
    ('11', u'Courier'),
    ('12', u'Handcarry. (NT 2013/005 v 1.10).'),
)

FORMA_IMPORTACAO = (
    ('1', u'Importação por conta própria'),
    ('2', u'Importação por conta e ordem'),
    ('3', u'Importação por encomenda'),                            
)


class sped_declaracao_importacao(osv.Model):
    _name = 'sped.declaracao.importacao'
    _description = u'SPED Declaração Importação'

    _columns = {
            'numero_documento': fields.char(u'Nº documento Importação', size=12),
            'data_registro': fields.datetime(u'Data registro'),
            'local_desembaraco': fields.char(u'Local Desembaraço', size=60),             
            'uf_desembaraco': fields.many2one('sped.estado', u'UF Desembaraço Aduaneiro'),
            'data_desembaraco': fields.datetime(u'Data desembaraço aduaneiro'),
            'via_trans_internacional': fields.selection(VIA_TRANSPORTE_INTER, u'Via transporte internacional', select=True),
            'vr_afrmm': fields.float(u'Valor da AFRMM'),
            'forma_importacao': fields.selection(FORMA_IMPORTACAO, u'Forma de importação', select=True),
            'partner_id': fields.many2one('res.partner', u'Adquirente/encomendante'),
            'uf_adquirente': fields.char(u'UF adquirente', size=2),            
            'documentoitem_id': fields.many2one('sped.documentoitem', u'Documento Item'),
            'declaracao_adicao_ids': fields.one2many('sped.declaracao.importacao.adicao', 'declaracao_id', u'Adições'),     
    }
    
sped_declaracao_importacao()

class sped_declaracao_importacao_adicao(osv.Model):
    _name = 'sped.declaracao.importacao.adicao'
    _description = u'SPED Declaração Importação adicões'
    

    _columns = {
           'numero_adicao': fields.integer(u'Nº da adição'),
           'sequencial': fields.integer(u'Sequencial'),           
           'vr_desconto': fields.float(u'Valor desconto'),
           'numero_drawback': fields.integer(u'Nº Drawback'), 
           'declaracao_id': fields.many2one('sped.declaracao.importacao', u'Declaração importação') 
    }

    

sped_declaracao_importacao_adicao()
