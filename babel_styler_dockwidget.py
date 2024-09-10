# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BabelStylerDockWidget
                                 A QGIS plugin
 Translates QGIS styles to various formats
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-09-09
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Pietro Laba
        email                : pietrolabacm@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.utils import iface
from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QMessageBox

from .bridgestyle.bridgestyle.qgis.togeostyler import convert as qgisToGeostyler
from .bridgestyle.bridgestyle.sld.fromgeostyler import convert as geostylerToSld

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'styleviewerwidget.ui'))


class BabelStylerDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(BabelStylerDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        iface.currentLayerChanged.connect(self.onLayerChange)
        QgsProject.instance().layerWasAdded.connect(self.onLayerAdd)
        self.active_layer = None
        self.onLayerChange()

        self.saveButton.clicked.connect(self.saveCurrentType)


    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def setupLayerStyleConnection(self):
        print(QgsProject.instance().mapLayers().values())
        for layer in QgsProject.instance().mapLayers().values():
            layer.styleChanged.connect(self.onLayerChange)

    def onLayerAdd(self,layer):
        layer.styleChanged.connect(self.stylechangdebug)

    def stylechangdebug(self):
        self.onLayerChange()

    def onLayerChange(self):
        self.active_layer = iface.activeLayer()
        if self.active_layer:
            self.convertStyles()
        else:
            self.widgetSld.setPlainText('')
            self.widgetGeostyler.setPlainText('')

    def convertStyles(self):
        txtGeostyler, _,_,warn = qgisToGeostyler(self.active_layer)
        self.txtGeostyler = str(txtGeostyler)
        self.txtWarnings = '\n'.join(warn)
        self.widgetGeostyler.setPlainText(str(txtGeostyler))
        txtSld, warn, = geostylerToSld(txtGeostyler)
        self.txtSld = txtSld
        self.txtWarnings = '\n'.join(warn)
        self.widgetSld.setPlainText(txtSld)

        self.widgetWarnings.setPlainText(self.txtWarnings)

    def saveCurrentType(self):
        tabsDict = {0:self.txtSld,
                    1:self.txtGeostyler,
                    2:self.txtWarnings}
        
        fileText = tabsDict[self.tabWidget.currentIndex()]
        savePath = self.fileWidget.filePath()

        #Handling invalid path inputs
        if not savePath:
            self.qgisMessage("Please specify a path to save", QMessageBox.Warning)
            return False
        if not os.path.exists(os.path.dirname(savePath)):
            self.qgisMessage("Invalid path provided", QMessageBox.Warning)
            return False

        try:
            with open(savePath,'w') as file:
                file.write(fileText)
            self.qgisMessage("File Saved Successfully",QMessageBox.NoIcon)
            return True
        except Exception as e:
            print("Error while saving the file:\n%s" % e, QMessageBox.Critical)
            return False
    
    def qgisMessage(self,message:str,icon):
        qgisInfoMessage = QMessageBox()
        qgisInfoMessage.setText(message)
        qgisInfoMessage.setIcon(icon)
        qgisInfoMessage.exec_()
