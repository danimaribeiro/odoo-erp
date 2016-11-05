# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import osv, fields
import base64
from pybrasil.inscricao import limpa_formatacao
from pybrasil.data import parse_datetime, mes_passado, primeiro_dia_mes, ultimo_dia_mes, data_hora_horario_brasilia, formata_data
from pybrasil.febraban.banco import BANCO_CODIGO, Remessa
from pybrasil.febraban.pessoa import Funcionario, Beneficiario
from pybrasil.febraban.holerite import Holerite, Holerite_Detalhe, Holerite_Informacao
from pybrasil.valor.decimal import Decimal as D
from collections import OrderedDict
from dateutil.relativedelta import relativedelta

class finan_remessa_folha(osv.Model):
    _name = 'finan.remessa_folha'
    _description = 'Remessa de Folha de Pagamento'
    _order = 'data_pagamento desc, id desc'
    _rec_name = 'nome_arquivo'

    def get_prepara_payslip_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}

        holerite_pool = self.pool.get('hr.payslip')

        for remessa_folha_obj in self.browse(cr, uid, ids):
            if remessa_folha_obj.tipo in ['N', 'D', 'P']:
                data = data_hora_horario_brasilia(parse_datetime(remessa_folha_obj.data_pagamento))

                if data:
                    data = data.date()

                if remessa_folha_obj.tipo == 'D':
                    data_inicial = primeiro_dia_mes(data)
                    data_final = ultimo_dia_mes(data)

                else:
                    data_inicial = primeiro_dia_mes(mes_passado(data))
                    data_final = ultimo_dia_mes(mes_passado(data))

                dados = {
                    'tipo': remessa_folha_obj.tipo,
                    'data_inicial': data_inicial,
                    'data_final': data_final,
                    'company_id': remessa_folha_obj.company_id.id,
                }

                where = ' '
                if remessa_folha_obj.payslip_id:
                    dados['holerite_id'] = remessa_folha_obj.payslip_id.id
                    where = "and h.id = {holerite_id} "

                where += "and h.date_from >= '{data_inicial}' and h.date_to <= '{data_final}' "

                if remessa_folha_obj.tipo == 'P':
                    dados['tipo'] = 'N'
                    where += "and cc.categoria_trabalhador = '722' "
                else:
                    where += "and cc.categoria_trabalhador != '722' "

            elif remessa_folha_obj.tipo == 'F':
                dados = {
                    'tipo': remessa_folha_obj.tipo,
                    'data_pagamento': remessa_folha_obj.data_pagamento,
                    'company_id': remessa_folha_obj.company_id.id,
                    'ferias_id': remessa_folha_obj.payslip_id.id,
                }
                if remessa_folha_obj.payslip_id.id:
                    where = "and h.id = {ferias_id}"
                else:
                    where = ""

            elif remessa_folha_obj.tipo == 'R':
                dados = {
                    'tipo': remessa_folha_obj.tipo,
                    'data_pagamento': remessa_folha_obj.data_pagamento,
                    'company_id': remessa_folha_obj.company_id.id,
                    'rescisao_id': remessa_folha_obj.payslip_id.id,
                }
                if remessa_folha_obj.payslip_id.id:
                    where = "and h.id = {rescisao_id}"
                else:
                    where = ""

            if not remessa_folha_obj.comprovante_salario:
                where += """ and h.remessa_id is null """

            sql = """
                select
                    h.id

                from hr_payslip h
                join res_company c on c.id = h.company_id
                join hr_employee e on e.id = h.employee_id
                join hr_contract cc on cc.id = h.contract_id

                where
                    h.state = 'done'
                    and h.tipo = '{tipo}'
                    and cc.categoria_trabalhador not in ('701', '702', '703')
                    and (h.company_id = {company_id} or c.parent_id = {company_id})
                    """ + where + """

                order by
                    e.nome;"""

            sql = sql.format(**dados)
            print(sql)

            cr.execute(sql)
            holerite_ids_lista = cr.fetchall()
            holerite_ids = []
            for dados in holerite_ids_lista:
                holerite_ids.append(dados[0])
            res[remessa_folha_obj.id] = holerite_ids

        return res

    _columns = {
        'partner_bank_id': fields.many2one('res.partner.bank', u'Conta bancária', required=True, select=True, ondelete='restrict'),

        'raiz_cnpj': fields.related('partner_bank_id', 'raiz_cnpj', type='char', string=u'Raiz do CNPJ', size=10),

        'data_pagamento': fields.date(u'Data de pagamento original', required=True, select=True),
        'data_pagamento_desejada': fields.date(u'Data de pagamento desejada'),
        'data': fields.datetime(u'Data e hora'),

        'payslip_ids': fields.one2many('hr.payslip', 'remessa_id', u'Holerites na remessa'),
        'prepara_payslip_ids': fields.function(get_prepara_payslip_ids, type='one2many', relation='hr.payslip', method=True, string=u'Holerites a incluir'),

        'tipo': fields.selection((('N', u'Normal'), ('F', u'Férias'), ('R', u'Rescisão'), ('D', u'Décimo terceiro'), ('P', u'Pro-labore')), string=u'Tipo'),
        'company_id': fields.many2one('res.company', u'Empresa', select=True, ondelete='restrict'),
        'payslip_id': fields.many2one('hr.payslip', u'Rescisão/Férias', select=True, ondelete='restrict'),

        'nome_arquivo': fields.char(u'Nome arquivo', size=120),
        'arquivo': fields.binary(u'Arquivo'),

        'nome_arquivo_comprovante': fields.char(u'Nome arquivo Comprovante', size=120),
        'arquivo_comprovante': fields.binary(u'Arquivo Comprovante'),

        'arquivo_texto': fields.text(u'Arquivo'),
        'lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro', select=True, ondelete='restrict'),
        'valor': fields.float(u'Valor'),
        'nome_arquivo_retorno': fields.char(u'Nome arquivo', size=120),
        'arquivo_retorno': fields.binary(u'Arquivo de retorno'),
        'arquivo_texto_retorno': fields.text(u'Arquivo de retorno'),
        'sequencia': fields.integer(u'Sequência'),
        'comprovante_salario': fields.boolean(u'Gerar comprovante salarial?'),
    }

    _defaults = {
        'data': lambda *a: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tipo': 'N',
    }

    def onchange_partner_bank_id(self, cr, uid, ids, partner_bank_id, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        if not partner_bank_id:
            return res

        bank_obj = self.pool.get('res.partner.bank').browse(cr, uid, partner_bank_id)

        valores['raiz_cnpj'] = bank_obj.raiz_cnpj

        return res

    def atualiza(self, cr, uid, id, context={}):
        return True

    def gera_arquivo(self, cr, uid, id, context={}):
        if isinstance(id, list):
            id = id[0]

        remessa_obj = self.browse(cr, uid, id)
        remessa_obj.valor = 0

        if (not remessa_obj.sequencia):
            if (not remessa_obj.comprovante_salario):
                cr.execute("""select max(r.sequencia) from finan_remessa_folha r
                    where r.partner_bank_id = {bank_id} and (r.comprovante_salario is null or r.comprovante_salario = false);""".format(bank_id=remessa_obj.partner_bank_id.id))
            else:
                cr.execute("""select max(r.sequencia) from finan_remessa_folha r
                    where r.partner_bank_id = {bank_id} and r.comprovante_salario = true;""".format(bank_id=remessa_obj.partner_bank_id.id))

            dados = cr.fetchall()
            if len(dados):
                sequencia = dados[0][0] or 0
                remessa_obj.write({'sequencia': sequencia + 1})
                remessa_obj.sequencia = sequencia + 1


        #
        # Cria uma lista com os funcionários ou holerites a incluir
        #
        lista_func = []
        lista_holerites = []

        if len(remessa_obj.payslip_ids):
            holerite_ids = remessa_obj.payslip_ids
        else:
            holerite_ids = remessa_obj.prepara_payslip_ids

        registro = 1
        valor_total = 0
        sequencia_arquivo = 2
        for h_obj in holerite_ids:
            if not (h_obj.bank_id and h_obj.banco_conta and h_obj.banco_agencia and h_obj.valor_liquido):
                continue

            if h_obj.bank_id.bic != remessa_obj.partner_bank_id.bank_bic:
                continue

            if not h_obj.valor_liquido:
                continue

            func = Funcionario()
            func.matricula = str(h_obj.contract_id.id)
            func.nome = h_obj.employee_id.nome.strip()
            func.conta.numero = h_obj.banco_conta.strip().replace('-', '')
            func.conta.digito = func.conta.numero[-1]
            func.conta.numero = func.conta.numero[:-1]
            func.holerite_id = h_obj.id
            func.cnpj_cpf = h_obj.employee_id.cpf or ''
            func.rg = h_obj.employee_id.rg_numero or ''
            func.nis = h_obj.employee_id.nis or ''
            func.carteira_trabalho = h_obj.employee_id.carteira_trabalho_numero or ''
            func.carteira_trabalho += h_obj.employee_id.carteira_trabalho_serie or ''
            func.data_admissao = parse_datetime(h_obj.contract_id.date_start)
            func.funcao = h_obj.contract_id.job_id.name or ''
            func.registro = registro
            registro += 2
            func.sequencia_arquivo = sequencia_arquivo
            sequencia_arquivo += 1

            func.agencia.numero = h_obj.banco_agencia.strip()
            if '-' in func.agencia.numero:
                func.agencia.numero = func.agencia.numero.split('-')[0]

            func.valor_creditar = D(h_obj.valor_liquido) or D(0)
            remessa_obj.valor += D(func.valor_creditar)
            valor_total += D(func.valor_creditar)

            if not remessa_obj.comprovante_salario:
                lista_func.append(func)
                h_obj.write({'remessa_id': remessa_obj.id})

            else:
                holerite = Holerite()
                holerite.tipo_comprovante = h_obj.tipo
                holerite.mes_referencia = h_obj.mes + str(h_obj.ano)
                holerite.data_liberacao = parse_datetime(remessa_obj.data_pagamento_desejada or remessa_obj.data_pagamento).date()

                #
                # DETALHE Devem estar na seqüência “1,2,3,4,5 e 6”
                #
                lista_rubrica = []
                total_credito = D(0)
                total_debito = D(0)

                for line_id in h_obj.line_ids:
                    #
                    # 1 creditos
                    #
                    if line_id.sinal == '+':
                        rubrica = Holerite_Detalhe()
                        rubrica.codigo_lancamento = line_id.salary_rule_id.codigo
                        rubrica.descricao_lancamento = line_id.salary_rule_id.name
                        rubrica.valor_lancamento = D(line_id.total or 0).quantize(D('0.01'))
                        rubrica.identificador_lancamento = 1
                        rubrica.sequencia_arquivo = sequencia_arquivo
                        lista_rubrica.append(rubrica)

                        total_credito += rubrica.valor_lancamento
                        sequencia_arquivo += 1

                #
                # 2 Total creditos
                #
                rubrica = Holerite_Detalhe()
                rubrica.valor_lancamento = total_credito
                rubrica.identificador_lancamento = 2
                rubrica.sequencia_arquivo = sequencia_arquivo
                lista_rubrica.append(rubrica)
                sequencia_arquivo += 1

                #
                # 3 debitos
                #
                for line_id in h_obj.line_ids:
                    if line_id.sinal == '-':
                        rubrica = Holerite_Detalhe()
                        rubrica.codigo_lancamento = line_id.salary_rule_id.codigo
                        rubrica.descricao_lancamento = line_id.salary_rule_id.name
                        rubrica.valor_lancamento = D(line_id.total or 0).quantize(D('0.01'))
                        rubrica.identificador_lancamento = 3
                        rubrica.sequencia_arquivo = sequencia_arquivo
                        lista_rubrica.append(rubrica)

                        total_debito += rubrica.valor_lancamento
                        sequencia_arquivo += 1

                #
                # 4 Total debitos
                #
                rubrica = Holerite_Detalhe()
                rubrica.valor_lancamento = total_debito
                rubrica.identificador_lancamento = 4
                rubrica.sequencia_arquivo = sequencia_arquivo
                lista_rubrica.append(rubrica)
                sequencia_arquivo += 1

                #  5/6 Liquido

                liquido = total_credito - total_debito

                if liquido > 0:
                    rubrica = Holerite_Detalhe()
                    rubrica.valor_lancamento = liquido
                    rubrica.identificador_lancamento = 5
                    rubrica.sequencia_arquivo = sequencia_arquivo
                    lista_rubrica.append(rubrica)
                else:
                    rubrica = Holerite_Detalhe()
                    rubrica.valor_lancamento = liquido
                    rubrica.identificador_lancamento = 6
                    rubrica.sequencia_arquivo = sequencia_arquivo
                    lista_rubrica.append(rubrica)

                sequencia_arquivo += 1

                informacao = Holerite_Informacao()
                informacao.data_pagamemto = parse_datetime(h_obj.date_to).date() + relativedelta(days=+5)
                informacao.qtd_horas_trabalhadas = 0
                informacao.vr_salario_base = D(h_obj.contract_id.wage or 0).quantize(D('0.01'))
                informacao.qtd_falta_ferias = 0
                if h_obj.tipo == 'F':
                    informacao.data_inicio_periodo_aquisitivo = parse_datetime(h_obj.data_inicio_periodo_aquisitivo)
                    informacao.data_fim_periodo_aquisitivo = parse_datetime(h_obj.data_fim_periodo_aquisitivo)
                    informacao.data_inicio_periodo_gozo = parse_datetime(h_obj.date_from)
                    informacao.data_fim_periodo_gozo = parse_datetime(h_obj.date_to)

                for line_id in h_obj.line_ids:

                    if line_id.salary_rule_id.code == 'BASE_INSS':
                        informacao.vr_base_inss = D(line_id.total or 0).quantize(D('0.01'))

                    if line_id.salary_rule_id.code == 'BASE_INSS_13':
                        informacao.vr_base_inss_13 = D(line_id.total).quantize(D('0.01'))

                    if line_id.salary_rule_id.code == 'BASE_IRPF':
                        informacao.vr_base_irrf_salario = D(line_id.total).quantize(D('0.01'))

                    if line_id.salary_rule_id.code == 'BASE_IRPF_FERIAS':
                        informacao.vr_base_irrf_ferias = D(line_id.total).quantize(D('0.01'))

                    if line_id.salary_rule_id.code == 'BASE_IRPF_FERIAS':
                        informacao.vr_base_irrf_fgts = D(line_id.total).quantize(D('0.01'))

                    if line_id.salary_rule_id.code == 'FGTS':
                        informacao.vr_fgts = D(line_id.total).quantize(D('0.01'))

                    if line_id.salary_rule_id.code == 'SALARIO_FAMILIA':
                        informacao.qtd_dep_salario_familia = line_id.quantity

                    if line_id.salary_rule_id.code == 'DEDUCAO_DEPENDENTES':
                        informacao.qtd_dep_irrf = line_id.quantity

                informacao.sequencia_arquivo = sequencia_arquivo
                sequencia_arquivo += 1

                holerite.holerite_informacao = informacao
                holerite.holerite_detalhe = lista_rubrica
                holerite.funcionario = func
                lista_holerites.append(holerite)

        #
        # Gera a remessa
        #
        remessa = Remessa()
        if remessa_obj.partner_bank_id.bank_bic == '237':
            if remessa_obj.comprovante_salario:
                remessa.tipo = 'CNAB_250'
                remessa.holerites = lista_holerites
            else:
                remessa.tipo = 'CNAB_240'
                remessa.funcionarios = lista_func
        else:
            #remessa.tipo = 'CNAB_240'
            remessa.tipo = 'CNAB_200'
            remessa.funcionarios = lista_func

        remessa.data_hora = parse_datetime(remessa_obj.data)
        remessa.sequencia = remessa_obj.sequencia

        if remessa_obj.data_pagamento_desejada:
            remessa.data_debito = parse_datetime(remessa_obj.data_pagamento_desejada)
        else:
            remessa.data_debito = parse_datetime(remessa_obj.data_pagamento)

        remessa.beneficiario = Beneficiario()
        remessa.beneficiario.banco = BANCO_CODIGO[remessa_obj.partner_bank_id.bank_bic]
        remessa.beneficiario.nome = remessa_obj.partner_bank_id.partner_id.razao_social
        remessa.beneficiario.cnpj_cpf = remessa_obj.partner_bank_id.cnpj_cpf or ''
        remessa.beneficiario.agencia.numero = remessa_obj.partner_bank_id.agencia or ''
        remessa.beneficiario.agencia.digito = remessa_obj.partner_bank_id.agencia_digito or ''
        remessa.beneficiario.conta.numero = remessa_obj.partner_bank_id.acc_number or ''
        remessa.beneficiario.conta.digito = remessa_obj.partner_bank_id.conta_digito or ''
        remessa.beneficiario.conta.convenio = remessa_obj.partner_bank_id.codigo_convenio or ''
        remessa.beneficiario.valor_total = valor_total
        remessa.beneficiario.registro = registro
        remessa.beneficiario.sequencia_arquivo = sequencia_arquivo

        if remessa_obj.comprovante_salario:
            dados = {
                'nome_arquivo': 'comprovante_salarial_' + remessa_obj.company_id.name.replace(' ', '_') + '_' + remessa_obj.data.replace(' ', '_') + '.txt',
                'arquivo': base64.encodestring(remessa.arquivo_remessa),
                'arquivo_texto': remessa.arquivo_remessa,
                'valor': remessa_obj.valor,
            }
        else:
            dados = {
                'nome_arquivo': 'folha_' + remessa_obj.company_id.name.replace(' ', '_') + '_' + remessa_obj.data.replace(' ', '_') + '.txt',
                'arquivo': base64.encodestring(remessa.arquivo_remessa),
                'arquivo_texto': remessa.arquivo_remessa,
                'valor': remessa_obj.valor,
            }

        return remessa_obj.write(dados)

    def gera_lancamento(self, cr, uid, ids, context={}):
        rubrica_pool = self.pool.get('hr.salary.rule')
        documento_pool = self.pool.get('finan.documento')
        lancamento_pool = self.pool.get('finan.lancamento')
        cc_pool = self.pool.get('finan.centrocusto')
        campos = cc_pool.campos_rateio(cr, uid)

        liquido_ids = rubrica_pool.search(cr, 1, [('code', '=', 'LIQ')])
        liquido_obj = rubrica_pool.browse(cr, 1, liquido_ids[0])
        prolabore_ids = rubrica_pool.search(cr, 1, [('code', '=', 'PROLABORE')])
        prolabore_obj = rubrica_pool.browse(cr, 1, prolabore_ids[0])


        for remessa_obj in self.browse(cr, uid, ids):
            conta_id = liquido_obj.finan_conta_despesa_id.id

            if remessa_obj.tipo == 'N':
                doc_folha_id = documento_pool.id_folha(cr, 1)
            elif remessa_obj.tipo == 'F':
                doc_folha_id = documento_pool.id_ferias(cr, 1)

                if liquido_obj.finan_conta_despesa_ferias_id:
                    conta_id = liquido_obj.finan_conta_despesa_ferias_id.id

            elif remessa_obj.tipo == 'R':
                doc_folha_id = documento_pool.id_rescisao(cr, 1)

                if liquido_obj.finan_conta_despesa_rescisao_id:
                    conta_id = liquido_obj.finan_conta_despesa_rescisao_id.id

            elif remessa_obj.tipo == 'D':
                doc_folha_id = documento_pool.id_decimo(cr, 1)

                if liquido_obj.finan_conta_despesa_13_id:
                    conta_id = liquido_obj.finan_conta_despesa_13_id.id

            elif remessa_obj.tipo == 'P':
                doc_folha_id = documento_pool.id_prolabore(cr, 1)

                conta_id = prolabore_obj.finan_conta_despesa_id.id

            dados = {
                'tipo': 'P',
                'data_documento': remessa_obj.data[:10],
                'data_vencimento': remessa_obj.data_pagamento[:10],
                'company_id': remessa_obj.company_id.id,
                'partner_id': remessa_obj.company_id.partner_id.id,
                'documento_id': doc_folha_id,
                'provisionado': False,
                'conta_id': conta_id,
                'valor_documento': remessa_obj.valor,
                'numero_documento': 'REMFOL-' + str(remessa_obj.id).zfill(4),
            }

            if remessa_obj.tipo == 'N':
                dados['numero_documento'] += ' ' + formata_data(mes_passado(remessa_obj.data_pagamento), '%m/%Y')

            if remessa_obj.lancamento_id:
                lanc_id = remessa_obj.lancamento_id.id
                lancamento_pool.write(cr, uid, [lanc_id], dados)
                for ro in remessa_obj.lancamento_id.rateio_ids:
                    ro.unlink()

            else:
                lanc_id = lancamento_pool.create(cr, uid, dados)
                remessa_obj.write({'lancamento_id': lanc_id})

            #
            # Prepara agora o rateio
            #
            rateio = {}
            for h_obj in remessa_obj.payslip_ids:
                if remessa_obj.tipo == 'P':
                    h_obj.realiza_rateio(rateio=rateio, conta_obj=prolabore_obj.finan_conta_despesa_id)
                else:
                    h_obj.realiza_rateio(rateio=rateio)

            dados = cc_pool.monta_dados(rateio, campos, lista_dados=[], valor=remessa_obj.valor)

            print('dados do rateio da folha', dados)

            rateio_ids = []
            for d in dados:
                if d['valor_documento'] != 0 and d['porcentagem'] != 0:
                    rateio_ids += [(0, lanc_id, d)]

            lancamento_pool.write(cr, uid, [lanc_id], {'rateio_ids': rateio_ids})

        return True

    def trata_retorno(self, cr, uid, id, context={}):
        if isinstance(id, list):
            id = id[0]

        remessa_obj = self.browse(cr, uid, id)

        arq_texto = base64.decodestring(remessa_obj.arquivo_retorno)
        remessa_obj.write({'arquivo_texto_retorno': arq_texto})

        #
        # Cria uma lista com os funcionários a incluir
        #
        funcionarios = {}
        arq_ret = remessa_obj.arquivo_texto_retorno.split('\n')
        if arq_ret[-1] in ('', '\r'):
            arq_ret = arq_ret[:-1]
        arq_ret = arq_ret[1:-1]
        valor_final = D(0)
        for linha in arq_ret:
            if remessa_obj.partner_bank_id.bank_bic == '237':
                agencia = linha[62:67]
                # 07050
                conta = linha[72:79]
                digito = linha[80]

                nome = linha[82:120]
                matricula = int(linha[120:126])
                valor = D(linha[126:139]) / D('100.00')
                ok = linha[150:152] == '  '

            elif remessa_obj.partner_bank_id.bank_bic == '748':
                #
                # Somente lidar com os registros tipos A e B
                #
                if linha[13] != 'A':
                    continue

                agencia = linha[23:28]
                conta = linha[29:41]
                nome = linha[43:73]
                matricula = int(linha[73:93].replace('ID_', ''))

                valor = D(linha[119:134]) / D('100.00')
                ok = linha[230:232] == 'BD'  # Incluído com sucesso

            #
            # Desvincula os funcionários com erro do arquivo atual
            # para uqe eles vão num novo arquivo
            #
            #print(agencia, conta, digito, nome, matricula, valor, ok)
            remove_ids = []
            if not ok:
                for h_obj in remessa_obj.payslip_ids:
                    if h_obj.employee_id.id == matricula:
                        remove_ids.append(h_obj.id)
                        remessa_obj.valor -= D(h_obj.valor_liquido)
                        texto = agencia + '|' + conta + '|' + digito + '|' + nome
                        print('retirado do arquivo', texto.encode('utf-8'))
            else:
                valor_final += valor

            for id in remove_ids:
                self.pool.get('hr.payslip').write(cr, uid, id, {'remessa_id': False})

        remessa_obj.write({'valor': valor_final})

        #for h_obj in holerite_ids:
            #if not (h_obj.bank_id and h_obj.banco_conta and h_obj.banco_agencia and h_obj.valor_liquido):
                #continue

            #if h_obj.bank_id.bic != remessa_obj.partner_bank_id.bank_bic:
                #continue

            #func = Funcionario()
            #func.matricula = h_obj.employee_id.id
            #func.nome = h_obj.employee_id.nome.strip()
            #func.conta.numero = h_obj.banco_conta.strip().replace('-', '')
            #func.conta.digito = func.conta.numero[-1]
            #func.conta.numero = func.conta.numero[:-1]

            #func.agencia.numero = h_obj.banco_agencia.strip()
            #if '-' in func.agencia.numero:
                #func.agencia.numero = func.agencia.numero.split('-')[0]

            #func.valor_creditar = D(h_obj.valor_liquido) or D(0)
            #remessa_obj.valor += D(func.valor_creditar)
            #lista_func.append(func)
            #h_obj.write({'remessa_id': remessa_obj.id})

        ##
        ## Gera a remessa
        ##
        #remessa = Remessa()
        #remessa.tipo = 'CNAB_200'
        #remessa.funcionarios = lista_func
        #remessa.data_hora = parse_datetime(remessa_obj.data)
        #remessa.data_debito = parse_datetime(remessa_obj.data_pagamento)
        #remessa.beneficiario = Beneficiario()
        #remessa.beneficiario.banco = BANCO_CODIGO[remessa_obj.partner_bank_id.bank_bic]
        #remessa.beneficiario.nome = remessa_obj.company_id.partner_id.razao_social
        #remessa.beneficiario.agencia.numero = remessa_obj.partner_bank_id.agencia or ''
        #remessa.beneficiario.conta.numero = remessa_obj.partner_bank_id.acc_number or ''
        #remessa.beneficiario.conta.digito = remessa_obj.partner_bank_id.conta_digito or ''

        #dados = {
            #'nome_arquivo': 'folha_' + remessa_obj.company_id.name.replace(' ', '_') + '_' + remessa_obj.data.replace(' ', '_') + '.txt',
            #'arquivo': base64.encodestring(remessa.arquivo_remessa),
            #'arquivo_texto': remessa.arquivo_remessa,
            #'valor': remessa_obj.valor,
        #}
        #return remessa_obj.write(dados)


finan_remessa_folha()
