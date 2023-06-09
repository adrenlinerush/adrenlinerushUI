#!/usr/bin/python3
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from qvncwidget import QVNCWidget
from QTermWidget import QTermWidget
import os, sys, logging#, qdarkstyle 
import subprocess, time, threading, datetime
from shutil import which
import qtawesome as qta
logging.basicConfig(filename="ui.log", encoding='utf-8', level=logging.ERROR)
textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
os.environ["TERM"] = "konsole-256color"

class MDIArea(QMdiArea):

    def __init__(self, background_pixmap, parent = None):
    
        QMdiArea.__init__(self, parent)
        self.background_pixmap = background_pixmap
        self.centered = False
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self.viewport())
        
        if not self.centered:
            painter.drawPixmap(0, 0, self.width(), self.height(), self.background_pixmap)
        else:
            painter.fillRect(event.rect(), self.palette().color(QPalette.Window))
            x = (self.width() - self.display_pixmap.width())/2
            y = (self.height() - self.display_pixmap.height())/2
            painter.drawPixmap(x, y, self.display_pixmap)
        
        painter.end()
    
    def resizeEvent(self, event):
    
        self.display_pixmap = self.background_pixmap.scaled(event.size(), Qt.KeepAspectRatio)


class statusBar(QObject):

    def __init__(self, status_bar):
        super().__init__()
        self.status_bar = status_bar
        self.is_acpi = which('acpi') is not None

    def update_status_bar(self):
        try:
            while True: 
                current = datetime.datetime.now()
                status_text = current.strftime("%m-%d-%Y %H:%M")
                if self.is_acpi:
                    acpi_info = subprocess.check_output(['acpi'], shell=True)
                    battery = acpi_info.decode('utf-8')
                    status_text = current.strftime("%m-%d-%Y %H:%M")+"\t\t"+battery
                self.status_bar.showMessage(status_text)
                time.sleep(1)
        except Exception as e:
            logging.error("App.update_status")
            logging.error(e)
            logging.exception("message")


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        try:
            self.setWindowIcon(QIcon('adrenaline.png'))
            self.shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"),self)
            self.shortcut_quit.activated.connect(QApplication.instance().quit)
            self.bg_img = QPixmap('adrenaline.jpg')
            self.mdi = MDIArea(self.bg_img)
            self.mdi.subWindowActivated.connect(self.update_window_list)
            self.shortcut_next_window = QShortcut(QKeySequence("Alt+Tab"), self)
            self.shortcut_next_window.activated.connect(self.mdi.activateNextSubWindow)
            self.shortcut_tile_windows = QShortcut(QKeySequence("Alt+T"), self)
            self.shortcut_tile_windows.activated.connect(self.mdi.tileSubWindows)
            self.shortcut_restore_window = QShortcut(QKeySequence("Alt+R"), self)
            self.shortcut_restore_window.activated.connect(lambda: self.mdi.activeSubWindow().setWindowState(Qt.WindowNoState))
            self.shortcut_maximize_window = QShortcut(QKeySequence("Alt+M"), self)
            self.shortcut_maximize_window.activated.connect(lambda: self.mdi.activeSubWindow().setWindowState(Qt.WindowMaximized))
            self.setCentralWidget(self.mdi)
            self.add_terminal()
            self.add_tabbed_browser()
            bar = self.menuBar()
		
            start = bar.addMenu("Start")
            start.addAction("Quit")
            start.addAction("Terminal")
            start.addAction("Web Browser")
            start.addAction("File Manager")
            start.addAction("Media Player")
            start.addAction("Vnc Client")
            start.addAction("Calculator")
            start.triggered[QAction].connect(self.start)

            view = bar.addMenu("View")
            view.addAction("Tile")
            view.addAction("Cascade")
            view.triggered[QAction].connect(self.view)

            self.windows = bar.addMenu("Window")
            self.windows.triggered[QAction].connect(self.window_activate)

            self.start_status_bar()

            self.mdi.tileSubWindows()
            self.show()

        except Exception as e:
            logging.error("App.__init__")
            logging.error(e)
            logging.exception("message")

    def start_status_bar(self):
        try:
            logging.info("App.start_status_bar")
            self.status_thread = QThread()
            self.status_worker = statusBar(self.statusBar())
            self.status_worker.moveToThread(self.status_thread)
            self.status_thread.started.connect(self.status_worker.update_status_bar)
            logging.info("bout to start status thread")
            self.status_thread.start()
        except Exception as e:
            logging.error("App.start_status_bar")
            logging.error(e)
            logging.exception("message")



    def view(self, action):
        if action.text() == "Tile":
            self.mdi.tileSubWindows()
        elif action.text() == "Cascade":
            self.mdi.cascadeSubWindows()

    def start(self, action):
        if action.text() == "Terminal":
            self.add_terminal()
        elif action.text() == "Web Browser":
            self.add_tabbed_browser()
        elif action.text() == "File Manager":
            self.add_file_manager()
        elif action.text() == "Media Player":
            self.add_media_player()
        elif action.text() == "Vnc Client":
            self.add_vnc()
        elif action.text() == "Calculator":
            self.add_calculator()
        elif action.text() == "Quit":
            QApplication.instance().quit()

    def window_activate(self, action):
        logging.info("App.window_activate")
        logging.info(action.text())
        action.data().setFocus()

    def update_window_list(self, active_window):
        logging.info("App.update_window_list")
        self.windows.clear()
        for window in self.mdi.subWindowList():
            logging.info("App.update_window_list: " + window.windowTitle())
            if window is active_window:
                logging.info("Active Window: " + window.windowTitle())
                activate_action = QAction("* " + window.windowTitle(),  self)
                #Hack because mdiSubWindow retains focus, prevents keystroke events from getting to VNC
                #Solution create new subwindow class and impliment keystroke event to emit to widget
                if window.windowTitle() == "VNC":
                    window.widget().setFocus()
            else:
                logging.info("InActive Window: " + window.windowTitle())
                activate_action = QAction(window.windowTitle(),  self)
            activate_action.setData(window)
            self.windows.addAction(activate_action)

    def add_sub_window(self, widget, title):
        try:
            sub = QMdiSubWindow()
            sub.setWindowIcon(QIcon('adrenaline.png'))
            sub.setWidget(widget)
            sub.setWindowTitle(title)
            sub.setAttribute(Qt.WA_DeleteOnClose)
            self.mdi.addSubWindow(sub)
            sub.show()
        except Exception as e:
            logging.error("App.add_sub_window")
            logging.error(e)
            logging.exception("message")

    def add_terminal(self):
        try:
            widget = Terminal()
            self.add_sub_window(widget, "Terminal")
        except Exception as e:
            logging.error("App.add_terminal")
            logging.error(e)
            logging.exception("message")

    def add_tabbed_browser(self):
        try:
            widget = Browser()
            self.add_sub_window(widget, "Web Browser")
        except Exception as e:
            logging.error("App.tabbed_browser")
            logging.error(e)
         
    def add_file_manager(self):
        try:
            widget = FileBrowser()
            self.add_sub_window(widget, "File Manager")
        except Exception as e:
            logging.error("App.add_file_manager")
            logging.error(e)
         
    def add_media_player(self):
        try:
            widget = VideoPlayer()
            self.add_sub_window(widget, "Video Player")
        except Exception as e:
            logging.error("App.add_media_player")
            logging.error(e)

    def add_vnc(self):
        try:
            widget = VncClient()
            self.add_sub_window(widget, "VNC")
            sub = QMdiSubWindow()
        except Exception as e:
            logging.error("App.add_vnc")
            logging.error(e)
            logging.exception("message")

    def add_calculator(self):
        try:   
            widget = Calculator()
            self.add_sub_window(widget, "Calculator")
            sub = QMdiSubWindow()
        except Exception as e:
            logging.error("App.add_calculator")
            logging.error(e)
            logging.exception("message")


