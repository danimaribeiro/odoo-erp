# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.base import mascara


LOGRADOURO_ABREVIADO = {
    '10ª Rua': '10ª-R',
    '10ª Travessa': '10ª-Tv',
    '11ª Rua': '11ª-R',
    '11ª Travessa': '11ª-Tv',
    '12ª Rua': '12ª-R',
    '12ª Travessa': '12ª-Tv',
    '13ª Travessa': '13ª-Tv',
    '14ª Travessa': '14ª-Tv',
    '15ª Travessa': '15ª-Tv',
    '16ª Travessa': '16ª-Tv',
    '17ª Travessa': '17ª-Tv',
    '18ª Travessa': '18ª-Tv',
    '19ª Travessa': '19ª-Tv',
    '1ª Avenida': '1ª-Av',
    '1ª Paralela': '1ª-Par',
    '1ª Rua': '1ª-R',
    '1ª Subida': '1ª-Sub',
    '1ª Travessa': '1ª-Tv',
    '1ª Travessa da Rodovia': '1ª-Tv-Rod',
    '1ª Vila': '1ª-Vl',
    '1º Alto': '1º-At',
    '1º Beco': '1º-Bc',
    '20ª Travessa': '20ª-Tv',
    '21ª Travessa': '21ª-Tv',
    '22ª Travessa': '22ª-Tv',
    '2ª Avenida': '2ª-Av',
    '2ª Ladeira': '2ª-Ld',
    '2ª Paralela': '2ª-Par',
    '2ª Rua': '2ª-R',
    '2ª Subida': '2ª-Sub',
    '2ª Travessa': '2ª-Tv',
    '2ª Travessa da Rodovia': '2ª-Tv-Rod',
    '2ª Vila': '2ª-Vl',
    '2º Alto': '2º-At',
    '2º Beco': '2º-Bc',
    '3ª Avenida': '3ª-Av',
    '3ª Ladeira': '3ª-Ld',
    '3ª Paralela': '3ª-Par',
    '3ª Rua': '3ª-R',
    '3ª Subida': '3ª-Sub',
    '3ª Travessa': '3ª-Tv',
    '3ª Vila': '3ª-Vl',
    '3º Alto': '3º-At',
    '3º Beco': '3º-Bc',
    '4ª Avenida': '4ª-Av',
    '4ª Paralela': '4ª-Par',
    '4ª Rua': '4ª-R',
    '4ª Subida': '4ª-Sub',
    '4ª Travessa': '4ª-Tv',
    '4ª Vila': '4ª-Vl',
    '5ª Avenida': '5ª-Av',
    '5ª Rua': '5ª-R',
    '5ª Subida': '5ª-Sub',
    '5ª Travessa': '5ª-Tv',
    '5ª Vila': '5ª-Vl',
    '6ª Avenida': '6ª-Av',
    '6ª Rua': '6ª-R',
    '6ª Subida': '6ª-Sub',
    '6ª Travessa': '6ª-Tv',
    '7ª Rua': '7ª-R',
    '7ª Travessa': '7ª-Tv',
    '8ª Travessa': '8ª-Tv',
    '9ª Rua': '9ª-R',
    '9ª Travessa': '9ª-Tv',
    'Acampamento': 'Acamp',
    'Acesso': 'Ac',
    'Acesso Local': 'Ac-Loc',
    'Adro': 'Ad',
    'Aeroporto': 'Aer',
    'Alameda': 'Al',
    'Alto': 'At',
    'Anel Viário': 'An-Vr',
    'Antiga Estação': 'Ant-Etç',
    'Antiga Estrada': 'Ant-Est',
    'Área': 'Á',
    'Área Especial': 'Á-Esp',
    'Área Verde': 'Á-Ver',
    'Artéria': 'Art',
    'Atalho': 'Atl',
    'Avenida': 'Av',
    'Avenida Contorno': 'Av-Cont',
    'Avenida Marginal': 'Av-Marg',
    'Avenida Marginal Direita': 'Av-Marg-Dir',
    'Avenida Marginal Esquerda': 'Av-Marg-Esq',
    'Avenida Marginal Norte': 'Av-Marg-Nor',
    'Avenida Perimetral': 'Av-Per',
    'Baixa': 'Bx',
    'Balão': 'Blo',
    'Beco': 'Bc',
    'Belvedere': 'Belv',
    'Bloco': 'Bl',
    'Blocos': 'Bls',
    'Bosque': 'Bsq',
    'Bulevar': 'Blv',
    'Buraco': 'Bco',
    'Cais': 'C',
    'Calçada': 'Calç',
    'Calçadão': 'Clção',
    'Caminho': 'Cam',
    'Caminho de Servidão': 'Cam-Srv',
    'Campo': 'Cpo',
    'Campus': 'Cpus',
    'Canal': 'Can',
    'Chácara': 'Chác',
    'Ciclovia': 'Ciclv',
    'Circular': 'Cir',
    'Colônia': 'Col',
    'Complexo Viário': 'Cmp-Vr',
    'Comunidade': 'Cdd',
    'Condomínio': 'Cond',
    'Condomínio Residencial': 'Cond-Res',
    'Conjunto': 'Cj',
    'Conjunto Habitacional': 'Cj-Hab',
    'Conjunto Mutirão': 'Cj-Mut',
    'Conjunto Residencial': 'Cj-Res',
    'Contorno': 'Cnt',
    'Corredor': 'Cor',
    'Córrego': 'Crg',
    'Descida': 'Dsc',
    'Desvio': 'Dsv',
    'Distrito': 'Dt',
    'Eixo': 'Eix',
    'Eixo Industrial': 'Eix-Ind',
    'Eixo Principal': 'Eix-Prin',
    'Elevada': 'Evd',
    'Entrada Particular': 'Ent-Part',
    'Entre Quadra': 'E-Q',
    'Escada': 'Esc',
    'Escada de Pedra': 'Esc-Pdr',
    'Escadaria': 'Escia',
    'Esplanada': 'Esp',
    'Estação': 'Etç',
    'Estacionamento': 'Estc',
    'Estádio': 'Etd',
    'Estrada': 'Est',
    'Estrada Antiga': 'Est-Ant',
    'Estrada de Ferro': 'Est-Fer',
    'Estrada de Ligação': 'Est-Lig',
    'Estrada de Servidão': 'Est-Srv',
    'Estrada Estadual': 'Est-Estal',
    'Estrada Intermunicipal': 'Est-Interm',
    'Estrada Municipal': 'Est-Mun',
    'Estrada Nova': 'Est-Nova',
    'Estrada Particular': 'Est-Part',
    'Estrada Velha': 'Est-Velha',
    'Estrada Vicinal': 'Est-Vici',
    'Favela': 'Fav',
    'Fazenda': 'Faz',
    'Feira': 'Fra',
    'Ferrovia': 'Fer',
    'Fonte': 'Fnt',
    'Forte': 'Fte',
    'Galeria': 'Gal',
    'Gleba': 'Glb',
    'Granja': 'Gja',
    'Ilha': 'Ia',
    'Jardim': 'Jd',
    'Jardim Residencial': 'Jd-Res',
    'Jardinete': 'Jde',
    'Ladeira': 'Ld',
    'Lago': 'Lg',
    'Lagoa': 'Lga',
    'Largo': 'Lrg',
    'Loteamento': 'Lot',
    'Margem': 'Mrg',
    'Marginal': 'Marg',
    'Mercado': 'Mrc',
    'Módulo': 'Mód',
    'Monte': 'Mte',
    'Morro': 'Mro',
    'Nova Avenida': 'Nova-Av',
    'Núcleo': 'Núc',
    'Núcleo Habitacional': 'Núc-Hab',
    'Núcleo Rural': 'Núc-Rur',
    'Outeiro': 'Out',
    'Parada': 'Pda',
    'Paralela': 'Par',
    'Parque': 'Pq',
    'Parque Municipal': 'Pq-Mun',
    'Parque Residencial': 'Pq-Res',
    'Passagem': 'Psg',
    'Passagem de Pedestres': 'Psg-Ped',
    'Passagem Subterrânea': 'Psg-Subt',
    'Passarela': 'Psa',
    'Passeio': 'Pas',
    'Passeio Público': 'Pas-Púb',
    'Pátio': 'Pát',
    'Ponta': 'Pnt',
    'Ponte': 'Pte',
    'Porto': 'Pto',
    'Praça': 'Pç',
    'Praça de Esportes': 'Pç-Esp',
    'Praia': 'Pr',
    'Prolongamento': 'Prl',
    'Quadra': 'Qd',
    'Quinta': 'Qt',
    'Ramal': 'Ram',
    'Rampa': 'Rmp',
    'Recanto': 'Rec',
    'Residencial': 'Res',
    'Reta': 'Ret',
    'Retiro': 'Rtr',
    'Retorno': 'Rtn',
    'Rodo Anel': 'Rod-An',
    'Rodovia': 'Rod',
    'Rotatória': 'Rtt',
    'Rótula': 'Rót',
    'Rua': 'R',
    'Rua de Ligação': 'R-Lig',
    'Rua de Pedestre': 'R-Ped',
    'Rua Particular': 'R-Part',
    'Rua Principal': 'R-Prin',
    'Rua Projetada': 'R-Proj',
    'Rua Velha': 'R-Velha',
    'Rua Vicinal': 'R-Vici',
    'Ruela': 'Rla',
    'Servidão': 'Srv',
    'Servidão de Passagem': 'Srv-Psg',
    'Setor': 'St',
    'Sítio': 'Sít',
    'Subida': 'Sub',
    'Terminal': 'Ter',
    'Travessa': 'Tv',
    'Travessa Particular': 'Tv-Part',
    'Trecho': 'Tr',
    'Trevo': 'Trv',
    'Trincheira': 'Tch',
    'Túnel': 'Tún',
    'Unidade': 'Unid',
    'Vala': 'Val',
    'Vale': 'Vle',
    'Variante da Estrada': 'Vrte-Est',
    'Vereda': 'Ver',
    'Via': 'V',
    'Via Coletora': 'V-Col',
    'Via Costeira': 'V-Cost',
    'Via de Acesso': 'V-Ac',
    'Via de Pedestre': 'V-Ped',
    'Via de Pedestres': 'V-Peds',
    'Via Expressa': 'V-Exp',
    'Via Lateral': 'V-Lat',
    'Via Litorânea': 'V-Lit',
    'Via Local': 'V-Loc',
    'Via Marginal': 'V-Marg',
    'Via Pedestre': 'V-Ped',
    'Via Principal': 'V-Prin',
    'Viaduto': 'Vd',
    'Viela': 'Vla',
    'Vila': 'Vl',
    'Zigue-zague': 'Zig-zag',
}


