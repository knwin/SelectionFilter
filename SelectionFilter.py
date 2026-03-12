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
#from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon, QAction
from qgis.PyQt.QtCore import QCoreApplication
from qgis.utils import iface
import os
from .setUniqueField import setUniqueFieldPopup
class SelectionFilter:
    def __init__(self, iface):
        super().__init__()
        self.iface = iface

        self.create_filter_action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/sf_icon.svg")), QCoreApplication.translate("filterSelected", "&Show selected feature(s) only"))
        self.create_hide_filter_action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/sf_hide_icon.svg")), QCoreApplication.translate("hideSelected", "&Hide selected feature(s)"))
        self.create_clear_filter_action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/sf_clear_icon.svg")), QCoreApplication.translate("clearFilterSelected", "&Clear filter"))
        self.set_unique_field_action = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "icons/sf_field_icon.svg")), QCoreApplication.translate("showSetUniqueFieldPopup", "Se&t field"))

    def initGui(self):    
        QgsProject.instance().layerWasAdded.connect(self.updateFilterActions)

        for layer in list(QgsProject.instance().mapLayers().values()):
            self.updateFilterActions(layer)
  
        self.create_filter_action.triggered.connect(self.filterSelected)
        self.create_hide_filter_action.triggered.connect(self.hideSelected)
        self.create_clear_filter_action.triggered.connect(self.clearFilterSelected)
        self.set_unique_field_action.triggered.connect(self.showSetUniqueFieldPopup)

        
    def unload(self):
        # 1) Disconnect project-level signals that reference our methods
        try:
            QgsProject.instance().layerWasAdded.disconnect(self.updateFilterActions)
        except Exception:
            pass

        self.iface.removeCustomActionForLayerType(self.create_filter_action)
        self.iface.removeCustomActionForLayerType(self.create_hide_filter_action)
        self.iface.removeCustomActionForLayerType(self.create_clear_filter_action)

        # 2) Disconnect QAction signals so slots won't be called after plugin unload
        try:
            self.create_filter_action.triggered.disconnect(self.filterSelected)
        except Exception:
            pass
        try:
            self.create_hide_filter_action.triggered.disconnect(self.hideSelected)
        except Exception:
            pass
        try:
            self.create_clear_filter_action.triggered.disconnect(self.clearFilterSelected)
        except Exception:
            pass
        try:
            self.set_unique_field_action.triggered.disconnect(self.showSetUniqueFieldPopup)
        except Exception:
            pass

        # 3) Remove per-layer custom actions that were added for each layer
        for layer in QgsProject.instance().mapLayers().values():
            try:
                self.iface.removeCustomActionForLayer(self.create_filter_action, layer)
            except Exception:
                pass
            try:
                self.iface.removeCustomActionForLayer(self.create_hide_filter_action, layer)
            except Exception:
                pass
            try:
                self.iface.removeCustomActionForLayer(self.create_clear_filter_action, layer)
            except Exception:
                pass
            try:
                self.iface.removeCustomActionForLayer(self.set_unique_field_action, layer)
            except Exception:
                pass

        # 4) Remove the actions registered for layer types (global registration)
        try:
            self.iface.removeCustomActionForLayerType(self.create_filter_action)
        except Exception:
            pass
        try:
            self.iface.removeCustomActionForLayerType(self.create_hide_filter_action)
        except Exception:
            pass
        try:
            self.iface.removeCustomActionForLayerType(self.create_clear_filter_action)
        except Exception:
            pass
        try:
            self.iface.removeCustomActionForLayerType(self.set_unique_field_action)
        except Exception:
            pass

        # 5) Close / delete any plugin dialogs still open to avoid dangling widgets
        try:
            if hasattr(self, 'popup') and self.popup:
                # close and schedule for deletion
                self.popup.reject()
                self.popup.deleteLater()
        except Exception:
            pass

      
    def filterSelected(self, layer:None):

        layer = self.iface.activeLayer() 
        field = layer.customProperty("unique_field", "") #stored unique field for this layer        
        if not field:
            self.showSetUniqueFieldPopup(layer)
            field = layer.customProperty("unique_field", "")
            
        selection = layer.selectedFeatures()
        
        if len(selection):
            fields = {f.name():f.type() for f in layer.fields()}
            if field in fields:
                values = [feature[field] for feature in selection ]
                unique_values = list(set(values))

                if len(unique_values) > 1:
                    query_syntax = f"{field} IN {tuple(unique_values)}"
                else:
                    query_syntax = f"{field} IN ({unique_values[0]})"
                    # make sure string value is written as string
                    if fields.get(field) == 10:
                        query_syntax = f"{field} IN (\'{unique_values[0]}\')"
                    
                    
                layer.setSubsetString(query_syntax)
                
                feature_count = layer.featureCount()
                feature_plural_text = "feature" if feature_count == 1 else "features"
                value_plural_text = "value" if len(unique_values) == 1 else "values"
                iface.messageBar().pushMessage(f"{len(unique_values)} unique {value_plural_text} and {feature_count} {feature_plural_text} filtered", level=Qgis.Info)
            else:               
                iface.messageBar().pushMessage(f"{field} field does not exists",level=Qgis.Warning)

        else:
            iface.messageBar().pushMessage("Nothing is selected!",level=Qgis.Warning)

    def hideSelected(self, layer:None):
        layer = self.iface.activeLayer() 
        field = layer.customProperty("unique_field", "")
        if not field:
            self.showSetUniqueFieldPopup(layer)
            field = layer.customProperty("unique_field", "")
        layer.invertSelection()    
        selection = layer.selectedFeatures()
        
        if len(selection):
            fields = {f.name():f.type() for f in layer.fields()}            
            if field in fields:
                unique_values = [feature[field] for feature in selection ]
                unique_values = list(set(unique_values))
                if len(unique_values) > 1:
                    query_syntax = f"{field} IN {tuple(unique_values)}"
                else:
                    query_syntax = f"{field} IN ({unique_values[0]})"
                    # make sure string value is written as string
                    if fields.get(field) == 10:
                        query_syntax = f"{field} IN (\'{unique_values[0]}\')"
                                    
                layer.setSubsetString(query_syntax)
                
                iface.messageBar().pushMessage(f"{len(unique_values)} feature(s) filtered", level=Qgis.Info)
            else:               
                iface.messageBar().pushMessage(f"{field} field does not exists",level=Qgis.Warning)

        else:
            iface.messageBar().pushMessage("Nothing is selected!",level=Qgis.Warning)
            
    def clearFilterSelected(self, layer:None):
        layer = self.iface.activeLayer()
        layer.setSubsetString('')
            
    def updateFilterActions(self, *args):
        self.iface.removeCustomActionForLayerType(self.create_filter_action)
        self.iface.addCustomActionForLayerType(self.create_filter_action,
                                               None, QgsMapLayerType.VectorLayer, allLayers=False)
        self.iface.removeCustomActionForLayerType(self.create_hide_filter_action)
        self.iface.addCustomActionForLayerType(self.create_hide_filter_action,
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
                self.iface.addCustomActionForLayer(self.create_hide_filter_action, layer)
                self.iface.addCustomActionForLayer(self.create_clear_filter_action, layer)
                self.iface.addCustomActionForLayer(self.set_unique_field_action, layer)
                
    def showSetUniqueFieldPopup(self,layer:None):
        self.popup = setUniqueFieldPopup()
        layer = self.iface.activeLayer()
        fieldNames = [field.name() for field in layer.fields()]
        self.popup.comboBoxFields.addItems(fieldNames)
        
        field = layer.customProperty("unique_field", "") #stored unique field for this layer        
        if field:
            #field = self.showSetUniqueFieldPopup(layer)
            self.popup.comboBoxFields.setCurrentText(field) 
        try:
            self.popup.show()
        except:
            pass
        
        ok = self.popup.exec()
        if ok:
            field = self.popup.comboBoxFields.currentText()
            layer.setCustomProperty("unique_field", field)
            iface.messageBar().pushMessage(f"{field} is set for {layer.name()} layer filtering", level=Qgis.Info)
            #return field