from qgis.core import QgsProject, QgsSpatialIndex, QgsGeometry

# Parameters
layer_name_ref = "schools_geojson"     # Name of reference layer (Schoolwijzer OpenData)
layer_name_osm = "OSM_full"  # Name of OSM layer (schools)
max_distance = 80                   # Match threshold (meters)

# Load layers
ref_layer = QgsProject.instance().mapLayersByName(layer_name_ref)[0]
osm_layer = QgsProject.instance().mapLayersByName(layer_name_osm)[0]

# Build a spatial index for OSM schools
osm_index = QgsSpatialIndex()
osm_feat_dict = {}
for feat in osm_layer.getFeatures():
    geom = feat.geometry()
    osm_index.insertFeature(feat)
    osm_feat_dict[feat.id()] = geom

# Count matched Schoolwijzer features
total_ref = 0
matched_ref = 0

for ref_feat in ref_layer.getFeatures():
    ref_geom = ref_feat.geometry()
    total_ref += 1
    # Find nearest OSM features (returns a list of IDs)
    nearest_ids = osm_index.nearestNeighbor(ref_geom.asPoint(), 1)
    matched = False
    if nearest_ids:
        osm_geom = osm_feat_dict[nearest_ids[0]]
        dist = ref_geom.distance(osm_geom)
        if dist <= max_distance:
            matched = True
            matched_ref += 1

# Calculate completeness percentage
if total_ref > 0:
    completeness = (matched_ref / total_ref) * 100
    print(f"Completeness: {matched_ref} / {total_ref} ({completeness:.2f}%) schools matched within {max_distance}m.")
else:
    print("No records in Schoolwijzer layer.")

