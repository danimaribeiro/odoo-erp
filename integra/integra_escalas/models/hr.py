# -*- coding: utf-8 -*-


import pytz
import time
from datetime import datetime, date, timedelta
from osv import osv, fields
#import unicodedata
#import logging
#import addons


class hr_attendance(osv.Model):
    _name = 'hr.attendance'
    _description = 'Attendance'
    _inherit = 'hr.attendance'

    _columns = {
        'escala_item_id': fields.many2one('hr.escala_item', 'Item da Escalas/Turnos', ondelete='cascade'),
    }

    def _altern_si_so(self, cr, uid, ids, context=None):
        #
        # Pára de fazer a verificação dos horários de entrada e saída
        #
        return True

    _constraints = [(_altern_si_so, 'Error: Sign in (resp. Sign out) must follow Sign out (resp. Sign in)', ['action'])]

hr_attendance()


class hr_analytic_timesheet(osv.osv):
    _name = 'hr.analytic.timesheet'
    _inherit = 'hr.analytic.timesheet'

    _columns = {
        'escala_item_id': fields.many2one('hr.escala_item', 'Item da Escalas/Turnos', ondelete='cascade'),
    }


hr_analytic_timesheet()


class account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'

    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Colaborador', required=True),
    }


account_analytic_line()


class hr_escala_departamento(osv.Model):
    _name = 'hr.escala_departamento'
    _description = 'Escalas/turnos do departamento'
    _order = 'department_id, hora_entrada, hora_saida'

    def _nome(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''
        for registro in self.browse(cursor, user_id, ids):
            txt = unicode(registro.department_id.name)
            hora_entrada = unicode(timedelta(hours=registro.hora_entrada))
            hora_saida = unicode(timedelta(hours=registro.hora_saida))
            txt += ' - de ' + hora_entrada + ' a ' + hora_saida

            retorno[registro.id] = txt

        return retorno

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('department_id', '=', texto),
        ]

        return procura

    _columns = {
        'name': fields.function(_nome, string='Escala/Turno', method=True, type='char', fnct_search=_procura_nome),
        'department_id': fields.many2one('hr.department', 'Departamento', required=True),
        'hora_entrada': fields.float('Hora de entrada', required=True),
        'hora_saida': fields.float(u'Hora de saída', required=True, help=u'Caso a hora de saída seja anterior à hora de entrada, o sistema irá considerar que a escala se estende até o dia subsequente.'),
        'product_id': fields.many2one('product.product', 'Serviço e valores'),
    }


hr_escala_departamento()


class hr_department(osv.Model):
    _name = 'hr.department'
    _description = 'Department'
    _inherit = 'hr.department'

    _columns = {
        'escala_departamento_ids': fields.one2many('hr.escala_departamento', 'department_id', 'Escalas/Turnos'),
        'estado_id': fields.many2one('sped.estado', u'Estado', help=u'O estado é necessário para determinar o fuso horário utilizado no departamento'),
        'project_id': fields.many2one('project.project', u'Projeto'),
    }


hr_department()


class hr_escala(osv.Model):
    _name = 'hr.escala'
    _description = 'Definição de escalas e turnos'

    def _nome(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}
        txt = u''
        for registro in self.browse(cursor, user_id, ids):
            txt = unicode(registro.department_id.name)
            txt += ' - ' + time.strftime('%d/%m/%Y', time.strptime(registro.data_referencia, '%Y-%m-%d'))

            retorno[registro.id] = txt

        return retorno

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('department_id', '=', texto),
        ]

        return procura

    _columns = {
        'name': fields.function(_nome, string='Escala/Turno', method=True, type='char', fnct_search=_procura_nome),
        'department_id': fields.many2one('hr.department', 'Departamento', required=True),
        'data_referencia': fields.date(u'Data de referência', required=True),
        'escala_item_ids': fields.one2many('hr.escala_item', 'escala_id', 'Itens da escala'),
    }

    _order = 'department_id, data_referencia'


hr_escala()


