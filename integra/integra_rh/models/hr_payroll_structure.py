#-*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_datetime
from datetime import date
from integra_rh.constantes_rh import TIPO_AFASTAMENTO, TIPO_SAQUE, TIPO_DESLIGAMENTO_RAIS
from osv import fields, osv


class hr_payroll_structure(osv.Model):
    _name = 'hr.payroll.structure'
    #_inherit = 'hr.payroll.structure'
    _description = 'Salary Structure'
    _order = 'name'

    _columns = {
        'name': fields.char(u'Descrição', size=256, required=True),
        'code': fields.char(u'Código', size=64, required=True),
        'company_id': fields.many2one('res.company', u'Empresa', required=False),
        'note': fields.text(u'Description'),
        'parent_id': fields.many2one('hr.payroll.structure', u'Estrutura pai'),
        'children_ids': fields.one2many('hr.payroll.structure', 'parent_id', u'Estruturas filhas'),
        'tipo': fields.selection((('N', 'Normal'), ('F', u'Férias'), ('R', u'Rescisão'), ('P', u'Parcial/retorno'), ('D', u'Décimo terceiro'), ('A', u'Aviso prévio')), string=u'Tipo'),
        'estrutura_ferias_id': fields.many2one('hr.payroll.structure', u'Estrutura de férias'),
        'estrutura_retorno_ferias_id': fields.many2one('hr.payroll.structure', u'Estrutura de retorno de férias'),
        'rule_ids':fields.many2many('hr.salary.rule', 'hr_structure_salary_rule_rel', 'struct_id', 'rule_id', u'Rubricas'),
        'afastamento_imediato': fields.boolean(u'Afastamento imediato na rescisão (justa causa, término de contrato etc.)'),
        'estrutura_adiantamento_decimo_terceiro_id': fields.many2one('hr.payroll.structure', u'Estrutura de adiantamento do décimo terceiro'),
        'estrutura_decimo_terceiro_id': fields.many2one('hr.payroll.structure', u'Estrutura de décimo terceiro'),
        'dispensa_empregador': fields.boolean(u'Dispensa pelo empregador?'),
        'codigo_afastamento': fields.char(u'Código de afastamento', size=5),
        'codigo_afastamento_cef': fields.char(u'Código de afastamento C.E.F', size=10),
        'codigo_saque': fields.selection(TIPO_SAQUE, u'Código de saque', size=2),
        'ignora_rubrica_funcionario': fields.boolean(u'Ignora rubrica específica do funcionário?'),
        'ignora_rubrica_funcionario_quantidade': fields.boolean(u'Ignora rubrica específica do funcionário com quantidade e valor?'),
        'codigo_desligamento_rais': fields.selection(TIPO_DESLIGAMENTO_RAIS, u'Código desligamento RAIS'),
        'complementar': fields.boolean(u'Complementar'),
    }

    def _get_parent(self, cr, uid, context=None):
        obj_model = self.pool.get('ir.model.data')
        res = False
        data_id = obj_model.search(cr, uid, [('model', '=', 'hr.payroll.structure'), ('name', '=', 'structure_base')])
        if data_id:
            res = obj_model.browse(cr, uid, data_id[0], context=context).res_id
        return res

    _defaults = {
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
        'parent_id': _get_parent,
        'tipo': 'N',
        'afastamento_imediato': False,
        'dispensa_empregador': True,
        'ignora_rubrica_funcionario': False,
        'ignora_rubrica_funcionario_quantidade': False,
        'codigo_desligamento_rais': '10',
    }

    def copy(self, cr, uid, id, default=None, context=None):
        """
        Create a new record in hr_payroll_structure model from existing one
        @param cr: cursor to database
        @param user: id of current user
        @param id: list of record ids on which copy method executes
        @param default: dict type contains the values to be override during copy of object
        @param context: context arguments, like lang, time zone

        @return: returns a id of newly created record
        """
        if not default:
            default = {}
        default.update({
            'code': self.browse(cr, uid, id, context=context).code + "(copia)",
            'company_id': self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        })
        return super(osv.Model, self).copy(cr, uid, id, default, context=context)

    def get_all_rules(self, cr, uid, structure_ids, context=None):
        """
        @param structure_ids: list of structure
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """

        all_rules = []
        for struct in self.browse(cr, uid, structure_ids, context=context):
            all_rules += self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, struct.rule_ids, context=context)
        return all_rules

    def _get_parent_structure(self, cr, uid, ids, context=None):
        if not ids:
            return []

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        parent_ids = []

        for estrutura_obj in self.browse(cr, uid, ids, context=context):
            if estrutura_obj.parent_id:
                parent_ids.append(estrutura_obj.parent_id.id)

        if parent_ids:
            parent_ids = self._get_parent_structure(cr, uid, parent_ids, context)

        return parent_ids + ids


hr_payroll_structure()
