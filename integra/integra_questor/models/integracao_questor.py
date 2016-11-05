# -*- coding: utf-8 -*-

from pybrasil.inscricao import limpa_formatacao
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje
from pybrasil.valor.decimal import Decimal as D


NATUREZA_LANCAMENTO = [
            ( '1', u'Débito'),
            ('-1', u'Crédito'),
]


class integracao_questor(object):
    def __init__(self, *args, **kwargs):
        self.cnpj_cpf = ''
        self.data_lancamento = hoje()
        self.numero_documento = u''
        self.conta_debito = 0
        self.conta_credito = 0
        self.valor_documento = 0
        self.codigo_historico = 0
        self.complemento_historico = u''

        self.natureza_lancamento = '1'
        self.centro_custo = 0
        self.valor_rateio_centocusto = 0

    def registro_contabil(self):
        campos = [
            u'C',
            self.cnpj_cpf[:18],
            self.data_lancamento.strftime('%d/%m/%Y'),
            unicode(self.numero_documento)[:10],
            unicode(self.conta_debito)[:11],
            unicode(self.conta_credito)[:11],
            unicode('%.2f' %self.valor_documento)[:16],
            unicode(self.codigo_historico)[:5],
            unicode(self.complemento_historico)[:300],
            '\r\n',
        ]
        reg = u';'.join(campos)
        reg = tira_acentos(reg)
        return reg

    def registro_gerencial(self):
        campos = [
            'XX',
            self.natureza_lancamento[:2],
            self.centro_custo[:11],
            unicode('%.2f' %self.valor_rateio_centocusto)[:16],
            '\r\n',
        ]
        reg = ';'.join(campos)
        reg = tira_acentos(reg).upper()
        return reg


integracao_questor()


