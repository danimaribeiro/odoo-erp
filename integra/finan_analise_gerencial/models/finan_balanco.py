# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
import os
import base64
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
from pybrasil.data import parse_datetime, formata_data, agora, hoje, mes_passado, primeiro_dia_mes, ultimo_dia_mes
from finan.wizard.finan_relatorio import Report


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

TIPO_PARTIDA = [
    ('D', u'Débito'),
    ('C', u'Crédito'),
]

FORMATO_RELATORIO = (
    ('pdf', u'PDF'),
    ('csv', u'XLS'),
)
    
class finan_balanco(osv.Model):
    _description = u'finan Balanço'
    _name = 'finan.balanco'
    _rec_name = 'company_id'
    _order = 'data_inicial,data_final'
            
    def _get_soma_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids):
            soma = D('0')
            total_ativo = D('0')
            total_passivo = D('0')
            
            for item_obj in lancamento_obj.lancamentos_ativos_ids:
                total_ativo += D(str(getattr(item_obj, 'valor', 0)))
                
            for item_obj in lancamento_obj.lancamentos_passivos_ids:
                total_passivo += D(str(getattr(item_obj, 'valor', 0)))
                                
            
            soma += total_ativo
            soma -= total_passivo
            soma = soma.quantize(D('0.01'))
        
            if nome_campo == 'vr_ativo':
                res[lancamento_obj.id] = total_ativo
                
            elif nome_campo == 'vr_passivo':
                res[lancamento_obj.id] = total_passivo
                
            elif nome_campo == 'vr_diferenca':
                res[lancamento_obj.id] = soma
                
        return res
            
            
            
    _columns = {                    
        'company_id': fields.many2one('res.company', u'Empresa'),                               
        'data_inicial': fields.date(u'Data Inicial'),
        'data_final': fields.date(u'Data Final'),
        'lancamentos_ativos_ids': fields.one2many('finan.balanco.lancamento', 'finan_balanco_id', u'Lançamentos Ativos',  domain=[('tipo_conta', '=', 'A')]),
        'lancamentos_passivos_ids': fields.one2many('finan.balanco.lancamento', 'finan_balanco_id', u'Lançamentos Passivos', domain=[('tipo_conta', '=', 'P')]),
        'vr_ativo': fields.function(_get_soma_funcao, type='float', store=False, digits=(18, 2), string=u'Total Ativo'),
        'vr_passivo': fields.function(_get_soma_funcao, type='float', store=False, digits=(18, 2), string=u'Total Passivo'),
        'vr_diferenca': fields.function(_get_soma_funcao, type='float', store=False, digits=(18, 2), string=u'Diferença'),
        'formato': fields.selection(FORMATO_RELATORIO, u'Formato'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'ecd.partida.lancamento', context=c),
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'formato': 'pdf',                    
    }
    
    def gera_balanco(self, cr, uid, ids, context={}):
        if not ids:
            return False

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        sql = """
        select *
        from (select
            rp.name as empresa,
            rp.cnpj_cpf,
            coalesce(fc.codigo, 0) as codigo,
            coalesce(fc.codigo_completo,'') as codigo_completo,
            coalesce(fc.nome, '') as nome,
            'Ativo' as tipo,
            fc.sintetica,
            sum(la.valor) as valor
        
        from finan_conta fc
        join finan_conta_arvore fca on fca.conta_pai_id = fc.id
        left join finan_balanco_lancamento la on la.conta_id = fca.conta_id
        left join finan_balanco fb on fb.id = la.finan_balanco_id
        left join res_company c on c.id = fb.company_id
        left join res_partner rp on rp.id = c.partner_id
        
        where
            fc.tipo =  'A'
            and fb.id = {id}        
        
        group by
            empresa,
            rp.cnpj_cpf,
            fc.codigo_completo,
            fc.tipo,
            fc.sintetica,
            fc.codigo,
            fc.nome
        
        union all
        
        select
            rp.name as empresa,
            rp.cnpj_cpf,
            coalesce(fc.codigo, 0) as codigo,
            coalesce(fc.codigo_completo,'') as codigo_completo,
            coalesce(fc.nome, '') as nome,
            'Passivo' as tipo,
            fc.sintetica,
            sum(la.valor * fca.redutora) as valor
        
        from finan_conta fc
        join finan_conta_arvore fca on fca.conta_pai_id = fc.id
        left join finan_balanco_lancamento la on la.conta_id = fca.conta_id
        left join finan_balanco fb on fb.id = la.finan_balanco_id
        left join res_company c on c.id = fb.company_id
        left join res_partner rp on rp.id = c.partner_id
        
        where
            fc.tipo =  'P'
            and fb.id = {id}        
        
        group by
            empresa,
            rp.cnpj_cpf,
            fc.codigo_completo,
            fc.tipo,
            fc.sintetica,
            fc.codigo,
            fc.nome
        ) as a
        order by
        a.tipo,
        a.codigo_completo;"""               
     

        filtro = {
            'id': str(rel_obj.id),            
        }

        sql = sql.format(**filtro)
        
        data_inicial = parse_datetime(rel_obj.data_inicial).date()
        data_final = parse_datetime(rel_obj.data_final).date()

        rel = Report(u'Balanço Financeiro Gerencial', cr, uid)
        rel.outputFormat = rel_obj.formato
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'finan_balanco.jrxml')
        rel.parametros['DATA_INICIAL'] = str(data_inicial)[:10]
        rel.parametros['DATA_FINAL'] = str(data_final)[:10]
        rel.parametros['SQL'] = sql

        pdf, formato = rel.execute()
        
        nome_rel =  u'BALANCO_FINANCEIRO_GERENCIAL_' + str(agora())[:10].replace(' ','_' ).replace('-','_') + '.' + rel_obj.formato
        attachment_pool = self.pool.get('ir.attachment')
        attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'finan.balanco'), ('res_id', '=', rel_obj.id), ('name', '=', nome_rel)])
        attachment_pool.unlink(cr, uid, attachment_ids)
        
        dados = {
            'datas': base64.encodestring(pdf),
            'name': nome_rel,
            'datas_fname': nome_rel,
            'res_model': 'finan.balanco',
            'res_id': rel_obj.id,
            'file_type': 'application/pdf',
        }
        attachment_pool.create(cr, uid, dados)        

        return True
    
