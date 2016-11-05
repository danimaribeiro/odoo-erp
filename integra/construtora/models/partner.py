# -*- coding: utf-8 -*-

from osv import osv, fields
from pybrasil.inscricao import formata_cpf, valida_cpf, limpa_formatacao
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional)
from integra_rh.models.hr_employee import SEXO, ESTADO_CIVIL, ESTADO_CIVIL_SEXO



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

                if len(partner_obj.sociedade_ids):
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
        'fone_comercial': fields.char(u'Fone Comercial', size=18),
        'creci_numero': fields.char(u'CRECI', size=14),
        'creci_data_expedicao': fields.date(u'Data de expedição do CRECI'),
        'cnai_numero': fields.char(u'CNAI', size=14),
        'cnai_data_expedicao': fields.date(u'Data de expedição do CNAI'),

        'conjuge_nome': fields.char(u'Cônjuge Nome', size=60),
        'conjuge_profissao': fields.char(u'Cônjuge Cargo', size=40),
        'conjuge_rg_numero': fields.char(u'Cônjuge RG', size=14),
        'conjuge_rg_orgao_emissor': fields.char(u'Cônjuge Órgão emisssor do RG', size=20),
        'conjuge_rg_data_expedicao': fields.date(u'Cônjuge Data de expedição do RG'),
        'conjuge_data_nascimento': fields.date(u'Cônjuge Data de Nascimento'),
        'conjuge_cpf': fields.char(u'Cônjuge CPF', size=14),
        'conjuge_pais_nacionalidade_id': fields.many2one('sped.pais', u'Cônjuge Nacionalidade'),

        'vendedor': fields.boolean(u'É vendedor'),
        'comprador': fields.boolean(u'É comprador'),
        'comprador_investidor': fields.boolean(u'É comprador/investidor'),
        'comprador_socio': fields.boolean(u'É comprador/sócio'),

        'eh_vendedor': fields.boolean(u'É vendedor'),
        'eh_comprador': fields.boolean(u'É comprador'),
        'eh_comprador_investidor': fields.boolean(u'É comprador/investidor'),
        'eh_comprador_socio': fields.boolean(u'É comprador/sócio'),

        'eh_contato': fields.boolean(u'É contato'),

        'data_nascimento': fields.date(u'Data de nascimento'),

        'qualificacao_contratual': fields.function(_qualificacao_contratual, type='char', string=u'Qualificação contratual'),
        'eh_corretor': fields.boolean(u'É corretor?'),
        'corretor_usuario_id': fields.many2one('res.users', u'Usuário corretor'),
        'tipo_corretor': fields.selection([('I', 'Interno'), ('A', 'Associado'), ('P', 'Parceiro'), ('D', u'Indicação')], u'Tipo do corretor'),
        'cep_id': fields.many2one('res.cep', u'CEP', ondelete='restrict'),

        'crm_lead_ids': fields.one2many('crm.lead', 'partner_id', u'Prospectos'),
    }

    def onchange_cpf(self, cr, uid, ids, cpf, context={}):
        if not cpf:
            return {}

        if not valida_cpf(cpf):
            raise osv.except_osv(u'Erro!', u'CPF inválido!')

        cpf = limpa_formatacao(cpf)
        cpf = formata_cpf(cpf)

        if ids != []:
            cnpj_ids = self.pool.get('hr.employee').search(cr, uid, [('cpf', '=', cpf), '!', ('id', 'in', ids)])
        else:
            cnpj_ids = self.pool.get('hr.employee').search(cr, uid, [('cpf', '=', cpf)])

        if len(cnpj_ids) > 0:
            return {'value': {'cpf': cpf}, 'warning': {'title': u'Aviso!', 'message': u'CPF já existe no cadastro!'}}

        return {'value': {'cpf': cpf}}

    def onchange_fone_celular(self, cr, uid, ids, fone, celular, context={}):
        if fone is not None and fone:
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Telefone fixo inválido!'}}

            fone = formata_fone(fone)
            return {'value': {'fone': fone}}

        elif celular is not None and celular:
            if not valida_fone_internacional(celular) and not valida_fone_celular(celular):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Celular inválido!'}}

            celular = formata_fone(celular)
            return {'value': {'celular': celular}}

    def onchange_cep_id(self, cr, uid, ids, cep_id):
        cep_pool = self.pool.get('res.cep')

        valores = cep_pool.onchange_consulta_cep(cr, uid, False, cep_id)

        return {'value': valores}


res_partner()

class res_partner_address(osv.Model):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'

    _columns = {
        'type': fields.selection( [ ('default','Default'),('invoice','Invoice'), ('delivery','Delivery'), ('contact','Contact'), ('other','Other'),('purchase','Compras') ],'Address Type'),
    }

    def cria_parceiro_contato(self, cr, uid, ids, context={}):
        partner_pool = self.pool.get('res.partner')

        ids = self.search(cr, uid, [('partner_id', '=', False), ('name', '!=', False)])

        for address_obj in self.browse(cr, uid, ids):
            if address_obj.partner_id:
                continue

            if not address_obj.name:
                continue

            cep = ''
            if address_obj.cep:
                cep = limpa_formatacao(address_obj.cep)
                if not cep.isdigit() or len(cep) != 8:
                    cep = ''
                else:
                    cep = cep[:5] + '-' + cep[5:]

            dados = {
                'name': address_obj.name,
                'eh_contato': True,
                'endereco': address_obj.endereco,
                'numero': address_obj.numero,
                'complemento': address_obj.complemento,
                'bairro': address_obj.bairro,
                'municipio_id': address_obj.municipio_id and address_obj.municipio_id.id,
                'cep': cep,
            }

            partner_id = partner_pool.create(cr, uid, dados)

            address_obj.write({'partner_id': partner_id})
            cr.commit()

        return True


res_partner_address()

