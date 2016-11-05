# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields


class frota_veiculo(osv.Model):
    _name = 'frota.veiculo'
    _inherit = 'frota.veiculo'
    _description = 'Veículos da frota'
    _order = 'placa asc'
    _rec_name = 'nome'

    def monta_nome(self, cr, uid, id):
        obj = self.browse(cr, uid, id)

        nome = obj.partner_id.name + ' / ' + obj.placa + ' / ' + obj.modelo_id.nome

        return nome

    #def get_nome(self, cr, uid, ids, context=None):
        #if not len(ids):
            #return []

        #res = []
        #for id in ids:
            #res += [(id, self.monta_nome(cr, uid, id))]

        #return res

    #def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        #res = self.get_nome(cr, uid, ids, context=context)
        #return dict(res)

    def _procura_nome(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = [
            '|', ('placa', 'like', texto),
            ('partner_id.name', 'ilike', texto)
        ]

        return procura

    _columns = {
        'partner_id': fields.many2one('res.partner', u'Cliente'),
    }

    def onchange_modelo_id(self, cr, uid, ids, modelo_id, context=None):
        if not modelo_id:
            return {}
        modelo_obj = self.pool.get('frota.modelo').browse(cr, uid, modelo_id, context=context)

        return {
            'value': {
                'ano': modelo_obj.ano,
                'combustivel': modelo_obj.combustivel,
            }
        }

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


frota_veiculo()
