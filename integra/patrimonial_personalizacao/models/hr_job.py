# -*- coding: utf-8 -*-


from osv import fields, orm , osv
from integra_rh.constantes_rh import *
from pybrasil.data import agora


class hr_job_orcamento(osv.osv_memory):
    _name = 'hr.job.orcamento'
    _description = u'Cargos - orçamento'

    _columns = {
        'job_id': fields.many2one('hr.job', u'Cargo', ondelete='cascade'),
        'company_id': fields.many2one('res.company', u'Unidade', ondelete='restrict'),
        'quantidade': fields.integer(u'Orçamento'),
    }


hr_job_orcamento()


class hr_job(orm.Model):
    _name = 'hr.job'
    _inherit = 'hr.job'

    _columns = {
        'orcamento_ids': fields.one2many('hr.job.orcamento', 'job_id', u'Orçamento')
    }


hr_job()