finan_balanco()
    
class finan_balanco_lancamento(osv.Model):
    _description = u'Finan Balanço Lançamento'
    _name = 'finan.balanco.lancamento'
    _rec_name = 'codigo'
    _order = 'id'
    
    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids):
            res[lancamento_obj.id] = lancamento_obj.id

        return res
    
    _columns = {
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=False, select=True),
        'tipo': fields.selection(TIPO_PARTIDA,u'Tipo'),        
        'data_inicial': fields.date(u'Data Inicial'),
        'data_final': fields.date(u'Data Final'),
        'finan_balanco_id': fields.many2one('finan.balanco', u'Balanço financeiro', ondelete='cascade'),
        'company_id': fields.related('finan_balanco_id', 'company_id', type='many2one', string=u'Empresa', relation='res.company', store=True),       
        'conta_id': fields.many2one('finan.conta', u'Conta Contábil', ondelete='restrict'),
        'tipo_conta': fields.related('conta_id', 'tipo', type='char', string=u'Tipo conta'),
        'valor': fields.float(u'valor'),
                
    }

    _defaults = {
        'valor': D(0),         
    }
    
    _sql_constraints = [
        ('finan_balanco_id_conta_id_valor_unique', 'unique(finan_balanco_id, conta_id)', u'Conta devem ser única no Balanço!')
    ]
    
    def tipo_conta(self, cr, uid, ids, conta_id, context={}):
        
        if not conta_id:
            return {}
        context['conta_simples'] = True  
        res = {}
        valores = {}
        res['value'] = valores  
           
        conta_pool = self.pool.get('finan.conta')
        conta_obj = conta_pool.browse(cr, uid, conta_id, context=context)
        self.verifica_conta_inativa(cr, uid , [ids], conta_id, context=context)
        valores['tipo_conta'] = conta_obj.tipo
        return res
   
    
    def verifica_conta_inativa(self, cr, uid, ids, conta_id, context={}):
        if not conta_id:
            return {}
        
        res = {}
        valores = {}
        res['value'] = valores          
        conta_pool = self.pool.get('finan.conta')
        conta_obj = conta_pool.browse(cr, uid, conta_id, context=context )
        data = context.get('data', False)
        
        if conta_obj.inativa and data:
            if data > conta_obj.data_inativacao:
                valores['conta_id'] = ''
                raise osv.except_osv(u'ATENÇÃO!', u'Conta: {conta}, Inativa! '.format(conta=conta_obj.nome_simples))
        
        return res
        
    
finan_balanco_lancamento()
