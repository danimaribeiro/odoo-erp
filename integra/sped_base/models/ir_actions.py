# -*- coding: utf-8 -*-

from osv import fields,osv


class act_window(osv.osv):
    _name = 'ir.actions.act_window'
    _inherit = 'ir.actions.act_window'

    _columns = {
        #'name': fields.char('Action Name', size=64, translate=True),
        #'type': fields.char('Action Type', size=32, required=True),
        #'view_id': fields.many2one('ir.ui.view', 'View Ref.', ondelete='cascade'),
        'domain': fields.char('Domain Value', size=2048,
            help="Optional domain filtering of the destination data, as a Python expression"),
        'context': fields.char('Context Value', size=2048, required=True,
            help="Context dictionary as Python expression, empty by default (Default: {})"),
        #'res_model': fields.char('Object', size=64, required=True,
            #help="Model name of the object to open in the view window"),
        #'src_model': fields.char('Source Object', size=64,
            #help="Optional model name of the objects on which this action should be visible"),
        #'target': fields.selection([('current','Current Window'),('new','New Window'),('inline','Inline')], 'Target Window'),
        #'view_type': fields.selection((('tree','Tree'),('form','Form')), string='View Type', required=True,
            #help="View type: set to 'tree' for a hierarchical tree view, or 'form' for other views"),
        #'view_mode': fields.char('View Mode', size=250, required=True,
            #help="Comma-separated list of allowed view modes, such as 'form', 'tree', 'calendar', etc. (Default: tree,form)"),
        #'usage': fields.char('Action Usage', size=32,
            #help="Used to filter menu and home actions from the user form."),
        #'view_ids': fields.one2many('ir.actions.act_window.view', 'act_window_id', 'Views'),
        #'views': fields.function(_views_get_fnc, type='binary', string='Views',
               #help="This function field computes the ordered list of views that should be enabled " \
                    #"when displaying the result of an action, federating view mode, views and " \
                    #"reference view. The result is returned as an ordered list of pairs (view_id,view_mode)."),
        #'limit': fields.integer('Limit', help='Default limit for the list view'),
        #'auto_refresh': fields.integer('Auto-Refresh',
            #help='Add an auto-refresh on the view'),
        #'groups_id': fields.many2many('res.groups', 'ir_act_window_group_rel',
            #'act_id', 'gid', 'Groups'),
        #'search_view_id': fields.many2one('ir.ui.view', 'Search View Ref.'),
        #'filter': fields.boolean('Filter'),
        #'auto_search':fields.boolean('Auto Search'),
        #'search_view' : fields.function(_search_view, type='text', string='Search View'),
        #'help': fields.text('Action description',
            #help='Optional help text for the users with a description of the target view, such as its usage and purpose.',
            #translate=True),
        #'display_menu_tip':fields.function(_get_help_status, type='boolean', string='Display Menu Tips',
            #help='It gives the status if the tip has to be displayed or not when a user executes an action'),
        #'multi': fields.boolean('Action on Multiple Doc.', help="If set to true, the action will not be displayed on the right toolbar of a form view"),
    }


act_window()


class actions_server(osv.osv):
    _name = 'ir.actions.server'
    _inherit = 'ir.actions.server'

    _columns = {
        #'name': fields.char('Action Name', required=True, size=64, translate=True),
        'condition' : fields.char('Condition', size=2048, required=True,
                                  help="Condition that is tested before the action is executed, "
                                       "and prevent execution if it is not verified.\n"
                                       "Example: object.list_price > 5000\n"
                                       "It is a Python expression that can use the following values:\n"
                                       " - self: ORM model of the record on which the action is triggered\n"
                                       " - object or obj: browse_record of the record on which the action is triggered\n"
                                       " - pool: ORM model pool (i.e. self.pool)\n"
                                       " - time: Python time module\n"
                                       " - cr: database cursor\n"
                                       " - uid: current user id\n"
                                       " - context: current context"),
        #'state': fields.selection([
            #('client_action','Client Action'),
            #('dummy','Dummy'),
            #('loop','Iteration'),
            #('code','Python Code'),
            #('trigger','Trigger'),
            #('email','Email'),
            #('sms','SMS'),
            #('object_create','Create Object'),
            #('object_copy','Copy Object'),
            #('object_write','Write Object'),
            #('other','Multi Actions'),
        #], 'Action Type', required=True, size=32, help="Type of the Action that is to be executed"),
        #'code':fields.text('Python Code', help="Python code to be executed if condition is met.\n"
                                               #"It is a Python block that can use the same values as for the condition field"),
        #'sequence': fields.integer('Sequence', help="Important when you deal with multiple actions, the execution order will be decided based on this, low number is higher priority."),
        #'model_id': fields.many2one('ir.model', 'Object', required=True, help="Select the object on which the action will work (read, write, create)."),
        #'action_id': fields.many2one('ir.actions.actions', 'Client Action', help="Select the Action Window, Report, Wizard to be executed."),
        #'trigger_name': fields.selection(_select_signals, string='Trigger Signal', size=128, help="The workflow signal to trigger"),
        #'wkf_model_id': fields.many2one('ir.model', 'Target Object', help="The object that should receive the workflow signal (must have an associated workflow)"),
        #'trigger_obj_id': fields.many2one('ir.model.fields','Relation Field', help="The field on the current object that links to the target object record (must be a many2one, or an integer field with the record ID)"),
        #'email': fields.char('Email Address', size=512, help="Expression that returns the email address to send to. Can be based on the same values as for the condition field.\n"
                                                             #"Example: object.invoice_address_id.email, or 'me@example.com'"),
        #'subject': fields.char('Subject', size=1024, translate=True, help="Email subject, may contain expressions enclosed in double brackets based on the same values as those "
                                                                          #"available in the condition field, e.g. `Hello [[ object.partner_id.name ]]`"),
        #'message': fields.text('Message', translate=True, help="Email contents, may contain expressions enclosed in double brackets based on the same values as those "
                                                                          #"available in the condition field, e.g. `Dear [[ object.partner_id.name ]]`"),
        #'mobile': fields.char('Mobile No', size=512, help="Provides fields that be used to fetch the mobile number, e.g. you select the invoice, then `object.invoice_address_id.mobile` is the field which gives the correct mobile number"),
        #'sms': fields.char('SMS', size=160, translate=True),
        #'child_ids': fields.many2many('ir.actions.server', 'rel_server_actions', 'server_id', 'action_id', 'Other Actions'),
        #'usage': fields.char('Action Usage', size=32),
        #'type': fields.char('Action Type', size=32, required=True),
        #'srcmodel_id': fields.many2one('ir.model', 'Model', help="Object in which you want to create / write the object. If it is empty then refer to the Object field."),
        #'fields_lines': fields.one2many('ir.server.object.lines', 'server_id', 'Field Mappings.'),
        #'record_id':fields.many2one('ir.model.fields', 'Create Id', help="Provide the field name where the record id is stored after the create operations. If it is empty, you can not track the new record."),
        #'write_id':fields.char('Write Id', size=256, help="Provide the field name that the record id refers to for the write operation. If it is empty it will refer to the active id of the object."),
        #'loop_action':fields.many2one('ir.actions.server', 'Loop Action', help="Select the action that will be executed. Loop action will not be avaliable inside loop."),
        #'expression':fields.char('Loop Expression', size=512, help="Enter the field/expression that will return the list. E.g. select the sale order in Object, and you can have loop on the sales order line. Expression = `object.order_line`."),
        #'copy_object': fields.reference('Copy Of', selection=_select_objects, size=256),
    }

actions_server()
