##############################################################################
#
# Copyright (c) 2008-2012 NaN Projectes de Programari Lliure, S.L.
#                         http://www.NaN-tic.com
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from jasper_report import *
from report_xml import *
import wizard
import os

import release
if release.major_version != '5.0':
    from http_server import *


DIR_ATUAL = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.join(DIR_ATUAL, '../../integra/reports/base/')
LOGO_DIR = os.path.join(DIR_ATUAL, '../../integra/reports/logo/')

if os.path.exists(os.path.join(LOGO_DIR, 'logo.png')):
    LOGO_CLIENTE = os.path.join(LOGO_DIR, 'logo.png')
elif os.path.exists(os.path.join(LOGO_DIR, 'logo.jpg')):
    LOGO_CLIENTE = os.path.join(LOGO_DIR, 'logo.jpg')
elif os.path.exists(os.path.join(LOGO_DIR, 'logo.jpeg')):
    LOGO_CLIENTE = os.path.join(LOGO_DIR, 'logo.jpeg')
else:
    LOGO_CLIENTE = os.path.join(LOGO_DIR, 'integra/logo.jpg')

arq_report_properties = open(os.path.join(DIR_ATUAL, 'report.properties'), 'w')
arq_report_properties.write('''BASE_DIR=%s
LOGO_DIR=%s
LOGO_CLIENTE=%s''' % (BASE_DIR, LOGO_DIR, LOGO_CLIENTE))
arq_report_properties.close()

arq_report_properties = open(os.path.join(DIR_ATUAL, '../../integra/reports/report.properties'), 'w')
arq_report_properties.write('''BASE_DIR=%s
LOGO_DIR=%s
LOGO_CLIENTE=%s''' % (BASE_DIR, LOGO_DIR, LOGO_CLIENTE))
arq_report_properties.close()
