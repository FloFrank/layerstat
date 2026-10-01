import math
import os
import statistics

from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    QgsApplication,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingOutputNumber,
    QgsProcessingOutputString,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingProvider,
    QgsWkbTypes,
)


class LayerStatProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(LayerStatisticsAlgorithm())

    def id(self):
        return "layerstat"

    def name(self):
        return "LayerStat"

    def longName(self):
        return "LayerStat Statistics"

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), "icon_inspector.png")
        return QIcon(icon_path)


class LayerStatisticsAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    FIELD = "FIELD"
    FEATURE_COUNT = "FEATURE_COUNT"
    GEOMETRY = "GEOMETRY"
    CRS = "CRS"
    BOUNDING_BOX = "BOUNDING_BOX"
    MINIMUM = "MINIMUM"
    MAXIMUM = "MAXIMUM"
    MEAN = "MEAN"
    MEDIAN = "MEDIAN"

    def name(self):
        return "layer_statistics"

    def displayName(self):
        return "Layer Statistics"

    def group(self):
        return "Layer Statistics"

    def groupId(self):
        return "layer_statistics"

    def shortHelpString(self):
        return (
            "Counts features and reports geometry type, CRS, bounding box, "
            "and numeric attribute statistics."
        )

    def createInstance(self):
        return LayerStatisticsAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                "Input vector layer",
                [QgsProcessing.TypeVector],
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD,
                "Numeric attribute",
                None,
                self.INPUT,
                QgsProcessingParameterField.Numeric,
            )
        )

        self.addOutput(QgsProcessingOutputNumber(self.FEATURE_COUNT, "Feature count"))
        self.addOutput(QgsProcessingOutputString(self.GEOMETRY, "Geometry type"))
        self.addOutput(QgsProcessingOutputString(self.CRS, "CRS"))
        self.addOutput(QgsProcessingOutputString(self.BOUNDING_BOX, "Bounding box"))
        self.addOutput(QgsProcessingOutputNumber(self.MINIMUM, "Minimum"))
        self.addOutput(QgsProcessingOutputNumber(self.MAXIMUM, "Maximum"))
        self.addOutput(QgsProcessingOutputNumber(self.MEAN, "Mean"))
        self.addOutput(QgsProcessingOutputNumber(self.MEDIAN, "Median"))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException("Could not load the input vector layer.")
        feature_total = source.featureCount()

        field_name = self.parameterAsString(parameters, self.FIELD, context)
        if source.fields().indexFromName(field_name) < 0:
            raise QgsProcessingException("The selected numeric attribute was not found.")

        count = 0
        numeric_values = []
        for feature in source.getFeatures():
            if feedback.isCanceled():
                raise QgsProcessingException("Processing was canceled.")
            count += 1
            if count % 256 == 0 and feature_total > 0:
                feedback.setProgress(min(100.0, count * 100.0 / feature_total))
            value = feature.attribute(field_name)
            if value is None:
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(number):
                numeric_values.append(number)

            feedback.setProgress(100)

        extent = source.sourceExtent()
        bounding_box = "Empty" if extent.isEmpty() else ", ".join(
            self.format_number(value)
            for value in (
                extent.xMinimum(),
                extent.yMinimum(),
                extent.xMaximum(),
                extent.yMaximum(),
            )
        )
        crs = source.sourceCrs()

        if numeric_values:
            minimum = min(numeric_values)
            maximum = max(numeric_values)
            mean = statistics.mean(numeric_values)
            median = statistics.median(numeric_values)
        else:
            minimum = maximum = mean = median = None

        feedback.pushInfo("Geometry: " + QgsWkbTypes.displayString(source.wkbType()))
        feedback.pushInfo("CRS: " + (crs.authid() or crs.description() or "Unknown"))
        feedback.pushInfo("Feature count: " + str(count))
        feedback.pushInfo("Bounding box: " + bounding_box)
        if numeric_values:
            feedback.pushInfo(
                "Attribute statistics for {}: min={}, max={}, mean={}, median={}".format(
                    field_name,
                    self.format_number(minimum),
                    self.format_number(maximum),
                    self.format_number(mean),
                    self.format_number(median),
                )
            )
        else:
            feedback.pushInfo("The selected attribute contains no finite numeric values.")

        return {
            self.FEATURE_COUNT: count,
            self.GEOMETRY: QgsWkbTypes.displayString(source.wkbType()),
            self.CRS: crs.authid() or crs.description() or "Unknown",
            self.BOUNDING_BOX: bounding_box,
            self.MINIMUM: minimum,
            self.MAXIMUM: maximum,
            self.MEAN: mean,
            self.MEDIAN: median,
        }

    @staticmethod
    def format_number(value):
        return format(value, ",.6g")