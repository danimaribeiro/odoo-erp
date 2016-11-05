# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from pybrasil.inscricao import formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual
from pybrasil.telefone import formata_fone


class Participante(orm.Model):
    #_inherit = 'res.partner'
    _description = u'Participantes'
    _name = 'sped.participante'

    _columns = {
        #
        # Chave primária natural
        #
        'partner_id': fields.many2one('res.partner'),
        'cnpj_cpf': fields.char(u'CNPJ/CPF', size=14,
                                help=u'Para participantes estrangeiros, usar EX9999, onde 9999 é um número a sua escolha'),

        #
        # Necessários para algumas validações de uso de cálculos e CFOP's
        #
        'eh_cliente': fields.boolean(u'É cliente?'),
        'eh_fornecedor': fields.boolean(u'É fornecedor?'),
        'eh_transportadora': fields.boolean(u'É transportadora?'),
        'eh_produtor_rural': fields.boolean(u'É produtor rural?'),
        'eh_funcionario': fields.boolean(u'É funcionário?'),
        'eh_consumidor_final': fields.boolean(u'É consumidor final?'),
        'eh_orgao_publico': fields.boolean(u'É órgão público?'),
        'eh_contabilista': fields.boolean(u'É contabilista?'),
        'eh_motorista': fields.boolean(u'É motorista?'),

        #
        # Campos obrigatórios na emissão da NF-e e no SPED
        #
        'nome': fields.char(u'Razão Social', size=60),
        'fantasia': fields.char(u'Fantasia', size=60),
        'endereco': fields.char(u'Endereço', size=60),
        'numero': fields.char(u'Número', size=60),
        'complemento': fields.char(u'Complemento', size=60),
        'bairro': fields.char(u'Bairro', size=60),
        'municipio_id': fields.many2one('sped.municipio', u'Município'),
        'cep': fields.char('CEP', size=8),

        #
        # Telefone e emeio para a emissão da NF-e
        #
        'fone': fields.char(u'Fone', size=14),
        'email_nfe': fields.char(u'Email para envio da NF-e', size=60),

        #
        # Inscrições e registros
        #
        'ie': fields.char(u'Inscrição estadual', size=14),
        'im': fields.char(u'Inscrição municipal', size=14),
        'suframa': fields.char(u'SUFRAMA', size=9),
        'rntrc': fields.char(u'RNTRC', size=15),
        'crc': fields.char(u'Conselho Regional de Contabilidade', size=14),
        'cnae_id': fields.many2one('sped.cnae', u'CNAE principal'),
    }

    #_sql_constraints = [
        #('cnpj_cpf_unique', 'unique (cnpj_cpf)',
        #u'O CNPJ/CPF não pode se repetir!'),
        #('partner_id_unique', 'unique (partner_id)',
        #u'Só é permitido vincular a um res_partner!'),
        #]

    _defaults = {
        'eh_cliente': True,
        'eh_fornecedor': False,
        'eh_transportadora': False,
        'eh_produtor_rural': False,
        'eh_funcionario': False,
        'eh_consumidor_final': False,
        'eh_orgao_publico': False,
        'eh_contabilista': False,
        'eh_motorista': False,
        'complemento': '',
        'fone': '',
        'email_nfe': '',
        'ie': 'ISENTO',
        'im': '',
        'suframa': '',
        'rntrc': '',
        'crc': '',
        }

    _rec_name = 'nome'
    _order = 'nome'

Participante()
