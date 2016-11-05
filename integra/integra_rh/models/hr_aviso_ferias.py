# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from datetime import datetime,timedelta



TIPO_DE_FERIAS = [
    ('1', 'Normal'),
    ('2', 'Coletiva'),
    ('3', 'antecipada'),
]

class hr_ferias(orm.Model):
    _name = 'hr.ferias'
    _description = 'Aviso de Ferias'

    _columns = {
        'employee_id': fields.many2one('hr.employee', u'Funcionário'),
        'contract_id': fields.many2one('hr.contract', u'Contrato'),
        'dt_aviso_de_ferias': fields.date(u'Data do aviso de ferias'),
        'dt_inicio_de_gozo': fields.date(u'Data de inicio de gozo'),
        'dt_final_de_gozo': fields.date(u'Data do fim de gozo'),
        'dt_inicio_periodo_de_aquisicao': fields.date(u'Data do inicio do período de aquisição'),
        'dt_fim_do_periodo_de_aquisicao': fields.date(u'Data do fim do período de aquisição'),
        'nro_dias_do_abono_pecuniario': fields.integer(u'Quantos dias de abono pecuniario'),
        'tipo_de_ferias': fields.selection(TIPO_DE_FERIAS, u'Tipo de ferias', required=True),
    }
    _defaults = {
        'tipo_de_ferias': '1',
    }

    def onchange_employee_id(self, cr, uid, ids, employee_id):
        valores = {}
        retorno = {'value': valores}
        contract_pool = self.pool.get('hr.contract')
        contract_ids = contract_pool.search(cr, uid, [('employee_id', '=', employee_id), ('date_end', '=', False)])
        variavel_dt_ultimas_ferias = ""
        if contract_ids:
            if len(contract_ids) > 1:
                raise osv.except_osv(u'Inválido!', u'Há mais de 1 contrato ativo para o funcionário!')

            contract_id = contract_ids[0]
            valores['contract_id'] = contract_id
            contract_obj = contract_pool.browse(cr, uid, contract_id)

            variavel_dt_de_admicao = datetime.strptime(contract_obj.date_start, '%Y-%m-%d')
            variavel_dt_inicio_periodo_de_aquisicao = variavel_dt_de_admicao + timedelta(days=365)
            variavel_dt_final_periodo_de_aquisicao = variavel_dt_inicio_periodo_de_aquisicao + timedelta(days=364)

            ferias_pool = self.pool.get('hr.ferias')
            ferias_ids = ferias_pool.search(cr, uid, [('employee_id', '=', employee_id)])

            if ferias_ids:
                if len(ferias_ids) > 1:

                   ferias_id = ferias_ids[0]
                   valores['ferias_id'] = ferias_id
                   ferias_obj = ferias_pool.browse(cr, uid, ferias_id)
                   variavel_dt_ultimas_ferias = datetime.strptime(ferias_obj.dt_inicio_de_gozo, '%Y-%m-%d')
                   variavel_dt_inicio_periodo_de_aquisicao = variavel_dt_ultimas_ferias + timedelta(days=365)
                   variavel_dt_final_periodo_de_aquisicao = variavel_dt_inicio_periodo_de_aquisicao + timedelta(days=364)

        valores['dt_inicio_periodo_de_aquisicao'] = str(variavel_dt_inicio_periodo_de_aquisicao)
        valores['dt_fim_do_periodo_de_aquisicao'] = str(variavel_dt_final_periodo_de_aquisicao)

         #valores[''] = str(variavel_dt_de_admicao)
         #valores[''] = str(variavel_dt_ultimas_ferias)


        return retorno
hr_ferias()

