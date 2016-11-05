# -*- coding: utf-8 -*-


from osv import osv, fields
from consulta_cnpj import executa_consulta, cookie_receita
# from pysped.tabela import MUNICIPIO_ESTADO_NOME
from consulta_cnae import executa_consulta_cnae

class wizard_consulta_cnpj(osv.osv_memory):
    _name = 'sped.consulta_cnpj'
    _description = 'SPED - Consulta CNPJ'

    _columns = {
        'texto_captcha': fields.char('Texto da imagem', size=6),
        'imagem': fields.binary(u'Imagem anti-robô'),
        'certificado_captcha': fields.text('Certificado do Captcha'),
        'cookie': fields.text('Cookie', size=80),
        'cnpj': fields.char('CNPJ', size=14),
        'partner_id': fields.many2one('res.partner'),
        'mensagem': fields.text('Mensagem', size=150)
    }

    def atualiza_captcha(self, cursor, user_id, ids, *args, **kwargs):
        dados = cookie_receita()

        if 'mensagem' in kwargs:
            dados['mensagem'] = kwargs['mensagem']

        consulta_id = self.write(cursor, user_id, ids, dados)
        return consulta_id

    def acao_consultar_cnpj(self, cursor, user_id, ids, context=None):
        consulta_cnpj = self.browse(cursor, user_id, ids, context)[0]

        if len(consulta_cnpj.cnpj) != 14:
            raise osv.except_osv(u'Atenção', u'O CNPJ deve ter 14 dígitos!')

        #try:
        #print(consulta_cnpj.cookie, consulta_cnpj.cnpj, consulta_cnpj.certificado_captcha, consulta_cnpj.texto_captcha.upper())
        consulta = executa_consulta(consulta_cnpj.cookie, consulta_cnpj.cnpj, consulta_cnpj.certificado_captcha, consulta_cnpj.texto_captcha)
        #except:
            #return False

        #print(consulta)

        if 'erro_letras' in consulta:
            self.atualiza_captcha(cursor, user_id, ids, mensagem=u'Erro na consulta! CNPJ inválido ou letras da imagem incorretas!')
            return {
                'name': 'Consulta CNPJ na Receita Federal',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'sped.consulta_cnpj',
                'context': "{}",
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'res_id': consulta_cnpj.id or False,
            }

        if 'cnpj_nao_existe' in consulta:
            self.atualiza_captcha(cursor, user_id, ids, mensagem=u'Erro na consulta! O CNPJ não existe na base da Receita Federal!')
            return {
                'name': 'Consulta CNPJ na Receita Federal',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'sped.consulta_cnpj',
                'context': "{}",
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'res_id': consulta_cnpj.id or False,
            }
            #consulta_cnpj.atualiza_captcha(cursor, user_id, ids)
            #raise osv.except_osv(u'Atenção', u'O CNPJ não existe na base da Receita Federal!')

        dados_partner = {
            'cnpj_cpf': consulta['cnpj'].replace('.', '').replace('/', '').replace('-', '').strip(),
            'razao_social': consulta['nome'].strip(),
            'fantasia': consulta['fantasia'].strip(),
            'endereco': consulta['endereco'].strip(),
            'numero': consulta['numero'].strip(),
            'complemento': consulta['complemento'].strip(),
            'bairro': consulta['bairro'].strip(),
            'cep': consulta['cep'].replace('.', '').replace('/', '').replace('-', '').strip(),
        }

        #
        # Busca a cidade
        #
        municipio_id = None

        if consulta['estado'] in MUNICIPIO_ESTADO_NOME and consulta['cidade'] in MUNICIPIO_ESTADO_NOME[consulta['estado']]:
            codigo_ibge = MUNICIPIO_ESTADO_NOME[consulta['estado']][consulta['cidade']].codigo_ibge + '0000'
            busca_municipio = [('codigo_ibge', '=', codigo_ibge)]
            municipio_id = self.pool.get('sped.municipio').search(cursor, user_id, busca_municipio)

        if not municipio_id:
            consulta_cnpj.atualiza_captcha(cursor, user_id, ids)
            raise osv.except_osv(u'Atenção', u'Erro no busca do código do município!')

        dados_partner['municipio_id'] = municipio_id[0]

        self.pool.get('res.partner').write(cursor, user_id, [consulta_cnpj.partner_id.id], dados_partner)

        #
        # Adiciona os CNAE
        #
        for codigo_cnae in consulta['cnae']:
            cnae_ids = self.pool.get('sped.cnae').search(cursor, user_id, [('codigo', '=', codigo_cnae)])

            if cnae_ids == []:
                #
                # Incluir o CNAE
                #
                consulta_cnae = executa_consulta_cnae(codigo_cnae)

                if 'descricao' in consulta_cnae:
                    cnae_id = self.pool.get('sped.cnae').create(cursor, user_id,
                        {
                            'codigo': codigo_cnae,
                            'descricao': consulta_cnae['descricao']
                        }
                    )
                    cnae_ids = [cnae_id]

            for cnae_id in cnae_ids:
                #
                # Técnica usada para inserir relacionamentos em campos many2many
                # http://stackoverflow.com/questions/9377402/insert-into-many-to-many-openerp
                #
                self.pool.get('res.partner').write(cursor, user_id, consulta_cnpj.partner_id.id,
                    {
                        'cnae_ids': [(4, cnae_id)]
                    }
                )

        if consulta['cnae']:
            #
            # O primeiro da lista é o CNAE principal
            #
            cnae_ids = self.pool.get('sped.cnae').search(cursor, user_id, [('codigo', '=', consulta['cnae'][0])])

            if cnae_ids:
                self.pool.get('res.partner').write(cursor, user_id, consulta_cnpj.partner_id.id,
                    {
                        'cnae_id': cnae_ids[0]
                    }
                )

        return {'type': 'ir.actions.act_window_close'}

wizard_consulta_cnpj()
