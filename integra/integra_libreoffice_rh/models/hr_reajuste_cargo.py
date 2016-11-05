# -*- coding: utf-8 -*-


from osv import fields, orm
from integra_rh.constantes_rh import *
from pybrasil.data import agora, formata_data


class hr_reajuste_cargo(orm.Model):
    _name = 'hr.reajuste_cargo'
    _inherit = 'hr.reajuste_cargo'
    _description = 'Modelos Cargos'

    _columns = {
        'lo_modelo_ids': fields.many2many('lo.modelo', 'lo_modelo_hr_cargo', 'hr_cargo_id', 'lo_modelo_id', u'Modelos LibreOffice'),
    }

    def gera_modelos(self, cr, uid, ids, context={}):
        attachment_pool = self.pool.get('ir.attachment')
        contract_pool = self.pool.get('hr.contract')

        for reajust_obj in self.browse(cr, uid, ids):

            if len(reajust_obj.lo_modelo_ids) > 0 and len(reajust_obj.cargos_reajustar_ids) > 0:
                attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.reajuste_cargo'), ('res_id', '=', reajust_obj.id)])
                attachment_pool.unlink(cr, uid, attachment_ids)

                for cargo_obj in reajust_obj.cargos_reajustar_ids:

                    contrato_obj = cargo_obj.contrato_id

                    for modelo_obj in reajust_obj.lo_modelo_ids:
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

                        #
                        # Apaga os recibos anteriores com o mesmo nome
                        #
                        nome_arquivo = modelo_obj.nome_arquivo.split('.')[0]
                        nome_arquivo += '_' + contrato_obj.employee_id.nome.upper().replace(' ', '-')

                        #attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'hr.reajuste_cargo'), ('res_id', '=', reajust_obj.id), ('name', 'like', nome_arquivo)])
                        #attachment_pool.unlink(cr, uid, attachment_ids)

                        nome_arquivo += agora().strftime('_%Y-%m-%d_%H-%M-%S')
                        nome_arquivo += '.'
                        nome_arquivo += modelo_obj.formato or 'doc'

                        novas_variaveis = {
                            'data': formata_data(reajust_obj.data or agora()),
                            'Data': formata_data(reajust_obj.data or agora()),
                            'DATA': formata_data(reajust_obj.data or agora()),
                        }

                        #try:
                        arquivo = modelo_obj.gera_modelo(dados, novas_variaveis=novas_variaveis)

                        dados = {
                            'datas': arquivo,
                            'name': nome_arquivo,
                            'datas_fname': nome_arquivo,
                            'res_model': 'hr.reajuste_cargo',
                            'res_id': reajust_obj.id,
                            'file_type': 'application/msword',
                        }
                        attachment_pool.create(cr, uid, dados)
                        #except:
                            #pass

            return



hr_reajuste_cargo()
