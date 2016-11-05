# -*- coding: utf-8 -*-

from __future__ import (division, print_function, unicode_literals,
                        absolute_import)

from .noh_base import NohXML


class TagCaracter(NohXML):
    def __init__(self, *args, **kwargs):
        super(TagCaracter, self).__init__(*args, **kwargs)
        self.valor = ''
        self.obrigatorio = True
        self.propriedade = None
        self.namespace_obrigatorio = False

    @property
    def valor(self):
        return self._valor

    @valor.setter
    def valor(self, valor):
        if valor:
            if isinstance(valor, str):
                self.valor = valor.decode('utf-8')

            elif isinstance(valor, unicode):
                self._valor = valor
                self._texto = self.valor

        else:
            self._valor = ''
            self._texto = self.valor

    @property
    def texto(self):
        return self._texto

    def __unicode__(self):
        return self.text

    def __repr__(self):
        return self.__unicode__().encode('utf-8')

    @property
    def xml(self):
        if (not self.obrigatorio) and (not self.valor):
            texto = ''
        else:
            texto = '<%s' % self.nome

            if self.namespace and self.namespace_obrigatorio:
                texto += ' xmlns="%s"' % self.namespace

            if self.propriedade:
                texto += ' %s="%s">' % (self.propriedade, self.texto)

            elif self.texto:
                texto += '>%s</%s>' % (self.texto, self.nome)

            else:
                texto += ' />'

        return texto

    @xml.setter
    def xml(self, arquivo_xml):
        self.arquivo_xml = arquivo_xml

    @property
    def text(self):
        if self.propriedade:
            return '%s_%s=%s' % (self.nome, self.propriedade, self.texto)
        else:
            return '%s=%s' % (self.nome, self.texto)
