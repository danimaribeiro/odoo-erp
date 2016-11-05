# -*- coding: utf-8 -*-


from osv import osv, fields
from StringIO import StringIO
from pybrasil.valor.decimal import Decimal as D, ROUND_DOWN
from pybrasil.inscricao import limpa_formatacao
from pybrasil.base import DicionarioBrasil, dicionario_para_xml, xml_para_dicionario, UnicodeBrasil, tira_acentos
from pybrasil.data import formata_data


class const_imovel(osv.Model):
    _name = b'const.imovel'
    _inherit = b'const.imovel'    
    
    def gera_xml_beview(self, cr, uid, ids, context={}):
        
        imoveis = DicionarioBrasil()
        imoveis['imoveis'] = []
        
        for imovel_obj in self.browse(cr, uid, ids):
            
            imovel = DicionarioBrasil()
            imovel['imovel'] = DicionarioBrasil()

            imovel.imovel['referencia'] = str(imovel_obj.id) 
            imovel.imovel['titulo'] = imovel_obj.descricao
            imovel.imovel['descricao'] = imovel_obj.descricao   
                     
            if imovel_obj.tipo == 'C':
                imovel.imovel['tipo'] = 'Casa'                
            elif imovel_obj.tipo == 'A':
                imovel.imovel['tipo'] = 'Apartamento'            
            elif imovel_obj.tipo == 'T':
                imovel.imovel['tipo'] = 'Terreno'
            elif imovel_obj.tipo == 'X':
                imovel.imovel['tipo'] = u'Chácara/sítio'
            elif imovel_obj.tipo == 'F':
                imovel.imovel['tipo'] = u'Fazenda/área de terras'
            elif imovel_obj.tipo == 'G':
                imovel.imovel['tipo'] = u'Galpão/pavilhão'
            elif imovel_obj.tipo == 'P':
                imovel.imovel['tipo'] = u'Prédio'
            elif imovel_obj.tipo == 'S':
                imovel.imovel['tipo'] = 'Sala comercial'            
            elif imovel_obj.tipo == 'L':
                imovel.imovel['tipo'] = 'Loja/ponto comercial'
            else:
                imovel.imovel['tipo'] = 'Outros'

            if imovel_obj.situacao == 'D':
                imovel.imovel['categoria'] = u'Disponível'
            elif imovel_obj.situacao == 'R':
                imovel.imovel['categoria'] = 'Reservado'
            elif imovel_obj.situacao == 'C':
                imovel['categoria'] = 'Cancelado'
            elif imovel_obj.situacao == 'V':
                imovel.imovel['categoria'] = 'Vendido'
            elif imovel_obj.situacao == 'A':
                imovel.imovel['categoria'] = 'Alugado'
            elif imovel_obj.situacao == 'ND':
                imovel.imovel['categoria'] = u'Não disponível'
            else:
                imovel.imovel['categoria'] = u'Não liberado'
                
            imovel.imovel['destaque'] = False
            imovel.imovel['valor_venda'] = D(str(imovel_obj.valor_venda)).quantize(D('0'))
            imovel.imovel['valor_iptu'] = 0            
            imovel.imovel['valor_condominio'] = D(str(imovel_obj.valor_condominio)).quantize(D('0.01'))
            imovel.imovel['area_total'] = D(str(imovel_obj.area_total)).quantize(D('0.01'))
            imovel.imovel['area_util'] = D(str(imovel_obj.area_util)).quantize(D('0.01'))
            imovel.imovel['suites'] = str(imovel_obj.suite)
            imovel.imovel['quartos'] = str(imovel_obj.quarto)
            imovel.imovel['cep'] = imovel_obj.cep
            imovel.imovel['uf'] = imovel_obj.municipio_id.estado
            imovel.imovel['cidade'] = imovel_obj.municipio_id.nome
            imovel.imovel['bairro'] = imovel_obj.bairro
            imovel.imovel['tipo_logradouro'] = ''
            imovel.imovel['logradouro'] = imovel_obj.endereco
            imovel.imovel['numero'] = str(imovel_obj.numero)
            imovel.imovel['complemento'] = str(imovel_obj.complemento)
            imovel.imovel['latitude'] = ''
            imovel.imovel['longitude'] = ''
            imovel.imovel['obra_inicio'] = ''
            imovel.imovel['obra_termino'] = ''
            imovel.imovel['obra_fundacoes'] = ''
            imovel.imovel['obra_estrutura_concreto'] = ''
            imovel.imovel['obra_alvenaria'] = ''
            imovel.imovel['obra_instalacoes'] = ''
            imovel.imovel['obra_revestimento_externo'] = ''
            imovel.imovel['obra_revestimento_interno'] = ''
            imovel.imovel['obra_acabamentos'] = ''
            imovel.imovel['obra_detalhes'] = ''
            imovel.imovel['informacoes_restritas'] = ''
            imovel.imovel['data'] = formata_data(imovel_obj.create_date)
            imovel.imovel['website'] = ''
            imovel.imovel['url_youtube'] = ''
            imovel.imovel['chaves'] = ''            
            
            #imovel['arquivos'] = []            
            #arquivo = DicionarioBrasil()
            #arquivo['url'] = '' #STRING, url para efetuar o download da imagem. Ex: http://www.beview.com.br/minhaimagem.jpg
            #arquivo['titulo'] = '' 
            #arquivo['tipo'] = ''
            #arquivo['ordem'] = ''
            #arquivo['categoria'] = ''
            #arquivo['principal'] = ''
            #imovel.arquivos.append(arquivo) 
            
            imovel_convertido = imovel.como_xml_em_texto                 
            imoveis.imoveis.append(imovel_convertido)
            print(imoveis.como_xml_em_texto)             
            
        
        arquivo_xml = imoveis.como_xml_em_texto
        open('/home/william/xml_beview.xml', 'wb').write(arquivo_xml.encode('utf-8'))    
        
        
            
const_imovel()