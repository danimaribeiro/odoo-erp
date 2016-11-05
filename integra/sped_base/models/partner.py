# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)
from pybrasil.base import mascara
from integra_rh.models.hr_employee import SEXO, ESTADO_CIVIL


AJUSTA_VINDO_DO_PARTICIPANTE = False

IE_DESTINATARIO = (
    ('1', 'CONTRIBUINTE'),
    ('2', 'ISENTO'),
    ('9', 'ESTRANGEIRO'),
)


TIPO_PESSOA = (
    ('F', u'Física'),
    ('J', u'Jurídica'),
    ('E', u'Estrangeiro'),
    ('I', u'Indeterminado'),
)


class res_partner(osv.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

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

    def _get_descricao(self, cr, uid, ids, prop, unknow_none, context={}):
        if not len(ids):
            return {}

        res = {}
        for partner_obj in self.browse(cr, uid, ids):
            nome = partner_obj.name

            #if partner_obj.participante_id:
                #participante_obj = partner_obj.participante_id[0]
            if partner_obj.cnpj_cpf:
                nome += ' - ' + partner_obj.cnpj_cpf

            res[partner_obj.id] = nome

        return res

    def _get_tipo_pessoa(self, cr, uid, ids, nome_campo, arg=None, context={}):
        res = {}

        for partner_obj in self.browse(cr, uid, ids):
            res[partner_obj.id] = 'I'

            if partner_obj.cnpj_cpf:
                if partner_obj.cnpj_cpf[:2] == 'EX':
                    res[partner_obj.id] = 'E'
                elif len(partner_obj.cnpj_cpf) == 18:
                    res[partner_obj.id] = 'J'
                else:
                    res[partner_obj.id] = 'F'

        return res

    _columns = {
        #'shop_id': fields.many2one('sale.shop', 'Shop'),
        #'address_municipio_id': fields.related('address', 'municipio_id', type='many2one', string=u'Município', relation='sped.municipio'),

        'eh_orgao_publico': fields.boolean(u'É órgão público?'),
        'eh_cooperativa': fields.boolean(u'É cooperativa?'),

        #'participante_id': fields.one2many('sped.participante', 'partner_id', u'SPED'),
        #'cnpj_cpf': fields.function(_get_cnpj_cpf_funcao, type='char', string=u'CNPJ/CPF', fnct_search=_procura_cnpj_cpf, store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'razao_social': fields.function(_get_razao_social_funcao, type='char', string=u'Razão Social', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'fantasia': fields.function(_get_fantasia_funcao, type='char', string=u'Fantasia', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'endereco': fields.function(_get_endereco_funcao, type='char', string=u'Endereço', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'numero': fields.function(_get_numero_funcao, type='char', string=u'Número', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'complemento': fields.function(_get_complemento_funcao, type='char', string=u'Complemento', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'bairro': fields.function(_get_bairro_funcao, type='char', string=u'Bairro', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'municipio_id': fields.function(_get_municipio_id_funcao, type='many2one', string=u'Município', store=AJUSTA_VINDO_DO_PARTICIPANTE, relation='sped.municipio'),
        #'cep': fields.function(_get_cep_funcao, type='char', string=u'CEP', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'fone': fields.function(_get_fone_funcao, type='char', string=u'Fone', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        ##'celular': fields.function(_get_fone_funcao, type='char', string=u'Fone', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'email_nfe': fields.function(_get_email_nfe_funcao, type='char', string=u'Email para envio da NF-e', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'ie': fields.function(_get_ie_funcao, type='char', string=u'Inscrição estadual', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'im': fields.function(_get_im_funcao, type='char', string=u'Inscrição municipal', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'suframa': fields.function(_get_suframa_funcao, type='char', string=u'SUFRAMA', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'rntrc': fields.function(_get_rntrc_funcao, type='char', string=u'RNTRC', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'crc': fields.function(_get_crc_funcao, type='char', string=u'Conselho Regional de Contabilidade', store=AJUSTA_VINDO_DO_PARTICIPANTE),
        #'cnae_id': fields.function(_get_cnae_id_funcao, type='many2one', string=u'CNAE principal', store=AJUSTA_VINDO_DO_PARTICIPANTE, relation='sped.cnae'),
        'descricao': fields.function(_get_descricao, type='char', string=u'Descrição'),

        #
        # Após a transição, comentar os campos acima
        # e descomentar os campos abaixo
        #
        'cnpj_cpf': fields.char(u'CNPJ/CPF', size=18, help=u'Para participantes estrangeiros, usar EX9999, onde 9999 é um número a sua escolha'),
        'tipo_pessoa': fields.function(_get_tipo_pessoa, type='char', size=1, string=u'Tipo pessoa', store=True, select=True),
        #
        # Campos obrigatórios na emissão da NF-e e no SPED
        #
        'razao_social': fields.char(u'Razão Social', size=60),
        'fantasia': fields.char(u'Fantasia', size=60),
        'endereco': fields.char(u'Endereço', size=60),
        'numero': fields.char(u'Número', size=60),
        'complemento': fields.char(u'Complemento', size=60),
        'bairro': fields.char(u'Bairro', size=60),
        'municipio_id': fields.many2one('sped.municipio', u'Município', ondelete='restrict'),
        'cidade': fields.related('municipio_id', 'nome', type='char', string=u'Município', store=True),
        'estado': fields.related('municipio_id', 'estado', type='char', string=u'Estado', store=True),
        'cep': fields.char('CEP', size=9),
        #
        # Telefone e emeio para a emissão da NF-e
        #
        'fone': fields.char(u'Fone', size=18),
        'celular': fields.char(u'Celular', size=18),
        'email_nfe': fields.char(u'Email para envio da NF-e', size=60),
        #
        # Inscrições e registros
        #
        'contribuinte': fields.selection(IE_DESTINATARIO, u'Contribuinte'),
        'ie': fields.char(u'Inscrição estadual', size=18),
        'im': fields.char(u'Inscrição municipal', size=14),
        'suframa': fields.char(u'SUFRAMA', size=12),
        'rntrc': fields.char(u'RNTRC', size=15),
        'cnae_id': fields.many2one('sped.cnae', u'CNAE principal'),
        'cei': fields.char(u'CEI', size=15),
        'nire': fields.char(u'NIRE', size=11),

        'fone_comercial': fields.char(u'Fone Comercial', size=18),


        'rg_numero': fields.char(u'RG', size=14),
        'rg_orgao_emissor': fields.char(u'Órgão emisssor do RG', size=20),
        'rg_data_expedicao': fields.date(u'Data de expedição do RG'),
        'crc': fields.char(u'CRC', size=14),
        'crc_uf': fields.many2one('sped.estado', u'UF do CRC', ondelete='restrict'),
        'profissao': fields.char(u'Cargo', size=40),
        'sexo': fields.selection(SEXO, u'Sexo' ),
        'estado_civil': fields.selection(ESTADO_CIVIL, u'Estado civil'),
        'pais_nacionalidade_id': fields.many2one('sped.pais', u'Nacionalidade'),
        'email': fields.char(u'Email', size=60),
        
        'property_account_payable': fields.property('account.account', type='many2one', relation='account.account', string="Account Payable", help="This account will be used instead of the default one as the payable account for the current partner", required=False),
        'property_account_receivable': fields.property('account.account',type='many2one',relation='account.account',string="Account Receivable", help="This account will be used instead of the default one as the receivable account for the current partner",required=False),        
    }

    _defaults = {
        'eh_orgao_publico': False,
        'eh_cooperativa': False,
        'contribuinte': '2',
        #
        # Deixando todos como padrão cliente e fornecedor ao mesmo tempo
        #
        'customer': True,
        'supplier': True,        
    }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []

        res = []
        for partner_obj in self.browse(cr, uid, ids):
            if hasattr(partner_obj, 'name'):
                nome = partner_obj.name or u''

                if partner_obj.razao_social and partner_obj.razao_social.upper() != partner_obj.name.upper():
                    nome += ' [' + partner_obj.razao_social + ']'

                if partner_obj.cnpj_cpf:
                    nome += ' - ' + partner_obj.cnpj_cpf

                if partner_obj.fantasia and partner_obj.fantasia.upper() != partner_obj.name.upper():
                    if partner_obj.razao_social:
                        if partner_obj.razao_social.upper() != partner_obj.fantasia.upper():
                            nome += ' [' + partner_obj.fantasia + ']'

                    else:
                        nome += ' [' + partner_obj.fantasia + ']'

                if 'mostra_fone' in context:
                    if partner_obj.fone:
                        nome += ' - ' + partner_obj.fone

                    if partner_obj.celular:
                        nome += ' - ' + partner_obj.celular

                res.append((partner_obj.id, nome))
            else:
                res.append((partner_obj.id, ''))

        return res

    def name_search(self, cr, uid, name, args=[], operator='ilike', context={}, limit=100):
        # short-circuit ref match when possible
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            busca = [
                '|', '|', '|', '|', '|', '|',
                ('ref', '=', name),
                '|',
                ('cnpj_cpf', 'ilike', mascara(name, u'  .   .   /    -  ')),
                ('cnpj_cpf', 'ilike', mascara(name, u'   .   .   -  ')),
                ('razao_social', 'ilike', name),
                ('fantasia', 'ilike', name),
                ('ref', 'ilike', name),
                ('fone', 'ilike', mascara(name, u'(  )·    -    ')),
                '|', '|',
                ('celular', 'ilike', mascara(name, u'(  )·    -    ')),
                ('celular', 'ilike', mascara(name, u'(  )·   -   -   ')),
                ('celular', 'ilike', mascara(name, u'(  )·     -    ')),
            ] + args
            #print(busca)
            ids = self.search(cr, uid, busca, limit=limit, context=context)

            if ids:
                return self.name_get(cr, uid, ids, context)

        return super(res_partner, self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)

    def create(self, cr, uid, dados, context={}):
        if 'cnpj_cpf' in dados and dados['cnpj_cpf']:
            cnpj_cpf = limpa_formatacao(dados['cnpj_cpf'])

            if cnpj_cpf[:2] != 'EX':
                if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
                    raise osv.except_osv(u'Erro!', u'CNPJ ou CPF inválido!')

                if len(cnpj_cpf) == 14:
                    dados['cnpj_cpf'] = formata_cnpj(cnpj_cpf)

                else:
                    dados['cnpj_cpf'] = formata_cpf(cnpj_cpf)

            #
            # Impede a inclusão do mesmo CNPJ mais de uma vez
            #
            cnpj_ids = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', dados['cnpj_cpf'])])

            if len(cnpj_ids) > 0:
                raise osv.except_osv(u'Erro!', u'CNPJ/CPF já existe no cadastro!')

        if 'fone' in dados and dados['fone']:
            fone = dados['fone']
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                raise osv.except_osv(u'Erro!', u'Telefone fixo inválido!')

            dados['fone'] = formata_fone(fone)

        if 'celular' in dados and dados['celular']:
            fone = dados['celular']
            if not valida_fone_internacional(fone) and not valida_fone_celular(fone):
                raise osv.except_osv(u'Erro!', u'Telefone celular inválido!')

            dados['celular'] = formata_fone(fone)

        if 'suframa' in dados and dados['suframa']:
            suframa = dados['suframa']
            if not valida_inscricao_estadual(unicode(suframa), 'SUFRAMA'):
                raise osv.except_osv(u'Erro!', u'Inscrição na SUFRAMA inválida!')

            dados['suframa'] = formata_inscricao_estadual(unicode(suframa), 'SUFRAMA')

        if 'ie' in dados:
            dados['ie'] = dados['ie'] or u''

            if 'municipio_id' in dados:
                municipio_id = dados['municipio_id']
                ie = dados['ie']
                municipio_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_id)

                if dados['contribuinte'] == u'1' and ie.strip().upper() == u'ISENTO':
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode ser “ISENTO”!')

                if dados['contribuinte'] == u'1' and len(ie.strip()) == 0:
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode estar em branco!')

                if not valida_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf):
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual inválida!')

                dados['ie'] = formata_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf)

            elif (dados['ie'] != 'ISENTO' or len(dados['ie']) == 0) and dados['contribuinte']:
                raise osv.except_osv(u'Erro!', u'Informando inscrição estadual sem informar o município!')

        if 'cep' in dados and dados['cep']:
            cep = dados['cep']

            cep = limpa_formatacao(cep)
            if not cep.isdigit() or len(cep) != 8:
                raise osv.except_osv(u'Erro!', u'CEP inválido!')

            dados['cep'] = cep[:5] + '-' + cep[5:]

        if 'razao_social' in dados and not dados['razao_social']:
            dados['razao_social'] = dados['name']

        return super(res_partner, self).create(cr, uid, dados, context)

    def write(self, cr, uid, ids, dados, context={}):
        if 'cnpj_cpf' in dados and dados['cnpj_cpf']:
            cnpj_cpf = limpa_formatacao(dados['cnpj_cpf'])

            if cnpj_cpf[:2] != 'EX':
                if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
                    raise osv.except_osv(u'Erro!', u'CNPJ ou CPF inválido!')

                if len(cnpj_cpf) == 14:
                    dados['cnpj_cpf'] = formata_cnpj(cnpj_cpf)
                else:
                    dados['cnpj_cpf'] = formata_cpf(cnpj_cpf)

            #
            # Impede a inclusão do mesmo CNPJ mais de uma vez, exceto quando for o CNPJ de
            # uma company
            #
            company_ids = self.pool.get('res.company').search(cr, 1, [('partner_id', 'in', ids)])

            if len(company_ids) == 0:
                cnpj_ids = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', dados['cnpj_cpf'])])

                if len(cnpj_ids) > 0 and ids[0] not in cnpj_ids:
                    raise osv.except_osv(u'Erro!', u'CNPJ/CPF já existe no cadastro!')

        if 'fone' in dados and dados['fone']:
            fone = dados['fone']
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                raise osv.except_osv(u'Erro!', u'Telefone fixo inválido!')

            dados['fone'] = formata_fone(fone)

        if 'celular' in dados and dados['celular']:
            fone = dados['celular']
            if not valida_fone_internacional(fone) and not valida_fone_celular(fone):
                raise osv.except_osv(u'Erro!', u'Telefone celular inválido!')

            dados['celular'] = formata_fone(fone)

        if 'suframa' in dados and dados['suframa']:
            suframa = dados['suframa']
            if not valida_inscricao_estadual(suframa, 'SUFRAMA'):
                raise osv.except_osv(u'Erro!', u'Inscrição na SUFRAMA inválida!')

            dados['suframa'] = formata_inscricao_estadual(suframa, 'SUFRAMA')

        if 'ie' in dados:
            dados['ie'] = dados['ie'] or u''

            if 'municipio_id' in dados:
                municipio_id = dados['municipio_id']
                ie = dados['ie']
                municipio_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_id)

                if dados['contribuinte'] == u'1' and ie.strip().upper() == u'ISENTO':
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode ser “ISENTO”!')

                if dados['contribuinte'] == u'1' and len(ie.strip()) == 0:
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode estar em branco!')

                if not valida_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf):
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual inválida!')

                dados['ie'] = formata_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf)

            #elif (dados['ie'] != 'ISENTO' or len(dados['ie']) == 0) and dados['contribuinte']:
                #raise osv.except_osv(u'Erro!', u'Informando inscrição estadual sem informar o município!')

        if 'cep' in dados and dados['cep']:
            cep = dados['cep']

            cep = limpa_formatacao(cep)
            if not cep.isdigit() or len(cep) != 8:
                raise osv.except_osv(u'Erro!', u'CEP inválido!')

            dados['cep'] = cep[:5] + '-' + cep[5:]

        return super(res_partner, self).write(cr, uid, ids, dados, context)

    def onchange_cnpj_cpf(self, cr, uid, ids, cnpj_cpf, context={}):
        if not cnpj_cpf:
            return {}

        if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
            raise osv.except_osv(u'Erro!', u'CNPJ ou CPF inválido!')

        cnpj_cpf = limpa_formatacao(cnpj_cpf)

        if len(cnpj_cpf) == 14:
            cnpj_cpf = formata_cnpj(cnpj_cpf)
            tipo_pessoa = 'J'
            regime_tributario = '1'
        else:
            cnpj_cpf = formata_cpf(cnpj_cpf)
            tipo_pessoa = 'F'
            regime_tributario = '3'

        if cnpj_cpf[:2] == 'EX':
            tipo_pessoa = 'E'
            regime_tributario = '3'

        if ids != []:
            cnpj_ids = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', cnpj_cpf), '!', ('id', 'in', ids)])
        else:
            cnpj_ids = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', cnpj_cpf)])

        if len(cnpj_ids) > 0:
            return {'value': {'cnpj_cpf': cnpj_cpf}, 'warning': {'title': u'Aviso!', 'message': u'CNPJ/CPF já existe no cadastro!'}}

        return {'value': {'cnpj_cpf': cnpj_cpf,'tipo_pessoa': tipo_pessoa, 'contribuinte': '2', 'regime_tributario': regime_tributario}}

    def onchange_fone_celular(self, cr, uid, ids, fone, celular, context={}):
        print(fone, celular)
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

    def onchange_cep(self, cr, uid, ids, cep, contex={}):
        if not cep:
            return {}

        cep = limpa_formatacao(cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise osv.except_osv(u'Erro!', u'CEP inválido!')

        return {'value': {'cep': cep[:5] + '-' + cep[5:]}}

    def onchange_suframa(self, cr, uid, ids, suframa, context={}):
        if not suframa:
            return {}

        if not valida_inscricao_estadual(suframa, 'SUFRAMA'):
            raise osv.except_osv(u'Erro!', u'Inscrição na SUFRAMA inválida!')

        return {'value': {'suframa': formata_inscricao_estadual(suframa, 'SUFRAMA')}}

    def onchange_ie(self, cr, uid, ids, ie, municipio_id, contribuinte, context={}):
        if not ie:
            return {}

        if not municipio_id:
            raise osv.except_osv(u'Erro!', u'Para validação da inscrição estadual é preciso informar o município!')

        municipio_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_id)

        if contribuinte == u'1' and ie.strip().upper() == u'ISENTO':
            raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode ser “ISENTO”!')

        if not valida_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf):
            raise osv.except_osv(u'Erro!', u'Inscrição estadual inválida!')

        return {'value': {'ie': formata_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf)}}

    def address_get(self, cr, uid, ids, adr_pref=['default']):
        tipos_endereco = adr_pref
        address_pool = self.pool.get('res.partner.address')
        address_ids = address_pool.search(cr, uid, [('partner_id', 'in', ids)])
        address_rec = address_pool.read(cr, uid, address_ids, ['type'])
        res = list((addr['type'], addr['id']) for addr in address_rec)
        adr = dict(res)
        # get the id of the (first) default address if there is one,
        # otherwise get the id of the first address in the list
        if res:
            default_address = adr.get('default', res[0][1])
        else:
            default_address = False

        #
        # Caso não exista um endereço padrão, cria um
        #
        if not default_address:
            partner_id = ids[0]
            partner_obj = self.browse(cr, uid, partner_id)

            street = ''
            street2 = ''
            zip = ''
            city = ''
            country_id = False
            state_id = False

            if partner_obj.endereco:
                street = partner_obj.endereco

            if partner_obj.numero:
                street += ', ' + partner_obj.numero

            if partner_obj.complemento:
                street += ' - ' + partner_obj.complemento

            if partner_obj.bairro:
                street2 = partner_obj.bairro

            if partner_obj.cep:
                if len(partner_obj.cep) >= 8:
                    zip = partner_obj.cep[:5] + '-' + partner_obj.cep[5:]
                else:
                    zip = partner_obj.cep

            if partner_obj.municipio_id:
                country_id = partner_obj.municipio_id.pais_id.res_country_id.id
                state_id = partner_obj.municipio_id.estado_id.res_country_state_id.id
                city = partner_obj.municipio_id.nome

            dados = {
                    'partner_id': partner_id,
                    'name': partner_obj.name,
                    'phone': partner_obj.fone,
                    'mobile': partner_obj.celular,
                    'email': partner_obj.email_nfe,
                    'street': street,
                    'street2': street2,
                    'zip': zip,
                    'city': city,
                    'country_id': country_id,
                    'state_id': state_id,
                    'endereco': partner_obj.endereco,
                    'numero': partner_obj.numero,
                    'complemento': partner_obj.complemento,
                    'cep': partner_obj.cep,
                    'bairro': partner_obj.bairro,
                    'municipio_id': partner_obj.municipio_id and partner_obj.municipio_id.id or False,
            }

            default_address = address_pool.create(cr, uid, dados)

        result = {}
        for tipo in tipos_endereco:
            result[tipo] = adr.get(tipo, default_address)
        return result


res_partner()
