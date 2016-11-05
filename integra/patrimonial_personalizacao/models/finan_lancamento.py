# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields


class finan_lancamento(orm.Model):
    _name = 'finan.lancamento'
    _inherit = 'finan.lancamento'

    _columns = {
        'hr_department_id': fields.related('contrato_id', 'hr_department_id', type='many2one', relation='hr.department', string=u'Departamento/posto', store=False),
        'vendedor_id': fields.related('contrato_id', 'vendedor_id', type='many2one', relation='res.users', string=u'Gestor de contas', store=False),
    }

    def personaliza_boleto(self, cr, uid, lancamento_obj, boleto):
        boleto = super(finan_lancamento, self).personaliza_boleto(cr, uid, lancamento_obj, boleto)

        #
        # Patrimonial Segurança de Caçador, Santa Cecília, Lebom Regis
        #
        if lancamento_obj.company_id.id in [41, 45, 70]:
            texto = u'<br/>CÓD. RASTREAMENTO: '
            texto += lancamento_obj.partner_id.rastreamento or u''
            texto += u'<br/>ROTA: '
            if lancamento_obj.partner_id.rota_id:
                texto += lancamento_obj.partner_id.rota_id.codigo or u''
                texto += ' - '
                texto += lancamento_obj.partner_id.rota_id.descricao or u''

            boleto.endereco_cobranca += texto

        return boleto


finan_lancamento()


