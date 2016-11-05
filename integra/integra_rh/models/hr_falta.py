# -*- coding: utf-8 -*-


from osv import fields, osv

TIPO_FALTA = (
    ('F', u'Falta'),
    ('S', u'Suspensão'),
    ('A', u'Advertência'),
)

class hr_falta(osv.Model):
    _name = 'hr.falta'
    _description = u'Faltas'
    _rec_name = 'employee_id'
    _order = 'data desc'

    _columns = {
        'tipo': fields.selection(TIPO_FALTA, string=u'Tipo', select=True),
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'employee_id': fields.many2one('hr.employee', u'Funcionário'),
        'data': fields.date(u'Data da falta'),
        'company_id': fields.related('contract_id', 'company_id', type='many2one', relation='res.company', string=u'Empresa'),
        'obs': fields.text(u'Observação'),
    }

    _defaults = {
        'tipo': 'F',
    }

    def onchange_employee_id(self, cr, uid, ids, employee_id, context={}):
        contract_pool = self.pool.get('hr.contract')

        valores = {
            'contract_id': False,
        }
        res = {
            'value': valores
        }

        if (not employee_id):
            return res

        #
        # Busca o contrato ativo do funcionário, e, caso haja mais de 1,
        # dá um erro
        #
        contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee_id), ('date_end', '=', None)])
        if len(contract_ids) > 1:
            raise osv.except_osv(u'Erro!', u'O funcionário tem mais de 1 contrato ativo!')
        elif len(contract_ids) == 0:
            raise osv.except_osv(u'Erro!', u'O funcionário não tem nenhum contrato ativo!')

        contract_id = contract_ids[0]
        valores['contract_id'] = contract_id

        return res

    _sql_constraints = [
        ('hr_falta_unique', 'unique(contract_id, data, tipo)',
            u'Não é permitido repetir a mesma data!'),
    ]


hr_falta()
