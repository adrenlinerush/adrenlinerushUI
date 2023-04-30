# Copyright 1999-2023 Gentoo Authors 
# Distributed under the terms of the GNU General Public License v2 
 
# please keep this ebuild at EAPI 7 -- sys-apps/portage dep 
EAPI=7 
 
DISTUTILS_USE_PEP517=poetry
PYTHON_COMPAT=( python3_{9..11} pypy3 ) 
 
inherit distutils-r1 pypi
 
DESCRIPTION="VNC QT Widget for Python using PyQt5"
HOMEPAGE="
    https://pypi.org/project/qvncwidget
	https://github.com/zocker-160/pyQVNCWidget
"
 
LICENSE="GPL-3+" 
SLOT="0" 
KEYWORDS="amd64 arm64" 
 
BDEPEND=" 
    >=dev-python/PyQt5-5.15.7
	>=dev-python/pyDes-2.0.1
	>=dev-python/twisted-22.10.0
" 
