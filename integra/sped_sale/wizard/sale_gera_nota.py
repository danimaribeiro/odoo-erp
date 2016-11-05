# -*- coding: utf-8 -*-

from osv import fields, osv
from integra_rh.models.hr_payslip_input import mes_atual, primeiro_ultimo_dia_mes


class finan_gera_nota(osv.osv_memory):
    _name = 'sale.gera_nota'
    _description = u'Gerar notas fiscais'

    def _set_input_ids(self, cr, uid, ids, nome_campo, valor_campo, arg, context=None):
        #
        # Salva manualmente as entradas
        #
        if not isinstance(ids, list):
            if ids:
                ids = [ids]
            else:
                ids = []

        if len(valor_campo) and len(ids):
            for gera_nota_obj in self.browse(cr, uid, ids):
                for operacao, entrada_id, valores in valor_campo:
                    #
                    # Cada lanc_item tem o seguinte formato
                    # [operacao, id_original, valores_dos_campos]
                    #
                    # operacao pode ser:
                    # 0 - criar novo registro (no caso aqui, vai ser ignorado)
                    # 1 - alterar o registro
                    # 2 - excluir o registro (também vai ser ignorado)
                    # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
                    # 4 - vincular a um registro existente
                    #
                    if operacao == 1:
                        self.pool.get('hr.payslip.input').write(cr, uid, [entrada_id], valores)
                    elif operacao == 0:
                        self.pool.get('hr.payslip.input').create(cr, uid, valores)
                    elif operacao == 2:
                        entrada_obj = self.pool.get('hr.payslip.input').browse(cr, uid, entrada_id)
                        if not entrada_obj.payslip_id:
                            self.pool.get('hr.payslip.input').unlink(cr, uid, [entrada_id])

    def _get_pedido_ids(self, cr, uid, ids, nome_campo, args=None, context={}):
        if ids:
            gera_nota_obj = self.browse(cr, uid, ids[0])
            data_inicial = gera_nota_obj.data_inicial
            data_final = gera_nota_obj.data_final

            if gera_nota_obj.company_id:
                company_id = gera_nota_obj.company_id.id
            else:
                company_id = False

            if gera_nota_obj.partner_id:
                partner_id = gera_nota_obj.partner_id.id
            else:
                partner_id = False

            if gera_nota_obj.pedido_id:
                pedido_id = gera_nota_obj.pedido_id.id
            else:
                pedido_id = False

        else:
            if 'data_inicial' not in context or 'data_final' not in context:
                return {}

            data_inicial = context['data_inicial']
            data_final = context['data_final']

            if not data_inicial or not data_final:
                raise osv.except_osv(u'Atenção', u'É preciso escolher um período!')

            company_id = context.get('company_id', False)
            pedido_id = context.get('pedido_id', False)

        sql = '''
        select distinct
            so.id

        from
            sale_order so
            left join sale_order_sped_documento sosd on sosd.sale_order_id = so.id
            left join sped_documento d on d.id = sosd.sped_documento_id

        where
            so.state = 'done'
            and so.sale_order_original_id is null
            and (sosd.sale_order_id is null or d.situacao not in ('00', '01'))
        '''

        if pedido_id:
            sql += '''
            and so.id = {pedido_id}
            '''.format(pedido_id=pedido_id)

        else:
            sql += '''
            and so.date_order between '{data_inicial}' and '{data_final}'
            '''.format(data_inicial=data_inicial, data_final=data_final)

        if company_id:
            sql += '''
            and so.company_id = {company_id}
            '''.format(company_id=company_id)

        if partner_id:
            sql += '''
            and so.partner_id = {partner_id}
            '''.format(partner_id=partner_id)

        pedido_pool = self.pool.get('sale.order')

        if 'mao_de_obra_instalacao' in pedido_pool._columns:
            sql += '''
            and (so.mao_de_obra_instalacao != so.vr_total_venda_impostos or so.mao_de_obra_instalacao_faturamento_direto is null)
            '''

        cr.execute(sql)
        dados = cr.fetchall()
        pedido_ids = []
        for pedido_id, in dados:
            pedido_ids.append(pedido_id)

        res = {}
        if ids:
            for id in ids:
                res[id] = pedido_ids
        else:
            res = pedido_ids

        return res

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa'),
        'data_inicial': fields.date('Data inicial'),
        'data_final': fields.date('Data final'),
        'partner_id': fields.many2one('res.partner', u'Cliente'),
        'pedido_id': fields.many2one('sale.order', u'Pedido'),
        'operacao_produto_id': fields.many2one('sped.operacao', u'Operação fiscal para produtos'),
        'operacao_servico_id': fields.many2one('sped.operacao', u'Operação fiscal para serviços'),
        'pedido_ids': fields.function(_get_pedido_ids, method=True, type='one2many', string=u'Pedidos', relation='sale.order'),  # , fnct_inv=_set_input_ids),
    }

    def onchange_get_operacao_produto_id(self, cr, uid, ids, context={}):
        if 'company_id' in context:
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sale.gera_nota', context),

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        if company_obj.operacao_id:
            return company_obj.operacao_id.id

    def onchange_get_operacao_servico_id(self, cr, uid, ids, context={}):
        if 'company_id' in context:
            company_id = context['company_id']
        else:
            company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'sale.gera_nota', context),

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

        if company_obj.operacao_servico_id:
            return company_obj.operacao_servico_id.id

    _defaults = {
        'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[0],
        'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_atual())[1],
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.gera_nota', context=c),
        'operacao_produto_id': onchange_get_operacao_produto_id,
        'operacao_servico_id': onchange_get_operacao_servico_id,
    }

    def onchange_company_id(self, cr, uid, ids, company_id, context={}):
        if not company_id:
            return {}

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        valores = {}
        retorno = {'value': valores}
        valores['operacao_produto_id'] = company_obj.operacao_id.id
        valores['operacao_servico_id'] = company_obj.operacao_servico_id.id

        return retorno

    def gera_notas(self, cr, uid, ids, context=None):
        pedidos = context['pedido_ids']
        pedido_ids = []

        for operacao, pedido_id, valores in pedidos:
            pedido_ids += [pedido_id]

        #
        # Agrupa os pedidos por cliente
        #
        pedidos_cliente = {}
        for pedido_obj in self.pool.get('sale.order').browse(cr, uid, pedido_ids):
            cnpj = pedido_obj.partner_id.cnpj_cpf
            if cnpj not in pedidos_cliente:
                pedidos_cliente[cnpj] = [pedido_obj]
            else:
                pedidos_cliente[cnpj].append(pedido_obj)

        #
        # Agora, gera as notas propriamente ditas
        #
        for cnpj in pedidos_cliente:
            if len(pedidos_cliente[cnpj]) == 1:
                pedido_obj = pedidos_cliente[cnpj][0]
                print('cnpj', cnpj)
                pedido_obj.gera_notas()
            else:
                pass

    def busca_pedidos(self, cr, uid, ids, context={}):
        #valores = {}
        #retorno = {'value': valores}

        pedido_ids = self._get_pedido_ids(cr, uid, ids, 'pedido_ids', context=context)

        return self.write(cr, uid, ids, {'pedido_ids': pedido_ids})


finan_gera_nota()
