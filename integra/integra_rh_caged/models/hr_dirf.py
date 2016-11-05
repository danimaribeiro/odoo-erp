# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from pybrasil.data import parse_datetime, hoje
from dateutil.relativedelta import relativedelta
import base64
from dirf import DIRF, DIRF_DECPJ, DIRF_BPFDEC, DIRF_REGISTROS, REGISTRO_DIRF_RUBRICA, REGISTRO_DIRF_RUBRICA_ORDEM, DIRF_PSE, DIRF_OPSE, DIRF_TPSE, DIRF_DTPSE
from integra_rh_caged.models import grrf
from pybrasil.valor.decimal import Decimal as D
from integra_rh.models.hr_payslip_input import  mes_passado
from pybrasil.telefone.telefone import limpa_fone
from collections import OrderedDict

TIPO_DECLARACAO = [
    ('S', u'Retificação'),
    ('N', u'Original'),
]


class hr_dirf(orm.Model):
    _name = 'hr.dirf'
    _description = 'Arquivo DIRF'
    _order = 'ano desc, data desc, company_id'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresa'),
        'employee_id': fields.many2one('hr.employee', u'Responsável', select=True, ondelete='restrict'),
        'ano': fields.integer(u'Ano'),
        'declaracao': fields.selection(TIPO_DECLARACAO, u'Declaração'),
        'nome_arquivo': fields.char(u'Nome arquivo', size=30),
        'codigo_receita_idrec': fields.char(u'Código Receita IDREC ', size=5),
        'data': fields.date(u'Data do Arquivo'),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),
        'numero_recibo': fields.integer(u'Numero do Recibo'),
    }

    _defaults = {
        'data': fields.date.today,
        'declaracao' : 'N',
        'ano': lambda *args, **kwargs: mes_passado()[0]-1,
    }

    def gera_arquivo_dirf(self, cr, uid, ids, context={}):
        if not ids:
            return True

        contract_pool = self.pool.get('hr.contract')

        ano = context.get('ano', mes_passado()[0])
        data_inicial = str(ano) + '-01-01'
        data_final = str(ano) + '-12-31'
        data_inicial_13 = str(ano) + '-12-01'
        data_final_13 = str(ano) + '-12-31'

        for dirf_obj in self.browse(cr, uid, ids):
            employee_obj = dirf_obj.employee_id
            company_obj =  dirf_obj.company_id

            dirf = DIRF()

            dirf.ano_referencia = str(ano + 1)
            dirf.ano_calendario = str(ano)

            if dirf_obj.declaracao == 'N':
                dirf.indicador_retificadora = 'N'
            else:
                dirf.indicador_retificadora = 'S'
                dirf.numero_recibo = str(dirf_obj.numero_recibo)

            dirf.identificador_estrutura_leiaute = 'L35QJS2'

            dirf.cpf_respo = employee_obj.cpf or ''
            dirf.nome_respo = employee_obj.nome or ''
            if company_obj.partner_id.fone:
                telefone = limpa_fone(company_obj.partner_id.fone)
                dirf.ddd = telefone[:2] or ''
                dirf.telefone = telefone[2:] or ''
                dirf.ramal = ''
                dirf.fax = ''
                dirf.correio_eletronico = ''

            #
            # Vamos buscar todos os CNPJs das empresas envolvidas
            #
            sql = """
                select
                    p.cnpj_cpf, min(c.id)

                from
                    res_company c
                    join res_partner p on p.id = c.partner_id

                where
                    p.cnpj_cpf like '{cnpj}%'

                group by
                    p.cnpj_cpf

                order by
                    p.cnpj_cpf;
            """
            sql = sql.format(cnpj=company_obj.partner_id.cnpj_cpf[:10])
            cr.execute(sql)
            cnpjs = cr.fetchall()

            arquivo_texto = dirf.registro_DIRF()
            arquivo_texto += dirf.registro_RESPO()
            
            #
            # Verifica as rubricas de convênio médico 
            #
            sql = """
                select
                r.code,
                p.name,
                p.cnpj_cpf
                
                from hr_salary_rule r
                join res_partner p on p.id = r.partner_id
                
                where 
                r.sinal = '-'
                order by 
                p.cnpj_cpf             
            """
            cr.execute(sql)
            convenio_medico = cr.fetchall()
            
            for rubrica, nome, cnpj in convenio_medico:
                if 'TPSE_' + cnpj not in REGISTRO_DIRF_RUBRICA:
                    REGISTRO_DIRF_RUBRICA['TPSE_' + cnpj] = []
                    
                REGISTRO_DIRF_RUBRICA['TPSE_' + cnpj].append(rubrica)
            

            #for cnpj, company_id in cnpjs:
            if True:
                dirf_decpj = DIRF_DECPJ()
                #company_obj = self.pool.get('res.company').browse(cr, uid, company_id)

                dirf_decpj.cnpj = company_obj.partner_id.cnpj_cpf
                dirf_decpj.nome_empresarial = company_obj.partner_id.razao_social or company_obj.partner_id.name
                dirf_decpj.cpf_responsavel = employee_obj.cpf
                dirf_decpj.codigo_receita_idrec = dirf_obj.codigo_receita_idrec or '0561'

                arquivo_texto += dirf_decpj.registro_DECPJ()
                arquivo_texto += dirf_decpj.registro_IDREC()

                #
                # Buscando os contratos a serem incluídos na DIRF
                #
                sql = """
                    select
                        hc.id

                    from
                            hr_contract hc
                        join res_company rc on rc.id = hc.company_id
                        join res_partner p on p.id = rc.partner_id
                        join hr_employee e on e.id = hc.employee_id

                    where
                        p.cnpj_cpf like '{cnpj}%'
                        and hc.date_start <= '{data_final}'

                    order by
                        e.cpf, e.nome, hc.date_start, hc.date_end;
                """

                sql = sql.format(cnpj=company_obj.partner_id.cnpj_cpf[:10], data_inicial=data_inicial, data_final=data_final)
                print(sql)
                cr.execute(sql)
                contrato_ids_listas = cr.fetchall()
                contrato_ids = []
                for contrato_id, in contrato_ids_listas:
                    contrato_ids.append(contrato_id)

                #
                # Agora, para cada contrato, vamos acumular as rubricas nos seus
                # devidos registros na DIRF
                #
                # Criamos um dicionário para conter e acumular os registros
                # e uma lista para controlar os funcionários que tiveram retenção
                # de IR sobre as férias na rescisão
                #
                registros = OrderedDict()
                irpf_ferias_rescisao = []

                print(contrato_ids)
                for contrato_obj in contract_pool.browse(cr, 1, contrato_ids):
                    if contrato_obj.id in [681,634]:
                        print(contrato_obj.id)
                        print(contrato_obj.employee_id.nome)

                    if contrato_obj.employee_id.id not in registros:
                        registros[contrato_obj.employee_id.id] = {}

                    registro_atual = registros[contrato_obj.employee_id.id]

                    #
                    # Agora, para cada holerite do contrato, vamos trazer
                    # as rubricas, e analisar cada uma
                    #
                    sql = """
                    select
                        h.id

                    from
                        hr_payslip h

                    where
                        h.simulacao = False and
                        h.contract_id = {contract_id}
                        and ((
                                h.tipo = 'N'
                                and h.date_from >= '{data_inicial}'
                                and h.date_to <= '{data_final}'
                            )
                            or (
                                h.tipo = 'R'
                                and h.data_afastamento between '{data_inicial}' and '{data_final}'
                            )
                            or (
                                h.tipo = 'D'
                                and h.date_from >= '{data_inicial_13}'
                                and h.date_to <= '{data_final_13}'
                            )
                            or (
                                h.tipo = 'F'
                                and to_char(h.date_from - interval '2 days', 'YYYY-MM-DD') between '{data_inicial}' and '{data_final}'
                            )
                        )

                    order by
                        h.date_from, h.date_to;
                    """

                    sql = sql.format(contract_id=contrato_obj.id, data_inicial=data_inicial, data_final=data_final, data_inicial_13=data_inicial_13, data_final_13=data_final_13)
                    if contrato_obj.employee_id.id == 748:
                        print(sql)

                    cr.execute(sql)
                    lista_holerite_ids = cr.fetchall()
                    holerite_ids = []
                    for holerite_id, in lista_holerite_ids:
                        holerite_ids.append(holerite_id)

                    for holerite_obj in self.pool.get('hr.payslip').browse(cr, uid, holerite_ids):
                        for linha_obj in holerite_obj.line_ids:
                            #
                            # Para cada rubrica no holerite, vamos verificar em qual
                            # registro da DIRF ela se encaixa
                            #
                            for registro_dirf in REGISTRO_DIRF_RUBRICA:
                                for codigo_rubrica in REGISTRO_DIRF_RUBRICA[registro_dirf]:
                                    #
                                    # O holerite de férias só vem o IRPF
                                    #
                                    if holerite_obj.tipo == 'F':
                                        if codigo_rubrica != 'IRPF':
                                            continue

                                    if linha_obj.code == codigo_rubrica:
                                        #
                                        # Se é a primeira vez que o registro está sendo
                                        # somado, cria a estrutura dos meses
                                        #
                                        if not registro_dirf in registro_atual:
                                            registro_atual[registro_dirf] = {
                                                '01': D(0),
                                                '02': D(0),
                                                '03': D(0),
                                                '04': D(0),
                                                '05': D(0),
                                                '06': D(0),
                                                '07': D(0),
                                                '08': D(0),
                                                '09': D(0),
                                                '10': D(0),
                                                '11': D(0),
                                                '12': D(0),
                                                '13': D(0),
                                            }

                                        #
                                        # Buscamos o mês de competência da rubrica
                                        #
                                        if holerite_obj.tipo == 'D' or '_13' in codigo_rubrica:
                                            mes = '13'
                                        elif holerite_obj.tipo == 'N':
                                            mes = holerite_obj.date_from[5:7]
                                        elif holerite_obj.tipo == 'F':
                                            mes = str(parse_datetime(holerite_obj.date_from) + relativedelta(days=-2))[5:7]
                                        else:  # Rescisão
                                            mes = holerite_obj.data_afastamento[5:7]

                                        #
                                        # Por fim, acumulamos o valor total da rubrica
                                        # no mês correspondente
                                        #
                                        registro_atual[registro_dirf][mes] += D(linha_obj.total)

                                        #
                                        # Identifica se o funcionário teve retenção de IR sobre
                                        # as férias na rescisão
                                        #
                                        if codigo_rubrica == 'IRPF_FERIAS':
                                            irpf_ferias_rescisao.append(holerite_obj.employee_id.cpf)

                #
                # Neste ponto, vamos ter uma estrutura assim:
                # {
                #     empregado: {
                #         codigo_registro_dirf: {
                #             mes_01: valor,
                #             mes_02: valor,
                #             mes_03: valor,
                #             mes_04: valor,
                #             mes_05: valor,
                #             mes_06: valor,
                #             mes_07: valor,
                #             mes_08: valor,
                #             mes_09: valor,
                #             mes_10: valor,
                #             mes_11: valor,
                #             mes_12: valor,
                #             mes_13: valor,
                #         }
                #     }
                # }
                #
                for empregado_id in registros:
                    empregado_obj = self.pool.get('hr.employee').browse(cr, uid, empregado_id)
                    empregado = DIRF_BPFDEC()
                    empregado.cpf = empregado_obj.cpf
                    empregado.nome = empregado_obj.name

                    #
                    # se a soma dos mes for 0 este empregado não pode ir na dirf.
                    #
                    if 'RTRT' not in registros[empregado_id]:
                        continue
                    soma = registros[empregado_id]['RTRT']['01']
                    soma += registros[empregado_id]['RTRT']['02']
                    soma += registros[empregado_id]['RTRT']['03']
                    soma += registros[empregado_id]['RTRT']['04']
                    soma += registros[empregado_id]['RTRT']['05']
                    soma += registros[empregado_id]['RTRT']['06']
                    soma += registros[empregado_id]['RTRT']['07']
                    soma += registros[empregado_id]['RTRT']['08']
                    soma += registros[empregado_id]['RTRT']['09']
                    soma += registros[empregado_id]['RTRT']['10']
                    soma += registros[empregado_id]['RTRT']['11']
                    soma += registros[empregado_id]['RTRT']['12']
                    soma += registros[empregado_id]['RTRT']['13']

                    if soma == 0:
                        continue
                    arquivo_texto += empregado.registro()

                    for registro_dirf in REGISTRO_DIRF_RUBRICA_ORDEM:
                        empregado_registro = DIRF_REGISTROS()

                        tem_registro = registro_dirf in registros[empregado_id]
                        #
                        # Caso o empregado tenha tido retenção de ir nas férias
                        # na rescisão, os valores de férias proporcionais e vencidas
                        # na rescisão tem que ir zerados
                        #
                        if empregado_obj.cpf in irpf_ferias_rescisao and registro_dirf == 'RIIRP':
                            tem_registro = False

                        if tem_registro:
                            empregado_registro.codigo_registro = registro_dirf
                            empregado_registro.mes_01 = registros[empregado_id][registro_dirf]['01']
                            empregado_registro.mes_02 = registros[empregado_id][registro_dirf]['02']
                            empregado_registro.mes_03 = registros[empregado_id][registro_dirf]['03']
                            empregado_registro.mes_04 = registros[empregado_id][registro_dirf]['04']
                            empregado_registro.mes_05 = registros[empregado_id][registro_dirf]['05']
                            empregado_registro.mes_06 = registros[empregado_id][registro_dirf]['06']
                            empregado_registro.mes_07 = registros[empregado_id][registro_dirf]['07']
                            empregado_registro.mes_08 = registros[empregado_id][registro_dirf]['08']
                            empregado_registro.mes_09 = registros[empregado_id][registro_dirf]['09']
                            empregado_registro.mes_10 = registros[empregado_id][registro_dirf]['10']
                            empregado_registro.mes_11 = registros[empregado_id][registro_dirf]['11']
                            empregado_registro.mes_12 = registros[empregado_id][registro_dirf]['12']
                            empregado_registro.mes_13 = registros[empregado_id][registro_dirf]['13']
                        else:
                            empregado_registro.codigo_registro = registro_dirf
                            empregado_registro.mes_01 = 0
                            empregado_registro.mes_02 = 0
                            empregado_registro.mes_03 = 0
                            empregado_registro.mes_04 = 0
                            empregado_registro.mes_05 = 0
                            empregado_registro.mes_06 = 0
                            empregado_registro.mes_07 = 0
                            empregado_registro.mes_08 = 0
                            empregado_registro.mes_09 = 0
                            empregado_registro.mes_10 = 0
                            empregado_registro.mes_11 = 0
                            empregado_registro.mes_12 = 0
                            empregado_registro.mes_13 = 0

                        arquivo_texto += empregado_registro.registro()
            
                        

            #
            # Verifica as rubricas de convênio médico 
            #
            sql = """
                select distinct
                p.codigo_ans,
                p.name,
                p.cnpj_cpf
                
                from hr_salary_rule r
                join res_partner p on p.id = r.partner_id
                
                where 
                r.sinal = '-'
                order by 
                p.cnpj_cpf             
            """
            cr.execute(sql)
            convenio_medicos = cr.fetchall()
            
            if len(convenio_medicos) > 0:
                                
                dirf_pse = DIRF_PSE()              
                arquivo_texto += dirf_pse.registro_PSE()
                
                for codigo_ans, nome_convenio, cnpj in convenio_medicos:
                    
                    dirf_opse = DIRF_OPSE()
                    dirf_opse.cnpj_plano = cnpj 
                    dirf_opse.nome_empresa = nome_convenio 
                    dirf_opse.registro_ans = codigo_ans or ''
                    
                    arquivo_texto += dirf_opse.registro_OPSE()
                    for empregado_id in registros:
                        
                        empregado_obj = self.pool.get('hr.employee').browse(cr, uid, empregado_id)
                        
                        dirf_tpse = DIRF_TPSE()                        
                        dirf_tpse.cpf = empregado_obj.cpf
                        dirf_tpse.nome = empregado_obj.name
                        
                        registro_empregado = registros[empregado_id]
                        codigo_tpse = 'TPSE_' + cnpj
                        
                        if codigo_tpse in registro_empregado:
                            registro_tpse = registro_empregado[codigo_tpse]
                            
                            soma = registro_tpse['01']
                            soma += registro_tpse['02']
                            soma += registro_tpse['03']
                            soma += registro_tpse['04']
                            soma += registro_tpse['05']
                            soma += registro_tpse['06']
                            soma += registro_tpse['07']
                            soma += registro_tpse['08']
                            soma += registro_tpse['09']
                            soma += registro_tpse['10']
                            soma += registro_tpse['11']
                            soma += registro_tpse['12']
                            soma += registro_tpse['13']
        
                            if soma == 0:
                                continue
                            else:
                                dirf_tpse.valor_pago = soma                            
                            
                        
                        arquivo_texto += dirf_tpse.registro_TPSE()
                                        
            
            arquivo_texto += dirf.registro_FIM()

            dados = {
                'nome_arquivo': 'DIRF' + str(ano).zfill(4) + '.txt',
                'arquivo_texto': arquivo_texto[:-2],
                'arquivo': base64.encodestring(arquivo_texto[:-2]),
            }

            dirf_obj.write(dados)

        return True
