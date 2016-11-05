# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
import os
from osv import orm, fields, osv
from datetime import datetime, timedelta, date
from dateutil import parser
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from copy import copy
import base64
from finan.wizard.finan_relatorio import Report


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

TIPO_INSTALACAO = (
    ('I', u'Instalação'),
    ('A', u'Ampliação'),
    ('R', u'Remoção do equipamento'),
    ('M', u'Manutenção do equipamento'),
)
TIPO_INSTALACAO_DICT = dict(TIPO_INSTALACAO)


class crm_meeting(orm.Model):
    _name = 'crm.meeting'
    _inherit = 'crm.meeting'
    _rec_name = 'descricao'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, 1, ids):
            if registro.tipo_instalacao or registro.sale_order_id:
                txt = TIPO_INSTALACAO_DICT[registro.tipo_instalacao or 'I']
                txt += ' - ' 
                if registro.sale_order_id:
                    txt += registro.sale_order_id.name
                retorno[registro.id] = txt
                
            else:
                retorno[registro.id] = registro.name

        return retorno

    def _procura_descricao(self, cursor, user_id, obj, nome_campo, args, context=None):
        texto = args[0][2]

        procura = ['|',
            ('name', 'ilike', texto), 
            '|',
            ('tipo_instalacao', 'ilike', texto), 
            ('sale_order_id', 'ilike', texto)
        ]

        return procura
    
    def _get_itens_mao_obra(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}
        item_pool = self.pool.get('sale.order.line')
        
        for inst_obj in self.browse(cr, uid, ids):
            item_ids = []
            
            if inst_obj.sale_order_id:
                item_ids = item_pool.search(cr, uid, [('order_id', '=', inst_obj.sale_order_id.id), ('crm_meeting_id', '=', False), ('orcamento_categoria_id', '=', 6)])
                
            res[inst_obj.id] = item_ids
            
        return res            

    _columns = {
        'descricao': fields.function(_descricao, string=u'Descrição', method=True, type='char', size=60, fnct_search=_procura_descricao),
        'sale_order_id': fields.many2one('sale.order', u'Proposta', ondelete='restrict'),
        'equipe_id': fields.many2one('instalacao.equipe', u'Equipes em instalação', ondelete='restrict'),
        'tipo_instalacao': fields.selection(TIPO_INSTALACAO, u'Tipo'),
        'data_inicial_prevista': fields.datetime(u'Data início prevista'),
        'data_final_prevista': fields.datetime(u'Data conlusão prevista'),
        'data_confirmacao': fields.datetime(u'Data de confirmação'),
        'data_conclusao': fields.datetime(u'Data de conclusão'),
        'nome': fields.char(u'Nome do arquivo', 254, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        
        #
        # Campos necessários pra fazer o cálculo dos novos itens de mão de obra
        #
        'pricelist_id': fields.related('sale_order_id', 'pricelist_id', type='integer', string='pricelist_id'),
        'shop_id': fields.related('sale_order_id', 'shop_id', type='integer', string='shop_id'),
        'company_id': fields.related('sale_order_id', 'company_id', type='integer', string='company_id'),
        'operacao_fiscal_produto_id': fields.related('sale_order_id', 'operacao_fiscal_produto_id', type='integer', string='operacao_fiscal_produto_id'),
        'operacao_fiscal_servico_id': fields.related('sale_order_id', 'operacao_fiscal_servico_id', type='integer', string='operacao_fiscal_servico_id'),
        'fiscal_position': fields.related('sale_order_id', 'fiscal_position', type='integer', string='fiscal_position'),
        'orcamento_aprovado': fields.related('sale_order_id', 'orcamento_aprovado', type='char', string='orcamento_aprovado'),
        'date_order': fields.related('sale_order_id', 'date_order', type='date', string='date_order'),
        'order_state': fields.related('sale_order_id', 'state', type='char', string='state'),
        'simulacao_parcelas': fields.related('sale_order_id', 'simulacao_parcelas', type='text', string=u'Parcelamento'),
        
        'mao_de_obra_original_ids': fields.function(_get_itens_mao_obra, type='one2many', relation='sale.order.line', string=u'Mão-de-obra original'),
        'mao_de_obra_extra_ids': fields.one2many('sale.order.line', 'crm_meeting_id', string=u'Mão-de-obra extra'),
    }
    
    def onchange_sale_order_id(self, cr, uid, ids, sale_order_id, context={}):
        if not sale_order_id:
            return {}
        
        pedido_obj = self.pool.get('sale.order').browse(cr, uid, sale_order_id)
        
        valores = {}
        res = {'value': valores}
        
        valores['partner_id'] = pedido_obj.partner_id.id
        valores['partner_address_id'] = pedido_obj.partner_shipping_id.id
        
        #
        # Campos para cálculo dos itens de mão de obra
        #
        valores['pricelist_id'] = pedido_obj.pricelist_id.id
        valores['company_id'] = pedido_obj.company_id.id
        valores['orcamento_aprovado'] = pedido_obj.orcamento_aprovado
        valores['date_order'] = pedido_obj.date_order
        valores['order_state'] = pedido_obj.state
        valores['simulacao_parcelas'] = pedido_obj.simulacao_parcelas
        
        if pedido_obj.shop_id:
            valores['shop_id'] = pedido_obj.shop_id.id

        if pedido_obj.fiscal_position:
            valores['fiscal_position'] = pedido_obj.fiscal_position.id
        
        if pedido_obj.operacao_fiscal_produto_id:
            valores['operacao_fiscal_produto_id'] = pedido_obj.operacao_fiscal_produto_id.id
            
        if pedido_obj.operacao_fiscal_servico_id:
            valores['operacao_fiscal_servico_id'] = pedido_obj.operacao_fiscal_servico_id.id
        
        return res
    
    def onchange_dates(self, cr, uid, ids, start_date, duration=False, end_date=False, allday=False, context=None):
        """Returns duration and/or end date based on values passed
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar event’s IDs.
        @param start_date: Starting date
        @param duration: Duration between start date and end date
        @param end_date: Ending Datee
        @param context: A standard dictionary for contextual values
        """
        if context is None:
            context = {}

        value = {}
        if not start_date:
            return value
        if not end_date and not duration:
            duration = 1.00
            value['duration'] = duration

        if allday: # For all day event
            value = {'duration': 24.0}
            duration = 24.0
            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                start_date = datetime.strftime(datetime(start.year, start.month, start.day, 0,0,0), "%Y-%m-%d %H:%M:%S")
                value['date'] = start_date


        start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        if end_date and not duration:
            end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            diff = end - start
            duration = float(diff.days)* 24 + (float(diff.seconds) / 3600)
            value['duration'] = round(duration, 2)
        elif not end_date:
            end = start + timedelta(hours=duration)
            value['date_deadline'] = end.strftime("%Y-%m-%d %H:%M:%S")
        elif end_date and duration and not allday:
            # we have both, keep them synchronized:
            # set duration based on end_date (arbitrary decision: this avoid
            # getting dates like 06:31:48 instead of 06:32:00)
            end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            diff = end - start
            duration = float(diff.days)* 24 + (float(diff.seconds) / 3600)
            value['duration'] = round(duration, 2)

        return {'value': value}
    
    def create(self, cr, uid, dados, context={}):
        if 'name' not in dados and 'tipo_instalacao' in dados:
            dados['name'] = TIPO_INSTALACAO_DICT[dados['tipo_instalacao']]
            
        self.pool.get('crm.meeting').valida_periodo(cr, uid, dados)

        return super(crm_meeting, self).create(cr, uid, dados, context=context)
    
    def write(self, cr, uid, ids, dados, context={}):
        if 'date' in dados or 'date_deadline' in dados or 'equipe_id' in dados:
            for inst_obj in self.pool.get('crm.meeting').browse(cr, uid, ids, context=context):
                teste = copy(dados)
                
                if 'date' not in dados:
                    teste['date'] = inst_obj.date
                    
                if 'date_deadline' not in dados:
                    teste['date_deadline'] = inst_obj.date_deadline
                    
                if 'equipe_id' not in dados:
                    teste['equipe_id'] = inst_obj.equipe_id.id
                
                self.pool.get('crm.meeting').valida_periodo(cr, uid, teste)
            
        return super(crm_meeting, self).write(cr, uid, ids, dados, context=context)

    def valida_periodo(self, cr, uid, dados):
        filtro = {
            'equipe_id': dados['equipe_id'],
            'data_inicial': dados['date'],
            'data_final': dados['date_deadline'],
        }
        
        sql = """
        select
            cm.id
        
        from crm_meeting cm
        
        where
            cm.equipe_id = {equipe_id}
            and ('{data_inicial}' between cm.date and cm.date_deadline
            or '{data_final}' between cm.date and cm.date_deadline);
        """
        
        sql = sql.format(**filtro)
        cr.execute(sql)
        
        if len(cr.fetchall()):
            raise osv.except_osv(u'Aviso!', u'Impossível realizar agendamento, pois já existe compromisso para o período.')
        
    def case_open(self, cr, uid, ids, *args):
        res = super(crm_meeting, self).case_open(cr, uid, ids, *args)
        
        for inst_obj in self.pool.get('crm.meeting').browse(cr, uid, ids):
            if not inst_obj.data_confirmacao:
                inst_obj.write({'data_confirmacao': fields.datetime.now(), 'data_inicial_prevista': inst_obj.date, 'data_final_prevista': inst_obj.date_deadline})

        return res
    
    def case_close(self, cr, uid, ids, *args):
        res = super(crm_meeting, self).case_close(cr, uid, ids, *args)
        
        for inst_obj in self.pool.get('crm.meeting').browse(cr, uid, ids):
            inst_obj.write({'data_conclusao': fields.datetime.now()})

        return res

    def imprime_ficha_tecnica(self, cr, uid, ids, context={}):
        for agenda_obj in self.browse(cr, uid, ids):
            rel = Report(u'Ficha técnica', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_orcamento_cotacao.jrxml')
            rel.parametros['UID'] = uid
            rel.parametros['REGISTRO_IDS'] = "(" + str(agenda_obj.sale_order_id.id) + ")"
            nome_arq = u'ficha_tecnica_' + agenda_obj.sale_order_id.name.strip() + u'.pdf'

            pdf, formato = rel.execute()

            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'crm.meeting'), ('res_id', '=', agenda_obj.id), ('name', '=', nome_arq)])
            #
            # Apaga os arquivos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': nome_arq,
                'datas_fname': nome_arq,
                'res_model': 'crm.meeting',
                'res_id': agenda_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

            return True
            
    def imprime_os(self, cr, uid, ids, context={}):
        for agenda_obj in self.browse(cr, uid, ids):
            #
            # Mão-de-obra
            #
            rel = Report(u'OS - mão-de-obra', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_orcamento_mao_obra.jrxml')
            rel.parametros['REGISTRO_IDS'] = '(' +  str(agenda_obj.sale_order_id.id) + ')'
            rel.parametros['OPERACIONAL'] = True
            nome_arq = u'os_mao_de_obra_' + agenda_obj.sale_order_id.name.strip() + u'.pdf'
            
            pdf, formato = rel.execute()
            
            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'crm.meeting'), ('res_id', '=', agenda_obj.id), ('name', '=', nome_arq)])
            #
            # Apaga os arquivos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': nome_arq,
                'datas_fname': nome_arq,
                'res_model': 'crm.meeting',
                'res_id': agenda_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

            return True

    def imprime_ordem_pagamento(self, cr, uid, ids, context={}):
        for agenda_obj in self.browse(cr, uid, ids):
            #
            # Mão-de-obra
            #
            rel = Report(u'OP - mão-de-obra', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'patrimonial_orcamento_mao_obra.jrxml')
            rel.parametros['REGISTRO_IDS'] = '(' +  str(agenda_obj.sale_order_id.id) + ')'
            rel.parametros['OPERACIONAL'] = False
            nome_arq = u'op_mao_de_obra_' + agenda_obj.sale_order_id.name.strip() + u'.pdf'
            
            pdf, formato = rel.execute()
            
            attachment_pool = self.pool.get('ir.attachment')
            attachment_ids = attachment_pool.search(cr, uid, [('res_model', '=', 'crm.meeting'), ('res_id', '=', agenda_obj.id), ('name', '=', nome_arq)])
            #
            # Apaga os arquivos anteriores com o mesmo nome
            #
            attachment_pool.unlink(cr, uid, attachment_ids)

            dados = {
                'datas': base64.encodestring(pdf),
                'name': nome_arq,
                'datas_fname': nome_arq,
                'res_model': 'crm.meeting',
                'res_id': agenda_obj.id,
                'file_type': 'application/pdf',
            }
            attachment_pool.create(cr, uid, dados)

            return True


crm_meeting()
