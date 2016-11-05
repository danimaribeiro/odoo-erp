# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from datetime import datetime,timedelta
from pybrasil.inscricao import limpa_formatacao
from pybrasil.base import tira_acentos



class hr_caged(orm.Model):
    _name = 'hr_caged'
    _description = 'Arquivo CAGED'

    _columns = {
        'data_geracao': fields.date(u'Data da Geraço do Arquivo'),
        'titulo_caged': fields.char(u'Nome do arquivo', size=30),
        'company_id': fields.many2one('res.company', 'Empresa'),
        'employee_id': fields.many2one('hr.employee',u'Funcionário Responsavel'),
        'identificador': fields.char(u'Nro Identificador CAGED', size=14),
        'tipo_alteracao': fields.selection([('1', 'Nada a Alterear'), ('2', u'Alterar Dados Cadastrais'), ('3', u'Fechamento do Estabelecimento')], u'Alteração'),
        'ddd': fields.char(u'DDD', size=4),
        'fone': fields.char(u'Fone', size=8),
        'ramal': fields.char(u'Ramal', size=5),
        'primeira_declaracao': fields.selection([('1', 'Primeira Declaração'), ('2', u'Já Infomou anteriormente')], u'Declaração'),

        #'arquivo': fields.binary(u'Arquivo', readonly=True),
    }

    _defaults = {
        'data_geracao': fields.date.today,
        'primeira_declaracao' : '2',
    }

    def gera_arquivo_caged(self, cr, uid, ids, context=None):
        data_geracao = context.get('data_geracao', False)
        employee_id = context.get('employee_id', False)
        company_id = context.get('company_id', False)
        tipo_alteracao = context.get('tipo_alteracao', False)
        identificador = context.get('identificador', False)
        ddd = context.get('ddd', False)
        fone = context.get('fone', False)
        ramal = context.get('ramal', False)
        primeira_declaracao = context.get('primeira_declaracao', False)
        employee_pool = self.pool.get('hr.employee')
        contract_pool = self.pool.get('hr.contract')
        company_pool = self.pool.get('res.company')
        partner_pool = self.pool.get('res.partner')

        matriz_obj = company_pool.browse(cr, uid, company_id)
        raiz_cnpj = matriz_obj.partner_id.cnpj_cpf[:10]
        empresa_ids = company_pool.search(cr, uid, [('partner_id.cnpj_cpf', 'like', raiz_cnpj + '%')]                                          , order='partner_id')
        contador = 0
        periodo = data_geracao[:7]
        inicio_periodo = periodo + '-01'
        arq_caged = []
        arq_a_caged = []
        arq_caged_todos_C = []
        arq_caged_todos_B = []
        sequencial_b = 1     # inicia em 1, ja reservando o 1 para o arquivo A = sequencia 00001
        sequencial_c = 2     # inicia em 2, ja reservando o 2 para o arquivo b = sequencia 00002
        tot_fun_geral = 0
        m_cria_a = 0
        m_tot_ad_e_dem = 0
        for empresa_obj in company_pool.browse(cr, uid, empresa_ids):
            m_espacos = "                                   " # 35 possições
            sequencial_b += 1
            m_achou_empresa = 1
            m_cria_b = 0
            arq_b_caged = []
            arq_c_caged = []
            tot_fun_admintidos = 0
            tot_fun_demitidos = 0
            company_ids = partner_pool.browse(cr, uid,company_id)
            contract_ids = contract_pool.search(cr, uid, [('company_id', '=' , empresa_obj.id)])
            employee_ids = employee_pool.search(cr, uid, [('company_id', '=' , empresa_obj.id)])

            for funcionario_obj in contract_pool.browse(cr, uid, contract_ids):

                if funcionario_obj.date_end == False:
                    tot_fun_geral += 1

                if funcionario_obj.date_start[:7] == periodo or str(funcionario_obj.date_end)[:7] == periodo:
                    m_cria_b += 1
                    sequencial_c += 1
                    employee_obj =  funcionario_obj.employee_id

                    print "entrou"
                    print employee_obj.nome

                    m_espacos = "                                        " # 40 possições
                    m_sequencia = str(sequencial_c)
                    m_seq = "00000"
                    m_sequencia = m_seq[:(-len(m_sequencia))] + m_sequencia

                    if funcionario_obj.wage == 0:
                        m_salario = '0.00'
                    else:
                        m_salario = str(funcionario_obj.wage)

                    m_sal = "00000000"
                    m_salario = m_sal[:(-len(m_salario))] + (m_salario[:(len(m_salario)-3)])+(m_salario[(len(m_salario)-2):(len(m_salario)+1)])

                    m_nascimento = employee_obj.data_nascimento[8:10]+employee_obj.data_nascimento[5:7]+employee_obj.data_nascimento[0:4]

                    m_admissao = funcionario_obj.date_start[8:10]+funcionario_obj.date_start[5:7]+funcionario_obj.date_start[0:4]

                    m_tipo_mov = 'xx'
                    if funcionario_obj.primeiro_emprego:
                        m_tipo_mov = '10'
                    elif funcionario_obj.tipo_admissao == '1':
                        m_tipo_mov = '20'
                    elif funcionario_obj.tipo_admissao == '3':
                        m_tipo_mov = '20'
                    elif funcionario_obj.tipo_admissao == '4':
                        m_tipo_mov = '35'
                    elif funcionario_obj.tipo_admissao == '2':
                        m_tipo_mov = '70'
                    elif funcionario_obj.tipo_contrato == '2':
                        m_tipo_mov = '25'

                    m_tot_def = 0
                    m_tipo_def = 0
                    if employee_obj.deficiente_motor or employee_obj.deficiente_auditivo or employee_obj.deficiente_visual or employee_obj.deficiente_reabilitado:
                        m_deficiente = '1'
                        if employee_obj.deficiente_motor:
                            m_tot_def += 1
                            m_tipo_def = '1'
                        elif employee_obj.deficiente_auditivo:
                            m_tot_def += 1
                            m_tipo_def = '2'
                        elif employee_obj.deficiente_visual:
                            m_tot_def += 1
                            m_tipo_def = '3'
                        elif employee_obj.deficiente_reabilitado:
                            m_tipo_def = '6'
                            m_tot_def = 0
                    else:
                        m_deficiente = '2'

                    if m_tot_def > 1:
                        m_tipo_def = '5'
                    elif m_tot_def == 0:
                        m_tipo_def = '0'

                    if funcionario_obj.categoria_trabalhador == '103' or funcionario_obj.categoria_trabalhador == '901':
                        m_tipo_trab = '1'
                    else:
                        m_tipo_trab = '2'

                ## aqui cria o arquivo C dos admitidos no periodo
                if funcionario_obj.date_start[:7] == periodo:
                    arq_c_caged.append('C' + '1' + m_sequencia + employee_obj.nis + employee_obj.sexo)
                    arq_c_caged.append(m_nascimento + employee_obj.grau_instrucao + "    " + m_salario)
