# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


# from datetime import datetime
from osv import fields, osv


class finan_rateio(osv.Model):
    _description = u'Rateio entre centros de custo'
    _name = 'finan.rateio'
    _inherit = 'finan.rateio'

    _columns = {
        'project_id': fields.many2one('project.project', u'Projeto', select=True, ondelete='restrict'),
    }

    #_sql_constraints = [
        #('rateio_centrocusto_unique', 'unique(centrocusto_pai_id, centrocusto_id, contrato_id)',
            #u'Não é permitido repetir um mesmo centro de custo e contrato!'),
    #]


finan_rateio()
