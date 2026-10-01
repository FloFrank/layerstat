# LayerStat

LayerStat is a QGIS plugin that lists the layers in the current project with
their source, geometry type, and feature count.

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