# ver campo horas semana - onde tirar ???
                    arq_c_caged.append('horas semana' + m_admissao + m_tipo_mov + '  ')
                    arq_c_caged.append(employee_obj.nome.ljust(40)[:40])
                    arq_c_caged.append(m_sal[:(8-(len(employee_obj.carteira_trabalho_numero[:8])))] + employee_obj.carteira_trabalho_numero)
                    arq_c_caged.append(employee_obj.carteira_trabalho_serie[-4:] + m_espacos[:7] + employee_obj.raca_cor + m_deficiente)
                    arq_c_caged.append(funcionario_obj.job_id.cbo_id.codigo + m_tipo_trab + employee_obj.carteira_trabalho_estado)
                    arq_c_caged.append(m_tipo_def + employee_obj.cpf + employee_obj.address_home_id.cep)
                    arq_c_caged.append(m_espacos + m_espacos + m_espacos[:1])

                    arq_c_caged = ''.join(arq_c_caged)
                    tot_fun_admintidos += 1
                    m_tot_ad_e_dem += 1
                    tot_fun_geral -= 1
                    arq_caged_todos_C.append(arq_c_caged)
                    arq_c_caged = []

                ## aqui cria o arquivo C dos demitidos no periodo
                if str(funcionario_obj.date_end)[:7] == periodo:
                    m_saida = funcionario_obj.date_end[8:10]
                    arq_c_caged.append('C' + '1' + m_sequencia + employee_obj.nis + employee_obj.sexo)
                    arq_c_caged.append(m_nascimento + employee_obj.grau_instrucao + "    " + m_salario)
                    arq_c_caged.append('horas semana' + m_admissao + m_tipo_mov + m_saida)
                    arq_c_caged.append(employee_obj.nome.ljust(40)[:40])
                    arq_c_caged.append(m_sal[:(8-(len(employee_obj.carteira_trabalho_numero[:8])))] + employee_obj.carteira_trabalho_numero)
                    arq_c_caged.append(employee_obj.carteira_trabalho_serie[-4:] + m_espacos[:7] + employee_obj.raca_cor + m_deficiente)
                    arq_c_caged.append(funcionario_obj.job_id.cbo_id.codigo + m_tipo_trab + employee_obj.carteira_trabalho_estado)
                    arq_c_caged.append(m_tipo_def + employee_obj.cpf + employee_obj.address_home_id.cep)
                    arq_c_caged.append(m_espacos + m_espacos + m_espacos[:1])

                    arq_c_caged = ''.join(arq_c_caged)
                    tot_fun_demitidos += 1
                    m_tot_ad_e_dem += 1
                    tot_fun_geral += 1
                    arq_caged_todos_C.append(',' + arq_c_caged)
                    arq_c_caged = []

            ## fim do FOR dos funcionarios, hora de criar o arquivo B.

            if m_cria_b > 0:
                m_espacos = "                                        " # 40 possições
                m_sequencia = str(sequencial_b)
                m_seq = "00000"
                m_sequencia = m_seq[:(-len(m_sequencia))] + m_sequencia
                # company_ids
                arq_b_caged.append('B' + '1')
                arq_b_caged.append(empresa_obj.cnpj_cpf[:2] + empresa_obj.cnpj_cpf[3:5] + empresa_obj.cnpj_cpf[7:10] + empresa_obj.cnpj_cpf[11:15] + empresa_obj.cnpj_cpf[16:19])
                arq_b_caged.append(m_sequencia + primeira_declaracao)
                arq_b_caged.append(tipo_alteracao)
                arq_b_caged.append(company_ids.cep[:5]+company_ids.cep[6:9])
                arq_b_caged.append('     ')
                arq_b_caged.append(company_ids.razao_social.ljust(40)[:40])
                arq_b_caged.append(company_ids.endereco.ljust(40)[:40])
                arq_b_caged.append(company_ids.bairro.ljust(20)[:20])
                arq_b_caged.append(company_ids.municipio_id.estado_id.uf)
                m_sequencia = str(tot_fun_geral)
                m_seq = "00000"
                m_sequencia = m_seq[:(-len(m_sequencia))] + m_sequencia
    # ver aqui os X
                arq_b_caged.append(m_sequencia + 'X' ) # quando incluir no cad de empresa, alterar PORTE
                arq_b_caged.append(company_ids.cnae_id.codigo)
                arq_b_caged.append(ddd + fone + m_espacos.ljust(50)[:50]) # no m_espacos por e_mail da empresa
                arq_b_caged.append(m_espacos[:27])
                arq_b_caged = ''.join(arq_b_caged)
                tot_fun_geral = 0
                arq_caged_todos_B.append(',' + arq_b_caged)
                arq_b_caged = []
            else:
                sequencial_b -= 1

        if m_cria_a > 0:
            # é da matriz_obj
            arq_a_caged.append('AL2009  ')
            arq_a_caged.append(periodo[5:7]+periodo[:5])
            arq_a_caged.append(tipo_alteracao)
            arq_a_caged.append('00001' + '1')
            arq_a_caged.append(identificador + matriz_obj.name.ljust(40)[:40])
            arq_a_caged.append(matriz_obj.partner_id.endereco.ljust(40)[:40])
            arq_b_caged.append(matriz_obj.partner_id.cep[:5]+matriz_obj.partner_id.cep[6:9])
            arq_a_caged.append(matriz_obj.partner_id.municipio_id.estado_id.uf)
            arq_a_caged.append(ddd + fone + ramal)

            m_sequencia = str(sequencial_b)
            m_seq = "00000"
            m_sequencia = m_seq[:(-len(m_sequencia))] + m_sequencia
            arq_a_caged.append(m_sequencia)

            m_sequencia = str(m_tot_ad_e_dem)
            m_seq = "00000"
            m_sequencia = m_seq[:(-len(m_sequencia))] + m_sequencia
            arq_a_caged.append(m_sequencia)
            arq_a_caged.append(m_espacos.ljust(92)[:92])
            arq_a_caged =  ''.join(arq_b_caged)

# o arquivo A é o arq_a_caged
# o arquivo B pode ter mais de um, ai eu acumulei um atraz do outro separado por uma ',' no arq_caged_todos_B
# o arquivo C fiz a mesma coisa que no B acumulei separado por ',', no arq_caged_todos_C
# ai é so ver como deve montar o arquivo do CAGED e gravar como esta na linha abaixo
# salvar o aquivo caged com o seguinte nome = CGED2014.M02  - 02 especifica o mes que esta na variavel PERIODO  -  CGED+periodo[0:4].M+periodo[5:7]



