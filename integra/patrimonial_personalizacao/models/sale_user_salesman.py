# -*- coding: utf-8 -*-

from osv import osv, fields
import datetime


class sale_reserve_last_salesman(osv.osv):
    _name = 'sale.reserve.last.salesman'
    _columns = {
        'company_id': fields.integer('Company', required=True),
        'user_id': fields.integer('User', required=True),
        'num_available_sales': fields.integer(u'Vendas ainda disponíveis')
    }

    def _get_default_company_id(self, cr, uid, context):
        company_id = self.pool.get('res.company')._company_default_get(
            cr, uid, 'sale.reserve.last.salesman', context=context)
        return company_id

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.reserve.last.salesman', context=c).id,
    }

    _sql_constraints = [
        ('company_id', 'UNIQUE(company_id)',
         'Não é possível criar o rodízio de vendedores 2 vezes para a mesma empresa!')
    ]

sale_reserve_last_salesman()


class crm_lead(osv.osv):
    _inherit = 'crm.lead'

    def _dono_cadastrou(self, cr, uid, ids, field_name, arg, context):
        retorno = {}

        for id in ids:
            lead = self.browse(cr, uid, id)
            retorno[id] = lead.user_id.id == lead.create_uid.id

        return retorno

    _columns = {
        'revenue_sales': fields.float(u'Receita de vendas'),
        'revenue_location': fields.float(u'Receita de locação'),
        'revenue_service': fields.float(u'Receita de serviços'),
        'planned_revenue': fields.float(u'Receita total'),
        #'user_id': fields.many2one('res.users', 'Vendedor',),
        'vendedor': fields.related('user_id', 'name', type='char', string='Vendedor'),
        'create_uid': fields.many2one('res.users', 'Author', select=True, readonly=True),
        'dono_cadastrou': fields.function(_dono_cadastrou, type='boolean', method=True, string='Vendedor cadastrou para si mesmo?')
    }

    _defaults = {
        #'user_id':False,
        'state': 'draft',
        'section_id': 1,
        'revenue_sales': 0,
        'revenue_location': 0,
        'revenue_service': 0,
        'planned_revenue': 0,
    }

    def create(self, cr, uid, data, context=None):
        #
        # Força o estágio para Novo
        #
        data['state'] = 'draft'

        #
        # Se o próprio usuário for um vendedor, ele é o dono do prospecto
        #
        user_obj = self.pool.get('res.users')
        if user_obj.browse(cr, uid, uid).salesman:
            data['user_id'] = uid
            return super(crm_lead, self).create(cr, uid, data, context=context)

        #
        # Empresa ativa no momento
        #
        company_id = self.pool.get('res.company')._company_default_get(
            cr, uid, 'crm.lead', context=context)
        company = self.pool.get('res.company').browse(cr, uid, company_id)

        #
        # Vendedores com permissão na empresa ativa no momento, que estejam ativos
        #
        user_ids = user_obj.search(
            cr, uid, [('salesman', '=', True), ('active', '=', True), ('company_ids', 'in', [company_id])], order='id')
        print('Usuário primeira lista', user_ids)

        #
        # Último vendedor no rodízio de vendedores da empresa ativa no momento
        #'
        last_salesman_obj = self.pool.get('sale.reserve.last.salesman')
        last_salesman_ids = last_salesman_obj.search(
            cr, uid, [('company_id', '=', company_id)])

        if last_salesman_ids:
            last_salesman = last_salesman_obj.browse(
                cr, uid, last_salesman_ids[0])
        else:
            last_salesman_id = last_salesman_obj.create(
                cr, uid, {'company_id': company_id, 'user_id': 0})
            last_salesman = last_salesman_obj.browse(cr, uid, last_salesman_id)

        #
        # Vendedores com permissão na empresa ativa no momento, que estejam ativos
        # e cujo id seja maior do que o do último vendedor
        #
        user_ids = user_obj.search(cr, uid, [('salesman', '=', True), ('active', '=', True), (
            'company_ids', 'in', [company_id]), ('id', '>', last_salesman.user_id)], order='id')
        print('Usuário segunda lista', user_ids)

        #
        # Se na lista de ids não vier nenhum, significa que o próximo tem um id menor do que o último
        #
        if not user_ids:
            user_ids = user_obj.search(cr, uid, [('salesman', '=', True), ('active', '=', True), (
                'company_ids', 'in', [company_id]), ('id', '!=', last_salesman.user_id)], order='id')
            print('Usuário terceira lista', user_ids)

        #
        # O último caso possível, e se só houver 1 vendedor, e ele for o último mesmo?
        #
        if not user_ids:
            user_ids = user_obj.search(cr, uid, [('salesman', '=', True), ('active', '=', True), (
                'company_ids', 'in', [company_id]), ('id', '=', last_salesman.user_id)], order='id')
            print('Usuário quarta lista', user_ids)

        if user_ids:
            next_salesman_id = user_ids[0]
            #
            # Aqui neste ponto sabemos que foi o último vendedor, e quem deveria ser o próximo
            # Mas, se o último vendendor ainda tiver vendas disponíveis, ele é que deve
            # ser o próximo
            #
            # Comentado no dia 14/01/2014, pois o pessoal não tem capacidade mental
            # pra lidar com a reserva de vendas...
            #
            #if last_salesman.num_available_sales > 0:
                #next_salesman_id = last_salesman.user_id


            #
            # O próximo vendedor tem reserva de vendas?
            #
            sale_reserve_obj = self.pool.get('sale.reserve.sale.salesman')
            sale_reserve_ids = sale_reserve_obj.search(
                cr, uid, [('user_id', '=', next_salesman_id), ('num_available_sales', '>', 0)], order='id')

            if sale_reserve_ids:
                #
                # Pega a primeira reserva ainda disponível
                #
                sale_reserve = sale_reserve_obj.browse(
                    cr, uid, sale_reserve_ids[0])

                #
                # Diminui 1 das vendas disponíveis
                #
                sale_reserve.num_available_sales -= 1
                sale_reserve_obj.write(cr, uid, sale_reserve.id, {
                                       'num_available_sales': sale_reserve.num_available_sales})

                #
                # Atribui o prospecto para o vendedor da reserva
                #
                data['user_id'] = sale_reserve.user_id.id

                #
                # Atualiza o controle de que o último vendendor tem reserva, para que ele seja
                # atribuído como próximo vendedor na próxima venda
                #
                last_salesman_obj.write(cr, uid, last_salesman.id, {
                                        'user_id': next_salesman_id, 'num_available_sales': sale_reserve.num_available_sales}, context)

                return super(crm_lead, self).create(cr, uid, data, context=context)

            #
            # Guarda o novo último vendedor
            #
            last_salesman_obj.write(
                cr, uid, last_salesman.id, {'user_id': next_salesman_id}, context)

            #
            # Atribui o prospecto ao vendedor que foi guardado como sendo o último
            #
            data['user_id'] = next_salesman_id
            return super(crm_lead, self).create(cr, uid, data, context=context)

        #
        # Se o código chegou até aqui, não há vendedor para atribuir ao prospecto
        #
        return super(crm_lead, self).create(cr, uid, data, context=context)

    def onchange_revenue_sales(self, cr, uid, ids, revenue_sales=0.0, revenue_location=0.0, revenue_service=0.0):
        res = {}
        res['value'] = {
            'planned_revenue': revenue_sales + revenue_location + revenue_service}
        return res

    def _inclui_reserva_automatica(self, cr, uid, ids, *args):
        reserva = self.pool.get('sale.reserve.sale.salesman')
        for lead in self.browse(cr, uid, ids):
            #
            # Cria uma reserva para cada lead perdido
            #
            reserva_id = reserva.create(cr, uid,
                                        {
                                        'user_id': lead.user_id.id,
                                        'num_reserved_sales': 2,
                                        'num_available_sales': 2
                                        })

    def case_mark_lost(self, cr, uid, ids, *args):
        resposta = super(crm_lead, self).case_mark_lost(cr, uid, ids, *args)

        #
        # Inclui a reserva automaticamente
        #
        self._inclui_reserva_automatica(cr, uid, ids, *args)

        return resposta

    def case_cancel(self, cr, uid, ids, *args):
        resposta = super(crm_lead, self).case_cancel(cr, uid, ids, *args)

        #
        # Inclui a reserva automaticamente
        #
        self._inclui_reserva_automatica(cr, uid, ids, *args)

        return resposta


