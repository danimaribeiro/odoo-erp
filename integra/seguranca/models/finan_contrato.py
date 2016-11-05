# -*- coding: utf-8 -*-

from osv import osv, fields
import os
import base64
from decimal import Decimal as D
from copy import copy
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, data_hora, hoje, formata_data, agora, data_por_extenso
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime, data_hora_horario_brasilia, data_hora, hoje, formata_data, agora, data_por_extenso
from pybrasil.valor import formata_valor
from pybrasil.base import DicionarioBrasil
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)


class finan_contrato(osv.Model):
    _name = 'finan.contrato'
    _inherit = 'finan.contrato'

    _columns = {
        'parent_id': fields.many2one('finan.contrato', u'Contrato pai', select=True, ondelete='restrict'),
        'contratos_filhos': fields.one2many('finan.contrato', 'parent_id', string=u'Contratos filhos'),
        'parent_left': fields.integer(u'Contrato à esquerda', select=1),
        'parent_right': fields.integer(u'Contrato a direita', select=1),
        'lo_modelo_id': fields.many2one('lo.modelo',u'Modelo de Contrato',  domain=[['tabela', '=', 'finan.contrator']]),
        'tipo_faturamento_id': fields.many2one('finan.tipo.faturamento', u'Tipo do faturamento', ondelete='restrict'),
    }

    def monta_dados_contrato(self, cr, uid, ids, context={}):

        for contrato_obj in self.browse(cr, uid, ids, context=context):
            contrato_obj.data_assinatura = formata_data(contrato_obj.data_assinatura) or ''
            contrato_obj.data_extenso = data_por_extenso(contrato_obj.data_assinatura) or ''

            if contrato_obj.data_distrato:
                contrato_obj.data_assinatura_distrato = formata_data(contrato_obj.data_distrato)
                contrato_obj.data_extenso_distrato = data_por_extenso(contrato_obj.data_distrato)
            else:
                contrato_obj.data_extenso_distrato = ''
                contrato_obj.data_assinatura_distrato = ''

            contrato_obj.data_extenso_hoje = data_por_extenso(hoje())
            contrato_obj.numero = contrato_obj.numero or ''

            #
            # Dados do cliente
            #
            partner = contrato_obj.partner_id
            endereco = partner.endereco or u''
            endereco += u', '
            endereco += partner.numero or u''

            if partner.complemento:
                endereco += u' – '
                endereco += partner.complemento

            endereco += u' — '
            endereco += partner.bairro or ''

            endereco += u' — '
            endereco += partner.cidade or ''
            endereco += u' – '
            endereco += partner.estado or ''

            endereco += u' — '
            endereco += partner.cep or ''

            contrato_obj.partner_id.endereco_completo = endereco

            if not contrato_obj.partner_id.razao_social:
                contrato_obj.partner_id.razao_social = contrato_obj.partner_id.name

            contrato_obj.partner_id.razao_social = contrato_obj.partner_id.razao_social or contrato_obj.partner_id.name or ''
            contrato_obj.partner_id.endereco = contrato_obj.partner_id.endereco or ''
            contrato_obj.partner_id.numero = contrato_obj.partner_id.numero or ''
            contrato_obj.partner_id.complemento = contrato_obj.partner_id.complemento or ''
            contrato_obj.partner_id.bairro = contrato_obj.partner_id.bairro or ''
            contrato_obj.partner_id.cidade = contrato_obj.partner_id.cidade or ''
            contrato_obj.partner_id.estado = contrato_obj.partner_id.estado or ''
            contrato_obj.partner_id.cep = contrato_obj.partner_id.cep or ''
            contrato_obj.partner_id.fone = contrato_obj.partner_id.fone or ''
            contrato_obj.partner_id.celular = contrato_obj.partner_id.celular or ''
            contrato_obj.partner_id.email = contrato_obj.partner_id.email or ''
            contrato_obj.partner_id.cnpj_cpf = contrato_obj.partner_id.cnpj_cpf or ''
            contrato_obj.partner_id.ie = contrato_obj.partner_id.ie or ''

            #
            # Dados da empresa
            #
            partner = contrato_obj.company_id.partner_id
            endereco = partner.endereco or u''
            endereco += u', '
            endereco += partner.numero or u''

            if partner.complemento:
                endereco += u' - '
                endereco += partner.complemento

            endereco += u' - '
            endereco += partner.bairro or ''

            endereco += u' - '
            endereco += partner.cidade or ''
            endereco += u'-'
            endereco += partner.estado or ''

            endereco += u' - '
            endereco += partner.cep or ''

            contrato_obj.company_id.partner_id.endereco_completo = endereco
            contrato_obj.company_id.partner_id.razao_social = contrato_obj.company_id.partner_id.razao_social or contrato_obj.company_id.partner_id.name or ''
            contrato_obj.company_id.partner_id.endereco = contrato_obj.company_id.partner_id.endereco or ''
            contrato_obj.company_id.partner_id.numero = contrato_obj.company_id.partner_id.numero or ''
            contrato_obj.company_id.partner_id.complemento = contrato_obj.company_id.partner_id.complemento or ''
            contrato_obj.company_id.partner_id.bairro = contrato_obj.company_id.partner_id.bairro or ''
            contrato_obj.company_id.partner_id.cidade = contrato_obj.company_id.partner_id.cidade or ''
            contrato_obj.company_id.partner_id.estado = contrato_obj.company_id.partner_id.estado or ''
            contrato_obj.company_id.partner_id.cep = contrato_obj.company_id.partner_id.cep or ''
            contrato_obj.company_id.partner_id.fone = contrato_obj.company_id.partner_id.fone or ''
            contrato_obj.company_id.partner_id.celular = contrato_obj.company_id.partner_id.celular or ''
            contrato_obj.company_id.partner_id.email = contrato_obj.company_id.partner_id.email or ''
            contrato_obj.company_id.partner_id.cnpj_cpf = contrato_obj.company_id.partner_id.cnpj_cpf or ''
            contrato_obj.company_id.partner_id.ie = contrato_obj.company_id.partner_id.ie or ''

            for i in range(len(contrato_obj.contrato_produto_ids)):
                contrato_obj.contrato_produto_ids[i].descricao = contrato_obj.contrato_produto_ids[i].product_id.name
                contrato_obj.contrato_produto_ids[i].unidade = contrato_obj.contrato_produto_ids[i].product_id.uom_id.name or ''
                contrato_obj.contrato_produto_ids[i].quantidade = formata_valor(contrato_obj.contrato_produto_ids[i].quantidade or 0)
                contrato_obj.contrato_produto_ids[i].vr_unitario = formata_valor(contrato_obj.contrato_produto_ids[i].vr_unitario or 0)
                contrato_obj.contrato_produto_ids[i].vr_total = formata_valor(contrato_obj.contrato_produto_ids[i].vr_total or 0)

            dados = {
                'contrato': contrato_obj,
                'cliente': contrato_obj.partner_id,
                'empresa': contrato_obj.company_id.partner_id,
                'produtos': contrato_obj.contrato_produto_ids,
            }

        return dados

    def gera_modelos(self, cr, uid, ids, context={}):
        attachment_pool = self.pool.get('ir.attachment')

        for contrato_obj in self.browse(cr, uid, ids):
            dados = self.monta_dados_contrato(cr, uid, ids, context=context)
            nome = u'' + contrato_obj.lo_modelo_id.nome.replace(' ', '_') + '.'
            formato = contrato_obj.lo_modelo_id.formato or 'pdf'
            nome += formato
            pdf = contrato_obj.lo_modelo_id.gera_modelo_novo(dados, formato=formato)

            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.contrato'), ('res_id', '=', contrato_obj.id), ('name', 'like', nome)])
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': pdf,
                'name': nome,
                'datas_fname': nome,
                'res_model': 'finan.contrato',
                'res_id': contrato_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

        return


finan_contrato()
