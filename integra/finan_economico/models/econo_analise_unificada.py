# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import orm, fields, osv
from pybrasil.valor.decimal import Decimal as D
from datetime import datetime
from pybrasil.data import parse_datetime, formata_data
from collections import OrderedDict
import base64
from StringIO import StringIO
import csv


class econo_analise_unificada(orm.Model):
    _name = 'econo.analise.unificada'
    _description = u'Análise econômica unificada'
    _order = 'descricao'

    _columns = {
        'descricao': fields.char(u'Descrição', size=120, select=True),
        'analise_ids': fields.many2many('econo.analise', 'econo_analise_unificada_analise', 'unificada_id', 'analise_id', u'Períodos'),
        'data': fields.datetime(u'Data de geração'),
        'nome': fields.char(u'Nome do arquivo', 120, readonly=True),
        'arquivo': fields.binary(u'Arquivo', readonly=True),
        'arquivo_texto': fields.text(u'Arquivo'),
    }

    def gera_analise(self, cr, uid, ids, context={}):
        if not ids:
            return
        
        conta_pool = self.pool.get('econo.conta')

        for unificada_obj in self.browse(cr, uid, ids):
            #
            # Criamos o dicionário com as contas, na ordem correta
            #
            unificado = OrderedDict()
            
            for conta_id in conta_pool.search(cr, uid, [], order='codigo_completo'):
                econo_conta_obj = conta_pool.browse(cr, uid, conta_id)
            
                unificado[econo_conta_obj.codigo_completo] = {
                    'codigo': econo_conta_obj.codigo_completo,
                    'descricao': econo_conta_obj.nome,
                }
                
            #
            # Acumulamos agora o valor correspondente a cada mês
            #
            meses = []
            titulo_meses = {}
            formato = csv.excel()
            formato.delimiter = ';'
            
            for analise_obj in unificada_obj.analise_ids:
                data = parse_datetime(analise_obj.data_inicial) 
                mes = formata_data(data, '%Y%m')
                titulo_mes = formata_data(data, '%b/%Y')
                
                #print(mes)
                
                if mes not in meses:
                    meses.append(mes)
                    titulo_meses[mes] = titulo_mes
                
                #valor_mes = 'VALOR_' + mes
                valor_liquido_mes = titulo_mes
             
                arquivo = StringIO()
                arquivo.write(analise_obj.arquivo_texto.encode('utf-8'))
                arquivo.seek(0)
                
                arquivo_csv = csv.DictReader(arquivo, dialect=formato)
                
                for linha in arquivo_csv:
                    codigo = linha[u'CÓDIGO'.encode('utf-8')]
                    
                    if codigo == 'BANCO':
                        continue
                    
                    descricao = linha[u'DESCRIÇÃO'.encode('utf-8')]
                    valor = linha[u'VALOR']
                    valor_liquido = linha[u'VALOR_LIQUIDO']
                    
                    #print(codigo, valor_liquido)
                    
                    if valor is None:
                        valor = D(0)
                    else:
                        valor = D(valor.replace(',', '.') or 0)
                        
                    if valor_liquido is None:
                        valor_liquido = D(0)
                    elif ' ' in valor_liquido:
                        valor_liquido = valor
                    else:
                        valor_liquido = D(valor_liquido.replace(',', '.') or 0)
                    
                    if codigo not in unificado:
                        unificado[codigo] = {
                            'codigo': codigo.decode('utf-8'),
                            'descricao': descricao.decode('utf-8'),
                        }
                        
                    #if valor_mes not in unificado[codigo]:
                        #unificado[codigo][valor_mes] = D(0)
                        
                    if valor_liquido_mes not in unificado[codigo]:
                        unificado[codigo][valor_liquido_mes] = D(0)
                        
                    #unificado[codigo][valor_mes] += valor
                    unificado[codigo][valor_liquido_mes] += valor_liquido
                    
                arquivo.close()
                        
            #
            # Agora, montamos o CSV unificado, corrigindo os números para o formato em português
            #
            campos = [
                'codigo',
                'descricao',
            ]
            meses.sort()
            for mes in meses:
                campos.append(titulo_meses[mes])
                
            arquivo = StringIO()
            arquivo_csv = csv.DictWriter(arquivo, fieldnames=campos, dialect=formato)
            
            for codigo in unificado:
                linha = unificado[codigo]
                
                #
                # Ajusta os valores decimais
                #
                for chave in linha:
                    if isinstance(linha[chave], D):
                        linha[chave] = str(linha[chave]).replace('.', ',')
                    elif isinstance(linha[chave], unicode):
                        linha[chave] = linha[chave].encode('utf-8')
                        
                arquivo_csv.writerow(linha)
                
            arquivo.seek(0)
            
            arquivo = arquivo.read()
            arquivo = arquivo.decode('utf-8')
            
            dados_analise = {
                'data': str(datetime.now())[:19],
                'arquivo_texto': arquivo.encode('utf-8'),
                'nome': 'analise_economica.csv',
                'arquivo': base64.encodestring(arquivo.encode('iso-8859-1')),
            }
            unificada_obj.write(dados_analise)


econo_analise_unificada()