crm_lead()


class res_users(osv.osv):
    _inherit = 'res.users'

    _columns = {
        'user_leave_date_id': fields.one2many('date.users', 'user_id', u'Data de saída do usuário'),
        'salesman': fields.boolean('Vendedor?'),
        'mobile': fields.char('Celular', size=12),
    }

    def check_user_date(self, cr, uid, context=None):
        cr.execute('select id from res_users')
        res = cr.fetchall()
        user_ids = [id[0] for id in res]
        for user in self.pool.get('res.users').browse(cr, uid, user_ids):
            x = 0
            if user.salesman:
                for each in user.user_leave_date_id:
                    if each.end_date and each.start_date:
                        y1 = int(each.end_date[0:4])
                        m1 = int(each.end_date[5:7])
                        d1 = int(each.end_date[8:10])
                        to_date = datetime.datetime(y1, m1, d1, 00, 00, 00)
                        y2 = int(each.start_date[0:4])
                        m2 = int(each.start_date[5:7])
                        d2 = int(each.start_date[8:10])
                        from_date = datetime.datetime(y2, m2, d2, 00, 00, 00)
                        if datetime.datetime.now() >= from_date and datetime.datetime.now() <= to_date:
                            x = 1
                            break
            if x:
                self.pool.get('res.users').write(
                    cr, uid, user.id, {'active': False})
            else:
                self.pool.get('res.users').write(
                    cr, uid, user.id, {'active': True})
        return True
