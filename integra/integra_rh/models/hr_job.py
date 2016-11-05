# -*- coding: utf-8 -*-


from osv import fields, orm


class hr_job(orm.Model):
    _name = 'hr.job'
    _inherit = 'hr.job'
    _description = 'Job Description'

    _columns = {
        'cbo_id': fields.many2one('hr.cbo', u'Código CBO'),
        'horas_mensalista': fields.float(u'Horas de trabalho no mês para mensalista'),
        'piso_salarial_ids': fields.one2many('hr.job_piso_salarial', 'job_id', u'Pisos salariais'),
    }

    _defaults = {
        'horas_mensalista': 220,
    }

    def piso_salarial(self, cr, uid, ids, data_inicial, data_final, context={}):
        res = {}

        for job_obj in self.browse(cr, uid, ids):
            #
            # Buscamos a alteração mais recente em relação ao período calculado
            #
            piso_atual = 0
            for piso_obj in job_obj.piso_salarial_ids:
                if piso_obj.data <= data_inicial:
                    piso_atual = piso_obj.piso_salarial or 0
                    break

            res[job_obj.id] = piso_atual

        if len(ids) == 1:
            res = res.values()[0]

        return res


hr_job()


class hr_job_piso_salarial(orm.Model):
    _name = 'hr.job_piso_salarial'
    _description = 'Piso salarial'
    #_inherit = 'hr.contract'
    _order = 'data desc'

    _columns = {
        'job_id': fields.many2one('hr.job', u'Cargo'),
        'data': fields.date(u'A partir de'),
        'piso_salarial': fields.float(u'Piso salarial'),
    }


hr_job_piso_salarial()
