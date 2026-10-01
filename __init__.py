def classFactory(iface):
    from .layerstat_plugin import LayerStatPlugin

    return LayerStatPlugin(iface)