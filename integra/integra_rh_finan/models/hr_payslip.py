# -*- coding: utf-8 -*-


from osv import fields, osv
from pybrasil.valor.decimal import Decimal as D
from copy import copy


class hr_payslip(osv.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    _columns = {
        'remessa_id': fields.many2one(u'finan.remessa_folha', u'Arquivo de remessa'),
        'bank_id': fields.related('employee_id', 'bank_id', type='many2one', relation='res.bank', string=u'Banco'),
        'banco_agencia': fields.related('employee_id', 'banco_agencia', type='char', string=u'Agência'),
        'banco_conta': fields.related('employee_id', 'banco_conta', type='char', string=u'Conta'),
        'remessa_ids': fields.one2many('finan.remessa_folha', 'payslip_id', u'Arquivos de remessa'),
    }

    def copy(self, cr, uid, ids, dados, context={}):
        dados['remessa_id'] = False
        dados['bank_id'] = False
        dados['remessa_ids'] = False

        return super(hr_payslip, self).copy(cr, uid, ids, dados, context)

    def realiza_rateio(self, cr, uid, ids, campo_valor='valor_liquido', padrao={}, rateio={}, conta_obj=None, context={}):
        if not ids:
            return D(0)

        rubrica_pool = self.pool.get('hr.salary.rule')
        cc_pool = self.pool.get('finan.centrocusto')
        campos = cc_pool.campos_rateio(cr, uid)

        if campo_valor == 'valor_liquido':
            rubrica = 'LIQ'
        else:
            rubrica = campo_valor

        rubrica_ids = rubrica_pool.search(cr, 1, [('code', '=', rubrica)])
        rubrica_obj = rubrica_pool.browse(cr, 1, rubrica_ids[0])

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        total = D(0)
        for h_obj in self.browse(cr, uid, ids):
            p = copy(padrao)
            p['company_id'] = h_obj.company_id.id
            p['hr_contract_id'] = h_obj.contract_id.id
            p['hr_department_id'] = h_obj.contract_id.department_id.id

            #
            # Estrutura para determinar qual conta usar quando
            # despesa ou custo no rateio
            #
            conta_id = [
                'tipo_conta',
                {
                    'D': rubrica_obj.finan_conta_custo_id.id,
                    'C': rubrica_obj.finan_conta_custo_id.id,
                    False: rubrica_obj.finan_conta_custo_id.id
                }
            ]

            if rubrica_obj.finan_conta_custo_id:
                conta_id[1]['C'] = rubrica_obj.finan_conta_custo_id.id

            if h_obj.tipo == 'F':
                if rubrica_obj.finan_conta_despesa_ferias_id:
                    conta_id[1]['D'] = rubrica_obj.finan_conta_despesa_ferias_id.id
                    conta_id[1]['C'] = rubrica_obj.finan_conta_despesa_ferias_id.id
                    conta_id[1][False] = rubrica_obj.finan_conta_despesa_ferias_id.id

                if rubrica_obj.finan_conta_custo_ferias_id:
                    conta_id[1]['C'] = rubrica_obj.finan_conta_custo_ferias_id.id
                    conta_id[1][False] = rubrica_obj.finan_conta_custo_ferias_id.id

            elif h_obj.tipo == 'R':
                if rubrica_obj.finan_conta_despesa_rescisao_id:
                    conta_id[1]['D'] = rubrica_obj.finan_conta_despesa_rescisao_id.id
                    conta_id[1]['C'] = rubrica_obj.finan_conta_despesa_rescisao_id.id
                    conta_id[1][False] = rubrica_obj.finan_conta_despesa_rescisao_id.id

                if rubrica_obj.finan_conta_custo_rescisao_id:
                    conta_id[1]['C'] = rubrica_obj.finan_conta_custo_rescisao_id.id
                    conta_id[1][False] = rubrica_obj.finan_conta_custo_rescisao_id.id

            elif h_obj.tipo == 'D':
                if rubrica_obj.finan_conta_despesa_13_id:
                    conta_id[1]['D'] = rubrica_obj.finan_conta_despesa_13_id.id
                    conta_id[1]['C'] = rubrica_obj.finan_conta_despesa_13_id.id
                    conta_id[1][False] = rubrica_obj.finan_conta_despesa_13_id.id

                if rubrica_obj.finan_conta_custo_13_id:
                    conta_id[1]['C'] = rubrica_obj.finan_conta_custo_13_id.id
                    conta_id[1][False] = rubrica_obj.finan_conta_custo_13_id.id

            #
            # Força a tratativa de uma conta que não está vinculada à rubrica
            #
            if conta_obj is not None:
                conta_id[1]['D'] = conta_obj.id
                conta_id[1]['C'] = conta_obj.id
                conta_id[1][False] = conta_obj.id

                if conta_obj.tipo == 'D' and conta_obj.conta_complementar_custo_id:
                    conta_id[1]['C'] = conta_obj.conta_complementar_custo_id.id
                    conta_id[1][False] = conta_obj.conta_complementar_custo_id.id
                elif conta_obj.tipo == 'C' and conta_obj.conta_complementar_despesa_id:
                    conta_id[1]['D'] = conta_obj.conta_complementar_despesa_id.id

            p['conta_id'] = conta_id

            if campo_valor == 'valor_liquido':
                valor = D(h_obj.valor_liquido)
            else:
                valor = D(0)
                for hl in h_obj.line_ids:
                    if hl.code == rubrica and '_anterior' not in hl.code:
                        valor = D(hl.total)

            if valor <= 0:
                continue

            total += valor

            if h_obj.contract_id.centrocusto_id:
                cc_pool.realiza_rateio(cr, uid, [h_obj.contract_id.centrocusto_id.id], valor=valor, padrao=p, rateio=rateio, context=context)
            else:
                cc_pool._realiza_rateio(valor, 100, campos, p, rateio)

        return total

hr_payslip()
