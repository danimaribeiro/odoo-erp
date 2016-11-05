# -*- encoding: utf-8 -*-
import os
import base64
from osv import osv, fields
from finan.wizard.finan_relatorio import Report
from pybrasil.data import hoje, formata_data, dia_da_semana_por_extenso, data_por_extenso
from pybrasil.valor import valor_por_extenso_unidade
from pybrasil.base import DicionarioBrasil
from pybrasil.valor.decimal import Decimal as D

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class sale_order(osv.Model):
    _inherit = 'sale.order'
    _name = 'sale.order'

    def _get_codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for sale_obj in self.browse(cr, uid, ids):
            codigo = sale_obj.pricelist_id.proposta_sigla or u''
            codigo += '-'
            codigo += sale_obj.name or u''
            codigo += sale_obj.pricelist_id.proposta_sufixo or u''

            res[sale_obj.id] = codigo

        return res

    _columns = {
        'codigo_di': fields.function(_get_codigo, type='char', string=u'Código', store=True, select=True),
        'stage_id': fields.many2one('crm.case.stage', u'Estágio'),

        'mostrar_valores': fields.boolean(u'Mostrar valores e quantidades?'),
        'mostrar_valores_opcionais': fields.boolean(u'Mostrar valores e quantidades somente dos acessórios opcionais?'),
        'mostrar_sub': fields.boolean(u'Mostrar Sub-total'),
        'mostrar_unitario': fields.boolean(u'Mostrar valor unitário?'),

        'representacao': fields.boolean(u'Representação'),

        'create_uid': fields.many2one('res.users', u'Usuário'),

        'prazo_entrega': fields.integer(u'Prazo de entrega'),
        'garantia': fields.integer(u'Garantia (meses)'),
    }

    _defaults = {
        'prazo_entrega': 100,
        'garantia': 3,
        'mostrar_unitario': True,
    }

    def imprime_proposta(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        pedido_obj = self.browse(cr, uid, id)

        #
        # Prepara alguns campos para passar como parâmetro
        #
        # Registros na ANVISA, garantia e prazo de entrega
        #
        registro_anvisa = u''
        pais_origem = u''
        com_kit = False
        for item_obj in pedido_obj.item_principal_ids:
            if (not item_obj.parent_id) and 'KIT ' in item_obj.product_id.name.upper():
                com_kit = True


            if item_obj.product_id.registro_anvisa:
                if len(registro_anvisa):
                    registro_anvisa += u', '

                registro_anvisa += item_obj.product_id.registro_anvisa

            if item_obj.product_id.sped_pais_id:
                po = item_obj.product_id.sped_pais_id.nome

                if po not in pais_origem:
                    if len(pais_origem):
                        pais_origem += ', '

                    pais_origem += po

        if pedido_obj.prazo_entrega:
            prazo_entrega = str(pedido_obj.prazo_entrega) + u' dias'
        else:
            prazo_entrega = u'100 dias'

        if pedido_obj.garantia:
            garantia = str(pedido_obj.garantia) + u' meses'
        else:
            garantia = u'90 dias'

        #if pedido_obj.pricelist_id.modelo == 'MA':
        rel = Report('Proposta de Venda Maquet', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'di_proposta_venda_maquet.jrxml')

        #elif pedido_obj.pricelist_id.modelo == 'WE':
            #rel = Report('Proposta de Venda Weinmann', cr, uid)
            #rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'di_proposta_venda_weinmann.jrxml')

        #elif pedido_obj.pricelist_id.modelo == 'PU':
            #rel = Report('Proposta de Venda Pulsion', cr, uid)
            #rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'di_proposta_venda_pulsion.jrxml')

        rel.outputFormat = 'pdf'
        recibo = 'proposta_'+ pedido_obj.name + '.pdf'

        rel.parametros['REGISTRO_IDS'] = '(' + str(id) + ')'
        rel.parametros['GARANTIA'] = garantia
        rel.parametros['PRAZO_ENTREGA'] = prazo_entrega
        rel.parametros['REGISTRO_ANVISA'] = registro_anvisa
        rel.parametros['PAIS_ORIGEM'] = pais_origem

        if pedido_obj.mostrar_valores:
            rel.parametros['MOSTRAR_VALORES'] = True
            rel.parametros['MOSTRAR_VALORES_OPCIONAIS'] = False
        elif pedido_obj.mostrar_valores_opcionais:
            rel.parametros['MOSTRAR_VALORES'] = False
            rel.parametros['MOSTRAR_VALORES_OPCIONAIS'] = True

        if pedido_obj.mostrar_sub:
            rel.parametros['MOSTRAR_SUB'] = True

        if pedido_obj.mostrar_unitario:
            rel.parametros['MOSTRAR_UNITARIO'] = True

        if not com_kit:
            rel.parametros['SEM_ACESSORIO'] = True
            for item_obj in pedido_obj.order_line:
                if item_obj.parent_id:
                    rel.parametros['SEM_ACESSORIO'] = False
                    break

        else:
            rel.parametros['SEM_ACESSORIO'] = False
            rel.parametros['COM_KIT'] = True

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', id), ('name', '=', recibo)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, 1, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': recibo,
            'datas_fname': recibo,
            'res_model': 'sale.order',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True

    def imprime_pedido_venda(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        pedido_obj = self.browse(cr, uid, id)
          
        dados = {
            'pedido_obj': pedido_obj,             
            'data': dia_da_semana_por_extenso(pedido_obj.date_order) + u', ' +  data_por_extenso(pedido_obj.date_order),                    
            'empresa': pedido_obj.company_id.partner_id,
            'cliente': pedido_obj.partner_id,     
            'linhas': pedido_obj.order_line,           
            #'produtos_objs': sale_obj.order_line,           
        }

        nome_arquivo = JASPER_BASE_DIR + 'di_pedido_venda.ods'

        planilha = self.pool.get('lo.modelo').gera_modelo_novo_avulso(cr, uid, nome_arquivo, dados)
        
        nome = u'pedido_venda.xlsx'
                
        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'sale.order'), ('res_id', '=', id), ('name', '=', nome)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, 1, attachment_ids)

        dados = {
            'datas': planilha,
            'name': nome,
            'datas_fname': nome,
            'res_model': 'sale.order',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)

        return True


    def create(self, cr, uid, dados, context={}):
        if 'name' in dados and dados['name']:
            if 'pricelist_id' in dados:
                lista_obj = self.pool.get('product.pricelist').browse(cr, uid, dados['pricelist_id'])

        res = super(sale_order, self).create(cr, uid, dados, context=context)
        #self.pool.get('sale.order')._calcula_comissao(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(sale_order, self).write(cr, uid, ids, dados, context=context)
        #self.pool.get('sale.order')._calcula_comissao(cr, uid, ids)

        return res

    ##def _calcula_comissao(self, cr, uid, ids):
        ##sql = '''
        ##update sale_order ped set vr_comissao = (
        ##select sum(
            ##coalesce(peditem.price_unit, 0) * coalesce(peditem.product_uom_qty, 1) *
            ##case
                ##when pped.comissao is not null and pped.comissao > 0 then pped.comissao
                ##else coalesce(prod.comissao, 0)
            ##end / 100.00
            ##)

        ##from
            ##sale_order_line peditem
            ##join sale_order pped on pped.id = peditem.order_id
            ##join product_product prod on prod.id = peditem.product_id

        ##where
            ##peditem.order_id = ped.id
        ##)

        ##where ped.id = {pedido_id};
        ##'''

        ##for id in ids:
            ##cr.execute(sql.format(pedido_id=id))

    def action_wait(self, cr, uid, ids, context={}):
        print('vai fazer')
        #
        # Antes de confirmar a liberação do pedido, verificamos as validações de permissão
        # da locação e venda
        #

        sale_pool = self.pool.get('sale.order')

        sale_obj = sale_pool.browse(cr, uid, ids[0])

        if not sale_obj.representacao:
            res = super(sale_order, self).action_wait(cr, uid, ids, context=context)

        elif sale_obj.payment_term:
            #
            # Vamos criar as parcelas da comissão no contas a receber
            #
            payment_term_obj = sale_obj.payment_term
            lista_vencimentos = payment_term_obj.compute(sale_obj.comissao_revenda, date_ref=str(hoje()))
            comissao_revenda_ids = []

            dados = {
                'tipo': 'R',
                'company_id': sale_obj.company_id.id,
                'partner_id': sale_obj.pricelist_id.fornecedor_id.id,
                'data_documento': str(hoje()),
                'data_vencimento': False,
                'valor_documento': 0,
                'conta_id': sale_obj.operacao_fiscal_produto_id.finan_conta_id.id,
                'documento_id': self.pool.get('finan.documento')._cria_id_novo(cr, 1, 'COMISSÃO REPRESENTAÇÃO'),
                'sale_order_id': sale_obj.id,
                'comissao_revenda_id': False,
            }

            if sale_obj.pricelist_id.currency_id.id != 6:
                dados['currency_id'] = sale_obj.pricelist_id.currency_id.id

            lancamento_pool = self.pool.get('finan.lancamento')

            #
            # Vamos criar agora, os lançamentos a pagar das comissões do empresa
            #
            i = 1
            for data, valor in lista_vencimentos:
                dados['data_vencimento'] = data
                dados['valor_documento'] = valor
                dados['numero_documento'] = u'CRv-' + sale_obj.name
                dados['numero_documento'] += u'-' + str(i).zfill(2) + u'/' + str(len(lista_vencimentos)).zfill(2)

                if 'currency_id' in dados:
                    dados['valor_documento_moeda'] = valor

                i += 1

                lanc_id = lancamento_pool.create(cr, uid, dados)
                comissao_revenda_ids.append(lanc_id)

            #
            # Vamos criar agora, os lançamentos a pagar das comissões do vendedor
            #
            vendedor_ids = self.pool.get('res.partner').search(cr, uid, [('name', '=', sale_obj.user_id.name)])

            if not len(vendedor_ids):
                dados = {
                    'name': sale_obj.user_id.name,
                }
                vendedor_id = self.pool.get('res.partner').create(cr, uid, dados)
            else:
                vendedor_id = vendedor_ids[0]

            lista_vencimentos = payment_term_obj.compute(sale_obj.comissao_vendedor, date_ref=str(hoje()))
            dados['tipo'] = 'P'
            dados['partner_id'] = vendedor_id
            dados['documento_id'] = self.pool.get('finan.documento')._cria_id_novo(cr, 1, 'COMISSÃO VENDEDOR')

            if sale_obj.pricelist_id.currency_id.id != 6:
                dados['currency_id'] = sale_obj.pricelist_id.currency_id.id

            i = 1
            for data, valor in lista_vencimentos:
                dados['data_vencimento'] = data
                dados['valor_documento'] = valor
                dados['numero_documento'] = u'CVd-' + sale_obj.name
                dados['numero_documento'] += u'-' + str(i).zfill(2) + u'/' + str(len(lista_vencimentos)).zfill(2)
                dados['comissao_revenda_id'] = comissao_revenda_ids[i-1]

                if 'currency_id' in dados:
                    dados['valor_documento_moeda'] = valor

                i += 1

                lancamento_pool.create(cr, uid, dados)

            cr.execute("update sale_order set state = 'done', date_confirm = '{data}' where id = {id};".format(data=str(hoje()), id=sale_obj.id))

            #
            # Excluímos a lista de separação, pois não será necessária
            #
            picking_ids = self.pool.get('stock.picking').search(cr, uid, [('sale_id', '=', sale_obj.id)])
            for picking_id in picking_ids:
                cr.execute("""
                    delete from stock_move where picking_id = {id};
                    delete from stock_picking where id = {id};
                """.format(id=picking_id))

            res = False

        return res

    def action_ship_create(self, cr, uid, ids, context=None):
        for sale_obj in self.browse(cr, uid, ids, context=context):
            if not sale_obj.representacao:
                res = super(sale_order, self).action_ship_create(cr, uid, ids, context=context)
            else:
                res = False

        return res

    def copy(self, cr, uid, id, default={}, context={}):
        default['date_order'] = fields.date.today()
        res = super(sale_order, self).copy(cr, uid, id, default=default, context=context)
        return res

    def ajusta_acessorios(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('sale.order.line')

        for order_obj in self.browse(cr, uid, ids):
            for item_obj in order_obj.order_line:
                for acessorio_obj in item_obj.itens_acessorios_ids:
                    produto_obj = acessorio_obj.acessorio_id
                    quantidade = acessorio_obj.quantidade

                    contexto_item = {
                        'partner_id': order_obj.partner_id.id,
                        'quantity': quantidade,
                        'product_uom_qty': quantidade,
                        'pricelist': order_obj.pricelist_id.id,
                        'shop': order_obj.shop_id.id,
                        'uom': produto_obj.uom_id.id,
                        'force_product_uom': True,
                        'operacao_fiscal_produto_id': order_obj.operacao_fiscal_produto_id.id,
                        'operacao_fiscal_servico_id': order_obj.operacao_fiscal_servico_id.id,
                        'company_id': order_obj.company_id.id
                    }

                    if acessorio_obj.linha_acessorio_id:
                        if acessorio_obj.linha_acessorio_id.quantidade_manual:
                            continue

                        #
                        # Ajustar a quantidade para ser proporcional
                        #
                        quantidade = D(item_obj.product_uom_qty or 0) * D(acessorio_obj.linha_acessorio_id.quantidade_componente or 0)

                        if quantidade == acessorio_obj.linha_acessorio_id.product_uom_qty:
                            continue

                    dados_item = item_pool.product_id_change(cr, uid, False, order_obj.pricelist_id.id, produto_obj.id, quantidade, False, False, False, False, order_obj.partner_id.id, False, True, order_obj.date_order, False, False, False, contexto_item)

                    dados_item = dados_item['value']
                    dados_item.update({
                        'order_id': order_obj.id,
                        'product_id': acessorio_obj.acessorio_id.id,
                        'item_acessorio_id': acessorio_obj.id,
                        'parent_id': item_obj.id,
                        'quantidade_componente': acessorio_obj.quantidade,
                        'price_unit': 0,
                        'vr_unitario_venda_impostos': 0,
                        'vr_total_venda_impostos': 0,
                    })
                    dados = {}
                    for chave in dados_item:
                        if not isinstance(dados_item[chave], DicionarioBrasil):
                            dados[chave] = dados_item[chave]

                    if not acessorio_obj.linha_acessorio_id:
                        item_id = item_pool.create(cr, uid, dados)
                        acessorio_obj.write({'linha_acessorio_id': item_id})
                    else:
                        acessorio_obj.linha_acessorio_id.write(dados)

                for opcionais_obj in item_obj.itens_opcionais_ids:
                    if opcionais_obj.linha_opcional_id:
                        continue

                    produto_obj = opcionais_obj.opcional_id

                    contexto_item = {
                        'partner_id': order_obj.partner_id.id,
                        'quantity': opcionais_obj.quantidade,
                        'product_uom_qty': opcionais_obj.quantidade,
                        'pricelist': order_obj.pricelist_id.id,
                        'shop': order_obj.shop_id.id,
                        'uom': produto_obj.uom_id.id,
                        'force_product_uom': True,
                        'operacao_fiscal_produto_id': order_obj.operacao_fiscal_produto_id.id,
                        'operacao_fiscal_servico_id': order_obj.operacao_fiscal_servico_id.id,
                        'company_id': order_obj.company_id.id
                    }

                    dados_item = item_pool.product_id_change(cr, uid, False, order_obj.pricelist_id.id, produto_obj.id, opcionais_obj.quantidade, False, False, False, False, order_obj.partner_id.id, False, True, order_obj.date_order, False, False, False, contexto_item)

                    dados_item = dados_item['value']
                    dados_item.update({
                        'order_id': order_obj.id,
                        'product_id': opcionais_obj.opcional_id.id,
                        'item_opcional_id': opcionais_obj.id,
                        'eh_opcional': True,
                        'quantidade_componente': opcionais_obj.quantidade,
                        #'parent_id': item_obj.id,
                    })
                    dados = {}
                    for chave in dados_item:
                        if not isinstance(dados_item[chave], DicionarioBrasil):
                            dados[chave] = dados_item[chave]

                    if not opcionais_obj.linha_opcional_id:
                        item_id = item_pool.create(cr, uid, dados)
                        opcionais_obj.write({'linha_opcional_id': item_id})
                    else:
                        opcionais_obj.write({'linha_opcional_id': item_id})



sale_order()