class hr_escala_item(osv.Model):
    _name = 'hr.escala_item'
    _description = 'Itens da escala'

    _columns = {
        'escala_id': fields.many2one('hr.escala', 'Escala', required=True, ondelete='cascade'),
        #'department_id': fields.many2one('hr.department', 'Departamento', required=True),
        'employee_id': fields.many2one('hr.employee', 'Colaborador', required=True),
        'escala_departamento_id': fields.many2one('hr.escala_departamento', u'Escala/turno', required=True),
        'data_hora_entrada': fields.datetime(u'Data e hora de entrada'),
        'data_hora_saida': fields.datetime(u'Data e hora de saída'),
        'attendance_entrada_id': fields.many2one('hr.attendance', u'Presença na entrada'),
        'attendance_saida_id': fields.many2one('hr.attendance', u'Presença na saida'),
        'hr_analytic_timesheet_id': fields.many2one('hr.analytic.timesheet', 'Apontamento de horas - RH'),
        'product_id': fields.many2one('product.product', 'Serviço e valores'),

        'preco_contratado': fields.float(u'Preço contratado'),

        'department_id': fields.related('escala_id', 'department_id', type='many2one', relation='hr.department', string='Departamento'),
        'data_referencia': fields.related('escala_id', 'data_referencia', type='date', string=u'Data de referência'),
    }

    _defaults = {
        'preco_contratado': 0,
    }

    def sincroniza_attendance(self, cr, uid, escala_item_id, escala_item_obj=None):
        if escala_item_obj is None:
            escala_item_obj = self.browse(cr, uid, escala_item_id)

        if escala_item_obj.attendance_entrada_id:
            self.pool.get('hr.attendance').unlink(cr, uid, escala_item_obj.attendance_entrada_id.id)

        dados = {
            'action': 'sign_in',
            'employee_id': escala_item_obj.employee_id.id,
            'name': escala_item_obj.data_hora_entrada,
            'escala_item_id': escala_item_obj.id,
        }
        attendance_entrada_id = self.pool.get('hr.attendance').create(cr, uid, dados)

        if escala_item_obj.attendance_saida_id:
            self.pool.get('hr.attendance').unlink(cr, uid, escala_item_obj.attendance_saida_id.id)

        dados = {
            'action': 'sign_out',
            'employee_id': escala_item_obj.employee_id.id,
            'name': escala_item_obj.data_hora_saida,
            'escala_item_id': escala_item_obj.id,
        }
        attendance_saida_id = self.pool.get('hr.attendance').create(cr, uid, dados)

        return attendance_entrada_id, attendance_saida_id

    def sincroniza_datas(self, cr, uid, escala_item_id, escala_item_obj=None):
        if escala_item_obj is None:
            escala_item_obj = self.browse(cr, uid, escala_item_id)

        data_referencia = time.strptime(escala_item_obj.data_referencia, '%Y-%m-%d')
        data_referencia = datetime.fromtimestamp(time.mktime(data_referencia))

        delta_entrada = timedelta(hours=escala_item_obj.escala_departamento_id.hora_entrada)
        delta_saida = timedelta(hours=escala_item_obj.escala_departamento_id.hora_saida)

        #
        # Acrescenta 1 dia quando a hora de entrada for menor do que a de saída
        #
        if escala_item_obj.escala_departamento_id.hora_saida < escala_item_obj.escala_departamento_id.hora_entrada:
            delta_saida += timedelta(days=1)

        escala_item_obj.data_hora_entrada = data_referencia + delta_entrada
        escala_item_obj.data_hora_saida = data_referencia + delta_saida

        #
        # Corrige a diferença de fusos horários
        # para o fuso horário do local de trabalho (departamento)
        #
        if escala_item_obj.escala_id.department_id.estado_id and escala_item_obj.escala_id.department_id.estado_id.fuso_horario:
            fuso_departamento = pytz.timezone(escala_item_obj.escala_id.department_id.estado_id.fuso_horario)
        else:
            fuso_departamento = pytz.timezone('UTC')

        escala_item_obj.data_hora_entrada = fuso_departamento.localize(escala_item_obj.data_hora_entrada)
        escala_item_obj.data_hora_saida = fuso_departamento.localize(escala_item_obj.data_hora_saida)

        UTC = pytz.UTC
        #
        # Convertemos para UTC
        #
        escala_item_obj.data_hora_entrada = UTC.normalize(escala_item_obj.data_hora_entrada)
        escala_item_obj.data_hora_saida = UTC.normalize(escala_item_obj.data_hora_saida)

        return escala_item_obj.data_hora_entrada, escala_item_obj.data_hora_saida

    def sincroniza_apontamento_horas(self, cr, uid, escala_item_id, escala_item_obj=None):
        if escala_item_obj is None:
            escala_item_obj = self.browse(cr, uid, escala_item_id)

        projeto_obj = escala_item_obj.department_id.project_id

        hr_analytic_timesheet_id = False
        if projeto_obj:
            print(escala_item_obj.data_hora_entrada)
            nome = escala_item_obj.escala_departamento_id.name + ' no dia ' + time.strftime('%d/%m/%Y', time.strptime(escala_item_obj.data_referencia, '%Y-%m-%d'))

            data_hora_entrada, data_hora_saida = self.sincroniza_datas(cr, uid, None, escala_item_obj)
            tempo = data_hora_saida - data_hora_entrada
            tempo = tempo.seconds / 60.0 / 60.0

            if escala_item_obj.hr_analytic_timesheet_id:
                self.pool.get('hr.analytic.timesheet').unlink(cr, uid, escala_item_obj.hr_analytic_timesheet_id.id)

            dados = {
                'escala_item_id': escala_item_obj.id,
                'name': nome,
                'employee_id': escala_item_obj.employee_id.id,
                'date': data_hora_entrada,
                #'user_id': escala_item_obj.employee_id.user_id.id,
                'account_id': projeto_obj.analytic_account_id.id,
                'unit_amount': tempo,
                'journal_id': escala_item_obj.employee_id.journal_id.id,
                'product_id': escala_item_obj.product_id.id,
                'amount': tempo * escala_item_obj.product_id.standard_price
            }

            if escala_item_obj.preco_contratado:
                dados['amount'] = tempo * escala_item_obj.preco_contratado
            else:
                dados['amount'] = tempo * escala_item_obj.product_id.standard_price

            hr_analytic_timesheet_id = self.pool.get('hr.analytic.timesheet').create(cr, uid, dados)

        return hr_analytic_timesheet_id

    def create(self, cr, uid, dados, context=None):
        res = super(hr_escala_item, self).create(cr, uid, dados, context)

        self.write(cr, uid, [res], dados, context)

        return res

    def write(self, cr, uid, ids, dados, context=None):
        for id in ids:
            escala_item_obj = self.browse(cr, uid, id)

            dados['data_hora_entrada'], dados['data_hora_saida'] = self.sincroniza_datas(cr, uid, None, escala_item_obj)

            dados['attendance_entrada_id'], dados['attendance_saida_id'] = self.sincroniza_attendance(cr, uid, None, escala_item_obj)

            dados['hr_analytic_timesheet_id'] = self.sincroniza_apontamento_horas(cr, uid, None, escala_item_obj)

        res = super(hr_escala_item, self).write(cr, uid, ids, dados, context)

        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(hr_escala_item, self).unlink(cr, uid, ids, context)

        #if res:
            #attendance_ids = self.pool.get('hr.attendance').search(cr, uid, )
            #self.pool.get('hr.attendance').unlink(cr, uid, attendance_ids, context)

        return res

    def on_change_escala_departamento_id(self, cr, uid, ids, escala_departamento_id):
        res = {}

        if escala_departamento_id:
            escala_departamento_obj = self.pool.get('hr.escala_departamento').browse(cr, uid, escala_departamento_id)
            res['product_id'] = escala_departamento_obj.product_id.id

        return {'value': res}


hr_escala_item()


class hr_employee(osv.osv):
    _inherit = 'hr.employee'

    def ajusta_usuario(self, cr, uid, ids):
        user_pool = self.pool.get('res.users')
        for empregado_obj in self.browse(cr, uid, self.search(cr, uid, [('user_id', '=', False)])):
            if not empregado_obj.user_id:
                user_id = user_pool.search(cr, 1, [('login', '=', 'func_id_' + str(empregado_obj.id) + '_')])

                if user_id:
                    user_id = user_id[0]
                else:
                    #
                    # Cria um usuário
                    #
                    dados = {
                        'name': empregado_obj.name,
                        'login': 'func_id_' + str(empregado_obj.id) + '_',
                    }

                    user_id = user_pool.create(cr, 1, dados)

                empregado_obj.write({'user_id': user_id})

    def create(self, cr, uid, dados, context=None):
        res = super(hr_employee, self).create(cr, uid, dados, context)

        self.ajusta_usuario(cr, uid, [res])

        return res

    def write(self, cr, uid, ids, dados, context=None):
        res = super(hr_employee, self).write(cr, uid, ids, dados, context)
        self.ajusta_usuario(cr, uid, ids)
        return res
