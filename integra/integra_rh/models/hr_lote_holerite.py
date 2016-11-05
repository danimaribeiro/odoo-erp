# -*- coding: utf-8 -*-


from osv import fields, osv
#from pybrasil.data import parse_datetime
from hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
from integra_rh.wizard.relatorio import *
from pybrasil.base import DicionarioBrasil
from pybrasil.data import parse_datetime, formata_data, ultimo_dia_mes
from pybrasil.valor.decimal import Decimal as D
from finan.wizard.finan_relatorio import *
import base64


class hr_lote_holerite(osv.Model):
    _name = 'hr.lote_holerite'
    _description = u'Lotes de holerites'
    _rec_name = ''
    _order = 'ano desc, mes desc, company_id'

    def get_payslip_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        holerite_pool = self.pool.get('hr.payslip')

        for lote_holerite_obj in self.browse(cr, uid, ids):
            dados = {
                'data_inicial': lote_holerite_obj.data_inicial,
                'data_final': lote_holerite_obj.data_final,
                'company_id': lote_holerite_obj.company_id.id,
                'tipo': lote_holerite_obj.tipo[0],
                'categoria_trabalhador': "''",
            }

            if lote_holerite_obj.provisao:
                dados['tipo'] = lote_holerite_obj.tipo_provisao

            if lote_holerite_obj.provisao or lote_holerite_obj.tipo[0] == 'D':
                #
                # Elimina do lote os pro-labore ('722') e RPA ('701','702','703')
                #
                dados['categoria_trabalhador'] = "'722','701','702','703'"

            sql = """
                select
                    h.id

                from
                    hr_payslip h
                    join res_company c on c.id = h.company_id
                    join hr_employee e on e.id = h.employee_id
                    join hr_contract co on co.id = h.contract_id

                where
                       (h.company_id = {company_id} or c.parent_id = {company_id})
                    and h.date_from >= '{data_inicial}'
                    and h.date_to <= '{data_final}'
                    and h.tipo = '{tipo}'
                    and co.categoria_trabalhador not in ({categoria_trabalhador})
            """
            
            if lote_holerite_obj.contract_id:
                sql += """
                    and co.id = {contract_id}
                """.format(contract_id=lote_holerite_obj.contract_id.id)

            if lote_holerite_obj.provisao:
                sql += """
                    and (h.simulacao = True and h.provisao = True)
                """
            else:
                sql += """
                    and (h.simulacao is null or h.simulacao = False)
                """

            sql += """
                order by
                    e.nome;
            """

            sql = sql.format(**dados)

            cr.execute(sql)
            holerite_ids_lista = cr.fetchall()
            holerite_ids = []
            for dados in holerite_ids_lista:
                holerite_ids.append(dados[0])
            res[lote_holerite_obj.id] = holerite_ids

        return res

    def get_contract_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        contrato_pool = self.pool.get('hr.contract')

        for lote_holerite_obj in self.browse(cr, uid, ids):
            dados = {
                'data_inicial': lote_holerite_obj.data_inicial,
                'data_final': lote_holerite_obj.data_final,
                'company_id': lote_holerite_obj.company_id.id,
                'tipo': lote_holerite_obj.tipo[0],
                'categoria_trabalhador': "''",
                'simulacao': lote_holerite_obj.provisao,
                'provisao': lote_holerite_obj.provisao,
            }

            if lote_holerite_obj.provisao:
                dados['tipo'] = lote_holerite_obj.tipo_provisao

            if lote_holerite_obj.provisao or lote_holerite_obj.tipo[0] == 'D':
                #
                # Elimina do lote os pro-labore ('722') e RPA ('701','702','703')
                #
                dados['categoria_trabalhador'] = "'722','701','702','703'"

            sql = """
                select
                    c.id

                from
                    hr_contract c
                    join res_company e on e.id = c.company_id
                    join hr_employee ee on ee.id = c.employee_id

                where
                    c.date_start <= '{data_final}' and
                    (c.date_end is null or c.date_end > '{data_final}')
                    and (e.id = {company_id} or e.parent_id = {company_id})
                    and c.categoria_trabalhador not in ({categoria_trabalhador})
            """
            
            if lote_holerite_obj.contract_id:
                sql += """
                    and c.id = {contract_id}
                """.format(contract_id=lote_holerite_obj.contract_id.id)

            if lote_holerite_obj.provisao:
                sql += """
                    and not exists(
                        select
                            h.contract_id
                        from
                            hr_payslip h
                        where
                            h.tipo = '{tipo}'
                            and (h.simulacao = True and h.provisao = True)
                            and h.contract_id = c.id
                            and h.date_from >= '{data_inicial}'
                            and h.date_to <= '{data_final}'
                    )
                """
            else:
                sql += """
                    and not exists(
                        select
                            h.contract_id
                        from
                            hr_payslip h
                        where
                            h.tipo = '{tipo}'
                            and (h.simulacao is null or h.simulacao = False)
                            and h.contract_id = c.id
                            and h.date_from >= '{data_inicial}'
                            and h.date_to <= '{data_final}'
                    )
                """

            sql += """
                order by
                    ee.nome;
            """

            sql = sql.format(**dados)
            #print(sql)
            cr.execute(sql)
            contrato_ids_lista = cr.fetchall()
            contrato_ids = []
            for dados in contrato_ids_lista:
                contrato_ids.append(dados[0])
            #print(contrato_ids)
            res[lote_holerite_obj.id] = contrato_ids

        return res

    def get_ferias_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        ferias_pool = self.pool.get('hr.contract_ferias')

        for lote_holerite_obj in self.browse(cr, uid, ids):
            dados = {
                'data_inicial': lote_holerite_obj.data_inicial,
                'data_final': lote_holerite_obj.data_final,
                'company_id': lote_holerite_obj.company_id.id,
                'tipo': lote_holerite_obj.tipo[0],
                'categoria_trabalhador': "''",
                'simulacao': lote_holerite_obj.provisao,
                'provisao': lote_holerite_obj.provisao,
            }

            if lote_holerite_obj.provisao:
                dados['tipo'] = lote_holerite_obj.tipo_provisao

            #
            # Elimina do lote os pro-labore ('722') e RPA ('701','702','703')
            #
            dados['categoria_trabalhador'] = "'722','701','702','703'"

            sql = """
                select
                    f.id

                from
                    hr_contract_ferias f
                    join hr_contract c on c.id = f.contract_id
                    join res_company e on e.id = c.company_id
                    join hr_employee ee on ee.id = c.employee_id

                where
                    c.date_start <= '{data_final}' and
                    (c.date_end is null or c.date_end > '{data_final}')
                    and (e.id = {company_id} or e.parent_id = {company_id})
                    and c.categoria_trabalhador not in ({categoria_trabalhador})
                    and (f.vencida = True or f.proporcional = True)
            """
            
            if lote_holerite_obj.contract_id:
                sql += """
                    and c.id = {contract_id}
                """.format(contract_id=lote_holerite_obj.contract_id.id)

            if lote_holerite_obj.provisao:
                sql += """
                    and not exists(
                        select
                            h.contract_ferias_id
                        from
                            hr_payslip h
                        where
                            h.tipo = '{tipo}'
                            and (h.simulacao = True and h.provisao = True)
                            and h.contract_id = c.id
                            and h.date_from >= '{data_inicial}'
                            and h.date_to <= '{data_final}'
                    )
                """
            else:
                sql += """
                    and not exists(
                        select
                            h.contract_ferias_id
                        from
                            hr_payslip h
                        where
                            h.tipo = '{tipo}'
                            and (h.simulacao is null or h.simulacao = False)
                            and h.contract_id = c.id
                            and h.date_from >= '{data_inicial}'
                            and h.date_to <= '{data_final}'
                    )
                """

            sql += """
                order by
                    ee.nome;
            """

            sql = sql.format(**dados)
            #print(sql)
            cr.execute(sql)
            contrato_ids_lista = cr.fetchall()
            contrato_ids = []
            for dados in contrato_ids_lista:
                contrato_ids.append(dados[0])
            #print(contrato_ids)
            res[lote_holerite_obj.id] = contrato_ids

        return res

    _columns = {
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        'data_inicial': fields.date(u'Data inicial', select=True),
        'data_final': fields.date(u'Data final', select=True),
        'company_id': fields.many2one('res.company', u'Unidade/Empresa', select=True),
        'contract_id': fields.many2one('hr.contract', u'Contrato', select=True),
        'tipo': fields.selection([['N', u'Normal'], ['D1', u'1ª parcela do 13º'], ['D2', u'13º']], u'Tipo', select=True),
        'contract_ids': fields.function(get_contract_ids, type='one2many', relation='hr.contract', method=True, string=u'Contratos a gerar'),
        'ferias_ids': fields.function(get_ferias_ids, type='one2many', relation='hr.contract_ferias', method=True, string=u'Férias a gerar'),
        'payslip_ids': fields.function(get_payslip_ids, type='one2many', relation='hr.payslip', method=True, string=u'Holerites gerados'),
        'provisao': fields.boolean(string=u'Provisão?'),
        'tipo_provisao': fields.selection([['D', u'13º'], ['F', u'Férias']], u'Tipo', select=True),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'folha_aberta': fields.boolean(u'Funcionários com folha aberta?'),
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'data_inicial': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[0],
        'data_final': lambda *args, **kwargs: primeiro_ultimo_dia_mes(*mes_passado())[1],
        'tipo': 'N',
        'tipo_provisao': 'D',
        'folha_aberta': True,
    }

    def onchange_ano_mes(self, cr, uid, ids, ano, mes, context={}):
        valores = {}
        retorno = {'value': valores}

        if not ano or not mes:
            return retorno

        if ano < 2013 or ano >= 2020:
            raise osv.except_osv(u'Inválido !', u'Ano inválido')

        data_inicial, data_final = primeiro_ultimo_dia_mes(ano, int(mes))

        valores['data_inicial'] = data_inicial
        valores['data_final'] = data_final

        return retorno

    def atualizar_dados(self, cr, uid, ids, context={}):
        lote_holerite_id = ids[0]

        lote_holerite_obj = self.browse(cr, uid, lote_holerite_id)

        res = {}
        valores = {}
        res['value'] = valores

        if lote_holerite_obj.provisao and lote_holerite_obj.tipo_provisao == 'F':
            ferias_ids = []
            self.pool.get('hr.contract').acao_demorada_recalcula_ferias(cr, uid, ids=[], data_provisao=lote_holerite_obj.data_final, context=context)

            for ferias_obj in lote_holerite_obj.ferias_ids:
                ferias_ids.append(ferias_obj.id)

            valores['ferias_ids'] = ferias_ids
        else:
            contract_ids = []

            for contract_obj in lote_holerite_obj.contract_ids:
                contract_ids.append(contract_obj.id)

            valores['contract_ids'] = contract_ids

        payslip_ids = []
        for payslip_obj in lote_holerite_obj.payslip_ids:
            payslip_ids.append(payslip_obj.id)

        valores['payslip_ids'] = payslip_ids

        return res

    def _gera_folha_e_decimo(self, cr, uid, ids, tipo, lote_holerite_obj, context={}):
        holerite_pool = self.pool.get('hr.payslip')
        input_pool = self.pool.get('hr.payslip.input')
        valores = {}

        #
        # Pega os contratos que faltam, e gera os holerites automaticamente
        #
        folha_aberta = False
        for contrato_obj in lote_holerite_obj.contract_ids:
            #
            # Provisão só gera do funcionário que estiver com a folha fechada
            #
            if lote_holerite_obj.provisao:
                sql = """
                select
                    h.id
                from 
                    hr_payslip h
                where
                    h.contract_id = {contract_id}
                    and h.tipo = 'N'
                    and coalesce(h.simulacao, False) = False
                    and h.state != 'done'
                    and h.date_from >= '{data_inicial}'
                    and h.date_to <= '{data_final}';
                """
                sql = sql.format(contract_id=contrato_obj.id, data_inicial=lote_holerite_obj.data_inicial, data_final=lote_holerite_obj.data_final)
                cr.execute(sql)
                if len(cr.fetchall()) > 0:
                    folha_aberta = True
                    continue
                
            dados = {
                'tipo': tipo,
                'company_id': contrato_obj.company_id.id,
                'employee_id': contrato_obj.employee_id.id,
                'contract_id': contrato_obj.id,
                'date_from': lote_holerite_obj.data_inicial,
                'date_to': lote_holerite_obj.data_final,
                'ano': lote_holerite_obj.ano,
                'mes': lote_holerite_obj.mes,
                'struct_id': contrato_obj.struct_id.id,
            }

            if lote_holerite_obj.provisao:
                dados['simulacao'] = True
                dados['provisao'] = True
                lote_holerite_obj.tipo = 'D2'
                dados['media_inclui_mes'] = True
            else:
                dados['simulacao'] = False
                dados['provisao'] = False

            holerite_id = holerite_pool.create(cr, uid, dados)

            holerite_obj = holerite_pool.browse(cr, uid, holerite_id)

            res = holerite_obj.onchange_ano_mes(lote_holerite_obj.ano, lote_holerite_obj.mes)
            if 'value' in res:
                print(res['value'])
                holerite_obj.write(res['value'])
                holerite_obj = holerite_pool.browse(cr, uid, holerite_id)

            res = holerite_obj.onchange_datas(tipo, contrato_obj.employee_id.id, contrato_obj.id, lote_holerite_obj.data_inicial, lote_holerite_obj.data_final, simulacao=dados['simulacao'])
            print('gerou onchange_datas', res['value'])
            if 'value' in res:
                if 'input_line_ids' in res['value']:
                    if len(res['value']['input_line_ids']):
                        res['value']['input_line_ids'] = [[6, False, res['value']['input_line_ids']]]

                holerite_pool.write(cr, uid, [holerite_obj.id], res['value'])
                holerite_obj = holerite_pool.browse(cr, uid, holerite_id)

            res = holerite_obj.onchange_employee_id(tipo, contrato_obj.employee_id.id,  lote_holerite_obj.data_inicial, lote_holerite_obj.data_final, contract_id=contrato_obj.id, simulacao=dados['simulacao'], provisao=dados['provisao'])
            print('gerou onchange_employee_id', res['value'])
            if 'value' in res:
                valores = res['value']
                #
                # Trata os campos many2one
                #
                line_ids_novo = []
                for li in valores['line_ids']:
                    line_ids_novo.append((4, li))
                valores['line_ids'] = line_ids_novo

                if tipo == 'N':
                    input_novo_ids = []
                    for ili in valores['input_line_ids']:
                        input_novo_ids.append((4, ili))

                    input_ids = input_pool.search(cr, uid, [('employee_id', '=', contrato_obj.employee_id.id), ('payslip_id', '=', False), ('data_inicial', '>=', holerite_obj.date_from), ('data_final', '<=', holerite_obj.date_to)])
                    for ili in input_ids:
                        input_novo_ids.append((4, ili))
                    valores['input_line_ids'] = input_novo_ids

                #afastamento_ids_novo = []
                #for ai in valores['afastamento_ids']:
                #    afastamento_ids_novo.append((4, ai))
                #valores['afastamento_ids'] = afastamento_ids_novo

                #worked_days_line_ids_novo = []
                #for wdli in valores['worked_days_line_ids']:
                #    worked_days_line_ids_novo.append((4, wdli))
                #valores['worked_days_line_ids'] = worked_days_line_ids_novo

                holerite_pool.write(cr, uid, [holerite_obj.id], valores)
                #holerite_obj = holerite_pool.browse(cr, uid, holerite_id)

            #
            # Para os casos em que há mais de 1 contrato, força o contrato atual
            #
            if lote_holerite_obj.tipo == 'N':
                holerite_pool.write(cr, uid, [holerite_obj.id], {'contract_id': contrato_obj.id})
            elif lote_holerite_obj.tipo == 'D1' and contrato_obj.struct_id.estrutura_adiantamento_decimo_terceiro_id:
                holerite_pool.write(cr, uid, [holerite_obj.id], {'contract_id': contrato_obj.id, 'struct_id': contrato_obj.struct_id.estrutura_adiantamento_decimo_terceiro_id.id})
            elif lote_holerite_obj.tipo == 'D2' and contrato_obj.struct_id.estrutura_decimo_terceiro_id:
                holerite_pool.write(cr, uid, [holerite_obj.id], {'contract_id': contrato_obj.id, 'struct_id': contrato_obj.struct_id.estrutura_decimo_terceiro_id.id})

            holerite_obj = holerite_pool.browse(cr, uid, holerite_id)

            if holerite_obj.struct_id:
                try:
                    holerite_obj.compute_sheet()

                    #
                    # No mês de dezembro, força o recálculo para computar a diferença
                    # do 13º considerando o próprio mês de dezembro
                    #
                    if lote_holerite_obj.tipo == 'N' and lote_holerite_obj.mes == '12':
                        holerite_obj.compute_sheet()

                except:
                    #cr.commit()
                    for input_obj in holerite_obj.input_line_ids:
                        if tipo == 'N':
                            input_obj.write({'payslip_id': False})
                        else:
                            input_obj.unlink()

                    holerite_pool.unlink(cr, uid, [holerite_id])
            else:
                for input_obj in holerite_obj.input_line_ids:
                    if tipo == 'N':
                        input_obj.write({'payslip_id': False})
                    else:
                        input_obj.unlink()

                holerite_pool.unlink(cr, uid, [holerite_id])

        lote_holerite_obj.write({'folha_aberta': folha_aberta})
        #contract_ids = []
        #for contract_obj in lote_holerite_obj.contract_ids:
            #contract_ids.append(contract_obj.id)

        #payslip_ids = []
        #for payslip_obj in lote_holerite_obj.payslip_ids:
            #payslip_ids.append(payslip_obj.id)

        #valores['contract_ids'] = lote_holerite_obj.contract_ids
        #valores['payslip_ids'] = lote_holerite_obj.payslip_ids

        return valores

    def _gerar_ferias(self, cr, uid, ids, tipo, lote_holerite_obj, context={}):

        folha_aberta = False
        for contrato_obj in lote_holerite_obj.contract_ids:
            #
            # Provisão só gera do funcionário que estiver com a folha fechada
            #
            if lote_holerite_obj.provisao:
                sql = """
                select
                    h.id
                from 
                    hr_payslip h
                where
                    h.contract_id = {contract_id}
                    and h.tipo = 'N'
                    and coalesce(h.simulacao, False) = False
                    and h.state != 'done'
                    and h.date_from >= '{data_inicial}'
                    and h.date_to <= '{data_final}';
                """
                sql = sql.format(contract_id=contrato_obj.id, data_inicial=lote_holerite_obj.data_inicial, data_final=lote_holerite_obj.data_final)
                cr.execute(sql)
                if len(cr.fetchall()) > 0:
                    folha_aberta = True
                    continue
            
            #
            # Férias vencidas
            #
            try:
                contrato_obj.ferias_vencidas(lote_holerite_obj.data_inicial, lote_holerite_obj.data_final, exclui_simulacao=False, mantem_provisao=True, data_provisao=lote_holerite_obj.data_final, context=context)
                contrato_obj.ferias_proporcionais(lote_holerite_obj.data_inicial, lote_holerite_obj.data_final, exclui_simulacao=False, mantem_provisao=True, data_provisao=lote_holerite_obj.data_final, context=context)
            except:
                pass

        lote_holerite_obj.write({'folha_aberta': folha_aberta})

    def gerar_holerites(self, cr, uid, ids, context={}):
        lote_holerite_id = ids[0]
        lote_holerite_obj = self.browse(cr, uid, lote_holerite_id)

        if lote_holerite_obj.provisao:
            tipo = lote_holerite_obj.tipo_provisao

        else:
            if lote_holerite_obj.tipo == 'N':
                tipo = 'N'
            else:
                tipo = 'D'

        res = {}
        valores = {}
        res['value'] = valores

        if tipo != 'F':
            valores = self._gera_folha_e_decimo(cr, uid, ids, tipo, lote_holerite_obj, context)
            #res['value'] = valores

            #self.gera_relatorio_provisao_13(cr, uid, ids)
        else:
            self._gerar_ferias(cr, uid, ids, tipo, lote_holerite_obj, context)

        return res

    def gerar_relatorio_provisao(self, cr, uid, ids, context={}):
        print('vai gerar os relatorios')
        self.gera_relatorio_provisao_13(cr, uid, ids)
        self.gera_relatorio_provisao_ferias(cr, uid, ids)
        print('jah gerou os relatorios')

    def gera_relatorio_provisao_13(self, cr, uid, ids, context={}):
        for lote_obj in self.browse(cr, uid, ids):
            print('provisao', lote_obj.provisao)
            print('tipo provisao', lote_obj.tipo_provisao)
            if not lote_obj.provisao:
                continue

            if lote_obj.tipo_provisao != 'D':
                continue

            sql = """
                select
                    cc.name as unidade,
                    e.nome as funcionario,
                    c.date_start as data_admissao,
                    --h.data_inicio_periodo_aquisitivo,
                    --h.data_fim_periodo_aquisitivo,
                    case
                        when coalesce(h.meses_decimo_terceiro, 0) < 0 then 0
                        else coalesce(h.meses_decimo_terceiro, 0)
                    end as meses_decimo_terceiro,
                    c.wage as salario_contratual,

                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'SAL_13'), 0) as salario_13,
                    coalesce((select sum(coalesce(hl.total, 0)) from hr_payslip_line hl join hr_salary_rule r on r.id = hl.salary_rule_id where hl.slip_id = h.id and r.tipo_media in ('valor', 'quantidade') and r.sinal = '+' ), 0) as valor_medias,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'BRUTO'), 0) as bruto,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'FGTS'), 0) as fgts,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'BASE_INSS'), 0) as base_inss,
                    coalesce((select hl.rate from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS'), 0) as aliquota_inss,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS'), 0) as inss,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS_EMPRESA'), 0) as inss_empresa,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS_OUTRAS_ENTIDADES'), 0) as inss_outras_entidades,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS_RAT'), 0) as inss_rat,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS_EMPRESA_TOTAL'), 0) as inss_empresa_total,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'LIQ_13'), 0) as liquido,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'PERICULOSIDADE'), 0) as periculosidade

                from
                hr_payslip h
                join hr_contract c on c.id = h.contract_id
                join hr_employee e on e.id = c.employee_id
                join res_company cc on cc.id = h.company_id

                where
                h.simulacao = True
                and h.provisao = True
                and h.tipo = 'D'
                and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
                and (
                    cc.id = {company_id}
                    or cc.parent_id = {company_id}
                )

                order by
                cc.name,
                e.nome;
            """

            filtro = {
                'data_inicial': lote_obj.data_inicial,
                'data_final': lote_obj.data_final,
                'company_id': lote_obj.company_id.id,
            }

            sql = sql.format(**filtro)
            #print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                return

            linhas = []
            for unidade, funcionario, data_admissao, meses_decimo_terceiro, salario_contratual, salario_13, valor_medias, bruto, fgts, base_inss, aliquota_inss, inss, inss_empresa, inss_outras_entidades, inss_rat, inss_empresa_total, liquido, periculosidade in dados:
                linha = DicionarioBrasil()
                linha['unidade'] = unidade or ''
                linha['funcionario'] = funcionario or ''
                linha['data_admissao'] = parse_datetime(data_admissao).date()
                linha['meses_decimo_terceiro'] = meses_decimo_terceiro
                linha['salario_contratual'] = D(salario_contratual or 0)
                linha['salario_13'] = D(salario_13 or 0)
                linha['valor_medias'] = D(valor_medias or 0)
                linha['bruto'] = D(bruto or 0)
                linha['fgts'] = D(fgts or 0)
                linha['base_inss'] = D(base_inss or 0)
                linha['aliquota_inss'] = D(aliquota_inss or 0)
                linha['inss'] = D(inss or 0)
                linha['inss_empresa'] = D(inss_empresa or 0)
                linha['inss_outras_entidades'] = D(inss_outras_entidades or 0)
                linha['inss_rat'] = D(inss_rat or 0)
                linha['inss_empresa_total'] = D(inss_empresa_total or 0)
                linha['liquido'] = D(liquido or 0)
                linha['periculosidade'] = D(periculosidade or 0)

                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Provisão de 13º'
            rel.monta_contagem = False
            rel.colunas = [
                ['funcionario'          , 'C', 60, u'Funcionário', False],
                ['data_admissao'        , 'D', 10, u'Admissão', False],
                ['meses_decimo_terceiro', 'I', 4, u'Avos', False],
                ['salario_contratual', 'F', 10, u'Sal. cont.', True],
                ['salario_13', 'F', 10, u'Sal. 13º', True],
                ['valor_medias', 'F', 10, u'Médias', True],
                ['periculosidade', 'F', 10, u'Periculosidade', True],
                ['bruto', 'F', 10, u'Bruto', True],
                ['fgts', 'F', 10, u'FGTS', True],
                ['base_inss', 'F', 10, u'Base INSS', True],
                ['aliquota_inss', 'I', 4, u'%', False],
                ['inss', 'F', 10, u'INSS', True],
                ['inss_empresa', 'F', 10, u'INSS empresa', True],
                ['inss_outras_entidades', 'F', 10, u'INSS outras', True],
                ['inss_rat', 'F', 10, u'RAT-FAP', True],
                ['inss_empresa_total', 'F', 10, u'Emp. total', True],
                ['liquido', 'F', 10, u'Líquido', True],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['unidade', u'Unidade', False],
            ]
            rel.monta_grupos(rel.grupos)

            rel.band_page_header.elements[-1].text = u'Grupo/Unidade ' + lote_obj.company_id.name + u' -  Competência ' + formata_data(lote_obj.data_inicial) + u' a ' + formata_data(lote_obj.data_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'provisao_13.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            lote_obj.write(dados)

    def gera_relatorio_provisao_ferias(self, cr, uid, ids, context={}):
        for lote_obj in self.browse(cr, uid, ids):
            print('provisao', lote_obj.provisao)
            print('tipo provisao', lote_obj.tipo_provisao)
            if not lote_obj.provisao:
                continue

            if lote_obj.tipo_provisao != 'F':
                continue

            sql = """
                select
                    h.vencida,
                    cc.name as unidade,
                    e.nome as funcionario,
                    c.date_start as data_admissao,
                    h.data_inicio_periodo_aquisitivo,
                    h.data_fim_periodo_aquisitivo,
                    h.dias_ferias,
                    h.dias_ferias / 2.5 as avos,
                    c.wage as salario_contratual,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'FERIAS'), 0) as salario_ferias,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'FERIAS_1_3'), 0) as salario_ferias_1_3,
                    coalesce((select sum(coalesce(hl.total, 0)) from hr_payslip_line hl join hr_salary_rule r on r.id = hl.salary_rule_id where hl.slip_id = h.id and r.tipo_media in ('valor', 'quantidade') and r.sinal = '+' ), 0) as valor_medias,
                    coalesce((select sum(coalesce(hl.total, 0)) from hr_payslip_line hl where hl.slip_id = h.id and hl.code in ('BRUTO', 'FERIAS_1_3')), 0) as bruto,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'FGTS'), 0) as fgts,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'BASE_INSS'), 0) as base_inss,
                    coalesce((select hl.rate from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS'), 0) as aliquota_inss,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS'), 0) as inss,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS_EMPRESA'), 0) as inss_empresa,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS_OUTRAS_ENTIDADES'), 0) as inss_outras_entidades,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS_RAT'), 0) as inss_rat,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'INSS_EMPRESA_TOTAL'), 0) as inss_empresa_total,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'LIQ_FERIAS'), 0) as liquido,
                    coalesce((select hl.total from hr_payslip_line hl where hl.slip_id = h.id and hl.code = 'PERICULOSIDADE'), 0) as periculosidade

                from
                    hr_payslip h
                    join hr_contract c on c.id = h.contract_id
                    join hr_employee e on e.id = c.employee_id
                    join res_company cc on cc.id = h.company_id

                where
                    h.simulacao = True
                    and h.provisao = True
                    and h.tipo = 'F'
                    and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
                    and (
                        cc.id = {company_id}
                        or cc.parent_id = {company_id}
                    )

                order by
                    h.vencida desc,
                    cc.name,
                    e.nome;
            """

            filtro = {
                'data_inicial': lote_obj.data_inicial,
                'data_final': lote_obj.data_final,
                'company_id': lote_obj.company_id.id,
            }

            sql = sql.format(**filtro)
            print(sql)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados) == 0:
                return

            linhas = []
            for vencida, unidade, funcionario, data_admissao, data_inicio_periodo_aquisitivo, data_fim_periodo_aquisitivo, dias_ferias, avos, salario_contratual, salario_ferias, salario_ferias_1_3, valor_medias, bruto, fgts, base_inss, aliquota_inss, inss, inss_empresa, inss_outras_entidades, inss_rat, inss_empresa_total, liquido, periculosidade in dados:
                linha = DicionarioBrasil()
                linha['vencida'] = 'Vencidas' if vencida else 'Proporcionais'
                linha['unidade'] = unidade or ''
                linha['funcionario'] = funcionario or ''
                linha['data_admissao'] = parse_datetime(data_admissao).date()
                linha['data_inicio_periodo_aquisitivo'] = parse_datetime(data_inicio_periodo_aquisitivo).date()
                linha['data_fim_periodo_aquisitivo'] = parse_datetime(data_fim_periodo_aquisitivo).date()
                linha['dias_ferias'] = dias_ferias
                linha['avos'] = avos
                linha['salario_contratual'] = D(salario_contratual or 0)
                linha['salario_ferias'] = D(salario_ferias or 0)
                linha['valor_medias'] = D(valor_medias or 0)
                linha['salario_ferias_1_3'] = D(salario_ferias_1_3 or 0)
                linha['bruto'] = D(bruto or 0)
                linha['fgts'] = D(fgts or 0)
                linha['base_inss'] = D(base_inss or 0)
                linha['aliquota_inss'] = D(aliquota_inss or 0)
                linha['inss'] = D(inss or 0)
                linha['inss_empresa'] = D(inss_empresa or 0)
                linha['inss_outras_entidades'] = D(inss_outras_entidades or 0)
                linha['inss_rat'] = D(inss_rat or 0)
                linha['inss_empresa_total'] = D(inss_empresa_total or 0)
                linha['liquido'] = D(liquido or 0)
                linha['periculosidade'] = D(periculosidade or 0)

                linhas.append(linha)

            rel = RHRelatorioAutomaticoPaisagem()
            rel.title = u'Provisão de Férias'
            rel.monta_contagem = False
            rel.colunas = [
                ['funcionario'          , 'C', 60, u'Funcionário', False],
                ['data_admissao'        , 'D', 10, u'Admissão', False],
                ['data_inicio_periodo_aquisitivo', 'D', 10, u'Período', False],
                ['data_fim_periodo_aquisitivo', 'D', 10, u'Aquisitivo', False],
                ['avos', 'I', 4, u'Avos', False],
                ['dias_ferias', 'F', 4, u'Dias', False],
                ['salario_contratual', 'F', 10, u'Sal. cont.', True],
                ['salario_ferias', 'F', 10, u'Férias', True],
                ['valor_medias', 'F', 10, u'Médias', True],
                ['periculosidade', 'F', 10, u'Periculosidade', True],
                ['salario_ferias_1_3', 'F', 10, u'Férias 1/3', True],
                ['bruto', 'F', 10, u'Bruto', True],
                ['fgts', 'F', 10, u'FGTS', True],
                ['base_inss', 'F', 10, u'Base INSS', True],
                ['aliquota_inss', 'I', 4, u'Alíq. INSS', False],
                ['inss', 'F', 10, u'INSS', True],
                ['inss_empresa', 'F', 10, u'INSS empresa', True],
                ['inss_outras_entidades', 'F', 10, u'INSS outras', True],
                ['inss_rat', 'F', 10, u'RAT-FAP', True],
                ['inss_empresa_total', 'F', 10, u'Emp. total', True],
                ['liquido', 'F', 10, u'Líquido', True],
            ]
            rel.monta_detalhe_automatico(rel.colunas)

            rel.grupos = [
                ['unidade', u'Unidade', False],
                ['vencida', u'Tipo', False],
            ]
            rel.monta_grupos(rel.grupos)

            rel.band_page_header.elements[-1].text = u'Grupo/Unidade ' + lote_obj.company_id.name + u' -  Competência ' + formata_data(lote_obj.data_inicial) + u' a ' + formata_data(lote_obj.data_final)

            pdf = gera_relatorio(rel, linhas)

            dados = {
                'nome': 'provisao_ferias.pdf',
                'arquivo': base64.encodestring(pdf)
            }
            lote_obj.write(dados)
        
    
            

hr_lote_holerite()
