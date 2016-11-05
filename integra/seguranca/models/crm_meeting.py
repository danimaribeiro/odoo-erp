# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
import os
from osv import orm, fields, osv
from datetime import datetime, timedelta, date
from dateutil import parser
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from copy import copy
import base64
from finan.wizard.finan_relatorio import Report


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class crm_meeting(orm.Model):
    _name = 'crm.meeting'
    _inherit = 'crm.meeting'
    #_rec_name = 'descricao'

    #def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        #retorno = {}

        #for registro in self.browse(cursor, 1, ids):
            #if registro.tipo_instalacao or registro.sale_order_id:
                #txt = TIPO_INSTALACAO_DICT[registro.tipo_instalacao or 'I']
                #txt += ' - '
                #if registro.sale_order_id:
                    #txt += registro.sale_order_id.name
                #retorno[registro.id] = txt

            #else:
                #retorno[registro.id] = registro.name

        #return retorno

    #def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        #texto = args[0][2]

        #procura = ['|',
            #('name', 'ilike', texto),
            #'|',
            #('tipo_instalacao', 'ilike', texto),
            #('sale_order_id', 'ilike', texto)
        #]

        #return procura

    _columns = {
        'sale_order_id': fields.many2one('sale.order', u'Proposta/OS', ondelete='restrict'),
        #'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', size=60, fnct_search=_procura_descricao),
        'servico_ids': fields.one2many('crm.meeting.servico', 'meeting_id', u'Serviços'),
    }

    def create(self, cr, uid, dados, context={}):
        if ('name' not in dados) and ('sale_order_id' in dados):
            sale_obj = self.pool.get('sale.order').browse(cr, uid, dados['sale_order_id'], context=context)

            nome = sale_obj.tipo_os_id.nome
            dados['name'] = nome

        return super(crm_meeting, self).create(cr, uid, dados, context=context)


crm_meeting()
