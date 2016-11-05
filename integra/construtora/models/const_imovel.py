# -*- coding: utf-8 -*-


# from __future__ import division, print_function, unicode_literals
from osv import osv, fields
from pybrasil.valor.decimal import Decimal as D, ROUND_DOWN
from pybrasil.inscricao import limpa_formatacao
from pybrasil.data import hoje



FACE_SOL = [
    ['N', u'Norte'],
    ['S', u'Sul'],
    ['L', u'Leste'],
    ['O', u'Oeste'],
]

POSICAO_RUA = [
    ['F', u'Frente'],
    ['U', u'Fundos'],
    ['M', u'Meio/lateral'],
]

PAVIMENTACAO = [
    ['A', 'Asfalto'],
    ['C', 'Calçamento'],
    ['P', 'Paralelepípedo'],
    ['V', 'Paver'],
    ['N', 'Nenhum/ausente'],
]

AQUECIMENTO_AGUA = [
    ['G', 'Gás'],
    ['S', 'Solar'],
    ['E', 'Elétrico'],
    ['N', 'Nenhum/ausente'],
]

TEMPO_VIGILANCIA = [
    ['24', '24 horas'],
    ['12', '12 horas'],
]

INCLINACAO_TERRENO = [
    ['P', 'Plano'],
    ['A', 'Aclive'],
    ['D', 'Declive'],
]

TIPO_IMOVEL = [
    ['C', u'Casa'],
    ['A', u'Apartamento'],
    ['T', u'Terreno'],
    ['X', u'Chácara/sítio'],
    ['F', u'Fazenda/área de terras'],
    ['U', u'Área de terras urbana'],
    ['G', u'Galpão/pavilhão'],
    ['P', u'Prédio'],
    ['S', u'Sala comercial'],
    ['L', u'Loja/ponto comercial'],
    ['O', u'Outros'],
]
TIPO_IMOVEL_DIC = dict(TIPO_IMOVEL)

SITUACAO_IMOVEL = [
    ['D', u'Disponível'],
    ['R', u'Reservado'],
    ['C', u'Cancelado'],
    ['V', u'Vendido'],
    ['A', u'Alugado'],
    ['ND', u'Não disponível'],
    ['NL', u'Não liberado'],
]

SITUACAO_CONTABIL = [
    ['D', u'Disponível'],
    ['V', u'Vendido'],
]

PROPRIEDADE = [
    ['P', u'Próprio'],
    ['T', u'Terceiros'],
    ['L', u'Terceiros-Locação'],
    ['A', u'Terceiros-Associado'],
]

CONDICAO_PREDIO = [
    ['1', u'Excelente'],
    ['2', u'Otimo'],
    ['3', u'Satisfatorio'],
    ['4', u'Simples'],
]

RESTRICOES = [
    ['1', u'Caucionado'],
    ['2', u'Hipotecado'],
    ['3', u'Aguardando Liberação Ambiental'],
    ['4', u'Em Processo de Unificação'],
    ['5', u'Em Processo de Desmembramento'],
]

TIPO_TESTADA = [
    ['1', u'Esquina'],
    ['2', u'Meio de quadra'],
]

TIPO_CONSTRUCAO = [
    ['1', u'Alvenaria'],
    ['2', u'Madeira'],
    ['3', u'Mista'],
    ['4', u'Outra'],
]


