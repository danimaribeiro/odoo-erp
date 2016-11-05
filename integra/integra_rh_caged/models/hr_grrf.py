# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from pybrasil.data import parse_datetime, hoje
import base64
from grrf import GRRF, Empregado
from integra_rh_caged.models import grrf
from pybrasil.valor.decimal import Decimal as D


class hr_payslip(orm.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'
    #_order = 'ano desc, mes desc, data desc, company_id'

    _columns = {
        'nome_arquivo': fields.char(u'Nome arquivo', size=30),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),
        'responsavel_id': fields.many2one('res.company', u'Empresa responsável', select=True, ondelete='restrict'),
    }

    _defaults = {
        #'data': fields.date.today,
        #'declaracao' : '1',
        #'ano': lambda *args, **kwargs: mes_passado()[0],
        #'mes': lambda *args, **kwargs: str(mes_passado()[1]),
    }

    def gera_grrf(self, cr, uid, ids, context={}):

        if not ids:
            return True

        holerite_item_pool = self.pool.get('hr.payslip.line')
        employee_pool = self.pool.get('hr.employee')
        contato_ids = employee_pool.search(cr, uid, [('user_id', '=', uid)])
        contato_obj = None
        if contato_ids:
            contato_obj = employee_pool.browse(cr, uid, contato_ids[0])

        for holerite_obj in self.browse(cr, uid, ids):
            employee_obj = holerite_obj.employee_id
            contract_obj = holerite_obj.contract_id
            empresa_obj =  contract_obj.company_id

            if holerite_obj.responsavel_id:
                company_obj = holerite_obj.responsavel_id
            else:
                company_obj = empresa_obj

            grrf = GRRF()

            grrf.cnpj = company_obj.partner_id.cnpj_cpf
            grrf.razao_social = company_obj.partner_id.razao_social

            if contato_obj:
                grrf.contato = contato_obj.nome
                grrf.email = contato_obj.user_id.user_email or ''

            grrf.endereco = company_obj.partner_id.endereco + ' ' + company_obj.partner_id.numero
            grrf.bairro = company_obj.partner_id.bairro or ''
            grrf.cidade = company_obj.partner_id.municipio_id.nome
            grrf.estado = company_obj.partner_id.municipio_id.estado_id.uf
            grrf.cep = company_obj.partner_id.cep or ''
            grrf.telefone = company_obj.partner_id.fone or ''
            grrf.data_recolhimento_grrf =  parse_datetime(holerite_obj.data_pagamento).date() or ''

            grrf.cnae =  company_obj.partner_id.cnae_id.codigo

            if company_obj.regime_tributario == 1:
                grrf.simples = '2'
            else:
                grrf.simples = '1'

            grrf.codigo_fpas = '515'

            #
            # Empresa contratante
            #
            grrf.empresa.cnpj = empresa_obj.partner_id.cnpj_cpf
            grrf.empresa.razao_social = empresa_obj.partner_id.razao_social
            grrf.empresa.endereco = empresa_obj.partner_id.endereco + ' ' + empresa_obj.partner_id.numero
            grrf.empresa.bairro = empresa_obj.partner_id.bairro or ''
            grrf.empresa.cidade = empresa_obj.partner_id.municipio_id.nome
            grrf.empresa.estado = empresa_obj.partner_id.municipio_id.estado_id.uf
            grrf.empresa.cep = empresa_obj.partner_id.cep or ''
            grrf.empresa.telefone = empresa_obj.partner_id.fone or ''
            grrf.empresa.cnae =  empresa_obj.partner_id.cnae_id.codigo

            if empresa_obj.regime_tributario == 1:
                grrf.empresa.simples = '2'
            else:
                grrf.empresa.simples = '1'

            grrf.empresa.codigo_fpas = '515'

            #
            # Empregado
            #
            empregado = Empregado()

            empregado.grrf = grrf
            empregado.nis = employee_obj.nis
            empregado.data_admissao = parse_datetime(contract_obj.date_start).date()

            if contract_obj.categoria_trabalhador in ['101','102']:
                empregado.categoria_trabalhador = '01'

            #
            # Menor aprendiz
            #
            elif contract_obj.categoria_trabalhador == '103':
                empregado.categoria_trabalhador = '07'

            elif contract_obj.categoria_trabalhador in ['701','702','703']:
                empregado.categoria_trabalhador = '02'

            empregado.nome = employee_obj.nome
            empregado.carteira_trabalho_numero = employee_obj.carteira_trabalho_numero
            empregado.carteira_trabalho_serie = employee_obj.carteira_trabalho_serie
            empregado.sexo = employee_obj.sexo
            empregado.grau_instrucao = employee_obj.grau_instrucao
            empregado.data_nascimento =  parse_datetime(employee_obj.data_nascimento).date()
            empregado.horas_trabalhadas_semana = int(contract_obj.horas_mensalista / 30.0 * 6)
            empregado.cbo = contract_obj.job_id.cbo_id.codigo or ''
            empregado.data_opcao_fgts = parse_datetime(contract_obj.data_opcao_fgts).date()
            empregado.codigo_movimentacao = holerite_obj.codigo_afastamento or ''
            empregado.data_movimentacao = parse_datetime(holerite_obj.data_afastamento).date()
            empregado.codigo_saque = holerite_obj.codigo_saque or '01'

            if holerite_obj.afastamento_imediato:
                empregado.aviso_previo = '3'

            elif holerite_obj.aviso_previo_indenizado:
                empregado.aviso_previo = '2'
                empregado.data_inicio_aviso = None
                empregado.valor_aviso_previo = D(0)

                #ferias_ap = holerite_obj.rubrica_outro_periodo(rubrica='FERIAS_PROPORCIONAL_AP', meses=0, tipo='R', mes_todo=True)
                #ferias_1_3_ap = holerite_obj.rubrica_outro_periodo(rubrica='FERIAS_PROPORCIONAL_1_3_AP', meses=0, tipo='R', mes_todo=True)
                sal_13_ap = holerite_obj.rubrica_outro_periodo(rubrica='SAL_13_AP', meses=0, tipo='R', mes_todo=True)
                ap = holerite_obj.rubrica_outro_periodo(rubrica='AVISO_INDENIZADO', meses=0, tipo='R', mes_todo=True)
                grat_40_ap = holerite_obj.rubrica_outro_periodo(rubrica='GRAT_FUNC_40_AP', meses=0, tipo='R', mes_todo=True)

                #if ferias_ap:
                    #empregado.valor_aviso_previo += D(ferias_ap.total)
                #if ferias_1_3_ap:
                    #empregado.valor_aviso_previo += D(ferias_1_3_ap.total)
                if sal_13_ap:
                    empregado.valor_aviso_previo += D(sal_13_ap.total)
                if ap:
                    empregado.valor_aviso_previo += D(ap.total)
                if grat_40_ap:
                    empregado.valor_aviso_previo += D(grat_40_ap.total)

                print(empregado.valor_aviso_previo)
            else: # Trabalhado
                empregado.aviso_previo = '1'
                empregado.data_inicio_aviso = parse_datetime(holerite_obj.data_aviso_previo).date()

            #empregado.reposicao = ''
            #empregado.data_homolagacao_disidio = ''
            #empregado.valor_disidio = ''
            #empregado.remuneracao_mes_anterior = '0'

            #
            # A remuneração no mês da rescisão é a base do FGTS
            #
            base_fgts_ids = holerite_item_pool.search(cr, uid, [('slip_id', '=', holerite_obj.id), ('code', '=', 'BASE_FGTS')])
            if base_fgts_ids:
                base_fgts_obj = holerite_item_pool.browse(cr, uid, base_fgts_ids[0])
                empregado.remuneracao_mes_rescisao = D(base_fgts_obj.total).quantize(D('0.01'))
                empregado.remuneracao_mes_rescisao -= empregado.valor_aviso_previo

            #empregado.remuneracao_mes_rescisao = '0'
            #empregado.remuneracao_mes_anterior = '0'
            #empregado.indic_pensao_alimenticia = 'N'
            #empregado.percentual_pensao = '0'
            #empregado.valor_pensao_alim = '0'
            empregado.cpf = employee_obj.cpf

            if employee_obj.bank_id:
                empregado.banco_trabalhador = employee_obj.bank_id.bic
                empregado.agencia_trabalhador = employee_obj.banco_agencia if employee_obj.banco_agencia else ''
                empregado.conta_corrente = employee_obj.banco_conta if employee_obj.banco_conta else ''

            empregado.saldo_rescisao = holerite_obj.saldo_fgts or 0

            arquivo_texto = grrf.registro()
            arquivo_texto += grrf.registro_10()
            arquivo_texto += empregado.registro_40()
            arquivo_texto += grrf.registro_90()

            dados = {
                'nome_arquivo': 'grrf.re',
                'arquivo_texto': arquivo_texto[:-2],
                'arquivo': base64.encodestring(arquivo_texto[:-2]),
            }
            holerite_obj.write(dados)
        return True
