# -*- coding: utf-8 -*-

from osv import osv, fields


class product_product(osv.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
        'foto_capa': fields.binary(u'Foto de capa'),
        'foto_capa_text': fields.text(u'Foto de capa'),
        'foto_produto_text': fields.text(u'Foto de Produto'),
        'legenda_foto_capa': fields.char(u'Foto de capa', size=32),
        'titulo': fields.char(u'Título', size=120),
        'subtitulo': fields.char(u'Subtítulo', size=120),
        'registro_anvisa': fields.char(u'Registro ANVISA', size=30),
        'sped_pais_id': fields.many2one('sped.pais', u'País'),
        'produto_principal': fields.boolean(u'Produto principal'),
        'comissao': fields.float(u'Comissão padrão'),
        
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),        
        'write_date': fields.datetime( u'Data Ultima Alteração'),
    }

    _defaults = {
        'produto_principal': False,
    }

    def create(self, cr, uid, dados, context={}):
        if 'acessorio_ids' in dados:
            if len(dados['acessorio_ids']) > 0:
                dados['produto_principal'] = True
            else:
                dados['produto_principal'] = False
        else:
            dados['produto_principal'] = False


        return super(product_product, self).create(cr, uid, dados, context=context)


    def write(self, cr, uid, ids, dados, context={}):
        if 'product_image' in dados:
            dados['foto_produto_text'] = dados['product_image']

        if 'foto_capa' in dados:
            dados['foto_capa_text'] = dados['foto_capa']

        if 'acessorio_ids' in dados:
            if len(dados['acessorio_ids']) > 0:
                dados['produto_principal'] = True
            else:
                dados['produto_principal'] = False
        else:
            dados['produto_principal'] = False


        return super(product_product, self).write(cr, uid, ids, dados, context=context)

product_product()
