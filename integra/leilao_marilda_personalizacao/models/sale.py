# -*- encoding: utf-8 -*-


from osv import osv, fields
from decimal import Decimal as D


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    _columns = {
        #'date_order': fields.datetime(u'Abertura'),
        'date_order': fields.date(u'Abertura'),
        'date_order_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'De data do pedido'),
        'date_order_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'A data do pedido'),
        'finan_formapagamento_id': fields.many2one('finan.formapagamento', u'Forma de pagamento'),
        'valor_frete': fields.float(u'Valor Frete'),
        'parcelas': fields.float(u'Parcelas'),
        'vr_parcelas': fields.float(u'Valor das Parcelas'),
        'vr_primeira_parcela': fields.float(u'Valor da primeira Parcela'),
        'frete_primeira': fields.boolean(u'Frete na primeira parcela?'),
        'data_hora_id': fields.many2one('data.hora.leilao',u'Horário'),
        'midia_id': fields.many2one('midia.leilao',u'Mídia'),

        # 'assinatura_ids': fields.one2many('sale.order.assinatura', 'order_id', u'Assinaturas'),
        # 'rateio_comissao_ids': fields.one2many('sale.order.rateio_comissao', 'order_id', u'Rateios de comissão'),
        #
        # Termos da proposta
        #
        # 'referencia': fields.text(u'Referência'),
        # 'texto_inicial': fields.text(u'Texto inicial'),
        # 'consideracoes': fields.text(u'Considerações'),
        # 'descricao_servico': fields.text(u'Descrição do(s) serviço(s)'),
        # 'descricao_prazo': fields.text(u'Prazos'),
        # 'condicoes_comerciais': fields.text(u'Condições comerciais'),
    }

    _defaults = {
        # 'orcamento_aprovado': 'venda',
    }

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, partner_id)

        if not partner_id:
            return res

        valores = res['value']

        partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)

        if partner_obj.finan_formapagamento_id:
            valores['finan_formapagamento_id'] = partner_obj.finan_formapagamento_id.id

        if partner_obj.account_payment_term_id:
            valores['payment_term'] = partner_obj.account_payment_term_id.id

        return res

    def write(self, cr, uid, ids, dados, context=None):

        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)
        #for id in ids:
            #self.pool.get('sale.order.line').calcula_total_orcamento(cr, uid, id)
            #self.calcula_total_orcamento(cr, uid, id)
            #self.cria_resumo_locacao(cr, uid, id)


        return res

    def _prepare_order_picking(self, cr, uid, order, context=None):
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        return {
            'name': pick_name,
            'origin': order.name,
            'date': order.date_order + ' 15:00:00',  # Compensa o fuso horário de Brasília x UTC
            'type': 'out',
            'state': 'auto',
            'move_type': order.picking_policy,
            'sale_id': order.id,
            'address_id': order.partner_shipping_id.id,
            'note': order.note,
            'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
            'company_id': order.company_id.id,
        }


sale_order()