class Terminal(QTermWidget):
    def __init__(self):
        try:
            super(QTermWidget, self).__init__()
            self.finished.connect(self.close)
            self.setTerminalBackgroundImage('adrenaline.jpg')
            self.setTerminalBackgroundMode(2)
            self.setColorScheme("Linux")
            termfont = QFont("Terminus", 6, QFont.Bold)
            self.setTerminalFont(termfont)
            self.copy = QShortcut(QKeySequence("Ctrl+Ins"),self)
            self.copy.activated.connect(self.copyClipboard)
            self.paste = QShortcut(QKeySequence("Shift+Ins"),self)
            self.paste.activated.connect(self.pasteClipboard)
        except Exception as e:
            logging.error("Terminal.__init__")
            logging.error(e)
            logging.exception("message")

    def run_program(self, program, args):
        try:     
            logging.info(program)
            self.sendText(program + " " + args[0] + "\n")
        except Exception as e:
            logging.error("Terminal.run_program")
            logging.error(e)
            logging.exception("message")


class WebEnginePage(QWebEnginePage):
    def certificateError(self, error):
        try:
            logging.info(error.url())
            ignore_certificate = QMessageBox()
            ignore_certificate.setText('Invalid Certificate')
            ignore_certificate.setInformativeText(error.url().toString() + 
                                                  " has presented an invalid certificate.  Continue to site anyway?")
            ignore_certificate.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            ignore_certificate.setDefaultButton(QMessageBox.No) 
            cont = ignore_certificate.exec()
            if cont == QMessageBox.Yes:
                logging.info("Attempting to ignore cerficate error.")
                error.ignoreCertificateError()
                return True
            return super().certificateError(error)
        except Exception as e:
            logging.error("WebEnginePage.certificateError")
            logging.error(e)
            logging.exception("message")
            return False

    def createWindow(self, create_type):
        try:
            logging.info(create_type)
            logging.info(self.parent)
            new_tab = self.parent().add_tab()
            return new_tab
        except Exception as e:
            logging.error("WebEnginePage.createWindow")
            logging.error(e)
            logging.exception("message")


