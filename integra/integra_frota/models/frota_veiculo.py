# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields

COMBUSTIVEL = (
    ('FLEX', 'Gasolina/etanol - FLEX'),
    ('GASOLINA', u'Gasolina'),
    ('ETANOL', u'Etanol'),
    ('DIESEL', u'Diesel'),
    ('GLP', 'GLP'),
    ('ELETRICO', 'Eletricidade')
)


class frota_veiculo(osv.Model):
    _name = 'frota.veiculo'
    _description = 'Veículos da frota'
    _order = 'placa asc'
    _rec_name = 'nome'

    def monta_nome(self, cr, uid, id):
        obj = self.browse(cr, uid, id)

        nome = obj.modelo_id.nome + ' / ' + obj.placa

        return nome

    def get_nome(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for id in ids:
            res += [(id, self.monta_nome(cr, uid, id))]

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.get_nome(cr, uid, ids, context=context)
        return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            ('placa', 'ilike', texto),
        ]

        return procura

    _columns = {
        'ativo': fields.boolean(u'Ativo?'),
        'nome': fields.function(_get_nome_funcao, type='char', string=u'Nome', store=True, fnct_search=_procura_nome),
        'res_company_id': fields.many2one('res.company', u'Empresa'),
        'modelo_id': fields.many2one('frota.modelo', u'Marca/modelo', required=False),
        'placa': fields.char(u'Placa', size=32, required=True),
        'sped_estado_id': fields.many2one('sped.estado', u'Estado'),
        'ano': fields.char(u'Ano (fabricação/modelo)', size=9),
        'cor': fields.char(u'Cor', size=20),
        'chassis': fields.char(u'Chassis', size=19),
        'renavam': fields.char(u'RENAVAM', size=11),
        'vencimento_ipva': fields.date(u'Vencimento do IPVA'),
        'vencimento_licenciamento': fields.date(u'Vencimento do licenciamento'),
        'res_partner_id': fields.many2one('res.partner', u'Seguradora'),
        'proprietario_id': fields.many2one('res.partner', u'Proprietário/locadora'),
        'vencimento_seguro': fields.date(u'Vencimento do seguro'),
        'capacidade_tanque': fields.float(u'Capacidade do tanque'),
        'tipo': fields.selection((('VEICULO', u'Veículo'), ('EQUIPAMENTO', u'Equipamento'), ('OUTROS', u'Outros')), u'Tipo'),
        'combustivel': fields.selection(COMBUSTIVEL, u'Combustível'),
        'data_aquisicao': fields.date(u'Data de aquisição'),
        'valor': fields.float(u'Valor do veículo'),
        'odometro': fields.float(u'Última quilometragem'),

        'servico_ids': fields.one2many('frota.veiculo.servico', 'veiculo_id', u'Serviços padrão'),
        #'image': fields.related('model_id', 'image', type="binary", string="Logo"),
        #'image_medium': fields.related('model_id', 'image_medium', type="binary", string="Logo"),
        #'image_small': fields.related('model_id', 'image_small', type="binary", string="Logo"),

        #'vin_sn': fields.char('Chassis Number', size=32, help='Unique number written on the vehicle motor (VIN/SN number)'),
        #'driver': fields.many2one('res.partner', 'Driver', help='Driver of the vehicle'),
        #'model_id': fields.many2one('frota.veiculo.model', 'Model', required=True, help='Model of the vehicle'),
        #'log_fuel': fields.one2many('frota.veiculo.log.fuel', 'vehicle_id', 'Fuel Logs'),
        #'log_services': fields.one2many('frota.veiculo.log.services', 'vehicle_id', 'Services Logs'),
        #'log_contracts': fields.one2many('frota.veiculo.log.contract', 'vehicle_id', 'Contracts'),
        #'acquisition_date': fields.date('Acquisition Date', required=False, help='Date when the vehicle has been bought'),
        #'color': fields.char('Color', size=32, help='Color of the vehicle'),
        #'state': fields.many2one('frota.veiculo.state', 'State', help='Current state of the vehicle', ondelete="set null"),
        #'location': fields.char('Location', size=128, help='Location of the vehicle (garage, ...)'),
        #'seats': fields.integer('Seats Number', help='Number of seats of the vehicle'),
        #'doors': fields.integer('Doors Number', help='Number of doors of the vehicle'),
        #'tag_ids' :fields.many2many('frota.veiculo.tag', 'frota_veiculo_veiculo_tag_rel', 'vehicle_tag_id','tag_id', 'Tags'),
        #'odometer': fields.function(_get_odometer, fnct_inv=_set_odometer, type='float', string='Last Odometer', help='Odometer measure of the vehicle at the moment of this log'),
        #'odometer_unit': fields.selection([('kilometers', 'Kilometers'),('miles','Miles')], 'Odometer Unit', help='Unit of the odometer ',required=True),
        #'transmission': fields.selection([('manual', 'Manual'), ('automatic', 'Automatic')], 'Transmission', help='Transmission Used by the vehicle'),
        #'fuel_type': fields.selection([('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')], 'Fuel Type', help='Fuel Used by the vehicle'),
        #'horsepower': fields.integer('Horsepower'),
        #'horsepower_tax': fields.float('Horsepower Taxation'),
        #'power': fields.integer('Power (kW)', help='Power in kW of the vehicle'),
        #'co2': fields.float('CO2 Emissions', help='CO2 emissions of the vehicle'),
        #'contract_renewal_due_soon': fields.function(_get_contract_reminder_fnc, fnct_search=_search_contract_renewal_due_soon, type="boolean", string='Has Contracts to renew', multi='contract_info'),
        #'contract_renewal_overdue': fields.function(_get_contract_reminder_fnc, fnct_search=_search_get_overdue_contract_reminder, type="boolean", string='Has Contracts Overdued', multi='contract_info'),
        #'contract_renewal_name': fields.function(_get_contract_reminder_fnc, type="text", string='Name of contract to renew soon', multi='contract_info'),
        #'contract_renewal_total': fields.function(_get_contract_reminder_fnc, type="integer", string='Total of contracts due or overdue minus one', multi='contract_info'),
        #'car_value': fields.float('Car Value', help='Value of the bought vehicle'),
    }

    _defaults = {
        'ativo': True,
        #'doors': 5,
        #'odometer_unit': 'kilometers',
        #'state': _get_default_state,
        #'tipo': 'VEICULO',
    }

    #def copy(self, cr, uid, id, default=None, context=None):
        #if not default:
            #default = {}
        #default.update({
            #'log_fuel':[],
            #'log_contracts':[],
            #'log_services':[],
            #'tag_ids':[],
            #'vin_sn':'',
        #})
        #return super(frota_veiculo, self).copy(cr, uid, id, default, context=context)

    #def on_change_model(self, cr, uid, ids, model_id, context=None):
        #if not model_id:
            #return {}
        #model = self.pool.get('frota.veiculo.model').browse(cr, uid, model_id, context=context)
        #return {
            #'value': {
                #'image_medium': model.image,
            #}
        #}

    #def create(self, cr, uid, data, context=None):
        #vehicle_id = super(frota_veiculo, self).create(cr, uid, data, context=context)
        #vehicle = self.browse(cr, uid, vehicle_id, context=context)
        #return vehicle_id

    #def write(self, cr, uid, ids, vals, context=None):
        #"""
        #This function write an entry in the openchatter whenever we change important information
        #on the vehicle like the model, the drive, the state of the vehicle or its license plate
        #"""
        #for vehicle in self.browse(cr, uid, ids, context):
            #changes = []
            #if 'model_id' in vals and vehicle.model_id.id != vals['model_id']:
                #value = self.pool.get('frota.veiculo.model').browse(cr,uid,vals['model_id'],context=context).name
                #oldmodel = vehicle.model_id.name or _('None')
                #changes.append(_("Model: from '%s' to '%s'") %(oldmodel, value))
            #if 'driver' in vals and vehicle.driver.id != vals['driver']:
                #value = self.pool.get('res.partner').browse(cr,uid,vals['driver'],context=context).name
                #olddriver = (vehicle.driver.name) or _('None')
                #changes.append(_("Driver: from '%s' to '%s'") %(olddriver, value))
            #if 'state' in vals and vehicle.state.id != vals['state']:
                #value = self.pool.get('frota.veiculo.state').browse(cr,uid,vals['state'],context=context).name
                #oldstate = vehicle.state.name or _('None')
                #changes.append(_("State: from '%s' to '%s'") %(oldstate, value))
            #if 'license_plate' in vals and vehicle.license_plate != vals['license_plate']:
                #old_license_plate = vehicle.license_plate or _('None')
                #changes.append(_("License Plate: from '%s' to '%s'") %(old_license_plate, vals['license_plate']))

            #if len(changes) > 0:
                #self.message_post(cr, uid, [vehicle.id], body=", ".join(changes), context=context)

        #vehicle_id = super(frota_veiculo,self).write(cr, uid, ids, vals, context)
        #return True

    _sql_constraints = [
        ('placa_unique', 'unique(placa)',
            u'Não é permitido repetir a mesma placa!'),
    ]


frota_veiculo()



class frota_veiculo_servico(osv.Model):
    _name = 'frota.veiculo.servico'
    _description = 'Serviços dos veículos da frota'

    _columns = {
        'veiculo_id': fields.many2one('frota.veiculo', u'Veículo', ondelete='cascade'),
        'servico_id': fields.many2one('frota.servico', u'Serviço', ondelete='restrict'),
        'partner_id': fields.many2one('res.partner', u'Fornecedor padrão', ondelete='restrict'),
        'valor_unitario': fields.float(u'Valor unitário'),
    }

    def replica_valor_unitario(self, cr, uid, ids, context={}):
        for servico_obj in self.pool.get('frota.veiculo.servico').browse(cr, uid, ids):
            sql = """
                update frota_veiculo_servico set valor_unitario = {valor_unitario}
                where partner_id = {partner_id} and servico_id = {servico_id};
            """
            filtro = {
                'valor_unitario': servico_obj.valor_unitario or 0,
                'partner_id': servico_obj.partner_id.id,
                'servico_id': servico_obj.servico_id.id,
            }

            sql = sql.format(**filtro)
            cr.execute(sql)

        return True


frota_veiculo_servico()
