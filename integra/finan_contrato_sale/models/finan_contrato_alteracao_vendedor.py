# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import osv, fields


class finan_contrato_alteracao_vendedor(osv.Model):
    _name = 'finan.contrato.alteracao.vendedor'
    _description = u'Alteração de vendedor nos contratos'
    _order = 'data_alteracao desc'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa/Grupo', ondelete='restrict'),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='restrict'),
        'grupo_economico_id': fields.many2one('finan.grupo.economico', u'Grupo econômico', ondelete='restrict'),
        'partner_category_id': fields.many2one('res.partner.category', u'Categoria', ondelete='restrict'),        

        'municipio_id': fields.many2one('sped.municipio', u'Cidade', ondelete='restrict'),
        'vendedor_antigo_id': fields.many2one('res.users', u'Vendedor antigo', ondelete='restrict'),
        'vendedor_novo_id': fields.many2one('res.users', u'Vendedor novo', ondelete='restrict'),
        'data_alteracao': fields.date(u'Data da alteração'),

        'contrato_alterar_ids': fields.one2many('finan.contrato.alteracao.vendedor.contrato', 'alteracao_id', u'Contratos a alterar'),
        'confirmado': fields.boolean(u'Confirmado?'),
        'data_confirmacao': fields.datetime(u'Data de confirmação'),
    }

    def buscar_contratos(self, cr, uid, ids, context={}):
        item_pool = self.pool.get('finan.contrato.alteracao.vendedor.contrato')
        contrato_pool = self.pool.get('finan.contrato')

        for alteracao_obj in self.browse(cr, uid, ids):
            if alteracao_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Essa alteracao já foi confirmado e não pode ser refeita!')

            #
            # Exclui os contratos incluídos anteriormente
            #
            for cont_obj in alteracao_obj.contrato_alterar_ids:
                cont_obj.unlink()

            #
            # Faz uma lista dos contratos a serem excluídos do alteracao
            #
            excecao = []
            #for cont_obj in alteracao_obj.contrato_excecoes_ids:
                #excecao += [cont_obj.id]

            sql = '''
            select
                c.id
            from
                finan_contrato c
                join res_company cc on cc.id = c.company_id
                join res_partner p on p.id = c.partner_id
            where
                c.ativo = True
                and c.natureza = 'R'
            '''

            filtro = {
                'excecoes': str(excecao).replace('[', '').replace(']', '')
            }

            if len(excecao) > 0:
                sql += '''
                and c.id not in ({excecoes})
                '''

            if alteracao_obj.company_id:
                filtro['company_id'] = alteracao_obj.company_id.id
                sql += '''
                and (cc.id = {company_id}
                or cc.parent_id = {company_id})
                '''

            if alteracao_obj.hr_department_id:
                filtro['hr_department_id'] = alteracao_obj.hr_department_id.id
                sql += '''
                and c.hr_department_id = {hr_department_id}
                '''
                
            if alteracao_obj.grupo_economico_id:
                filtro['grupo_economico_id'] = alteracao_obj.grupo_economico_id.id
                sql += '''
                and c.grupo_economico_id = {grupo_economico_id}
                '''

            if alteracao_obj.partner_category_id:
                filtro['grupo_economico_id'] = alteracao_obj.partner_category_id.id
                sql += '''
                and c.res_partner_category_id = {partner_category_id}
                '''

            if alteracao_obj.municipio_id:
                filtro['municipio_id'] = alteracao_obj.municipio_id.id
                sql += '''
                and p.municipio_id = {municipio_id}
                '''

            if alteracao_obj.vendedor_antigo_id:
                filtro['vendedor_id'] = alteracao_obj.vendedor_antigo_id.id
                sql += '''
                and c.vendedor_id = {vendedor_id}
                '''

            sql = sql.format(**filtro)
            print(sql)

            cr.execute(sql.format(**filtro))
            dados = cr.fetchall()

            for id, in dados:
                contrato_obj = contrato_pool.browse(cr, uid, id)
                dados_item = {
                    'alteracao_id': alteracao_obj.id,
                    'contrato_id': id,
                    'vendedor_antigo_id': contrato_obj.vendedor_id.id,
                    'vendedor_novo_id': alteracao_obj.vendedor_novo_id.id,
                }
                item_pool.create(cr, uid, dados_item)

    def efetiva_alteracao(self, cr, uid, ids, context={}):
        vendedor_pool = self.pool.get('finan.contrato.vendedor')
        contrato_pool = self.pool.get('finan.contrato')

        for alteracao_obj in self.browse(cr, uid, ids):
            if alteracao_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Essa alteração já foi confirmada e não pode ser refeita!')

            if not alteracao_obj.data_confirmacao:
                raise osv.except_osv(u'Erro!', u'Para efetivar a alteração, é preciso preencher a data e hora de confirmação!')

            #
            # Vamos agora varrer todos os contratos a serem reajustados
            #
            for item_obj in alteracao_obj.contrato_alterar_ids:
                dados = {
                    'contrato_id': item_obj.contrato_id.id,
                    'vendedor_id': item_obj.vendedor_novo_id.id,
                    'data_inicial': alteracao_obj.data_alteracao,
                    'forca_ajuste': str(fields.datetime.now()),
                }
                vendedor_pool.create(cr, uid, dados)
                dados = {
                    'vendedor_id': alteracao_obj.vendedor_novo_id.id,
                }
                contrato_pool.write(cr, uid, [item_obj.contrato_id.id], dados)


            #
            # Agora, trava o alteracao, para não ser mais alterado
            #
            alteracao_obj.write({'confirmado': True})

    def write(self, cr, uid, ids, dados, context={}):
        #
        # Não deixa alterar alteracaos confirmados
        #
        for alteracao_obj in self.browse(cr, uid, ids):
            if alteracao_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Essa alteração já foi confirmada e não pode ser alterada!')

        return super(finan_contrato_alteracao_vendedor, self).write(cr, uid, ids, dados, context=context)

    def unlink(self, cr, uid, ids, context={}):
        #
        # Não deixa excluir alteracaos confirmados
        #
        for alteracao_obj in self.browse(cr, uid, ids):
            if alteracao_obj.confirmado:
                raise osv.except_osv(u'Erro!', u'Essa alteração já foi confirmada e não pode ser excluída!')

        return super(finan_contrato_alteracao_vendedor, self).unlink(cr, uid, ids, context=context)


finan_contrato_alteracao_vendedor()


class finan_contrato_alteracao_vendedor_contrato(osv.Model):
    _description = u'Itens da alteração de vendedor'
    _name = 'finan.contrato.alteracao.vendedor.contrato'
    _order = 'alteracao_id, contrato_id'

    _columns = {
        'alteracao_id': fields.many2one('finan.contrato.alteracao.vendedor', u'Alteração', required=True, ondelete="cascade"),
        'contrato_id': fields.many2one('finan.contrato', u'Contrato', required=True, ondelete="restrict"),

        'company_id': fields.related('contrato_id', 'company_id', relation='res.company', string=u'Empresa', type='many2one'),
        'numero': fields.related('contrato_id', 'numero', type='char', string=u'Número'),
        'partner_id': fields.related('contrato_id', 'partner_id', relation='res.partner', string=u'Parceiro', type='many2one'),

        'vendedor_antigo_id': fields.many2one('res.users', u'Vendedor', ondelete='restrict'),
        'vendedor_novo_id': fields.many2one('res.users', u'Vendedor', ondelete='restrict'),
    }


finan_contrato_alteracao_vendedor_contrato()
