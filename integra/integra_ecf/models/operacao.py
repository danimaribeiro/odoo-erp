 #voip.agiltec.info-*- coding: utf-8 -*-

from osv import osv, fields



class sped_operacao(osv.Model):
    _description = u'Operações fiscais'
    _name = 'sped.operacao'
    _inherit = 'sped.operacao'

    _columns = {
        'modelo_partida_dobrada_id': fields.many2one('sped.modelo_partida_dobrada', u'Modelo de Partidas Dobradas'),
    }


sped_operacao()