class const_imovel(osv.Model):
    _name = 'const.imovel'
    _rec_name = 'descricao_lista'

    def _codigo(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for imovel_obj in self.browse(cr, uid, ids):

            if imovel_obj.id:
                if not imovel_obj.codigo:
                    res[imovel_obj.id] = str(imovel_obj.id).zfill(6)

        return res


    def _descricao(self, cursor, user_id, ids, fields, arg, context=None):
        retorno = {}

        for registro in self.browse(cursor, user_id, ids):
            txt = registro.tipo or ''
            txt += '-'
            txt += registro.codigo or u'[SEM CÓDIGO]'

            txt += ' Q '
            txt += registro.quadra or ''
            txt += ' L '
            txt += registro.lote or ''

            if registro.project_id:
                txt += ' - '
                txt += registro.project_id.name

            retorno[registro.id] = txt

        return retorno

    def _get_base(self, cr, uid, ids, nome_campo, args, context=None):

        res = {}
        total_base = D('0')
        for imovel_obj in self.browse(cr, uid, ids):

            if imovel_obj.zoneamento_item_id and imovel_obj.area_total:

               taxa_ocupacao = D('0')
               taxa_ocupacao += D(str(imovel_obj.zoneamento_item_id.taxa_ocupacao))
               area_total =  D(str(imovel_obj.area_total))
               total_base += (area_total * taxa_ocupacao) / 100

        res[imovel_obj.id] = total_base.quantize(D('0.01'))

        return res

    def _get_potencial_construtivo(self, cr, uid, ids, nome_campo, args, context=None):

        res = {}

        total_potencial_construtivo = D('0')
        for imovel_obj in self.browse(cr, uid, ids):

            if imovel_obj.zoneamento_item_id.coeficiente_aproveitamento and imovel_obj.area_total:

               coeficiente_aproveitamento =  D('0')
               area_total =  D('0')
               coeficiente_aproveitamento +=  D(str(imovel_obj.zoneamento_item_id.coeficiente_aproveitamento))
               area_total +=  D(str(imovel_obj.area_total))
               total_potencial_construtivo += area_total * coeficiente_aproveitamento

        res[imovel_obj.id] = total_potencial_construtivo.quantize(D('0.01'))

        return res

    def _get_torre(self, cr, uid, ids, nome_campo, args, context=None):

        res = {}

        total_torre = D('0')
        for imovel_obj in self.browse(cr, uid, ids):

            if imovel_obj.zoneamento_item_id and imovel_obj.area_total:

               taxa_ocupacao_torre =  D('0')
               taxa_ocupacao_torre +=  D(str(imovel_obj.zoneamento_item_id.taxa_ocupacao_torre))
               area_total =  D(str(imovel_obj.area_total))
               total_torre += (area_total * taxa_ocupacao_torre) / 100

        res[imovel_obj.id] = total_torre.quantize(D('0.01'))

        return res

    def _get_altura_maxima(self, cr, uid, ids, nome_campo, args, context=None):

        res = {}

        total_altura_maxima = D('0')
        for imovel_obj in self.browse(cr, uid, ids):

            if imovel_obj.zoneamento_item_id and imovel_obj.largura_rua:

               recuo_minimo = D('0')
               fator_altura = D('0')
               largura_rua = D('0')

               recuo_minimo += D(str(imovel_obj.zoneamento_item_id.recuo_minimo))
               fator_altura += D(str(imovel_obj.zoneamento_item_id.fator_altura))
               largura_rua += D(str(imovel_obj.largura_rua))

               total_altura_maxima += fator_altura * ( largura_rua + recuo_minimo)

        res[imovel_obj.id] = total_altura_maxima.quantize(D('0.01'))

        return res

    def _get_numero_pavimento(self, cr, uid, ids, nome_campo, args, context=None):

        res = {}

        total_numero_pavimento = D('0')
        for imovel_obj in self.browse(cr, uid, ids):

            if imovel_obj.zoneamento_item_id.altura_media_pavimento and imovel_obj.vr_altura_maxima:

               altura_maxima = D('0')
               altura_media_pavimento = D('0')

               altura_maxima +=  D(str(imovel_obj.vr_altura_maxima))
               altura_media_pavimento +=  D(str(imovel_obj.zoneamento_item_id.altura_media_pavimento))

               total_numero_pavimento +=  altura_maxima / altura_media_pavimento

        res[imovel_obj.id] = total_numero_pavimento.quantize(D('0.01', ROUND_DOWN))

        return res

    def _get_tamanho_pavimento_altura_max(self, cr, uid, ids, nome_campo, args, context=None):

        res = {}

        total_tamanho_pavimento = D('0')
        for imovel_obj in self.browse(cr, uid, ids):

            if imovel_obj.vr_potencial_construtivo and imovel_obj.numero_pavimento:


               vr_potencial_construtivo = D('0')
               numero_pavimento = D('0')
               vr_potencial_construtivo +=  D(str(imovel_obj.vr_potencial_construtivo))
               numero_pavimento +=  D(str(imovel_obj.numero_pavimento))

               total_tamanho_pavimento +=  vr_potencial_construtivo / numero_pavimento

        res[imovel_obj.id] = total_tamanho_pavimento.quantize(D('0.01'))

        return res

    def _get_numero_pavimento_max(self, cr, uid, ids, nome_campo, args, context=None):

        res = {}

        total_numero_pavimento_max = D('0')
        for imovel_obj in self.browse(cr, uid, ids):

            if imovel_obj.vr_potencial_construtivo and imovel_obj.vr_base and imovel_obj.vr_torre :

               vr_potencial_construtivo = D('0')
               vr_base = D('0')
               vr_torre = D('0')

               vr_potencial_construtivo +=  D(str(imovel_obj.vr_potencial_construtivo))
               vr_base +=  D(str(imovel_obj.vr_base))
               vr_torre += D(str(imovel_obj.vr_torre))

               total_numero_pavimento_max +=  ( vr_potencial_construtivo - vr_base ) / vr_torre

        res[imovel_obj.id] = total_numero_pavimento_max.quantize(D('0.01'))

        return res

    def _confrontacoes_contratuais(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for imovel_obj in self.browse(cr, uid, ids):
            confrontacoes = u''

            if imovel_obj.confrontacao_norte:
                if confrontacoes != u'':
                    confrontacoes += u'; '
                confrontacoes += u'ao NORTE '
                confrontacoes += imovel_obj.confrontacao_norte

            if imovel_obj.confrontacao_nordeste:
                if confrontacoes != u'':
                    confrontacoes += u'; '
                confrontacoes += u'ao NORDESTE '
                confrontacoes += imovel_obj.confrontacao_nordeste

            if imovel_obj.confrontacao_leste:
                if confrontacoes != u'':
                    confrontacoes += u'; '
                confrontacoes += u'ao LESTE '
                confrontacoes += imovel_obj.confrontacao_leste

            if imovel_obj.confrontacao_sudeste:
                if confrontacoes != u'':
                    confrontacoes += u'; '
                confrontacoes += u'ao SUDESTE '
                confrontacoes += imovel_obj.confrontacao_sudeste

            if imovel_obj.confrontacao_sul:
                if confrontacoes != u'':
                    confrontacoes += u'; '
                confrontacoes += u'ao SUL '
                confrontacoes += imovel_obj.confrontacao_sul

            if imovel_obj.confrontacao_sudoeste:
                if confrontacoes != u'':
                    confrontacoes += u'; '
                confrontacoes += u'ao SUDOESTE '
                confrontacoes += imovel_obj.confrontacao_sudoeste

            if imovel_obj.confrontacao_oeste:
                if confrontacoes != u'':
                    confrontacoes += u'; '
                confrontacoes += u'ao OESTE '
                confrontacoes += imovel_obj.confrontacao_oeste

            if imovel_obj.confrontacao_noroeste:
                if confrontacoes != u'':
                    confrontacoes += u'; '
                confrontacoes += u'ao NOROESTE '
                confrontacoes += imovel_obj.confrontacao_noroeste

            res[imovel_obj.id] = confrontacoes

        return res

    def _valor_metro_quadrado(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for imovel_obj in self.browse(cr, uid, ids):
            valor = D(0)

            if imovel_obj.tipo in ['T', 'X', 'F', 'U']:
                if imovel_obj.area_total:
                    valor = D(imovel_obj.valor_venda or 0) / D(imovel_obj.area_total or 1)

            elif imovel_obj.area_construida_total:
                valor = D(imovel_obj.valor_venda or 0) / D(imovel_obj.area_construida_total or 1)

            res[imovel_obj.id] = valor

        return res

    def _proposta_id(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        for imovel_obj in self.browse(cr, uid, ids):
            res[imovel_obj.id] = False

            partner_id = context.get('partner_id', False)

            if not partner_id:
                continue

            sql = """
            select
                c.id

            from
                finan_contrato c

            where
                c.partner_id = {partner_id}
                and c.imovel_id = {imovel_id};
            """
            sql = sql.format(partner_id=partner_id, imovel_id=imovel_obj.id)
            cr.execute(sql)

            dados = cr.fetchall()

            if len(dados) and dados[0][0]:
                res[imovel_obj.id] = dados[0][0]

        return res

    def _field_readonly(self, cr, uid, ids, nome_campo, args=None, context={}):
        res = {}

        nome_campo = nome_campo.replace('_readonly', '')

        for obj in self.browse(cr, uid, ids, context=context):
            if nome_campo[-3:] == '_id':
                campo = getattr(obj, nome_campo, False)

                if campo:
                    res[obj.id] = campo.id
                else:
                    res[obj.id] = False

            else:
                res[obj.id] = getattr(obj, nome_campo, False)

        return res

    _columns = {
        'proposta_id': fields.function(_proposta_id, type='many2one', relation='finan.contrato', string=u'Proposta/Contrato'),

        'create_date': fields.datetime(string=u'Data de criação'),
        'descricao_lista': fields.function(_descricao, string=u'Imóvel', method=True, type='char', store=True, select=True),
        'project_id': fields.many2one('project.project', u'Projeto'),
        'company_id': fields.related('project_id','company_id',  type='many2one', string=u'Empresa', relation='res.company', store=False),
        'eh_condominio': fields.related('project_id', 'eh_condominio', type='boolean', string=u'É num condomínio?'),
        'propriedade': fields.selection(PROPRIEDADE, u'Propriedade', select=True),
        'situacao': fields.selection(SITUACAO_IMOVEL, u'Situação comercial', select=True),
        'situacao_readonly': fields.function(_field_readonly, type='selection', selection=SITUACAO_IMOVEL, string=u'Situação comercial'),
        'situacao_contabil': fields.selection(SITUACAO_CONTABIL, u'Situação contábil', select=True),
        'data_renovacao': fields.date(u'Data de renovação'),
        'finan_motivo_distrato_id': fields.many2one('finan.motivo_distrato', u'Motivo', ondelete='restrict'),
        'tipo': fields.selection(TIPO_IMOVEL, u'Tipo', select=True),
        'codigo': fields.char(u'Código', size=20, select=True, required=True),
        #'codigo': fields.function(_codigo, type='char', method=True, string=u'Código', store=True, select=True),
        'descricao': fields.text(u'Descrição geral', select=True),
        'endereco': fields.char(u'Endereço', size=60, select=True),
        'esquina': fields.char(u'Esquina com', size=60, select=True),
        'numero': fields.char(u'Número', size=60),
        'complemento': fields.char(u'Complemento', size=60),
        'bairro': fields.char(u'Bairro', size=60, select=True),
        'municipio_id': fields.many2one('sped.municipio', u'Município', ondelete='restrict'),
        'cidade': fields.related('municipio_id', 'nome', type='char', string=u'Município', store=True, select=True),
        'estado': fields.related('municipio_id', 'estado', type='char', string=u'Estado', store=True, select=True),
        'cep': fields.char('CEP', size=9, select=True),
        'cep_id': fields.many2one('res.cep', u'CEP', ondelete='restrict'),
        'quadra': fields.char(u'Quadra', size=10, select=True),
        'lote': fields.char(u'Lote', size=60, select=True),
        'condominio': fields.char(u'Edifício/condomínio/loteamento', size=60, select=True),
        'ponto_referencia': fields.char(u'Ponto de referência', size=60),
        'valor_documento_from': fields.function(lambda *a, **k: {}, method=True, type='float', string=u'De valor'),
        'valor_documento_to': fields.function(lambda *a, **k: {}, method=True, type='float', string=u'A valor'),
        'crm_leads_ids': fields.many2many('crm.lead', 'crm_lead_imovel', 'imovel_id', 'lead_id', u'Prospecções'),

        'area_util': fields.float(u'Área construida(m²)', select=True),
        'area_total': fields.float(u'Área total (m²)', select=True),
        'area_terreno': fields.float(u'Área terreno (m²)', select=True),
        'area_construida_averbada': fields.float(u'Área construída averbada(m²)', select=True),
        'area_construida_nao_averbada': fields.float(u'Área construída não averbada total (m²)', select=True),
        'area_privativa': fields.float(u'Área privativa (m²)', select=True),

        'area_construida_total': fields.float(u'Área construída total (m²)', select=True),
        'largura': fields.float(u'Testada/largura'),
        'comprimento': fields.float(u'Comprimento'),
        'dimensoes': fields.char(u'Dimensões', size=60),
        'topografia': fields.selection(INCLINACAO_TERRENO, u'Topografia'),
        'cercamento': fields.char(u'Cercamento', size=60),
        'largura_rua': fields.float(u'Largura da rua princial'),

        'pavimentacao': fields.selection(PAVIMENTACAO, u'Pavimentação', select=True),
        'face_sol': fields.selection(FACE_SOL, u'Face sol', select=True),
        'posicao_rua': fields.selection(POSICAO_RUA, u'Posição na rua', select=True),

        'apartamento': fields.char(u'Apartamento nº', size=60),
        'ultimo_andar': fields.boolean(u'Último andar', select=True),
        'cobertura': fields.boolean(u'Cobertura', select=True),
        'pavimento': fields.integer(u'Pavimento/andar', select=True),

        'suite': fields.integer(u'Suíte(s)'),
        'suite_hidro': fields.integer(u'Hidromassagem'),
        'suite_closet': fields.integer(u'Closet'),
        'suite_sacada': fields.integer(u'Sacada'),

        'quarto': fields.integer(u'Quarto(s)'),
        'quarto_closet': fields.integer(u'Com closet'),
        'quarto_sacada': fields.integer(u'Sacada'),

        'banheiro': fields.integer(u'Banheiro(s)'),
        'banheiro_hidro': fields.integer(u'Hidromassagem'),

        'lavabo': fields.integer(u'Lavabo(s)'),
        'banheiro_social': fields.integer(u'Banheiro(s) social(is)'),
        'banheiro_servico': fields.integer(u'Banheiro(s) de serviço'),

        'sala_estar': fields.integer(u'Sala(s) de estar'),
        'sala_jantar': fields.integer(u'Sala(s) de jantar'),
        'sala_tv': fields.integer(u'Sala(s) de TV'),
        'lareira': fields.integer(u'Lareira(s)'),
        'escritorio': fields.integer(u'Escritório(s)'),
        'cozinha': fields.integer(u'Cozinha(s)'),
        'empregada': fields.integer(u'Dep. empregado(s)'),
        'lavanderia': fields.integer(u'Lavanderia(s)'),
        'area_servico': fields.integer(u'Área(s) de serviço'),
        'sacada': fields.integer(u'Sacada'),
        'churrasqueira_sacada': fields.integer(u'Churrasqueira na sacada'),
        'outro_local': fields.char(u'Outro local', size=60),

        'churrasqueira': fields.boolean(u'Churrasqueira(s)'),
        'churrasqueira_local': fields.char(u'Local da churrasqueira', size=60),
        'espaco_gourmet': fields.boolean(u'Espaço gourmet'),

        'calefacao': fields.char(u'Calefação', size=60),
        'aquecimento_piso': fields.char(u'Aquecimento do piso', size=60),
        'pontos_climatizacao': fields.char(u'Pontos de climatização', size=60),

        'terraco': fields.integer(u'Terraço'),
        'aquecimento_agua': fields.selection(AQUECIMENTO_AGUA, u'Aquecimento da água', select=True),
        'garagem': fields.integer(u'Garagem(ns)'),
        'garagem_tipo': fields.char(u'Tipo de garagem', size=60),

        'imovel_concluido': fields.boolean(u'Imóvel concluído', select=True),
        'imovel_ocupado': fields.boolean(u'Imóvel ocupado', select=True),
        'imovel_locado': fields.boolean(u'Imóvel Locado', select=True),
        'imovel_locado_valor': fields.float(u'Valor Locação', select=True),
        'imovel_projetado': fields.boolean(u'Imóvel projetado', select=True),
        'data_projetado': fields.date(u'Data'),
        'imovel_desocupado': fields.boolean(u'Imóvel desocupado', select=True),
        'imovel_ocupado_obs': fields.char(u'Obs.', size=60),
        'prazo_locacao': fields.date(u'Prazo Locação'),
        'acabamento': fields.selection(CONDICAO_PREDIO, u'Acabamento', select=True),
        'imovel_chave': fields.boolean(u'Chave', select=True),

        'obs': fields.text(u'Observações'),
        'visita_obs': fields.text(u'Visita ao imóvel'),
        'contato_visita': fields.char(u'Contato para visita', size=60),
        'fone_visita': fields.char(u'Fone', size=60),
        'agendamento_visita': fields.char(u'Data de agendamento', size=60),

        #
        # Sobre o edifício
        #
        'poco_artesiano': fields.boolean(u'Poço artesiano'),
        'gas_natural': fields.boolean(u'Gás natural/GLP'),
        'elevador': fields.integer(u'Elevador(es)'),
        'salao_festa': fields.integer(u'Salão(ões) de festa'),
        'salao_festa_churrasqueira': fields.integer(u'Churrasqueira(s)'),
        'salao_festa_banheiro': fields.integer(u'Banheiro(s)'),
        'salao_festa_cozinha': fields.integer(u'Cozinha(s)'),
        'salao_festa_mobiliado': fields.char(u'Mobília', size=60),
        'ligacao_gas_individual': fields.boolean(u'Gás individual'),
        'ligacao_energia_individual': fields.boolean(u'Energia individual'),
        'ligacao_agua_individual': fields.boolean(u'Água individual'),
        'operadora_banda_larga': fields.char(u'Operadora(s) de banda larga', size=60),
        'operadora_tv_cabo': fields.char(u'Operadora(s) de Tv cabo', size=60),
        'tubulacao_subterranea': fields.boolean(u'Tubulação(ões) subterrânea(s)'),
        'necessita_reforma': fields.boolean(u'Necessita reforma'),
        'terraco': fields.boolean(u'Terraço'),
        'metragem_terraco': fields.float(u'Metragem terraço'),

        'monitorado_alarme': fields.boolean(u'Monitorado por alarme', select=True),
        'monitorado_camera': fields.boolean(u'Monitorado por câmera'),
        'portaria_vigilante': fields.boolean(u'Portaria com vigilante'),
        'portaria': fields.integer(u'Portaria(s)'),
        'vigilancia': fields.selection(TEMPO_VIGILANCIA, u'Vigilancia'),
        'numero_alarme': fields.integer(u'Nº alarme'),

        'condominio_fechado': fields.boolean(u'Condomínio fechado'),

        'playground': fields.boolean(u'Playground'),
        'sauna': fields.boolean(u'Sauna'),
        'academia': fields.boolean(u'Espaço fitness/Academia'),
        'academia_ar_livre': fields.boolean(u'Espaço fitness/Acadeia ao ar livre'),
        'brinquedoteca': fields.boolean(u'Brinquedoteca'),
        'cinema': fields.boolean(u'Cinema'),
        'espaco_beleza': fields.boolean(u'Espaço beleza'),
        'heliponto': fields.boolean(u'Heliponto'),
        'piscina': fields.boolean(u'Piscina', select=True),
        'piscina_aquecida': fields.boolean(u'Piscina aquecida'),
        'lago': fields.integer(u'Lago(s)'),
        'baia_cavalo': fields.integer(u'Baia(s) para cavalo'),
        'trilha_caminhada': fields.integer(u'Trilha(s) para caminhada'),
        'quiosque': fields.integer(u'Quiosque(s)'),
        'quadra_poliesportiva': fields.integer(u'Quadra(s) poliesportiva'),
        'quadra_tenis': fields.integer(u'Quadra(s) de tênis'),
        'ginasio': fields.integer(u'Ginásio(s)'),
        'campo_futebol_salao': fields.integer(u'Campo(s) de futebol de salão'),
        'campo_futebol': fields.integer(u'Campo(s) de futebol'),
        'brinquedoteca': fields.boolean(u'Brinquedoteca'),
        'cinema': fields.boolean(u'Cinema'),

        'valor_condominio': fields.float(u'Valor condomínio', digits=(18,2)),
        'chamada_capital': fields.float(u'Valor chamada de capital', digits=(18,2)),
        'condicao_predio': fields.selection(CONDICAO_PREDIO, u'Condição geral do prédio', select=True),
        'administradora_condominio': fields.char(u'Administradora do condomínio', size=60),
        'administradora_condominio_fone': fields.char(u'Fone', size=60),
        'sindico_condominio': fields.char(u'Síndico', size=60),
        'sindico_condominio_fone': fields.char(u'Fone', size=60),

        #
        # Casa
        #
        'muro_altura': fields.float(u'Muro (altura)'),
        'grade': fields.boolean(u'Grade'),
        'cerca_eletrica': fields.boolean(u'Cerca elétrica'),
        'cor_predominante': fields.char(u'Cor predominante', size=60),
        'laje': fields.boolean(u'Laje'),
        'pomar': fields.boolean(u'Pomar'),
        'pomar_obs': fields.text(u'Obs.'),
        'horta': fields.boolean(u'Horta'),
        'mobilia_obs': fields.text(u'Mobília'),
        'maquina_obs': fields.text(u'Maquinário'),
        'cerdado': fields.boolean(u'Cercado'),
        'murado': fields.boolean(u'Murado'),
        'possui_casa': fields.boolean(u'Possui casa?'),


        #
        # Terreno, chácara, etc.
        #
        'construcao': fields.selection(TIPO_CONSTRUCAO, u'Construção'),
        'imovel_arrendado': fields.boolean(u'Imóvel arrendado', select=True),
        'imovel_arrendado_obs': fields.char(u'Obs.', size=60),
        'tipo_testada': fields.selection(TIPO_TESTADA, u'Tipo Testada'),
        'uso_residencial': fields.boolean(u'Residencial'),
        'uso_comercial': fields.boolean(u'Comercial'),
        'uso_lazer': fields.boolean(u'Lazer'),
        'uso_pecuaria': fields.boolean(u'Pecuária'),
        'uso_agricultura': fields.boolean(u'Agricultura'),
        'uso_reflorestamento': fields.boolean(u'Reflorestamento'),
        'uso_obs': fields.char(u'Obs.', size=60),
        'arvores_frutiferas': fields.integer(u'Árvores Frutíferas'),
        'pinheiro': fields.integer(u'Pinheiro(s)'),
        'cultura_area': fields.char(u'Cultura área', size=60),
        'vegetacao': fields.boolean(u'Vegetação'),
        'maquina_equipamento': fields.boolean(u'Máquinas e equipamentos'),
        'animais': fields.boolean(u'Animais'),
        'acude': fields.boolean(u'Açude'),
        'hectare': fields.float(u'Hectares (ha)'),



        #
        # Calculo de Zoneamento
        #
        'zoneamento_item_id': fields.many2one('const.zoneamento.item',u'Zoneamento/plano diretor'),
        'vr_base': fields.function(_get_base, type='float', store=True, digits=(18, 2), string=u'Base'),
        'vr_potencial_construtivo': fields.function(_get_potencial_construtivo, type='float', store=True, digits=(18, 2), string=u'Potencial construtivo'),
        'vr_torre': fields.function(_get_torre, type='float', store=True, digits=(18, 2), string=u'Torre'),
        'vr_altura_maxima': fields.function(_get_altura_maxima, type='float', store=True, digits=(18, 2), string=u'Altura máxima'),
        'numero_pavimento': fields.function(_get_numero_pavimento, type='integer', store=True, string=u'Nº de pavimentos'),
        'tamanho_pavimento_altura_max': fields.function(_get_tamanho_pavimento_altura_max, type='float', store=True, digits=(18, 2), string=u'Tamanho do pavimento usando altura máx'),
        'numero_pavimento_max': fields.function(_get_numero_pavimento_max, type='float', store=True, digits=(18, 2), string=u'Nº de pavimentos pela metragem máxima'),


        #
        # Confrotações
        #
        'confrontacao_norte': fields.text(u'Confrotação norte (N)'),
        'confrontacao_sul': fields.text(u'Confrotação sul (S)'),
        'confrontacao_leste': fields.text(u'Confrotação leste (L)'),
        'confrontacao_oeste': fields.text(u'Confrotação oeste (O)'),
        'confrontacao_nordeste': fields.text(u'Confrotação nordeste (NE)'),
        'confrontacao_sudeste': fields.text(u'Confrotação sudeste (SE)'),
        'confrontacao_noroeste': fields.text(u'Confrotação noroeste (NW)'),
        'confrontacao_sudoeste': fields.text(u'Confrotação sudoeste (SW)'),
        'confrontacoes_contratuais': fields.function(_confrontacoes_contratuais, type='char', string=u'Confrontações contratuais'),

        #
        # Galpões
        #
        'pe_direito': fields.float(u'Pé direito'),
        'mezanino': fields.float(u'Mezanino'),
        'vestiario': fields.float(u'Vestiário(s)'),
        'refeitorio': fields.float(u'Refeitório(s)'),
        'estacionamento': fields.char(u'Estacionamento', size=60),
        'piso_resistencia': fields.char(u'Resistência do piso (peso)', size=60),

        #
        # Prédio
        #
        'predio_sala': fields.boolean(u'Salas/lojas'),
        'predio_apartamento': fields.boolean(u'Apartamentos'),
        'predio_garagem': fields.boolean(u'Garagens'),
        'predio_estacionamento': fields.boolean(u'Estacionamentos'),

        'predio_sala_quantidade': fields.integer(u'Quantidade'),
        'predio_apartamento_quantidade': fields.integer(u'Quantidade'),
        'predio_garagem_quantidade': fields.integer(u'Quantidade'),
        'predio_estacionamento_quantidade': fields.integer(u'Quantidade'),

        'area_predio_sala': fields.float(u'Area (m²)'),
        'area_predio_apartamento': fields.float(u'Area (m²)'),
        'area_predio_garagem': fields.float(u'Area (m²)'),
        'area_predio_estacionamento': fields.float(u'Area (m²)'),

        'predio_sala_obs': fields.char(u'Obeservação', size=120),
        'predio_apartamento_obs': fields.char(u'Obeservação', size=120),
        'predio_garagem_obs': fields.char(u'Obeservação', size=120),
        'predio_estacionamento_obs': fields.char(u'Obeservação', size=120),



        'andares': fields.integer(u'Andares'),
        'apartamentos': fields.integer(u'Apartamentos'),
        'apartamentos_obs': fields.integer(u'Obs.'),
        'salas': fields.integer(u'Salas/escritórios'),

        #
        # Geral
        #
        'matricula_imbobiliaria': fields.char(u'Matrícula imobiliária', size=60),
        'venda': fields.boolean(u'Venda'),
        'locacao': fields.boolean(u'Locação'),
        'valor_venda': fields.float(u'Valor Venda', digits=(18, 2), select=True),
        'valor_locacao': fields.float(u'Valor Locação', digits=(18, 2), select=True),
        'valor_cub': fields.float(u'Valor CUB', digits=(18, 2), select=True),
        'valor_metro_quadrado': fields.function(_valor_metro_quadrado, type='float', digits=(18, 2)),
        'comissao': fields.float(u'Comissão', digits=(18, 2)),
        'quitado': fields.boolean(u'Quitado', select=True),
        'exclusividade': fields.boolean(u'Exclusividade total'),
        'exclusividade_parcial': fields.boolean(u'Exclusividade parcial'),
        'exclusividade_nenhuma': fields.boolean(u'Sem exclusividade'),
        'exclusividade_anunciar': fields.boolean(u'Exclusividade p/ anunciar?'),
        'exclusividade_outras': fields.char(u'Outras imobiliárias', size=60),
        'anunciar_site': fields.boolean(u'Site'),
        'anunciar_jornal': fields.boolean(u'Jornal'),
        'anunciar_radio': fields.boolean(u'Rádio'),
        'anunciar_jornal_obs': fields.text(u'Jornal(is)', size=60),
        'anunciar_outros': fields.text(u'Outros'),
        'condicao_pagamento': fields.text(u'Condições de pagamento'),
        'colocar_placa': fields.boolean(u'Com placa'),
        'placa_colocador': fields.char(u'Placa colocada por', size=60),
        'placa_data_colocacao': fields.date(u'Data'),
        'placa_tipo': fields.char(u'Tipo da placa', size=60),
        'data_vencimento_opcao': fields.date(u'Opção vence em'),
        'restricao': fields.selection(RESTRICOES, u'Restrição'),

        'proprietario_id': fields.many2one('res.partner', u'Proprietário'),
        'locatario_id': fields.many2one('res.partner', u'Locatário'),
        'captador_id': fields.many2one('res.partner', u'Captador'),
        'res_partner_bank_id': fields.many2one('res.partner.bank', u'Conta Bancária', select=True, ondelete='restrict'),
        #'agenciador_id': fields.many2one('res.partner', u'Agenciador'),
        'agenciador_ids': fields.many2many('res.partner', 'const_imovel_agenciador', 'imovel_id', 'partner_id', u'Agenciadores'),
        'sociedade_ids': fields.one2many('const.imovel.sociedade','imovel_id', u'Sociedade'),

        'foto_1': fields.binary(u'Foto 1'),
        'legenda_foto_1': fields.char(u'Foto 1', size=32),
        'foto_2': fields.binary(u'Foto 2'),
        'legenda_foto_2': fields.char(u'Foto 2', size=32),
        'foto_3': fields.binary(u'Foto 3'),
        'legenda_foto_3': fields.char(u'Foto 3', size=32),
        'foto_4': fields.binary(u'Foto 4'),
        'legenda_foto_4': fields.char(u'Foto 4', size=32),
        'foto_5': fields.binary(u'Foto 5'),
        'legenda_foto_5': fields.char(u'Foto 5', size=32),
        'foto_6': fields.binary(u'Foto 6'),
        'legenda_foto_6': fields.char(u'Foto 6', size=32),
        'foto_7': fields.binary(u'Foto 7'),
        'legenda_foto_7': fields.char(u'Foto 7', size=32),
        'foto_8': fields.binary(u'Foto 8'),
        'legenda_foto_8': fields.char(u'Foto 8', size=32),
        'foto_9': fields.binary(u'Foto 9'),
        'legenda_foto_9': fields.char(u'Foto 9', size=32),
        'foto_10': fields.binary(u'Foto 10'),
        'legenda_foto_10': fields.char(u'Foto 10', size=32),
        'foto_11': fields.binary(u'Foto 11'),
        'legenda_foto_11': fields.char(u'Foto 11', size=32),
        'foto_12': fields.binary(u'Foto 12'),
        'legenda_foto_12': fields.char(u'Foto 12', size=32),

        'quantidade_moradores': fields.integer(u'Moradores'),

        #
        # Condições comerciais
        #
        'condicao_ids': fields.one2many('finan.contrato.condicao', 'imovel_id', u'Condições de pagamento'),
    }

    _defaults = {
        'propriedade': 'T',
        'situacao': 'NL',
        'situacao_readonly': 'NL',
        'situacao_contabil': 'D',
    }

    def verifica_condicao_pagamento(self, cr, uid, ids, vals, context=None):
        if ('condicao_ids' not in vals or not vals['condicao_ids']) and ('valor_venda' not in vals):
            return

        condicao_pool = self.pool.get('finan.contrato.condicao')
        imovel_pool = self.pool.get('const.imovel')

        if 'valor_venda' in vals:
            valor_venda = D(vals['valor_venda'] or 0)
        else:
            dados = imovel_pool.read(cr, uid, ids, ['valor_venda'])
            valor_venda = D(dados[0]['valor_venda'] or 0)

        if 'condicao_ids' in vals:
            condicao = vals['condicao_ids']
        else:
            dados = imovel_pool.read(cr, uid, ids, ['condicao_ids'])
            condicao = []
            print(dados)
            for condicao_id in dados[0]['condicao_ids']:
                dados_cond = condicao_pool.read(cr, uid, [condicao_id], ['valor_principal'])
                condicao.append([0, ids[0], {'valor_principal': dados_cond[0]['valor_principal']}])

        condicao_alteradas = []

        total_condicao = D('0')

        for operacao, condicao_id, valores in condicao:
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

            print(operacao, 'operacao', condicao_id, valores)

            if operacao == 0:
                total_condicao += D(valores.get('valor_principal', 0) or 0)

            elif operacao == 5:
                excluido_ids = condicao_pool.search(cr, uid, [('imovel_id', 'in', ids)])
                condicao_alteradas += excluido_ids

            elif operacao == 2:
                condicao_alteradas += [condicao_id]

            elif operacao == 1 and 'valor_principal' in valores:
                condicao_alteradas += [condicao_id]

                for provisao_obj in condicao_pool.browse(cr, uid, [condicao_id]):

                    total_condicao += D(valores.get('valor_principal', 0) or 0)

        #
        # Ajusta com os possíveis não alterados
        #
        condicao_ids = []
        if ids and ids[0]:

            imovel_obj = imovel_pool.browse(cr, uid, ids[0])

            condicao_ids = condicao_pool.search(cr, uid, [('imovel_id', '=', ids[0]), ('id', 'not in', condicao_alteradas)])

            for provisao_obj in condicao_pool.browse(cr, uid, condicao_ids):
                total_condicao += D(str(provisao_obj.valor_principal or 0))

        total_condicao = total_condicao.quantize(D('0.01'))
        if total_condicao > valor_venda:
            raise osv.except_osv(u'Inválido !', u'Valor total da condição de pagamento deve ser igual ao valor de venda!')


    def create(self, cr, uid, dados, context={}):
        if 'cnpj_cpf' in dados and dados['cnpj_cpf']:
            cnpj_cpf = limpa_formatacao(dados['cnpj_cpf'])
            if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
                raise osv.except_osv(u'Erro!', u'CNPJ ou CPF inválido!')

            if len(cnpj_cpf) == 14:
                dados['cnpj_cpf'] = formata_cnpj(cnpj_cpf)
            else:
                dados['cnpj_cpf'] = formata_cpf(cnpj_cpf)

            #
            # Impede a inclusão do mesmo CNPJ mais de uma vez
            #
            cnpj_ids = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', dados['cnpj_cpf'])])

            if len(cnpj_ids) > 0:
                raise osv.except_osv(u'Erro!', u'CNPJ/CPF já existe no cadastro!')

        if 'fone' in dados and dados['fone']:
            fone = dados['fone']
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                raise osv.except_osv(u'Erro!', u'Telefone fixo inválido!')

            dados['fone'] = formata_fone(fone)

        if 'celular' in dados and dados['celular']:
            fone = dados['celular']
            if not valida_fone_internacional(fone) and not valida_fone_celular(fone):
                raise osv.except_osv(u'Erro!', u'Telefone celular inválido!')

            dados['celular'] = formata_fone(fone)

        if 'suframa' in dados and dados['suframa']:
            suframa = dados['suframa']
            if not valida_inscricao_estadual(unicode(suframa), 'SUFRAMA'):
                raise osv.except_osv(u'Erro!', u'Inscrição na SUFRAMA inválida!')

            dados['suframa'] = formata_inscricao_estadual(unicode(suframa), 'SUFRAMA')

        if 'ie' in dados:
            dados['ie'] = dados['ie'] or u''

            if 'municipio_id' in dados:
                municipio_id = dados['municipio_id']
                ie = dados['ie']
                municipio_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_id)

                if dados['contribuinte'] == u'1' and ie.strip().upper() == u'ISENTO':
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode ser “ISENTO”!')

                if dados['contribuinte'] == u'1' and len(ie.strip()) == 0:
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode estar em branco!')

                if not valida_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf):
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual inválida!')

                dados['ie'] = formata_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf)

            elif (dados['ie'] != 'ISENTO' or len(dados['ie']) == 0) and dados['contribuinte']:
                raise osv.except_osv(u'Erro!', u'Informando inscrição estadual sem informar o município!')

        if 'cep' in dados and dados['cep']:
            cep = dados['cep']

            cep = limpa_formatacao(cep)
            if not cep.isdigit() or len(cep) != 8:
                raise osv.except_osv(u'Erro!', u'CEP inválido!')

            dados['cep'] = cep[:5] + '-' + cep[5:]

        if 'razao_social' in dados and not dados['razao_social']:
            dados['razao_social'] = dados['name']

        self.verifica_percentual(cr, uid, [], dados)
        self.verifica_condicao_pagamento(cr, uid, [], dados)

        return super(const_imovel, self).create(cr, uid, dados, context)

    def write(self, cr, uid, ids, dados, context={}):
        if 'cnpj_cpf' in dados and dados['cnpj_cpf']:
            cnpj_cpf = limpa_formatacao(dados['cnpj_cpf'])
            if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
                raise osv.except_osv(u'Erro!', u'CNPJ ou CPF inválido!')

            if len(cnpj_cpf) == 14:
                dados['cnpj_cpf'] = formata_cnpj(cnpj_cpf)
            else:
                dados['cnpj_cpf'] = formata_cpf(cnpj_cpf)

            #
            # Impede a inclusão do mesmo CNPJ mais de uma vez, exceto quando for o CNPJ de
            # uma company
            #
            company_ids = self.pool.get('res.company').search(cr, 1, [('partner_id', 'in', ids)])

            print('company_ids', company_ids)

            if len(company_ids) == 0:
                cnpj_ids = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', dados['cnpj_cpf'])])

                if len(cnpj_ids) > 0 and ids[0] not in cnpj_ids:
                    raise osv.except_osv(u'Erro!', u'CNPJ/CPF já existe no cadastro!')

        if 'fone' in dados and dados['fone']:
            fone = dados['fone']
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                raise osv.except_osv(u'Erro!', u'Telefone fixo inválido!')

            dados['fone'] = formata_fone(fone)

        if 'celular' in dados and dados['celular']:
            fone = dados['celular']
            if not valida_fone_internacional(fone) and not valida_fone_celular(fone):
                raise osv.except_osv(u'Erro!', u'Telefone celular inválido!')

            dados['celular'] = formata_fone(fone)

        if 'suframa' in dados and dados['suframa']:
            suframa = dados['suframa']
            if not valida_inscricao_estadual(suframa, 'SUFRAMA'):
                raise osv.except_osv(u'Erro!', u'Inscrição na SUFRAMA inválida!')

            dados['suframa'] = formata_inscricao_estadual(suframa, 'SUFRAMA')

        if 'ie' in dados:
            dados['ie'] = dados['ie'] or u''

            if 'municipio_id' in dados:
                municipio_id = dados['municipio_id']
                ie = dados['ie']
                municipio_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_id)

                if dados['contribuinte'] == u'1' and ie.strip().upper() == u'ISENTO':
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode ser “ISENTO”!')

                if dados['contribuinte'] == u'1' and len(ie.strip()) == 0:
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode estar em branco!')

                if not valida_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf):
                    raise osv.except_osv(u'Erro!', u'Inscrição estadual inválida!')

                dados['ie'] = formata_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf)

            #elif (dados['ie'] != 'ISENTO' or len(dados['ie']) == 0) and dados['contribuinte']:
                #raise osv.except_osv(u'Erro!', u'Informando inscrição estadual sem informar o município!')

        if 'cep' in dados and dados['cep']:
            cep = dados['cep']

            cep = limpa_formatacao(cep)
            if not cep.isdigit() or len(cep) != 8:
                raise osv.except_osv(u'Erro!', u'CEP inválido!')

            dados['cep'] = cep[:5] + '-' + cep[5:]

        self.verifica_percentual(cr, uid, ids, dados)
        self.verifica_condicao_pagamento(cr, uid, ids, dados)

        return super(const_imovel, self).write(cr, uid, ids, dados, context)

    def onchange_cnpj_cpf(self, cr, uid, ids, cnpj_cpf, context={}):
        if not cnpj_cpf:
            return {}

        if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
            raise osv.except_osv(u'Erro!', u'CNPJ ou CPF inválido!')

        cnpj_cpf = limpa_formatacao(cnpj_cpf)

        if len(cnpj_cpf) == 14:
            cnpj_cpf = formata_cnpj(cnpj_cpf)
        else:
            cnpj_cpf = formata_cpf(cnpj_cpf)

        if ids != []:
            cnpj_ids = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', cnpj_cpf), '!', ('id', 'in', ids)])
        else:
            cnpj_ids = self.pool.get('res.partner').search(cr, uid, [('cnpj_cpf', '=', cnpj_cpf)])

        if len(cnpj_ids) > 0:
            return {'value': {'cnpj_cpf': cnpj_cpf}, 'warning': {'title': u'Aviso!', 'message': u'CNPJ/CPF já existe no cadastro!'}}

        return {'value': {'cnpj_cpf': cnpj_cpf}}

    def onchange_fone_celular(self, cr, uid, ids, fone, celular, context={}):
        print(fone, celular)
        if fone is not None and fone:
            if not valida_fone_internacional(fone) and not valida_fone_fixo(fone):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Telefone fixo inválido!'}}

            fone = formata_fone(fone)
            return {'value': {'fone': fone}}

        elif celular is not None and celular:
            if not valida_fone_internacional(celular) and not valida_fone_celular(celular):
                return {'value': {}, 'warning': {'title': u'Erro!', 'message': u'Celular inválido!'}}

            celular = formata_fone(celular)
            return {'value': {'celular': celular}}

    def onchange_cep(self, cr, uid, ids, cep, contex={}):
        if not cep:
            return {}

        cep = limpa_formatacao(cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise osv.except_osv(u'Erro!', u'CEP inválido!')

        return {'value': {'cep': cep[:5] + '-' + cep[5:]}}

    def onchange_suframa(self, cr, uid, ids, suframa, context={}):
        if not suframa:
            return {}

        if not valida_inscricao_estadual(suframa, 'SUFRAMA'):
            raise osv.except_osv(u'Erro!', u'Inscrição na SUFRAMA inválida!')

        return {'value': {'suframa': formata_inscricao_estadual(suframa, 'SUFRAMA')}}

    def onchange_ie(self, cr, uid, ids, ie, municipio_id, contribuinte, context={}):
        if not ie:
            return {}

        if not municipio_id:
            raise osv.except_osv(u'Erro!', u'Para validação da inscrição estadual é preciso informar o município!')

        municipio_obj = self.pool.get('sped.municipio').browse(cr, uid, municipio_id)

        if contribuinte == u'1' and ie.strip().upper() == u'ISENTO':
            raise osv.except_osv(u'Erro!', u'Inscrição estadual para contribuinte não pode ser “ISENTO”!')

        if not valida_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf):
            raise osv.except_osv(u'Erro!', u'Inscrição estadual inválida!')

        return {'value': {'ie': formata_inscricao_estadual(unicode(ie), municipio_obj.estado_id.uf)}}

    def address_get(self, cr, uid, ids, adr_pref=['default']):
        tipos_endereco = adr_pref
        address_pool = self.pool.get('res.partner.address')
        address_ids = address_pool.search(cr, uid, [('partner_id', 'in', ids)])
        address_rec = address_pool.read(cr, uid, address_ids, ['type'])
        res = list((addr['type'], addr['id']) for addr in address_rec)
        adr = dict(res)
        # get the id of the (first) default address if there is one,
        # otherwise get the id of the first address in the list
        if res:
            default_address = adr.get('default', res[0][1])
        else:
            default_address = False

        #
        # Caso não exista um endereço padrão, cria um
        #
        if not default_address:
            partner_id = ids[0]
            partner_obj = self.browse(cr, uid, partner_id)

            street = ''
            street2 = ''
            zip = ''
            city = ''
            country_id = False
            state_id = False

            if partner_obj.endereco:
                street = partner_obj.endereco

            if partner_obj.numero:
                street += ', ' + partner_obj.numero

            if partner_obj.complemento:
                street += ' - ' + partner_obj.complemento

            if partner_obj.bairro:
                street2 = partner_obj.bairro

            if partner_obj.cep:
                if len(partner_obj.cep) >= 8:
                    zip = partner_obj.cep[:5] + '-' + partner_obj.cep[5:]
                else:
                    zip = partner_obj.cep

            if partner_obj.municipio_id:
                country_id = partner_obj.municipio_id.pais_id.res_country_id.id
                state_id = partner_obj.municipio_id.estado_id.res_country_state_id.id
                city = partner_obj.municipio_id.nome

            dados = {
                    'partner_id': partner_id,
                    'name': partner_obj.name,
                    'phone': partner_obj.fone,
                    'mobile': partner_obj.celular,
                    'email': partner_obj.email_nfe,
                    'street': street,
                    'street2': street2,
                    'zip': zip,
                    'city': city,
                    'country_id': country_id,
                    'state_id': state_id,
                    'endereco': partner_obj.endereco,
                    'numero': partner_obj.numero,
                    'complemento': partner_obj.complemento,
                    'cep': partner_obj.cep,
                    'bairro': partner_obj.bairro,
                    'municipio_id': partner_obj.municipio_id and partner_obj.municipio_id.id or False,
            }

            default_address = address_pool.create(cr, uid, dados)

        result = {}
        for tipo in tipos_endereco:
            result[tipo] = adr.get(tipo, default_address)
        return result

    _sql_constraints = [
        ('unique_codigo', 'UNIQUE(codigo)', u'Não é permitido criar código repetidos!')
    ]

    def copy(self, cr, uid, id, default={}, context={}):
        #print('default', default)

        default.update({
            'codigo': False,
        })

        res = super(osv.Model, self).copy(cr, uid, id, default, context=context)

        return res

    def verifica_percentual(self, cr, uid, ids, vals, context=None):
        if 'sociedade_ids' not in vals or not vals['sociedade_ids']:
            return

        sociedades = vals['sociedade_ids']
        sociedade_alteradas = []

        total_percentual = D('0')

        for operacao, socio_id, valores in sociedades:
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

            print(operacao, 'operacao', socio_id, valores)

            if operacao == 0:
                total_percentual += D(valores.get('percentual', 0) or 0)

            if operacao == 5:
                excluido_ids = self.pool.get('const.imovel.sociedade').search(cr, uid, [('imovel_id', 'in', ids)])
                sociedade_alteradas += excluido_ids

            if operacao == 2:
                sociedade_alteradas += [socio_id]

            if operacao == 1 and 'percentual' in valores:
                sociedade_alteradas += [socio_id]
                total_percentual += D(valores.get('percentual', 0) or 0)

        #
        # Ajusta com os possíveis não alterados
        #

        sociedades_ids = []
        if ids and ids[0]:
            sociedade_pool = self.pool.get('const.imovel.sociedade')
            sociedades_ids = sociedade_pool.search(cr, uid, [('imovel_id', '=', ids[0]), ('id', 'not in', sociedade_alteradas)])

            for sociedade_obj in sociedade_pool.browse(cr, uid, sociedades_ids):
                total_percentual += D(str(sociedade_obj.percentual or 0))
        print(total_percentual)
        if total_percentual != 100 and total_percentual != 0:
            raise osv.except_osv(u'Erro!', u'A soma dos percentuais dos sócios deve ser igual a 100%')


    def onchange_cep_id(self, cr, uid, ids, cep_id):
        cep_pool = self.pool.get('res.cep')

        valores = cep_pool.onchange_consulta_cep(cr, uid, False, cep_id)

        return {'value': valores}

    def guarda_selecao_usuario(self, cr, uid, ids, context={}):
        if not context or 'active_ids' not in context:
            return False

        user_pool = self.pool.get('res.users')
        user_obj = user_pool.browse(cr, 1, uid)

        imovel_ids = context['active_ids']
        for imovel_obj in user_obj.imovel_ids:
            if imovel_obj.id not in imovel_ids:
                imovel_ids.append(imovel_obj.id)

        cr.execute('delete from res_user_imovel where user_id = ' + str(uid) + ';')
        for imovel_id in imovel_ids:
            cr.execute('insert into res_user_imovel (user_id, imovel_id) values ({uid}, {imovel_id});'.format(uid=uid, imovel_id=imovel_id))
        cr.commit()

        return {}

    def limpa_selecao_usuario(self, cr, uid, ids, context={}):
        cr.execute('delete from res_user_imovel where user_id = ' + str(uid) + ';')
        cr.commit()
        return {}

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        novo_args = []

        for busca in args:
            print(busca)
            if isinstance(busca, (list, tuple)) and isinstance(busca[2], (str, unicode)) and 'minha_selecao_imovel_ids' in busca[2]:
                user_obj = self.pool.get('res.users').browse(cr, uid, uid)
                imovel_ids = []

                if len(user_obj.imovel_ids):
                    imovel_ids = [imovel_obj.id for imovel_obj in user_obj.imovel_ids]

                busca[2] = imovel_ids

            novo_args.append(busca)

        res = super(const_imovel, self).search(cr, uid, novo_args, offset=offset, limit=limit, order=order, context=context, count=count)

        return res

    def inclui_lead(self, cr, uid, ids, context={}):
        print(context, 'inclui interesse')
        if 'prospecto' in context:
            lead_pool = self.pool.get('crm.lead')
            lead_obj = lead_pool.browse(cr, uid, context['prospecto'])

            jah_tem = []
            for imovel_obj in lead_obj.imovel_ids:
                jah_tem.append(imovel_obj.id)

            for imovel_id in ids:
                if not imovel_id in jah_tem:
                    jah_tem.append(imovel_id)

            print('jah_tem', jah_tem)

            cr.execute('delete from crm_lead_imovel where lead_id = ' + str(lead_obj.id) + ';')

            for imovel_id in jah_tem:
                sql = 'insert into crm_lead_imovel (lead_id, imovel_id) values ({lead_id}, {imovel_id});'.format(lead_id=lead_obj.id, imovel_id=imovel_id)
                print(sql)
                cr.execute(sql)
                sql = 'delete from crm_lead_imovel_busca where lead_id = {lead_id} and imovel_id = {imovel_id};'.format(lead_id=lead_obj.id, imovel_id=imovel_id)
                print(sql)
                cr.execute(sql)

        return {}

    def onchange_area_contruida_casa(self, cr, uid, ids, area_construida_averbada, area_construida_nao_averbada, context={}):
        res = {}
        valores = {}
        res['value'] = valores

        area_total = D(area_construida_averbada or 0) + D(area_construida_nao_averbada or 0)
        valores['area_total'] = area_total

        return res

    def inclui_proposta(self, cr, uid, ids, context={}):
        if not ids:
            return

        partner_id = context.get('partner_id', False)
        crm_lead_id = context.get('crm_lead_id', False)
        corretor_id = context.get('corretor_id', False)
        imovel_id = ids[0]

        if not (partner_id and crm_lead_id and imovel_id and corretor_id):
            return

        imovel_obj = self.pool.get('const.imovel').browse(cr, uid, imovel_id, context=context)

        if imovel_obj.proposta_id:
            return

        dados = {
            'imovel_id': imovel_id,
            'crm_lead_id': crm_lead_id,
            'vendedor_id': corretor_id,
            'partner_id': partner_id,
            'natureza': 'RI',
            'etapa_id': 1,
        }

        print('vai criar o contrato')
        contrato_id = self.pool.get('finan.contrato').create(cr, uid, dados)
        self.pool.get('finan.contrato').write(cr, uid, [contrato_id], {'numero': str(hoje().year) + '-' + str(contrato_id)})

        print('contrato criado', contrato_id)

        return True


const_imovel()


class const_imovel_sociedade(osv.Model):
    _name = 'const.imovel.sociedade'
    _rec_name = 'Imovel Sociedade'


    _columns = {
        'imovel_id': fields.many2one('const.imovel', u'Imóvel', on_delete='cascade'),
        'socio_id': fields.many2one('res.partner', u'Sócio', on_delete='restrict'),
        'res_partner_bank_id': fields.many2one('res.partner.bank',u'Banco'),
        'percentual': fields.float(u'Percentual'),
        }

    _defaults = {
        'percentual': 0,
    }

const_imovel_sociedade()


