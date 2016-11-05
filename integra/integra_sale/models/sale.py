# -*- encoding: utf-8 -*-
import os
import base64
from sped.models.fields import CampoDinheiro
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
#from decimal import Decimal as D
#from openerp import SUPERUSER_ID
from copy import copy
import decimal_precision as dp
from tools.translate import _
from sale_order_line import *
from finan.wizard.finan_relatorio import Report
from dateutil.relativedelta import relativedelta
from pybrasil.data import parse_datetime
DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')



class sale_motivo_cancelamento(osv.Model):
    _name = 'sale.motivocancelamento'
    _description = 'Pedido Motivos para Camcecelamento'
    _order = 'nome'
    _rec_name = 'nome'

    _columns = {
        'nome': fields.char(u'Motivo do Cancelamento', size=60, required=True, select=True),
    }

sale_motivo_cancelamento()

class sale_order(osv.Model):
    _inherit = ['sale.order', 'mail.thread']
    _name = 'sale.order'

    def onchange_date_order(self, cursor, user_id, ids, date_order, dias_validade=10, context={}):
        valores = {}
        retorno = {'value': valores}

        data = parse_datetime(date_order).date() + relativedelta(days=+dias_validade)
        valores['dt_validade'] = str(data)

        return retorno

    _columns = {
        'orcamento_aprovado': fields.char(u'Orçamento aprovado', size=15),
        'dias_validade': fields.float(u'Dias de validade'),
        'dt_validade': fields.date(u'Data de Validade'),
        'motivo_cancelamento_id': fields.many2one('sale.motivocancelamento', u'Motivo do Cancelamento', select=True),
        'mail_message_ids': fields.one2many('mail.message', 'res_id', 'Emails', domain=[('model', '=', 'sale.order')]),
        'crm_phonecall_ids': fields.one2many('crm.phonecall', 'sale_order_id', u'Ligações telefônicas'),
        'partner_fone': fields.related('partner_id', 'fone', type='char', string='Fone'),
        'partner_celular': fields.related('partner_id', 'celular', type='char', string='Celular'),
        'bloqueado_limite_credito': fields.float(u'Bloaqueado por limite de crédito'),
    }

    _defaults = {
        'dias_validade': 10,
    }

    def verifica_limite_credito(self, cr, uid, ids, dados={}, context={}):
        user_pool = self.pool.get('res.users')
        usuario_obj = user_pool.browse(cr, 1, uid)
        nivel_usuario = usuario_obj.nivel_aprovacao_comercial or 0

        print('dados', dados)

        if ('state' not in dados) or (dados['state'] != 'manual'):
            return

        for sale_order_obj in self.browse(cr, uid, ids):
            cr.execute('update sale_order set bloqueado_limite_credito = 0 where id = {id};'.format(id=sale_order_obj.id))

            if sale_order_obj.partner_id.credit_limit:
                print('limite do cliente', sale_order_obj.partner_id.credit_limit)
                print('valor da venda', sale_order_obj.vr_total_venda_impostos)
                bloqueado_limite_credito = D(0)
                total = sale_order_obj.vr_total_venda_impostos or sale_order_obj.amount_total or 0

                if sale_order_obj.partner_id.credit_limit < total:
                    bloqueado_limite_credito = D(total) / D(sale_order_obj.partner_id.credit_limit)
                    bloqueado_limite_credito -= 1
                    bloqueado_limite_credito *= 100

                    #
                    # Agora, busca o nível mais baixo de usuário que pode aprovar este pedido
                    #
                    cr.execute("""
                        select
                            coalesce(min(oga.nivel), 0) as nivel
                        from
                            orcamento_grupo_aprovacao oga
                        where
                           oga.percentual_limite_credito >= {bloqueado_limite_credito};
                        """.format(bloqueado_limite_credito=bloqueado_limite_credito))
                    niveis = cr.fetchone()
                    nivel = 0
                    if len(niveis):
                        nivel = niveis[0]

                    if (nivel_usuario < nivel) or (nivel_usuario == 0) or (nivel == 0):
                        cr.execute('update sale_order set bloqueado_limite_credito = {bloqueado_limite_credito} where id = {id};'.format(id=sale_order_obj.id, bloqueado_limite_credito=bloqueado_limite_credito))
                        raise osv.except_osv(u'Erro', u'Você não tem permissão de realizer essa operação, pois o limite de crédito do cliente foi ultrapassado!')


    def create(self, cr, uid, dados, context={}):
        if 'date_order' in dados and dados['date_order']:
            if 'dias_validade' in dados and dados['dias_validade']:
                dados['dt_validade'] = str(parse_datetime(dados['date_order']).date() + relativedelta(days=+dados['dias_validade']))

        return super(sale_order, self).create(cr, uid, dados, context=context)

    def write(self, cr, uid, ids, dados, context={}):
        self.verifica_limite_credito(cr, uid, ids, dados, context=context)
        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)
        return res

    def agenda_ligacao(self, cr, uid, ids, hora, resumo_ligacao, descricao, fone, user_id, acao='schedule', context={}):
        """
        action :('schedule','Schedule a call'), ('log','Log a call')
        """
        ligacao_pool= self.pool.get('crm.phonecall')
        dados_ligacao = {}

        for saleorder_obj in self.browse(cr, uid, ids, context=context):
            dados = {
                    'name' : resumo_ligacao,
                    'sale_order_id': saleorder_obj.id,
                    'opportunity_id' : False,
                    'user_id' : user_id or saleorder_obj.user_id.id or uid,
                    'categ_id' : False,
                    'description' : descricao or '',
                    'date' : hora,
                    'section_id' : False,
                    'partner_id': saleorder_obj.partner_id and saleorder_obj.partner_id.id or False,
                    'partner_address_id': saleorder_obj.partner_invoice_id and saleorder_obj.partner_invoice_id.id or False,
                    'partner_phone' : fone or saleorder_obj.partner_fone or (saleorder_obj.partner_invoice_id and saleorder_obj.partner_invoice_id.phone or False),
                    'partner_mobile' : saleorder_obj.partner_celular or saleorder_obj.partner_invoice_id and saleorder_obj.partner_invoice_id.mobile or False,
                    #'priority': saleorder_obj.priority,
            }

            ligacao_id = ligacao_pool.create(cr, uid, dados, context=context)
            ligacao_pool.case_open(cr, uid, [ligacao_id])
            if acao == 'log':
                ligacao_pool.case_close(cr, uid, [ligacao_id])
            dados_ligacao[saleorder_obj.id] = ligacao_id

        return dados_ligacao

    def incluir_anotacao(self, cr, uid, ids, context=None):
        if ids:
            lancamento_id = ids[0]

        if not lancamento_id:
            return

        view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'integra_sale', 'sale_nota_wizard')[1]

        retorno = {
            'type': 'ir.actions.act_window',
            'name': 'Anotação',
            'res_model': 'sale.nota',
            #'res_id': None,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',  # isto faz abrir numa janela no meio da tela
            'context': {'modelo': 'sale.order', 'active_ids': [lancamento_id]},
        }

        return retorno

    def onchange_dias_validade(self, cr, uid, ids, dias_validade, date_order, context={}):
        if not dias_validade:
            return {}

        data = parse_datetime(date_order).date() + relativedelta(days=+dias_validade)

        res = {'value': {'dt_validade': str(data)}}

        return res


