# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.data import parse_datetime, formata_data, agora, hoje
from pybrasil.valor import formata_valor
from pybrasil.valor.decimal import Decimal as D
from dateutil.relativedelta import relativedelta

class ecd_recomposicao_saldo(osv.Model):
    _description = u'Ecd Recomposição de Saldo'
    _name = 'ecd.recomposicao.saldo'
    _rec_name = 'periodo_id'
    _order = 'periodo_id'
    
    _columns = {
        'company_id': fields.many2one('res.company',u'Empresa', ondelete='restrict'),
        'cnpj_cpf': fields.related('company_id', 'cnpj_cpf', type='char', string=u'Cnpj', store=True),
        'periodo_id': fields.many2one('ecd.periodo', u'Periodo', ondele='restrict'),
        'data_inicial': fields.date(u'Data Inicial'),
        'data_final': fields.date(u'Data Final'),         
        'data_ultima': fields.date(u'Última recomposição'),               
        'user_id': fields.many2one('res.users',u'Usúario'),
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),        
        'write_date': fields.datetime( u'Data Alteração'),
        'conta_ids': fields.many2many('finan.conta','recomposica_finan_conta', 'recomposica_id', 'conta_id', string=u'Contas Contábeis'),        
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'ecd.recomposicao.saldo', context=c),
                 
    }   
    
    _sql_constraints = [
        ('cnpj_cpf_periodo_id_unique', 'unique(company_id,cnpj_cpf,periodo_id)',
            u'Já existe Recomposição para Empresa/Periodo selecionado!'),
    ]
    
    def on_change_periodo(self, cr, uid, ids, periodo_id, context={}):
        
        periodo_obj = self.pool.get('ecd.periodo').browse(cr, uid, periodo_id)
        
        retorno = {}
        valores = {}
        retorno['value'] = valores
        
        if periodo_obj.data_inicial and periodo_obj.data_final:
            valores['data_inicial'] = periodo_obj.data_inicial
            valores['data_final'] = periodo_obj.data_final
            
        return retorno
         
    def valida_data(self, cr, uid, ids, vals, context={}):
        
        if not ids:            
            data_inicial = vals.get('data_inicial')     
            data_final = vals.get('data_final')     
            periodo_id = vals.get('periodo_id') 
            periodo_obj = self.pool.get('ecd.periodo').browse(cr, uid, periodo_id)
                
        else:
            reco_obj = self.browse(cr, uid, ids[0])
            if 'data_inicial' in vals :
                data_inicial = vals.get('data_inicial')   
            else:
                data_inicial = reco_obj.data_inicial
                
            if 'data_final' in vals :
                data_final = vals.get('data_final')   
            else:
                data_final = reco_obj.data_final
                
            periodo_obj = reco_obj.periodo_id                
        
        if data_inicial < periodo_obj.data_inicial:
            raise osv.except_osv(u'Inválido !', u'Data devem esta entre {a} e {b}!'.format(a=formata_data(periodo_obj.data_inicial),b=formata_data(periodo_obj.data_final)))
        
        elif data_inicial > periodo_obj.data_final:            
            raise osv.except_osv(u'Inválido !', u'Data devem esta entre {a} e {b}!'.format(a=formata_data(periodo_obj.data_inicial),b=formata_data(periodo_obj.data_final)))
        
        elif data_final < periodo_obj.data_inicial:            
            raise osv.except_osv(u'Inválido !', u'Data devem esta entre {a} e {b}!'.format(a=formata_data(periodo_obj.data_inicial),b=formata_data(periodo_obj.data_final)))
        
        elif data_final > periodo_obj.data_final:            
            raise osv.except_osv(u'Inválido !', u'Data devem esta entre {a} e {b}!'.format(a=formata_data(periodo_obj.data_inicial),b=formata_data(periodo_obj.data_final)))
                   
    def create(self, cr, uid, vals, context={}):        
                                
        self.valida_data(cr, uid, [], vals)
                
        res = super(ecd_recomposicao_saldo, self).create(cr, uid, vals, context)
        
        return res

    def write(self, cr, uid, ids, vals, context={}):
        
        self.valida_data(cr, uid, ids, vals)                           
                
        res = super(ecd_recomposicao_saldo, self).write(cr, uid, ids, vals, context=context)                                                    
            
        return res
         
    def gera_recomposicao_saldo_antigo(self, cr, uid, ids, context):
        
        for saldo_obj in self.browse(cr, uid, ids):
            periodo_obj = saldo_obj.periodo_id
            
            if not periodo_obj.situacao == 'A':
                raise osv.except_osv(u'ATENÇÃO!', u'Periodo Fechado!') 
            
            cr.execute("delete from ecd_saldo where data between '{data_inicial}' and '{data_final}' and cnpj_cpf = '{cnpj}' ".format(cnpj=saldo_obj.cnpj_cpf, data_inicial=periodo_obj.data_inicial,data_final=periodo_obj.data_final))                
            
            saldo_pool = self.pool.get('ecd.saldo')
                        
            data_inicial = parse_datetime(periodo_obj.data_inicial).date()
            data_final = parse_datetime(periodo_obj.data_final).date()
                        
            sql_empresa = """
                select 
                rp.cnpj_cpf as cnpj_cpf,
                c.id company_id,
                fc.id as conta_id
                from finan_conta fc 
                join ecd_plano_conta ep on ep.id = fc.plano_id 
                join res_company c on c.plano_id = ep.id
                join res_partner rp on rp.id = c.partner_id 
                
                where
                fc.sintetica = False
                and rp.cnpj_cpf = '{cnpj}';"""
            sql_empresa = sql_empresa.format(cnpj=saldo_obj.cnpj_cpf)
           
            cr.execute(sql_empresa)
            dados_empresa = cr.fetchall()
                        
            for _cnpj_cpf, _company_id, _conta_id in dados_empresa:                
                
                print('recompondo',_cnpj_cpf, _company_id)
                
                _data = data_inicial
                
                while _data <= data_final:
                    
                    print('data', _data )
                                                                               
                    sql_insert = """                        
                        select
                            rp.cnpj_cpf,
                            c.id as company_id,
                            lc.data as data_lancamento,
                            fc.id as conta_id,
                            coalesce(sum(pt.vr_debito),0) as valor_debito,
                            coalesce(sum(pt.vr_credito),0) as valor_credito, 
                            coalesce(sum(cast(pt.vr_debito as numeric(18,2))) - sum(cast(pt.vr_credito as numeric(18,2))), 0) as saldo                                                
                        from
                            ecd_lancamento_contabil lc
                            join ecd_partida_lancamento pt on pt.lancamento_id = lc.id
                            join finan_conta fc on fc.id = pt.conta_id
                            join res_company c on c.id = lc.company_id
                            join res_partner rp on rp.id = c.partner_id
                        where
                            lc.data = '{data}'
                            and rp.cnpj_cpf = '{cnpj}'
                            and c.id = {company_id}
                            and fc.id = {conta_id}                           
                        group by
                            rp.cnpj_cpf,
                            c.id,
                            lc.data,
                            fc.id                     
                        order by
                            rp.cnpj_cpf,
                            lc.data,
                            fc.id"""
                        
                    sql_insert = sql_insert.format(cnpj=_cnpj_cpf, company_id=_company_id, conta_id=_conta_id, data=str(_data)[:10])
                    
                    cr.execute(sql_insert)
                                        
                    dados = cr.fetchall()
                                        
                    if dados and dados > 0:                        
                        for cnpj_cpf, company_id, data, conta_id, vr_debito , vr_credito, saldo in dados:
                            
                            dados_insert  = {
                                'cnpj_cpf': cnpj_cpf, 
                                'company_id': company_id, 
                                'data': data,                                 
                                'conta_id': conta_id, 
                                'vr_debito': vr_debito or 0, 
                                'vr_credito': vr_credito or 0, 
                                'saldo': saldo or 0, 
                                'saldo_anterior': 0, 
                            }                              
                            saldo_pool.create(cr, uid, dados_insert ) 
                    else:  
                        dados_insert  = {
                            'cnpj_cpf': _cnpj_cpf, 
                            'company_id': _company_id, 
                            'data': _data, 
                            'conta_id': _conta_id, 
                            'vr_debito': 0, 
                            'vr_credito': 0, 
                            'saldo': 0, 
                            'saldo_anterior': 0, 
                        }                                               
                        saldo_pool.create(cr, uid, dados_insert) 
                        
                    _data = _data + relativedelta(days=+1)
            
                
            sql_update = """
                update ecd_saldo es set 
                write_date = '{data_hoje}'
                ,
                saldo_anterior = (select sum(esa.saldo) from ecd_saldo esa
                                where 
                                    esa.conta_id = es.conta_id 
                                    and esa.cnpj_cpf = es.cnpj_cpf
                                    and esa.company_id = es.company_id 
                                    and esa.data < es.data)
                , 
                saldo = coalesce((select sum(esa.saldo) from ecd_saldo esa
                                where esa.conta_id = es.conta_id
                                and esa.cnpj_cpf = es.cnpj_cpf
                                and esa.company_id = es.company_id 
                                and esa.data < es.data),0) +  coalesce(es.vr_debito,0) -  coalesce(es.vr_credito,0)
                where
                    es.data between '{data_inicial}' and '{data_final}'
                    and es.cnpj_cpf = '{cnpj}';"""
                    
            sql_update = sql_update.format(cnpj=saldo_obj.cnpj_cpf, data_inicial=periodo_obj.data_inicial,data_final=periodo_obj.data_final, data_hoje=agora())
            cr.execute(sql_update)
             
            saldo_obj.write({'data_ultima': agora(), 'user_id': uid})
                                          
        return True    
    
    def gera_recomposicao_saldo(self, cr, uid, ids, context): 
        
        lancamento_pool = self.pool.get('ecd.lancamento.contabil')
        
        for saldo_obj in self.browse(cr, uid, ids):   
            
            conta_ids = []
            if len(saldo_obj.conta_ids):    
                    
                for conta_obj in saldo_obj.conta_ids:
                    conta_ids.append(conta_obj.id)                     
            
            sql = """
            
            select 
                a.cnpj_cpf,
                a.company_id,
                a.conta_id,
                min(a.data_inicial) as data_inicial,
                max(a.data_final) as data_final
                
            from (
                select distinct
                    l.cnpj_cpf,
                    l.company_id,
                    lp.conta_id,
                    min(l.data) as data_inicial,
                    (select 
                        max(ml.data) 
                    from 
                        ecd_lancamento_contabil ml
                        join ecd_partida_lancamento mlp on mlp.lancamento_id = ml.id    
                    where
                        ml.company_id = l.company_id
                        and ml.cnpj_cpf = l.cnpj_cpf
                        and mlp.conta_id = lp.conta_id
                    ) as data_final
                    
                from 
                    ecd_lancamento_contabil l                 
                    join ecd_partida_lancamento lp on lp.lancamento_id = l.id 
                    
                where
                    l.cnpj_cpf = '{cnpj}'
                    and l.data between '{data_inicial}' and '{data_final}'   
                    
                group by 
                    l.cnpj_cpf,
                    l.company_id,
                    lp.conta_id
                
                union all
                
                select distinct
                    s.cnpj_cpf,
                    s.company_id,
                    s.conta_id,
                    min(s.data) as data_inicial,
                    (select 
                        max(ml.data) 
                    from 
                        ecd_saldo ml        
                    where
                        ml.company_id = s.company_id
                        and ml.cnpj_cpf = s.cnpj_cpf
                        and ml.conta_id = s.conta_id
                    ) as data_final
                
                from 
                    ecd_saldo s 
                    left join ecd_lancamento_contabil l on l.cnpj_cpf = s.cnpj_cpf and l.data = s.data 
                    left join ecd_partida_lancamento lp on lp.lancamento_id = l.id and lp.conta_id = s.conta_id   
                where
                    s.cnpj_cpf = '{cnpj}'
                    and s.data between '{data_inicial}' and '{data_final}'
                    and lp.id is null
                    and (s.saldo_anterior <> 0 or s.saldo <> 0)
                
                group by 
                    s.cnpj_cpf,
                    s.company_id,
                    s.conta_id 
            ) as a """
            
            if len(conta_ids) > 0:
                sql +=""" 
            where
                a.conta_id in """ +  str(tuple(conta_ids)).replace(',)', ')')
            
            sql +=""" 
            group by
                a.cnpj_cpf,
                a.company_id,
                a.conta_id               
        
            order by 
                4;""" 
            
            sql = sql.format(cnpj=saldo_obj.cnpj_cpf, data_inicial=saldo_obj.data_inicial, data_final=saldo_obj.data_final)
            print(sql)
                        
            cr.execute(sql)            
            dados = cr.fetchall()
            
            if dados > 0:                                  
                self.gera_saldo_contas(cr, uid, dados, context)                                          
            else:
                raise osv.except_osv(u'Inválido !', u'Não existe Saldo para Recompor!')
            
        return True    
    
    def gera_dados_contas_recompor(self, cr, uid, lote_id=False, lancamento_id=False, context=None):
                        
        sql_busca = """        
        select distinct
            l.cnpj_cpf,
            l.company_id,
            lp.conta_id,
            min(l.data) as data_inicial,
            (select 
                max(ml.data) 
            from 
                ecd_lancamento_contabil ml
                join ecd_partida_lancamento mlp on mlp.lancamento_id = ml.id    
            where
                ml.company_id = l.company_id
                and ml.cnpj_cpf = l.cnpj_cpf
                and mlp.conta_id = lp.conta_id
            ) as data_final
            
        from 
            ecd_lancamento_contabil l
            join ecd_partida_lancamento lp on lp.lancamento_id = l.id    
        where
        """ 
            
        if lote_id:     
            sql_busca += """ 
            l.lote_id = """ + str(lote_id)  
            
        if lancamento_id:     
            sql_busca += """ 
            l.id = """ + str(lancamento_id)  
            
        sql_busca += """ 
            group by 
                l.cnpj_cpf,
                l.company_id,
                lp.conta_id;"""
                                             
        cr.execute(sql_busca)
        dados = cr.fetchall()
        
        return dados

    def gera_saldo_contas(self, cr, uid, dados={}, context=None):
        
        saldo_pool = self.pool.get('ecd.saldo')
        
        for cnpj_cpf, company_id, conta_id, data_inicial, data_final in dados:
                                                                    
            cr.execute("delete from ecd_saldo where data between '{data_inicial}' and '{data_final}' and cnpj_cpf = '{cnpj}' and conta_id = {conta_id} and company_id = {company_id}; ".format(cnpj=cnpj_cpf, data_inicial=data_inicial, data_final=data_final, conta_id=conta_id, company_id=company_id))
            
            _data_inicial = parse_datetime(data_inicial).date()
            _data_final = parse_datetime(data_final).date()
            
            _data = _data_inicial
                
            while _data <= _data_final:
                
                sql_insert = """                        
                        select                            
                            coalesce(sum(pt.vr_debito),0) as valor_debito,
                            coalesce(sum(pt.vr_credito),0) as valor_credito, 
                            coalesce(sum(cast(pt.vr_debito as numeric(18,2))) - sum(cast(pt.vr_credito as numeric(18,2))), 0) as saldo                                                
                        from
                            ecd_partida_lancamento pt 
                                                        
                        where
                            pt.data = '{data}'
                            and pt.cnpj_cpf = '{cnpj}'
                            and pt.company_id = {company_id}
                            and pt.conta_id = {conta_id}                                                                       
                        """
                        
                sql_insert = sql_insert.format(cnpj=cnpj_cpf, company_id=company_id, conta_id=conta_id, data=str(_data)[:10])                
                cr.execute(sql_insert)                                    
                dados = cr.fetchall()
                                        
                if dados and dados > 0:                        
                    for vr_debito, vr_credito, saldo in dados:
                            
                            dados_insert  = {
                                'cnpj_cpf': cnpj_cpf, 
                                'company_id': company_id, 
                                'data': _data,                                 
                                'conta_id': conta_id, 
                                'vr_debito': vr_debito or 0, 
                                'vr_credito': vr_credito or 0, 
                                'saldo': saldo or 0, 
                                'saldo_anterior': 0, 
                            }                              
                            saldo_pool.create(cr, uid, dados_insert ) 
                else:  
                    dados_insert  = {
                        'cnpj_cpf': cnpj_cpf, 
                        'company_id': company_id, 
                        'data': _data, 
                        'conta_id': conta_id, 
                        'vr_debito': 0, 
                        'vr_credito': 0, 
                        'saldo': 0, 
                        'saldo_anterior': 0, 
                    }                                               
                    saldo_pool.create(cr, uid, dados_insert) 
                        
            
                sql_update = """
                    update ecd_saldo es set 
                    write_date = '{data_hoje}'
                    ,
                    saldo_anterior = coalesce((select esa.saldo from ecd_saldo esa
                                    where 
                                        esa.conta_id = es.conta_id 
                                        and esa.cnpj_cpf = es.cnpj_cpf
                                        and esa.company_id = es.company_id 
                                        and esa.data < es.data
                                    order by
                                        esa.data desc
                                        limit 1), 0)
                                                                            
                    , 
                    saldo = coalesce((select esa.saldo from ecd_saldo esa
                                    where esa.conta_id = es.conta_id
                                    and esa.cnpj_cpf = es.cnpj_cpf
                                    and esa.company_id = es.company_id 
                                    and esa.data < es.data
                                    order by
                                        esa.data desc
                                        limit 1),0) +  coalesce(es.vr_debito,0) -  coalesce(es.vr_credito,0)
                    where
                        es.data = '{data_anterior}'
                        and es.cnpj_cpf = '{cnpj}'
                        and es.conta_id = {conta_id} 
                        and es.company_id = {company_id};"""
                        
                sql_update = sql_update.format(cnpj=cnpj_cpf,data_anterior=_data,data_hoje=agora(),conta_id=conta_id,company_id=company_id)                    
                cr.execute(sql_update)                

                _data = _data + relativedelta(days=+1)
            
        return True   
        
    
ecd_recomposicao_saldo()



class ecd_saldo(osv.Model):
    _description = u'Ecd Saldo de Contas'
    _name = 'ecd.saldo'
    _rec_name = 'data'
    _order = 'data'
    
    _columns = {
        'cnpj_cpf': fields.char(u'CNPJ', size=18),
        'company_id': fields.many2one('res.company',u'Empresa', ondelete='restrict'),
        'data': fields.date(u'Data Lançamento'),
        'conta_id': fields.many2one('finan.conta', u'Conta Contábil', ondelete='restrict'),
        'vr_debito': fields.float(u'Débito'),
        'vr_credito': fields.float(u'Crédito'),
        'saldo': fields.float(u'Saldo'),
        'saldo_anterior': fields.float(u'Saldo anterior'),
        'nao_excluir': fields.boolean(u'Não excluir'),
        'data_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'Data de'),
        'data_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'Data até'),
    }
    
    def unlink(self, cr, uid, ids, context={}):
        
        nao_excluir = context.get('nao_excluir')
                
        if nao_excluir:
            return {}
        else:
            return super(ecd_partida_lancamento, self).unlink(cr, uid, ids, context)
    
ecd_saldo()


