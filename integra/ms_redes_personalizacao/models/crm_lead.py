# -*- coding: utf-8 -*-

from osv import osv, fields


class crm_lead(osv.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    _columns = {
        'project_orcamento_modelo_id': fields.many2one('project.orcamento', u'Orçamento modelo'),
        'project_orcamento_id': fields.many2one('project.orcamento', u'Orçamento'),
    }

    def criar_project_orcamento(self, cr, uid, ids, context={}):
        orcamento_pool = self.pool.get('project.orcamento')

        for lead_obj in self.browse(cr, uid, ids, context=context):
            dados = {
                'crm_lead_id': lead_obj.id,
                'partner_id': lead_obj.partner_id.id if lead_obj.partner_id else False,
            }

            if lead_obj.project_id:
                dados['project_id'] = lead_obj.project_id.id

            orcamento_id = orcamento_pool.copy(cr, uid, lead_obj.project_orcamento_modelo_id.id, dados, context=context)
            lead_obj.write({'project_orcamento_id': orcamento_id})

        return


crm_lead()
