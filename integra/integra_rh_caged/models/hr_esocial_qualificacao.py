# -*- coding: utf-8 -*-


from osv import orm, fields, osv
from pybrasil.base import tira_acentos
from pybrasil.data import parse_datetime, hoje
import base64
from hr_caged import limpa_caged


class hr_esocial_qualificacao(orm.Model):
    _name = 'hr.esocial_qualificacao'
    _description = u'Arquivo Qualificação eSocial'
    #_order = 'ano desc, mes desc, data desc, company_id'

    _columns = {
        'company_id': fields.many2one('res.company', u'Empresas'),
        'nome_arquivo': fields.char(u'Nome arquivo', size=30),
        'data': fields.date(u'Data do Arquivo'),
        #'tipo_alteracao': fields.selection([('1', 'Nada a Alterear'), ('2', u'Alterar Dados Cadastrais'), ('3', u'Fechamento do Estabelecimento')], u'Alteração'),
        'arquivo': fields.binary(u'Arquivo'),
        'arquivo_texto': fields.text(u'Arquivo'),
    }

    _defaults = {
        'data': fields.date.today,
    }

    def gera_arquivo(self, cr, uid, ids, context={}):
        contract_pool = self.pool.get('hr.contract')

        for qualificacao_obj in self.browse(cr, uid, ids):
            contract_ids = contract_pool.search(cr, uid, [('company_id', '=', qualificacao_obj.company_id.id), '|', ('date_end', '=', False), ('date_end', '>=', qualificacao_obj.data)])

            arquivo = u''
            for contrato_obj in contract_pool.browse(cr, uid, contract_ids):
                if contrato_obj.employee_id.cpf:
                    arquivo += contrato_obj.employee_id.cpf.strip()
                arquivo += ';'

                if contrato_obj.employee_id.nis:
                    arquivo += contrato_obj.employee_id.nis.strip()
                arquivo += ';'

                if contrato_obj.employee_id.nome:
                    arquivo += contrato_obj.employee_id.nome.strip()
                arquivo += ';'

                if contrato_obj.employee_id.data_nascimento:
                    arquivo += parse_datetime(contrato_obj.employee_id.data_nascimento).date().strftime('%d%m%Y')
                arquivo += ';'
                arquivo += '\r\n'

            arquivo = arquivo.upper()
            arquivo = arquivo.encode('utf-8')

            dados = {
                'nome_arquivo': 'qualificacao_esocial.txt',
                'arquivo_texto': arquivo,
                'arquivo': base64.encodestring(arquivo),
            }
            qualificacao_obj.write(dados)

        return True