class VncClient(QWidget):
    def __init__(self):
        try:
            super(QWidget, self).__init__()
            host, ok = QInputDialog().getText(self, "VNC Connect", "Host:")
            if not host and ok:
               return
            port, ok = QInputDialog().getText(self, "VNC Connect", "Port:")
            if not host and ok:
               return
            passwd, ok = QInputDialog().getText(self, "VNC Connect", "Password:", QLineEdit.Password)
            if not passwd and ok:
               return
            self.vnc = QVNCWidget(
                parent=self,
                host=host, port=int(port),
                password=passwd,
                mouseTracking=True
            )   
            self.vnc.onInitialResize.connect(self.resize)
            self.vnc.start()
        except Exception as e:
            logging.error("Vnc.__init__")
            logging.error(e)
            logging.exception("message")

    def keyPressEvent(self, ev: QKeyEvent):
        logging.info("VncClient.keyPressEvent")
        logging.info(ev)
        self.vnc.onKeyPress.emit(ev)

    def keyReleaseEvent(self, ev: QKeyEvent):
        logging.info("VncClient.keyReleaseEvent")
        logging.info(ev)
        self.vnc.onKeyRelease.emit(ev)


class DocumentBrowser(QWidget):
    def __init__(self, url):
        try:
            super(QWidget, self).__init__()
            self.browser = QWebEngineView()
            self.browser.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
            self.browser.settings().setAttribute(QWebEngineSettings.PdfViewerEnabled, True)
            self.browser.setUrl(QUrl(url))
            self.layout = QVBoxLayout(self) 
            self.layout.addWidget(self.browser)
            self.setLayout(self.layout)
        except Exception as e:
            logging.error("DocumentBrowser.__init__")
            logging.error(e)
            logging.exception("message")


