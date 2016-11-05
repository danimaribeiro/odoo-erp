# -*- coding: utf-8 -*-


from osv import fields, osv


class project_project(osv.Model):
    _name = 'project.project'
    _description = "Project"
    #_inherit = 'project.project'
    #_inherits = {'account.analytic.account': "analytic_account_id"}
    #_inherit = 'account.analytic.account'
    #_parent_name = 'parent_id'
    #_parent_store = True
    _parent_order = 'nome_completo'
    _order = 'nome_completo'
    _rec_name = 'nome_completo'

    def monta_nome(self, cr, uid, id):
        conta_obj = self.pool.get('project.project').browse(cr, uid, id)

        print(conta_obj)
        #print(conta_obj.name)
        nome = getattr(conta_obj, 'name', '')

        if getattr(conta_obj, 'parent_id', False):
            nome = self.pool.get('project.project').monta_nome(cr, uid, conta_obj.parent_id.id) + u' / ' + nome

        return nome

    def nome_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []

        res = []
        for obj in self.pool.get('project.project').browse(cr, 1, ids):
            res.append([obj.id, self.pool.get('project.project').monta_nome(cr, 1, obj.id)])

        return res

    def _get_nome_funcao(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.pool.get('project.project').nome_get(cr, uid, ids, context=context)
        return dict(res)

    #def name_get(self, cr, uid, ids, context=None):
        #if not ids:
            #return []
        #res = []
        #for account in self.browse(cr, uid, ids, context=context):
            #data = []
            #acc = account
            #while acc:
                #data.insert(0, acc.name or '')
                #acc = acc.parent_id
            #data = ' / '.join(data)
            #res.append((account.id, data))
        #return res

    #def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        #if user == 1:
            #return super(project_project, self).search(cr, user, args, offset=offset, limit=limit, order=order, context=context, count=count)
        #if context and context.get('user_preference'):
                #cr.execute("""SELECT project.id FROM project_project project
                           #LEFT JOIN account_analytic_account account ON account.id = project.analytic_account_id
                           #LEFT JOIN project_user_rel rel ON rel.project_id = project.analytic_account_id
                           #WHERE (account.user_id = %s or rel.uid = %s)"""%(user, user))
                #return [(r[0]) for r in cr.fetchall()]
        #return super(project_project, self).search(cr, user, args, offset=offset, limit=limit, order=order,
            #context=context, count=count)

    #def _complete_name(self, cr, uid, ids, name, args, context=None):
        #res = {}
        #for m in self.browse(cr, uid, ids, context=context):
            #res[m.id] = (m.parent_id and (m.parent_id.name + '/') or '') + m.name
        #return res

    def onchange_partner_id(self, cr, uid, ids, part=False, context=None):
        partner_obj = self.pool.get('res.partner')
        if not part:
            return {'value':{'contact_id': False}}
        addr = partner_obj.address_get(cr, uid, [part], ['contact'])
        val = {'contact_id': addr['contact']}
        if 'pricelist_id' in self.fields_get(cr, uid, context=context):
            pricelist = partner_obj.read(cr, uid, part, ['property_product_pricelist'], context=context)
            pricelist_id = pricelist.get('property_product_pricelist', False) and pricelist.get('property_product_pricelist')[0] or False
            val['pricelist_id'] = pricelist_id
        return {'value': val}

    def _get_projects_from_tasks(self, cr, uid, task_ids, context=None):
        tasks = self.pool.get('project.task').browse(cr, uid, task_ids, context=context)
        project_ids = [task.project_id.id for task in tasks if task.project_id]
        return self.pool.get('project.project')._get_project_and_parents(cr, uid, project_ids, context)

    def _get_project_and_parents(self, cr, uid, ids, context=None):
        """ return the project ids and all their parent projects """
        res = set(ids)
        while ids:
            cr.execute("""
                SELECT DISTINCT parent.id
                FROM project_project project, project_project parent
                WHERE 
                    project.parent_id = parent.id
                    and project.id IN %s
                """, (tuple(ids),))
            ids = [t[0] for t in cr.fetchall()]
            res.update(ids)
        return list(res)

    #def _get_project_and_children(self, cr, uid, ids, context=None):
        #""" retrieve all children projects of project ids;
            #return a dictionary mapping each project to its parent project (or None)
        #"""
        #res = dict.fromkeys(ids, None)
        #while ids:
            #cr.execute("""
                #SELECT project.id, parent.id
                #FROM project_project project, project_project parent
                #WHERE parent.id IN %s
                #""", (tuple(ids),))
            #dic = dict(cr.fetchall())
            #res.update(dic)
            #ids = dic.keys()
        #return res

    def _progress_rate(self, cr, uid, ids, names, arg, context=None):
        #child_parent = self._get_project_and_children(cr, uid, ids, context)
        ## compute planned_hours, total_hours, effective_hours specific to each project
        #cr.execute("""
            #SELECT project_id, COALESCE(SUM(planned_hours), 0.0),
                #COALESCE(SUM(total_hours), 0.0), COALESCE(SUM(effective_hours), 0.0)
            #FROM project_task WHERE project_id IN %s AND state <> 'cancelled'
            #GROUP BY project_id
            #""", (tuple(child_parent.keys()),))
        ## aggregate results into res
        #res = dict([(id, {'planned_hours':0.0,'total_hours':0.0,'effective_hours':0.0}) for id in ids])
        #for id, planned, total, effective in cr.fetchall():
            ## add the values specific to id to all parent projects of id in the result
            #while id:
                #if id in ids:
                    #res[id]['planned_hours'] += planned
                    #res[id]['total_hours'] += total
                    #res[id]['effective_hours'] += effective
                #id = child_parent[id]
        ## compute progress rates
        
        res = {}
        for id in ids:
            res[id] = {}
            res[id]['total_hours'] = '0'
            res[id]['planned_hours'] = '0'
            res[id]['effective_hours'] = '0'
            res[id]['progress_rate'] = '0'

        return res

    def unlink(self, cr, uid, ids, *args, **kwargs):
        for proj in self.browse(cr, uid, ids):
            if proj.tasks:
                raise osv.except_osv(_('Operation Not Permitted !'), _('You cannot delete a project containing tasks. I suggest you to desactivate it.'))
        return super(project_project, self).unlink(cr, uid, ids, *args, **kwargs)


    _columns = {
        'parent_id': fields.many2one('project.project', u'Projeto pai', select=True, ondelete='cascade'),
        #'complete_name': fields.function(_complete_name, string="Project Name", type='char', size=250),
        'name': fields.char(u'Projeto', size=128, select=True),
        
        'nome_completo': fields.function(_get_nome_funcao, type='char', string=u'Projeto', store=True, select=True),
        'complete_name': fields.function(_get_nome_funcao, type='char', string=u'Projeto', store=True, select=True),
        
        'description': fields.text('Description'),
        'currency_id': fields.many2one('res.currency', u'Moeda'),
        
        'warn_manager': fields.boolean('Avisar gerente'),
        'warn_customer': fields.boolean('Avisar cliente'),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the project without removing it."),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of Projects."),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', ondelete="cascade", required=False),
        #'priority': fields.integer('Sequence', help="Gives the sequence order when displaying the list of projects"),
        #'warn_manager': fields.boolean('Warn Manager', help="If you check this field, the project manager will receive an email each time a task is completed by his team.", states={'close':[('readonly',True)], 'cancelled':[('readonly',True)]}),

        'members': fields.many2many('res.users', 'project_user_rel', 'project_id', 'uid', 'Project Members',
            help="Project's members are users who can have an access to the tasks related to this project.", states={'close':[('readonly',True)], 'cancelled':[('readonly',True)]}),
        'tasks': fields.one2many('project.task', 'project_id', "Project tasks"),
        #'planned_hours': fields.function(_progress_rate, multi="progress", string='Planned Time', help="Sum of planned hours of all tasks related to this project and its child projects.",
            #store = {
                #'project.project': (_get_project_and_parents, ['tasks', 'parent_id', 'child_ids'], 10),
                #'project.task': (_get_projects_from_tasks, ['planned_hours', 'remaining_hours', 'work_ids', 'state'], 20),
            #}),
        #'effective_hours': fields.function(_progress_rate, multi="progress", string='Time Spent', help="Sum of spent hours of all tasks related to this project and its child projects.",
            #store = {
                #'project.project': (_get_project_and_parents, ['tasks', 'parent_id', 'child_ids'], 10),
                #'project.task': (_get_projects_from_tasks, ['planned_hours', 'remaining_hours', 'work_ids', 'state'], 20),
            #}),
        #'total_hours': fields.function(_progress_rate, string='Total Time', store=True, type='float'),
        #'progress_rate': fields.float(u'Progresso'),
        #'planned_hours': fields.float(u'Progresso'),
        #'effective_hours': fields.float(u'Progresso'),
        #'total_hours': fields.float(u'Progresso'),
        #'progress_rate': fields.function(_progress_rate, multi="progress", string='Progress', type='float', group_operator="avg", help="Percent of tasks closed according to the total of tasks todo.",
            #store = {
                #'project.project': (_get_project_and_parents, ['tasks', 'parent_id', 'child_ids'], 10),
                #'project.task': (_get_projects_from_tasks, ['planned_hours', 'remaining_hours', 'work_ids', 'state'], 20),
            #}),
            
        'effective_hours': fields.float(u'Horas totais'),
        'planned_hours': fields.float(u'Horas totais'),
        'progress_rate': fields.float(u'Horas totais'),
        'total_hours': fields.float(u'Horas totais'),
        'progress': fields.float(u'Progresso'),
        'delay_hours': fields.float(u'Horas restantes'),
            
        #'resource_calendar_id': fields.many2one('resource.calendar', 'Working Time', help="Timetable working hours to adjust the gantt diagram report", states={'close':[('readonly',True)]} ),
        #'warn_customer': fields.boolean('Warn Partner', help="If you check this, the user will have a popup when closing a task that propose a message to send by email to the customer.", states={'close':[('readonly',True)], 'cancelled':[('readonly',True)]}),
        #'warn_header': fields.text('Mail Header', help="Header added at the beginning of the email for the warning message sent to the customer when a task is closed.", states={'close':[('readonly',True)], 'cancelled':[('readonly',True)]}),
        #'warn_footer': fields.text('Mail Footer', help="Footer added at the beginning of the email for the warning message sent to the customer when a task is closed.", states={'close':[('readonly',True)], 'cancelled':[('readonly',True)]}),
        #'type_ids': fields.many2many('project.task.type', 'project_task_type_rel', 'project_id', 'type_id', 'Tasks Stages', states={'close':[('readonly',True)], 'cancelled':[('readonly',True)]}),
        
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'contact_id': fields.many2one('res.partner.address', 'Contact'),
        'user_id': fields.many2one('res.users', 'Account Manager'),
        'date_start': fields.date('Date Start'),
        'date': fields.date('Date End', select=True),
        'company_id': fields.many2one('res.company', 'Company', required=False), #not required because we want to allow different companies to use the same chart of account, except for leaf accounts.
        'state': fields.selection([('template', 'Template'),('draft','New'),('open','Open'), ('pending','Pending'),('cancelled', 'Cancelled'),('close','Closed')], 'State', required=False,
                                  help='* When an account is created its in \'Draft\' state.\
                                  \n* If any associated partner is there, it can be in \'Open\' state.\
                                  \n* If any pending balance is there it can be in \'Pending\'. \
                                  \n* And finally when all the transactions are over, it can be in \'Close\' state. \
                                  \n* The project can be in either if the states \'Template\' and \'Running\'.\n If it is template then we can make projects based on the template projects. If its in \'Running\' state it is a normal project.\
                                 \n If it is to be reviewed then the state is \'Pending\'.\n When the project is completed the state is set to \'Done\'.'),

        #
        # Campos do project_issue
        #
        #'project_escalation_id' : fields.many2one('project.project','Project Escalation', help='If any issue is escalated from the current Project, it will be listed under the project selected here.', states={'close':[('readonly',True)], 'cancelled':[('readonly',True)]}),
        #'reply_to': fields.char('Reply-To Email Address', size=256),

        #
        # Campos do project_message
        #
        #'message_ids': fields.one2many('project.messages', 'project_id', 'Messages'),
    }

    #def _check_escalation(self, cr, uid, ids, context=None):
         #project_obj = self.browse(cr, uid, ids[0], context=context)
         #if project_obj.project_escalation_id:
             #if project_obj.project_escalation_id.id == project_obj.id:
                 #return False
         #return True

    def _get_type_common(self, cr, uid, context):
        ids = self.pool.get('project.task.type').search(cr, uid, [('project_default','=',1)], context=context)
        return ids

    _defaults = {
        'active': True,
        'state': 'open',
        #'priority': 1,
        #'sequence': 10,
        #'type_ids': _get_type_common
    }

    # TODO: Why not using a SQL contraints ?
    def _check_dates(self, cr, uid, ids, context=None):
        #for leave in self.read(cr, uid, ids, ['date_start', 'date'], context=context):
            #if leave['date_start'] and leave['date']:
                #if leave['date_start'] > leave['date']:
                    #return False
        return True

    _constraints = [
        (_check_dates, 'Error! project start-date must be lower then project end-date.', ['date_start', 'date']),
        #(_check_escalation, 'Error! You cannot assign escalation to the same project!', ['project_escalation_id'])
    ]

    def set_template(self, cr, uid, ids, context=None):
        res = self.setActive(cr, uid, ids, value=False, context=context)
        return res

    def set_done(self, cr, uid, ids, context=None):
        task_obj = self.pool.get('project.task')
        task_ids = task_obj.search(cr, uid, [('project_id', 'in', ids), ('state', 'not in', ('cancelled', 'done'))])
        task_obj.write(cr, uid, task_ids, {'state': 'done', 'date_end':time.strftime('%Y-%m-%d %H:%M:%S'), 'remaining_hours': 0.0})
        self.write(cr, uid, ids, {'state':'close'}, context=context)
        for (id, name) in self.name_get(cr, uid, ids):
            message = _("The project '%s' has been closed.") % name
            self.log(cr, uid, id, message)
        return True

    def set_cancel(self, cr, uid, ids, context=None):
        task_obj = self.pool.get('project.task')
        task_ids = task_obj.search(cr, uid, [('project_id', 'in', ids), ('state', '!=', 'done')])
        task_obj.write(cr, uid, task_ids, {'state': 'cancelled', 'date_end':time.strftime('%Y-%m-%d %H:%M:%S'), 'remaining_hours': 0.0})
        self.write(cr, uid, ids, {'state':'cancelled'}, context=context)
        return True

    def set_pending(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'pending'}, context=context)
        return True

    def set_open(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'open'}, context=context)
        return True

    def reset_project(self, cr, uid, ids, context=None):
        res = self.setActive(cr, uid, ids, value=True, context=context)
        for (id, name) in self.name_get(cr, uid, ids):
            message = _("The project '%s' has been opened.") % name
            self.log(cr, uid, id, message)
        return res

    def map_tasks(self, cr, uid, old_project_id, new_project_id, context=None):
        """ copy and map tasks from old to new project """
        if context is None:
            context = {}
        map_task_id = {}
        task_obj = self.pool.get('project.task')
        proj = self.browse(cr, uid, old_project_id, context=context)
        for task in proj.tasks:
            map_task_id[task.id] =  task_obj.copy(cr, uid, task.id, {}, context=context)
        self.write(cr, uid, new_project_id, {'tasks':[(6,0, map_task_id.values())]})
        task_obj.duplicate_task(cr, uid, map_task_id, context=context)
        return True

    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}

        default = default or {}
        context['active_test'] = False
        default['state'] = 'open'
        default['code'] = False
        default['line_ids'] = []
        default['tasks'] = []
        proj = self.browse(cr, uid, id, context=context)
        if not default.get('name', False):
            default['name'] = proj.name + _(' (copy)')

        res = super(project_project, self).copy(cr, uid, id, default, context)
        self.map_tasks(cr,uid,id,res,context)
        return res

    def duplicate_template(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data_obj = self.pool.get('ir.model.data')
        result = []
        for proj in self.browse(cr, uid, ids, context=context):
            parent_id = context.get('parent_id', False)
            context.update({'analytic_project_copy': True})
            new_date_start = time.strftime('%Y-%m-%d')
            new_date_end = False
            if proj.date_start and proj.date:
                start_date = date(*time.strptime(proj.date_start,'%Y-%m-%d')[:3])
                end_date = date(*time.strptime(proj.date,'%Y-%m-%d')[:3])
                new_date_end = (datetime(*time.strptime(new_date_start,'%Y-%m-%d')[:3])+(end_date-start_date)).strftime('%Y-%m-%d')
            context.update({'copy':True})
            new_id = self.copy(cr, uid, proj.id, default = {
                                    'name': proj.name +_(' (copy)'),
                                    'state':'open',
                                    'date_start':new_date_start,
                                    'date':new_date_end,
                                    'parent_id':parent_id}, context=context)
            result.append(new_id)

            child_ids = self.search(cr, uid, [('parent_id','=', proj.analytic_account_id.id)], context=context)
            parent_id = self.read(cr, uid, new_id, ['analytic_account_id'])['analytic_account_id'][0]
            if child_ids:
                self.duplicate_template(cr, uid, child_ids, context={'parent_id': parent_id})

        if result and len(result):
            res_id = result[0]
            form_view_id = data_obj._get_id(cr, uid, 'project', 'edit_project')
            form_view = data_obj.read(cr, uid, form_view_id, ['res_id'])
            tree_view_id = data_obj._get_id(cr, uid, 'project', 'view_project')
            tree_view = data_obj.read(cr, uid, tree_view_id, ['res_id'])
            search_view_id = data_obj._get_id(cr, uid, 'project', 'view_project_project_filter')
            search_view = data_obj.read(cr, uid, search_view_id, ['res_id'])
            return {
                'name': _('Projects'),
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'project.project',
                'view_id': False,
                'res_id': res_id,
                'views': [(form_view['res_id'],'form'),(tree_view['res_id'],'tree')],
                'type': 'ir.actions.act_window',
                'search_view_id': search_view['res_id'],
                'nodestroy': True
            }

    # set active value for a project, its sub projects and its tasks
    def setActive(self, cr, uid, ids, value=True, context=None):
        task_obj = self.pool.get('project.task')
        for proj in self.browse(cr, uid, ids, context=None):
            self.write(cr, uid, [proj.id], {'state': value and 'open' or 'template'}, context)
            cr.execute('select id from project_task where project_id=%s', (proj.id,))
            tasks_id = [x[0] for x in cr.fetchall()]
            if tasks_id:
                task_obj.write(cr, uid, tasks_id, {'active': value}, context=context)
            child_ids = self.search(cr, uid, [('parent_id','=', proj.analytic_account_id.id)])
            if child_ids:
                self.setActive(cr, uid, child_ids, value, context=None)
        return True

    ###def _schedule_header(self, cr, uid, ids, force_members=True, context=None):
        ###context = context or {}
        ###if type(ids) in (long, int,):
            ###ids = [ids]
        ###projects = self.browse(cr, uid, ids, context=context)

        ###for project in projects:
            ###if (not project.members) and force_members:
                ###raise osv.except_osv(_('Warning !'),_("You must assign members on the project '%s' !") % (project.name,))

        ###resource_pool = self.pool.get('resource.resource')

        ###result = "from openerp.addons.resource.faces import *\n"
        ###result += "import datetime\n"
        ###for project in self.browse(cr, uid, ids, context=context):
            ###u_ids = [i.id for i in project.members]
            ###if project.user_id and (project.user_id.id not in u_ids):
                ###u_ids.append(project.user_id.id)
            ###for task in project.tasks:
                ###if task.state in ('done','cancelled'):
                    ###continue
                ###if task.user_id and (task.user_id.id not in u_ids):
                    ###u_ids.append(task.user_id.id)
            ###calendar_id = project.resource_calendar_id and project.resource_calendar_id.id or False
            ###resource_objs = resource_pool.generate_resources(cr, uid, u_ids, calendar_id, context=context)
            ###for key, vals in resource_objs.items():
                ###result +='''
###class User_%s(Resource):
    ###efficiency = %s
###''' % (key,  vals.get('efficiency', False))

        ###result += '''
###def Project():
        ###'''
        ###return result

    ###def _schedule_project(self, cr, uid, project, context=None):
        ###resource_pool = self.pool.get('resource.resource')
        ###calendar_id = project.resource_calendar_id and project.resource_calendar_id.id or False
        ###working_days = resource_pool.compute_working_calendar(cr, uid, calendar_id, context=context)
        #### TODO: check if we need working_..., default values are ok.
        ###puids = [x.id for x in project.members]
        ###if project.user_id:
            ###puids.append(project.user_id.id)
        ###result = """
  ###def Project_%d():
    ###start = \'%s\'
    ###working_days = %s
    ###resource = %s
###"""       % (
            ###project.id,
            ###project.date_start, working_days,
            ###'|'.join(['User_'+str(x) for x in puids])
        ###)
        ###vacation = calendar_id and tuple(resource_pool.compute_vacation(cr, uid, calendar_id, context=context)) or False
        ###if vacation:
            ###result+= """
    ###vacation = %s
###""" %   ( vacation, )
        ###return result

    #TODO: DO Resource allocation and compute availability
    ##def compute_allocation(self, rc, uid, ids, start_date, end_date, context=None):
        ##if context ==  None:
            ##context = {}
        ##allocation = {}
        ##return allocation

    ##def schedule_tasks(self, cr, uid, ids, context=None):
        ##context = context or {}
        ##if type(ids) in (long, int,):
            ##ids = [ids]
        ##projects = self.browse(cr, uid, ids, context=context)
        ##result = self._schedule_header(cr, uid, ids, False, context=context)
        ##for project in projects:
            ##result += self._schedule_project(cr, uid, project, context=context)
            ##result += self.pool.get('project.task')._generate_task(cr, uid, project.tasks, ident=4, context=context)

        ##local_dict = {}
        ##exec result in local_dict
        ##projects_gantt = Task.BalancedProject(local_dict['Project'])

        ##for project in projects:
            ##project_gantt = getattr(projects_gantt, 'Project_%d' % (project.id,))
            ##for task in project.tasks:
                ##if task.state in ('done','cancelled'):
                    ##continue

                ##p = getattr(project_gantt, 'Task_%d' % (task.id,))

                ##self.pool.get('project.task').write(cr, uid, [task.id], {
                    ##'date_start': p.start.strftime('%Y-%m-%d %H:%M:%S'),
                    ##'date_end': p.end.strftime('%Y-%m-%d %H:%M:%S')
                ##}, context=context)
                ##if (not task.user_id) and (p.booked_resource):
                    ##self.pool.get('project.task').write(cr, uid, [task.id], {
                        ##'user_id': int(p.booked_resource[0].name[5:]),
                    ##}, context=context)
        ##return True


project_project()
