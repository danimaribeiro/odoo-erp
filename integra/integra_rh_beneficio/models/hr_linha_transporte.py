# -*- coding: utf-8 -*-


from osv import osv, fields
from datetime import datetime, date, timedelta


class hr_linha_transporte(osv.Model):
    _name = 'hr.linha.transporte'
    _description = 'Linhas de Transporte'
    _rec_name = 'codigo'
    _order = 'codigo desc'


    def _codigo(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''
        for registro in self.browse(cursor, user_id, ids):
            txt = '[' + str(registro.id) + ']' + registro.nome
            retorno[registro.id] = txt

        return retorno
    
    _columns = {
        'codigo': fields.function(_codigo, string=u'Código', method=True, type='char', store=True),
        'contract_transporte_id': fields.many2one('hr.contract.linha.transporte', u'Contrato transporte'),        
        'municipio_id': fields.many2one('sped.municipio', u'Município'),
        'nome': fields.char(u'Nome', size=60),
        'valor': fields.float(u'Valor'),
        'data_validade': fields.date(u'Data validade'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),        
        'partner_id': fields.many2one('res.partner', u'Fornecedor'),
    }
    
    _defaults = {
        'data_validade': fields.date.today,         
    }


hr_linha_transporte()

