# -*- coding: utf-8 -*-


from osv import fields, orm



class hr_variavel_folha(orm.Model):
    _name = 'hr.variavel.folha'
    _description = u'Guarda o cabeçalho dos itens variaveis para o calculo de salário'
    _order = 'data_final_periodo desc,data_inicio_periodo desc'

    _columns = {
       'contract_id': fields.many2one('hr.contract', u'Nº matrícula'),
       'data_inicio_periodo': fields.date(u'Data do início período'),
       'data_final_periodo': fields.date(u'Data do final período'),
       'variavel_folha_item_ids': fields.one2many('hr.variavel.folha.item', 'variavel_folha_id', string=u'Itens variáveis'),
    }

    def buscar_rubricas(self, cr, uid, ids, context=None):
        for variavel_folha_obj in self.browse(cr, uid, ids):
            contrato_obj = variavel_folha_obj.contract_id
            estrutura_salario_obj = contrato_obj.struct_id

            for regra_salario_obj in estrutura_salario_obj.rule_ids:
                if regra_salario_obj.manual:
                    dados = {
                        'variavel_folha_id': variavel_folha_obj.id,
                        'salary_rule_id': regra_salario_obj.id,
                        'valor_da_regra': 0,
                    }
                    self.pool.get('hr.variavel.folha.item').create(cr, uid, dados)


hr_variavel_folha()


class hr_variavel_folha_item(orm.Model):
    _name = 'hr.variavel.folha.item'
    _description = u'Guarda os itens variaveis do calculo de salário'
    _order = 'variavel_folha_id, sequence'

    _columns = {
       'variavel_folha_id': fields.many2one('hr.variavel.folha', u'Nº matrícula'),
       'valor_da_regra': fields.float(u'Valor da Lançamento (Horas / Valor / Qtde)', digits=(8, 2)),
       'salary_rule_id': fields.many2one('hr.salary.rule', u'Rubricas para Lançamento'),
       'sequence': fields.related('salary_rule_id', 'sequence', type='integer', string=u'Sequência', store=True),
       'code': fields.related('salary_rule_id', 'code', type='char', string=u'Código'),
    }


hr_variavel_folha_item()