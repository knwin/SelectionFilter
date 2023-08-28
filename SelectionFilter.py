"""
/***************************************************************************
 SelectionFilter
                                 A QGIS plugin
 This plugin show selected features only.

 Base was written manually
                              -------------------
        begin                : 2023-08-24
        copyright            : (C) 2023 Kyaw Naing Win
        email                : kyawnaingwinknw@gmail.com
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

from qgis.core import (QgsApplication, QgsMapLayerType, QgsProject, QgsMessageLog, Qgis)
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication
from qgis.utils import iface
import os

class SelectionFilter:
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.create_filter_action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/sf_icon.svg")), QCoreApplication.translate("filterSelected", "&Show selected feature only"))
        self.create_clear_filter_action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/sf_clear_icon.svg")), QCoreApplication.translate("clearFilterSelected", "&Clear filter"))
        '''self.create_filter_action = QAction(
            QgsApplication.getThemeIcon("/mActionAddTable.svg"), QCoreApplication.translate("filterSelected", "&Show selected feature only"))
        self.create_clear_filter_action = QAction(
            QgsApplication.getThemeIcon("/mActionAddTable.svg"), QCoreApplication.translate("clearFilterSelected", "&Clear filter"))'''


    def initGui(self):    
        QgsProject.instance().layerWasAdded.connect(self.updateFilterActions)

        for layer in list(QgsProject.instance().mapLayers().values()):
            self.updateFilterActions(layer)
            
        self.create_filter_action.triggered.connect(self.filterSelected)
        self.create_clear_filter_action.triggered.connect(self.clearFilterSelected)
    
    def unload(self):

        self.iface.removeCustomActionForLayerType(self.create_filter_action)
        self.iface.removeCustomActionForLayerType(self.create_clear_filter_action)

      
    def filterSelected(self, layer:None):
        #if layer==None:
        layer = self.iface.activeLayer()            
        selection = layer.selectedFeatures()
        if len(selection):
            ids = [feature['FID'] for feature in selection ]
            query_syntax = f"FID IN {tuple(ids)}"
            layer.setSubsetString(query_syntax)
        else:
            #print ("Nothing is selected")
            QgsMessageLog.logMessage("Nothing is selected!","SelectionFilter",level=Qgis.Info)

            
    def clearFilterSelected(self, layer:None):
        layer = self.iface.activeLayer()
        layer.setSubsetString('')
            
    def updateFilterActions(self, *args):
        self.iface.removeCustomActionForLayerType(self.create_filter_action)
        self.iface.addCustomActionForLayerType(self.create_filter_action,
                                               None, QgsMapLayerType.VectorLayer, allLayers=False)
        self.iface.removeCustomActionForLayerType(self.create_clear_filter_action)
        self.iface.addCustomActionForLayerType(self.create_clear_filter_action,
                                               None, QgsMapLayerType.VectorLayer, allLayers=False)
        for layer in QgsProject.instance().mapLayers().values():
            if layer and layer.type() == QgsMapLayerType.VectorLayer:
                self.iface.addCustomActionForLayer(self.create_filter_action, layer)
                self.iface.addCustomActionForLayer(self.create_clear_filter_action, layer)