class res_cep(osv.Model):
    _name = 'res.cep'
    _order = 'cep'
    _rec_name = 'descricao'

    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, user_id, ids):
            txt = registro.cep
            txt += ' - '
            txt += registro.endereco.strip()

            if registro.complemento:
                txt += '-'
                txt += registro.complemento.strip()

            txt += ' - '
            txt += registro.bairro
            txt += ' - '
            txt += registro.cidade
            txt += '-'
            txt += registro.estado

            retorno[registro.id] = txt

        return retorno

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []

        res = []
        for cep_obj in self.browse(cr, uid, ids):
            res.append((cep_obj.id, cep_obj.descricao))

        return res

    def name_search(self, cr, uid, texto, args=[], operator='ilike', context={}, limit=100):
        if texto and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                texto = texto.strip().replace(' ', '%')

            ids = self.search(cr, uid, [
                '|', '|', '|', '|',
                ('cep', 'ilike', mascara(texto, u'     -   ')),
                ('endereco', 'ilike', texto),
                ('bairro', 'ilike', texto),
                ('cidade', 'ilike', texto),
                ('estado', 'ilike', texto),
                ] + args, limit=limit, context=context)

        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)

        result = self.name_get(cr, uid, ids, context=context)

        return result

    _columns = {
        'descricao': fields.function(_descricao, type='char', size=300, store=False, select=True),
        'cep': fields.char('CEP', size=9, select=True),
        'municipio_id': fields.many2one('sped.municipio', u'Município', ondelete='restrict'),
        'cidade': fields.related('municipio_id', 'nome', type='char', string=u'Município', store=True),
        'estado': fields.related('municipio_id', 'estado', type='char', string=u'Estado', store=True),
        'endereco': fields.char(u'Endereço', size=60),
        'bairro': fields.char(u'Bairro', size=60),
        'complemento': fields.char(u'Complemento', size=60),
    }

    def create(self, cr, uid, dados, context={}):
        if 'cep' in dados and dados['cep']:
            cep = dados['cep']

            cep = limpa_formatacao(cep)
            if not cep.isdigit() or len(cep) != 8:
                raise osv.except_osv(u'Erro!', u'CEP inválido!')

            dados['cep'] = cep[:5] + '-' + cep[5:]

        return super(res_cep, self).create(cr, uid, dados, context)

    def write(self, cr, uid, ids, dados, context={}):
        if 'cep' in dados and dados['cep']:
            cep = dados['cep']

            cep = limpa_formatacao(cep)
            if not cep.isdigit() or len(cep) != 8:
                raise osv.except_osv(u'Erro!', u'CEP inválido!')

            dados['cep'] = cep[:5] + '-' + cep[5:]

        return super(res_cep, self).write(cr, uid, ids, dados, context)

    def onchange_cep(self, cr, uid, ids, cep, contex={}):
        if not cep:
            return {}

        cep = limpa_formatacao(cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise osv.except_osv(u'Erro!', u'CEP inválido!')

        return {'value': {'cep': cep[:5] + '-' + cep[5:]}}

    def carrega(self, cr, uid, ids, context={}):
        cep_pool = self.pool.get('res.cep')
        municipio_pool = self.pool.get('sped.municipio')

        arq = open('/home/exata/cep.csv')

        i = 1
        for linha in arq.readlines():
            if i <= 2:
                i += 1
                continue

            if not linha.strip():
                continue

            print(linha.strip())
            print(linha.strip().split('|'))
            cep, codigo_ibge, bairro, endereco = linha.strip().split('|')

            print(cep)
            cep = cep[:5] + '-' + cep[5:]
            print(cep)

            cep_ids = cep_pool.search(cr, uid, [('cep', '=', cep)])

            if len(cep_ids):
                continue

            municipio_ids = municipio_pool.search(cr, uid, [('codigo_ibge', '=', codigo_ibge)])

            if not municipio_ids:
                continue

            dados = {
                'cep': cep,
                'municipio_id': municipio_ids[0],
                'bairro': bairro or '',
                'endereco': endereco or '',
            }

            cep_pool.create(cr, uid, dados)
            cr.commit()

        arq.close()

    def onchange_consulta_cep(self, cr, uid, ids, cep_id, context={}):
        if not cep_id:
            return {}

        cep_obj = self.pool.get('res.cep').browse(cr, uid, cep_id)

        res = {
            'cep': cep_obj.cep,
            'municipio_id': cep_obj.municipio_id.id,
            'bairro': cep_obj.bairro.strip(),
            'endereco': cep_obj.endereco.strip(),
            'complemento': cep_obj.complemento,
        }

        return res





res_cep()
