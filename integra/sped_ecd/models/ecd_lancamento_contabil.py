# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D
from pybrasil.valor import formata_valor
from pybrasil.data import parse_datetime
import random

TIPO_LANCAMENTO = [
   ('N', u'Normal'),
   ('E', u'Enceramento'),
]

LANCAMENTO = [
    ('M', u'Manual'),
    ('I', u'Importado'),    
]


class ecd_lancamento_contabil(osv.Model):
    _description = u'ECD Lançamento Contábil'
    _name = 'ecd.lancamento.contabil'
    _rec_name = 'descricao'
    _order = 'codigo desc'
    
    
    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids):
            res[lancamento_obj.id] = lancamento_obj.id

        return res
    
    def _descricao(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids):
            res[lancamento_obj.id] = str(lancamento_obj.id)

        return res
    
    def _get_soma_funcao(self, cr, uid, ids, nome_campo, args, context=None):
        res = {}

        for lancamento_obj in self.browse(cr, uid, ids):
            soma = D('0')
            total_debito = D('0')
            total_credito = D('0')
            
            for item_obj in lancamento_obj.partida_ids:
                total_debito += D(str(getattr(item_obj, 'vr_debito', 0)))
                total_credito += D(str(getattr(item_obj, 'vr_credito', 0)))
            
            soma += total_debito
            soma -= total_credito
            soma = soma.quantize(D('0.01'))
        
            if nome_campo == 'vr_debito':
                res[lancamento_obj.id] = total_debito
                
            elif nome_campo == 'vr_credito':
                res[lancamento_obj.id] = total_credito
                
            elif nome_campo == 'vr_diferenca':
                res[lancamento_obj.id] = soma
                
        return res
    
    _columns = {
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=True, select=False),
        'descricao': fields.function(_descricao, type='char', method=True, store=True, string=u'Descrição'),
        'data': fields.date(u'Data', required=True),
        'tipo': fields.selection(TIPO_LANCAMENTO,u'Tipo'),                
        'lanc': fields.selection(LANCAMENTO,u'Lançamento'),                
        'company_id': fields.many2one('res.company', u'Empresa', required=True, ondelete='restrict'),                
        'cnpj_cpf': fields.char(u'Cnpj', size=18),        
        'plano_id': fields.many2one('ecd.plano.conta', u'Plano de Conta'),
        'user_id': fields.many2one('res.users', u'Usuário', ondelete='restrict', required=True),   
        'vr_debito': fields.function(_get_soma_funcao, type='float', store=False, digits=(18, 2), string=u'Valor Débito'),
        'vr_credito': fields.function(_get_soma_funcao, type='float', store=False, digits=(18, 2), string=u'Valor Crédito'),
        'vr_diferenca': fields.function(_get_soma_funcao, type='float', store=False, digits=(18, 2), string=u'Valor Diferença'),                
        'lote_id': fields.many2one('lote.contabilidade', u'Lote', ondelete='cascade'),
        'tipo_lote': fields.related('lote_id', 'tipo', type='char', string=u'Tipo Lote', store=False),
        'partida_ids': fields.one2many('ecd.partida.lancamento', 'lancamento_id', string=u'Lançamentos'), 
        'saldo_inicial': fields.boolean(u'Saldo Inicial'),
        'finan_lancamento_id': fields.many2one('finan.lancamento', u'Lançamento financeiro', ondelete='restrict'),
        'sped_documento_id': fields.many2one('sped.documento', u'Documento fiscal', ondelete='restrict'),        
        'create_uid': fields.many2one('res.users', u'Criado por'),
        'write_uid': fields.many2one('res.users', u'Alterado por'),        
        'write_date': fields.datetime( u'Data Alteração'),
        
        'data_from': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'Data de'),
        'data_to': fields.function(lambda *a, **k: {}, method=True, type='date', string=u'Data até'),
        'exlusao_manual': fields.boolean(u'Exclusão Manual'),
    }

    _defaults = {
        'data': fields.datetime.now,
        'tipo': 'N',
        'lanc': 'M',
        'vr_debito': D(0),
        'vr_credito': D(0),
        'vr_diferenca': D(0),
        'user_id': lambda self, cr, uid, context: uid,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'ecd.partida.lancamento', context=c),
        'exlusao_manual': False,                                 
    }
    
    def on_change_plano(self, cr, uid, ids, company_id, context={}):
        if not company_id:
            return {}
        retorno = {}
        valores = {}
        retorno['value'] = valores
     
        company_pool = self.pool.get('res.company')
        company_obj = company_pool.browse(cr, uid, company_id)
        if company_obj.plano_id:
            valores['plano_id'] = company_obj.plano_id.id 
            valores['cnpj_cpf'] = company_obj.partner_id.cnpj_cpf 
        else:
            raise osv.except_osv(u'Inválido !', u'Não existe plano de Contas na Empresa selecionada!')             
        return retorno
    
    def on_change_data(self, cr, uid, ids, company_id, data, context={}):
        if not company_id and not data:
            return {}
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        data = parse_datetime(data).date()
        data = str(data)[:10]
        
        periodo_pool = self.pool.get('ecd.periodo')
        
        sql = """
            select 
                id
            from
                ecd_periodo 
            where
                cnpj_cpf = '{cnpj_cpf}'
                and '{data}' between data_inicial and data_final
            order by
                company_id,
                data_final desc
                
        """
        sql = sql.format(cnpj_cpf=company_obj.partner_id.cnpj_cpf,data=data)
        cr.execute(sql)
        #print(sql)

        dados = cr.fetchall()
        if not dados:
            raise osv.except_osv(u'ATENÇÃO!', u'Não existe período contábil na Empresa selecionada!')                                      
        for id in dados:            
            periodo_obj = periodo_pool.browse(cr, uid, id[0])
            
            if periodo_obj.permitir_lancamento in ['2','3'] and periodo_obj.situacao == 'F':
                raise osv.except_osv(u'ATENÇÃO!', u'Período contábil já Fechado!')             
                                 
        return
        
    
    def verifica_debito_credito(self, cr, uid, ids, vals, context=None):
        
        if 'partida_ids' not in vals or not vals['partida_ids']:
            return

        partidas = vals['partida_ids']
        partidas_alteradas = []        

        total_debito = D('0')
        total_credito = D('0')
        data = vals.get('data')
        conta_ids = []
        
        for operacao, partida_id, valores in partidas:
                   
            #
            # Cada lanc_item tem o seguinte formato
            # [operacao, id_original, valores_dos_campos]
            #
            # operacao pode ser:
            # 0 - criar novo registro (no caso aqui, vai ser ignorado)
            # 1 - alterar o registro
            # 2 - excluir o registro (também vai ser ignorado)
            # 3 - desvincula o registro (no caso aqui, seria setar o res_partner_bank_id para outro id)
            # 4 - vincular a um registro existente
            # 5 - excluiu todos a vai incluir todos de novo

            #print(operacao, 'operacao', partida_id, valores)        
            
            if operacao == 0:
                total_debito += D(valores.get('vr_debito', 0) or 0)                  
                total_credito += D(valores.get('vr_credito', 0) or 0)
                if total_debito == 0 and total_credito == 0:  
                    raise osv.except_osv(u'Inválido !', u'Lançamento Zerado')
                
                conta_id = valores.get('conta_id')
                if conta_id:  
                    conta_ids.append(conta_id)
                
            if operacao == 5:
                excluido_ids = self.pool.get('ecd.partida.lancamento').search(cr, uid, [('lancamento_id', 'in', ids)])
                partidas_alteradas += excluido_ids

            if operacao == 2:
                partidas_alteradas += [partida_id]
        
            if operacao == 1 and ('vr_debito' in valores or 'vr_credito' in valores):
                partidas_alteradas += [partida_id]
                total_debito += D(valores.get('vr_debito', 0) or 0)                  
                total_credito += D(valores.get('vr_credito', 0) or 0)            

        #
        # Ajusta com os possíveis não alterados
        #
        
        partidas_ids = []
        if ids and ids[0]:
            partida_pool = self.pool.get('ecd.partida.lancamento')
            lancamento_obj = self.browse(cr, uid, ids[0])
            data = lancamento_obj.data 
            partidas_ids = partida_pool.search(cr, uid, [('lancamento_id', '=', ids[0]), ('id', 'not in', partidas_alteradas)])

            for partida_obj in partida_pool.browse(cr, uid, partidas_ids):
                total_debito += D(str(partida_obj.vr_debito or 0))
                total_credito += D(str(partida_obj.vr_credito or 0))
                if partida_obj.conta_id: 
                    conta_ids.append(partida_obj.conta_id.id)                
        
        total_debito = total_debito.quantize(D('0.01')) 
        total_credito = total_credito.quantize(D('0.01'))
        saldo = total_debito - total_credito
        if not saldo == 0:
            raise osv.except_osv(u'Inválido !', u' Valor Débito: ' + formata_valor(total_debito) + u' Valor Crédito: ' + formata_valor(total_credito) + u' Diferença: ' + formata_valor(saldo))
        
        for conta_id in conta_ids:            
            self.pool.get('ecd.partida.lancamento').verifica_conta_inativa(cr, uid , ids, conta_id, context={'data': data})
    
    def create(self, cr, uid, vals, context={}):
        
        context['conta_simples'] = True 
                
        if 'default_saldo_inicial' in context and context['default_saldo_inicial'] == False:        
            self.verifica_debito_credito(cr, uid, [], vals)
            
            self.verifica_periodo_contabil(cr, uid, [], vals)
                
        res = super(ecd_lancamento_contabil, self).create(cr, uid, vals, context)
        
        if not 'lote_id' in vals:
            dados = self.pool.get('ecd.recomposicao.saldo').gera_dados_contas_recompor(cr, uid, False, res, context=context)
            
            self.pool.get('ecd.recomposicao.saldo').gera_saldo_contas(cr, uid, dados, context=context)
            
        return res

    def write(self, cr, uid, ids, vals, context={}):
        
        context['conta_simples'] = True                 
        
        for lancamento_obj in self.browse(cr, uid, ids):
            
            if lancamento_obj.saldo_inicial == False:
                self.verifica_debito_credito(cr, uid, ids, vals)
                    
                self.verifica_periodo_contabil(cr, uid, ids, vals)
                
            dados = self.pool.get('ecd.recomposicao.saldo').gera_dados_contas_recompor(cr, uid, False, lancamento_obj.id, context=context)
                    
            res = super(ecd_lancamento_contabil, self).write(cr, uid, ids, vals, context=context)            
                               
            self.pool.get('ecd.recomposicao.saldo').gera_saldo_contas(cr, uid, dados, context=context)        
            
        return res
    
    def unlink(self, cr, uid, ids, context={}): 
        
        context['conta_simples'] = True
        
        lote_excluir = False
        
        if 'lote_excluir' in context:
            lote_excluir =  True
        
        
        for lancamento_obj in self.browse(cr, uid, ids):                        
            
            dados_excluir = {
                'cnpj_cpf': lancamento_obj.cnpj_cpf,        
                'company_id': lancamento_obj.company_id.id, 
                'usuario_id': uid,
                'data': lancamento_obj.data,
                'valor': lancamento_obj.vr_debito,
            }
            
            if lancamento_obj.lote_id and not lote_excluir:                
                dados_excluir['lote_id'] = lancamento_obj.lote_id.id
                    
                if lancamento_obj.exlusao_manual:
                    dados = self.pool.get('ecd.recomposicao.saldo').gera_dados_contas_recompor(cr, uid, False, lancamento_obj.id, context=context)
                
                elif lancamento_obj.lote_id.tipo in ['FG','PF','PD','PT']:
                    raise osv.except_osv(u'ATENÇÃO!', u'Lançamento sem permissão de exclusão! Exclua o Lote!')
                                    
                else:
                    raise osv.except_osv(u'ATENÇÃO!', u'Lançamento do Lote!  Marque a opção: "Exclusão Manual" para excluir!')
            elif not lote_excluir:     
                dados = self.pool.get('ecd.recomposicao.saldo').gera_dados_contas_recompor(cr, uid, False, lancamento_obj.id, context=context)
                
            res = super(ecd_lancamento_contabil, self).unlink(cr, uid, ids, context=context)
            
            if not lote_excluir:
                self.pool.get('ecd.recomposicao.saldo').gera_saldo_contas(cr, uid, dados, context=context)            
            
            if lancamento_obj.finan_lancamento_id:
                dados_excluir['finan_lancamento_id'] = lancamento_obj.finan_lancamento_id.id
                
                cr.execute('update finan_lancamento set lote_id = null where id = {id}'.format(id=lancamento_obj.finan_lancamento_id.id))        
                cr.execute('delete from lote_contabilidade_item where lancamento_id = {id}'.format(id=lancamento_obj.finan_lancamento_id.id))        
           
            elif lancamento_obj.sped_documento_id:
                dados_excluir['sped_documento_id'] = lancamento_obj.sped_documento_id.id
                
                cr.execute('update sped_documento set lote_id = null where id = {id}'.format(id=lancamento_obj.sped_documento_id.id))        
                cr.execute('delete from lote_contabilidade_item where documento_id = {id}'.format(id=lancamento_obj.sped_documento_id.id)) 
                       
            if lancamento_obj.lote_id and lancamento_obj.exlusao_manual:                      
                self.pool.get('ecd.lancamento.excluido').create(cr, 1, dados_excluir)            
              
            return res
    
    def forca_recalculo(self, cr, uid, ids, context={}):
        for lancamento_obj in self.browse(cr, uid, ids):
            for item_obj in lancamento_obj.partida_ids:
                item_obj.write({'recalculo': int(random.random() * 100000000)})
                
                     
    def verifica_periodo_contabil(self, cr, uid, ids, vals, context=None):
        
        if ids:
            id = ids[0]
            periodo_obj = self.browse(cr, uid, id)
                          
            if 'company_id' in vals:
                company_id = vals.get('company_id')
            else:               
                company_id = periodo_obj.company_id.id

            if 'data' in vals:
                data = vals.get('data')
            else:
                data = periodo_obj.data
            
        else:
            company_id = vals.get('company_id')    
            data = vals.get('data')
                
        data = parse_datetime(data).date()
        data = str(data)[:10]
        
        periodo_pool = self.pool.get('ecd.periodo')
        company_obj = self.pool.get('res.company').browse(cr, uid, company_id)
        
        sql = """
            select 
                id
            from
                ecd_periodo 
            where
                cnpj_cpf = '{cnpj_cpf}'
                and '{data}' between data_inicial and data_final
            order by
                company_id,
                data_final desc
            
        """
        sql = sql.format(cnpj_cpf=company_obj.partner_id.cnpj_cpf,data=data)
        cr.execute(sql)
        #print(sql)

        dados = cr.fetchall()
        if not dados:
            raise osv.except_osv(u'ATENÇÃO!', u'Não existe período contábil na Empresa selecionada!')                                      
        for id in dados:            
            periodo_obj = periodo_pool.browse(cr, uid, id[0])
            
            if periodo_obj.permitir_lancamento in ['3'] and periodo_obj.situacao == 'F':
                raise osv.except_osv(u'ATENÇÃO!', u'Período contábil já Fechado!')  
                

ecd_lancamento_contabil()
