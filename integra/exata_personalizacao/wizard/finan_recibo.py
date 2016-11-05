# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals

from datetime import datetime
from osv import fields, osv
import os
from finan.wizard.finan_relatorio import Report
import base64
from finan.wizard import SQL_DIVIDA
from StringIO import StringIO
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger

DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
JASPER_BASE_DIR = os.path.join(DIR_ATUAL, '../../reports/base/')

SQL_PAGAMENTO = """
select
  divida.data_documento,
  divida.data_vencimento,
  l.data_quitacao,
  coalesce(d.nome, '') as tipo_documento,
  coalesce(divida.numero_documento, '') as numero_documento,
  formata_valor(cast(coalesce(l.valor_documento, coalesce(l.valor, 0)) as varchar)) as valor_documento_formatado,
  l.cheque_id,
  chq.numero_cheque,
  chq.agencia || ' - ' || chq.conta_corrente as agencia_cc,
  chq.valor,
  chq.data_pre_datado,
  chq.titular_nome,
  b.name as chq_banco,
  rb.name as banc_liquidacao

from
  finan_lancamento l
  join finan_lancamento divida on divida.id = l.lancamento_id
  left join finan_documento d on d.id = divida.documento_id
  left join finan_cheque chq on chq.id = l.cheque_id
  left join res_bank b on b.id = chq.bank_id
  left join res_partner_bank rb on rb.id = chq.res_partner_bank_id

where
  l.lancamento_id in {divida_ids}
  {filtro_adicional}

order by
  l.data_quitacao;
"""

SQL_PAGAMENTO_PREVIO = """
select
  divida.data_documento,
  divida.data_vencimento,
  current_date as data_quitacao,
  coalesce(d.nome, '') as tipo_documento,
  coalesce(divida.numero_documento, '') as numero_documento,
  formata_valor(cast(coalesce(divida.valor_saldo, coalesce(divida.valor, 0)) as varchar)) as valor_documento_formatado,
  l.cheque_id,
  chq.numero_cheque,
  chq.agencia || ' - ' || chq.conta_corrente as agencia_cc,
  chq.valor,
  chq.data_pre_datado,
  chq.titular_nome,
  b.name as chq_banco,
  rb.name as banc_liquidacao

from
  finan_lancamento divida
  left join finan_documento d on d.id = divida.documento_id
  left join finan_cheque chq on chq.id = l.cheque_id
  left join res_bank b on b.id = chq.bank_id
  left join res_partner_bank rb on rb.id = chq.res_partner_bank_id

where
  divida.id in {divida_ids};
"""


