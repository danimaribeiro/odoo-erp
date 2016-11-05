# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)


AJUSTA_VINDO_DO_PARTICIPANTE = False


class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Partner'

    def get_participante_campo(self, cr, uid, ids, campo):
        if not len(ids):
            return {}

        res = {}
        for partner_obj in self.browse(cr, uid, ids):
            valor_campo = False

            if partner_obj.participante_id:
                participante_obj = partner_obj.participante_id[0]

                if campo == 'cnpj_cpf':
                    if participante_obj.cnpj_cpf:
                        if len(participante_obj.cnpj_cpf) == 14:
                            valor_campo = formata_cnpj(participante_obj.cnpj_cpf)
                        else:
                            valor_campo = formata_cpf(participante_obj.cnpj_cpf)

                elif campo == 'fone':
                    if participante_obj.fone:
                        valor_campo = formata_fone(participante_obj.fone)

                elif campo == 'ie':
                    if participante_obj.ie and participante_obj.municipio_id:
                        valor_campo = formata_inscricao_estadual(participante_obj.ie, participante_obj.municipio_id.estado_id.uf)
                    elif participante_obj.ie:
                        valor_campo = participante_obj.ie

                elif campo == 'suframa':
                    if participante_obj.suframa:
                        valor_campo = formata_inscricao_estadual(participante_obj.suframa, 'SUFRAMA')

                elif campo == 'municipio_id':
                    if participante_obj.municipio_id:
                        valor_campo = participante_obj.municipio_id.id
                    else:
                        valor_campo = None

                elif campo == 'cnae_id':
                    if participante_obj.cnae_id:
                        valor_campo = participante_obj.cnae_id.id
                    else:
                        valor_campo = None

                elif campo == 'nome':
                    valor_campo = participante_obj.nome

                elif campo == 'fantasia':
                    valor_campo = participante_obj.fantasia

                elif campo == 'endereco':
                    valor_campo = participante_obj.endereco

                elif campo == 'numero':
                    valor_campo = participante_obj.numero

                elif campo == 'complemento':
                    valor_campo = participante_obj.complemento

                elif campo == 'bairro':
                    valor_campo = participante_obj.bairro

                elif campo == 'cep':
                    if participante_obj.cep:
                        if len(participante_obj.cep) == 8:
                            valor_campo = participante_obj.cep[:5] + '-' + participante_obj.cep[5:]
                        else:
                            valor_campo = participante_obj.cep
                    else:
                        valor_campo = participante_obj.cep

                elif campo == 'email_nfe':
                    valor_campo = participante_obj.email_nfe

                elif campo == 'im':
                    valor_campo = participante_obj.im

                elif campo == 'rntrc':
                    valor_campo = participante_obj.rntrc

                elif campo == 'crc':
                    valor_campo = participante_obj.crc

            res[partner_obj.id] = valor_campo

        return res

    def _get_cnpj_cpf_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'cnpj_cpf')

    def _procura_cnpj_cpf(self, cursor, user_id, obj, cnpj_cpf_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('participante_id.cnpj_cpf', 'like', limpa_formatacao(texto)),
        ]

        return procura

    def _get_razao_social_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'nome')

    def _get_fantasia_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'fantasia')

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
        return self.get_participante_campo(cr, uid, ids, 'email_nfe')

    def _get_ie_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'ie')

    def _get_im_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'im')

    def _get_suframa_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'suframa')

    def _get_rntrc_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'rntrc')

    def _get_crc_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'crc')

    def _get_cnae_id_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        return self.get_participante_campo(cr, uid, ids, 'cnae_id')

    _columns = {
        'participante_id': fields.one2many('sped.participante', 'partner_id', u'SPED'),
        'cnpj_cpf': fields.function(_get_cnpj_cpf_funcao, type='char', string=u'CNPJ/CPF', fnct_search=_procura_cnpj_cpf, store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'razao_social': fields.function(_get_razao_social_funcao, type='char', string=u'Razão Social', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'fantasia': fields.function(_get_fantasia_funcao, type='char', string=u'Fantasia', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'endereco': fields.function(_get_endereco_funcao, type='char', string=u'Endereço', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'numero': fields.function(_get_numero_funcao, type='char', string=u'Número', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'complemento': fields.function(_get_complemento_funcao, type='char', string=u'Complemento', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'bairro': fields.function(_get_bairro_funcao, type='char', string=u'Bairro', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'municipio_id': fields.function(_get_municipio_id_funcao, type='many2one', string=u'Município', store=AJUSTA_VINDO_DO_PARTICIPANTE, relation='sped.municipio'),
        'cep': fields.function(_get_cep_funcao, type='char', string=u'CEP', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'fone': fields.function(_get_fone_funcao, type='char', string=u'Fone', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'email_nfe': fields.function(_get_email_nfe_funcao, type='char', string=u'Email para envio da NF-e', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'ie': fields.function(_get_ie_funcao, type='char', string=u'Inscrição estadual', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'im': fields.function(_get_im_funcao, type='char', string=u'Inscrição municipal', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'suframa': fields.function(_get_suframa_funcao, type='char', string=u'SUFRAMA', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'rntrc': fields.function(_get_rntrc_funcao, type='char', string=u'RNTRC', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'crc': fields.function(_get_crc_funcao, type='char', string=u'Conselho Regional de Contabilidade', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        'cnae_id': fields.function(_get_cnae_id_funcao, type='many2one', string=u'CNAE principal', store=AJUSTA_VINDO_DO_PARTICIPANTE, relation='sped.cnae'),
    }


res_partner()
