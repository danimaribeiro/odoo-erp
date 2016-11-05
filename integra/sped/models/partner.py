# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from sped.constante_tributaria import *
from sped.models.trata_nfe import consulta_cadastro_empresa


class res_partner(osv.Model):
    _inherit = 'res.partner'

    _columns = {
        'operacao_fiscal_produto_id': fields.many2one('sped.operacao', u'Operação padrão para produtos'),
        'operacao_fiscal_servico_id': fields.many2one('sped.operacao', u'Operação padrão para serviços'),
        'transportadora_id': fields.many2one('res.partner', u'Transportadora'),
        'regime_tributario': fields.selection(REGIME_TRIBUTARIO, u'Regime tributário'),
    }

    _defaults = {
        'regime_tributario': REGIME_TRIBUTARIO_SIMPLES,
    }

    def consulta_cadastro_sefaz(self, cr, uid, ids, context={}):
        for partner_obj in self.browse(cr, uid, ids, context=context):
            consulta_cadastro_empresa(self, cr, uid, partner_obj)
            
    def consulta_cadastro_sefaz_todos(self, cr, uid, ids, context={}):
        partner_ids = self.pool.get('res.partner').search(cr, 1, [('tipo_pessoa', '=', 'J')], order='razao_social, cnpj_cpf')
        
        falhou = open('/home/integra/consulta_sefaz.txt', 'w')
        
        for partner_obj in self.pool.get('res.partner').browse(cr, 1, partner_ids):
            try:
                consulta_cadastro_empresa(self, cr, uid, partner_obj)
            except:
                linha = partner_obj.cnpj_cpf + u'|'
                linha += partner_obj.name + u'\n'
                falhou.write(linha.encode('utf-8'))
                
                
        

res_partner()