class finan_recibos(osv.osv_memory):
    _name = 'finan.recibos'
    _inherit = 'finan.recibos'

    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária'),
    }

    _defaults = {
        'data_inicial': fields.date.today,
        'data_final': fields.date.today,
    }

    def gerar_recibos_exata(self, cr, uid, ids, context=None):
        if not context or 'active_ids' not in context:
            return {'type': 'ir.actions.act_window_close'}

        lancamento_ids = context['active_ids']
        lancamento_pool = self.pool.get('finan.lancamento')

        lista_recibo = []
        partner_id = False
        tipo = ''
        complemento = ''
        #
        # Fazemos uma pré-validação das informações
        #
        for lancamento_obj in lancamento_pool.browse(cr, uid, lancamento_ids, context):
            if not partner_id:
                partner_id = lancamento_obj.partner_id.id
            elif lancamento_obj.partner_id.id != partner_id:
                raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos de clientes/fornecedores diferentes!')

            if tipo == '':
                tipo = lancamento_obj.tipo
            elif lancamento_obj.tipo != tipo:
                raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos de tipos diferentes!')

            if complemento == '':
                complemento = lancamento_obj.complemento

            elif lancamento_obj.complemento != complemento:
                raise osv.except_osv(u'Atenção', u'Não é possível realizar a operação em lançamentos com complementos diferentes!')

        rel = Report('Recibo', cr, uid)
        rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_recibo_financeiro_varios.jrxml')

        #
        # Prepara os dados
        #
        filtro = {
            'divida_ids': str(tuple(lancamento_ids)).replace(',)', ')'),
            'filtro_adicional': '',
            'valor_documento': "coalesce((select sum(coalesce(p.valor_documento, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
            'valor_juros': "coalesce((select sum(coalesce(p.valor_juros, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
            'valor_multa': "coalesce((select sum(coalesce(p.valor_multa, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
            'valor_desconto': "coalesce((select sum(coalesce(p.valor_desconto, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
            'valor': "coalesce((select sum(coalesce(p.valor_documento, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
        }

        rel_obj = self.browse(cr, uid, ids[0])

        if rel_obj.recibo_previo or tipo in ('E', 'S', 'T'):
            filtro.update({
                'valor_documento': "coalesce((select sum(coalesce(p.valor_saldo, coalesce(p.valor, 0))) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                'valor_juros': "coalesce((select sum(coalesce(p.valor_juros, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                'valor_multa': "coalesce((select sum(coalesce(p.valor_multa, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                'valor_desconto': "coalesce((select sum(coalesce(p.valor_desconto, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                'valor': "coalesce((select sum(coalesce(p.valor_saldo, coalesce(p.valor, 0))) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
            })

            sql_divida = SQL_DIVIDA.format(**filtro)
            sql_divida = sql_divida.format(**filtro)
            sql_pagamento = SQL_PAGAMENTO_PREVIO.format(**filtro)
            #print(sql_pagamento)

        else:
            if rel_obj.data_quitacao:
                filtro['filtro_adicional'] = "and l.data_quitacao = '{data_quitacao}'".format(data_quitacao=rel_obj.data_quitacao)

            sql_divida = SQL_DIVIDA.format(**filtro)
            sql_pagamento = SQL_PAGAMENTO.format(**filtro)

            if rel_obj.data_quitacao:
                filtro['filtro_adicional'] = "and p.data_quitacao = '{data_quitacao}'".format(data_quitacao=rel_obj.data_quitacao)

            sql_divida = sql_divida.format(**filtro)

        rel.parametros['SQL_DIVIDA'] = sql_divida.replace('\n', ' ')
        rel.parametros['SQL_PAGAMENTO'] = sql_pagamento.replace('\n', ' ')
        rel.parametros['COMPANY_ID'] = self.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio')

        pdf, formato = rel.execute()

        banco_de_dados = cr.dbname
        nome = 'Recibo_' + banco_de_dados + '.pdf'
        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})


    def gerar_lote_recibos_exata(self, cr, uid, ids, context=None):
        if not ids:
            return {}
        lancamento_pool = self.pool.get('finan.lancamento')

        id = ids[0]
        rel_obj = self.browse(cr, uid, id)

        sql ="""
        select distinct
            d.id
        from
            finan_lancamento lr
            join finan_lancamento d on d.id = lr.lancamento_id
        where
            d.tipo = 'R'
            and lr.tipo = 'PR'
            and
            (
                lr.data_quitacao between '{data_inicial}' and '{data_final}'
            or
                lr.data between '{data_final}' and '{data_final}'
            )
            and lr.res_partner_bank_id = {res_partner_bank_id}
        """
        sql = sql.format(res_partner_bank_id=rel_obj.res_partner_bank_id.id,data_inicial=rel_obj.data_inicial,data_final=rel_obj.data_final)
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados) == 0:
            raise osv.except_osv(u'Atenção', u'Não há dados para gerar o relatório, com base nos parâmetros informados!')

        lancamento_ids = []
        for lanc_id in dados:
            lancamento_ids.append(lanc_id[0])

        lista_recibo = []

        #
        # Fazemos uma pré-validação das informações
        #
        for lancamento_obj in lancamento_pool.browse(cr, uid, lancamento_ids, context):
            partner_id = lancamento_obj.partner_id.id
            tipo = lancamento_obj.tipo
            complemento = lancamento_obj.complemento

            rel = Report('Recibo', cr, uid)
            rel.caminho_arquivo_jasper = os.path.join(JASPER_BASE_DIR, 'exata_recibo_financeiro_varios.jrxml')

            #
            # Prepara os dados
            #
            filtro = {
                'divida_ids': '(' + str(lancamento_obj.id) + ')',
                'filtro_adicional': '',
                'valor_documento': "coalesce((select sum(coalesce(p.valor_documento, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
                'valor_juros': "coalesce((select sum(coalesce(p.valor_juros, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
                'valor_multa': "coalesce((select sum(coalesce(p.valor_multa, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
                'valor_desconto': "coalesce((select sum(coalesce(p.valor_desconto, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
                'valor': "coalesce((select sum(coalesce(p.valor_documento, 0)) from finan_lancamento p where p.lancamento_id in {divida_ids} and p.tipo in ('PP', 'PR') {filtro_adicional}), 0)",
            }

            rel_obj = self.browse(cr, uid, ids[0])

            if tipo in ('E', 'S', 'T'):
                filtro.update({
                    'valor_documento': "coalesce((select sum(coalesce(p.valor_saldo, coalesce(p.valor, 0))) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor_juros': "coalesce((select sum(coalesce(p.valor_juros, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor_multa': "coalesce((select sum(coalesce(p.valor_multa, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor_desconto': "coalesce((select sum(coalesce(p.valor_desconto, 0)) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                    'valor': "coalesce((select sum(coalesce(p.valor_saldo, coalesce(p.valor, 0))) from finan_lancamento p where p.id in {divida_ids} {filtro_adicional}), 0)",
                })

                sql_divida = SQL_DIVIDA.format(**filtro)
                sql_divida = sql_divida.format(**filtro)
                sql_pagamento = SQL_PAGAMENTO_PREVIO.format(**filtro)
            else:
                sql_divida = SQL_DIVIDA.format(**filtro)
                sql_pagamento = SQL_PAGAMENTO.format(**filtro)
                sql_divida = sql_divida.format(**filtro)

            rel.parametros['SQL_DIVIDA'] = sql_divida.replace('\n', ' ')
            rel.parametros['SQL_PAGAMENTO'] = sql_pagamento.replace('\n', ' ')
            rel.parametros['COMPANY_ID'] = self.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio')

            pdf, formato = rel.execute()
            lista_recibo.append(pdf)

        #pdf_unico = PdfFileWriter()
        pdf_unico = PdfFileMerger()

        #
        # Monta o PDF com os recibos
        #
        for recibo in lista_recibo:
            arq_pdf_recibos = StringIO()
            arq_pdf_recibos.write(recibo)
            pdf_unico.append(PdfFileReader(arq_pdf_recibos))

        #
        # Gera 1 PDF com tudo junto
        #
        arq_pdf = StringIO()
        pdf_unico.write(arq_pdf)
        arq_pdf.seek(0)
        pdf = arq_pdf.read()
        arq_pdf_recibos.close()
        arq_pdf.close()


        banco_de_dados = cr.dbname
        nome = 'Lote_Recibos_' + banco_de_dados + '.pdf'
        self.write(cr, uid, ids, {'nome': nome, 'arquivo': base64.encodestring(pdf)})


finan_recibos()
