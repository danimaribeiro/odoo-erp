# -*- coding: utf-8 -*-


#from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from pybrasil.valor.decimal import Decimal as D
import base64
from StringIO import StringIO
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.data import parse_datetime, horario_decimal_to_hora_decimal



class stock_move(orm.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    #def _data_hora(self, cr, uid, ids, nome_campo, args=None, context={}):
        #res = {}

        #for id in ids:
            #sql = """
            #select
                #sm.date at time zone 'UTC' at time zone 'America/Sao_Paulo'

            #from
                #stock_move sm

            #where
                #sm.id = {id};
            #"""
            #sql = sql.format(id=id)
            #cr.execute(sql)
            #dados = cr.fetchall()

            #res[id] = False
            #if len(dados):
                #data = parse_datetime(dados[0][0])

                #if nome_campo == 'data':
                    #res[id] = str(data)[:10]
                #else:
                    #res[id] = horario_decimal_to_hora_decimal(data)

        #return res

    _columns = {
        'importado': fields.boolean(u'Importado'),
        'finan_contrato_id': fields.many2one('finan.contrato', u'Contrato', ondelete='cascade'),
        'nota_retorno': fields.char(u'Nº NF de origem nossa (em caso de NF de retorno)', size=30),
        'nota_origem': fields.char(u'NF origem', size=30),
        #'data': fields.function(_data_hora, type='date', string=u'Data'),
        #'hora': fields.function(_data_hora, type='float', string=u'Hora'),
        'cnpj': fields.char(u'CNPJ (emissor do documento)', size=18),
    }

    def onchange_product_id_inventario_cliente(self, cr, uid, ids,  prod_id=False, loc_id=False, loc_dest_id=False, address_id=False, data=False, company_id=False, context={}):
        move_pool = self.pool.get('stock.move')
        location_pool = self.pool.get('stock.location')
        location_ids = location_pool.search(cr, uid, [('padrao_locacao', '=', True)])
        local_locacao_id = location_ids[0]

        res = move_pool.onchange_product_id(cr, uid, ids, prod_id=prod_id, loc_id=loc_id, loc_dest_id=loc_dest_id, address_id=address_id)

        sql = """
        select
            cm.quantidade,
            cm.vr_unitario_custo,
            cm.vr_total
        from custo_medio({company_id}, {local_id}, {produto_id}) cm
        where
            cm.data <= '{data_final}'
        order by
            cm.data desc, cm.entrada_saida desc, cm.move_id desc limit 1;
        """
        filtro = {
            'data_final': data,
            'company_id': company_id,
            'local_id': local_locacao_id,
            'produto_id': prod_id,
        }
        sql = sql.format(**filtro)
        print(sql)
        cr.execute(sql)
        dados = cr.fetchall()

        if len(dados):
            res['value']['price_unit'] = dados[0][1]
            print(res['value'])

        return res

    def onchange_cnpj(self, cr, uid, ids, cnpj_cpf, context={}):
        if not cnpj_cpf:
            return {}

        if not valida_cnpj(cnpj_cpf):
            raise osv.except_osv(u'Erro!', u'CNPJ inválido!')

        cnpj_cpf = limpa_formatacao(cnpj_cpf)

        if len(cnpj_cpf) == 14:
            cnpj_cpf = formata_cnpj(cnpj_cpf)

        return {'value': {'cnpj': cnpj_cpf}}

    def create(self, cr, uid, dados, context={}):
        if 'cnpj' in dados and dados['cnpj']:
            cnpj_cpf = limpa_formatacao(dados['cnpj'])

            if not valida_cnpj(cnpj_cpf):
                raise osv.except_osv(u'Erro!', u'CNPJ inválido!')

            dados['cnpj'] = formata_cnpj(cnpj_cpf)

        return super(stock_move, self).create(cr, uid, dados, context)

    def write(self, cr, uid, ids, dados, context={}):
        if 'cnpj' in dados and dados['cnpj']:
            cnpj_cpf = limpa_formatacao(dados['cnpj'])

            if not valida_cnpj(cnpj_cpf):
                raise osv.except_osv(u'Erro!', u'CNPJ inválido!')

            dados['cnpj'] = formata_cnpj(cnpj_cpf)

        return super(stock_move, self).write(cr, uid, ids, dados, context)


stock_move()


class finan_contrato(orm.Model):
    _name = 'finan.contrato'
    _inherit = 'finan.contrato'

    _columns = {
        'stock_move_ids': fields.one2many('stock.move', 'finan_contrato_id', u'Movimentos de estoque'),
        'nome_csv': fields.char(u'Nome do arquivo CSV', 120),
        'arquivo_csv': fields.binary(u'Arquivo CSV'),
        'texto_csv': fields.text(u'Arquivo CSV'),
    }

    def write(self, cr, uid, ids, dados, context={}):
        if 'texto_csv' in dados and dados['texto_csv']:
            dados['texto_csv'] = dados['texto_csv'].replace('\t|', '|').replace('|\t', '|')
            dados['arquivo_csv'] = base64.encodestring(dados['texto_csv'].encode('utf-8'))

        elif 'arquivo_csv' in dados and dados['arquivo_csv']:
            dados['texto_csv'] = base64.decodestring(dados['arquivo_csv']).encode('utf-8')

        res = super(finan_contrato, self).write(cr, uid, ids, dados, context=context)

        #for contrato_obj in self.pool.get('finan.contrato').browse(cr, uid, ids):
            #contrato_obj.write({'texto_csv': contrato_obj.arquivo_csv})

        return res

    def importar_arquivo_inventario(self, cr, uid, ids, context={}):
        company_pool = self.pool.get('res.company')
        produto_pool = self.pool.get('product.product')
        operacao_pool = self.pool.get('stock.operacao')
        move_pool = self.pool.get('stock.move')

        for contrato_obj in self.browse(cr, uid, ids):
            sql = """
            delete from stock_move where finan_contrato_id = {contrato_id} and importado = True;
            """
            sql = sql.format(contrato_id=contrato_obj.id)
            cr.execute(sql)

            arquivo_csv = StringIO()
            arquivo_csv.write(contrato_obj.texto_csv)
            arquivo_csv.seek(0)

            for linha in arquivo_csv.readlines():
                if linha[0] != '2':
                    continue

                if '|' not in linha:
                    continue

                linha = linha.replace('|\n', '')
                linha = linha.replace('\n', '')

                print(linha)
                print(linha.split('|'))
                data, origem, operacao, cnpj, produto, quantidade, unitario, retorno = linha.split('|')

                data = data.strip()
                origem = origem.strip()
                operacao = operacao.strip()
                cnpj = cnpj.strip()
                produto = produto.strip()
                quantidade = quantidade.strip()
                quantidade = D(quantidade or 0)

                if quantidade <= 0:
                    continue

                unitario = unitario.strip()
                unitario = D(unitario or 0)
                retorno = retorno.strip()

                company_ids = company_pool.search(cr, uid, [('cnpj_cpf', '=', cnpj)], limit=1)
                if not company_ids:
                    raise osv.except_osv(u'Erro', u'Empresa com CNPJ {cnpj} não foi encontrada!'.format(cnpj=cnpj))
                company_id = company_ids[0]

                operacao_ids = operacao_pool.search(cr, uid, [('nome', 'ilike', operacao)], limit=1)
                if not operacao_ids:
                    raise osv.except_osv(u'Erro', u'Operação código {operacao} não foi encontrada!'.format(operacao=operacao))
                operacao_id = operacao_ids[0]

                produto_ids = produto_pool.search(cr, uid, [('default_code', '=', produto)], limit=1)
                if not produto_ids:
                    raise osv.except_osv(u'Erro', u'Produto código {produto} não foi encontrado!'.format(produto=produto))
                produto_id = produto_ids[0]

                dados = {
                    'importado': True,
                    'finan_contrato_id': contrato_obj.id,
                    'date': data,
                    'company_id': company_id,
                    'operacao_id': operacao_id,
                    'product_id': produto_id,
                    'product_qty': quantidade,
                    'nota_origem': origem,
                    'nota_retorno': retorno,
                }

                dados_operacao = move_pool.onchange_operacao_id(cr, uid, False, operacao_id, company_id)
                dados.update(dados_operacao['value'])

                dados_produto = move_pool.onchange_product_id_inventario_cliente(cr, uid, False, produto_id, dados['location_id'], dados['location_dest_id'], False, data, company_id)
                dados.update(dados_produto['value'])

                if unitario > 0:
                    dados['price_unit'] = unitario

                move_id = move_pool.create(cr, uid, dados)
                #move_pool.write(cr, uid, [move_id], dados)
                #print(dados)


        return True


finan_contrato()


class finan_contrato_inventario(orm.Model):
    _name = 'finan.contrato_inventario'
    _inherit = 'finan.contrato_inventario'

    def _custo_locacao_atual(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for inventario_obj in self.browse(cr, uid, ids):
            res[inventario_obj.id] = False

            sql = """
                select
                    coalesce((
                        select
                            cm.vr_unitario_custo
                        from
                            custo_medio(5, 27, {produto_id}) cm
                        where
                            cm.data <= current_date
                        order by
                            cm.data desc, cm.entrada_saida desc, cm.move_id desc
                        limit 1), 0) as custo_medio,
                    t.standard_price

                from
                    product_product p
                    join product_template t on t.id = p.product_tmpl_id

                where
                    p.id = {produto_id};
            """
            sql = sql.format(produto_id=inventario_obj.product_id.id)
            cr.execute(sql)
            dados = cr.fetchall()

            if len(dados):
                vr_unitario = D(dados[0][0] or 0)

                if vr_unitario <= 0:
                    vr_unitario = D(dados[0][1] or 0)

                res[inventario_obj.id] = vr_unitario

                if nome_campo == 'vr_custo_atual':
                    if D(inventario_obj.quantidade or 0) > 0:
                        res[inventario_obj.id] = vr_unitario * D(inventario_obj.quantidade or 0)
                    else:
                        res[inventario_obj.id] = D(0)

        return res

    _columns = {
        'vr_unitario_custo_atual': fields.function(_custo_locacao_atual, type='float', string=u'Custo unitário atual', store=True, select=True),
        'vr_custo_atual': fields.function(_custo_locacao_atual, type='float', string=u'Custo atual',  store=True, select=True),
    }


finan_contrato_inventario()
