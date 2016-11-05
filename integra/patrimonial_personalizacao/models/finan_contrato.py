# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields,osv
from pybrasil.valor.decimal import Decimal as D
import random


DIAS_VENCIMENTO = [
    #[ '1', ' 1'],
    [ '2', ' 2'],
    #[ '3', ' 3'],
    #[ '4', ' 4'],
    [ '5', ' 5'],
    #[ '6', ' 6'],
    #[ '7', ' 7'],
    #[ '8', ' 8'],
    #[ '9', ' 9'],
    ['10', '10'],
    #['11', '11'],
    #['12', '12'],
    #['13', '13'],
    #['14', '14'],
    ['15', '15'],
    #['16', '16'],
    #['17', '17'],
    #['18', '18'],
    #['19', '19'],
    ['20', '20'],
    #['21', '21'],
    #['22', '22'],
    #['23', '23'],
    #['24', '24'],
    ['25', '25'],
    #['26', '26'],
    #['27', '27'],
    #['28', '28'],
    #['29', '29'],
    ['30', '30']
]


class finan_contrato(orm.Model):
    _name = 'finan.contrato'
    _inherit = 'finan.contrato'

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
                and (current_date - l.data_vencimento) >= 30
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
        'dia_vencimento': fields.selection(DIAS_VENCIMENTO, u'Dia de vencimento'),
        'contrato_atualizado': fields.boolean(u'Contrato Atualizado para Suspensão com 30 dias de Atraso no Pagamento'),
        'suspensao_ids': fields.one2many('finan.contrato.suspensao', 'contrato_id', u'Suspensões Contratuais'),
        'suspenso_inadimplente': fields.boolean(u'Suspenso por Inadimplência'),
        'pendencia_financeira': fields.function(_pendencia_financeira, type='boolean', string=u'Pendência financeira', fnct_search=_search_pendencia_financeira),
    }

    _defaults = {
        'contrato_atualizado': False,
    }

    def onchange_sale_order_id(self, cr, uid, ids, company_id, sale_order_id):
        res = {}
        valores = {}
        res['value'] = valores

        if not (company_id and sale_order_id):
            return res

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        sale_order_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)

        valores['partner_id'] = sale_order_obj.partner_id.id

        if getattr(sale_order_obj, 'hr_department_id', False):
            valores['hr_department_id'] = sale_order_obj.hr_department_id.id

        if getattr(sale_order_obj, 'grupo_economico_id', False):
            valores['grupo_economico_id'] = sale_order_obj.grupo_economico_id.id

        if getattr(sale_order_obj, 'res_partner_category_id', False):
            valores['res_partner_category_id'] = sale_order_obj.res_partner_category_id.id

        valores['vendedor_id'] = sale_order_obj.user_id.id

        #
        # Patrimonial Segurança
        #
        mensal_mon_eletronico = D(0)
        if sale_order_obj.monitoramento_eletronico:
            mensal_mon_eletronico = D(sale_order_obj.monitoramento_eletronico or 0)

        if sale_order_obj.posto_movel:
            mensal_mon_eletronico += D(sale_order_obj.posto_movel or 0)

        if sale_order_obj.ronda:
            mensal_mon_eletronico += D(sale_order_obj.ronda or 0)

        #if sale_order_obj.manutencao_tecnica:
            #mensal_mon_eletronico += D(sale_order_obj.manutencao_tecnica or 0)

        if sale_order_obj.qtd_becape_chip and sale_order_obj.produto_chip_id:
            mensal_mon_eletronico += D(sale_order_obj.qtd_becape_chip or 0) * D(sale_order_obj.vr_becape_chip or 0)

        mensal_mon_imagens = D(0)
        if sale_order_obj.monitoramento_imagens:
            mensal_mon_imagens = D(sale_order_obj.monitoramento_imagens or 0)

        mensal_mon_garantido = D(0)
        if sale_order_obj.qtd_monitoramento_garantido:
            mensal_mon_garantido = D(sale_order_obj.qtd_monitoramento_garantido or 0) * D(sale_order_obj.vr_monitoramento_garantido or 0)

        mensal_vig_animal = D(0)
        if sale_order_obj.animal_adestrado:
            mensal_vig_animal = D(sale_order_obj.animal_adestrado or 0)

        mensal_seguranca = mensal_mon_eletronico + mensal_mon_imagens + mensal_mon_garantido + mensal_vig_animal

        if '82.891.805' in company_obj.partner_id.cnpj_cpf:
            mensalidade = mensal_seguranca
            produtos = []

            if mensal_mon_eletronico != 0:
                dados_produto = {
                    #'novo': 'S',
                    #'contrato_id': contrato_obj.id,
                    'product_id': 3178,
                    'quantidade': 1,
                    'vr_unitario': mensal_mon_eletronico,
                    'vr_total': mensal_mon_eletronico,
                }
                produtos.append([0, False, dados_produto])

            if mensal_mon_imagens != 0:
                dados_produto = {
                    #'novo': 'S',
                    #'contrato_id': contrato_obj.id,
                    'product_id': 3186,
                    'quantidade': 1,
                    'vr_unitario': mensal_mon_imagens,
                    'vr_total': mensal_mon_imagens,
                }
                produtos.append([0, False, dados_produto])

            if mensal_mon_garantido != 0:
                dados_produto = {
                    #'novo': 'S',
                    #'contrato_id': contrato_obj.id,
                    'product_id': 3179,
                    'quantidade': 1,
                    'vr_unitario': mensal_mon_garantido,
                    'vr_total': mensal_mon_garantido,
                }
                produtos.append([0, False, dados_produto])

            if mensal_vig_animal != 0:
                dados_produto = {
                    #'novo': 'S',
                    #'contrato_id': contrato_obj.id,
                    'product_id': 3187,
                    'quantidade': 1,
                    'vr_unitario': mensal_vig_animal,
                    'vr_total': mensal_vig_animal,
                }
                produtos.append([0, False, dados_produto])

            valores['contrato_produto_mensal_ids'] = produtos

        #
        # Patrimonial Comércio
        #
        else:
            mensalidade = (sale_order_obj.vr_mensal or 0)
            mensalidade -= mensal_seguranca


            produtos = []
            if sale_order_obj.manutencao_tecnica:
                dados_produto = {
                    #'novo': 'S',
                    #'contrato_id': contrato_obj.id,
                    'product_id': 3315,  # Locação de equipamentos
                    'quantidade': 1,
                    'vr_unitario': sale_order_obj.manutencao_tecnica,
                    'vr_total': sale_order_obj.manutencao_tecnica,
                }
                produtos.append([0, False, dados_produto])

                if mensalidade > sale_order_obj.manutencao_tecnica:
                    dados_produto = {
                        #'novo': 'S',
                        #'contrato_id': contrato_obj.id,
                        'product_id': 3182,  # Locação de equipamentos
                        'quantidade': 1,
                        'vr_unitario': mensalidade - sale_order_obj.manutencao_tecnica,
                        'vr_total': mensalidade - sale_order_obj.manutencao_tecnica,
                    }
                    produtos.append([0, False, dados_produto])

            else:
                dados_produto = {
                    #'novo': 'S',
                    #'contrato_id': contrato_obj.id,
                    'product_id': 3182,  # Locação de equipamentos
                    'quantidade': 1,
                    'vr_unitario': mensalidade,
                    'vr_total': mensalidade,
                }
                produtos.append([0, False, dados_produto])

            valores['contrato_produto_mensal_ids'] = produtos

        valores['valor_mensal'] = mensalidade

        print(res)

        return res



    def create(self, cr, uid, dados, context={}):
        res = super(finan_contrato, self).create(cr, uid, dados, context=context)

        self.pool.get('finan.contrato').ajusta_vendedor_cliente(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_contrato, self).write(cr, uid, ids, dados, context=context)

        self.pool.get('finan.contrato').ajusta_vendedor_cliente(cr, uid, ids)

        return res

    def ajusta_vendedor_cliente(self, cr, uid, ids):
        for contrato_obj in self.pool.get('finan.contrato').browse(cr, uid, ids):
            if contrato_obj.natureza == 'R':
                contrato_obj.partner_id.write({'recalculo': int(random.random() * 100000000)})

                ##
                ## Atualiza os outros contratos do mesmo cliente com os mesmos dados
                ##
                #sql = """
                #update finan_contrato set
                    #hr_department_id = {hr_department_id},
                    #grupo_economico_id = {grupo_economico_id}

                #where
                    #partner_id = {partner_id}
                    #and natureza = 'R'
                    #and id != {id};
                #"""
                #filtro = {
                    #'hr_department_id': contrato_obj.hr_department_id.id if contrato_obj.hr_department_id else 'null',
                    #'grupo_economico_id': contrato_obj.grupo_economico_id.id if contrato_obj.grupo_economico_id else 'null',
                    #'res_partner_category_id': contrato_obj.res_partner_category_id.id if contrato_obj.res_partner_category_id else 'null',
                    #'partner_id': contrato_obj.partner_id.id,
                    #'id': contrato_obj.id,
                #}
                #sql = sql.format(**filtro)
                #cr.execute(sql)


finan_contrato()

class finan_contrato_produto(osv.Model):
    _inherit = 'finan.contrato_produto'
    _order = 'data desc'

    _columns = {
        'suspensao_id': fields.many2one('finan.contrato.suspensao', u'Suspensões Contratuais'),
    }


finan_contrato_produto()
