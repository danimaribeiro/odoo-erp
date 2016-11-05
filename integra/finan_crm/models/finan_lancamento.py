# -*- coding: utf-8 -*-

from osv import fields, osv


class finan_lancamento(osv.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'crm_phonecall_ids': fields.one2many('crm.phonecall', 'finan_lancamento_id', u'Ligações telefônicas'),
        'partner_fone': fields.related('partner_id', 'fone', type='char', string='Fone'),
        'partner_celular': fields.related('partner_id', 'celular', type='char', string='Fone'),
    }

    def agenda_ligacao(self, cr, uid, ids, hora, resumo_ligacao, descricao, fone, user_id, acao='schedule', context={}):
        """
        action :('schedule','Schedule a call'), ('log','Log a call')
        """
        ligacao_pool= self.pool.get('crm.phonecall')
        dados_ligacao = {}

        for lancamento_obj in self.browse(cr, uid, ids, context=context):
            dados = {
                    'name' : resumo_ligacao,
                    'finan_lancamento_id': lancamento_obj.id,
                    'opportunity_id' : False,
                    'user_id' : user_id or uid,
                    'categ_id' : False,
                    'description' : descricao or '',
                    'date' : hora,
                    'section_id' : False,
                    'partner_id': lancamento_obj.partner_id and lancamento_obj.partner_id.id or False,
                    'partner_address_id': lancamento_obj.res_partner_address_id and lancamento_obj.res_partner_address_id.id or False,
                    'partner_phone' : fone or lancamento_obj.partner_fone or (lancamento_obj.res_partner_address_id and lancamento_obj.res_partner_address_id.phone or False),
                    'partner_mobile' : lancamento_obj.partner_celular or lancamento_obj.res_partner_address_id and lancamento_obj.res_partner_address_id.mobile or False,
                    #'priority': lancamento_obj.priority,
            }

            ligacao_id = ligacao_pool.create(cr, uid, dados, context=context)
            ligacao_pool.case_open(cr, uid, [ligacao_id])
            if acao == 'log':
                ligacao_pool.case_close(cr, uid, [ligacao_id])
            dados_ligacao[lancamento_obj.id] = ligacao_id

        return dados_ligacao


finan_lancamento()