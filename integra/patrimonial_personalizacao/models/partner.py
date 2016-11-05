# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from pybrasil.data import parse_datetime, hoje



class res_partner(orm.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _padrao_contrato(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for partner_obj in self.browse(cr, uid, ids):
            res[partner_obj.id] = False

            if len(partner_obj.finan_contrato_ativo_ids):
                user_ids = []

                c_obj = None
                for contrato_obj in partner_obj.finan_contrato_ativo_ids:
                    c_obj = contrato_obj

                    if c_obj.vendedor_id:
                        if c_obj.vendedor_id.id not in user_ids:
                            user_ids.append(c_obj.vendedor_id.id)

                        if c_obj.vendedor_id.id == uid:
                            break

                if c_obj is None:
                    continue

                if nome_campo == 'hr_department_id' and c_obj.hr_department_id:
                    res[partner_obj.id] = c_obj.hr_department_id.id

                if nome_campo == 'grupo_economico_id' and c_obj.grupo_economico_id:
                    res[partner_obj.id] = c_obj.grupo_economico_id.id

                if nome_campo == 'partner_category_id' and c_obj.res_partner_category_id:
                    res[partner_obj.id] = c_obj.res_partner_category_id.id

                #if nome_campo == 'user_id' and c_obj.vendedor_id:
                    #res[partner_obj.id] = c_obj.vendedor_id.id

                if c_obj.vendedor_id:
                    user_ids.append(c_obj.vendedor_id.id)

                if nome_campo == 'user_ids':
                    res[partner_obj.id] = user_ids

        return res

    def _pendencia_financeira(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for partner_id in ids:
            sql = """
            select
                l.id

            from
                finan_lancamento l

            where
                l.tipo = 'R'
                and l.situacao = 'Vencido'
                and coalesce(l.provisionado, False) = False
                and (current_date - l.data_vencimento) >= 10
                and l.partner_id = {partner_id};
            """
            sql = sql.format(partner_id=partner_id)
            cr.execute(sql)
            dados = cr.fetchall()

            res[partner_id] = len(dados) > 0

        return res

    def _search_pendencia_financeira(self, cr, uid, partner_pool, texto, args, context={}):
        partner_ids = []

        partner_pesquisa_ids = partner_pool.search(cr, uid, [])

        for partner_obj in partner_pool.browse(cr, uid, partner_pesquisa_ids):
            if 'True' in str(args):
                if partner_obj.pendencia_financeira:
                    partner_ids.append(partner_obj.id)
            elif 'False' in str(args):
                if not partner_obj.pendencia_financeira:
                    partner_ids.append(partner_obj.id)

        return [('id', 'in', partner_ids)]


    _columns = {
        'pendencia_financeira': fields.function(_pendencia_financeira, type='boolean', string=u'Pendência financeira', fnct_search=_search_pendencia_financeira),

        'rastreamento': fields.char(u'Código de Rastreamento', size=60),
        'rota_id': fields.many2one('partner.rota', u'Rota'),
        'finan_contrato_ids': fields.one2many('finan.contrato', 'partner_id', u'Contratos financeiros'),
        'finan_contrato_ativo_ids': fields.one2many('finan.contrato', 'partner_id', u'Contratos financeiros', domain=[('ativo', '=', True), ('data_distrato', '=', False), ('natureza', '=', 'R')]),

        'hr_department_id': fields.function(_padrao_contrato, type='many2one', relation='hr.department', string=u'Departamento/posto', ondelete='restrict', store=False, select=True),
        'grupo_economico_id': fields.function(_padrao_contrato, type='many2one', relation='finan.grupo.economico', string=u'Grupo econômico', ondelete='restrict', store=False, select=True),
        'partner_category_id': fields.function(_padrao_contrato, type='many2one', relation='res.partner.category', string=u'Categoria', ondelete='restrict', store=False, select=True),
        'user_id': fields.function(_padrao_contrato, type='many2one', relation='res.users', string=u'Gestor de contas', ondelete='restrict', store=False, select=True),
        'user_ids': fields.function(_padrao_contrato, type='many2many', relation='res.users', string=u'Gestor de contas', ondelete='restrict', store=False, select=True),
        'recalculo': fields.integer(u'Campo para obrigar o recalculo dos itens'),
        'data_analise_credito': fields.date(u'Data da análise de crédito'),
        'vr_limite_credito': fields.float(u'Limite de crédito mensal'),
        'user_analise': fields.many2one('res.users', u'Analisado por'),
    }

    def create(self, cr, uid, dados, context=None):
        if 'email_nfe' in dados and dados['email_nfe']:
            if u',' in dados['email_nfe']:
                raise osv.except_osv(u'Erro!', u'Insira somente 1 email!')

        res = super(res_partner, self).create(cr, uid, dados, context)

        return res

    def write(self, cr, uid, ids, dados, context={}):

        if 'email_nfe' in dados and dados['email_nfe']:
            if u',' in dados['email_nfe']:
                raise osv.except_osv(u'Erro!', u'Insira somente 1 email!')

        res = super(res_partner, self).write(cr, uid, ids, dados, context=context)

        return res

    def liberar_credito(self, cr, uid, ids, context={}):
        if not ids:
            return {}
        os_form_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'patrimonial_personalizacao', 'res_partner_analise_credito_form')[1]

        for res_obj in self.browse(cr, uid, ids):
            res = {
                'type': 'ir.actions.act_window',
                'view_id': os_form_id,
                'name': u'Clientes',
                'res_model': 'res.partner',
                'res_id': res_obj.id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'target': 'new',  # isto faz abrir numa janela no meio da tela
                #'target': 'inline',  # Abre na mesma janela, sem ser no meio da tela
                'context': {'form_view_ref': 'patrimonial_personalizacao.res_partner_analise_credito_form','default_user_analise': uid },
            }
        return res

    def onchange_valor(self, cr, uid, ids, valor, context={}):
        if not valor:
            return {}
        retorno = {}
        valores = {}
        retorno['value'] = valores
        valores['data_analise_credito'] = str(parse_datetime(hoje()))[:10]
        valores['user_analise'] = uid

        return retorno

    def confirma_credito(self, cr, uid, ids, contexte={}):


        for partner_obj in self.browse(cr, uid, ids):

            dados = {
                'data_analise_credito': partner_obj.data_analise_credito,
                'user_analise': uid,
                'user_analise': uid,
                'vr_limite_credito': partner_obj.vr_limite_credito,
            }
            partner_obj.write(dados)

        return {'type':'ir.actions.act_window_close'}

res_partner()


class res_partner_address(orm.Model):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'

    _columns = {
        '1_referencia_pessoal': fields.text(u'1º Ref. Pessoal'),
        '2_referencia_pessoal': fields.text(u'2º Ref. Pessoal'),
        '1_referencia_comercial': fields.text(u'1º Ref. Comercial'),
        '2_referencia_comercial': fields.text(u'2º Ref. Comercial'),
    }

res_partner_address()
