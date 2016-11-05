# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields




class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _qualificacao_contratual(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for partner_obj in self.browse(cr, uid, ids):
            qualificacao = u''

            if partner_obj.tipo_pessoa == 'J':
                qualificacao += u'pessoa jurídica de direito privado, estabelecida a '

                qualificacao += partner_obj.endereco or u''
                qualificacao += u', nº '
                qualificacao += partner_obj.numero or u''

                if partner_obj.complemento:
                    qualificacao += u', '
                    qualificacao += partner_obj.complemento or u''

                if partner_obj.bairro:
                    qualificacao += u', '
                    qualificacao += partner_obj.bairro or u''

                qualificacao += u', '
                qualificacao += partner_obj.cidade or u''
                qualificacao += u'-'
                qualificacao += partner_obj.estado or u''
                qualificacao += u', CEP '
                qualificacao += partner_obj.cep or u''

                qualificacao += u', inscrita no CNPJ sob o nº '
                qualificacao += partner_obj.cnpj_cpf or u''

                if hasattr(partner_obj, 'sociedade_ids') and len(partner_obj.sociedade_ids):
                    qualificacao += u', neste ato representada por '

                    socio_obj = partner_obj.sociedade_ids[0]

                    if socio_obj.tipo_pessoa == 'F':
                        if socio_obj.sexo == 'M':
                            qualificacao += u'seu sócio, o Sr. '
                        else:
                            qualificacao += u'sua sócia, a Sra. '

                    else:
                        qualificacao += u'seu sócio '

                    qualificacao += socio_obj.razao_social or u''

            else:
                if partner_obj.pais_nacionalidade_id:
                    qualificacao += u'natural do '
                    qualificacao += partner_obj.pais_nacionalidade_id.nome
                    qualificacao += u', '

                if partner_obj.estado_civil:
                    if not partner_obj.sexo:
                        partner_obj.sexo = 'M'

                    qualificacao += ESTADO_CIVIL_SEXO[partner_obj.estado_civil][partner_obj.sexo]
                    qualificacao += u', '

                if partner_obj.sexo == 'M':
                    qualificacao += u'residente e domiciliado a '
                else:
                    qualificacao += u'residente e domiciliada a '

                qualificacao += partner_obj.endereco or u''
                qualificacao += u', nº '
                qualificacao += partner_obj.numero or u''

                if partner_obj.complemento:
                    qualificacao += u', '
                    qualificacao += partner_obj.complemento or u''

                if partner_obj.bairro:
                    qualificacao += u', '
                    qualificacao += partner_obj.bairro or u''

                qualificacao += u', '
                qualificacao += partner_obj.cidade or u''
                qualificacao += '-'
                qualificacao += partner_obj.estado or u''
                qualificacao += u', CEP '
                qualificacao += partner_obj.cep or u''

                if partner_obj.sexo == 'M':
                    qualificacao += u', portador do RG nº '
                    qualificacao += partner_obj.rg_numero or u''
                    qualificacao += u' e inscrito no CPF sob o nº '
                    qualificacao += partner_obj.cnpj_cpf or u''
                else:
                    qualificacao += u', portadora do RG nº '
                    qualificacao += partner_obj.rg_numero or u''
                    qualificacao += u' e inscrita no CPF sob o nº '
                    qualificacao += partner_obj.cnpj_cpf or u''

            res[partner_obj.id] = qualificacao

        return res

    _columns = {
        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='restrict'),
        'grupo_economico_id': fields.many2one('finan.grupo.economico', u'Grupo econômico', ondelete='restrict'),
        'partner_category_id': fields.many2one('res.partner.category', u'Categoria', ondelete='restrict'),
        'qualificacao_contratual': fields.function(_qualificacao_contratual, type='char', string=u'Qualificação contratual'),
    }


res_partner()
