# -*- coding: utf-8 -*-


from osv import fields, orm
from integra_rh.constantes_rh import *
from pybrasil.data import agora, parse_datetime, formata_data


class hr_contract(orm.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'
    #_description = 'Job Description'

    def gera_modelos(self, cr, uid, ids, context={}):
        attachment_pool = self.pool.get('ir.attachment')

        for contrato_obj in self.browse(cr, uid, ids):
            if contrato_obj.job_id and len(contrato_obj.job_id.lo_modelo_ids) > 0:
                for modelo_obj in contrato_obj.job_id.lo_modelo_ids:
                    dados = {
                        'contrato': contrato_obj,
                        'empregado': contrato_obj.employee_id,
                        'empresa': contrato_obj.company_id.partner_id,
                        'cargo': contrato_obj.job_id,
                        'funcao': contrato_obj.job_id,
                        'ESTADO_CIVIL': dict(ESTADO_CIVIL),
                        'UNIDADE_SALARIO': dict(UNIDADE_SALARIO),
                        'RACA_COR': dict(RACA_COR),
                        'filhos': contrato_obj.employee_id.dependente_salario_familia_ids,
                    }

                    data_cadastro_ultimo_filho = ''
                    for filho_obj in contrato_obj.employee_id.dependente_salario_familia_ids:
                        if filho_obj.data_cadastro and filho_obj.data_cadastro > data_cadastro_ultimo_filho:
                            data_cadastro_ultimo_filho = filho_obj.data_cadastro

                    if data_cadastro_ultimo_filho:
                        data_cadastro_ultimo_filho = formata_data(data_cadastro_ultimo_filho)

                    dados['data_cadastro_ultimo_filho'] = data_cadastro_ultimo_filho

                    #
                    # Apaga os recibos anteriores com o mesmo nome
                    #
                    nome_arquivo = modelo_obj.nome_arquivo.split('.')[0]
                    nome_arquivo += '_' + contrato_obj.employee_id.nome.upper().replace(' ', '-')

                    attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.contract'), ('res_id', '=', contrato_obj.id), ('name', 'like', nome_arquivo)])
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
                        'res_model': 'hr.contract',
                        'res_id': contrato_obj.id,
                        'file_type': 'application/msword',
                    }
                    attachment_pool.create(cr, uid, dados)
                    #except:
                        #pass

        return

hr_contract()
