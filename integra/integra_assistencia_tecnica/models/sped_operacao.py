# -*- coding: utf-8 -*-


from osv import orm, fields, osv



class sped_operacao(osv.Model):
    _name = 'sped.operacao'
    _inherit = 'sped.operacao'

    _columns = {
        'ordem_servico_etapa_id': fields.many2one('ordem.servico.etapa', u'Etapa'),
        
    }

 
sped_operacao()

