# -*- coding: utf-8 -*-


from osv import fields, orm


class hr_job(orm.Model):
    _name = 'hr.job'
    _inherit = 'hr.job'
    _description = 'Job Description'

    _columns = {
        'lo_modelo_ids': fields.many2many('lo.modelo', 'lo_modelo_hr_job', 'hr_job_id', 'lo_modelo_id', u'Modelos LibreOffice'),
    }


hr_job()
