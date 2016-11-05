# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from decimal import Decimal as D
from sped.models.fields import *
from pybrasil.data import parse_datetime, idade_meses, hoje, primeiro_dia_mes, ultimo_dia_mes


class finan_controle_cobranca(osv.Model):
    _description = u'Controle de Cobrança'
    _name = 'finan.controle.cobranca'

    def _get_raiz_cnpj(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for obj in self.browse(cr, uid, ids):
            if obj.company_id:
                if obj.company_id.partner_id.cnpj_cpf:
                    res[obj.id] = obj.company_id.partner_id.cnpj_cpf[:10]
            else:
                res[obj.id] = ''

        return res
    
    def _get_soma_total(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for cobranca_obj in self.browse(cr, uid, ids):
                        
            sql = """
                select
                    sum(valor_saldo)
                from finan_lancamento l
                    join finan_cobranca_itens ci on ci.lancamento_id = l.id
                where 
                    ci.cobranca_id = """ + str(cobranca_obj.id)
 
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados):
                res[cobranca_obj.id] = D(dados[0][0] or 0)
            else:
                res[cobranca_obj.id] = 0    
                
        return res


    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa', ondelete='restrict'),
        'raiz_cnpj': fields.function(_get_raiz_cnpj, type='char', string=u'Raiz do CNPJ', size=10, store=True, method=True),
        'partner_id': fields.many2one('res.partner', u'Cliente', ondelete='restrict'),        
        'data': fields.datetime(u'Data e hora'),      
        'lancamento_ids': fields.many2many('finan.lancamento', 'finan_cobranca_itens', 'cobranca_id', 'lancamento_id', string=u'Títulos a Cobrar', ondelete='cascade', domain=[('tipo', '=', 'R'), ('provisionado', '=', False),('situacao','in',('Vencido','Vence hoje','A vencer'))]),
        'vr_total': fields.function(_get_soma_total, type='float', store=True, digits=(18, 2), string=u'Valor Total'),                
        'create_uid': fields.many2one('res.users', u'Usuário'), 
        'obs': fields.text(u'Observação'),
        'create_uid': fields.many2one('res.users', u'Criado por', select=True, ondelete='restrict'),
        'cobrador_id': fields.many2one('res.users', u'Cobrador', select=True, ondelete='restrict'),       
        'data_agendamento': fields.date(u'Data Agendamento'),       
    }

    _defaults = {               
        'data':  fields.datetime.now,                      
    }

      

finan_controle_cobranca()



