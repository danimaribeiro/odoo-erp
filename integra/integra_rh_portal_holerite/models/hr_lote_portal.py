# -*- coding: utf-8 -*-

from osv import fields, osv
#from pybrasil.data import parse_datetime
from integra_rh.models.hr_payslip_input import primeiro_ultimo_dia_mes, mes_passado, MESES, MESES_DIC
#from finan.wizard.finan_relatorio import Report
#import os
#import base64
from pybrasil.inscricao import limpa_formatacao



#DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
#JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')


class hr_lote_portal(osv.Model):
    _name = 'hr.lote_portal'
    _rec_name = 'company_id'
    _description = u'Lotes de holerites para o portal'
    _order = 'ano desc, mes desc, company_id'

    def get_user_ids(self, cr, uid, ids, nome_campo, args, context={}):
        if not len(ids):
            return {}

        res = {}
        
        user_pool = self.pool.get('res.users')

        for lote_portal_obj in self.browse(cr, uid, ids):
            user_ids = []
            
            for holerite_obj in lote_portal_obj.holerite_ids:
                print('cpf', holerite_obj.contract_id.employee_id.cpf, limpa_formatacao(holerite_obj.contract_id.employee_id.cpf))
                cpf_ids = user_pool.search(cr, 1, [('login', '=', limpa_formatacao(holerite_obj.contract_id.employee_id.cpf))])
                print(cpf_ids)
                
                if cpf_ids:
                    if cpf_ids[0] not in user_ids:
                        user_ids.append(cpf_ids[0])
                    
            res[lote_portal_obj.id] = user_ids

        return res

    _columns = {
        'ano': fields.integer(u'Ano', select=True),
        'mes': fields.selection(MESES, u'Mês', select=True),
        'company_id': fields.many2one('res.company', u'Unidade/Empresa', select=True),
        'tipo': fields.selection([['N', u'Normal'], ['D', u'13º'], ['F', u'Férias']], u'Tipo', select=True),
        
        'user_ids': fields.function(get_user_ids, type='one2many', relation='res.users', method=True, string=u'Usuários e senhas'),
        
        'holerite_ids': fields.many2many('hr.payslip', 'hr_lote_portal_payslip', 'lote_id', 'payslip_id', u'Holerites a liberar'),
    }

    _defaults = {
        'ano': lambda *args, **kwargs: mes_passado()[0],
        'mes': lambda *args, **kwargs: str(mes_passado()[1]),
        'tipo': 'N',
    }

    def liberar_portal(self, cr, uid, ids, context={}):
        if not ids:
            return False

        for lote_portal_obj in self.browse(cr, uid, ids):
            for holerite_obj in lote_portal_obj.holerite_ids:
                holerite_obj.liberar_portal()

        return True


hr_lote_portal()
