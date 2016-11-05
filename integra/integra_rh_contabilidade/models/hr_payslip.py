# -*- coding: utf-8 -*-

from osv import fields, orm , osv
from pybrasil.valor.decimal import Decimal as D
from copy import copy
from pybrasil.valor import formata_valor
from sped_contabilidade.models.sped_modelo_partida_dobrada import PartidaDobrada
from pybrasil.data import parse_datetime, formata_data
from dateutil.relativedelta import relativedelta



class hr_payslip(orm.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    _columns = {
        'contabilizacao_ids': fields.one2many('rh.contabilidade', 'slip_id', u'Lançamentos contábeis'),
    }

    def get_partidas_dobradas_folha(self, cr, uid, ids, context={}):
        res = []

        partida_pool = self.pool.get('sped.modelo_partida_dobrada')
        contract_pool = self.pool.get('hr.contract')

        partida_obj = False

        for holerite_obj in self.browse(cr, uid, ids):
            if not holerite_obj.line_ids:
                continue

            if (not holerite_obj.provisao) and (not holerite_obj.state == 'done'):
                continue

            if holerite_obj.contract_id.centrocusto_id:
                if holerite_obj.contract_id.centrocusto_id.tipo == 'C':
                    tipo_conta = 'C'
                else:
                    if holerite_obj.contract_id.centrocusto_id.rateio_ids[0].tipo_conta:
                        if holerite_obj.contract_id.centrocusto_id.rateio_ids[0].tipo_conta == 'D':
                            tipo_conta = 'D'
                        else:
                            tipo_conta = 'C'
            else:
                tipo_conta = 'C'

            for rubrica_obj in holerite_obj.line_ids:
                if rubrica_obj.holerite_anterior_line_id:
                    continue

                partida = PartidaDobrada()

                partida_ids = []
                if holerite_obj.tipo == 'N':
                    if tipo_conta == 'D':
                        if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_despesa_id:
                            partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_despesa_id.id]
                        elif rubrica_obj.salary_rule_id.modelo_folha_custo_id:
                            partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_id.id]

                    else:
                        if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_custo_id:
                            partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_id.id]

                elif holerite_obj.tipo == 'R':
                    if tipo_conta == 'D':
                        if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_despesa_rescisao_id:
                            partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_despesa_rescisao_id.id]
                        elif rubrica_obj.salary_rule_id.modelo_folha_custo_rescisao_id:
                            partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_rescisao_id.id]

                    else:
                        if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_custo_rescisao_id:
                            partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_rescisao_id.id]

                elif holerite_obj.tipo == 'F':
                    if not holerite_obj.provisao:
                        if tipo_conta == 'D':
                            if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_despesa_ferias_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_despesa_ferias_id.id]
                            elif rubrica_obj.salary_rule_id.modelo_folha_custo_ferias_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_ferias_id.id]

                        else:
                            if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_custo_ferias_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_ferias_id.id]
                    else:
                        print(rubrica_obj.salary_rule_id.code, rubrica_obj.salary_rule_id.modelo_folha_despesa_provisao_ferias_id, rubrica_obj.salary_rule_id.modelo_folha_custo_provisao_ferias_id, tipo_conta)
                        if tipo_conta == 'D':
                            if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_despesa_provisao_ferias_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_despesa_provisao_ferias_id.id]
                            elif rubrica_obj.salary_rule_id.modelo_folha_custo_provisao_ferias_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_provisao_ferias_id.id]

                        else:
                            if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_custo_provisao_ferias_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_provisao_ferias_id.id]

                elif holerite_obj.tipo == 'D':
                    if not holerite_obj.provisao:
                        if tipo_conta == 'D':
                            if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_despesa_13_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_despesa_13_id.id]
                            elif rubrica_obj.salary_rule_id.modelo_folha_custo_13_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_13_id.id]
                        else:
                            if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_custo_13_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_13_id.id]
                    else:
                        if tipo_conta == 'D':
                            if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_despesa_provisao_13_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_despesa_provisao_13_id.id]
                            elif rubrica_obj.salary_rule_id.modelo_folha_custo_provisao_13_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_provisao_13_id.id]
                        else:
                            if rubrica_obj.salary_rule_id and rubrica_obj.salary_rule_id.modelo_folha_custo_provisao_13_id:
                                partida_ids = [rubrica_obj.salary_rule_id.modelo_folha_custo_provisao_13_id.id]

                if len(partida_ids) > 0:
                    partida_obj = partida_pool.browse(cr, uid, partida_ids[0])

                    for item_partida_obj in partida_obj.item_ids:
                        partida = PartidaDobrada()

                        if holerite_obj.tipo == 'N':
                            partida.data = parse_datetime(holerite_obj.date_to).date()
                            tipo = u''

                        elif holerite_obj.tipo == 'F':
                            partida.data = parse_datetime(holerite_obj.date_from).date() + relativedelta(days=-2)
                            if not holerite_obj.provisao:
                                tipo = u'Férias - ' + holerite_obj.employee_id.name + ' - '
                            else:
                                tipo = u'Provisão Férias - '

                        elif holerite_obj.tipo == 'R':
                            partida.data = parse_datetime(holerite_obj.data_afastamento).date()
                            tipo = u'Rescisão - ' + holerite_obj.employee_id.name + ' - '

                        elif holerite_obj.tipo == 'D':
                            partida.data = parse_datetime(holerite_obj.date_to).date()

                            if not holerite_obj.provisao:
                                tipo = u'13º salário - '
                            else:
                                tipo = u'Provisão 13º Salário - '

                        if item_partida_obj.conta_credito_id:
                            partida.conta_credito_id = item_partida_obj.conta_credito_id

                        if item_partida_obj.conta_debito_id:
                            partida.conta_debito_id = item_partida_obj.conta_debito_id

                        if item_partida_obj.historico_id:
                            partida.codigo_historico = item_partida_obj.historico_id.codigo
                            partida.historico = item_partida_obj.historico_id.nome

                        if holerite_obj.contract_id.centrocusto_id:
                            partida.centrocusto_id =  holerite_obj.contract_id.centrocusto_id.id

                        #
                        # Busca o valor do campo correspondente
                        #
                        partida.valor = D(rubrica_obj.total or 0)
                        #print('valor', partida.valor)

                        #
                        # No caso de provisão, o valor a ser contabilizado
                        # é na realidade a diferença entre este mês e o mês anterior
                        # para a mesma rubrica
                        #
                        if holerite_obj.provisao:
                            if holerite_obj.tipo == 'F':
                                sql = """
                                select
                                    coalesce(hl.total, 0)

                                from
                                    hr_payslip h
                                    join hr_payslip_line hl on hl.slip_id = h.id

                                where
                                    h.contract_id = {contract_id}
                                    and h.provisao = True
                                    and h.tipo = 'F'
                                    and to_char(h.date_from, 'YYYY-MM') = '{competencia_anterior}'
                                    and h.data_inicio_periodo_aquisitivo = '{data_inicio_periodo_aquisitivo}'
                                    and hl.salary_rule_id = {rule_id};
                                """
                                filtro = {
                                    'contract_id': holerite_obj.contract_id.id,
                                    'rule_id': rubrica_obj.salary_rule_id.id,
                                    'data_inicio_periodo_aquisitivo': holerite_obj.data_inicio_periodo_aquisitivo,
                                    'competencia_anterior': formata_data(parse_datetime(holerite_obj.date_from) + relativedelta(day=1, months=-1) , '%Y-%m'),
                                }
                                sql = sql.format(**filtro)

                                cr.execute(sql)

                                valor_provisao_anterior = cr.fetchall()

                                if valor_provisao_anterior:
                                    valor_provisao_anterior = D(valor_provisao_anterior[0][0] or 0)
                                    print('valor anterior', valor_provisao_anterior)
                                    partida.valor -= valor_provisao_anterior

                            elif holerite_obj.date_to[5:7] != '01':
                                sql = """
                                select
                                    coalesce(hl.total, 0)

                                from
                                    hr_payslip h
                                    join hr_payslip_line hl on hl.slip_id = h.id

                                where
                                    h.contract_id = {contract_id}
                                    and h.provisao = True
                                    and h.tipo = 'D'
                                    and to_char(h.date_to, 'YYYY-MM') = '{competencia_anterior}'
                                    and hl.salary_rule_id = {rule_id};
                                """
                                filtro = {
                                    'contract_id': holerite_obj.contract_id.id,
                                    'rule_id': rubrica_obj.salary_rule_id.id,
                                    'competencia_anterior': formata_data(parse_datetime(holerite_obj.date_to) + relativedelta(day=1, months=-1) , '%Y-%m'),
                                }
                                sql = sql.format(**filtro)

                                cr.execute(sql)

                                valor_provisao_anterior = cr.fetchall()

                                if valor_provisao_anterior:
                                    valor_provisao_anterior = D(valor_provisao_anterior[0][0] or 0)
                                    partida.valor -= valor_provisao_anterior

                            #
                            # No caso de haver necessidade de desprovisionar uma parte de médias, inverter
                            # as contas a débito e a crédito
                            #
                            if partida.valor < 0:
                                partida.valor = partida.valor * -1
                                cd = partida.conta_debito_id
                                cc = partida.conta_credito_id
                                partida.conta_debito_id = cc
                                partida.conta_credito_id = cd

                        partida.cnpj = holerite_obj.company_id.partner_id.cnpj_cpf

                        partida.historico = rubrica_obj.name + ' - ' +  tipo +  holerite_obj.company_id.partner_id.name


                        if (partida.valor > 0) and \
                            (partida.conta_debito_id and partida.conta_credito_id) and \
                            partida.conta_credito_id.id != partida.conta_debito_id.id:
                            res.append(partida)
                        else:
                            print('partida.valor, partida.conta_debito_id, partida.conta_credito_id')
                            print(rubrica_obj.salary_rule_id.name, partida.valor, partida.conta_debito_id, partida.conta_credito_id)
                            partida.sem_partida = True
                            partida.rule_id = rubrica_obj.salary_rule_id.id
                            res.append(partida)


        return res

    def gera_contabilizacao(self, cr, uid, ids, context={}):
        for doc_obj in self.browse(cr, uid, ids):
            #
            # Exclui as contabilizações anteriores
            #

            for cont_obj in doc_obj.contabilizacao_ids:
                cont_obj.unlink()


            partidas = doc_obj.get_partidas_dobradas_folha()

            for partida in partidas:
                dados = {
                    'slip_id': doc_obj.id,
                    'data': fields.related('slip_id', 'date_from', type='date', string=u'Data'),
                    'conta_credito_id': partida.conta_credito_id.id,
                    'conta_debito_id': partida.conta_debito_id.id,
                    'valor': partida.valor,
                    'codigo_historico': partida.codigo_historico,
                    'historico': partida.historico,
                }
                self.pool.get('rh.contabilidade').create(cr, uid, dados)

        return {}


hr_payslip()
