# -*- coding: utf-8 -*-

import unicodedata
from osv import osv, fields
from openerp import SUPERUSER_ID
from orcamento_categoria_view_sale import CABECALHO_FORM as CABECALHO_FORM_SALE
from orcamento_categoria_view_sale import RODAPE_FORM as RODAPE_FORM_SALE
from orcamento_categoria_view_sale import CORPO_FORM as CORPO_FORM_SALE
from orcamento_categoria_view_stock import CABECALHO_FORM as CABECALHO_FORM_STOCK
from orcamento_categoria_view_stock import RODAPE_FORM as RODAPE_FORM_STOCK
from orcamento_categoria_view_stock import CORPO_FORM as CORPO_FORM_STOCK


SUFIXO_SALE = '_sale_ids'
SUFIXO_STOCK = '_stock_ids'


def cria_nome_campo(valor, sufixo=SUFIXO_SALE):
    nome_campo = 'x_' + valor.lower()
    nome_campo = nome_campo.replace(' ', '_').replace('-', '_')
    #
    # Remove acentos e outros caracteres especiais do nome
    #
    nome_campo = unicodedata.normalize('NFD', unicode(nome_campo)).encode('ascii', 'ignore')
    nome_campo += sufixo
    return nome_campo


class orcamento_categoria(osv.osv):
    _name = 'orcamento.categoria'
    _description = u'Categoria de orçamento'
    _columns = {
        'ordem': fields.integer(u'Ordem no orçamento'),
        'nome': fields.char('Nome', size=64),
        'margem': fields.float(u'Margem (%)'),
        'meses_retorno_investimento': fields.float(u'Meses para retorno do investimento'),
        'valida_preco_minimo': fields.boolean(u'Valida preço mímino menor que custo?'),
        'abate_custo_comissao': fields.boolean(u'Abate o valor de custo na comissão de venda?'),
        'abate_impostos_comissao': fields.float(u'% de impostos a abater sobre a venda na comissão'),
        'comissao_venda_id': fields.many2one('orcamento.comissao', u'Tabela de comissão para venda'),
        'comissao_locacao_id': fields.many2one('orcamento.comissao', u'Tabela de comissão para locação'),
        'considera_venda': fields.boolean(u'Considerar itens para venda no total?'),
    }

    _defaults = {
        'valida_preco_minimo': False,
        'considera_venda': True,
    }

    _rec_name = 'nome'
    _order = 'ordem,nome'

    def ajusta_parametro_views(self):
        self.cabecalho_form_sale = CABECALHO_FORM_SALE
        self.rodape_form_sale = RODAPE_FORM_SALE
        self.corpo_form_sale = CORPO_FORM_SALE

        self.cabecalho_form_stock = CABECALHO_FORM_STOCK
        self.rodape_form_stock = RODAPE_FORM_STOCK
        self.corpo_form_stock = CORPO_FORM_STOCK

        self.sufixo_sale = SUFIXO_SALE
        self.sufixo_stock = SUFIXO_STOCK

        print('ajustou view aqui 1')

    def unlink(self, cr, uid, ids, context=None):
        res = super(orcamento_categoria, self).unlink(
            cr, uid, ids, context=context)

        self.ajusta_parametro_views()
        self.recria_view_sale(cr, uid)
        #self.recria_view_stock(cr, uid)

        return res

    def create(self, cr, uid, vals, context=None):
        res = super(orcamento_categoria, self).create(
            cr, uid, vals, context=context)
        vals['id'] = res
        #
        # Cria campos dinâmicos
        #
        self.ajusta_parametro_views()
        self.recria_view_sale(cr, uid)
        #self.recria_view_stock(cr, uid)

        return res

    def write(self, cr, uid, ids, vals, context=None):
        categoria_obj = self.pool.get('orcamento.categoria').browse(cr, uid, ids[0])

        res = super(orcamento_categoria, self).write(
            cr, uid, ids, vals, context=context)
        vals['id'] = ids[0]

        vals['nome'] = vals.get('nome', categoria_obj.nome or '')
        #
        # Cria campos dinâmicos
        #
        self.ajusta_parametro_views()
        self.recria_view_sale(cr, uid)
        #self.recria_view_stock(cr, uid)

        return res

    def _cria_campo_orcamento(self, cursor_id, user_id, nome_campo, dados_novo_campo, modelo='sale.order'):
        #
        # Verificamos se o campo já existe
        #
        field_ids = self.pool.get('ir.model.fields').search(
            cursor_id, SUPERUSER_ID, [('model', '=', modelo), ('name', '=', nome_campo)])

        if field_ids:
            return field_ids[0]

        #
        # O campo precisa ser criado
        #

        #
        # Pega o ID do modelo orçamento
        #
        orcamento_model_id = self.pool.get('ir.model').search(
            cursor_id, SUPERUSER_ID, [('model', '=', modelo)])[0]

        dados_novo_campo['model_id'] = orcamento_model_id

        field_id = self.pool.get('ir.model.fields').create(cursor_id, SUPERUSER_ID, dados_novo_campo)

        return field_id

    def _cria_campos_orcamento_item_ids(self, cursor_id, user_id, categoria_nome, categoria_id):
        #
        # Primeiro, determinamos o nome do novo campo
        #
        nome_campo = cria_nome_campo(categoria_nome)

        dados_novo_campo = {
            'model': 'sale.order',
            'model_id': None,
            'name': nome_campo,
            'relation': 'sale.order.line',
            'relation_field': 'order_id',
            'field_description': categoria_nome,
            'ttype': 'one2many',
            'state': 'manual',
            'select_level': '0',
            'view_load': False,
            'relate': False,
            'translate': False,
            'selectable': True,
            'required': False,
            'readonly': False,
        }

        field_id = self._cria_campo_orcamento(cursor_id, user_id, nome_campo, dados_novo_campo)

        #
        # Agora nós atualizamos o domain/filtro do campo
        #
        self.pool.get('ir.model.fields').write(cursor_id, SUPERUSER_ID, [field_id],
            {
                'domain': "[('orcamento_categoria_id', '=', %s)]" % unicode(categoria_id),
            }
        )

        #
        # E, por fim, os campos no itens de estoque
        #
        nome_campo = cria_nome_campo(categoria_nome, sufixo=self.sufixo_stock)
        dados_novo_campo['name'] = nome_campo
        dados_novo_campo['model'] = 'stock.picking'
        dados_novo_campo['relation'] = 'stock.move'
        dados_novo_campo['relation_field'] = 'picking_id'

        field_id = self._cria_campo_orcamento(cursor_id, user_id, nome_campo, dados_novo_campo, modelo='stock.picking')

        #
        # Agora nós atualizamos o domain/filtro do campo
        #
        self.pool.get('ir.model.fields').write(cursor_id, SUPERUSER_ID, [field_id],
            {
                'domain': "[('orcamento_categoria_id', '=', %s)]" % unicode(categoria_id),
            }
        )

    def recria_view_categoria_orcamento(self, cursor_id, user_id, view_original_obj,
            view_dinamica_nome, modelo, cabecalho_form, rodape_form, corpo_form, sufixo=SUFIXO_SALE):
        ir_ui_view_pool = self.pool.get('ir.ui.view')

        #
        # Já existe o form auto-gerado?
        #
        view_dinamica_ids = ir_ui_view_pool.search(cursor_id, SUPERUSER_ID, [('name', '=', view_dinamica_nome), ('inherit_id', '=', view_original_obj.id)])

        if view_dinamica_ids:
            view_dinamica_obj = ir_ui_view_pool.browse(cursor_id, SUPERUSER_ID, view_dinamica_ids[0])

        else:
            #
            # Se não, criamos o registro correspondente
            #
            dados = {
                'name': view_dinamica_nome,
                'model': modelo,
                'type': 'form',
                'arch': u'<?xml version="1.0"?><group string="categoria_orcamento" position="replace"></group>',
                'priority': 20,
                'inherit_id': view_original_obj.id,
            }
            view_dinamica_id = ir_ui_view_pool.create(cursor_id, SUPERUSER_ID, dados)
            view_dinamica_obj = ir_ui_view_pool.browse(cursor_id, SUPERUSER_ID, view_dinamica_id)

        #
        # Constrói o xml da view
        #
        view_dinamica_arch = cabecalho_form

        orcamento_categoria_pool = self.pool.get('orcamento.categoria')
        categoria_ids = orcamento_categoria_pool.search(cursor_id, user_id, [])

        for categoria_id in categoria_ids:
            categoria_obj = orcamento_categoria_pool.browse(cursor_id, user_id, categoria_id)

            if categoria_obj.ordem < 1000:
                self._cria_campos_orcamento_item_ids(cursor_id, user_id, categoria_obj.nome, categoria_obj.id)
                nome_campo = cria_nome_campo(categoria_obj.nome, sufixo=sufixo)
                view_dinamica_arch += corpo_form.format(
                    **{
                        'categoria_nome': categoria_obj.nome,
                        'nome_campo': nome_campo,
                        'categoria_id': categoria_id,
                    })

        view_dinamica_arch += rodape_form

        #
        # Atualizamos agora o form dinâmico
        #
        ir_ui_view_pool.write(cursor_id, SUPERUSER_ID, view_dinamica_obj.id,
            {
                'arch': view_dinamica_arch
            }
        )

    def recria_view_sale(self, cursor_id, user_id):
        ir_ui_view_pool = self.pool.get('ir.ui.view')
        #
        # Buscamos a view original de que a view dinâmica é herdada
        #
        sale_original_ids = ir_ui_view_pool.search(cursor_id, SUPERUSER_ID, [('name', '=', 'sale.order.form'), ('inherit_id', '=', None)])

        #
        # Só pode voltar uma view
        #
        if not sale_original_ids:
            return

        view_original_ids = ir_ui_view_pool.search(cursor_id, SUPERUSER_ID, [('name', '=', 'orcamento.sale_order_form'), ('inherit_id', '=', sale_original_ids[0])])

        #
        # Só pode voltar uma view
        #
        if not view_original_ids:
            return

        view_original_obj = ir_ui_view_pool.browse(cursor_id, SUPERUSER_ID, view_original_ids[0])

        self.recria_view_categoria_orcamento(cursor_id, user_id,
            view_original_obj,
            'orcamento.sale_order_form_dinamico',
            'sale.order',
            self.cabecalho_form_sale,
            self.rodape_form_sale,
            self.corpo_form_sale,
            sufixo=self.sufixo_sale
            )

    def recria_view_stock(self, cursor_id, user_id):
        ir_ui_view_pool = self.pool.get('ir.ui.view')
        #
        # Buscamos a view original; no caso do estoque, temos que alterar a view original mesmo
        #
        stock_original_ids = ir_ui_view_pool.search(cursor_id, SUPERUSER_ID, [('name', '=', 'stock.picking.out.form'), ('inherit_id', '=', None)])

        #
        # Só pode voltar uma view
        #
        if not stock_original_ids:
            return

        view_original_obj = ir_ui_view_pool.browse(cursor_id, SUPERUSER_ID, stock_original_ids[0])

        #
        # Constrói o xml da view
        #
        view_dinamica_arch = '' + self.cabecalho_form_stock

        orcamento_categoria_pool = self.pool.get('orcamento.categoria')
        categoria_ids = orcamento_categoria_pool.search(cursor_id, user_id, [])

        for categoria_id in categoria_ids:
            categoria_obj = orcamento_categoria_pool.browse(cursor_id, user_id, categoria_id)
            if categoria_obj.ordem < 1000:
                self._cria_campos_orcamento_item_ids(cursor_id, user_id, categoria_obj.nome, categoria_obj.id)
                nome_campo = cria_nome_campo(categoria_obj.nome, sufixo=self.sufixo_stock)
                view_dinamica_arch += self.corpo_form_stock.format(
                    **{
                        'categoria_nome': categoria_obj.nome,
                        'nome_campo': nome_campo,
                        'categoria_id': categoria_id,
                    })

        view_dinamica_arch += self.rodape_form_stock

        #
        # Atualizamos agora o form dinâmico
        #
        ir_ui_view_pool.write(cursor_id, SUPERUSER_ID, view_original_obj.id,
            {
                'arch': view_dinamica_arch
            }
        )


orcamento_categoria()
