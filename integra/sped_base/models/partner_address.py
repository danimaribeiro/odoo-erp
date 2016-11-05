# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)
from pybrasil.base import mascara


TIPOS_ENDERECO = (
    ('contact', u'Contato'),
    ('delivery', u'Entrega'),
    ('invoice', u'Faturamento'),
    ('instalacao', u'Instalação'),
    ('other', u'Outro'),
    ('default', u'Comercial/Padrão'),
    ('assina', u'Assina pela empresa'),
    ('refcom', u'Referência comercial'),
    ('refpes', u'Referência pessoal'),
)


class res_partner_address(osv.Model):
    _description = 'Partner Addresses'
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'

    def get_participante_campo(self, cr, uid, ids, campo, arg=None, context={}):
        if not len(ids):
            return {}

        res = {}
        for partner_obj in self.browse(cr, uid, ids):
            valor_campo = False

            if campo == 'fone' and partner_obj.phone:
                valor_campo = partner_obj.phone

            elif campo == 'celular' and partner_obj.mobile:
                valor_campo = partner_obj.mobile

            res[partner_obj.id] = valor_campo

        return res

    _columns = {
        'endereco': fields.char(u'Endereço', size=60),
        'numero': fields.char(u'Número', size=60),
        'complemento': fields.char(u'Complemento', size=60),
        'bairro': fields.char(u'Bairro', size=60),
        'municipio_id': fields.many2one('sped.municipio', u'Município', ondelete='restrict'),
        'cidade': fields.related('municipio_id', 'nome', type='char', string=u'Município', store=True),
        'estado': fields.related('municipio_id', 'estado', type='char', string=u'Estado', store=True),
        'cep': fields.char('CEP', size=9),
        'type': fields.selection(TIPOS_ENDERECO, u'Tipo do endereço', help="Used to select automatically the right address according to the context in sales and purchases documents."),

        'fone': fields.function(get_participante_campo, type='char', string=u'Fone', store=True),
        'celular': fields.function(get_participante_campo, type='char', string=u'Celular', store=True),

        #'street': fields.char('Street', size=128),
        #'street2': fields.char('Street2', size=128),
        #'zip': fields.char('Zip', change_default=True, size=24),
        #'city': fields.char('City', size=128),
        #'state_id': fields.many2one("res.country.state", 'Fed. State', domain="[('country_id','=',country_id)]"),
        #'country_id': fields.many2one('res.country', 'Country'),
        'cpf': fields.char(u'CPF', size=14, select=True),
        'rg_numero': fields.char(u'RG', size=14, select=True),
        #'rg_orgao_emissor': fields.char(u'Órgão emisssor do RG', size=20),
        #'rg_data_expedicao': fields.date(u'Data de expedição do RG'),
    }

    def _display_address(self, cr, uid, endereco_obj, context=None):
        u'''Formata o endereço, segundo o site dos Correios:
        http://www.correios.com.br/servicos/cep/cep_formas.cfm
        '''
        texto = ''

        texto += endereco_obj.endereco or ''

        if endereco_obj.numero:
            texto += ', ' + endereco_obj.numero

        if endereco_obj.complemento:
            texto += ' - ' + endereco_obj.complemento

        if endereco_obj.bairro:
            texto += '\n' + endereco_obj.bairro

        if endereco_obj.municipio_id:
            if endereco_obj.municipio_id.estado_id.uf != 'EX':
                texto += '\n' + endereco_obj.municipio_id.nome + ' - ' + endereco_obj.municipio_id.estado_id.uf
                texto += '\n' + endereco_obj.cep[0:5] + '-' + endereco_obj.cep[5:]

            else:
                texto += '\n' + endereco_obj.municipio_id.nome
                texto += '\n' + endereco_obj.municipio_id.pais_id.res_country_id.code + '-' + endereco_obj.cep
                texto += '\n' + endereco_obj.municipio_id.pais_id.res_country_id.code + '-' + endereco_obj.municipio_id.pais_id.nome

        return texto

    def atualiza_endereco(self, cr, uid, ids):
        for endereco_obj in self.browse(cr, uid, ids):
            street = ''
            street2 = ''
            zip = ''
            city = ''
            country_id = 'null'
            state_id = 'null'

            if endereco_obj.endereco:
                street = endereco_obj.endereco

            if endereco_obj.numero:
                street += ', ' + endereco_obj.numero

            if endereco_obj.complemento:
                street += ' - ' + endereco_obj.complemento

            if endereco_obj.bairro:
                street2 = endereco_obj.bairro

            if endereco_obj.cep:
                if len(endereco_obj.cep) >= 8:
                    zip = endereco_obj.cep[:5] + '-' + endereco_obj.cep[5:]
                else:
                    zip = endereco_obj.cep

            if endereco_obj.municipio_id:
                country_id = str(endereco_obj.municipio_id.pais_id.res_country_id.id)
                state_id = str(endereco_obj.municipio_id.estado_id.res_country_state_id.id)
                city = endereco_obj.municipio_id.nome
                city = city.replace("'", "''")

            sql = "update res_partner_address set street='%s', street2='%s', city='%s', zip='%s', state_id=%s, country_id=%s where id = %d;"

            cr.execute(sql % (street, street2, city, zip, state_id, country_id, endereco_obj.id))

    def write(self, cr, uid, ids, dados, context=None):
        res = super(res_partner_address, self).write(cr, uid, ids, dados, context=context)

        self.atualiza_endereco(cr, uid, ids)

        return res

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if not len(ids):
            return []

        res = {}

        for endereco_obj in self.browse(cr, uid, ids):
            if context.get('contact_display', 'contact') == 'partner' and endereco_obj.partner_id:
                res[endereco_obj.id] = endereco_obj.partner_id.name
            else:
                res[endereco_obj.id] = ''

                if context.get('contrato', '') == '':
                    if endereco_obj.name:
                        res[endereco_obj.id] += endereco_obj.name

                #if endereco_obj.street:
                    #if len(res[endereco_obj.id]):
                        #res[endereco_obj.id] += ' - '
                    #res[endereco_obj.id] += endereco_obj.street

                #if endereco_obj.street2:
                    #if len(res[endereco_obj.id]):
                        #res[endereco_obj.id] += ' - '
                    #res[endereco_obj.id] += endereco_obj.street2

                if endereco_obj.endereco:
                    if len(res[endereco_obj.id]):
                        res[endereco_obj.id] += ' - '
                    res[endereco_obj.id] += endereco_obj.endereco.strip()

                if endereco_obj.numero:
                    if len(res[endereco_obj.id]):
                        res[endereco_obj.id] += ', '
                    res[endereco_obj.id] += endereco_obj.numero.strip()

                if endereco_obj.complemento:
                    if len(res[endereco_obj.id]):
                        res[endereco_obj.id] += ' - '
                    res[endereco_obj.id] += endereco_obj.complemento.strip()

                if endereco_obj.municipio_id:
                    if len(res[endereco_obj.id]):
                        res[endereco_obj.id] += ' - '
                    res[endereco_obj.id] += endereco_obj.municipio_id.nome + '-' + endereco_obj.municipio_id.estado_id.uf

                #if endereco_obj.zip:
                    #if len(res[endereco_obj.id]):
                        #res[endereco_obj.id] += ' - '
                    #res[endereco_obj.id] += endereco_obj.zip

                if endereco_obj.cep:
                    if len(res[endereco_obj.id]):
                        res[endereco_obj.id] += ' - '
                    res[endereco_obj.id] += endereco_obj.cep

                if not len(res[endereco_obj.id]):
                    res[endereco_obj.id] = '/'

                if context.get('contact_display', 'contact') == 'partner_address' and endereco_obj.partner_id:
                    res[endereco_obj.id] = endereco_obj.partner_id.name + ':' + res[endereco_obj.id]

        return res.items()

    def onchange_cpf(self, cr, uid, ids, cpf, context={}):
        if not cpf:
            return {}

        if not valida_cpf(cpf):
            raise osv.except_osv(u'Erro!', u'CPF inválido!')

        cpf = limpa_formatacao(cpf)
        cpf = formata_cpf(cpf)

        return {'value': {'cpf': cpf}}

    def create(self, cr, uid, dados, context={}):
        if 'cpf' in dados and dados['cpf']:
            cpf = limpa_formatacao(dados['cpf'])
            if not valida_cpf(cpf):
                raise osv.except_osv(u'Erro!', u'CPF inválido!')

            dados['cpf'] = formata_cpf(cpf)

        if 'phone' in dados and dados['phone']:
            fone = dados['phone']
            dados['phone'] = formata_varios_fones(fone)

        if 'mobile' in dados and dados['mobile']:
            fone = dados['mobile']
            dados['mobile'] = formata_varios_fones(fone)

        if 'cep' in dados and dados['cep']:
            cep = dados['cep']

            cep = limpa_formatacao(cep)
            if not cep.isdigit() or len(cep) != 8:
                raise osv.except_osv(u'Erro!', u'CEP inválido!')

            dados['cep'] = cep[:5] + '-' + cep[5:]

        res = super(res_partner_address, self).create(cr, uid, dados, context=context)
        self.atualiza_endereco(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context={}):
        if 'cpf' in dados and dados['cpf']:
            cpf = limpa_formatacao(dados['cpf'])
            if not valida_cpf(cpf):
                raise osv.except_osv(u'Erro!', u'CPF inválido!')

            dados['cpf'] = formata_cpf(cpf)

        if 'phone' in dados and dados['phone']:
            fone = dados['phone']
            dados['phone'] = formata_varios_fones(fone)

        if 'mobile' in dados and dados['mobile']:
            fone = dados['mobile']
            dados['mobile'] = formata_varios_fones(fone)

        if 'cep' in dados and dados['cep']:
            cep = dados['cep']

            cep = limpa_formatacao(cep)
            if not cep.isdigit() or len(cep) != 8:
                raise osv.except_osv(u'Erro!', u'CEP inválido!')

            dados['cep'] = cep[:5] + '-' + cep[5:]

        return super(res_partner_address, self).write(cr, uid, ids, dados, context)

    def onchange_cep(self, cr, uid, ids, cep, contex={}):
        if not cep:
            return {}

        cep = limpa_formatacao(cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise osv.except_osv(u'Erro!', u'CEP inválido!')

        return {'value': {'cep': cep[:5] + '-' + cep[5:]}}

res_partner_address()
