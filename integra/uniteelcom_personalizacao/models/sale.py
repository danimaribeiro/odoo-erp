# -*- encoding: utf-8 -*-


from osv import osv, fields


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    _columns = {
        'assinatura_ids': fields.one2many('sale.order.assinatura', 'order_id', u'Assinaturas'),
        'rateio_comissao_ids': fields.one2many('sale.order.rateio_comissao', 'order_id', u'Rateios de comissão'),

        #
        # Termos da proposta
        #
        'referencia': fields.text(u'Referência'),
        'texto_inicial': fields.text(u'Texto inicial'),
        'consideracoes': fields.text(u'Considerações'),
        'descricao_servico': fields.text(u'Descrição do(s) serviço(s)'),
        'descricao_prazo': fields.text(u'Prazos'),
        'condicoes_comerciais': fields.text(u'Condições comerciais'),
    }

    _defaults = {
        #'orcamento_aprovado': 'venda',
    }

    def gera_assinatura(self, cr, uid, ids, context):
        assinatura_pool = self.pool.get('sale.order.assinatura')

        for id in ids:
            dados = {
                'order_id': id,
                'user_id': uid,
                'data': fields.datetime.now()
            }

            assinatura_pool.create(cr, uid, dados)

            assinatura_ids = assinatura_pool.search(cr, uid, [('order_id', '=', id)])

            if len(assinatura_ids) >= 2:
                self.write(cr, uid, [id], {'state': 'invoice_except'})

    def gera_aprovacao_cliente(self, cr, uid, ids, context):
        assinatura_pool = self.pool.get('sale.order.assinatura')

        for id in ids:
            dados = {
                'order_id': id,
                'user_id': uid,
                'data': fields.datetime.now(),
                'aprovacao_cliente': True,
            }

            assinatura_pool.create(cr, uid, dados)

            self.write(cr, uid, [id], {'state': 'progress'})

    def action_wait(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.order_line:
                raise osv.except_osv(u'Error!', u'Você não pode confirmar um pedido de venda sem nenhum item!')

            if not o.assinatura_ids or len(o.assinatura_ids) < 2:
                raise osv.except_osv(u'Error!', u'É preciso ainda a confirmação de pelo menos 2 assinaturas!')

            assinatura_id = self.pool.get('sale.order.assinatura').search(cr, uid, [('order_id', '=', o.id), ('aprovacao_cliente', '=', True)])

            if not assinatura_id or len(assinatura_id) == 0:
                raise osv.except_osv(u'Error!', u'É preciso ainda a confirmação do cliente!')

            if not o.assinatura_ids or len(o.assinatura_ids) < 3:
                raise osv.except_osv(u'Error!', u'É preciso ainda a confirmação de pelo menos 2 assinaturas!')

            if (o.order_policy == 'manual'):
                self.write(cr, uid, [o.id], {'state': 'manual', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
            else:
                self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
            self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line])
            message = u'O orçamento "%s" foi convertido em pedido de venda.' % (o.name,)
            self.log(cr, uid, o.id, message)
        return True

    def write(self, cr, uid, ids, dados, context=None):
        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)
        self.ajusta_rateio_comissao(cr, uid, ids)
        return res

    def ajusta_rateio_comissao(self, cr, uid, ids):

        for ped_obj in self.browse(cr, uid, ids):
            if len(ped_obj.rateio_comissao_ids) == 0:
                dados = {
                    'order_id': ped_obj.id,
                    'user_id': ped_obj.user_id.id,
                    'comissao': 100.00,
                }
                self.pool.get('sale.order.rateio_comissao').create(cr, uid, dados)

            else:
                total = 0
                for ratcom_obj in ped_obj.rateio_comissao_ids:
                    total += ratcom_obj.comissao

                if int(total) > 0 and int(total) != 100:
                    raise osv.except_osv(u'Inválido!', u'A soma do rateio das comissões é diferente de 100%! Revise os rateios de comissão!')


sale_order()



class sale_order_assinatura(osv.Model):
    _name = 'sale.order.assinatura'
    _order = 'data desc'

    _columns = {
        'order_id': fields.many2one('sale.order', u'Pedido'),
        'user_id': fields.many2one('res.users', u'Usuário'),
        'data': fields.datetime(u'Data'),
        'aprovacao_cliente': fields.boolean(u'Aprovado pelo cliente?'),
    }

    _default = {
        'user_id': lambda self, cr, uid, context: uid,
        'data': fields.datetime.now,
        'aprovacao_cliente': False,
    }


sale_order_assinatura()


class sale_order_rateio_comissao(osv.Model):
    _name = 'sale.order.rateio_comissao'

    _columns = {
        'order_id': fields.many2one('sale.order', u'Pedido'),
        'user_id': fields.many2one('res.users', u'Usuário'),
        'comissao': fields.float(u'Comissão'),
    }


sale_order_rateio_comissao()
