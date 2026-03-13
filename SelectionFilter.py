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

import os

from qgis.core import Qgis, QgsMapLayerType, QgsProject
from qgis.PyQt.QtCore import QCoreApplication

#from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QAction, QIcon
from qgis.utils import iface

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

      
    def _format_query(self, field, field_type, values, operator):
        if len(values) > 1:
            return f"{field} {operator} {tuple(values)}"
        if field_type == 10:
            return f"{field} {operator} ('{values[0]}')"
        return f"{field} {operator} ({values[0]})"

    def _shorter_query(self, field, field_type, in_values, not_in_values):
        """Return IN (in_values) or NOT IN (not_in_values), whichever list is shorter."""
        if not_in_values and len(not_in_values) < len(in_values):
            return self._format_query(field, field_type, not_in_values, "NOT IN")
        return self._format_query(field, field_type, in_values, "IN")

    def _build_query(self, layer, field, field_type, show_selected):
        selected_unique = list(set(f[field] for f in layer.selectedFeatures()))
        prior_subset = layer.subsetString()

        layer.invertSelection()
        inverted_unique = list(set(f[field] for f in layer.selectedFeatures()))
        layer.invertSelection()  # restore original selection

        if show_selected:
            # IN (selected) always replaces the prior filter cleanly — no AND needed.
            # NOT IN (inverted) is only safe when there is no prior subset, because
            # NOT IN on the full layer could expose features outside the prior view.
            if not prior_subset:
                return self._shorter_query(field, field_type, selected_unique, inverted_unique)
            return self._format_query(field, field_type, selected_unique, "IN")
        else:
            # For hide, NOT IN (selected) is short but must be scoped.
            # Compose with prior_subset via AND when NOT IN is chosen.
            query = self._shorter_query(field, field_type, inverted_unique, selected_unique)
            if "NOT IN" in query and prior_subset:
                return f"({prior_subset}) AND {query}"
            return query

    def _applySelectionFilter(self, show_selected):
        layer = self.iface.activeLayer()
        field = layer.customProperty("unique_field", "")
        if not field:
            self.showSetUniqueFieldPopup(layer)
            field = layer.customProperty("unique_field", "")

        original_count = layer.selectedFeatureCount()
        if not original_count:
            iface.messageBar().pushMessage("Nothing is selected!", level=Qgis.Warning)
            return

        fields = {f.name(): f.type() for f in layer.fields()}
        if field not in fields:
            iface.messageBar().pushMessage(f"{field} field does not exists", level=Qgis.Warning)
            return

        field_type = fields[field]
        query_syntax = self._build_query(layer, field, field_type, show_selected)
        layer.setSubsetString(query_syntax)

        if show_selected:
            feature_count = layer.featureCount()
            feature_plural_text = "feature" if feature_count == 1 else "features"
            iface.messageBar().pushMessage(f"{feature_count} {feature_plural_text} filtered", level=Qgis.Info)
        else:
            iface.messageBar().pushMessage(f"{original_count} feature(s) hidden", level=Qgis.Info)

    def filterSelected(self, layer:None):
        self._applySelectionFilter(show_selected=True)

    def hideSelected(self, layer:None):
        self._applySelectionFilter(show_selected=False)
            
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
        except Exception:
            pass
        
        ok = self.popup.exec()
        if ok:
            field = self.popup.comboBoxFields.currentText()
            layer.setCustomProperty("unique_field", field)
            iface.messageBar().pushMessage(f"{field} is set for {layer.name()} layer filtering", level=Qgis.Info)
            #return field