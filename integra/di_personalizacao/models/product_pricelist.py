# -*- coding: utf-8 -*-

from osv import fields, osv


MODELO_PEDIDO = (
         ('GE', u'Getinge'),
         ('MA', u'Maquet'),         
         ('WE', u'Weinmann'),
         ('AR', u'Arjo'),
         ('PU', u'Pulsion'),
         ('SP', u'Spacelabs'),
)

class product_pricelist(osv.Model):
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    _columns = {
        'modelo': fields.selection(MODELO_PEDIDO, u'Modelo de Impresão'),
        'fornecedor_id': fields.many2one('res.partner', u'Fornecedor'),
        'proposta_sigla': fields.char(u'Proposta sigla', size=20),
        'proposta_sufixo': fields.char(u'Proposta Sufixo', size=5),
        'referencia_proposta': fields.char(u'Referencia da proposta', size=80),
        'abertura_proposta': fields.text(u'Abertura da Proposta'),
        'condicoes_proposta': fields.text(u'Condições da proposta'),
        'validade_proposta': fields.integer(u'Validade da proposta'),
        'proposta_frete': fields.char(u'Frete', size=20),
        'proposta_rodape': fields.text(u'Proposta rodapé'),
        'proposta_empresa_rodape': fields.text(u'Proposta empresa rodapé'),
        'print_princial': fields.boolean('Print produto principal'),
        'fob': fields.boolean(u'Fob'),
        'titulo_acessorios_opc': fields.char(u'Título Acessórios Opcionais', size=80),
        'titulo_condicao_venda': fields.char(u'Título Condições de Venda', size=80),
        

        #
        # FOTOS
        #
        'foto_ilustrativa':  fields.binary(u'Foto Ilustrativa'),
        'foto_ilustrativa_text': fields.text(u'Foto Ilustrativa text'),

        'imagem_cabecalho': fields.binary(u'Imagem cabeçalho'),
        'imagem_cabecalho_text': fields.text(u'Imagem cabeçalho text'),

        'imagem_rodape': fields.binary(u'Imagem rodapé'),
        'imagem_rodape_text': fields.text(u'Imagem rodapé text'),
        
        'imagem_pedido': fields.binary(u'Imagem pedido venda'),
        'imagem_pedido_text': fields.text(u'Imagem pedido venda text'),
    }

    _defaults = {
             'validade_proposta': 0,

    }

    def create(self, cr, uid, dados, context={}):
        if 'foto_ilustrativa' in dados:
            dados['foto_ilustrativa_text'] = dados['foto_ilustrativa']

        if 'imagem_cabecalho' in dados:
            dados['imagem_cabecalho_text'] = dados['imagem_cabecalho']

        if 'imagem_rodape' in dados:
            dados['imagem_rodape_text'] = dados['imagem_rodape']
            
        if 'imagem_pedido' in dados:
            dados['imagem_pedido_text'] = dados['imagem_pedido']


        return super(product_pricelist, self).create(cr, uid, dados, context=context)


    def write(self, cr, uid, ids, dados, context={}):
        if 'foto_ilustrativa' in dados:
            dados['foto_ilustrativa_text'] = dados['foto_ilustrativa']

        if 'imagem_cabecalho' in dados:
            dados['imagem_cabecalho_text'] = dados['imagem_cabecalho']

        if 'imagem_rodape' in dados:
            dados['imagem_rodape_text'] = dados['imagem_rodape']
            
        if 'imagem_pedido' in dados:
            dados['imagem_pedido_text'] = dados['imagem_pedido']

        return super(product_pricelist, self).write(cr, uid, ids, dados, context=context)

product_pricelist()

class product_pricelist_item(osv.Model):
    _name = "product.pricelist.item"
    _inherit = "product.pricelist.item"

    _columns = {
            'price_surcharge': fields.float('Price Surcharge'),

    }

product_pricelist_item()