class Browser(QWidget):
    def __init__(self):
        try:
            super(QWidget, self).__init__()
            self.tabs = QTabWidget()
            self.tabs.setDocumentMode(True)
            self.tabs.tabBarDoubleClicked.connect(lambda: self.add_tab())
            self.tabs.currentChanged.connect(self.update_url_bar)
            self.tabs.setTabsClosable(True)
            self.tabs.tabCloseRequested.connect(self.close_tab)
            self.layout = QVBoxLayout(self)
            self.navbar = QToolBar("Navigation")
            self.backbtn = QPushButton()
            self.backbtn.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_ArrowBack')))
            self.fwdbtn = QPushButton()
            self.fwdbtn.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_ArrowForward')))
            self.reloadbtn = QPushButton()
            self.reloadbtn.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_BrowserReload')))
            self.shortcut_reload = QShortcut(QKeySequence("F5"), self)
            self.shortcut_new_tab = QShortcut(QKeySequence("Ctrl+T"), self)
            self.shortcut_find_text = QShortcut(QKeySequence("Ctrl+F"), self)
            self.shortcut_find_text.activated.connect(self.find_text)
            self.homebtn = QPushButton()
            self.homebtn.setIcon(qta.icon("fa5s.home"))
            self.stopbtn = QPushButton()
            self.stopbtn.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_BrowserStop')))
            self.backbtn.clicked.connect(lambda: self.tabs.currentWidget().back())
            self.fwdbtn.clicked.connect(lambda: self.tabs.currentWidget().forward())
            self.reloadbtn.clicked.connect(lambda: self.tabs.currentWidget().reload())
            self.shortcut_reload.activated.connect(lambda: self.tabs.currentWidget().reload())
            self.shortcut_new_tab.activated.connect(lambda: self.add_tab())
            self.stopbtn.clicked.connect(lambda: self.tabs.currentWidget().stop())
            self.homebtn.clicked.connect(self.go_home)
            self.urlbar = QLineEdit()
            self.shortcut_url = QShortcut(QKeySequence("Ctrl+G"), self)
            self.shortcut_url.activated.connect(self.focus_urlbar)
            self.urlbar.returnPressed.connect(self.goto_url)
            self.shortcut_print_to_pdf = QShortcut(QKeySequence("Ctrl+P"), self)
            self.shortcut_print_to_pdf.activated.connect(self.printToPdf)
            self.navbar.addWidget(self.backbtn)
            self.navbar.addWidget(self.fwdbtn)
            self.navbar.addWidget(self.homebtn)
            self.navbar.addWidget(self.urlbar)
            self.navbar.addWidget(self.reloadbtn)
            self.navbar.addWidget(self.stopbtn)
            self.layout.addWidget(self.navbar)
            self.layout.addWidget(self.tabs)
            self.favbtn = QToolButton()
            self.favbtn.setIcon(qta.icon("fa.star"))
            self.favbtn.setPopupMode(QToolButton.InstantPopup)
            self.favmenu = QMenu()
            self.favmenu.triggered[QAction].connect(self.goto_favorite)
            self.favbtn.setMenu(self.favmenu)
            self.navbar.addWidget(self.favbtn)
            self.load_favorites()
            self.setLayout(self.layout)
            self.add_tab()
            self.search_text = ''
            self.shortcut_find_next = QShortcut(QKeySequence("N"), self)
            self.shortcut_find_prev = QShortcut(QKeySequence("P"), self)
            self.shortcut_find_exit = QShortcut(QKeySequence("ESC"), self)
            self.shortcut_find_next.activated.connect(self.find_next)
            self.shortcut_find_prev.activated.connect(self.find_prev)
            self.shortcut_find_exit.activated.connect(self.find_exit)
        except Exception as e:
            logging.error("Browser.__init__")
            logging.error(e)
            logging.exception("message")

    def add_favorite(self):
        try:
            tab_index = self.tabs.currentIndex()
            name = self.tabs.tabText(tab_index)
            url = self.tabs.currentWidget().url().toString()
            favorite = name+"="+url+"\n"
            fav_file = open(os.path.expanduser('~/.favorites'), 'a')
            fav_file.write(favorite)
            fav_file.close()
            self.load_favorites()
        except Exception as e:
            logging.error("Browser.add_favorite")
            logging.error(e)
            logging.exception("message") 

    def load_favorites(self):
        try:
            self.favmenu.clear()
            self.favmenu.addAction("Add Favorite")
            
            fav_file = open(os.path.expanduser('~/.favorites'), 'r')
            favs = fav_file.readlines()
            for fav in favs:
                if fav != "":
                    aryfav = fav.split('=')
                    fav_act = QAction(aryfav[0], self)
                    fav_act.setData(aryfav[1].strip())
                    self.favmenu.addAction(fav_act)
            fav_file.close()
        except Exception as e:
            logging.error("Browser.load_favorites")
            logging.error(e)
            logging.exception("message")

    def goto_favorite(self, favorite):
        logging.info("Browser.goto_favorite ")
        if favorite.text() == "Add Favorite":
            self.add_favorite()
        else:
            logging.info(favorite.data())
            self.tabs.currentWidget().setUrl(QUrl(favorite.data()))

    def handle_auth(self, url, auth):
        logging.info("Browser.handle_auth")
        logging.info(url)
        logging.info(auth)
        try:
            user, ok = QInputDialog().getText(self, url.toString() + " has requested authenticaiton", "User name:")
            if user and ok:
                auth.setUser(user)
                logging.info("Browser.handle_auth set user")
            passwd, ok = QInputDialog().getText(self, url.toString() + " has requested authenticaiton", "Password:", QLineEdit.Password)
            if passwd and ok:
                auth.setPassword(passwd)
                logging.info("Browser.handle_auth set password")
        except Exception as e:
            logging.error("Browser.handle_auth")
            logging.error(e)
            logging.exception("message")

    def find_text(self):
        try:
            text, ok = QInputDialog().getText(self,"Search", "Find Text:")
            if text and ok:
                logging.info("Browser.find_text")
                logging.info(text)
                self.search_text = text
                self.tabs.currentWidget().page().findText(self.search_text, QWebEnginePage.FindFlags(0), self.find_text_callback)
        except Exception as e:
            logging.error("Browser.find_text")
            logging.error(e)
            logging.exception("message")

    def find_text_callback(self, b_found):
        logging.info(b_found)
        if not b_found and self.search_text != None:
            self.find_text()
    
    def find_next(self):
        try:
            self.tabs.currentWidget().page().findText(self.search_text, QWebEnginePage.FindFlags(0), self.find_text_callback)
        except Exception as e:
            logging.error("Browser.find_next")
            logging.error(e)
            logging.exception("message")

    def find_prev(self):
        try:
            self.tabs.currentWidget().page().findText(self.search_text, QWebEnginePage.FindFlags(QWebEnginePage.FindBackward), self.find_text_callback)
        except Exception as e:
            logging.error("Browser.find_prev")
            logging.error(e)
            logging.exception("message")

    def find_exit(self):
        try:
            self.search_text = None
            self.tabs.currentWidget().page().findText(self.search_text, QWebEnginePage.FindFlags(0), self.find_text_callback)
        except Exception as e:
            logging.error("Browser.find_exit")
            logging.error(e)
            logging.exception("message")

    def close_tab(self, i):
        try:
            if self.tabs.count() > 1:
                self.tabs.removeTab(i)
        except Exception as e:
            logging.error("Browser..close_tab")
            logging.error(e)
            logging.exception("message")

    def add_tab(self, qurl=QUrl("https://google.com")):
        try:
            browser = QWebEngineView()
            page = WebEnginePage(parent=self)
            page.profile().downloadRequested.connect(self.save)
            page.authenticationRequired.connect(self.handle_auth)
            browser.setPage(page)
            browser.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
            browser.settings().setAttribute(QWebEngineSettings.PdfViewerEnabled, True)
            logging.info("Browser.add_tab: url: " + str(qurl))
            browser.setUrl(qurl)
            browser.urlChanged.connect(self.update_url)
            browser.titleChanged.connect(self.update_tab_label)
            i = self.tabs.addTab(browser, browser.title())
            self.tabs.setCurrentIndex(i)
            return page
        except Exception as e:
            logging.error("Browser.add_tab")
            logging.error(e)
            logging.exception("message")

    def printToPdf(self):
        try:
            tab_index = self.tabs.currentIndex()
            tab_text = self.tabs.tabText(tab_index)
            logging.info("Browser.printToPdf.tab_text: " + tab_text)
            page = self.tabs.currentWidget().page()
            path, _ = QFileDialog.getSaveFileName(self, "Print to PDF", "", "*.pdf")
            logging.info("Browser.printToPdf.path: " + path)
            page.printToPdf(path)
        except Exception as e:
            logging.error("Browser.printToPdf")
            logging.error(e)
            logging.exception("message")

    def save(self, request):
        try:
            logging.info("save requested:")
            logging.info(request.state())
            logging.info(request.path())
            if request.state() == 0:
                url = request.path()
                suffix = QFileInfo(url).suffix()
                path, _ = QFileDialog.getSaveFileName(self.tabs.currentWidget().page().view(), "Save File", url, "*."+suffix)
                if path:
                    request.setPath(path)
                    request.accept()
                else:
                    request.cancel()
        except Exception as e:
            logging.error("Browser.save")
            logging.error(e)
            logging.exception("message")
        
    def focus_urlbar(self):
        try:
            self.urlbar.setText('')
            self.urlbar.setCursorPosition(0)
            self.urlbar.setFocus()
        except Exception as e:
            logging.error("Browser.focus_urlbar")
            logging.error(e)
            logging.exception("message")

    def go_home(self):
        self.tabs.currentWidget().setUrl(QUrl("http://retro.adrenlinerush.net"))

    def goto_url(self):
        url = QUrl(self.urlbar.text())
        if " " in url.toString() or ("." not in url.toString() and url.scheme() == ""):
            url = QUrl("https://www.google.com/search?q=" + "+".join(url.toString().split(" ")))
            logging.info('Browser.goto_url search: ' + url.toString())
        elif url.scheme() == "":
            url.setScheme("http")
        self.tabs.currentWidget().setUrl(url)

    def update_url(self, url=None):
        logging.info("Browser.update_url: url: " + str(url))
        if isinstance(url, QUrl):
            url = url.toString()
        if isinstance(url, str) and (url != ""):
            logging.info("Browser.update_url: url: " + str(url))
            self.update_url_bar(url)

    def update_url_bar(self, url):
        if url:
            try:
                logging.info("Browser.update_url_bar: url: " + str(url))
                self.urlbar.setText(url)
                self.urlbar.setCursorPosition(0)
            except Exception as e:
                logging.error("Browser.update_url_bar")
                logging.error(e)
                logging.exception("message")

    def update_tab_label(self):
        try:
            logging.info("Browser.update_tab_label: title: " + self.tabs.currentWidget().page().title())
            i = self.tabs.currentIndex()
            title = self.tabs.currentWidget().page().title()
            if len(title) > 15:
                title = title[:15]
            self.tabs.setTabText(i, title)
        except Exception as e:
            logging.error("Browser.update_tab_label")
            logging.error(e)
            logging.exception("message")
        