res_users()


class sale_reserve_sale_salesman(osv.osv):
    _name = 'sale.reserve.sale.salesman'
    _columns = {
        'user_id': fields.many2one('res.users', 'Vendedor'),
        'num_reserved_sales': fields.integer('Vendas reservadas'),
        'num_available_sales': fields.integer(u'Vendas ainda disponíveis')
    }

    #_sql_constraints = [
    #    ('user_name_uniq', 'unique (user_id)', 'The User Name should be unique per record !'),
    #]

    def onchange_num_available_sales(self, cr, uid, ids, num_reserved_sales):

        result = {'num_available_sales': 0}
        if (not num_reserved_sales):
            return {'value': result}
        result['num_available_sales'] = num_reserved_sales
        return {'value': result}

sale_reserve_sale_salesman()


class date_users(osv.osv):
    _name = 'date.users'
    _columns = {
        'user_id': fields.many2one('res.users', 'User Id'),
        'start_date': fields.datetime('Start Date'),
        'end_date': fields.datetime('End Date'),
    }
date_users()


class hr_holidays(osv.osv):
    _inherit = "hr.holidays"

    def holidays_validate(self, cr, uid, ids, context=None):
        self.check_holidays(cr, uid, ids, context=context)
        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        leave_obj = self.browse(cr, uid, ids[0])
        if leave_obj.employee_id.user_id and leave_obj.employee_id.user_id.salesman:
            self.pool.get(
                'date.users').create(cr, uid, {'start_date': leave_obj.date_from,
                                               'end_date': leave_obj.date_to,
                                               'user_id': leave_obj.employee_id.user_id.id
                                               })
        return self.write(cr, uid, ids, {'state': 'validate1', 'manager_id': manager})

    def holidays_validate2(self, cr, uid, ids, context=None):
        self.check_holidays(cr, uid, ids, context=context)
        obj_emp = self.pool.get('hr.employee')
        ids2 = obj_emp.search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        self.write(cr, uid, ids, {'state': 'validate'})
        data_holiday = self.browse(cr, uid, ids)
        holiday_ids = []
        for record in data_holiday:
            if record.holiday_status_id.double_validation:
                holiday_ids.append(record.id)
            if record.holiday_type == 'employee' and record.type == 'remove':
                meeting_obj = self.pool.get('crm.meeting')
                vals = {
                    'name': record.name,
                    'categ_id': record.holiday_status_id.categ_id.id,
                    'duration': record.number_of_days_temp * 8,
                    'description': record.notes,
                    'user_id': record.user_id.id,
                    'date': record.date_from,
                    'end_date': record.date_to,
                    'date_deadline': record.date_to,
                }
                case_id = meeting_obj.create(cr, uid, vals)
                self._create_resource_leave(cr, uid, [record], context=context)
                self.write(cr, uid, ids, {'case_id': case_id})
            elif record.holiday_type == 'category':
                emp_ids = obj_emp.search(
                    cr, uid, [('category_ids', 'child_of', [record.category_id.id])])
                leave_ids = []
                for emp in obj_emp.browse(cr, uid, emp_ids):
                    vals = {
                        'name': record.name,
                        'type': record.type,
                        'holiday_type': 'employee',
                        'holiday_status_id': record.holiday_status_id.id,
                        'date_from': record.date_from,
                        'date_to': record.date_to,
                        'notes': record.notes,
                        'number_of_days_temp': record.number_of_days_temp,
                        'parent_id': record.id,
                        'employee_id': emp.id
                    }
                    leave_ids.append(self.create(cr, uid, vals, context=None))
                wf_service = netsvc.LocalService("workflow")
                for leave_id in leave_ids:
                    wf_service.trg_validate(
                        uid, 'hr.holidays', leave_id, 'confirm', cr)
                    wf_service.trg_validate(
                        uid, 'hr.holidays', leave_id, 'validate', cr)
                    wf_service.trg_validate(
                        uid, 'hr.holidays', leave_id, 'second_validate', cr)

        if holiday_ids:
            self.write(cr, uid, holiday_ids, {'manager_id2': manager})
            leave_obj = data_holiday[0]
            if leave_obj.employee_id.user_id and leave_obj.employee_id.user_id.salesman:
                self.pool.get('date.users').create(cr, uid, {
                                                   'start_date': leave_obj.date_from,
                                                   'end_date': leave_obj.date_to,
                                                   'user_id': leave_obj.employee_id.user_id.id
                                                   })

        return True

hr_holidays()
