# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from rais import *
from pybrasil.data import parse_datetime, hoje
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, MESES, MESES_DIC, mes_passado
import base64
import re
from pybrasil.data import primeiro_dia_mes, ultimo_dia_mes
from caged import limpa_caged
import re
from integra_rh_caged.models.grrf import Empregado
from pybrasil.valor.decimal import Decimal as D

LIMPA = re.compile(r'[^0-9]')



TIPO_DECLARACAO = [
    ('1', u'Retificação'),
    ('2', u'1ª declaração'),
]

TIPO_ALTERACAO = [
    ('1', u'Nada'),
    ('2', u'Dados cadastrais'),
    ('3', u'Fechamento do estabelecimento'),
]


class hr_rais(orm.Model):
    _name = 'hr.rais'
    _description = 'Arquivo RAIS'
    _order = 'ano desc, mes desc, data desc, company_id'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresas'),
        'responsavel_id': fields.many2one('res.company', u'Empresa responsável', select=True, ondelete='restrict'),
        'employee_id': fields.many2one('hr.employee', u'Responsável', select=True, ondelete='restrict'),
        'ano': fields.integer(u'Ano'),
        'declaracao': fields.selection(TIPO_DECLARACAO, u'Declaração'),
        'nome_arquivo': fields.char(u'Nome arquivo', size=30),
        'data': fields.date(u'Data do Arquivo'),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),
    }

    _defaults = {
        'data': fields.date.today,
        'declaracao' : '2',
        'ano': lambda *args, **kwargs: mes_passado()[0]-1,
    }

    _SQL_REMUNERACAO = """
            select
                cast(coalesce(
                    sum(
                        case
                            when sr.sinal = '+' then hl.total
                            else hl.total * -1
                        end
                    ), 0) as numeric(18,2)
                ) as liquido
            from
                hr_payslip_line as hl
                join hr_salary_rule as sr on hl.salary_rule_id = sr.id
                join hr_payslip h on h.id = hl.slip_id
            where
                sr.sinal = '+'
                and hl.total > 0
                and h.contract_id = {contract_id}
                and coalesce(h.simulacao, False) = False
                and h.tipo = '{tipo}'
                and (
                        (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
                    or
                        (h.tipo = 'N' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
                    or
                        (h.tipo = 'F' and cast(h.date_from - interval '2 days' as date) between '{data_inicial}' and '{data_final}')
                    or
                        (h.tipo = 'D' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
                    )
                -- and hl.holerite_anterior_line_id is null
                and sr.code {filtro_rubricas}
    """

    def _gera_empregados(self, cr, uid, estabelecimento, data_inicial, data_final, sequencia, ano):
        employee_pool = self.pool.get('hr.employee')
        contract_pool = self.pool.get('hr.contract')

        sql = """
            select
                hc.id

            from
                hr_contract hc
                join res_company rc on rc.id = hc.company_id
                join res_partner p on p.id = rc.partner_id
                join hr_employee e on e.id = hc.employee_id
                join hr_job j on j.id = hc.job_id
                join hr_cbo cbo on cbo.id = j.cbo_id
                join hr_payslip h on h.contract_id = hc.id and coalesce(h.simulacao, False) = False

            where
                p.cnpj_cpf = '{cnpj}'
                and hc.categoria_trabalhador not between '700' and '799'
                and coalesce(h.simulacao, False) = False
                and (
                    (h.tipo != 'R' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
                    or
                    (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
                )

            group by
                hc.id, e.nome, hc.date_start, hc.date_end

            order by
                e.nome, hc.date_start, hc.date_end;
        """

        sql = sql.format(cnpj=estabelecimento.cnpj, data_inicial=data_inicial, data_final=data_final)
        #print(sql)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()
        contrato_ids = []
        for lista_contrato in contrato_ids_listas:
            contrato_ids.append(lista_contrato[0])

        #print('contrato_ids', contrato_ids)

        for contrato_obj in contract_pool.browse(cr, 1, contrato_ids):
            empregado_obj = contrato_obj.employee_id
            empregado = RAIS_Empregado()
            empregado.estabelecimento = estabelecimento

            empregado.cnpj = contrato_obj.company_id.partner_id.cnpj_cpf
            empregado.cod_pis_pasep = empregado_obj.nis
            empregado.nome_empregado = empregado_obj.name
            empregado.data_nascimento = parse_datetime(empregado_obj.data_nascimento).date()
            empregado.nacionalidade = 10
            if empregado_obj.estrangeiro_data_chegada:
                empregado.ano_chegada = parse_datetime(empregado.estrangeiro_data_chegada).date()
            empregado.grau_instrucao = empregado_obj.grau_instrucao
            empregado.cpf = empregado_obj.cpf
            empregado.ctps_numero = empregado_obj.carteira_trabalho_numero or ''
            empregado.ctps_serie = empregado_obj.carteira_trabalho_numero or ''
            empregado.data_admissao = parse_datetime(contrato_obj.date_start).date()

            if contrato_obj.tipo_admissao in ('1', '3'):
                empregado.tipo_admissao = '02'
            elif contrato_obj.tipo_admissao in ('2', '4'):
                empregado.tipo_admissao = '04'
                empregado.data_admissao = parse_datetime(contrato_obj.data_transf).date()

            ##if contrato_obj.wage:
                ##data_inicial_wage = str(ano) + '-12-01'
                ##if contrato_obj.date_end and contrato_obj.date_end <= data_final:

                    ##if contrato_obj.unidade_salario == '4':
                        ##empregado.salario_contratual = contrato_obj.salario_mes(data_inicial ,contrato_obj.date_end)
                    ##else:
                        ##empregado.salario_contratual = contrato_obj.salario_hora(data_inicial ,contrato_obj.date_end)

                ##else:
                    ##if contrato_obj.unidade_salario == '4':
                        ##empregado.salario_contratual = contrato_obj.salario_mes(data_inicial_wage ,data_final)
                    ##else:
                        ##empregado.salario_contratual = contrato_obj.salario_hora(data_inicial_wage ,data_final)
            ##else:
                ##for piso in contrato_obj.job_id.piso_salarial_ids:
                    ##empregado.salario_contratual = piso.piso_salarial

            if contrato_obj.unidade_salario == '1':
                empregado.tipo_salario_contratual = '5'
                empregado.salario_contratual = contrato_obj.salario_hora(str(ano) + '-12-01', str(ano) + '-12-31')
            elif contrato_obj.unidade_salario == '4':
                empregado.tipo_salario_contratual = '1'
                empregado.salario_contratual = contrato_obj.salario_mes(str(ano) + '-12-01', str(ano) + '-12-31')

            if contrato_obj.categoria_trabalhador in ('103','901'):
                empregado.horas_semanais = '24'
            elif contrato_obj.horas_mensalista:
                empregado.horas_semanais = str(int(D(contrato_obj.horas_mensalista) / D(5)))
            else:
                empregado.horas_semanais = '44'

            empregado.numero_cbo = contrato_obj.job_id.cbo_id.codigo or ''

            if contrato_obj.categoria_trabalhador == '101':
                empregado.vinculo_empregaticio = '10'

            if contrato_obj.categoria_trabalhador == '102':
                empregado.vinculo_empregaticio = '20'

            if contrato_obj.categoria_trabalhador in ('103','901'):
                empregado.vinculo_empregaticio = '55'

            if contrato_obj.categoria_trabalhador == '104':
                empregado.vinculo_empregaticio = '15'

            if contrato_obj.categoria_trabalhador == '105':
                empregado.vinculo_empregaticio = '60'

            if contrato_obj.categoria_trabalhador == '106':
                empregado.vinculo_empregaticio = '60'

            if contrato_obj.categoria_trabalhador == '107':
                empregado.vinculo_empregaticio = '80'

            if contrato_obj.categoria_trabalhador in ('201','202','203'):
                empregado.vinculo_empregaticio = '40'

            if contrato_obj.categoria_trabalhador in ('301','302','303','304','305'):
                empregado.vinculo_empregaticio = '35'

            if contrato_obj.categoria_trabalhador == '401':
                empregado.vinculo_empregaticio = '80'

            if contrato_obj.categoria_trabalhador in ('701','702','703'):
                empregado.vinculo_empregaticio = '40'

            if contrato_obj.categoria_trabalhador in ('711','712','713'):
                empregado.vinculo_empregaticio = '40'

            if contrato_obj.categoria_trabalhador in ('721','722'):
                empregado.vinculo_empregaticio = '80'

            if contrato_obj.categoria_trabalhador in ('731','732','733','734','735','736','741',751):
                empregado.vinculo_empregaticio = '40'

            if contrato_obj.date_end and contrato_obj.date_end <= data_final:
                #print(contrato_obj.date_end, contrato_obj.employee_id.nome)

                empregado.codigo_desligamento = self.busca_codigo_desligamento(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-12-31')
                empregado.data_desligamento =  parse_datetime(contrato_obj.date_end).date()
                #print(empregado.data_desligamento.strftime('%m'))

                if empregado.codigo_desligamento == '11':
                    #empregado.valor_multa_rescisao_sem_justa_causa = self.valor_remuneracao_rescisao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-12-31', tipo='R')

                    empregado.aviso_previo_indenizado = self._get_aviso_previo(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-12-31')


                    data_inicial = str(ano) + '-01-01'
                    data_final = str(ano) + '-12-31'
                    slip_pool = self.pool.get('hr.payslip')


                    slip_ids = slip_pool.search(cr, 1, [('contract_id', '=', contrato_obj.id),('tipo','=','R'),('data_afastamento','>=', data_inicial),('data_afastamento','<=',data_final)])

                    empregado.valor_multa_rescisao_sem_justa_causa = 0
                    for slip_id in slip_ids:

                        slip_obj = slip_pool.browse(cr, 1, slip_id)
                        if slip_obj.multa_fgts:
                            empregado.valor_multa_rescisao_sem_justa_causa += slip_obj.multa_fgts
                    if contrato_obj.id == 1322:
                        print(empregado.valor_multa_rescisao_sem_justa_causa)


                gratificacoes = self._get_gratificao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-12-31')
                if gratificacoes:
                    for gratificacao in gratificacoes:
                        valor_gratificacao = gratificacao[0]
                        quantidade_gratificacao = gratificacao[1]

                    empregado.valor_gratificoes = D(valor_gratificacao)
                    empregado.quantidade_meses_gratificoes = int(quantidade_gratificacao)

            valores = []
            empregado.remuneracao_janeiro = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-01-31', tipo='N')
            #empregado.remuneracao_janeiro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-01-31', tipo='F')
            empregado.remuneracao_janeiro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-01-31', tipo='R')
            valores.append( empregado.remuneracao_janeiro)
            empregado.remuneracao_fevereiro = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-02-01' , data_final = str(ano) + '-02-28', tipo='N')
            #empregado.remuneracao_fevereiro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-02-01' , data_final = str(ano) + '-02-28', tipo='F')
            empregado.remuneracao_fevereiro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-02-01' , data_final = str(ano) + '-02-28', tipo='R')
            valores.append( empregado.remuneracao_fevereiro)
            empregado.remuneracao_marco = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-03-01' , data_final = str(ano) + '-03-31', tipo='N')
            #empregado.remuneracao_marco += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-03-01' , data_final = str(ano) + '-03-31', tipo='F')
            empregado.remuneracao_marco += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-03-01' , data_final = str(ano) + '-03-31', tipo='R')

            #if contrato_obj.id == 1063:
            #    print(empregado_obj.nome, empregado.remuneracao_marco)

            valores.append( empregado.remuneracao_marco)
            empregado.remuneracao_abril = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-04-01' , data_final = str(ano) + '-04-30', tipo='N')
            #empregado.remuneracao_abril += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-04-01' , data_final = str(ano) + '-04-30', tipo='F')
            empregado.remuneracao_abril += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-04-01' , data_final = str(ano) + '-04-30', tipo='R')
            valores.append( empregado.remuneracao_abril)
            empregado.remuneracao_maio = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-05-01' , data_final = str(ano) + '-05-31', tipo='N')
            #empregado.remuneracao_maio += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-05-01' , data_final = str(ano) + '-05-31', tipo='F')
            empregado.remuneracao_maio += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-05-01' , data_final = str(ano) + '-05-31', tipo='R')
            valores.append( empregado.remuneracao_maio)
            empregado.remuneracao_junho = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-06-01' , data_final = str(ano) + '-06-30', tipo='N')
            #empregado.remuneracao_junho += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-06-01' , data_final = str(ano) + '-06-30', tipo='F')
            empregado.remuneracao_junho += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-06-01' , data_final = str(ano) + '-06-30', tipo='R')
            valores.append( empregado.remuneracao_junho)
            empregado.remuneracao_julho = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-07-01' , data_final = str(ano) + '-07-31', tipo='N')
            #empregado.remuneracao_julho += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-07-01' , data_final = str(ano) + '-07-31', tipo='F')
            empregado.remuneracao_julho += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-07-01' , data_final = str(ano) + '-07-31', tipo='R')
            valores.append( empregado.remuneracao_julho)
            empregado.remuneracao_agosto = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-08-01' , data_final = str(ano) + '-08-31', tipo='N')
            #empregado.remuneracao_agosto += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-08-01' , data_final = str(ano) + '-08-31', tipo='F')
            empregado.remuneracao_agosto += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-08-01' , data_final = str(ano) + '-08-31', tipo='R')
            valores.append( empregado.remuneracao_agosto)
            empregado.remuneracao_setembro = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-09-01' , data_final = str(ano) + '-09-30', tipo='N')
            #empregado.remuneracao_setembro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-09-01' , data_final = str(ano) + '-09-30', tipo='F')
            empregado.remuneracao_setembro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-09-01' , data_final = str(ano) + '-09-30', tipo='R')
            valores.append( empregado.remuneracao_setembro)
            empregado.remuneracao_outubro = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-10-01' , data_final = str(ano) + '-10-31', tipo='N')
            #empregado.remuneracao_outubro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-10-01' , data_final = str(ano) + '-10-31', tipo='F')
            empregado.remuneracao_outubro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-10-01' , data_final = str(ano) + '-10-31', tipo='R')
            valores.append( empregado.remuneracao_outubro)
            empregado.remuneracao_novembro = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-11-01' , data_final = str(ano) + '-11-30', tipo='N')
            #empregado.remuneracao_novembro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-11-01' , data_final = str(ano) + '-11-30', tipo='F')
            empregado.remuneracao_novembro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-11-01' , data_final = str(ano) + '-11-30', tipo='R')
            valores.append( empregado.remuneracao_novembro)
            empregado.remuneracao_dezembro = self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-12-01' , data_final = str(ano) + '-12-31', tipo='N')
            #empregado.remuneracao_dezembro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-12-01' , data_final = str(ano) + '-12-31', tipo='F')
            empregado.remuneracao_dezembro += self.valor_remuneracao(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-12-01' , data_final = str(ano) + '-12-31', tipo='R')
            valores.append( empregado.remuneracao_dezembro)
            empregado.remuneracao_13_adiantamento = self.valor_remuneracao_13(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-11-01' , data_final = str(ano) + '-11-30', tipo='D')
            if empregado.remuneracao_13_adiantamento == 0:
                empregado.mes_13_adiantamento = '00'
            else:
                empregado.mes_13_adiantamento = '11'
            empregado.remuneracao_13 = self.valor_remuneracao_13(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-12-01' , data_final = str(ano) + '-12-31', tipo='D')
            if empregado.remuneracao_13 >= empregado.remuneracao_13_adiantamento:
                empregado.remuneracao_13 -= empregado.remuneracao_13_adiantamento
            if empregado.data_desligamento:
                empregado.remuneracao_13 = self.valor_remuneracao_rescisao_13(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-12-31', tipo='R')

            if empregado.remuneracao_13 == 0:
                empregado.me_13 = '00'
            elif empregado.data_desligamento:
                empregado.mes_13 = empregado.data_desligamento.strftime('%m')
            else:
                empregado.mes_13 = '12'

            empregado.raca_cor = empregado_obj.raca_cor

            if empregado_obj.deficiente_motor or empregado_obj.deficiente_auditivo or empregado_obj.deficiente_mental or empregado_obj.deficiente_reabilitado or empregado_obj.deficiente_visual:
                empregado.indicador_deficiencia = 1
            else:
                empregado.indicador_deficiencia = 2

            if empregado_obj.deficiente_motor:
                empregado.tipo_deficiencia = '1'
            elif empregado_obj.deficiente_auditivo:
                empregado.tipo_deficiencia = '2'
            elif empregado_obj.deficiente_visual:
                empregado.tipo_deficiencia = '3'
            elif empregado_obj.deficiente_mental:
                empregado.tipo_deficiencia = '4'
            elif empregado_obj.deficiente_reabilitado:
                empregado.tipo_deficiencia = '6'
            else:
                empregado.tipo_deficiencia = '0'

            empregado.indicador_alvara = 2

            if empregado_obj.sexo == 'M':
                empregado.sexo = 1
            else:
                empregado.sexo = 2

            afastamentos = self._get_afastamentos(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-12-31')

            if afastamentos:
                count = 1
                dias = 0
                for afastamento in afastamentos:

                    data_inicial_afastamento = afastamento[0]
                    data_final_afastamento = afastamento[1]
                    motivo = afastamento[2]
                    dias_afastamento = afastamento[3]


                    if motivo == 'AUX_ACIDENTE_TRABALHO':
                        motivo = '10'
                    elif motivo in ('AUX_APOSENTADORIA_INVALIDEZ','AUX_ACIDENTE_TRABALHO_15','AUX_DOENCA_15','AUX_RECLUSAO','LICENCA_PATERNIDADE'):
                        motivo = '70'
                    elif motivo == 'AUX_DOENCA_INSS':
                        motivo = '30'
                    elif motivo == 'LICENCA_MATERNIDADE':
                        motivo = '50'
                    else:
                        motivo = '70'

                    if count == 1:
                        empregado.motivo_primeiro_afastamento = motivo
                        empregado.data_inicio_primeiro_afastamento = parse_datetime(data_inicial_afastamento).date()
                        empregado.data_final_primeiro_afastamento = parse_datetime(data_final_afastamento).date()

                    if count == 2:
                        empregado.motivo_segundo_afastamento = motivo
                        empregado.data_inicio_segundo_afastamento = parse_datetime(data_inicial_afastamento).date()
                        empregado.data_final_segundo_afastamento = parse_datetime(data_final_afastamento).date()
                    if count == 3:
                        empregado.motivo_terceiro_afastamento = motivo
                        empregado.data_inicio_terceiro_afastamento = parse_datetime(data_inicial_afastamento).date()
                        empregado.data_final_terceiro_afastamento = parse_datetime(data_final_afastamento).date()

                    dias += dias_afastamento
                    count += 1

                empregado.quantidade_dias_afastamento = int(dias)

            empregado.valor_ferias_indenizadas = self.valor_remuneracao_ferias(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-12-31', tipo='R')

            #self.valor_banco_horas = 0
            #self.quantidade_meses_banco_horas = 0
            #self.valor_dissidio_coletivo = 0
            #self.quantidade_meses_dissidio_coletivo = 0

            empregado.valor_contribuicao_associativa_1 = self.valor_sindicato(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-12-31', tipo="('M_SINDICAL')")
            if empregado.valor_contribuicao_associativa_1 > 0:
                empregado.numero_indicador_sindicato = '1'

                if contrato_obj.sindicato_id:
                    empregado.cnpj_contribuicao_associativa_1 = contrato_obj.sindicato_id.cnpj_cpf or ''

            empregado.valor_contribuicao_sindical = self.valor_sindicato(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-12-31', tipo="('C_SINDICAL','R_6')")
            if empregado.valor_contribuicao_sindical > 0 and contrato_obj.sindicato_id:
                empregado.cnpj_contribuicao_sindical = contrato_obj.sindicato_id.cnpj_cpf or ''

            empregado.valor_contribuicao_assistencial = 0
            if empregado.valor_contribuicao_assistencial > 0 and contrato_obj.sindicato_id:
                empregado.cnpj_contribuicao_assistencial = contrato_obj.sindicato_id.cnpj_cpf or ''

            empregado.valor_contribuicao_confederativa = 0
            if empregado.valor_contribuicao_confederativa > 0 and contrato_obj.sindicato_id:
                empregado.cnpj_contribuicao_confederativa = contrato_obj.sindicato_id.cnpj_cpf or ''

            empregado.municipio_local = contrato_obj.company_id.partner_id.municipio_id.codigo_ibge[:7] or ''

            empregado.horas_extras_trabalhadas_janeiro = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-01-01' , data_final = str(ano) + '-01-31', tipo='N'))

            empregado.horas_extras_trabalhadas_fevereiro = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-02-01' , data_final = str(ano) + '-02-28', tipo='N'))

            empregado.horas_extras_trabalhadas_marco = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-03-01' , data_final = str(ano) + '-03-31', tipo='N'))

            empregado.horas_extras_trabalhadas_abril = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-04-01' , data_final = str(ano) + '-04-30', tipo='N'))

            empregado.horas_extras_trabalhadas_maio = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-05-01' , data_final = str(ano) + '-05-31', tipo='N'))

            empregado.horas_extras_trabalhadas_junho = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-06-01' , data_final = str(ano) + '-06-30', tipo='N'))

            empregado.horas_extras_trabalhadas_julho = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-07-01' , data_final = str(ano) + '-07-31', tipo='N'))

            empregado.horas_extras_trabalhadas_agosto = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-08-01' , data_final = str(ano) + '-08-31', tipo='N'))

            empregado.horas_extras_trabalhadas_setembro = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-09-01' , data_final = str(ano) + '-09-30', tipo='N'))

            empregado.horas_extras_trabalhadas_outubro = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-10-01' , data_final = str(ano) + '-10-31', tipo='N'))

            empregado.horas_extras_trabalhadas_novembro = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-11-01' , data_final = str(ano) + '-11-30', tipo='N'))

            empregado.horas_extras_trabalhadas_dezembro = str(self.valor_hora_extra(cr, uid, contrato_obj.id, data_inicial= str(ano) + '-12-01' , data_final = str(ano) + '-12-31', tipo='N'))

            #print(empregado.quantidade_dias_afastamento, empregado.nome_empregado, sum(valores))
            #if sum(valores) > 0 and empregado.quantidade_dias_afastamento < 365:
            estabelecimento.empregados.append(empregado)
            empregado.sequencial = str(sequencia)
            sequencia += 1

        return sequencia

    def _gera_estabelecimento(self, cr, uid, rais, cnpj, employee_id, data_inicial, data_final, prefixo_estabelecimento):
        partner_pool = self.pool.get('res.partner')
        company_pool = self.pool.get('res.company')
        employee_pool = self.pool.get('hr.employee')

        empresa_id = partner_pool.search(cr, 1, [('cnpj_cpf', '=', cnpj)])[0]
        empresa_obj = partner_pool.browse(cr, 1, empresa_id)

        company_id = company_pool.search(cr, 1, [('partner_id.cnpj_cpf', '=', cnpj)])[0]
        company_obj = company_pool.browse(cr, 1, company_id)
        employee_obj = employee_pool.browse(cr, 1, employee_id)

        estabelecimento = RAIS_Estabelecimento()
        rais.estabelecimentos.append(estabelecimento)

        estabelecimento.sequencial = str(prefixo_estabelecimento)
        estabelecimento.cnpj = empresa_obj.cnpj_cpf
        estabelecimento.razao_social = empresa_obj.razao_social or empresa_obj.name
        estabelecimento.endereco = empresa_obj.endereco or ''
        numero = LIMPA.sub('', empresa_obj.numero) or ''
        estabelecimento.numero += numero
        estabelecimento.bairro = empresa_obj.bairro or ''
        estabelecimento.cep = empresa_obj.cep or ''

        estabelecimento.codigo_municipio = empresa_obj.municipio_id.codigo_ibge[:7] or ''
        estabelecimento.nome_municipio = empresa_obj.municipio_id.nome or ''

        try:
            estabelecimento.estado = empresa_obj.municipio_id.estado_id.uf
        except:
            estabelecimento.estado = '  '

        estabelecimento.telefone = empresa_obj.fone or ''
        estabelecimento.email = employee_obj.user_id.user_email or ''
        estabelecimento.cnae = empresa_obj.cnae_id.codigo or ''

        estabelecimento.natureza_juridica = company_obj.natureza_juridica or ''
        estabelecimento.numero_proprietarios = 1

        estabelecimento.data_base = '01'
        estabelecimento.tipo_incr = 1

        sql = """
            select
                hc.id

            from
                    hr_contract hc
                join res_company rc on rc.id = hc.company_id
                join res_partner p on p.id = rc.partner_id
                join hr_employee e on e.id = hc.employee_id
                join hr_job j on j.id = hc.job_id
                join hr_cbo cbo on cbo.id = j.cbo_id
                join hr_payslip h on h.contract_id = hc.id and coalesce(h.simulacao, False) = False

            where
                    p.cnpj_cpf = '{cnpj}'
                and hc.categoria_trabalhador not between '700' and '799'
                and coalesce(h.simulacao, False) = False
                and (
                    (h.tipo != 'R' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
                    or
                    (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
                )

            group by
                hc.id, e.nome, hc.date_start, hc.date_end

            order by
                e.nome, hc.date_start, hc.date_end;
        """

        sql = sql.format(cnpj=estabelecimento.cnpj, data_inicial=data_inicial, data_final=data_final)
        #print(sql)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()
        if len(contrato_ids_listas) > 0:
            estabelecimento.tipo_rais = 0
        else:
            estabelecimento.tipo_rais = 1

        estabelecimento.cnpj_contr_patro = ''
        estabelecimento.valor_contr_associativa = 0
        estabelecimento.cnpj_contr_sindical = ''
        estabelecimento.valor_contr_sindical = 0
        estabelecimento.cnpj_contr_assintencial = ''
        estabelecimento.valor_contr_assintencial = 0
        estabelecimento.cnpj_contr_confederativa = ''
        estabelecimento.valor_contr_confederativa = 0
        estabelecimento.atividade_ano_base = '1'
        estabelecimento.cnpj_centralizado_contr_sindical = ''

        return estabelecimento

    def _gera_rais(self, cr, uid, cnpj_responsavel, cnpj, employee_id ,ano, declaracao, data_arquivo):
        partner_pool = self.pool.get('res.partner')
        employee_pool = self.pool.get('hr.employee')

        empresa_id = partner_pool.search(cr, 1, [('cnpj_cpf', '=', cnpj)])[0]
        responsal_id = partner_pool.search(cr, 1, [('cnpj_cpf', '=', cnpj_responsavel)])[0]
        empresa_obj = partner_pool.browse(cr, 1, empresa_id)
        responsavel_obj = partner_pool.browse(cr, 1, responsal_id)
        employee_obj = employee_pool.browse(cr, 1, employee_id)

        rais = RAIS()

        rais.sequencial = 1
        rais.cnpj = empresa_obj.cnpj_cpf
        rais.cpf_cnpj_responsavel = responsavel_obj.cnpj_cpf
        rais.razao_social_responsavel = responsavel_obj.razao_social
        rais.tipo_inscricao = '1'
        rais.razao_social = empresa_obj.razao_social
        rais.endereco = responsavel_obj.endereco or ''
        rais.numero =  LIMPA.sub('', responsavel_obj.numero) or ''
        rais.complemento = ''
        rais.bairro = responsavel_obj.bairro or ''
        rais.cep = responsavel_obj.cep or ''
        rais.codigo_municipio = responsavel_obj.municipio_id.codigo_ibge[:7] or ''
        rais.nome_municipio = responsavel_obj.municipio_id.nome or ''
        rais.estado = responsavel_obj.municipio_id.estado_id.uf or ''
        rais.telefone = responsavel_obj.fone or ''
        rais.indetificado_retificacao = declaracao

        if rais.indetificado_retificacao == '1':
            rais.data_retificacao = data_arquivo
        rais.data_geracao = data_arquivo
        rais.email = employee_obj.user_id.user_email or ''
        rais.nome_responsavel = employee_obj.name or ''
        rais.cpf_responsavel = employee_obj.cpf
        rais.crea_retificado = ''
        rais.data_nasc_resp = parse_datetime(employee_obj.data_nascimento).date()

        return rais

    def gera_arquivo(self, cr, uid, ids, context={}):
        if not ids:
            return True

        company_pool = self.pool.get('res.company')
        partner_pool = self.pool.get('res.partner')
        ano = context.get('ano', mes_passado()[0])


        data_inicial = str(ano) + '-01-01'
        data_final = str(ano) + '-12-31'
        company_id = context.get('company_id', 1)
        company_obj = company_pool.browse(cr, 1, company_id)


        for rais_obj in self.browse(cr, uid, ids):
            cnpj = company_obj.partner_id.cnpj_cpf
            responsavel_obj = rais_obj.responsavel_id

            declaracao = rais_obj.declaracao
            data_arquivo = parse_datetime(rais_obj.data).date()

            rais = self._gera_rais(cr, uid, responsavel_obj.partner_id.cnpj_cpf , company_obj.partner_id.cnpj_cpf, rais_obj.employee_id.id, ano, declaracao, data_arquivo)

            sequencia_estabelecimento = 2
            estabelecimento = self._gera_estabelecimento(cr, uid, rais, cnpj, rais_obj.employee_id.id, data_inicial, data_final, sequencia_estabelecimento)
            sequencia_estabelecimento = self._gera_empregados(cr, uid, estabelecimento, data_inicial, data_final, sequencia_estabelecimento + 1, ano)

            arquivo_texto = rais.registro_0()

            total_reg_1 = 1
            total_reg_2 = int(sequencia_estabelecimento - 3)

            arquivo_texto += rais.registro_9(sequencial=sequencia_estabelecimento,total_reg_1=total_reg_1,total_reg_2=total_reg_2)

            dados = {
                'nome_arquivo': 'RAIS' + str(ano).zfill(4) + '.txt',
                'arquivo_texto': arquivo_texto[:-2],
                'arquivo': base64.encodestring(arquivo_texto[:-2]),
            }
            rais_obj.write(dados)

        return True

    def numero_empregados(self, cr, uid, estabelecimento, data_inicial, data_final):
        sql = """
            select count(*)
            from (
            select
                hc.id

            from
                hr_contract hc
                join res_company rc on rc.id = hc.company_id
                join res_partner p on p.id = rc.partner_id
                join hr_employee e on e.id = hc.employee_id
                join hr_job j on j.id = hc.job_id
                join hr_cbo cbo on cbo.id = j.cbo_id
                join hr_payslip h on h.contract_id = hc.id and coalesce(h.simulacao, False) = False

            where
                    p.cnpj_cpf = '{cnpj}'
                and hc.categoria_trabalhador not between '700' and '799'
                and coalesce(h.simulacao, False) = False
                and (
                    (h.tipo != 'R' and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}')
                    or
                    (h.tipo = 'R' and h.data_afastamento between '{data_inicial}' and '{data_final}')
                )

            group by
                hc.id, e.nome, hc.date_start, hc.date_end

            );
        """

        sql = sql.format(cnpj=estabelecimento.cnpj, data_inicial=data_inicial, data_final=data_final)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()
        for lista_contrato in contrato_ids_listas:
            return lista_contrato[0]


    def valor_remuneracao(self, cr, uid, contract_id, data_inicial, data_final, tipo):
        filtro = {
            'contract_id': contract_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo,
        }

        if tipo == 'R':
            filtro['filtro_rubricas'] = """not in ('DESC_INDEVIDO','AVISO_INDENIZADO','INSS_FERIAS_GOZADAS','VAD','SALFAM','KM_RODADO''AUX_TRANSP','ajuda_custo','SALDO_DEVEDOR','PERICULOSIDADE_VALOR','AUX_TRANSP', 'DEV_CONT','DEVOLUCAO_UNIMED','DIFERENCA_INSS','FERIAS_PROPORCIONAL','FERIAS_PROPORCIONAL_1_3','FERIAS_PROPORCIONAL_1_3_AP','FERIAS_PROPORCIONAL_AP','FERIAS_VENCIDA','FERIAS_VENCIDA_1_3','SAL_13', 'SAL_13_AP')"""
        else:
            filtro['filtro_rubricas'] = """not in ('DESC_INDEVIDO','AVISO_INDENIZADO','INSS_FERIAS_GOZADAS','VAD','SALFAM','KM_RODADO''AUX_TRANSP','ajuda_custo','SALDO_DEVEDOR','PERICULOSIDADE_VALOR','AUX_TRANSP', 'DEV_CONT','DEVOLUCAO_UNIMED','DIFERENCA_INSS')"""

        sql = self._SQL_REMUNERACAO.format(**filtro)

        if contract_id == 62:
            print(sql)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        res = D(0)
        if len(contrato_ids_listas) > 0:
            res = D(contrato_ids_listas[0][0])

        return res

    def valor_remuneracao_13(self, cr, uid, contract_id, data_inicial, data_final, tipo):
        filtro = {
            'contract_id': contract_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo,
            'filtro_rubricas': """not in ('INSS_13','DESC_1A_PARC_13','DESC_13','LIQ_13','FGTS_13','DIF_13','BASE_INSS_13','DECIMO_TERCEIRO_PAGO','BASE_FGTS_13')""",
        }
        sql = self._SQL_REMUNERACAO.format(**filtro)
        #print(sql)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        res = D(0)
        if len(contrato_ids_listas) > 0:
            res = D(contrato_ids_listas[0][0])

        return res

    def valor_remuneracao_rescisao(self, cr, uid, contract_id, data_inicial, data_final, tipo):
        filtro = {
            'contract_id': contract_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo,
            'filtro_rubricas': """not in ('FERIAS_PROPORCIONAL_AP','FERIAS_PROPORCIONAL','FERIAS_VENCIDA','FERIAS_PROPORCIONAL_1_3','AVISO_INDENIZADO','SAL_13', 'SAL_13_AP','FERIAS_VENCIDA_1_3','FERIAS_PROPORCIONAL_1_3_AP')""",
        }
        sql = self._SQL_REMUNERACAO.format(**filtro)

        #if contract_id == 1124:
        #    print(sql)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        res = D(0)
        if len(contrato_ids_listas) > 0:
            res = D(contrato_ids_listas[0][0])

        return res

    def valor_remuneracao_rescisao_13(self, cr, uid, contract_id, data_inicial, data_final, tipo):
        filtro = {
            'contract_id': contract_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo,
            'filtro_rubricas': """in ('SAL_13','SAL_13_AP')""",
        }
        sql = self._SQL_REMUNERACAO.format(**filtro)

        #print(sql)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        res = D(0)
        if len(contrato_ids_listas) > 0:
            res = D(contrato_ids_listas[0][0])

        return res

    def valor_remuneracao_ferias(self, cr, uid, contract_id, data_inicial, data_final, tipo):
        filtro = {
            'contract_id': contract_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'tipo': tipo,
            'filtro_rubricas': """in ('FERIAS_PROPORCIONAL','FERIAS_PROPORCIONAL_1_3','FERIAS_PROPORCIONAL_1_3_AP','FERIAS_PROPORCIONAL_AP','FERIAS_VENCIDA','FERIAS_VENCIDA_1_3')""",
        }
        sql = self._SQL_REMUNERACAO.format(**filtro)

        #if contract_id == 1124:
        #    print(sql)

        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        res = D(0)
        if len(contrato_ids_listas) > 0:
            res = D(contrato_ids_listas[0][0])

        return res



    def valor_hora_extra(self, cr, uid, contract_id, data_inicial, data_final, tipo):

        sql = """
            SELECT coalesce(sum(hl.quantity),0)
            FROM hr_payslip_line as hl
            join hr_payslip h on h.id = hl.slip_id
            where hl.code IN ('H100','H50') and h.contract_id = {contract_id}
            and to_char(h.date_from, 'YYYY-MM-DD') >= '{data_inicial}' and to_char(h.date_to, 'YYYY-MM-DD') <= '{data_final}'
            and h.simulacao = False and h.tipo = '{tipo}'
        """
        sql = sql.format(contract_id=contract_id, data_inicial=data_inicial, data_final=data_final, tipo=tipo)

        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        for lista_contrato in contrato_ids_listas:
            if lista_contrato:
                return int(lista_contrato[0])
            else:
                return 0

    def busca_codigo_desligamento(self, cr, uid, contract_id, data_inicial, data_final):
        sql = """
            SELECT
                hp.codigo_desligamento_rais
            FROM
                hr_payslip h
                join hr_payroll_structure hp on hp.id = h.struct_id
            where
                h.contract_id = {contract_id}
                and to_char(h.date_from, 'YYYY-MM-DD') >= '{data_inicial}' and to_char(h.date_to, 'YYYY-MM-DD') <= '{data_final}'
                and h.simulacao = False and h.tipo = 'R'
            order by
                h.id desc
            limit 1
        """

        sql = sql.format(contract_id=contract_id, data_inicial=data_inicial, data_final=data_final)
        cr.execute(sql)
        codigos = cr.fetchall()

        if len(codigos):
            codigo = codigos[0][0]
        else:
            codigo = '10'

        return codigo

    def valor_sindicato(self, cr, uid, contract_id, data_inicial, data_final, tipo):

        sql = """
            SELECT coalesce(sum(hl.total),0)
            FROM hr_payslip_line as hl
            join hr_payslip h on h.id = hl.slip_id
            where hl.code IN {tipo} and h.contract_id = {contract_id}
            and to_char(h.date_from, 'YYYY-MM-DD') >= '{data_inicial}' and to_char(h.date_to, 'YYYY-MM-DD') <= '{data_final}'
            and h.simulacao = False
        """
        sql = sql.format(contract_id=contract_id, data_inicial=data_inicial, data_final=data_final, tipo=tipo)
        #print(sql)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        res = 0
        if len(contrato_ids_listas) > 0:
            res = contrato_ids_listas[0][0]
        return res

    def _get_afastamentos(self, cr, uid, contract_id, data_inicial, data_final):

        sql = """
            select
                afastamento.*,
                cast((afastamento.data_final + interval '1 day') as date) - afastamento.data_inicial as dias

             from

            (
            select
            case
              when ha.data_inicial < '{data_inicial}' then cast('2015-01-01' as date)
              else ha.data_inicial
            end as data_inicial,

            case
              when ha.data_final is null or ha.data_final > '{data_final}' then cast('2015-12-31' as date)
              else ha.data_final - interval '1 day'
            end as data_final,

            hs.code as motivo

            from hr_afastamento ha
            join hr_salary_rule hs on hs.id = ha.rule_id

            where
            ha.contract_id = {contract_id}
            and ha.data_inicial <= '{data_final}'
            and (
            ha.data_final is null
            or ha.data_final >= '{data_inicial}'
            )

            order by
            ha.data_inicial desc
            limit 3

            ) as afastamento

            order by

            afastamento.data_inicial
        """
        sql = sql.format(contract_id=contract_id, data_inicial=data_inicial, data_final=data_final)
        #print(sql)
        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        if len(contrato_ids_listas) > 0:
            return contrato_ids_listas
        else:
            return False

    def _get_gratificao(self, cr, uid, contract_id, data_inicial, data_final):
        sql = """
            SELECT
            coalesce(sum(
            hl.total),0) as valor,
            count(h.id) as quantidade


            FROM hr_payslip_line as hl
            join hr_salary_rule as sr on hl.salary_rule_id = sr.id
            join hr_payslip h on h.id = hl.slip_id
            where sr.sinal = '+' and hl.total > 0 and h.contract_id = {contract_id}
            and to_char(h.date_from, 'YYYY-MM-DD') >= '{data_inicial}' and to_char(h.date_to, 'YYYY-MM-DD') <= '{data_final}'
            and h.simulacao = False
            and sr.code in ('GRAT_FUNC_10','GRAT_FUNC_40')

        """

        sql = sql.format(contract_id=contract_id, data_inicial=data_inicial, data_final=data_final)
        #print(sql)

        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        if len(contrato_ids_listas) > 0:
            return contrato_ids_listas
        else:
            return False

    def _get_aviso_previo(self, cr, uid, contract_id, data_inicial, data_final):
        sql = """
            select
                cast(coalesce(
                    sum(
                        case
                            when sr.sinal = '+' then hl.total
                            else hl.total * -1
                        end
                    ), 0) as numeric(18,2)
                ) as liquido
            from
                hr_payslip_line as hl
                join hr_salary_rule as sr on hl.salary_rule_id = sr.id
                join hr_payslip h on h.id = hl.slip_id
            where
                sr.sinal = '+'
                and hl.total > 0
                and h.contract_id = {contract_id}
                and coalesce(h.simulacao, False) = False
                and h.tipo = 'R'
                and (
                    h.data_afastamento between '{data_inicial}' and '{data_final}'
                    or
                    h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}'
                )
                and sr.code in ('AVISO_INDENIZADO')
        """

        sql = sql.format(contract_id=contract_id, data_inicial=data_inicial, data_final=data_final)
        #print(sql)

        cr.execute(sql)
        contrato_ids_listas = cr.fetchall()

        res = D(0)
        if len(contrato_ids_listas) > 0:
            res = D(contrato_ids_listas[0][0])

        return res



hr_rais()
