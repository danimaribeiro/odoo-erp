# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, orm, fields
import base64
from pybrasil.valor.decimal import Decimal as D
from copy import copy
from sped.constante_tributaria import *
from pybrasil.valor import formata_valor


CFOPS_COMPRA_CUSTO_LOCACAO = CFOPS_COMPRA_ATIVO + CFOPS_USO_CONSUMO


class product_product(orm.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    def get_product_available(self, cr, uid, ids, context=None):
        """ Finds whether product is available or not in particular warehouse.
        @return: Dictionary of values
        """
        if context is None:
            context = {}

        location_obj = self.pool.get('stock.location')
        warehouse_obj = self.pool.get('stock.warehouse')
        shop_obj = self.pool.get('sale.shop')

        user_obj = self.pool.get('res.users').browse(cr, 1, uid)

        states = context.get('states',[])
        what = context.get('what',())
        if not ids:
            ids = self.search(cr, uid, [])
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res

        if context.get('shop', False) and context['shop']:
            warehouse_id = shop_obj.read(cr, 1, int(context['shop']), ['warehouse_id'])['warehouse_id'][0]
            if warehouse_id:
                context['warehouse'] = warehouse_id

        if context.get('warehouse', False) and context['warehouse']:
            lot_id = warehouse_obj.read(cr, 1, int(context['warehouse']), ['lot_stock_id'])['lot_stock_id'][0]
            if lot_id:
                context['location'] = lot_id

        if context.get('location', False) and context['location']:
            if type(context['location']) == type(1):
                location_ids = [context['location']]
            elif type(context['location']) in (type(''), type(u'')):
                location_ids = location_obj.search(cr, 1, [('name','ilike',context['location'])], context=context)
            else:
                location_ids = context['location']
        else:
            location_ids = []
            #wids = warehouse_obj.search(cr, uid, [], context=context)
            #for w in warehouse_obj.browse(cr, uid, wids, context=context):
            #    location_ids.append(w.lot_stock_id.id)
            lids = location_obj.search(cr, 1, [])
            #print(lids, 'todas os locais', user_obj.company_id.id)
            for lo in location_obj.browse(cr, 1, lids, context=context):
                #print(lo.id, lo.company_id, lo.company_ids, user_obj.company_id.id)
                if lo.company_id and user_obj.company_id.id == lo.company_id.id:
                    location_ids.append(lo.id)
                else:
                    for co in lo.company_ids:
                        if user_obj.company_id.id == co.id:
                            location_ids.append(lo.id)

        # build the list of ids of children of the location given by id
        if context.get('compute_child', True):
            if len(location_ids) == 0:
                raise osv.except_osv(u'Atenção!', u'Não há local de estoque definido para a empresa/unidade!')

            child_location_ids = location_obj.search(cr, 1, [('location_id', 'child_of', location_ids)])
            location_ids = child_location_ids or location_ids

        # this will be a dictionary of the UoM resources we need for conversion purposes, by UoM id
        uoms_o = {}
        # this will be a dictionary of the product UoM by product id
        product2uom = {}
        for product in self.browse(cr, 1, ids, context=context):
            product2uom[product.id] = product.uom_id.id
            uoms_o[product.uom_id.id] = product.uom_id

        results = []
        results2 = []

        from_date = context.get('from_date',False)
        to_date = context.get('to_date',False)
        date_str = False
        date_values = False
        where = [tuple(location_ids),tuple(location_ids),tuple(ids),tuple(states)]
        if from_date and to_date:
            date_str = "date>=%s and date<=%s"
            where.append(tuple([from_date]))
            where.append(tuple([to_date]))
        elif from_date:
            date_str = "date>=%s"
            date_values = [from_date]
        elif to_date:
            date_str = "date<=%s"
            date_values = [to_date]
        if date_values:
            where.append(tuple(date_values))

        prodlot_id = context.get('prodlot_id', False)
        prodlot_clause = ''
        if prodlot_id:
            prodlot_clause = ' and prodlot_id = %s '
            where += [prodlot_id]
        elif 'prodlot_id' in context and not prodlot_id:
            prodlot_clause = 'and prodlot_id is null '

        # TODO: perhaps merge in one query.
        if 'in' in what:
            # all moves from a location out of the set to a location in the set
            cr.execute(
                'select sum(product_qty), product_id, product_uom '\
                'from stock_move '\
                'where location_id NOT IN %s '\
                'and location_dest_id IN %s '\
                'and product_id IN %s '\
                'and state IN %s ' + (date_str and 'and '+date_str+' ' or '') +' '\
                + prodlot_clause +
                'group by product_id,product_uom',tuple(where))
            results = cr.fetchall()
        if 'out' in what:
            # all moves from a location in the set to a location out of the set
            cr.execute(
                'select sum(product_qty), product_id, product_uom '\
                'from stock_move '\
                'where location_id IN %s '\
                'and location_dest_id NOT IN %s '\
                'and product_id  IN %s '\
                'and state in %s ' + (date_str and 'and '+date_str+' ' or '') + ' '\
                + prodlot_clause +
                'group by product_id,product_uom',tuple(where))
            results2 = cr.fetchall()

        # Get the missing UoM resources
        uom_obj = self.pool.get('product.uom')
        uoms = map(lambda x: x[2], results) + map(lambda x: x[2], results2)
        if context.get('uom', False):
            uoms += [context['uom']]
        uoms = filter(lambda x: x not in uoms_o.keys(), uoms)
        if uoms:
            uoms = uom_obj.browse(cr, 1, list(set(uoms)), context=context)
            for o in uoms:
                uoms_o[o.id] = o

        #TOCHECK: before change uom of product, stock move line are in old uom.
        context.update({'raise-exception': False})
        # Count the incoming quantities
        for amount, prod_id, prod_uom in results:
            amount = uom_obj._compute_qty_obj(cr, 1, uoms_o[prod_uom], amount,
                     uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
            res[prod_id] += amount
        # Count the outgoing quantities
        for amount, prod_id, prod_uom in results2:
            amount = uom_obj._compute_qty_obj(cr, 1, uoms_o[prod_uom], amount,
                    uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
            res[prod_id] -= amount

        for prod_id in res:
            if isinstance(res[prod_id], D):
                res[prod_id] = float(res[prod_id])
        return res



    def _custo_ultima_compra(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        #
        # O custo da última compra é contextual para o CNPJ da empresa
        # ativa do usuário no momento
        # O custo da última compra também pode vir de uma atualização de tabela
        # do fornecedor
        #

        if 'company_id' in context:
            company_id = context['company_id']
            company_obj = self.pool.get('res.company').browse(cr, 1, company_id)
        else:
            user_obj = self.pool.get('res.users').browse(cr, 1, uid)
            company_obj = user_obj.company_id

        cnpj = company_obj.partner_id.cnpj_cpf
        #
        # Na Patrimonial, o custo vem sempre da matriz
        #
        cnpj = str(cnpj)[:10]
        cfops = str(CFOPS_COMPRA_CUSTO_VENDA).replace('[', '(').replace(']', ')').replace("u'", "'")

        for product_id in ids:
            sql = '''
select
coalesce(di.vr_unitario_custo, 0), d.id

from
sped_documentoitem di
join sped_documento d on d.id = di.documento_id
join res_company c on c.id = d.company_id
join res_partner p on p.id = c.partner_id
join res_partner pp on pp.id = d.partner_id
join sped_cfop cf on cf.id = di.cfop_id

where
p.cnpj_cpf like '{cnpj}/0001-%'
and d.modelo in ('01', '55', 'TF')
and d.data_entrada_saida_brasilia <= current_date
and d.emissao = '1' and d.entrada_saida = '0'
and d.situacao in ('00', '01', '08')
and di.produto_id = {product_id}
and p.cnpj_cpf != pp.cnpj_cpf
and cf.codigo in {cfops}

order by
d.data_entrada_saida desc

limit 1;'''

            sql = sql.format(product_id=product_id, cnpj=cnpj, cfops=cfops)
            #print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            #
            # O custo padrão, de toda forma, é o informado manualmente
            #
            res[product_id] = self.pool.get('product.product').read(cr, 1, product_id, 'standard_price')['standard_price']

            if len(dados):
                res[product_id] = D(dados[0][0])
                print('buscando custo da ultima compra para venda, produto ', product_id)
                print('id da nota de onde vem o custo', dados[0][1])


        return res


    def _custo_ultima_compra_locacao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        #
        # O custo da última compra é contextual para o CNPJ da empresa
        # ativa do usuário no momento
        # O custo da última compra também pode vir de uma atualização de tabela
        # do fornecedor
        #

        if 'company_id' in context:
            company_id = context['company_id']
            company_obj = self.pool.get('res.company').browse(cr, 1, company_id)
        else:
            user_obj = self.pool.get('res.users').browse(cr, 1, uid)
            company_obj = user_obj.company_id

        cnpj = company_obj.partner_id.cnpj_cpf
        #
        # Na Patrimonial, o custo vem sempre da matriz
        #
        cnpj = str(cnpj)[:10]
        cfops = str(CFOPS_COMPRA_CUSTO_LOCACAO).replace('[', '(').replace(']', ')').replace("u'", "'")

        for product_id in ids:
            sql = '''
select
coalesce(di.vr_unitario_custo, 0), d.id

from
sped_documentoitem di
join sped_documento d on d.id = di.documento_id
join res_company c on c.id = d.company_id
join res_partner p on p.id = c.partner_id
join res_partner pp on pp.id = d.partner_id
join sped_cfop cf on cf.id = di.cfop_id

where
p.cnpj_cpf like '{cnpj}/0001-%'
and d.modelo in ('01', '55', 'TF')
and d.data_entrada_saida_brasilia <= current_date
and d.emissao = '1' and d.entrada_saida = '0'
and d.situacao in ('00', '01', '08')
and di.produto_id = {product_id}
and p.cnpj_cpf != pp.cnpj_cpf
and cf.codigo in {cfops}

order by
d.data_entrada_saida desc

limit 1;'''

            sql = sql.format(product_id=product_id, cnpj=cnpj, cfops=cfops)
            cr.execute(sql)
            dados = cr.fetchall()

            #
            # O custo padrão, de toda forma, é o informado manualmente
            #
            res[product_id] = self.pool.get('product.product').read(cr, 1, product_id, 'standard_price')['standard_price']

            if len(dados):
                res[product_id] = D(dados[0][0])
                print('buscando custo da ultima compra para locacao, produto ', product_id)
                print('id da nota de onde vem o custo', dados[0][1])

        return res

    def _get_quantidade_venda(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        user_obj = self.pool.get('res.users').browse(cr, 1, uid)

        for product_obj in self.browse(cr, uid , ids):
            #
            # Regra da Segurança; local 500, id 21
            #
            #@if user_obj.company_id.partner_id.cnpj_cpf[:10] == '82.891.805':
            if nome_campo == 'qty_novo':
                sql = """
                    select
                        coalesce(es.quantidade, 0) as quantidade
                    from stock_saldo es
                        join stock_location lo on lo.id = es.location_id
                        join res_company c on c.id = es.company_id

                    where
                        es.product_id = {product_id}
                        and es.location_id = 21
                        and es.data <= current_date
                        and c.raiz_cnpj = '82.891.805'
                    order by
                        es.data desc
                    limit 1;
                """
                sql = sql.format(product_id=str(product_obj.id))

            #
            # Regra da Comércio, local 01, id 22
            #
            else:
                sql = """
                    select
                        coalesce(es.quantidade, 0) as quantidade
                    from stock_saldo es
                    join res_company c on c.id = es.company_id
                    join res_partner rp on rp.id = c.partner_id

                    where
                        es.product_id = {product_id}
                        and es.location_id = 22
                        and rp.cnpj_cpf = '{cnpj_cpf}'
                        and es.data <= current_date
                    order by
                        es.data desc
                    limit 1;
                """
                sql = sql.format(product_id=str(product_obj.id),cnpj_cpf=user_obj.company_id.partner_id.cnpj_cpf)

            cr.execute(sql)
            quantidades = cr.fetchall()
            if len(quantidades) > 0:
                res[product_obj.id] = quantidades[0][0]
            else:
                res[product_obj.id] = 0

        return res

    def _get_quantidade_locacao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        user_obj = self.pool.get('res.users').browse(cr, 1, uid)

        for product_obj in self.browse(cr, 1 , ids):
            #
            # Regra da Segurança; local 503, id 1457
            #
            #if user_obj.company_id.partner_id.cnpj_cpf[:10] == '82.891.805':
            if nome_campo == 'qty_usado':
                sql = """
                    select
                        coalesce(es.quantidade, 0) as quantidade

                    from
                        stock_saldo es
                        join stock_location lo on lo.id = es.location_id
                        join res_company c on c.id = es.company_id

                    where
                        es.product_id = {product_id}
                        and es.location_id = 1457
                        and es.data <= current_date
                        and c.raiz_cnpj = '82.891.805'

                    order by
                        es.data desc

                    limit 1;
                """
                sql = sql.format(product_id=str(product_obj.id))

            #
            # Regra da Comércio, local 10, id 27
            #
            else:
                sql = """
                    select
                        coalesce(es.quantidade, 0) as quantidade

                    from
                        stock_saldo es
                        join res_company c on c.id = es.company_id
                        join res_partner rp on rp.id = c.partner_id

                    where
                        es.product_id = {product_id}
                        and es.location_id = 27
                        and rp.cnpj_cpf = '{cnpj_cpf}'
                        and es.data <= current_date

                    order by
                        es.data desc

                    limit 1;
                """
                sql = sql.format(product_id=str(product_obj.id),cnpj_cpf=user_obj.company_id.partner_id.cnpj_cpf)

            cr.execute(sql)
            quantidades = cr.fetchall()
            if len(quantidades) > 0:
                res[product_obj.id] = quantidades[0][0]
            else:
                res[product_obj.id] = 0

        return res
   

    def _get_quantidade_disponivel_venda(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        user_obj = self.pool.get('res.users').browse(cr, 1, uid)

        for product_obj in self.browse(cr, 1 , ids):
            #
            # Quantidade aprovada para compra
            #
            quantidade_compra = D(0)
            sql = """
                select
                    coalesce(sum(pol.product_qty), 0)
                from purchase_order po
                join purchase_order_line pol on pol.order_id = po.id
                join res_company cc on cc.id = po.company_id
                join res_partner rpc on rpc.id = cc.partner_id
                where
                    po.state = 'approved'
                    and pol.product_id = {product_id}
                    and rpc.cnpj_cpf = '{cnpj_cpf}'
            """
            sql = sql.format(product_id=str(product_obj.id),cnpj_cpf=user_obj.company_id.partner_id.cnpj_cpf)
            cr.execute(sql)
            quantidades = cr.fetchall()
            if len(quantidades) > 0:
                quantidade_compra += D(quantidades[0][0])

            #
            # Quantidade aprovada para venda
            #
            quantidade_venda = D(0)
            sql = """
                select
                    coalesce(sum(slo.quantidade), 0)
                    from sale_order sl
                    join sale_order_line slo on slo.order_id = sl.id
                    join res_company cv on cv.id = sl.company_id
                    join res_partner rpv on rpv.id = cv.partner_id
                    where
                    sl.state = 'manual'
                    and sl.orcamento_aprovado = 'venda'
                    and slo.product_id =  {product_id}
                    and rpv.cnpj_cpf = '{cnpj_cpf}'

                """
            sql = sql.format(product_id=str(product_obj.id),cnpj_cpf=user_obj.company_id.partner_id.cnpj_cpf)
            cr.execute(sql)
            quantidades = cr.fetchall()
            if len(quantidades) > 0:
                quantidade_venda += D(quantidades[0][0])

            quantidade_transferencia = D(0)
            sql = """
            select
                coalesce(sum(
                case
                when es.tipo= 'E' then
                es.quantidade
                when es.tipo= 'S' then
                es.quantidade * -1
                end ), 0) as quantidade

            from estoque_entrada_saida es
            join stock_location lo on lo.id = es.location_id
            join stock_move sm on sm.id = es.move_id
            join stock_picking sp on sp.id = sm.picking_id
            where
                es.product_id = {product_id}
                and sp.type = 'transf'
                and sm.state = 'draft'
                and lo.padrao_venda = true
            """
            sql = sql.format(product_id=str(product_obj.id))
            cr.execute(sql)
            quantidades = cr.fetchall()
            if len(quantidades) > 0:
                quantidade_transferencia = D(quantidades[0][0])

            if '0001' in user_obj.company_id.partner_id.cnpj_cpf:
                res[product_obj.id] =  D(str(product_obj.qty_available)) + quantidade_compra - quantidade_transferencia - quantidade_venda

            else:
                res[product_obj.id] =  D(str(product_obj.qty_available)) + quantidade_transferencia - quantidade_venda

        return res

    def _get_quantidade_disponivel_locacao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        user_obj = self.pool.get('res.users').browse(cr, 1, uid)

        for product_obj in self.browse(cr, 1 , ids):
            #
            # Quantidade aprovada para compra
            #
            quantidade_compra = D(0)
            sql = """
                select
                    coalesce(sum(pol.product_qty), 0)
                from purchase_order po
                join purchase_order_line pol on pol.order_id = po.id
                join res_company cc on cc.id = po.company_id
                join res_partner rpc on rpc.id = cc.partner_id
                where
                    po.state = 'approved'
                    and pol.product_id = {product_id}
                    and rpc.cnpj_cpf = '{cnpj_cpf}'

            """
            sql = sql.format(product_id=str(product_obj.id),cnpj_cpf=user_obj.company_id.partner_id.cnpj_cpf)
            cr.execute(sql)
            quantidades = cr.fetchall()
            if len(quantidades) > 0:
                quantidade_compra += D(quantidades[0][0])

            #
            # Quantidade aprovada para venda
            #
            quantidade_venda = D(0)
            sql = """
                select
                    coalesce(sum(slo.quantidade), 0)
                    from sale_order sl
                    join sale_order_line slo on slo.order_id = sl.id
                    join res_company cv on cv.id = sl.company_id
                    join res_partner rpv on rpv.id = cv.partner_id
                    where
                    sl.state = 'manual'
                    and sl.orcamento_aprovado = 'locacao'
                    and slo.product_id =  {product_id}
                    and rpv.cnpj_cpf = '{cnpj_cpf}'

                """
            sql = sql.format(product_id=str(product_obj.id),cnpj_cpf=user_obj.company_id.partner_id.cnpj_cpf)
            cr.execute(sql)
            quantidades = cr.fetchall()
            if len(quantidades) > 0:
                quantidade_venda += D(quantidades[0][0])

            quantidade_transferencia = D(0)
            sql = """
            select
                coalesce(sum(
                case
                when es.tipo= 'E' then
                es.quantidade
                when es.tipo= 'S' then
                es.quantidade * -1
                end ), 0) as quantidade
            from estoque_entrada_saida es
            join stock_location lo on lo.id = es.location_id
            join stock_move sm on sm.id = es.move_id
            join stock_picking sp on sp.id = sm.picking_id
            where
                es.product_id = {product_id}
                and sp.type = 'transf'
                and sm.state = 'draft'
                and lo.padrao_locacao = true
            """
            sql = sql.format(product_id=str(product_obj.id))
            cr.execute(sql)
            quantidades = cr.fetchall()
            if len(quantidades) > 0:
                quantidade_transferencia = D(quantidades[0][0])

            if '0001' in user_obj.company_id.partner_id.cnpj_cpf:
                res[product_obj.id] =  D(str(product_obj.qty_available)) + quantidade_compra - quantidade_transferencia - quantidade_venda

            else:
                res[product_obj.id] =  D(str(product_obj.qty_available)) + quantidade_transferencia - quantidade_venda

        return res

    _columns = {
        'nome_generico': fields.char(u'Nome genérico', size=60, select=True),
        'percentual_acessorios': fields.float(u'Markup de acessórios'),
        'quantidade_referencia_acessorios': fields.float(u'Quantidade de referência'),
        'valor_acessorios_id': fields.many2one('product.product', u'Item para valor de acessórios'),
        'custo_ultima_compra': fields.function(_custo_ultima_compra, string=u'Custo da última compra/atualização de tabela', method=True, type='float'),
        'custo_ultima_compra_locacao': fields.function(_custo_ultima_compra_locacao, string=u'Custo da última compra/atualização de tabela', method=True, type='float'),
        'qty_available': fields.function(_get_quantidade_venda, type='float', string='Quantidade na mão venda'),        
        'qty_locacao': fields.function(_get_quantidade_locacao, type='float', string='Quantidade na mão locação'),
        'qty_novo': fields.function(_get_quantidade_venda, type='float', string='Quantidade na mão novo'),
        'qty_usado': fields.function(_get_quantidade_locacao, type='float', string='Quantidade na mão usado'),
        'virtual_available': fields.function(_get_quantidade_disponivel_venda, type='float', string='Quantidade disponível venda'),
        'quantidade_disponivel_locacao': fields.function(_get_quantidade_disponivel_locacao, type='float', string='Quantidade disponível locação'),
    }

    def name_get(self, cr, uid, ids, context={}):
        if 'orcamento_aprovado' not in context:
            res = super(product_product, self).name_get(cr, uid, ids, context=context)
        else:
            #
            # Locais de estoque padrão para buscar a quantidade disponível
            #
            if context['orcamento_aprovado'] == 'venda':
                context['location'] = 22  # Local 01 - mercadorias novas para revenda
            else:
                context['location'] = 27  # Local 10 - mercadorias usadas para locação

            produto_pool = self.pool.get('product.product')
            res = []
            for produto_obj in produto_pool.browse(cr, uid, ids, context=context):
                if produto_obj.type == 'service':
                    nome = u'[{codigo}] {nome}'
                else:
                    nome = u'[{codigo}] ({quantidade}) {nome}'

                dados = {
                    'codigo': produto_obj.default_code or '',
                    'nome': produto_obj.name or '',
                    'quantidade': formata_valor(produto_obj.qty_available or 0),
                }
                res.append((produto_obj.id, nome.format(**dados)))

        return res

    def copy(self, cr, uid, id, default, context={}):
        default['custo_ultima_compra'] = False
        default['custo_ultima_compra_locacao'] = False

        res = super(product_product, self).copy(cr, uid, id, default, context=context)

        print(res)

        return res


product_product()
