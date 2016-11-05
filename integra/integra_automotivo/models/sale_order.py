# -*- coding: utf-8 -*-


from osv import osv, fields


class sale_order(osv.osv):
    _name = 'sale.order'
    _inherit = 'sale.order'

    _columns = {
        'frota_veiculo_id': fields.many2one('frota.veiculo', u'Veículo'),
        'avarias': fields.text(u'Avarias'),
        'solicitacoes': fields.text(u'Solicitações'),
        'obs': fields.text(u'Observações'),
        'km_atual': fields.float(u'Km atual'),
        'data_entrega': fields.datetime(u'Data de entrega'),
        'prisma': fields.char(u'Prisma', size=10),
        'user_id': fields.many2one('res.users', u'Mecânico'),

        'state': fields.selection([
            ('draft', u'Orçamento'),
            ('waiting_date', u'Aguardando agendamento'),
            ('manual', u'Para faturar'),
            ('progress', u'Em andamento'),
            ('shipping_except', u'Exceção de entrega'),
            ('invoice_except', u'Exceção de faturamento'),
            ('done', u'Concluído'),
            ('cancel', u'Cancelado')
            ], u'Situação', readonly=True, help=u"Informa a Situação do orçamento ou pedido. A Situação de Exceção é automaticamente definida quando um Cancelamento ocorre na validação do faturamento (Exceção de faturamento) ou no processo de separação (Excessão de entrega). O 'Aguardando agendamento' é definido quando a fatura está confirmada, mas está esperando o agendamento na data do pedido.", select=True),
    }

    def action_wait(self, cr, uid, ids, context=None):
        for o in self.browse(cr, uid, ids):
            if not o.order_line:
                raise osv.except_osv(u'Erro!', u'Você não pode confirmar um orçamento sem itens.')

            #if (o.order_policy == 'manual'):
                #self.write(cr, uid, [o.id], {'state': 'manual', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)}, context={'calculo_resumo': True})
            #else:
            self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)}, context={'calculo_resumo': True})
            self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line])
            message = u"O orçamento '%s' foi convertido num pedido." % o.versao
            self.log(cr, uid, o.id, message)
        return True

    def confirma_execucao(self, cr, uid, ids, context={}):
        for o in self.browse(cr, uid, ids):
            self.write(cr, uid, [o.id], {'state': 'done', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)}, context={'calculo_resumo': True})
            self.log(cr, uid, o.id, u'A execução do orçamento foi confirmada.')


sale_order()



class sale_order_line(osv.osv):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'

    _columns = {
        'colaborador_id': fields.many2one('res.users', u'Colaborador'),
        'posicao': fields.char(u'Posição', size=10),
        'user_id': fields.many2one('res.users', u'Mecânico'),
    }


sale_order_line()
