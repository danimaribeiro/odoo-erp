# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)


AJUSTA_VINDO_DO_PARTICIPANTE = True


class hr_employee(osv.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'
    _description = 'Employee'

    def get_participante_campo(self, cr, uid, ids, campo):
        if not len(ids):
            return {}

        res = {}
        for employee_obj in self.browse(cr, uid, ids):
            valor_campo = False

            if employee_obj.address_home_id:
                address_obj = employee_obj.address_home_id

                if campo == 'fone':
                    if address_obj.phone:
                        valor_campo = formata_fone(address_obj.phone)        
                
                elif campo == 'celular':
                    if address_obj.mobile:
                        valor_campo = formata_fone(address_obj.mobile)
                                 
                elif campo == 'municipio_id':
                    if address_obj.municipio_id:
                        valor_campo = address_obj.municipio_id.id
                    else:
                        valor_campo = None           

                elif campo == 'endereco':
                    valor_campo = address_obj.endereco

                elif campo == 'numero':
                    valor_campo = address_obj.numero

                elif campo == 'complemento':
                    valor_campo = address_obj.complemento

                elif campo == 'bairro':
                    valor_campo = address_obj.bairro

                elif campo == 'cep':
                    if address_obj.cep:
                        if len(address_obj.cep) == 8:
                            valor_campo = address_obj.cep[:5] + '-' + address_obj.cep[5:]
                        else:
                            valor_campo = address_obj.cep
                    else:
                        valor_campo = address_obj.cep

                elif campo == 'email':
                    valor_campo = address_obj.email
                
                    
            res[employee_obj.id] = valor_campo

        return res

    
    def _get_endereco_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'endereco')

    def _get_numero_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'numero')

    def _get_complemento_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'complemento')

    def _get_bairro_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'bairro')

    def _get_municipio_id_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'municipio_id')

    def _get_cep_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'cep')

    def _get_fone_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'fone')

    def _get_email_nfe_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'email')

    def _get_clular_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'celular')


    _columns = {
        
        'endereco': fields.function(_get_endereco_funcao, type='char', string=u'Endereço', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'numero': fields.function(_get_numero_funcao, type='char', string=u'Número', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'complemento': fields.function(_get_complemento_funcao, type='char', string=u'Complemento', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'bairro': fields.function(_get_bairro_funcao, type='char', string=u'Bairro', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'municipio_id': fields.function(_get_municipio_id_funcao, type='many2one', string=u'Município', store=AJUSTA_VINDO_DO_PARTICIPANTE, relation='sped.municipio'),
        'cep': fields.function(_get_cep_funcao, type='char', string=u'CEP', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'fone': fields.function(_get_fone_funcao, type='char', string=u'Fone', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'email': fields.function(_get_email_nfe_funcao, type='char', string=u'Email', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'celular': fields.function(_get_fone_funcao, type='char', string=u'Celular', store=AJUSTA_VINDO_DO_PARTICIPANTE),

    }


hr_employee()
