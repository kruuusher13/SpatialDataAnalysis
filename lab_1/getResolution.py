from math import sqrt
from qgis.core import QgsWkbTypes, QgsProject

def getsmallestlength(ring, smallestlength):
    lastpoint = None
    for point in ring:
        length = smallestlength
        if lastpoint is not None:
            length = sqrt(point.sqrDist(lastpoint))
        lastpoint = point
        if length < smallestlength:
            smallestlength = length
    return smallestlength

def getResolution(layer):
    features = layer.getFeatures()
    smallestLength= 1000
    nofeatures= 0
    geotype = ""
    for feature in features:
        geom = feature.geometry()
        nofeatures +=1
        if geom.wkbType() == QgsWkbTypes.MultiPolygon:
            geotype = "MultiPolygon"
            x = geom.asMultiPolygon()
            for polyg in x:
                for ring in polyg:
                    smallestLength = getsmallestlength(ring,smallestLength)
    print("smallest distinguishable length : " + str(smallestLength) + " in "+ str(nofeatures) +" " + geotype +" features")

layer_list = QgsProject.instance().mapLayersByName("OSM_poly")
if not layer_list:
    print("Layer named 'OSM_poly' not found.")
else:
    layer = layer_list[0]
    getResolution(layer)