class VideoPlayer(QWidget):
    def __init__(self, filename = None, can_open = True):
        try:
            super(QWidget, self).__init__()
            self.mediaPlayer = QMediaPlayer()
            self.videoWidget = QVideoWidget()
            self.mediaPlayer.setVideoOutput(self.videoWidget)       
            self.mediaPlayer.error.connect(self.handleError)
            self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
            self.mediaPlayer.positionChanged.connect(self.positionChanged)
            self.mediaPlayer.durationChanged.connect(self.durationChanged)
            
            self.playBtn = QPushButton()
            self.playBtn.setEnabled(False)
            self.playBtn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.playBtn.clicked.connect(self.play)
            
            self.positionSlider = QSlider(Qt.Horizontal)
            self.positionSlider.setRange(0, 0)
            self.positionSlider.sliderMoved.connect(self.setPosition)
            
            if can_open:
                self.shortcut_open = QShortcut(QKeySequence("Ctrl+O"), self)
                self.shortcut_open.activated.connect(self.openFile)

            if filename:
                self.openFile(filename)

            self.controlLayout = QHBoxLayout()
            self.controlLayout.setContentsMargins(0, 0, 0, 0)
            self.controlLayout.addWidget(self.playBtn)
            self.controlLayout.addWidget(self.positionSlider)

            self.layout = QVBoxLayout()
            self.layout.addWidget(self.videoWidget)
            self.layout.addLayout(self.controlLayout)

            self.setLayout(self.layout)
        except Exception as e:
            logging.error("VideoPlayer.__init__")
            logging.error(e)
            logging.exception("message")

    def openFile(self, fileName = None):
        if not fileName:
            fileName, _ = QFileDialog.getOpenFileName(self, "Open Movie",
                    QDir.homePath())

        if fileName != '':
            logging.debug(fileName)
            self.mediaPlayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playBtn.setEnabled(True)


    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            logging.debug("Attempting to play video.")
            self.mediaPlayer.play()

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playBtn.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playBtn.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playBtn.setEnabled(False)
        logging.error("VideoPlayer.handleError")
        logging.error(self.mediaPlayer.errorString())


