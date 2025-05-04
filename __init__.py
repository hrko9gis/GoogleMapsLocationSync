# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Google Maps LocationSync
                                  A QGIS plugin
                              -------------------
        copyright            : Kohei Hara
 ***************************************************************************/
"""

def classFactory(iface):
    from .google_maps_location_sync import GoogleMapsLocationSync
    return GoogleMapsLocationSync(iface)

