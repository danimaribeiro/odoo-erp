# -*- coding: utf-8 -*-


from osv import fields, orm , osv
from integra_rh.constantes_rh import *
from compiler.ast import Raise
from pybrasil.data import agora, formata_data, dia_util_pagamento, parse_datetime, idade_anos
from dateutil.relativedelta import relativedelta

class hr_payslip(orm.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'


    def gera_modelos(self, cr, uid, ids, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        tabela_aviso_pool = self.pool.get('hr.aviso_previo_proporcional_item')

        for slip_obj in self.browse(cr, uid, ids):
            if slip_obj.struct_id and len(slip_obj.struct_id.lo_modelo_ids) > 0:
                for modelo_obj in slip_obj.struct_id.lo_modelo_ids:
                    if slip_obj.tipo == 'R':
                        if slip_obj.aviso_previo_indenizado and modelo_obj.aviso_previo == 'T':
                            continue
                        elif (not slip_obj.aviso_previo_indenizado) and modelo_obj.aviso_previo == 'I':
                            continue

                    dados = {
                        'holerite': slip_obj,
                        'paysplip': slip_obj,
                        'contrato': slip_obj.contract_id,
                        'empregado': slip_obj.contract_id.employee_id,
                        'empresa': slip_obj.company_id.partner_id,
                        'cargo': slip_obj.contract_id.job_id,
                        'funcao': slip_obj.contract_id.job_id,
                        'ESTADO_CIVIL': slip_obj.contract_id.employee_id.estado_civil,
                        'UNIDADE_SALARIO': slip_obj.contract_id.wage,
                        'RACA_COR': slip_obj.contract_id.employee_id.raca_cor,
                        'filhos': slip_obj.contract_id.employee_id.dependente_salario_familia_ids,
                    }

                    if slip_obj.tipo == 'R':
                        if slip_obj.data_aviso_previo:
                            
                            dados['data_aviso_previo'] = formata_data(slip_obj.data_aviso_previo)
                            data_aviso = parse_datetime(slip_obj.data_aviso_previo)
                            dados['data_inicio_aviso_previo'] = formata_data(data_aviso + relativedelta(days=+1))
                            data = dia_util_pagamento(data_aviso, slip_obj.company_id.partner_id.estado or '', slip_obj.company_id.partner_id.cidade or '', antecipa=True)
                            dados['data_util_aviso_previo'] = formata_data(data)

                            data_inicial_contrato = parse_datetime(slip_obj.contract_id.date_start)                                
                            anos_trabalhados = idade_anos(slip_obj.contract_id.date_start, data_aviso)
                            
                            tabela_aviso_id = tabela_aviso_pool.search(cr, uid, [('anos', '=', int(anos_trabalhados))], context={})
                            tabela_aviso_obj = tabela_aviso_pool.browse(cr, uid, tabela_aviso_id)[0]
                            dados['dias_aviso'] = str(tabela_aviso_obj.dias)
                            print(dados['dias_aviso'])

                        else:
                            dados['data_aviso_previo'] = ''
                            dados['data_util_aviso_previo'] = ''
                            dados['data_inicio_aviso_previo'] = ''

                        if slip_obj.data_afastamento:
                            dados['data_afastamento_real'] = formata_data(slip_obj.data_afastamento)
                            data = parse_datetime(slip_obj.data_afastamento)
                            data = dia_util_pagamento(data, slip_obj.company_id.partner_id.estado or '', slip_obj.company_id.partner_id.cidade or '', antecipa=True)
                            dados['data_util_afastamento_real'] = formata_data(data)

                        else:
                            dados['data_afastamento_real'] = ''
                            dados['data_util_afastamento_real'] = ''

                        if slip_obj.date_to:
                            dados['data_afastamento_projetado'] = formata_data(slip_obj.date_to)
                            data = parse_datetime(slip_obj.date_to)
                            data = dia_util_pagamento(data, slip_obj.company_id.partner_id.estado or '', slip_obj.company_id.partner_id.cidade or '', antecipa=True)
                            dados['data_util_afastamento_projetado'] = formata_data(data)

                        else:
                            dados['data_afastamento_projetado'] = ''
                            dados['data_util_afastamento_projetado'] = ''
                            
                            
                    if slip_obj.tipo == 'F':
                        if slip_obj.data_fim_periodo_aquisitivo:
                            dados['data_fim_periodo_aquisitivo'] = formata_data(slip_obj.data_fim_periodo_aquisitivo)
                            data_solicitacao_abono = parse_datetime(slip_obj.data_fim_periodo_aquisitivo).date() +  relativedelta(days=-15)
                            dados['data_solicitacao_abono'] = formata_data(data_solicitacao_abono)

                    #
                    # Apaga os recibos anteriores com o mesmo nome
                    #
                    nome_arquivo = modelo_obj.nome_arquivo.split('.')[0]
                    nome_arquivo += '_' + slip_obj.contract_id.employee_id.nome.upper().replace(' ', '-')

                    attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.payslip'), ('res_id', '=', slip_obj.id), ('name', 'like', nome_arquivo)])
                    attachment_pool.unlink(cr, uid, attachment_ids)

                    nome_arquivo += agora().strftime('_%Y-%m-%d_%H-%M-%S')
                    nome_arquivo += '.'
                    nome_arquivo += modelo_obj.formato or 'doc'

                    #try:
                    arquivo = modelo_obj.gera_modelo(dados)

                    dados = {
                        'datas': arquivo,
                        'name': nome_arquivo,
                        'datas_fname': nome_arquivo,
                        'res_model': 'hr.payslip',
                        'res_id': slip_obj.id,
                        'file_type': 'application/msword',
                    }
                    attachment_pool.create(cr, uid, dados)
                    #except:
                        #pass
            else:
                raise osv.except_osv(u'Inválido !', u'Não existe modelo vinculado a estrutura de Salário')

        return

hr_payslip()