class Calculator(QWidget):
    def __init__(self):
        try:
            super(QWidget, self).__init__()
            self.calc_layout = QGridLayout(self)
  
            self.label_in = QLabel(self)
            self.label_out = QLabel(self)
            self.label_in.setAlignment(Qt.AlignRight)
            self.label_out.setAlignment(Qt.AlignRight)
            self.calc_layout.addWidget(self.label_in, 0 , 0, 1, 4)
            self.calc_layout.addWidget(self.label_out, 1, 0, 1, 4) 

            buttons_ui: list = [
                ["(",  ")",  "DEL", "AC"],
                ["7",  "8",  "9",   "/" ], 
                ["4",  "5",  "6",   "*" ],
                ["1",  "2",  "3",   "-" ],
                [".",  "0",  "^" ,   "+"],
            ]

            self.buttons = {}

            for row, values in enumerate(buttons_ui):
                logging.info("row: " + str(row))
                for col, val in enumerate(values):
                    logging.info("col: " + str(col))
                    logging.info("val: " + str(val))

                    btn = QPushButton(val, self)
                    btn.clicked.connect(self.btn_clicked)
                    self.calc_layout.addWidget(btn, row+2, col, 1, 1)
                    if len(val) == 1:
                        btn.setShortcut(QKeySequence(val))
                    elif val == "DEL":
                        btn.setShortcut(QKeySequence('Del'))
                    elif val == "AC":
                        btn.setShortcut(QKeySequence('Backspace'))


        except Exception as e:
            logging.error("Calculator.__init__")
            logging.error(e)
            logging.exception("message")    

    def btn_clicked(self):
        try:
            btn = self.sender()
            if len(btn.text()) == 1:
                self.label_in.setText(self.label_in.text() + btn.text())
            elif btn.text() == 'DEL':
                self.label_in.setText(self.label_in.text()[:-1])
            elif btn.text() == 'AC':
                self.label_in.setText(None)
            try: output = str(eval(self.label_in.text()))[:20]
            except ZeroDivisionError: output = "inf"
            except SyntaxError: output = "nan"
            self.label_out.setText(output)
        except Exception as e:
            logging.error("Calculator.btn_clicked")
            logging.error(e)
            logging.exception("message")


