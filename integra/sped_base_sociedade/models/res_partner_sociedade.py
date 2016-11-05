# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D

class res_partner_sociedade(osv.Model):
    _description = u'Sociedade'
    _name = 'res.partner.sociedade'


    _columns = {
        'partner_id': fields.many2one('res.partner', u'Cliente/Fornecedor', on_delete='cascade'),
        'socio_id': fields.many2one('res.partner', u'Sócio', on_delete='cascade'),
        'percentual': fields.float(u'Percentual'),        
        }

    _defaults = {
        'percentual': 0,   
    }

res_partner_sociedade()
    

class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'


    _columns = {
        'sociedade_ids': fields.one2many('res.partner.sociedade','partner_id', u'Sociedade'),        
    } 
    
    def verifica_percentual(self, cr, uid, ids, vals, context=None):
        if 'sociedade_ids' not in vals or not vals['sociedade_ids']:
            return
        
        sociedades = vals['sociedade_ids']
        sociedade_alteradas = []        

        total_percentual = D('0')
        
        for operacao, socio_id, valores in sociedades:
            #
            # Cada lanc_item tem o seguinte formato
            # [operacao, id_original, valores_dos_campos]
            #
            # operacao pode ser:
            # 0 - criar novo registro (no caso aqui, vai ser ignorado)
            # 1 - alterar o registro
            # 2 - excluir o registro (também vai ser ignorado)
            # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
            # 4 - vincular a um registro existente
            # 5 - excluiu todos a vai incluir todos de novo

            print(operacao, 'operacao', socio_id, valores)
            
            if operacao == 0:
                total_percentual += D(valores.get('percentual', 0) or 0)                                  
                
            if operacao == 5:
                excluido_ids = self.pool.get('res.partner.sociedade').search(cr, uid, [('partner_id', 'in', ids)])
                sociedade_alteradas += excluido_ids

            if operacao == 2:
                sociedade_alteradas += [socio_id]
        
            if operacao == 1 and 'percentual' in valores:
                sociedade_alteradas += [socio_id]
                total_percentual += D(valores.get('percentual', 0) or 0)                               

        #
        # Ajusta com os possíveis não alterados
        #
        
        sociedades_ids = []
        if ids and ids[0]:
            sociedade_pool = self.pool.get('res.partner.sociedade')
            sociedades_ids = sociedade_pool.search(cr, uid, [('partner_id', '=', ids[0]), ('id', 'not in', sociedade_alteradas)])

            for sociedade_obj in sociedade_pool.browse(cr, uid, sociedades_ids):
                total_percentual += D(str(sociedade_obj.percentual or 0))
        print(total_percentual)                        
        if total_percentual != 100 and total_percentual != 0:
            raise osv.except_osv(u'Erro!', u'A soma dos percentuais dos sócios deve ser igual a 100%')
    
    def create(self, cr, uid, vals, context={}):
        self.verifica_percentual(cr, uid, [], vals)
        
        return super(res_partner, self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context={}):
        self.verifica_percentual(cr, uid, ids, vals)
         
        return super(res_partner, self).write(cr, uid, ids, vals, context)
        
        
        
res_partner()

