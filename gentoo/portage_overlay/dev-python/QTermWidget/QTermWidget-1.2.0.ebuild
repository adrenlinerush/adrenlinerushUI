# Copyright 1999-2023 Gentoo Authors 
# Distributed under the terms of the GNU General Public License v2 
 
# please keep this ebuild at EAPI 7 -- sys-apps/portage dep 
EAPI=7 
 
DISTUTILS_USE_PEP517=sip
PYTHON_COMPAT=( python3_{9..11} pypy3 ) 
 
inherit distutils-r1
 
DESCRIPTION="PyQt5 bindings for QTermWidget" 
HOMEPAGE="https://github.com/adrenlinerush/qtermwidget" 
SRC_URI="https://github.com/adrenlinerush/qtermwidget/releases/download/v${PV}/${P}.tar.gz"
 
LICENSE="GPL-2+" 
SLOT="0" 
KEYWORDS="amd64" 
 
BDEPEND=" 
    >=x11-libs/qtermwidget-1.2.0
    >=dev-python/PyQt5-5.15.7
" 