class FileBrowser(QWidget):
    def __init__(self):
        try:
            super(QWidget, self).__init__()

            self.layout = QHBoxLayout(self)
            self.file_group = QGroupBox()
            self.file_group_layout = QVBoxLayout(self)
            self.file_group.setLayout(self.file_group_layout)

            self.files = QListWidget()
            self.files.itemActivated.connect(self.itemActivated)
            self.view = QTabWidget()
            self.view.setTabsClosable(True)
            self.view.tabCloseRequested.connect(self.closeTab)

            self.dir = os.path.expanduser('~')
            self.dir_display = QLineEdit()
            self.dir_display.setReadOnly(True)

            self.file_group_layout.addWidget(self.dir_display)
            self.file_group_layout.addWidget(self.files)
            self.layout.addWidget(self.file_group)
            self.layout.addWidget(self.view)

            logging.info(self.dir)
            self.updateDirListing()
            self.setLayout(self.layout)

        except Exception as e:
            logging.error("FileBrowser.__init__")
            logging.error(e)
            logging.exception("message")

    def closeTab(self, i):
        try:
            self.view.widget(i).close()
            self.view.removeTab(i)
        except Exception as e:
            logging.error("FileBrowser.closeTab")
            logging.error(e)
            logging.exception("message")

    def updateDirListing(self):
        try:
            self.files.clear()
            self.files.addItem("..")
            self.dir_display.setText(self.dir)

            for i in os.listdir(self.dir):
                logging.info(i)
                self.files.addItem(i)
        except Exception as e:
            logging.error("FileBrowser.updateDirListing")
            logging.error(e)
            logging.exception("message")
            
    def itemActivated(self):
        try:
            logging.info(self.dir)
            i = self.files.currentItem().text()
            logging.info(i)
            if i == "..":
                logging.info(self.dir.count('/'))
                if self.dir.count('/') == 1:
                    self.dir = '/'
                elif self.dir != "/":
                    self.dir = self.dir.rsplit('/',1)[0]
                self.updateDirListing()
            elif os.path.isdir(self.dir + "/" + i):
                self.dir = self.dir + "/" + i
                self.updateDirListing()
            else:
                if not is_binary_string(open(self.dir + "/" + i, 'rb').read(1024)):
                    logging.info('file is text')
                    self.openTextFile(self.dir + "/" + i)
                else:
                    logging.info('file is binary')
                    ext = i[i.rindex('.')+1:]
                    if ext in ['jpg','pdf','gif','png']:
                        self.openBrowser(self.dir + "/" + i)
                    if ext in ['avi', 'mpg', 'mp4', 'ogg', 'mp3']:
                        self.openMediaPlayer(self.dir + "/" + i)
                             
        except Exception as e:
            logging.error("FileBrowser.itemActivated")
            logging.error(e)
            logging.exception("message")

    def openMediaPlayer(self, filepath):
        try:
            mediaplayer = VideoPlayer(filepath, False)
            self.view.addTab(mediaplayer, filepath)
            self.view.setCurrentIndex(self.view.count()-1)
        except Exception as e:
            logging.error("FileBrowser.openMediaPlayer")
            logging.error(e)
            logging.exception("message")

    def openTextFile(self, filepath):
        try:
            vim = Terminal()
            self.view.addTab(vim, filepath)
            vim.run_program("vim", [filepath])
            self.view.setCurrentIndex(self.view.count()-1)
        except Exception as e:
            logging.error("FileBrowser.openTextFile")
            logging.error(e)
            logging.exception("message")

    def openBrowser(self, filepath):
        try:
            mediabrowser = DocumentBrowser("file://" + filepath)
            self.view.addTab(mediabrowser, filepath)
            self.view.setCurrentIndex(self.view.count()-1)
        except Exception as e:
            logging.error("FileBrowser.openBrowser")
            logging.error(e)
            logging.exception("message")
        

def start_ui():
    app = QApplication([])
    app.setFont(QFont("Terminus", 6, QFont.Bold))
    #app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    ex = App()
    sys.exit(app.exec())


if __name__ == "__main__":
    start_ui()
