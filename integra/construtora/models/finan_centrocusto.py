# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals


from osv import orm, fields, osv
from pybrasil.data import hoje, primeiro_dia_mes, ultimo_dia_mes, parse_datetime, mes_passado
from pybrasil.valor.decimal import Decimal as D
from copy import copy


class finan_centrocusto(orm.Model):
    _inherit = 'finan.centrocusto'

    _columns = {
        'rateio_empreendimento': fields.boolean(u'CONTÁBIL – alocação custo dos lotes', select=True),
        'project_id': fields.many2one('project.project', u'Empreendimento'),
        'rateio_rh': fields.boolean(u'RECURSOS HUMANOS – alocações', select=True),
        'rateio_finan_locacao': fields.boolean(u'FINANCEIRO – alocações', select=True),
    }

    _defaults = {
        'rateio_empreendimento': False,
    }

    def realiza_rateio(self, cr, uid, ids, context={}, valor=0, campos=[], padrao={}, rateio={}, tabela_pool=None):
        #
        # No caso de rateio da folha, antes de fazer o rateio, preparamos
        # os itens de rateio de acordo com os dados adequados da folha
        #
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        if not campos:
            campos = self.campos_rateio(cr, uid)

        imovel_pool = self.pool.get('const.imovel')
        cc_pool = self.pool.get('finan.centrocusto')

        if tabela_pool is None:
            tabela_pool = self.pool.get('finan.centrocusto')

        for cc_obj in tabela_pool.browse(cr, uid, ids):
            return super(finan_centrocusto, self).realiza_rateio(cr, uid, ids, context=context, valor=valor, campos=campos, padrao=padrao, rateio=rateio, tabela_pool=tabela_pool)
        
            #
            # Comentado para ser usado o rateio por imóvel somente na contabilidade
            #
            ####if not getattr(cc_obj, 'rateio_empreendimento', False):
                ####return super(finan_centrocusto, self).realiza_rateio(cr, uid, ids, context=context, valor=valor, campos=campos, padrao=padrao, rateio=rateio, tabela_pool=tabela_pool)
            
            ####else:
                #####
                ##### Seleciona os imóveis e suas áreas
                #####
                ####sql = """
                ####select
                    ####ci.id, coalesce(ci.area_total, 0) as area_total
                
                ####from const_imovel ci

                ####where 
                    ####ci.project_id = {project_id}
                    ####and ci.situacao_contabil = 'D';
                ####"""

                ####filtro = {
                    ####'project_id': cc_obj.project_id.id,
                ####}

                ####print(sql.format(**filtro))
                ####cr.execute(sql.format(**filtro))

                ####imovel_ids = {}
                ####dados = cr.fetchall()
                ####area_total = D(0)
                ####for imovel_id, area, in dados:
                    ####imovel_ids[imovel_id] = D(area or 0)
                    ####area_total += D(area or 0)
                ####if not area_total:
                    ####raise osv.except_osv(u'Erro!', u'Está sendo usado um rateio por projeto, porém não existem imóveis vinculados a esse projeto (área total zerada)!')

                #####
                ##### Prepara agora o rateio, com o percentual de cada imóvel
                #####
                ####for imovel_id in imovel_ids:
                    ####p = copy(padrao)
                    ####p['centrocusto_id'] = False
                    ####p['imovel_id'] = imovel_id
                    ####p['project_id'] = cc_obj.project_id.id
                    
                    ####if imovel_ids[imovel_id]:
                        ####percentual = imovel_ids[imovel_id] / area_total * 100
                    ####else:
                        ####percentual = 0
                        
                    ####cc_pool._realiza_rateio(valor, percentual, campos, p, rateio)
                    
            ####print(rateio)

            return rateio


finan_centrocusto()


class finan_rateio(orm.Model):
    _inherit = 'finan.rateio'

    _columns = {
        'project_id': fields.many2one('project.project', u'Projeto/empreendimento', select=True, ondelete='restrict'),
        'imovel_id': fields.many2one('const.imovel', u'Imóvel', select=True, ondelete='restrict'),
    }


finan_rateio()