class integracao_questor_fiscal_A(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro A
        #
        self.nomepessoa = ''
        self.tipoinscr = 2
        self.inscrfederal = ''
        self.logradpessoa = ''
        self.enderecopessoa = ''
        self.numenderpessoa = 0
        self.complenderpessoa = ''
        self.bairroenderpessoa = ''
        self.siglaestado = ''
        self.codigomunic = ''
        self.cependerpessoa = ''
        self.dddfone = ''
        self.numerofone = ''
        self.produtrural = 'N'
        self.inscrprod = ''
        self.inscrestad = ''
        self.email = ''
        self.paginainternet = ''
        self.inscrmunic = ''
        self.codigoativfederal = ''

    def registro_A(self):

    #
    #A Pessoa (nGem) Clientes Um registro para cada cadastro de cliente
    #

        campos = [
            'A',
            self.nomepessoa[:50],
            unicode(self.tipoinscr)[:1],
            self.inscrfederal[:18],
            self.logradpessoa[:15],
            self.enderecopessoa[:40],
            self.numenderpessoa[:6],
            self.complenderpessoa[:20],
            self.bairroenderpessoa[:30],
            self.siglaestado[:2],
            self.codigomunic[:50],
            limpa_formatacao(self.cependerpessoa)[:10],
            self.dddfone[:4],
            self.numerofone[:8],
            self.produtrural,
            self.inscrprod[:25],
            self.inscrestad[:25],
            self.email[:100],
            self.paginainternet[:100],
            self.inscrmunic[:25],
            self.codigoativfederal[:9],
            '\r\n',
        ]
        reg = '|'.join(campos)
        reg = reg.replace(';', ',').replace('|', ';')
        reg = tira_acentos(reg).upper()
        #print(reg)
        return reg


class integracao_questor_fiscal_B(object):
    def __init__(self, *args, **kwargs):
        #
        # Registro B
        #
        self.codigoempresa = 0
        self.referenproduto = ''
        self.codigogrupoproduto = ''
        self.descrproduto = ''
        self.codigoncm = ''
        self.unidademedida = ''
        self.dacon = ''
        #self.dacontiporeceita = 0
        self.indicadortipo = 0
        self.tipomedicamento = ''
        self.incentivofis = ''
        self.tipocredito = ''
        self.tipodebito = ''

    def registro_B(self):

    #
    # B Produto (nGem)Produtos Um registro para cada cadastro de produto
    #

        campos = [
            'B',
            unicode(self.codigoempresa)[:5],
            unicode(self.referenproduto)[:15],
            unicode(self.codigogrupoproduto)[:5],
            self.descrproduto[:40],
            self.codigoncm[:12],
            self.unidademedida[:10],
            unicode(self.dacon)[:1],
            #self.dacontiporeceita[:5],
            unicode(self.indicadortipo)[:5],
            self.tipomedicamento[:1],
            self.incentivofis[:1],
            self.tipocredito[:20],
            self.tipodebito[:20],
            '\r\n',
        ]
        reg = '|'.join(campos)
        reg = reg.replace(';', ',').replace('|', ';')
        reg = tira_acentos(reg).upper()
        #print(reg)
        return reg


class integracao_questor_fiscal_C(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro C
        #
        self.codigoestab = ''
        self.codigopessoa = ''
        self.numeronf = 0
        self.numeronffinal = 0
        self.especienf = ''
        self.serienf = ''
        self.subserienf = ''
        self.datalctofis = hoje()
        self.valorcontabil = 0
        self.basecalculoipi = 0
        self.valoripi = 0
        self.isentasipi = 0
        self.outrasipi = 0
        self.contribuinte = False
        self.acrescimofinanceiro = 0
        self.siglaestadoorigem = ''
        self.codigomunicorigem = ''
        self.complhist = ''
        self.codigotipodctosintegra = 0
        self.emitentenf = ''
        self.modalidadefrete = 1
        self.adicionaliss = ''
        self.cancelada = 'N'
        self.conciliada = 'N'
        self.chaveorigem = ''
        self.desfeitonegocio = ''
        self.vlrdesc = 0
        self.vlrabatntrib = 0
        self.vlrfrete = 0
        self.vlrseguro = 0
        self.vlroutrdesp = 0
        self.cdmodelo = ''
        self.chavenfesai = ''
        self.chavenfesairef = ''
        self.cdsituacao = ''
        self.indpagto = ''

    def registro_C(self):

    #
    # LctoFisSai (nFis) Dados do Documento Fiscal Um registro para cada documento fiscal de saída
    #

        campos = [
            'C',
            self.codigoestab[:18],
            self.codigopessoa[:18],
            unicode(self.numeronf)[:9],
            unicode(self.numeronffinal)[:9],
            self.especienf[:4],
            self.serienf[:3],
            self.subserienf[:2],
            self.datalctofis.strftime('%d/%m/%Y')[:10],
            unicode('%.2f' %self.valorcontabil)[:16],
            unicode('%.2f' %self.basecalculoipi)[:16],
            unicode('%.2f' %self.valoripi)[:16],
            unicode('%.2f' %self.isentasipi)[:16],
            unicode('%.2f' %self.outrasipi)[:16],
            self.contribuinte,
            unicode('%.2f' %self.acrescimofinanceiro)[:16],
            self.siglaestadoorigem[:2],
            self.codigomunicorigem[:50],
            self.complhist[:100],
            unicode(self.codigotipodctosintegra)[:2],
            self.emitentenf[:1],
            unicode(self.modalidadefrete)[:2],
            self.adicionaliss[:50],
            self.cancelada[:1],
            self.conciliada[:1],
            self.chaveorigem[:25],
            self.desfeitonegocio[:1],
            unicode('%.2f' %self.vlrdesc)[:16],
            unicode('%.2f' %self.vlrabatntrib)[:16],
            unicode('%.2f' %self.vlrfrete)[:16],
            unicode('%.2f' %self.vlrseguro)[:16],
            unicode('%.2f' %self.vlroutrdesp)[:16],
            self.cdmodelo[:2],
            self.chavenfesai[:44],
            self.chavenfesairef[:44],
            self.cdsituacao[:5],
            self.indpagto[:1],
            '\r\n',
        ]
        reg = '|'.join(campos)
        reg = reg.replace(';', ',').replace('|', ';')
        reg = tira_acentos(reg).upper()
        #print(reg)
        return reg


class integracao_questor_fiscal_D(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro D
        #

        self.codigocfop = 0
        self.tipoimposto = 0
        self.valorcontabilimposto = 0
        self.basecalculoimposto = 0
        self.aliqimposto = 0
        self.valorimposto = 0
        self.isentasimposto = 0
        self.outrasimposto = 0
        self.valorexvaloradicional = 0
        self.codigotabctbfis = 0

    def registro_D(self):

    #
    # LctoFisSaiCFOP (nFis) Impostos Um registro para cada CFOP do documento fiscal
    #

        campos = [
            'D',
            unicode(self.codigocfop)[:7],
            unicode(self.tipoimposto)[:2],
            unicode('%.2f' %self.valorcontabilimposto)[:16],
            unicode('%.2f' %self.basecalculoimposto)[:16],
            unicode('%.2f' %self.aliqimposto)[:7],
            unicode('%.2f' %self.valorimposto)[:16],
            unicode('%.2f' %self.isentasimposto)[:16],
            unicode('%.2f' %self.outrasimposto)[:16],
            unicode('%.2f' %self.valorexvaloradicional)[:16],
            unicode(self.codigotabctbfis)[:4],
            '\r\n',
        ]
        reg = '|'.join(campos)
        reg = reg.replace(';', ',').replace('|', ';')
        reg = tira_acentos(reg).upper()
        return reg


class integracao_questor_fiscal_E(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro E
        #
        self.codigooperacaofis = 0
        self.basecalculocompl = 0
        self.aliqcompl = 0
        self.valorcompl = 0
        self.codigoobs = ''
        self.complobs = ''
        self.codobs0450 = ''
        self.complobs0450 = ''
        self.codigoproduto = 0

    def registro_E(self):

    #
    #  E LctoFisSaiCompl (nFis) Operações Complementares Um registro para cada Operação Complementar
    #

        campos = [
            'E',
            unicode(self.codigooperacaofis)[:10],
            unicode('%.2f' %self.basecalculocompl)[:16],
            unicode('%.2f' %self.aliqcompl)[:6],
            unicode('%.2f' %self.valorcompl)[:16],
            self.codigoobs[:6],
            self.complobs[:300],
            self.codobs0450[:6],
            self.complobs0450[:300],
            unicode(self.codigoproduto)[:16],
            '\r\n',
        ]
        reg = '|'.join(campos)
        reg = reg.replace(';', ',').replace('|', ';')
        reg = tira_acentos(reg).upper()
        return reg


class integracao_questor_fiscal_F(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro F
        #

        self.seq = 0
        self.codigocfop = 0
        self.codigoproduto = ''
        self.codigosituacaotribut = 0
        self.unidademedida = ''
        self.quantidade = 0
        self.valorunitario = 0
        self.valortotal = 0
        self.basecalculoicms = 0
        self.aliqicms = 0
        self.valoricms = 0
        self.isentasicms = 0
        self.outrasicms = 0
        self.basecalculoipi = 0
        self.aliqipi = 0
        self.valoripi = 0
        self.isentasipi = 0
        self.outrasipi = 0
        self.basecalculoiss = 0
        self.aliqiss = 0
        self.valoriss = 0
        self.isentasiss = 0
        self.outrasiss = 0
        self.basecalculosubtribut = 0
        self.aliqsubtribut = 0
        self.valorsubtribut = 0
        self.valordesconto = 0
        self.valordespesa = 0
        self.tipoestoque = 0
        self.cstipi = 0
        self.cstiss = 0
        self.cststicms = 0
        self.qtdeseloipi = 0
        self.vlrfrete = 0
        self.vlrseguro = 0
        self.abatnaotrib = 0
        self.outrassubtrib = 0
        self.isentassubtrib = 0
        self.indmov = ''

    def registro_F(self):

    #
    #  F LctoFisSaiProduto (nFis) Detalhamento dos Itens Um registro para cada item/produto do documento fiscal
    #

        campos = [
            'F',
            unicode(self.seq)[:4],
            unicode(self.codigocfop)[:10],
            self.codigoproduto[:15],
            unicode(self.codigosituacaotribut)[:4],
            self.unidademedida[:10],
            unicode('%.2f' %self.quantidade)[:16],
            unicode('%.2f' %self.valorunitario)[:18],
            unicode('%.2f' %self.valortotal)[:16],
            unicode('%.2f' %self.basecalculoicms)[:16],
            unicode('%.2f' %self.aliqicms)[:6],
            unicode('%.2f' %self.valoricms)[:16],
            unicode('%.2f' %self.isentasicms)[:16],
            unicode('%.2f' %self.outrasicms)[:16],
            unicode('%.2f' %self.basecalculoipi)[:16],
            unicode('%.2f' %self.aliqipi)[:6],
            unicode('%.2f' %self.valoripi)[:16],
            unicode('%.2f' %self.isentasipi)[:16],
            unicode('%.2f' %self.outrasipi)[:16],
            unicode('%.2f' %self.basecalculoiss)[:16],
            unicode('%.2f' %self.aliqiss)[:6],
            unicode('%.2f' %self.valoriss)[:16],
            unicode('%.2f' %self.isentasiss)[:16],
            unicode('%.2f' %self.outrasiss)[:16],
            unicode('%.2f' %self.basecalculosubtribut)[:16],
            unicode('%.2f' %self.aliqsubtribut)[:6],
            unicode('%.2f' %self.valorsubtribut)[:16],
            unicode('%.2f' %self.valordesconto)[:16],
            unicode('%.2f' %self.valordespesa)[:16],
            unicode(self.tipoestoque)[:2],
            unicode(self.cstipi)[:6],
            unicode(self.cstiss)[:6],
            unicode(self.cststicms)[:5],
            unicode(self.qtdeseloipi)[:10],
            unicode('%.2f' %self.vlrfrete)[:16],
            unicode('%.2f' %self.vlrseguro)[:16],
            unicode('%.2f' %self.abatnaotrib)[:16],
            unicode('%.2f' %self.outrassubtrib)[:16],
            unicode('%.2f' %self.isentassubtrib)[:16],
            self.indmov[:1],
            '\r\n',
        ]
        reg = '|'.join(campos)
        reg = reg.replace(';', ',').replace('|', ';')
        reg = tira_acentos(reg).upper()
        return reg


class integracao_questor_fiscal_G(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro G
        #

        self.codigoproduto = ''
        self.codigocfop = 0
        self.receitapiscofins = 0
        self.basecalculopiscofins = 0
        self.aliqpis = 0
        self.valorpis = 0
        self.aliqcofins = 0
        self.valorcofins = 0
        self.quantidade = 0
        self.cdsituatributpis = 0
        self.cdsituatributcofins = 0
        self.pissubstrib = 0
        self.cofinssubstrib =  0
        self.tipodebito = ''

    def registro_G(self):

        #
        #  G LctoFisSaiPISCOFINS (nFis) PIS / COFINS / Outros Um registro para cada item/produto do doc. fiscal com PIS/COFINS
        #
            campos = [
                'G',
                self.codigoproduto[:15],
                unicode(self.codigocfop)[:10],
                unicode('%.2f' %self.receitapiscofins)[:16],
                unicode('%.2f' %self.basecalculopiscofins)[:16],
                unicode('%.2f' %self.aliqpis)[:6],
                unicode('%.2f' %self.valorpis)[:16],
                unicode('%.2f' %self.aliqcofins)[:6],
                unicode('%.2f' %self.valorcofins)[:16],
                unicode('%.2f' %self.quantidade)[:16],
                unicode(self.cdsituatributpis)[:10],
                unicode(self.cdsituatributcofins)[:10],
                unicode('%.2f' %self.pissubstrib)[:16],
                unicode('%.2f' %self.cofinssubstrib)[:16],
                self.tipodebito[:20],
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg


class integracao_questor_fiscal_H(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro H
        #
        self.codigoestab = ''
        self.valordespesa = 0
        self.codigoantecipacao = 0
        self.codigooperacaofis = 0
        self.basecalculosubtribut= 0
        self.valorsubtribut = 0
        self.basecalcicmsprop = 0
        self.valoricmsprop = 0
        self.siglaestado = ''
        self.codigoobs = ''
        self.complobs = ''
        self.codigocfop = 0
        self.codigoproduto = 0
        self.aliqimpostocfop = 0

    def registro_H(self):

        #
        #  H LctoFisSaiSubtribut (nFis) Substituição tributária Um registro para cada ICMS Retido do documento fiscal
        #

            campos = [
                'H',
                self.codigoestab[:18],
                unicode('%.2f' %self.valordespesa)[:16],
                unicode(self.codigoantecipacao)[:1],
                unicode(self.codigooperacaofis)[:10],
                unicode('%.2f' %self.basecalculosubtribut)[:16],
                unicode('%.2f' %self.valorsubtribut)[:16],
                unicode('%.2f' %self.basecalcicmsprop)[:16],
                unicode('%.2f' %self.valoricmsprop)[:16],
                self.siglaestado[:2],
                self.codigoobs[:6],
                self.complobs[:300],
                unicode(self.codigocfop)[:10],
                unicode(self.codigoproduto)[:16],
                unicode(self.aliqimpostocfop)[:7],
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg


class integracao_questor_fiscal_J(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro J
        #

        self.codigoimpressorafiscal = 0
        self.dctoinicial = 0
        self.dctofinal = 0
        self.contadorreducaoz = 0
        self.contadorreiniciooperacao = 0
        self.totalbruto = 0
        self.totalgeral = 0
        self.valorsubtribut = 0
        self.valorisento = 0
        self.valornaoincidencia = 0
        self.valorcancelado = 0
        self.valordesconto = 0
        self.observreducaoz = ''

    def registro_J(self):

        #
        #  J LctoFisSaiECF (nFis) Detalhamento ECF Um registro para cada Detalhamento das ECF – SINTEGRA
        #

            campos = [
                'J',
                unicode(self.codigoimpressorafiscal)[:4],
                self.dctoinicial.strftime('%d/%m/%Y'),
                self.dctofinal.strftime('%d/%m/%Y'),
                unicode(self.contadorreducaoz)[:8],
                unicode(self.contadorreiniciooperacao)[:4],
                unicode('%.2f' %self.totalbruto)[:16],
                unicode('%.2f' %self.totalgeral)[:16],
                unicode('%.2f' %self.valorsubtribut)[:16],
                unicode('%.2f' %self.valorisento)[:16],
                unicode('%.2f' %self.valornaoincidencia)[:16],
                unicode('%.2f' %self.valorcancelado)[:16],
                unicode('%.2f' %self.valordesconto)[:16],
                self.observreducaoz[:100],
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg


class integracao_questor_fiscal_K(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro K
        #

        self.basecalculoicms = 0
        self.aliqicms = 0
        self.valoricms = 0

    def registro_K(self):

        #
        #  K LctoFisSaiECFICMS (nFis) Detalhamento ECF - ICMS Um registro para cada Detalhamento das ECF – SINTEGRA
        #

            campos = [
                'K',
                unicode('%.2f' %self.basecalculoicms)[:16],
                unicode('%.2f' %self.aliqicms)[:16],
                unicode('%.2f' %self.valoricms)[:16],
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg


class integracao_questor_fiscal_KI(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro KI
        #

        self.basecalculoissqn = 0
        self.aliqissqn = 0
        self.valorissqn = 0

    def registro_KI(self):

        #
        #  KI LctoFisSaiECFISS (nFis) Detalhamento ECF – ISS Um registro para cada Detalhamento das ECF – SINTEGRA
        #

            campos = [
                'KI',
                unicode('%.2f' %self.basecalculoissqn)[:16],
                unicode('%.2f' %self.aliqissqn)[:6],
                unicode('%.2f' %self.valorissqn)[:16],
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg


class integracao_questor_fiscal_L(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro L
        #

        self.tipoanexo = 0
        self.codigoanexo = 0
        self.codigocfop = 0
        self.valordebito = 0

    def registro_L(self):

        #
        #  L LctoFisSaiAnexoRS (nFis) Detalhamento das Isentas Anexo V-A e V-B (Estado RS) Um registro para cada Anexo e Código de Isenção
        #

            campos = [
                'L',
                unicode(self.tipoanexo)[:5],
                unicode(self.codigoanexo)[:5],
                unicode(self.codigocfop)[:10],
                unicode(self.valordebito)[:16],
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg


class integracao_questor_fiscal_M(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro M
        #

        self.siglaestado = ''
        self.tipoinscr = 0
        self.inscrfederal = ''
        self.inscrestad = ''
        self.dataemissaonf = hoje()
        self.codigotipodctosintegra = 0
        self.numeronf = 0
        self.especienf = ''
        self.serienf = ''
        self.subserienf = ''
        self.valortotalnf = 0
        self.siglaestadodest = ''
        self.tipoinscrdest = 0
        self.inscrfederaldest = ''
        self.inscrestaddest = ''
        self.cdmodelo = ''
        self.chavenfe = ''
        self.vlrmerc = 0
        self.qtdvolume = 0
        self.pesobrt = 0
        self.pesoliq = 0
        self.siglaestcol = ''
        self.codmunicol = 0
        self.tipoinscrcol = 0
        self.inscrfederalcol = ''
        self.iecol = ''
        self.siglaestent = ''
        self.codmunient = 0
        self.tipoinscrentg = 0
        self.inscrfederalentg = ''
        self.ieentg = ''
        self.despacho = ''

    def registro_M(self):

        #
        #  M LctoFisSaiConFrete (nFis) Conhecimento Frete – NFs Um registro para cada NF ref. Conhecimento de Frete – SINTEGRA
        #

            campos = [
                'M',
                self.siglaestado[:2],
                unicode(self.tipoinscr)[:2],
                self.inscrfederal[:18],
                self.inscrestad[:25],
                self.dataemissaonf.strftime('%d/%m/%Y'),
                unicode(self.codigotipodctosintegra)[:2],
                unicode(self.numeronf)[:6],
                self.especienf[:4],
                self.serienf[:3],
                self.subserienf[:2],
                unicode('%.2f' %self.valortotalnf)[:16],
                self.siglaestadodest[:2],
                unicode(self.tipoinscrdest)[:2],
                self.inscrfederaldest[:18],
                self.inscrestaddest[:25],
                self.cdmodelo[:2],
                self.chavenfe[:44],
                unicode('%.2f' %self.vlrmerc)[:16],
                unicode('%.2f' %self.qtdvolume)[:16],
                unicode('%.2f' %self.pesobrt)[:16],
                unicode('%.2f' %self.pesoliq)[:16],
                self.siglaestcol[:2],
                unicode(self.codmunicol)[:21],
                unicode(self.tipoinscrcol)[:1],
                self.inscrfederalcol[:18],
                self.iecol[:25],
                self.siglaestent[:2],
                unicode(self.codmunient)[:21],
                unicode(self.tipoinscrentg)[:1],
                self.inscrfederalentg[:28],
                self.ieentg[:25],
                self.despacho[:10],
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg


class integracao_questor_fiscal_N(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro N
        #

        self.numerodeclaexport = 0
        self.datadeclaexport = hoje()
        self.naturezaexport = 0
        self.numeroregexport = 0
        self.dataregexport = hoje()
        self.numeroconhecembarque = ''
        self.dataconhecembarque = hoje()
        self.tipoconhecembarque = 0
        self.numerocompexport = 0
        self.datacompexport = hoje()
        self.dataaverbacaoexport = hoje()
        self.modelonf = 0
        self.codigomoedaexport = 0
        self.valordespacho = 0

    def registro_N(self):

        #
        #  N LctoFisSaiExport (nFis) Exportação Um registro para cada documento fiscal de saída
        #

            campos = [
                'N',
                unicode(self.numerodeclaexport)[:15],
                self.datadeclaexport.strftime('%d/%m/%Y'),
                unicode(self.naturezaexport)[:4],
                unicode(self.numeroregexport)[:15],
                self.dataregexport.strftime('%d/%m/%Y'),
                self.numeroconhecembarque[:16],
                self.dataconhecembarque.strftime('%d/%m/%Y'),
                unicode(self.tipoconhecembarque)[:4],
                unicode(self.numerocompexport)[:15],
                self.datacompexport.strftime('%d/%m/%Y'),
                self.dataaverbacaoexport.strftime('%d/%m/%Y'),
                unicode(self.modelonf)[:5],
                unicode(self.codigomoedaexport)[:5],
                unicode('%.2f' %self.valordespacho)[:16],
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg


class integracao_questor_fiscal_O(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro O
        #

        self.codigocentrocusto = 0
        self.percentual = 0

    def registro_O(self):

        #
        #  O LctoFisSaiCCusto (nFis) Centros de Custos Um registro para cada centro de custo do lançamento fiscal
        #

            campos = [
                'O',
                unicode(self.codigocentrocusto)[:10],
                unicode(self.percentual)[:6],
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg


class integracao_questor_fiscal_R(object):
    def __init__(self, *args, **kwargs):

        #
        # Registro R
        #

        self.tiporetencao = 0
        self.basecalculoinss = 0
        self.aliqinss = 0
        self.valorinss = 0
        self.basecalculoirpj = 0
        self.aliqirpj = 0
        self.valorirpj = 0
        self.basecalculoissqn = 0
        self.aliqissqn = 0
        self.valorissqn = 0
        self.basecalculoirrf = 0
        self.aliqirrf = 0
        self.valorirrf = 0
        self.codigoimpostoirrf = 0
        self.variacaoimpostoirrf = 0
        self.dataprevirrfirpj = hoje()
        self.datapgtoirrfirpj = hoje()
        self.totalpiscofinscsll = 0
        self.basecalculopis = 0
        self.aliqpis = 0
        self.valorpis = 0
        self.codigoimpostopis = 0
        self.variacaoimpostopis = 0
        self.basecalculocofins = 0
        self.aliqcofins = 0
        self.valorcofins = 0
        self.codigoimpostocofins = 0
        self.variacaoimpostocofins = 0
        self.basecalculocsll = 0
        self.aliqcsll = 0
        self.valorcsll = 0
        self.codigoimpostocsll = 0
        self.variacaoimpostocsll = 0
        self.dataprevpiscofinscsll = hoje()
        self.datapgtopiscofinscsll = hoje()
        self.conciliada = ''
        self.dataprevissqn = hoje()
        self.datapgtoissqn = hoje()

    def registro_R(self):

        #
        #  R LctoFisSaiRetido (nFis) Retenção Um registro para o documento fiscal com retenção
        #

            campos = [
                'R',
                unicode(self.tiporetencao)[:5],
                unicode('%.2f' %self.basecalculoinss)[:16],
                unicode('%.2f' %self.aliqinss)[:6],
                unicode('%.2f' %self.valorinss)[:16],
                unicode('%.2f' %self.basecalculoirpj)[:16],
                unicode('%.2f' %self.aliqirpj)[:6],
                unicode('%.2f' %self.valorirpj)[:16],
                unicode('%.2f' %self.basecalculoissqn)[:16],
                unicode('%.2f' %self.aliqissqn)[:6],
                unicode('%.2f' %self.valorissqn)[:16],
                unicode('%.2f' %self.basecalculoirrf)[:16],
                unicode('%.2f' %self.aliqirrf)[:6],
                unicode('%.2f' %self.valorirrf)[:16],
                unicode(self.codigoimpostoirrf)[:10],
                unicode(self.variacaoimpostoirrf)[:5],
                self.dataprevirrfirpj.strftime('%d/%m/%Y'),
                self.datapgtoirrfirpj.strftime('%d/%m/%Y'),
                unicode('%.2f' %self.totalpiscofinscsll)[:16],
                unicode('%.2f' %self.basecalculopis)[:16],
                unicode('%.2f' %self.aliqpis)[:7],
                unicode('%.2f' %self.valorpis)[:16],
                unicode(self.codigoimpostopis)[:10],
                unicode(self.variacaoimpostopis)[:5],
                unicode('%.2f' %self.basecalculocofins)[:16],
                unicode(self.aliqcofins)[:7],
                unicode('%.2f' %self.valorcofins)[:16],
                unicode(self.codigoimpostocofins)[:10],
                unicode(self.variacaoimpostocofins)[:5],
                unicode('%.2f' %self.basecalculocsll)[:16],
                unicode(self.aliqcsll)[:7],
                unicode('%.2f' %self.valorcsll)[:16],
                unicode(self.codigoimpostocsll)[:10],
                unicode(self.variacaoimpostocsll)[:5],
                self.dataprevpiscofinscsll.strftime('%d/%m/%Y'),
                self.datapgtopiscofinscsll.strftime('%d/%m/%Y'),
                self.conciliada[:1],
                self.dataprevissqn.strftime('%d/%m/%Y'),
                self.datapgtoissqn.strftime('%d/%m/%Y'),
                '\r\n',
            ]
            reg = '|'.join(campos)
            reg = reg.replace(';', ',').replace('|', ';')
            reg = tira_acentos(reg).upper()
            return reg
