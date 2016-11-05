# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from osv import orm, fields, osv


class finan_centrocusto(orm.Model):
    _name = 'finan.centrocusto'
    _inherit = 'finan.centrocusto'
    
    _columns = {
        'hr_department_id': fields.many2one('hr.department', u'Departamento/posto', ondelete='set null'),
    }

    def ajusta_departamentos(self, cr, uid, ids, context={}):
        #dep_ids = self.pool.get('hr.department').search(cr, uid, [('parent_id', '!=', False)], order='parent_id, id')
        
        #self.pool.get('hr.department').ajusta_centrocusto(cr, uid, dep_ids)
        
        return True


finan_centrocusto()


class hr_department(orm.Model):
    _name = 'hr.department'
    _inherit = 'hr.department'

    _columns = {
        'finan_centrocusto_id': fields.many2one('finan.centrocusto', u'Centro de custo', ondelete='set null'),
    }
    
    def ajusta_centrocusto(self, cr, uid, ids):
        #cc_pool = self.pool.get('finan.centrocusto')
        #cc_raiz_id = cc_pool.search(cr, uid, [('codigo', '=', '99')])[0]
        
        #for departamento_obj in self.browse(cr, uid, ids):
            #if departamento_obj.parent_id and (not departamento_obj.finan_centrocusto_id):
                #self.ajusta_centrocusto(cr, uid, [departamento_obj.parent_id.id])

            ##
            ## Não está vinculado ao centro de custo
            ##
            #if not departamento_obj.finan_centrocusto_id:
                #dados = {
                    #'tipo': 'C',
                    #'nome': departamento_obj.name,
                    #'codigo': int(departamento_obj.id),
                    #'hr_department_id': departamento_obj.id,
                #}
                
                #if departamento_obj.parent_id:
                    #dados['parent_id'] = departamento_obj.parent_id.finan_centrocusto_id.id
                #else:
                    #dados['parent_id'] = cc_raiz_id
                    
                #cc_id = cc_pool.create(cr, uid, dados)
                #sql = """
                #update hr_department set
                    #finan_centrocusto_id = {cc_id}
                #where
                    #id = {id};
                #"""
                #sql = sql.format(cc_id=cc_id, id=departamento_obj.id)
                #cr.execute(sql)
                #cr.commit()
            #elif departamento_obj.parent_id:
                #cc_obj = departamento_obj.finan_centrocusto_id
                #cc_pai_obj = departamento_obj.parent_id.finan_centrocusto_id

                #if cc_obj.id != cc_pai_obj.id:
                    #cc_obj.write({'parent_id': cc_pai_obj.id})

        return True
    
    def create(self, cr, uid, dados, context={}):
        res = super(hr_department, self).create(cr, uid, dados, context=context)
        
        self.pool.get('hr.department').ajusta_centrocusto(cr, uid, [res])
        
        return res
    
    #def write(self, cr, uid, ids, dados, context={}):
        #res = super(hr_department, self).write(cr, uid, ids, dados, context=context)

        #self.pool.get('hr.department').ajusta_centrocusto(cr, uid, ids)
        
        #return res
    
    
hr_department()
