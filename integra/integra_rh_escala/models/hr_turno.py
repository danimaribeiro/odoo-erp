#-*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date
from osv import fields, osv


class hr_turno(osv.Model):
    _name = 'hr.turno'
    _description = u'Turno Contratual'
    _rec_name = 'descricao'   
    
    
    def _descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for turno_obj in self.browse(cr, uid, ids):

            nome =  turno_obj.partner_id.name + '/' 
            nome += turno_obj.department_id.name + '/'
            nome += turno_obj.jornada_id.descricao
            
            res[turno_obj.id] = nome

        return res 
    def _procura_descricao(self, cr, uid, obj, nome_campo, args, context=None):
        texto = args[0][1][2]

        procura = [
            '|', 
            '|',
            ('partner_id.name', 'ilike', texto),
            ('finan_contrato_id', 'ilike', texto),
            ('department_id.name', 'ilike', texto),
            ('jornada_id.name', 'ilike', texto),
        ]

        return procura
    
    _columns = {
        'descricao': fields.function(_descricao, type='char', string=u'Turno', fnct_search=_procura_descricao),
        'partner_id': fields.many2one('res.partner', u'Cliente', ondelete='restrict'),
        'department_id': fields.many2one('hr.department', u'Departamento', ondelete='restrict'),
        'jornada_id': fields.many2one('hr.jornada', u'Jornada de Trabalho', ondelete='restrict'),
        'finan_contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='restrict'),
        'cobranca_extra': fields.boolean(u'Cobrança extra no contrato do cliente?'),
    }

    _defaults = {
    
    }

hr_turno()
