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
from .setUniqueField import setUniqueFieldPopup
class SelectionFilter:
    def __init__(self, iface):
        super().__init__()
        self.iface = iface

        self.create_filter_action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/sf_icon.svg")), QCoreApplication.translate("filterSelected", "&Show selected feature only"))
        self.create_clear_filter_action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/sf_clear_icon.svg")), QCoreApplication.translate("clearFilterSelected", "&Clear filter"))
        self.set_unique_field_action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/sf_icon.svg")), QCoreApplication.translate("showSetUniqueFieldPopup", "Set &unique field"))

    def initGui(self):    
        QgsProject.instance().layerWasAdded.connect(self.updateFilterActions)

        for layer in list(QgsProject.instance().mapLayers().values()):
            self.updateFilterActions(layer)
  
        self.create_filter_action.triggered.connect(self.filterSelected)
        self.create_clear_filter_action.triggered.connect(self.clearFilterSelected)
        self.set_unique_field_action.triggered.connect(self.showSetUniqueFieldPopup)

        
    def unload(self):

        self.iface.removeCustomActionForLayerType(self.create_filter_action)
        self.iface.removeCustomActionForLayerType(self.create_clear_filter_action)

      
    def filterSelected(self, layer:None):
        #if layer==None:
        #field = "VT_PCODE"
        layer = self.iface.activeLayer() 
        field = layer.customProperty("unique_field", "")
        if not field:
            #field = "FID"
            #layer.setCustomProperty("unique_field", field)
            iface.messageBar().pushMessage("You need to set unique value field first, type in console as follow.. \nlayer=iface.activeLayer() \nlayer.setCustomProperty(\"unique_field\", \"field\")\n\nwhere field is actual field name with unique values.",level=Qgis.Warning)
            return None
            
        selection = layer.selectedFeatures()
        if len(selection):
            fields = layer.fields()
            #fields = [f for f in fields]
            fields = [f.name() for f in fields]
            if field in fields:
                unique_values = [feature[field] for feature in selection ]
                if len(unique_values) > 1:
                    query_syntax = f"{field} IN {tuple(unique_values)}"
                else:
                    query_syntax = f"{field} IN ({unique_values[0]})"
                    
                layer.setSubsetString(query_syntax)
                
                iface.messageBar().pushMessage(f"{len(unique_values)} feature(s) filtered", level=Qgis.Info)
            else:               
                iface.messageBar().pushMessage(f"{field} field does not exists",level=Qgis.Warning)

        else:
            #print ("Nothing is selected")
            #QgsMessageLog.logMessage("Nothing is selected!","Messages",level=Qgis.Info)
            iface.messageBar().pushMessage("Nothing is selected!",level=Qgis.Warning)

            
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
        self.iface.removeCustomActionForLayerType(self.set_unique_field_action)
        self.iface.addCustomActionForLayerType(self.set_unique_field_action,
                                               None, QgsMapLayerType.VectorLayer, allLayers=False)
        for layer in QgsProject.instance().mapLayers().values():
            if layer and layer.type() == QgsMapLayerType.VectorLayer:
                self.iface.addCustomActionForLayer(self.create_filter_action, layer)
                self.iface.addCustomActionForLayer(self.create_clear_filter_action, layer)
                self.iface.addCustomActionForLayer(self.set_unique_field_action, layer)
                
    def showSetUniqueFieldPopup(self,layer:None):
        self.popup = setUniqueFieldPopup()
        layer = self.iface.activeLayer()
        fieldNames = [field.name() for field in layer.fields()]
        self.popup.comboBoxFields.addItems(fieldNames) 
        self.popup.show()
        
        ok = self.popup.exec_()
        if ok:
            field = self.popup.comboBoxFields.currentText()
            layer.setCustomProperty("unique_field", field)
