

## Description
LayerStats is a QGIS plugin that displays statistics for a selected layer in QGIS.

![QGIS](https://img.shields.io/badge/QGIS-3.x-589632?logo=qgis&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![Plugin](https://img.shields.io/badge/Type-QGIS%20Plugin-93b023)


## LayerStat

<p align="center">
	<img src="icon_inspector.png" alt="LayerStat icon" width="128">
</p>

LayerStats displays the following information for the selected layer: geometry type, projection, feature count, and bounding box. Additionally, the minimum, maximum, arithmetic mean, and median can be displayed for all numerical values of the layer.

## Install

This folder is already in the QGIS profile plugin directory. In QGIS, open
**Plugins > Manage and Install Plugins**, then enable **LayerStat** under
**Installed**. Restart QGIS if the plugin does not appear immediately.

The plugin can also be installed by copying this `layerstat` folder into the
QGIS profile's `python/plugins` directory. The folder must contain
`metadata.txt` and `__init__.py`.

## Use

Choose **Plugins > LayerStat > LayerStat** or click its toolbar button to open
the statistics window. Select a layer and a numeric attribute to view its
statistics.

The **Layer Statistics** algorithm is available in the **Processing Toolbox**
under **LayerStat > Layer Statistics**. Select a vector layer and numeric
attribute; the algorithm reports the feature count, geometry, CRS, bounding
box, minimum, maximum, mean, and median.