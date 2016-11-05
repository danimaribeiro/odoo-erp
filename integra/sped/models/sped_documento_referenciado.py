# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from sped.constante_tributaria import *


class sped_documentoreferenciado(orm.Model):
    _description = u'Documentos fiscais referenciados por documentos SPED'
    _name = 'sped.documentoreferenciado'

    def documentoreferenciado_on_change(self):
        pass

    _columns = {
        'documento_id': fields.many2one('sped.documento', u'Documento', required=True, ondelete='cascade'),
        'company_id': fields.related('documento_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa'),
        'company_cnpj_cpf': fields.related('company_id', 'cnpj_cpf', type='char', string=u'CNJP/CPF da empresa'),
        'documento_data_emissao': fields.related('documento_id', 'data_emissao', type='datetime', string=u'Data de emissão'),
        'documentoreferenciado_id': fields.many2one('sped.documento', u'Documento', domain=[('modelo', 'in', MODELO_FISCAL_REFERENCIADO_FILTRO)]),
        'partner_id': fields.many2one('res.partner', u'Destinatário/Remetente'),
        'modelo': fields.selection(MODELO_FISCAL_REFERENCIADO, u'Modelo'),
        'serie': fields.char(u'Série', size=3),
        'numero': fields.integer(u'Número'),
        'data_emissao': fields.datetime(u'Data de emissão'),
        'chave': fields.char(u'Chave NF-e/CT-e', size=44),
        'numero_ecf': fields.char(u'Número do ECF', size=3),
        'numero_coo': fields.integer(u'Número do Contador de Ordem da Operação'),
    }

    _defaults = {
        'modelo': '55',
        'chave': '',
        'numero_ecf': '',
        'numero_coo': '',
    }
    
            
    def onchange_documentoreferenciado(self, cr, uid, ids, documentoreferenciado_id):
        res = {}
        valores = {}
        res['value'] = valores
        
        
        if not documentoreferenciado_id:
            return {}
        
        documento_item = self.pool.get('sped.documento').browse(cr, uid, documentoreferenciado_id)

        valores = {'partner_id': documento_item.partner_id.id or '',
                   'data_emissao': documento_item.data_emissao or '',                
                   'chave': documento_item.chave or '',
                   'numero': documento_item.numero or '',
                   'serie': documento_item.serie or '',
                   'modelo': documento_item.modelo or '',                  
                   }
        res['value'] = valores

        return res 


sped_documentoreferenciado()
