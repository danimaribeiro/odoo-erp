# -*- coding: utf-8 -*-


from osv import fields, osv


class hr_contract(osv.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    _columns = {
        'centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo'),
    }

    def verifica_rateio(self, cr, uid, ids, dados, context={}):
        #
        # É criação de registro novo
        #
        if len(ids) == 0:
            if 'centrocusto_id' not in dados:
                return
        #
        # É alteração de registro, tá alterando a unidade ou o centro de custo
        #
        elif ('company_id' not in dados) and ('centrocusto_id' not in dados):
            return

        if len(ids):
            contract_obj = self.pool.get('hr.contract').browse(cr, uid, ids[0])

        centrocusto_id = None
        if 'centrocusto_id' in dados:
            centrocusto_id = dados['centrocusto_id']
        elif contract_obj.centrocusto_id:
            centrocusto_id = contract_obj.centrocusto_id.id

        company_id = None
        if 'company_id' in dados:
            company_id = dados['company_id']
        elif contract_obj.company_id:
            company_id = contract_obj.company_id.id

        #
        # Se não tiver a unidade e o centro de custo, não tem o que validar
        #
        if not (centrocusto_id and company_id):
            return

        centrocusto_obj = self.pool.get('finan.centrocusto').browse(cr, uid, centrocusto_id)

        #
        # Se não for rateio, não precisa validar nada
        #
        if centrocusto_obj.tipo == 'C':
            return

        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        if company_obj.parent_id:
            grupo_id = company_obj.parent_id.id
        else:
            grupo_id = company_obj.id

        for rateio_obj in centrocusto_obj.rateio_ids:
            if not rateio_obj.company_id:
                continue

            mensagem = u'Os itens do rateio selecionado não têm todos o mesmo grupo/unidade do contrato'

            if len(ids):
                mensagem += u' do(a) funcionário(a) '
                mensagem += contract_obj.employee_id.nome or ''

            #
            # A unidade do rateio perntece ao mesmo grupo, ou é o próprio grupo?
            #
            if rateio_obj.company_id.parent_id:
                if rateio_obj.company_id.parent_id.id != grupo_id:
                    raise osv.except_osv(u'Erro!', mensagem)

            elif rateio_obj.company_id.id != grupo_id:
                raise osv.except_osv(u'Erro!', mensagem)

    def create(self, cr, uid, dados, context={}):
        self.verifica_rateio(cr, uid, [], dados, context)

        res = super(hr_contract, self).create(cr, uid, dados, context)

        return res

    def write(self, cr, uid, ids, dados, context={}):
        self.verifica_rateio(cr, uid, ids, dados, context)

        res = super(hr_contract, self).write(cr, uid, ids, dados, context)

        return res


hr_contract()



class hr_payslip(osv.Model):
    _name = 'hr.payslip'
    _inherit = 'hr.payslip'

    _columns = {
        'bank_id': fields.related('employee_id', 'bank_id', type='many2one', relation='res.bank', string=u'Banco'),
        'banco_agencia': fields.related('employee_id', 'banco_agencia', type='char', string=u'Agência'),
        'banco_conta': fields.related('employee_id', 'banco_conta', type='char', string=u'Conta'),
    }


hr_payslip()
