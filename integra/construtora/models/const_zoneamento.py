# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D


class const_zoneamento(osv.Model):
    _name = 'const.zoneamento'
    _description = u'Zoneamento'
    _rec_name = 'municipio_id'

    _columns = {                
        'municipio_id': fields.many2one('sped.municipio', u'Município', ondelete='restrict'),
        'item_ids': fields.one2many('const.zoneamento.item','zoneamento_id', u'Zoneamentos'),
        'obs': fields.text(u'Observações'),
    }

    
    def create(self, cr, uid, dados, context={}):

        res = super(const_zoneamento, self).create(cr, uid, dados, context=context)            
        
        return res
    
    def write(self, cr, uid, ids, dados, context={}):        
               
        res = super(const_zoneamento, self).write(cr, uid, ids, dados, context=context)            
        
        return res
    
const_zoneamento()

class const_zoneamento_item(osv.Model):
    _name = 'const.zoneamento.item'
    _description = u'Item de zoneamento'
    _rec_name = 'descricao'
    
    _columns = {
        'zoneamento_id': fields.many2one('const.zoneamento', u'Zoneamento', ondelete='cascade'),        
        'municipio_id': fields.many2one('sped.municipio', u'Município', ondelete='restrict'),
        'descricao': fields.char(u'Zoneamento/plano diretor', size=60),
        
        'taxa_ocupacao': fields.float(u'% Taxa de Ocupação base (%)'),
        'taxa_ocupacao_torre': fields.float(u'% Taxa de Ocupação torre (%)'),
        
        'coeficiente_aproveitamento_minino': fields.float(u'Coeficiente de Aproveitamento min.'),  
        'coeficiente_aproveitamento': fields.float(u'Coeficiente de Aproveitamento básc.'),  
        'coeficiente_aproveitamento_max': fields.float(u'Coeficiente de Aproveitamento max.'),  
        
        #'unidade_territorial': fields.char(u'Unidade territoria', size=60), 
        'lote_minimo': fields.float(u'Lote minimo m²'), 
        'lote_maximo': fields.float(u'Lote máximo m²'), 
        'esquina_meio': fields.float(u'Testada min.esquina (m)'), 
        'meio_quadra': fields.float(u'Testada min.meio quadra (m)'), 
        'recuo_minimo': fields.float(u'Recuo Min.(m)'), 
        'recuo_minimo_obs': fields.char(u'Recuo Min Obs.', size=120), 
        'afastamento_minimo': fields.float(u'Afastamento min.(m)'), 
        'indice_verde': fields.float(u'Ìndice verde(%)'), 
        'numero_pavimento': fields.float(u'Número pavimentos'), 
        'numero_pavimento_obs': fields.char(u'Nº pavimentos obs.', size=120), 
        'taxa_permeabilidade': fields.float(u'Taxa de permeabilidade(TP)(%)'), 
        'dime_max_quadra': fields.float(u'Dimensões máximas quadras (m)'), 
        'fator_altura': fields.float(u'Fator altura (m)'), 
        'altura_media_pavimento': fields.float(u'Altura média entre pavimentos (m)'),         
        'numero_max_lote': fields.float(u'Nº Máx de lotes (m)'), 
    
    }

    _defaults = {
                
    }

const_zoneamento_item()
