# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import osv, fields
import base64
import StringIO
import zipfile
from sped.constante_tributaria import *
from pybrasil.inscricao import limpa_formatacao
from pybrasil.data import mes_passado, primeiro_dia_mes, ultimo_dia_mes
from pybrasil.data import parse_datetime, formata_data, agora, hoje


class zip_xml(osv.Model):
    _description = u'Exportação XML'
    _name = 'zip_xml'
    _rec_name = 'nome'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for exp_obj in self.browse(cr, uid, ids):
            res[exp_obj.id] = exp_obj.id

        return res


    _columns = {
        'data_inicial': fields.date(u'Data inicial'),
        'data_final': fields.date(u'Data final'),
        'company_id': fields.many2one('res.company', u'Empresa'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'codigo': fields.function(_codigo, type='integer', method=True, string=u'Código', store=False, select=True),
        'emissao': fields.selection(TIPO_EMISSAO, u'Tipo de emissão'),
        'modelo_fiscal': fields.selection(MODELO_FISCAL, u'Modelo Fiscal'),
    }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'finan.relatorio', context=c),
        'data_inicial': lambda *args, **kwargs: str(primeiro_dia_mes(mes_passado())),
        'data_final': lambda *args, **kwargs: str(ultimo_dia_mes(mes_passado())),
        'emissao': '0',
        'modelo_fiscal': '55',
    }


    def gera_exportacao(self, cr, uid, ids, context={}):
        if not ids:
            return {}

        for export_obj in self.browse(cr, uid, ids):

            sql = u"""
            select
                sd.id
            from
                     sped_documento sd
                join res_company c on c.id = sd.company_id
                join res_partner rp on rp.id = c.partner_id

            where
                    sd.data_emissao_brasilia between '{data_inicial}' and '{data_final}'
                and c.cnpj_cpf = '{cnpj_cpf}'
                and sd.emissao = '{emissao}'
                and sd.modelo = '{modelo}'

            order by
                c.name,
                sd.data_emissao_brasilia,
                sd.numero;
            """

            filtro = {
                'data_inicial': export_obj.data_inicial,
                'data_final': export_obj.data_final,
                'cnpj_cpf': export_obj.company_id.cnpj_cpf,
                'emissao': export_obj.emissao,
                'modelo': export_obj.modelo_fiscal,
            }

            cr.execute(sql.format(**filtro))

            dados = cr.fetchall()

            if not dados:
                raise osv.except_osv(u'Erro!', u'Não existem documentos nos parâmetros informados!')

            documento_ids = []
            for doc_id, in dados:
                documento_ids.append(doc_id)

            sql_anexos = u"""
            select
                anexo.id
            from
                ir_attachment anexo
            where
                    anexo.res_model = 'sped.documento'
                and anexo.res_id in {doc_ids}
                and (
                    anexo.name like '%-can.xml'
                    or anexo.name like '%-nfe.xml'
                )
            """

            cr.execute(sql_anexos.format(doc_ids=str(tuple(documento_ids)).replace(',)', ')')))

            dados = cr.fetchall()

            if not len(dados):
                raise osv.except_osv(u'Erro!', u'Não existem xmls de documentos nos parâmetros informados!')

            arqzipmemoria = StringIO.StringIO()
            arqzip = zipfile.ZipFile(arqzipmemoria, 'w', zipfile.ZIP_DEFLATED)

            anexo_ids = []
            for anexo_id, in dados:
                anexo_ids.append(anexo_id)

            for anexo_obj in self.pool.get('ir.attachment').browse(cr, 1, anexo_ids):
                xml = anexo_obj.datas
                xml = base64.decodestring(xml)
                arqzip.writestr(anexo_obj.name, xml)

            arqzip.close()
            conteudo_zip = arqzipmemoria.getvalue()
            arqzipmemoria.close()

            nome_arquivo = limpa_formatacao(export_obj.company_id.cnpj_cpf) + '_'
            nome_arquivo += export_obj.data_inicial + '_'
            nome_arquivo += export_obj.data_final + '_'
            nome_arquivo += 'xml.zip'

            dados = {
                'nome': nome_arquivo,
                'arquivo': base64.encodestring(conteudo_zip),
            }
            export_obj.write(dados)


zip_xml()
