# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv
from pybrasil.data import hoje, primeiro_dia_mes, ultimo_dia_mes, parse_datetime, mes_passado
from pybrasil.valor.decimal import Decimal as D


#TIPO_CONTA = (
    #('D', u'Despesa'),
    #('C', u'Custo'),
#)


#class finan_rateio(orm.Model):
    #_description = u'Rateio entre centros de custo'
    #_name = 'finan.rateio'
    #_inherit = 'finan.rateio'

    #_columns = {
        #'tipo_conta': fields.selection(TIPO_CONTA, u'Tipo', select=True),
    #}


#finan_rateio()



class finan_centrocusto(orm.Model):
    _name = 'finan.centrocusto'
    _inherit = 'finan.centrocusto'


    _columns = {
        'rateio_rh': fields.boolean(u'Rateio do RH?', select=True),
        'company_id': fields.many2one('res.company', u'Grupo/unidade'),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica'),
        'company_ids': fields.many2many('res.company', 'finan_centrocusto_company', 'centrocusto_id', 'company_id', u'Grupos/unidades'),
        'rule_ids': fields.many2many('hr.salary.rule', 'finan_centrocusto_rubrica', 'centrocusto_id', 'rule_id', u'Rubricas'),
        'tipo_parceiro': fields.selection([('S', u'Sindicato'), ('E', u'Empregado')], u'Sindicato/Empregado'),
        'periodo_rh': fields.selection([('=', u'Mesmo mês'), ('<', u'Mês anterior')], u'Período da folha'),
    }

    _defaults = {
        'rateio_rh': False,
        'periodo_rh': '<',
    }

    def realiza_rateio(self, cr, uid, ids, context={}, valor=0, campos=[], padrao={}, rateio={}, tabela_pool=None):
        #
        # No caso de rateio da folha, antes de fazer o rateio, preparamos
        # os itens de rateio de acordo com os dados adequados da folha
        #
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        if not campos:
            campos = self.campos_rateio(cr, uid)

        holerite_pool = self.pool.get('hr.payslip')
        rubrica_pool = self.pool.get('hr.salary.rule')

        if tabela_pool is None:
            tabela_pool = self.pool.get('finan.centrocusto')

        for cc_obj in tabela_pool.browse(cr, uid, ids):
            if not getattr(cc_obj, 'rateio_rh', False):
                return super(finan_centrocusto, self).realiza_rateio(cr, uid, ids, context=context, valor=valor, campos=campos, padrao=padrao, rateio=rateio, tabela_pool=tabela_pool)
            else:
                periodo = parse_datetime(context.get('data_vencimento', hoje())).date()
                #
                # Caso o período seja anterior ao vencimento
                #
                if cc_obj.periodo_rh == '<':
                    periodo = mes_passado(periodo)

                data_inicial = primeiro_dia_mes(periodo)
                data_final = ultimo_dia_mes(periodo)
                partner_id = context.get('partner_id', False)

                #print(periodo, data_inicial, data_final)

                if cc_obj.company_id:
                    company_id = str(cc_obj.company_id.id)
                else:
                    company_id = ''
                    for company_obj in cc_obj.company_ids:
                        company_id += str(company_obj.id) + ','
                    if len(company_id) and company_id[-1] == ',':
                        company_id = company_id[:-1]

                rule_id = ''
                rubricas = ['LIQ']
                if cc_obj.rule_id:
                    rule_id = str(cc_obj.rule_id.id)
                    rubricas = [cc_obj.rule_id.code]
                else:
                    rubricas = []
                    for rule_obj in cc_obj.rule_ids:
                        rule_id += str(rule_obj.id) + ','
                        rubricas.append(rule_obj.code)

                    if len(rule_id) and rule_id[-1] == ',':
                        rule_id = rule_id[:-1]

                filtro = {
                    'company_id': company_id,
                    'data_inicial': str(data_inicial),
                    'data_final': str(data_final),
                }
                #
                # Seleciona os holerites do período correspondente
                #
                sql = """
                    select distinct
                        h.id
                    from
                        hr_payslip h
                        join hr_payslip_line hl on hl.slip_id = h.id
                        join hr_contract c on c.id = h.contract_id
                        join hr_employee e on e.id = c.employee_id
                        join res_company u on u.id = c.company_id
                        left join res_company g on g.id = u.parent_id
                    where
                        h.state = 'done'
                        and (h.simulacao is null or h.simulacao = False)
                        and hl.code not like '%_anterior'
                """

                #
                # Identifica se, entre as rubricas, está o IRPF
                # Se estiver, altera a pesquisa das datas para considerar a data
                # de pagamento do IRPF, que muda na férias
                #
                if 'IRPF' in rubricas:
                    sql += """
                        and (
                            u.id in ({company_id}) or
                            g.id in ({company_id}) or
                            g.parent_id in ({company_id})
                        ) and h.data_pagamento_irpf between '{data_inicial}' and '{data_final}'
                    """
                else:
                    sql += """
                        and (
                            u.id in ({company_id}) or
                            g.id in ({company_id}) or
                            g.parent_id in ({company_id})
                        ) and (
                            (h.tipo = 'N' and
                            h.date_from >= '{data_inicial}' and
                            h.date_to <= '{data_final}'
                            ) or
                            (h.tipo = 'F' and
                            h.date_from between '{data_inicial}' and '{data_final}'
                            ) or
                            (h.tipo = 'R' and
                            h.data_afastamento between '{data_inicial}' and '{data_final}'
                            ) or
                            (h.tipo = 'D' and
                            h.date_from >= '{data_inicial}' and
                            h.date_to <= '{data_final}')
                        )
                    """

                if rule_id:
                    filtro['rule_id'] = rule_id
                    sql += """
                    and hl.salary_rule_id in ({rule_id})
                    """

                if partner_id:
                    filtro['partner_id'] = partner_id
                    if cc_obj.tipo_parceiro == 'S':
                        sql += """
                        and c.sindicato_id = {partner_id}
                        """
                    elif cc_obj.tipo_parceiro == 'E':
                        sql += """
                        and e.partner_id = {partner_id}
                        """
                elif 'IRPF' not in rubricas:
                    #
                    # Retira os RPA do rateio se não for específico para eles
                    # a não ser no caso do rateio do IR, que entra RPA normal
                    #
                    sql += """
                    and c.categoria_trabalhador not in ('701','702','703')
                    """

                print(sql.format(**filtro))
                cr.execute(sql.format(**filtro))

                holerite_ids = []
                dados = cr.fetchall()
                for holerite_id, in dados:
                    holerite_ids.append(holerite_id)

                #
                # Prepara agora o rateio
                #
                conta_obj = None
                if 'conta_id' in padrao:
                    conta_obj = self.pool.get('finan.conta').browse(cr, 1, padrao['conta_id'])

                rateio = {}
                total = D(0)
                for h_obj in holerite_pool.browse(cr, 1, holerite_ids):
                    for rubrica in rubricas:
                        total += h_obj.realiza_rateio(rateio=rateio, campo_valor=rubrica, conta_obj=conta_obj, context={'rateio_folha': True})

                #
                # Agora, com base no valor total da rubricas apurado, ajusta os
                # valores para adequar ao rateio real
                #
                proporcao = D(1)
                if total > 0:
                    proporcao = valor / total

                rateio = self._ajusta_rateio_folha(rateio, proporcao)

            #print(rateio)
            return rateio

    def _ajusta_rateio_folha(self, rateio, proporcao):
        for id in rateio:
            if isinstance(rateio[id], dict):
                rateio[id] = self._ajusta_rateio_folha(rateio[id], proporcao)

            else:
                rateio[id] *= proporcao
                rateio[id] = rateio[id].quantize(D('0.01'))

        return rateio

    def _verifica_rateio_rh(self, cr, uid, ids, dados, context={}):
        for cc_obj in self.browse(cr, uid, ids):
            if cc_obj.tipo != 'R':
                continue

            #
            # Verifica se o rateio está sendo usado em algum funcionário
            #
            contract_pool = self.pool.get('hr.contract')
            contract_ids = contract_pool.search(cr, 1, [('centrocusto_id', '=', cc_obj.id), ('date_end', '=', False)])

            if not len(contract_ids):
                continue

            for contract_id in contract_ids:
                contract_pool.verifica_rateio(cr, 1, [contract_id], {'centrocusto_id': cc_obj.id}, context)

    def write(self, cr, uid, ids, dados, context={}):
        res = super(finan_centrocusto, self).write(cr, uid, ids, dados, context)

        self._verifica_rateio_rh(cr, uid, ids, dados, context)

        return res


finan_centrocusto()



class finan_rateio(orm.Model):
    _name = 'finan.rateio'
    _inherit = 'finan.rateio'

    _columns = {
        'hr_contract_id': fields.many2one('hr.contract', u'Funcionário', select=True, ondelete='restrict'),
        'hr_department_id': fields.many2one('hr.department', u'Departamento/Posto', select=True, ondelete='restrict'),
    }


finan_rateio()