sale_order()


class mail_compose_message(osv.osv_memory):
    """Generic E-mail composition wizard. This wizard is meant to be inherited
       at model and view level to provide specific wizard features.

       The behavior of the wizard can be modified through the use of context
       parameters, among which are:

         * mail.compose.message.mode: if set to 'reply', the wizard is in
                      reply mode and pre-populated with the original quote.
                      If set to 'mass_mail', the wizard is in mass mailing
                      where the mail details can contain template placeholders
                      that will be merged with actual data before being sent
                      to each recipient. Recipients will be derived from the
                      records determined via  ``context['active_model']`` and
                      ``context['active_ids']``.
         * active_model: model name of the document to which the mail being
                        composed is related
         * active_id: id of the document to which the mail being composed is
                      related, or id of the message to which user is replying,
                      in case ``mail.compose.message.mode == 'reply'``
         * active_ids: ids of the documents to which the mail being composed is
                      related, in case ``mail.compose.message.mode == 'mass_mail'``.
    """

    _name = 'mail.compose.message'
    _inherit = 'mail.compose.message'

    def get_value(self, cr, uid, model, res_id, context=None):
        res = super(mail_compose_message, self).get_value(cr, uid, model, res_id, context=context)

        if model == 'sale.order':
            doc_obj = self.pool.get('sale.order').browse(cr, uid, res_id)

            res['email_to'] = doc_obj.partner_order_id.email or doc_obj.partner_id.email_nfe or ''
            res['subject'] = u'Envio de pedido'

        return res


mail_compose_message()
