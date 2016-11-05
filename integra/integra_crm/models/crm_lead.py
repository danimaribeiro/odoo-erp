# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields
from mail.mail_message import to_email


class crm_lead(orm.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'
    _order = 'partner_name,priority,date_action,id desc'

    _columns = {
        'data_prospeccao': fields.datetime(u'Data de prospecção'),
        'endereco': fields.char(u'Endereço', size=60),
        'numero': fields.char(u'Número', size=60),
        'complemento': fields.char(u'Complemento', size=60),
        'bairro': fields.char(u'Bairro', size=60),
        'municipio_id': fields.many2one('sped.municipio', u'Município'),
        'cep': fields.char('CEP', size=8),
        'motivo_id': fields.many2one('crm.motivo', u'Motivo para o estágio'),
    }

    def atualiza_endereco(self, cr, uid, ids):
        for lead_obj in self.browse(cr, uid, ids):
            street = ''
            street2 = ''
            zip = ''
            city = ''
            country_id = 'null'
            state_id = 'null'

            if lead_obj.endereco:
                street = lead_obj.endereco

            if lead_obj.numero:
                street += ', ' + lead_obj.numero

            if lead_obj.complemento:
                street += ' - ' + lead_obj.complemento

            if lead_obj.bairro:
                street2 = lead_obj.bairro

            if lead_obj.cep:
                if len(lead_obj.cep) >= 8:
                    zip = lead_obj.cep[:5] + '-' + lead_obj.cep[5:]
                else:
                    zip = lead_obj.cep

            if lead_obj.municipio_id:
                country_id = str(lead_obj.municipio_id.pais_id.res_country_id.id)
                state_id = str(lead_obj.municipio_id.estado_id.res_country_state_id.id)
                city = lead_obj.municipio_id.nome

            sql = "update crm_lead set street='%s', street2='%s', city='%s', zip='%s', state_id=%s, country_id=%s where id = %d;"

            cr.execute(sql % (street, street2, city, zip, state_id, country_id, lead_obj.id))

    def create(self, cr, uid, vals, context=None):
        res = super(crm_lead, self).create(cr, uid, vals, context=context)
        self.atualiza_data_criacao(cr, uid)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(crm_lead, self).write(cr, uid, ids, vals, context=context)
        self.atualiza_data_criacao(cr, uid)
        return res

    def atualiza_data_criacao(self, cr, uid):
        cr.execute('''
            begin;
            update crm_lead
            set create_date = data_prospeccao
            where create_date != data_prospeccao and data_prospeccao is not null;
            commit work;
            begin;
            update crm_lead
            set data_prospeccao = create_date
            where data_prospeccao is null;
            commit work;
        ''')

    def _lead_create_partner_address(self, cr, uid, lead, partner_id, context=None):
        address = self.pool.get('res.partner.address')
        return address.create(cr, uid, {
                    'partner_id': partner_id,
                    'name': lead.contact_name,
                    'phone': lead.phone,
                    'mobile': lead.mobile,
                    'email': lead.email_from and to_email(lead.email_from)[0],
                    'fax': lead.fax,
                    'title': lead.title and lead.title.id or False,
                    'function': lead.function,
                    'street': lead.street,
                    'street2': lead.street2,
                    'zip': lead.zip,
                    'city': lead.city,
                    'country_id': lead.country_id and lead.country_id.id or False,
                    'state_id': lead.state_id and lead.state_id.id or False,
                    'endereco': lead.endereco,
                    'numero': lead.numero,
                    'complemento': lead.complemento,
                    'cep': lead.cep,
                    'bairro': lead.bairro,
                    'municipio_id': lead.municipio_id and lead.municipio_id.id or False,
                })


crm_lead()
