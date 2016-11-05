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
from pybrasil.data import hoje


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

    def _situacao(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for agenda_obj in self.browse(cr, uid, ids, context=context):
            if agenda_obj.state == 'done':
                res[agenda_obj.id] = u'Executada'
            elif agenda_obj.state == 'cancel':
                res[agenda_obj.id] = u'Cancelada'
            else:
                if agenda_obj.date[:10] < str(hoje()):
                    res[agenda_obj.id] = u'Em atraso'
                else:
                    res[agenda_obj.id] = u'A executar'
        return res

    def _descricao_agenda(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for agenda_obj in self.browse(cr, uid, ids, context=context):
            if nome_campo == 'descricao_agenda_situacao':
                texto = u'[' + agenda_obj.user_id.name.strip() + u']<br/><br/>'

            else:
                if agenda_obj.situacao == 'Em atraso':
                    texto = u'<span style="background-color: #ff0000;">['
                elif agenda_obj.situacao == 'Executada':
                    texto = u'<span style="background-color: #0066ff;">['
                elif agenda_obj.situacao == 'Cancelada':
                    texto = u'<span style="background-color: #333333;">['
                elif agenda_obj.situacao == 'A executar':
                    texto = u'<span style="background-color: #009933;">['

                texto += agenda_obj.situacao + u']</span><br/><br/>'

            if agenda_obj.sale_order_id:
                texto += u'OS nº ' + agenda_obj.sale_order_id.name.strip() + u'<br/><br/>'
                texto += agenda_obj.sale_order_id.partner_id.name.strip()

            res[agenda_obj.id] = texto

        return res

    _columns = {
        'sale_order_id': fields.many2one('sale.order', u'Proposta/OS', ondelete='restrict'),
        #'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', size=60, fnct_search=_procura_descricao),
        'servico_ids': fields.one2many('crm.meeting.servico', 'meeting_id', u'Serviços'),
        'user_id': fields.many2one('res.users', u'Técnico', states={'done': [('readonly', True)]}),
        'situacao': fields.function(_situacao, type='char', size=20, string=u'Situação', store=False),

        'descricao_agenda_situacao': fields.function(_descricao_agenda, type='char', size=128, string=u'Descrição na agenda por situação'),
        'descricao_agenda_tecnico': fields.function(_descricao_agenda, type='char', size=128, string=u'Descrição na agenda por técnico'),
    }

    def create(self, cr, uid, dados, context={}):
        if ('name' not in dados) and ('sale_order_id' in dados):
            sale_obj = self.pool.get('sale.order').browse(cr, uid, dados['sale_order_id'], context=context)

            nome = sale_obj.tipo_os_id.nome
            dados['name'] = nome

        return super(crm_meeting, self).create(cr, uid, dados, context=context)


crm_meeting()
