import math
import statistics

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)
from qgis.core import QgsApplication, QgsProject, QgsVectorLayer, QgsWkbTypes


class LayerStatPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None
        self.processing_provider = None

    def initGui(self):
        from .processing_provider import LayerStatProvider

        self.action = QAction("LayerStat", self.iface.mainWindow())
        icon_path = os.path.join(os.path.dirname(__file__), "icon_inspector.png")
        self.action.setIcon(QIcon(icon_path))
        self.action.setStatusTip("Layerstatistiken des aktuellen Projekts anzeigen")
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&LayerStat", self.action)
        self.iface.addToolBarIcon(self.action)

        self.processing_provider = LayerStatProvider()
        QgsApplication.processingRegistry().addProvider(self.processing_provider)

    def unload(self):
        if self.action is not None:
            self.iface.removePluginMenu("&LayerStat", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        if self.dialog is not None:
            self.dialog.close()
            self.dialog = None
        if self.processing_provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.processing_provider)
            self.processing_provider = None

    def run(self):
        if self.dialog is None:
            self.dialog = LayerStatDialog(self.iface.mainWindow())
        self.dialog.refresh()
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()


class LayerStatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Layer Statistics")
        self.resize(460, 480)
        self._statistics_running = False

        self.layer_combo = QComboBox(self)
        self.layer_combo.currentIndexChanged.connect(self.update_layer)
        self.attribute_combo = QComboBox(self)
        self.attribute_combo.currentIndexChanged.connect(self.update_statistics)

        self.geometry_value = QLabel("-")
        self.crs_value = QLabel("-")
        self.features_value = QLabel("-")
        self.bounds_value = QLabel("-")
        self.minimum_value = QLabel("-")
        self.maximum_value = QLabel("-")
        self.mean_value = QLabel("-")
        self.median_value = QLabel("-")
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.status_value = QLabel("Ready")

        form = QFormLayout()
        form.addRow("Layer:", self.layer_combo)
        form.addRow("Geometry:", self.geometry_value)
        form.addRow("CRS:", self.crs_value)
        form.addRow("Features:", self.features_value)
        form.addRow("Bounding Box:", self.bounds_value)
        form.addRow("Attribute:", self.attribute_combo)
        form.addRow("Min:", self.minimum_value)
        form.addRow("Max:", self.maximum_value)
        form.addRow("Mean:", self.mean_value)
        form.addRow("Median:", self.median_value)
        form.addRow("Progress:", self.progress_bar)
        form.addRow("Status:", self.status_value)

        layout = QVBoxLayout(self)
        layout.addLayout(form)

    def refresh(self):
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                self.layer_combo.addItem(layer.name(), layer.id())
        if self.layer_combo.count() == 0:
            self.layer_combo.addItem("No vector layers", None)
        self.layer_combo.setCurrentIndex(0)
        self.layer_combo.blockSignals(False)
        self.update_layer()

    def update_layer(self, *_args):
        layer_id = self.layer_combo.currentData()
        layer = QgsProject.instance().mapLayer(layer_id) if layer_id else None
        if not isinstance(layer, QgsVectorLayer):
            self.geometry_value.setText("-")
            self.crs_value.setText("-")
            self.features_value.setText("-")
            self.bounds_value.setText("-")
            self.attribute_combo.clear()
            self.attribute_combo.addItem("No numeric attributes", None)
            self.attribute_combo.setEnabled(False)
            self.status_value.setText("No vector layer selected")
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)
            self.update_statistics()
            return

        self.geometry_value.setText(QgsWkbTypes.displayString(layer.wkbType()))
        crs = layer.crs()
        self.crs_value.setText(crs.authid() or crs.description() or "Unknown")
        feature_count = layer.featureCount()
        self.features_value.setText(
            format(feature_count, ",") if feature_count >= 0 else "Unknown"
        )

        extent = layer.extent()
        if extent.isEmpty():
            self.bounds_value.setText("Empty")
        else:
            bounds = (extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum())
            self.bounds_value.setText(", ".join(self.format_number(value) for value in bounds))

        self.attribute_combo.blockSignals(True)
        self.attribute_combo.clear()
        for index, field in enumerate(layer.fields()):
            if field.isNumeric():
                self.attribute_combo.addItem(field.name(), index)
        if self.attribute_combo.count() == 0:
            self.attribute_combo.addItem("No numeric attributes", None)
            self.attribute_combo.setEnabled(False)
        else:
            self.attribute_combo.setEnabled(True)
        self.attribute_combo.setCurrentIndex(0)
        self.attribute_combo.blockSignals(False)
        self.update_statistics()

    def update_statistics(self, *_args):
        if self._statistics_running:
            return

        layer_id = self.layer_combo.currentData()
        layer = QgsProject.instance().mapLayer(layer_id) if layer_id else None
        field_index = self.attribute_combo.currentData()
        if not isinstance(layer, QgsVectorLayer) or field_index is None:
            values = ("-", "-", "-", "-")
            self.status_value.setText("No numeric attribute selected")
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)
        else:
            numeric_values = []
            feature_total = layer.featureCount()
            progress_maximum = max(1, feature_total)
            if feature_total >= 0:
                self.progress_bar.setRange(0, progress_maximum)
            else:
                self.progress_bar.setRange(0, 0)
            self.progress_bar.setValue(0)
            self.status_value.setText("Calculating statistics...")
            self._statistics_running = True
            self.layer_combo.setEnabled(False)
            self.attribute_combo.setEnabled(False)
            processed = 0
            QApplication.processEvents()
            try:
                for feature in layer.getFeatures():
                    processed += 1
                    value = feature.attribute(field_index)
                    if value is not None:
                        try:
                            number = float(value)
                        except (TypeError, ValueError):
                            number = None
                        if number is not None and math.isfinite(number):
                            numeric_values.append(number)

                    if processed % 256 == 0:
                        if feature_total >= 0:
                            self.progress_bar.setValue(min(processed, progress_maximum))
                        self.status_value.setText(
                            "Processed {:,} of {:,} features".format(
                                processed,
                                feature_total,
                            )
                            if feature_total >= 0
                            else "Processed {:,} features".format(processed)
                        )
                        QApplication.processEvents()
            except Exception as error:
                self.status_value.setText("Calculation failed: {}".format(error))
                return
            finally:
                self._statistics_running = False
                self.layer_combo.setEnabled(True)
                self.attribute_combo.setEnabled(self.attribute_combo.currentData() is not None)

            progress_maximum = max(1, feature_total if feature_total >= 0 else processed)
            self.progress_bar.setRange(0, progress_maximum)
            self.progress_bar.setValue(progress_maximum)
            self.status_value.setText(
                "Complete: {:,} features, {:,} numeric values".format(
                    processed,
                    len(numeric_values),
                )
            )

            if numeric_values:
                values = (
                    self.format_number(min(numeric_values)),
                    self.format_number(max(numeric_values)),
                    self.format_number(statistics.mean(numeric_values)),
                    self.format_number(statistics.median(numeric_values)),
                )
            else:
                values = ("No values", "No values", "No values", "No values")

        self.minimum_value.setText(values[0])
        self.maximum_value.setText(values[1])
        self.mean_value.setText(values[2])
        self.median_value.setText(values[3])

    @staticmethod
    def format_number(value):
        return format(value, ",.6g")