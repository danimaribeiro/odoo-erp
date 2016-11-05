# -*- coding: utf-8 -*-


from osv import fields, osv
from pybrasil.data import parse_datetime, hoje, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta
from finan.wizard.finan_relatorio import Report
import os
import base64

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

class hr_afastamento(osv.Model):
    _name = 'hr.afastamento'
    _description = u'Afastamentos'
    _rec_name = 'rule_id'
    _order = 'data_inicial desc, data_final desc'

    #def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        #retorno = {}
        #txt = u''
        #for registro in self.browse(cursor, user_id, ids):
            #txt = registro.codigo #+ ' - Entrando às ' + registro.ocupacao

            #if registro.hora_saida_intervalo_1 and registro.hora_retorno_intervalo_1:
                #txt += u', 1º interv. de ' + float_time(registro.hora_saida_intervalo_1)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_1)[:5]

            #if registro.hora_saida_intervalo_2 and registro.hora_retorno_intervalo_2:
                #txt += u', 2º interv. de ' + float_time(registro.hora_saida_intervalo_2)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_2)[:5]

            #if registro.hora_saida_intervalo_3 and registro.hora_retorno_intervalo_3:
                #txt += u', 3º interv. de ' + float_time(registro.hora_saida_intervalo_3)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_3)[:5]

            #if registro.hora_saida_intervalo_4 and registro.hora_retorno_intervalo_4:
                #txt += u', 4º interv. de ' + float_time(registro.hora_saida_intervalo_4)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_4)[:5]

            #if registro.hora_saida_intervalo_5 and registro.hora_retorno_intervalo_5:
                #txt += u', 5º interv. de ' + float_time(registro.hora_saida_intervalo_5)[:5] + ' a ' + float_time(registro.hora_retorno_intervalo_5)[:5]

            #retorno[registro.id] = txt

        #return retorno

    #def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        #texto = args[0][2]

        #procura = [
            #('codigo', 'like', texto)
        #]
        #return procura

    _columns = {
        'employee_id': fields.many2one('hr.employee', u'Funcionário', select=True),
        'contract_id': fields.many2one('hr.contract', u'Contrato', select=True),
        'data_inicial': fields.date(u'Data de afastamento', select=True),
        'data_final': fields.date(u'Data de retorno', select=True),
        'rule_id': fields.many2one('hr.salary.rule', u'Rubrica', select=True),
        'company_id': fields.related('contract_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa', store=True, select=True),
        'valor_inss': fields.float(u'Valor INSS'),
        'afastamento_relacionado_id': fields.many2one('hr.afastamento', u'Afastamento relacionado', select=True),
        'simulacao_id': fields.many2one('hr.payslip', u'Simulação'),
        'retorno_informado': fields.boolean(u'Não criar afastamento vinculado automático?'),
    }

    def onchange_employee_id(self, cr, uid, ids, employee_id, context={}):
        contract_pool = self.pool.get('hr.contract')

        valores = {
            'contract_id': False,
        }
        res = {
            'value': valores
        }

        if (not employee_id):
            return res

        #
        # Busca o contrato ativo do funcionário, e, caso haja mais de 1,
        # dá um erro
        #
        contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee_id)], order='date_start desc, date_end desc')
        #if len(contract_ids) > 1:
            #raise osv.except_osv(u'Erro!', u'O funcionário tem mais de 1 contrato ativo!')
        #elif len(contract_ids) == 0:
            #raise osv.except_osv(u'Erro!', u'O funcionário não tem nenhum contrato ativo!')

        contract_id = contract_ids[0]
        valores['contract_id'] = contract_id

        return res

    def create(self, cr, uid, dados, context={}):
        res = super(hr_afastamento, self).create(cr, uid, dados, context=context)

        if not dados.get('afastamento_relacionado_id', False):
            self.ajusta_afastamentos_empresa(cr, uid, context=context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        res = super(hr_afastamento, self).write(cr, uid, ids, dados, context=context)

        self.ajusta_afastamentos_empresa(cr, uid, context=context)

        return res

    def unlink(self, cr, uid, ids, context={}):
        res = super(hr_afastamento, self).unlink(cr, uid, ids, context=context)

        self.ajusta_afastamentos_empresa(cr, uid, context=context)

        return res

    def ajusta_afastamentos_empresa(self, cr, uid, context={}):
        #
        # Ajusta primeiro as licenças maternidade
        #
        self.ajusta_afastamentos_licenca_maternidade(cr, uid, context=context)

        rule_pool = self.pool.get('hr.salary.rule')
        ajuste_ids = self.search(cr, uid, [('rule_id.code', 'in', ['AUX_DOENCA_INSS', 'AUX_ACIDENTE_TRABALHO', 'AUX_DOENCA_15', 'AUX_ACIDENTE_TRABALHO_15', 'LICENCA_MATERNIDADE']), ('afastamento_relacionado_id', '=', False), ('retorno_informado', '=', False)])

        aux_doenca_id = rule_pool.search(cr, uid, [('code', '=', 'AUX_DOENCA_INSS'), ('afastamento', '=', True)])[0]
        #aux_doenca_obj = rule_pool.browse(cr, uid, aux_doenca_id[0])
        aux_doenca_15_id = rule_pool.search(cr, uid, [('code', '=', 'AUX_DOENCA_15'), ('afastamento', '=', True)])[0]
        #aux_doenca_15_obj = rule_pool.browse(cr, uid, aux_doenca_15_id[0])
        aux_acidente_id = rule_pool.search(cr, uid, [('code', '=', 'AUX_ACIDENTE_TRABALHO'), ('afastamento', '=', True)])[0]
        #aux_acidente_obj = rule_pool.browse(cr, uid, aux_acidente_id[0])
        aux_acidente_15_id = rule_pool.search(cr, uid, [('code', '=', 'AUX_ACIDENTE_TRABALHO_15'), ('afastamento', '=', True)])[0]
        #aux_acidente_15_obj = rule_pool.browse(cr, uid, aux_acidente_15_id[0])

        dias_15_empresa = 15
        for afastamento_obj in self.browse(cr, uid, ajuste_ids):
            data_afastamento = parse_datetime(afastamento_obj.data_inicial).date()

            if str(data_afastamento) >= '2015-03-01' and str(data_afastamento) <= '2015-06-18':
                dias_15_empresa = 30
            else:
                dias_15_empresa = 15

            dados = {
                'employee_id': afastamento_obj.employee_id.id,
                'contract_id': afastamento_obj.contract_id.id,
                'valor_inss': 0,
            }

            busca = [
                ('employee_id', '=', afastamento_obj.employee_id.id),
                ('contract_id', '=', afastamento_obj.contract_id.id),
            ]

            if afastamento_obj.rule_id.code in ['AUX_DOENCA_INSS', 'AUX_DOENCA_15']:
                rule_id = aux_doenca_id
                rule_15_id = aux_doenca_15_id
            else:
                rule_id = aux_acidente_id
                rule_15_id = aux_acidente_15_id


            if afastamento_obj.rule_id.code in ['AUX_DOENCA_INSS', 'AUX_ACIDENTE_TRABALHO']:
                busca += [('rule_id', '=', rule_15_id)]

                #
                # Verifica se já existe um lançamento com a data correta
                #
                data_inicial = data_afastamento + relativedelta(days=(dias_15_empresa * -1))
                busca += [('data_inicial', '=', str(data_inicial)[:10])]
                busca += [('data_final', '=', str(data_afastamento)[:10])]

                rel_ids = self.search(cr, uid, busca)
                #
                # Se já existe, vincula os 2
                #
                if rel_ids:
                    rel_id = rel_ids[0]
                    cr.execute("""
                        update hr_afastamento set
                        afastamento_relacionado_id = {rel_id}
                        where id = {id};

                        update hr_afastamento set
                        afastamento_relacionado_id = {id}
                        where id = {rel_id};
                    """.format(id=afastamento_obj.id, rel_id=rel_id))

                #
                # Se não existe, vamos lançar um novo, considerando a
                # data de afastamento como sendo a data inicial do período
                # total, se já passaram mais de 15 dias;
                # caso contrário, só trocamos a rubrica para a rubrica
                # de 15 dias pela empresa
                #
                else:
                    if afastamento_obj.data_final:
                        data_final = parse_datetime(afastamento_obj.data_final).date()
                    else:
                        data_final = hoje()

                    dias_passados = data_final - data_afastamento
                    dias_passados = dias_passados.days

                    if dias_passados < dias_15_empresa:
                        cr.execute("""
                            update hr_afastamento
                            set rule_id = {rule_id}
                            where id = {id}
                        """.format(rule_id=rule_15_id, id=afastamento_obj.id)
                        )
                    else:
                        data_final = data_afastamento + relativedelta(days=dias_15_empresa)
                        dados['data_inicial'] = str(data_afastamento)[:10]
                        dados['data_final'] = str(data_final)[:10]
                        dados['rule_id'] = rule_15_id
                        dados['afastamento_relacionado_id'] = afastamento_obj.id
                        rel_id = self.create(cr, uid, dados)
                        cr.execute("""
                            update hr_afastamento set
                            afastamento_relacionado_id = {rel_id},
                            data_inicial = '{data_inicial}'
                            where id = {id}
                        """.format(rel_id=rel_id, id=afastamento_obj.id, data_inicial=str(data_final)[:10])
                        )


            elif afastamento_obj.rule_id.code in ['AUX_DOENCA_15', 'AUX_ACIDENTE_TRABALHO_15']:
                busca += [('rule_id', '=', rule_id)]

                #
                # Verifica se já existe um lançamento com a data correta
                #
                data_inicial = data_afastamento + relativedelta(days=dias_15_empresa)
                busca += [('data_inicial', '=', str(data_inicial)[:10])]

                rel_ids = self.search(cr, uid, busca)
                #
                # Se já existe, vincula os 2
                #
                if rel_ids:
                    rel_id = rel_ids[0]
                    cr.execute("""
                        update hr_afastamento set
                        afastamento_relacionado_id = {rel_id}
                        where id = {id};

                        update hr_afastamento set
                        afastamento_relacionado_id = {id}
                        where id = {rel_id};
                    """.format(id=afastamento_obj.id, rel_id=rel_id))

                #
                # Se não existe, vamos lançar um novo, considerando a
                # data de afastamento se já passaram mais de 15 dias;
                # caso contrário, não fazemos nada
                #
                else:
                    if afastamento_obj.data_final:
                        dias_passados = parse_datetime(afastamento_obj.data_final).date() - data_afastamento
                    else:
                        dias_passados = hoje() - data_afastamento

                    dias_passados = dias_passados.days

                    if dias_passados >= dias_15_empresa:
                        data_final = data_afastamento + relativedelta(days=dias_15_empresa)

                        dados['data_inicial'] = str(data_final)[:10]
                        dados['rule_id'] = rule_id
                        dados['afastamento_relacionado_id'] = afastamento_obj.id
                        rel_id = self.create(cr, uid, dados)
                        cr.execute("""
                            update hr_afastamento set
                            afastamento_relacionado_id = {rel_id},
                            data_final = '{data_final}'
                            where id = {id}
                        """.format(rel_id=rel_id, id=afastamento_obj.id, data_final=str(data_final)[:10])
                        )

    def ajusta_afastamentos_licenca_maternidade(self, cr, uid, context={}):
        rule_pool = self.pool.get('hr.salary.rule')
        ajuste_ids = self.search(cr, uid, [('rule_id.code', '=', 'LICENCA_MATERNIDADE'), ('data_final', '=', False)])

        maternidade_id = rule_pool.search(cr, uid, [('code', '=', 'LICENCA_MATERNIDADE'), ('afastamento', '=', True)])[0]

        for afastamento_obj in self.browse(cr, uid, ajuste_ids):
            #
            # Verifica se já passaram os 120 dias da licença maternidade
            #
            data_afastamento = parse_datetime(afastamento_obj.data_inicial).date()
            data_final = data_afastamento + relativedelta(days=120)

            if data_final >= hoje():
                cr.execute("""
                    update hr_afastamento set
                    data_final = '{data_final}'
                    where id = {id}
                """.format(id=afastamento_obj.id, data_final=str(data_final)[:10])
                )

    def gera_beneficio_incapacidade(self, cr, uid, ids, context={}):
        if not ids:
            return False

        if isinstance(ids, (list, tuple)):
            id = ids[0]
        else:
            id = ids

        rel = Report('Termo de Rescisão', cr, uid)

        beneficio_obj = self.browse(cr, uid, id)


        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'hr_beneficio_incapacidade.jrxml')
        beneficio = 'Benefico_incapacidade.pdf'

        rel.parametros['REGISTRO_ID'] =  id

        if beneficio_obj.rule_id.code in ('AUX_DOENCA_15','AUX_DOENCA_INSS','DESC_AUX_DOENCA_INSS'):
            rel.parametros['DOENCA'] =  True

        elif beneficio_obj.rule_id.code in ('DESC_AUX_ACIDENTE_TRABALHO','AUX_ACIDENTE_TRABALHO','AUX_ACIDENTE_TRABALHO_15'):
            rel.parametros['ACIDENTE'] =  True

        pdf, formato = rel.execute()

        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.afastamento'), ('res_id', '=', id), ('name', '=', beneficio)])
        #
        # Apaga os recibos anteriores com o mesmo nome
        #
        attachment_pool.unlink(cr, uid, attachment_ids)

        dados = {
            'datas': base64.encodestring(pdf),
            'name': beneficio,
            'datas_fname': beneficio,
            'res_model': 'hr.afastamento',
            'res_id': id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)
        return True

    def calcula_licenca_maternidade(self, cr, uid, ids, context={}):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        res = [False, D(0)]

        for afastamento_obj in self.pool.get('hr.afastamento').browse(cr, uid, ids):
            if afastamento_obj.simulacao_id:
                res = [afastamento_obj.simulacao_id.id, D(afastamento_obj.simulacao_id.proventos)]

            dados = {
                'tipo': 'M',
                'simulacao': True,
                'employee_id': afastamento_obj.contract_id.employee_id.id,
                'contract_id': afastamento_obj.contract_id.id,
                'struct_id': afastamento_obj.contract_id.struct_id.id,
                'dias_saldo_salario': 30,
            }

            #
            # Período aquisitivo são os 6 últimos meses, exceto em caso
            # de contratação recente
            #
            data_final = primeiro_dia_mes(afastamento_obj.data_inicial)
            data_final += relativedelta(months=-1)
            data_final = ultimo_dia_mes(data_final)
            data_inicial = data_final + relativedelta(months=-5)
            data_inicial = primeiro_dia_mes(data_inicial)

            if str(data_inicial) < afastamento_obj.contract_id.date_start:
                data_inicial = primeiro_dia_mes(afastamento_obj.contract_id.date_start)

            dados['data_inicio_periodo_aquisitivo'] = str(data_inicial)
            dados['data_fim_periodo_aquisitivo'] = str(data_final)
            data_inicial = data_final + relativedelta(days=1)
            data_final = ultimo_dia_mes(data_inicial)
            dados['date_from'] = str(data_inicial)
            dados['date_to'] = str(data_final)

            simulacao_id = self.pool.get('hr.payslip').create(cr, uid, dados)
            afastamento_obj.write({'simulacao_id': simulacao_id})
            res[0] = simulacao_id
            simulacao_obj = self.pool.get('hr.payslip').browse(cr, uid, simulacao_id)
            simulacao_obj.compute_sheet()
            simulacao_obj = self.pool.get('hr.payslip').browse(cr, uid, simulacao_id)
            res[1] = simulacao_obj.proventos

        print('licenca maternidade', res)

        return res

    def calcula_auxilio_acidente(self, cr, uid, ids, context={}):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        res = [False, D(0)]

        for afastamento_obj in self.pool.get('hr.afastamento').browse(cr, uid, ids):
            if afastamento_obj.simulacao_id:
                res = [afastamento_obj.simulacao_id.id, D(afastamento_obj.simulacao_id.proventos)]

            dados = {
                'tipo': 'C',
                'simulacao': True,
                'employee_id': afastamento_obj.contract_id.employee_id.id,
                'contract_id': afastamento_obj.contract_id.id,
                'struct_id': afastamento_obj.contract_id.struct_id.id,
                'dias_saldo_salario': 30,
            }

            #
            # Período aquisitivo são os 12 últimos meses, exceto em caso
            # de contratação recente
            #
            data_final = primeiro_dia_mes(afastamento_obj.data_inicial)
            data_final += relativedelta(months=-1)
            data_final = ultimo_dia_mes(data_final)
            data_inicial = data_final + relativedelta(months=-11)
            data_inicial = primeiro_dia_mes(data_inicial)

            if str(data_inicial) < afastamento_obj.contract_id.date_start:
                data_inicial = primeiro_dia_mes(afastamento_obj.contract_id.date_start)

            dados['data_inicio_periodo_aquisitivo'] = str(data_inicial)
            dados['data_fim_periodo_aquisitivo'] = str(data_final)
            data_inicial = data_final + relativedelta(days=1)
            data_final = ultimo_dia_mes(data_inicial)
            dados['date_from'] = str(data_inicial)
            dados['date_to'] = str(data_final)

            simulacao_id = self.pool.get('hr.payslip').create(cr, uid, dados)
            afastamento_obj.write({'simulacao_id': simulacao_id})
            res[0] = simulacao_id
            simulacao_obj = self.pool.get('hr.payslip').browse(cr, uid, simulacao_id)
            simulacao_obj.compute_sheet()
            simulacao_obj = self.pool.get('hr.payslip').browse(cr, uid, simulacao_id)
            res[1] = simulacao_obj.proventos

        print('auxilio acidente de trabalho', res)

        return res


hr_afastamento()
