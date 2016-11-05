# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
from decimal import Decimal as D


class sped_documentoitem(osv.Model):
    _description = 'Itens de documentos SPED'
    _name = 'sped.documentoitem'
    _inherit = 'sped.documentoitem'

    def _get_custo_unitario_estoque(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):
            if item_obj.operacao_id.traz_custo_medio:
                res[item_obj.id] = D(item_obj.vr_unitario)

            elif item_obj.stock_location_id:
                sql_custo = """
                       select
                           coalesce(cm.vr_unitario_custo, 0) as vr_unitario_custo

                       from
                           custo_medio({company_id}, {location_id}, {product_id}) cm

                       where
                           cm.data <= '{data}'

                       order by
                           cm.data desc, cm.entrada_saida desc, cm.move_id desc

                       limit 1;
                """
                sql_custo = sql_custo.format(company_id=item_obj.company_id.id,location_id=item_obj.stock_location_id.id, product_id=item_obj.produto_id.id,data=item_obj.documento_id.data_emissao)
                #print(sql_custo)
                cr.execute(sql_custo)
                dados_custo = cr.fetchall()
                if len(dados_custo):
                    res[item_obj.id] = D(dados_custo[0][0] or 0)
                else:
                    res[item_obj.id] = 0
            else:
                res[item_obj.id] = 0

        return res

    def _get_custo_estoque(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for item_obj in self.browse(cr, uid, ids):

            vr_custo_estoque = D(0)

            vr_custo_estoque += D(item_obj.vr_unitario_custo_estoque) * D(item_obj.quantidade)

            res[item_obj.id] = vr_custo_estoque

        return res

    _columns = {
        'stock_move_id': fields.many2one('stock.move', u'Movimentação do estoque', ondelete='cascade'),
        'stock_location_id': fields.many2one('stock.location', u'Local de origem', ondelete='restrict'),
        'stock_location_dest_id': fields.many2one('stock.location', u'Local de destino', ondelete='restrict'),
        'produto_type': fields.related('produto_id', 'type', type='char', string=u'Tipo de produto'),
        'stock_move_picking_id': fields.many2one('stock.move', u'Item do Pedido de Compra', ondelete='restrict', select=True),
        'vr_unitario_custo_estoque': fields.function(_get_custo_unitario_estoque, type='float', string=u'Valor Unitário Estoque', digits=(21, 10), store=True),
        'vr_custo_estoque': fields.function(_get_custo_estoque, type='float', string=u'Valor Custo Estoque', digits=(18, 2), store=True),
    }

    #def onchange_produto_entrada(self, cr, uid, ids, produto_id, cfop_original_id, cfop_id, context):
        #res = super(sped_documentoitem, self).onchange_produto_entrada(cr, uid, ids, produto_id, cfop_original_id, cfop_id, context)

        #print(context)

        #company_id = context['default_company_id']
        #partner_id = context['default_partner_id']
        #operacao_id = context['default_operacao_id']
        #entrada_saida = context['default_entrada_saida']
        #regime_tributario = context['default_regime_tributario']
        #emissao = context['default_emissao']
        #data_emissao = context.get('default_data_emissao', None)
        #municipio_fato_gerador_id = context.get('default_municipio_fato_gerador_id', None)
        #contribuinte = context.get('default_contribuinte', '1')
        #modelo = context.get('default_modelo', '55')

        ##
        ## O tipo do contribuinte só tem nexo para NF-e modelo 55
        ## nos demais casos, definir fixo como '1'
        ##
        #if modelo != '55' or emissao != '0':
            #contribuinte = '1'


        #modelo = context.get('default_modelo', '55')

        #if modelo == '57':
            #return res

        ##
        ## Vamos trazer todos os registros necessários
        ##
        #company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        #partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)
        #operacao_obj = self.pool.get('sped.operacao').browse(cr, uid, operacao_id)
        #produto_obj = self.pool.get('product.product').browse(cr, uid, produto_id)

        #if municipio_fato_gerador_id:
            #municipio_fato_gerador_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_fato_gerador_id)
        #else:
            #municipio_fato_gerador_obj = partner_obj.municipio_id

        ##
        ## Achamos a família tributária do ICMS, que vai determinar
        ## as alíquotas do ICMS e a CFOP
        ##
        #if produto_obj.familiatributaria_id:
            #familiatributaria_obj = produto_obj.familiatributaria_id
        #elif company_obj.familiatributaria_id:
            #familiatributaria_obj = company_obj.familiatributaria_id
        #else:
            #raise osv.except_osv(u'Erro!', u'Não há família tributária padrão, nem família tributária definida no produto/serviço “%s”!' % produto_obj.name)

        ##
        ## Guarda a família tributária original
        ##
        #familiatributaria_original_obj = familiatributaria_obj

        #try:
            #uf_origem = company_obj.partner_id.municipio_id.estado_id.uf
        #except:
            #raise osv.except_osv(u'Erro!', u'Não há município para a empresa “' + company_obj.name + u'”')

        #try:
            #uf_destino = partner_obj.municipio_id.estado_id.uf
        #except:
            #raise osv.except_osv(u'Erro!', u'Não há município para o cliente “' + partner_obj.name + u'”')

        #dentro_estado = uf_origem == uf_destino
        #fora_estado = uf_origem != uf_destino
        #fora_pais = uf_destino == 'EX'

        ##
        ## E vamos localizar o item da operação com a CFOP correta para o caso
        ##
        #lista_operacaoitem_ids = self.pool.get('sped.operacaoitem').search(
            #cr,
            #uid,
            #[
                #('operacao_id', '=', operacao_obj.id),
                #('familiatributaria_id', '=', familiatributaria_obj.id),
                #('cfop_id.dentro_estado', '=', dentro_estado),
                #('cfop_id.fora_estado', '=', fora_estado),
                #('cfop_id.fora_pais', '=', fora_pais),
                #'|', ('contribuinte', '=', contribuinte), ('contribuinte', '=', None),
            #]
        #)

        ##
        ## Caso não haja um item da operação específico para a família, busca
        ## o genérico (item da operação sem família)
        ##
        #if len(lista_operacaoitem_ids) == 0:
            #lista_operacaoitem_ids = self.pool.get('sped.operacaoitem').search(
                #cr,
                #uid,
                #[
                    #('operacao_id', '=', operacao_obj.id),
                    #('familiatributaria_id', '=', None),
                    #('cfop_id.dentro_estado', '=', dentro_estado),
                    #('cfop_id.fora_estado', '=', fora_estado),
                    #('cfop_id.fora_pais', '=', fora_pais),
                    #'|', ('contribuinte', '=', contribuinte), ('contribuinte', '=', None),
                #]
            #)

        #if len(lista_operacaoitem_ids) == 0 or len(lista_operacaoitem_ids) > 1:
            #if len(lista_operacaoitem_ids) == 0:
                #mensagem = u'Não há um item da operação “%s” configurado para o produto “%s”, família tributária “%s”,' % (operacao_obj.nome, produto_obj.name, familiatributaria_obj.descricao)
            #else:
                #mensagem = u'Há mais de um item da operação “%s” configurado para o produto “%s”, família tributária “%s”,' % (operacao_obj.nome, produto_obj.name, familiatributaria_obj.descricao)

            #if contribuinte == '1':
                #mensagem += ' para contribuinte com IE '
            #elif contribuinte == '2':
                #mensagem += ' para contribuinte isento '
            #elif contribuinte == '9':
                #mensagem += ' para estrangeiro '

            #if dentro_estado:
                #mensagem += 'com CFOP para dentro do estado!'
            #elif fora_estado:
                #mensagem += 'com CFOP para fora do estado!'
            #else:
                #mensagem += 'com CFOP para fora do país!'

            #raise osv.except_osv(u'Erro!', mensagem)

        #lista_operacaoitem_id = lista_operacaoitem_ids[0]
        #operacao_item_obj = self.pool.get('sped.operacaoitem').browse(cr, uid, lista_operacaoitem_id)

        #valores = res['value']
        #if operacao_item_obj.stock_location_id:
            #valores['stock_location_id'] = operacao_item_obj.stock_location_id.id

        #if operacao_item_obj.stock_location_dest_id:
            #valores['stock_location_dest_id'] = operacao_item_obj.stock_location_dest_id.id

        #if operacao_obj.traz_custo_medio:
            #vr_unitario = 0


            #if operacao_item_obj.stock_location_id:
                ##
                ## Busca o custo unitário médio do produto no momento
                ##
                #custo_pool = self.pool.get('product.custo')
                #qtd, unit, tot = custo_pool.busca_custo(cr, 1, company_id=company_id, location_id=operacao_item_obj.stock_location_id.id, product_id=produto_obj.id)
                #vr_unitario = D(unit)

            #if vr_unitario != 0:
                #for local_custo_obj in operacao_obj.local_custo_ids:
                    ##
                    ## Busca o custo unitário médio do produto no momento
                    ##
                    #custo_pool = self.pool.get('product.custo')
                    #qtd, unit, tot = custo_pool.busca_custo(cr, 1, company_id=company_id, location_id=local_custo_obj.stock_location_id.id, product_id=produto_obj.id)
                    #vr_unitario = D(unit)

                    #if vr_unitario:
                        #break

            #if vr_unitario <= 0:
                #vr_unitario = D(produto_obj.standard_price)

            #valores['vr_unitario'] = vr_unitario

        #return res

    def create(self, cr, uid, dados, context={}):
        res = super(sped_documentoitem, self).create(cr, uid, dados, context=context)

        self.pool.get('sped.documentoitem').ajusta_estoque(cr, uid, [res])
        #self.ajusta_custo(cr, uid, res)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sped_documentoitem, self).write(cr, uid, ids, dados, context=context)

        if not 'ajusta_estoque' in context:
            self.pool.get('sped.documentoitem').ajusta_estoque(cr, uid, ids)
            #self.ajusta_custo(cr, uid, ids)

        return res

    def ajusta_estoque(self, cr, uid, ids):
        move_pool = self.pool.get('stock.move')
        item_pool = self.pool.get('sped.documentoitem')
        custo_pool = self.pool.get('product.custo')

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for item_obj in item_pool.browse(cr, uid, ids):
            if (item_obj.documento_id.numero > 0) and (item_obj.documento_id.modelo in ['55', '01', '2D']) and (item_obj.stock_location_id and item_obj.stock_location_dest_id):
                if item_obj.documento_id.modelo == '55' and item_obj.documento_id.emissao == '0' and item_obj.documento_id.state != 'autorizada':
                    continue

                if item_obj.documento_id.modelo == '2D' and item_obj.documento_id.emissao == '0' and item_obj.documento_id.state != 'autorizada':
                    continue

                qtd = item_obj.quantidade_estoque

                if item_obj.documento_id.modelo == '55':
                    nome = u'Item da NF-e ' + formata_valor(item_obj.documento_id.numero, casas_decimais=0) + u' do dia ' + parse_datetime(item_obj.documento_id.data_emissao).date().strftime('%d/%m/%Y')
                elif item_obj.documento_id.modelo == '01':
                    nome = u'Item da NF ' + formata_valor(item_obj.documento_id.numero, casas_decimais=0) + u' do dia ' + parse_datetime(item_obj.documento_id.data_emissao).date().strftime('%d/%m/%Y')
                elif item_obj.documento_id.modelo == '2D':
                    nome = u'Item do CF ' + formata_valor(item_obj.documento_id.numero, casas_decimais=0) + u' do dia ' + parse_datetime(item_obj.documento_id.data_emissao).date().strftime('%d/%m/%Y')

                dados = {
                    'origin': nome,
                    'name': nome,
                    'partner_id': item_obj.documento_id.partner_id.id,
                    'sped_documentoitem_id': item_obj.id,
                    'product_id': item_obj.produto_id.id,
                    'product_qty': qtd,
                    'product_uom': item_obj.uom_id.id,
                    'location_id': item_obj.stock_location_id.id,
                    'location_dest_id': item_obj.stock_location_dest_id.id,
                    'company_id': item_obj.documento_id.company_id.id,
                }

                if item_obj.stock_move_picking_id:
                    if not item_obj.stock_move_picking_id.quantidade_original:
                        item_obj.stock_move_picking_id.write({'quantidade_original': item_obj.stock_move_picking_id.product_qty})
                        item_obj.stock_move_picking_id.quantidade_original = item_obj.stock_move_picking_id.product_qty
                        dados['quantidade_original'] = item_obj.stock_move_picking_id.product_qty
                    else:
                        dados['quantidade_original'] = item_obj.stock_move_picking_id.quantidade_original

                    dados['picking_id'] = item_obj.stock_move_picking_id.picking_id.id
                    dados['purchase_line_id'] = item_obj.stock_move_picking_id.purchase_line_id.id

                dados['state'] = 'done'
                if item_obj.stock_move_id:
                    #dados['state'] = 'done'
                    move_id = item_obj.stock_move_id.id
                    move_pool.write(cr, uid, [move_id], dados)

                else:
                    #dados['state'] = 'assigned'
                    move_id = move_pool.create(cr, uid, dados)
                    item_obj.write({'stock_move_id': move_id}, context={'ajusta_estoque': True, 'calcula_custo': False})

                #
                # Ajusta o picking para a nova quantidade, ou marca como concluído
                #
                if item_obj.stock_move_picking_id and dados['state'] == 'assigned':
                    #
                    # Recebeu a quantidade correta, encerrar o picking
                    #
                    if qtd >= item_obj.stock_move_picking_id.product_qty:
                        item_obj.stock_move_picking_id.write({'product_qty': 0, 'state': 'done'})
                    else:
                        item_obj.stock_move_picking_id.write({'product_qty': item_obj.stock_move_picking_id.product_qty - qtd})

                    move_pool.write(cr, uid, move_id, {'state': 'done'})

                sql_busca_custo = """
                select
                    pc.id
                from
                    product_custo pc
                where
                        pc.company_id = {company_id}
                    and pc.location_id = {location_id}
                    and pc.product_id = {product_id};
                """

                filtro_custo = {
                    'company_id': item_obj.documento_id.company_id.id,
                    'product_id': item_obj.produto_id.id,
                    'location_id': item_obj.stock_location_id.id,
                }

                sql = sql_busca_custo.format(**filtro_custo)
                cr.execute(sql)
                ja_existe = cr.fetchall()

                if not len(ja_existe):
                    dados_custo = {
                        'company_id': item_obj.documento_id.company_id.id,
                        'product_id': item_obj.produto_id.id,
                        'location_id': item_obj.stock_location_id.id,
                    }
                    custo_pool.create(cr, uid, dados_custo)

                filtro_custo = {
                    'company_id': item_obj.documento_id.company_id.id,
                    'product_id': item_obj.produto_id.id,
                    'location_id': item_obj.stock_location_dest_id.id,
                }

                sql = sql_busca_custo.format(**filtro_custo)
                cr.execute(sql)
                ja_existe = cr.fetchall()

                if not len(ja_existe):
                    dados_custo = {
                        'company_id': item_obj.documento_id.company_id.id,
                        'product_id': item_obj.produto_id.id,
                        'location_id': item_obj.stock_location_dest_id.id,
                    }
                    custo_pool.create(cr, uid, dados_custo)

    def ajusta_custo(self, cr, uid, ids):
        custo_pool = self.pool.get('product.custo')
        item_pool = self.pool.get('sped.documentoitem')

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        for item_obj in item_pool.browse(cr, uid, ids):
            vr_custo = D(str(item_obj.vr_custo))
            quantidade_estoque = D(str(item_obj.quantidade_estoque))
            vr_unitario_custo = vr_custo / quantidade_estoque

            #
            # O item foi lançado no estoque, isso quer dizer
            # que vai haver custo médio
            #
            if item_obj.stock_move_id:
                quantidade_por_local = D(str(item_obj.produto_id.get_product_available(context={'location': item_obj.stock_move_id.location_dest_id.id, 'states': ['done'], 'what': ['in', 'out']})))

                print('quantidade por local', quantidade_por_local)

                quantidade_existente = D(str(quantidade_por_local.get(item_obj.produto_id.id, 0.00)))

                #
                # A própria quantidade do item atual está no estoque
                #
                if item_obj.stock_move_id.state == 'done':
                    quantidade_existente -= item_obj.stock_move_id.product_qty

                custo_ids = custo_pool.search(cr, uid, [('company_id', '=', item_obj.company_id.id), ('product_id', '=', item_obj.produto_id.id), ('location_id', '=', item_obj.stock_move_id.location_dest_id.id)])

                vr_unitario_custo_anterior = D(str(0))
                custo_obj = False
                if custo_ids:
                    custo_obj = custo_pool.browse(cr, uid, custo_ids[0])
                    vr_unitario_custo_anterior = D(str(custo_obj.vr_unitario))

                custo_atual = quantidade_existente * vr_unitario_custo_anterior
                custo_atual += quantidade_estoque * vr_unitario_custo
                vr_unitario_custo_atual = custo_atual / (quantidade_existente + quantidade_estoque)

                #
                # A própria quantidade do item atual está no estoque
                #
                if item_obj.stock_move_id.state == 'done':
                    quantidade_existente += D(str(item_obj.stock_move_id.product_qty))

                if custo_obj:
                    custo_obj.write({'vr_unitario': vr_unitario_custo_atual, 'quantidade': quantidade_existente, 'vr_total': quantidade_existente *  vr_unitario_custo_atual})
                else:
                    dados = {
                        'company_id': item_obj.company_id.id,
                        'product_id': item_obj.produto_id.id,
                        'location_id': item_obj.stock_move_id.location_dest_id.id,
                        'quantidade': quantidade_existente,
                        'vr_unitario': vr_unitario_custo_atual,
                        'vr_total': quantidade_existente * vr_unitario_custo_atual,
                    }
                    custo_pool.create(cr, uid, dados)

            else:
                custo_ids = custo_pool.search(cr, uid, [('company_id', '=', item_obj.company_id.id), ('product_id', '=', item_obj.produto_id.id)])

                if custo_ids:
                    custo_obj = custo_pool.browse(cr, uid, custo_ids)[0]
                    if custo_obj.data < item_obj.documento_id.data_emissao:
                        custo_obj.write({'vr_unitario': vr_unitario_custo, 'data': item_obj.documento_id.data_emissao})
                else:
                    dados = {
                        'data': item_obj.documento_id.data_emissao,
                        'company_id': item_obj.company_id.id,
                        'product_id': item_obj.produto_id.id,
                        'vr_unitario': vr_unitario_custo,
                    }
                    custo_pool.create(cr, uid, dados)

    #def onchange_produto(self, cr, uid, ids, produto_id, context):
        #res = super(sped_documentoitem, self).onchange_produto(cr, uid, ids, produto_id, context)

        #company_id = context['default_company_id']
        #partner_id = context['default_partner_id']
        #operacao_id = context['default_operacao_id']
        #entrada_saida = context['default_entrada_saida']
        #regime_tributario = context['default_regime_tributario']
        #emissao = context['default_emissao']
        #data_emissao = context.get('default_data_emissao', None)
        #municipio_fato_gerador_id = context.get('default_municipio_fato_gerador_id', None)
        #contribuinte = context.get('default_contribuinte', '1')
        #modelo = context.get('default_modelo', '55')

        ##
        ## O tipo do contribuinte só tem nexo para NF-e modelo 55
        ## nos demais casos, definir fixo como '1'
        ##
        #if modelo != '55' or emissao != '0':
            #contribuinte = '1'

        ##
        ## Vamos trazer todos os registros necessários
        ##
        #company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        #partner_obj = self.pool.get('res.partner').browse(cr, uid, partner_id)
        #operacao_obj = self.pool.get('sped.operacao').browse(cr, uid, operacao_id)
        #produto_obj = self.pool.get('product.product').browse(cr, uid, produto_id)

        #if municipio_fato_gerador_id:
            #municipio_fato_gerador_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_fato_gerador_id)
        #else:
            #municipio_fato_gerador_obj = partner_obj.municipio_id

        ##
        ## Achamos a família tributária do ICMS, que vai determinar
        ## as alíquotas do ICMS e a CFOP
        ##
        #if produto_obj.familiatributaria_id:
            #familiatributaria_obj = produto_obj.familiatributaria_id
        #elif company_obj.familiatributaria_id:
            #familiatributaria_obj = company_obj.familiatributaria_id
        #else:
            #raise osv.except_osv(u'Erro!', u'Não há família tributária padrão, nem família tributária definida no produto/serviço “%s”!' % produto_obj.name)

        ##
        ## Guarda a família tributária original
        ##
        #familiatributaria_original_obj = familiatributaria_obj

        #try:
            #uf_origem = company_obj.partner_id.municipio_id.estado_id.uf
        #except:
            #raise osv.except_osv(u'Erro!', u'Não há município para a empresa “' + company_obj.name + u'”')

        #try:
            #uf_destino = partner_obj.municipio_id.estado_id.uf
        #except:
            #raise osv.except_osv(u'Erro!', u'Não há município para o cliente “' + partner_obj.name + u'”')

        #dentro_estado = uf_origem == uf_destino
        #fora_estado = uf_origem != uf_destino
        #fora_pais = uf_destino == 'EX'

        ##
        ## E vamos localizar o item da operação com a CFOP correta para o caso
        ##
        #lista_operacaoitem_ids = self.pool.get('sped.operacaoitem').search(
            #cr,
            #uid,
            #[
                #('operacao_id', '=', operacao_obj.id),
                #('familiatributaria_id', '=', familiatributaria_obj.id),
                #('cfop_id.dentro_estado', '=', dentro_estado),
                #('cfop_id.fora_estado', '=', fora_estado),
                #('cfop_id.fora_pais', '=', fora_pais),
                #'|', ('contribuinte', '=', contribuinte), ('contribuinte', '=', None),
            #]
        #)

        ##
        ## Caso não haja um item da operação específico para a família, busca
        ## o genérico (item da operação sem família)
        ##
        #if len(lista_operacaoitem_ids) == 0:
            #lista_operacaoitem_ids = self.pool.get('sped.operacaoitem').search(
                #cr,
                #uid,
                #[
                    #('operacao_id', '=', operacao_obj.id),
                    #('familiatributaria_id', '=', None),
                    #('cfop_id.dentro_estado', '=', dentro_estado),
                    #('cfop_id.fora_estado', '=', fora_estado),
                    #('cfop_id.fora_pais', '=', fora_pais),
                    #'|', ('contribuinte', '=', contribuinte), ('contribuinte', '=', None),
                #]
            #)

        #if len(lista_operacaoitem_ids) == 0 or len(lista_operacaoitem_ids) > 1:
            #if len(lista_operacaoitem_ids) == 0:
                #mensagem = u'Não há um item da operação “%s” configurado para o produto “%s”, família tributária “%s”,' % (operacao_obj.nome, produto_obj.name, familiatributaria_obj.descricao)
            #else:
                #mensagem = u'Há mais de um item da operação “%s” configurado para o produto “%s”, família tributária “%s”,' % (operacao_obj.nome, produto_obj.name, familiatributaria_obj.descricao)

            #if contribuinte == '1':
                #mensagem += ' para contribuinte com IE '
            #elif contribuinte == '2':
                #mensagem += ' para contribuinte isento '
            #elif contribuinte == '9':
                #mensagem += ' para estrangeiro '

            #if dentro_estado:
                #mensagem += 'com CFOP para dentro do estado!'
            #elif fora_estado:
                #mensagem += 'com CFOP para fora do estado!'
            #else:
                #mensagem += 'com CFOP para fora do país!'

            #raise osv.except_osv(u'Erro!', mensagem)

        #lista_operacaoitem_id = lista_operacaoitem_ids[0]
        #operacao_item_obj = self.pool.get('sped.operacaoitem').browse(cr, uid, lista_operacaoitem_id)

        #valores = res['value']
        #if operacao_item_obj.stock_location_id:
            #valores['stock_location_id'] = operacao_item_obj.stock_location_id.id

        #if operacao_item_obj.stock_location_dest_id:
            #valores['stock_location_dest_id'] = operacao_item_obj.stock_location_dest_id.id

        #if operacao_obj.traz_custo_medio:
            #vr_unitario = D(produto_obj.standard_price)
            #if operacao_item_obj.stock_location_id:
                ##
                ## Busca o custo unitário médio do produto no momento
                ##
                #for custo_obj in produto_obj.custo_ids:
                    #if custo_obj.company_id.id == company_id and custo_obj.location_id.id == operacao_item_obj.stock_location_id.id:
                        #vr_unitario = D(custo_obj.vr_unitario)

            #valores['vr_unitario'] = vr_unitario

        #return res

    def action_calcula_item(self, cr, uid, ids, context=None):
        retorno = {}
        for item_obj in self.browse(cr, uid, ids):
            dados = calcula_item(self, cr, uid, item_obj)
            retorno[item_obj.id] = self.pool.get('sped.documentoitem').write(cr, uid, [item_obj.id], dados)

        return retorno

    def unlink(self, cr, uid, ids, context={}):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        #
        # Exclui as movimentações de estoque antes
        #
        for item_obj in self.browse(cr, uid, ids):
            if item_obj.stock_move_id:
                #
                # Quando houver vínculo com uma lista de separação, não excluir, apenas desvincular do item da NF
                #
                if item_obj.stock_move_id.picking_id:
                    cr.execute("update stock_move set sped_documentoitem_id = null where id = {move_id};".format(move_id=item_obj.stock_move_id.id))
                    cr.execute("update sped_documentoitem set stock_move_id = null where id = {item_id};".format(item_id=item_obj.id))

                else:
                    cr.execute("update stock_move set state='draft' where id = {move_id};".format(move_id=item_obj.stock_move_id.id))
                    cr.execute('delete from stock_move where id = {move_id}'.format(move_id=item_obj.stock_move_id.id))

        return super(sped_documentoitem, self).unlink(cr, uid, ids, context=context)


sped_documentoitem()
