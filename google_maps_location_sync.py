# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Google Maps LocationSync
                                  A QGIS plugin
                              -------------------
        copyright            : Kohei Hara
 ***************************************************************************/
"""

from qgis.core import *
    
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, QSettings, QTranslator, qVersion, QCoreApplication, Qt, QUrl
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import QAction, QShortcut, QMessageBox, QWidget, QHBoxLayout, QVBoxLayout

from .resources import *
from PyQt5.QtNetwork import QNetworkProxyFactory

from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebView, QWebPage

import os.path

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'google_maps_location_sync_dockwidget_base.ui'))


class GoogleMapsLocationSyncDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()


    def __init__(self, parent=None):
        super(GoogleMapsLocationSyncDockWidget, self).__init__(parent)
        self.setupUi(self)


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()


class GoogleMapsLocationSync:


    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.plugin_dir = os.path.dirname(__file__)

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir,'i18n','Qweb_{}.qm'.format(locale))
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&Google Maps LocationSync')
        self.toolbar = self.iface.addToolBar(u'Google Maps LocationSync')
        self.toolbar.setObjectName(u'Google Maps LocationSync')

        self.pluginIsActive = False
        self.dockwidget = None


    def tr(self, message):
        return QCoreApplication.translate('Google Maps LocationSync', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToWebMenu(self.menu,action)

        self.actions.append(action)

        return action


    def initGui(self):
        icon_path = ':/plugins/GoogleMapsLocationSync/icon.png'
        self.add_action(icon_path,text=self.tr(u'Google Maps LocationSync'),callback=self.run,parent=self.iface.mainWindow())

        self.dockwidget = GoogleMapsLocationSyncDockWidget()

        self.dockwidget.webView.loadFinished.connect(self.on_load_finished)
        self.dockwidget.webView.urlChanged.connect(self.on_webview_urlChanged)
        self.dockwidget.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        
        self.dockwidget.syncCheckBox.stateChanged.connect(self.on_syncCheckBox_stateChanged)


    def on_load_finished(self):
        self.dockwidget.lineEdit.setText(self.dockwidget.webView.url().toString())


    def on_syncCheckBox_stateChanged(self):
        if self.dockwidget.syncCheckBox.isChecked():
            self.sync_location()


    def on_webview_urlChanged(self):
        url = self.dockwidget.webView.url().toString()
        self.dockwidget.lineEdit.setText(url)
        
        if self.dockwidget.syncCheckBox.isChecked():
            self.sync_location()


    def sync_location(self):
        url = self.dockwidget.webView.url().toString()
        
        if '@' in url:
            url_param = url[url.find('@') + 1:]
            url_param_split = url_param.split(',')
            point = (url_param_split[1]), str(url_param_split[0])
            self.locate(point)


    def locate(self, point):

        self.set_canvas_center_lon_lat(point[0], point[1])

        # if scale:
        #     self.canvas.zoomScale(scale)

        self.canvas.refresh()


    def set_canvas_center_lon_lat(self, lon, lat):

        point = QgsPoint(float(lon), float(lat))

        map_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        crs_wgs84 = QgsCoordinateReferenceSystem('EPSG:4326') # WGS 84 / UTM zone 33N
        transformer = QgsCoordinateTransform(crs_wgs84, map_crs, QgsProject.instance())

        point = transformer.transform(QgsPointXY(point)) 

        self.canvas.setCenter(point)


    def onClosePlugin(self):
        self.pluginIsActive = False


    def unload(self):
        for action in self.actions:
            self.iface.removePluginWebMenu(self.tr(u'&Google Maps LocationSync'),action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar


    def run(self):

        if not self.pluginIsActive:
            self.pluginIsActive = True
            if self.dockwidget == None:
                return

            QNetworkProxyFactory.setUseSystemConfiguration(True)
            QWebSettings.globalSettings().setAttribute(QWebSettings.PluginsEnabled, True)
            self.dockwidget.webView.settings().setAttribute(QWebSettings.PluginsEnabled, True)

            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            url = "https://www.google.com/maps"
            self.dockwidget.webView.load(QUrl(url))
