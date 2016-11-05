# -*- coding: utf-8 -*-


from osv import orm, fields, osv


class hr_job(orm.Model):
    _name = 'hr.job'
    _inherit = 'hr.job'

    _columns = {
        'fator_risco_ids': fields.many2many('sesmt.fator_risco', 'sesmt_fator_risco_hr_job', 'job_id', 'fator_risco_id', u'Fatores de risco'),
        'risco_acidente_ids': fields.many2many('sesmt.risco', 'sesmt_risco_acidente_hr_job', 'job_id', 'risco_id', u'Riscos de acidente'),
        'risco_ergonomico_ids': fields.many2many('sesmt.risco', 'sesmt_risco_ergonomico_hr_job', 'job_id', 'risco_id', u'Riscos ergonômicos'),
        'restricao_ids': fields.many2many('sesmt.restricao', 'sesmt_restricao_hr_job', 'job_id', 'restricao_id', u'Restrições'),
        'epi_ids': fields.many2many('sesmt.epi', 'sesmt_epi_hr_job', 'job_id', 'epi_id', u'EPIs'),
        'epi_eletivo_ids': fields.many2many('sesmt.epi', 'sesmt_epi_eletivo_hr_job', 'job_id', 'epi_id', u'EPIs eletivos'),
        'treinamento_ids': fields.many2many('sesmt.treinamento', 'sesmt_treinamento_hr_job', 'job_id', 'treinamento_id', u'Treinamentos'),
        'treinamento_eletivo_ids': fields.many2many('sesmt.treinamento', 'sesmt_treinamento_eletivo_hr_job', 'job_id', 'treinamento_id', u'Treinamentos eletivos'),
    }


hr_job()

