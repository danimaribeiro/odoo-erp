# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
import time
from osv import osv, fields
from sped.models.fields import CampoPorcentagem


class sped_familiatributaria(osv.Model):
    _description = u'Família tributária do ICMS'
    _name = 'sped.familiatributaria'
    _columns = {
        'descricao': fields.char(u'Descrição', size=60, required=True),
        'familiatributariaitem_ids': fields.one2many('sped.familiatributariaitem', 'familiatributaria_id', u'Ítens da família tributária'),
        'familiatributariaitemservico_ids': fields.one2many('sped.familiatributariaitemservico', 'familiatributaria_id', u'Ítens da família tributária'),
        'al_previdencia': CampoPorcentagem(u'Alíquota do INSS para retenção'),
        'usa_mva_ajustado': fields.boolean(u'Usa MVA ajustado?'),
        'familiatributariaestado_ids': fields.one2many('sped.familiatributariaestado', 'familiatributaria_id', u'Estados de validade da família tributária'),
        #'ncm_ids': fields.one2many('sped.ncm', 'familiatributaria_id', u'NCMs'),
        'ncm_ids': fields.many2many('sped.ncm', 'sped_ncm_familiatributaria', 'familiatributaria_id', 'ncm_id', u'NCMs'),
        'product_ids': fields.one2many('product.product', 'familiatributaria_id', u'Produtos'),
    }

    _rec_name = 'descricao'
    _order = 'descricao'

    _sql_constraints = [
        ('descricao_unique', 'unique (descricao)', u'A descrição não pode se repetir!'),
    ]

    _defaults = {
        'usa_mva_ajustado': False,
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}

        default.update({
            'descricao': '',
            'ncm_ids': False,
            'product_ids': False,
        })

        res = super(osv.Model, self).copy(cr, uid, id, default, context=context)

        return res


sped_familiatributaria()


class sped_familiatributariaitem(osv.Model):
    _description = u'Item da família tributária do ICMS'
    _name = 'sped.familiatributariaitem'
    _columns = {
        'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família Tributária', required=True, ondelete='cascade', select=True),
        'estado_origem_id': fields.many2one('sped.estado', u'Estado de origem', required=True, select=True),
        'estado_destino_id': fields.many2one('sped.estado', u'Estado de destino', required=True, select=True),
        'data_inicio': fields.date(u'Data de início da validade', required=True, select=True),
        'al_icms_proprio_id': fields.many2one('sped.aliquotaicmsproprio', u'ICMS próprio', required=True, select=True),
        'al_icms_st_id': fields.many2one('sped.aliquotaicmsst', u'ICMS retido na operação por substituição tributária', select=True),
        'al_icms_st_retido_id': fields.many2one('sped.aliquotaicmsst', u'ICMS retido antecipadamente por substituição tributária', select=True),
        'infadic': fields.text(u'Informações adicionais'),
    }

    _defaults = {
        'data_inicio': lambda *a: time.strftime('%Y-%m-%d'),
    }

    _rec_name = 'familiatributaria_id'
    #_order = 'descricao'

    _sql_constraints = [
        ('familiatributaria_estado_origem_estado_destino_data_inicio', 'unique (familiatributaria_id, estado_origem_id, estado_destino_id, data_inicio)', u'O item não pode se repetir!'),
    ]

sped_familiatributariaitem()


class sped_familiatributariaitemservico(osv.Model):
    _description = u'Item da família tributária do ISS'
    _name = 'sped.familiatributariaitemservico'
    _columns = {
        'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família Tributária', required=True, ondelete='cascade', select=True),
        'municipio_id': fields.many2one('sped.municipio', u'Município', required=True, select=True),
        'al_iss_id': fields.many2one('sped.aliquotaiss', u'ISS', required=True, select=True),
    }

    _rec_name = 'familiatributaria_id'
    #_order = 'descricao'

    _sql_constraints = [
        ('familiatributaria_municipio', 'unique (familiatributaria_id, municipio_id)', u'O item não pode se repetir!'),
    ]

sped_familiatributariaitemservico()


class sped_familiatributariaestado(osv.Model):
    _description = u'Estados da família tributária'
    _name = 'sped.familiatributariaestado'
    _columns = {
        'familiatributaria_id': fields.many2one('sped.familiatributaria', u'Família Tributária', required=True, ondelete='cascade', select=True),
        'estado_id': fields.many2one('sped.estado', u'Estado', required=True, select=True),
    }

    _rec_name = 'estado_id'
    #_order = 'descricao'

    _sql_constraints = [
        ('familiatributaria_estado', 'unique (familiatributaria_id, estado_id)', u'O item não pode se repetir!'),
    ]

sped_familiatributariaestado()