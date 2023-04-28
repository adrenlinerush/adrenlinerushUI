# Copyright 1999-2023 Gentoo Authors 
# Distributed under the terms of the GNU General Public License v2 
 
# please keep this ebuild at EAPI 7 -- sys-apps/portage dep 
EAPI=7 
 
DISTUTILS_USE_PEP517=setuptools
PYTHON_COMPAT=( python3_{9..11} pypy3 ) 
 
inherit distutils-r1
 
DESCRIPTION="PyQt5 UI intended for use on Linux Framebuffer"
HOMEPAGE="https://github.com/adrenlinerush/adrenlinerushUI"
SRC_URI="https://github.com/adrenlinerush/adrenlinerushUI/releases/download/v${PV}/${P}.tar.gz"
 
LICENSE="GPL-2" 
SLOT="0" 
KEYWORDS="amd64" 
 
BDEPEND=" 
	>=dev-python/QTermWidget-1.2.0
	>=dev-python/PyQt5-5.15.7[dbus,declarative,gui,multimedia,network,opengl,printsupport,sql,ssl,webchannel,widgets]
	>=dev-python/qvncwidget-0.2.4
	>=dev-qt/qtgui-5.15.8-r3[linuxfb,jpeg,udev,evdev,-libinput]
	>=dev-qt/qtmultimedia-5.15.8[widgets,gstreamer]
	>=dev-qt/qtwebchannel-5.15.8[qml]
	>=dev-qt/qtwebengine-5.15.8[widgets,-bindist]
	>=dev-qt/qtcore-5.15.8-r3[icu]
	>=dev-qt/qtprintsupport-5.15.8[cups]
	>=sys-power/acpi-1.7-r1
	>=dev-python/qtawesome-1.2.2
	>=dev-python/qdarkstyle-3.1
	>=dev-python/PyQtWebEngine-5.15.6
	>=media-plugins/gst-plugins-meta-1.20.4
" 
