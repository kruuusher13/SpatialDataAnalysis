import geopandas as gpd
import pandas as pd
import rasterstats as rs
from rasterio import features
from rasterio.transform import from_origin
import numpy as np
import os
import folium

# Set working directory
os.chdir('/Users/hornet/Documents/coding/SpatialDataAnalysis/Lab_2')

print("Starting Assignment 2.1: Buffer Analysis")
# Load data
schools = gpd.read_file("data/schools.gpkg", layer="locations")
districts = gpd.read_file("data/Amsterdam_BAG.gpkg", layer="Wijken")

# Project to RD New (EPSG:28992) for calculation
schools = schools.to_crs(28992)
districts = districts.to_crs(28992)

# Create buffers
schools_buffers = schools.copy()
schools_buffers['geometry'] = schools.geometry.buffer(300)

# Dissolve buffers
schools_buffers['const'] = 1
buffers_dissolved = schools_buffers.dissolve(by='const').reset_index(drop=True)

# Intersect with districts
intersection = gpd.overlay(districts, buffers_dissolved, how="intersection")

# Calculate area
intersection['covered_area'] = intersection.geometry.area
districts['total_area'] = districts.geometry.area

# Aggregate covered area by district
# Use 'Buurtcombinatie' as the district name/identifier
district_col = 'Buurtcombinatie'
covered_by_district = intersection.groupby(district_col)['covered_area'].sum().reset_index()

# Merge back to districts
districts = districts.merge(covered_by_district, on=district_col, how='left')
districts['covered_area'] = districts['covered_area'].fillna(0)

# Calculate proportion NOT covered
districts['prop_covered'] = districts['covered_area'] / districts['total_area']
districts['prop_not_covered'] = 1 - districts['prop_covered']

print("Numerical Results (Top 5 Districts with highest uncovered proportion):")
print(districts[[district_col, 'prop_not_covered']].sort_values(by='prop_not_covered', ascending=False).head())

# Save map
# Folium needs WGS84 (EPSG:4326)
districts_wgs84 = districts.to_crs(4326)
m = districts_wgs84.explore(column='prop_not_covered', cmap='OrRd', legend=True, tooltip=[district_col, 'prop_not_covered'])
m.save("assignment_2_1_map.html")
print("Assignment 2.1 Map saved to assignment_2_1_map.html")


print("\nStarting Assignment 2.2: Areal Interpolation")
# Load data
cbs_districts = gpd.read_file("data/CBS_Buurt_2014_AP_RDNew.shp")
PC4_districts = gpd.read_file("data/PC4.shp")

# Ensure CRS match
if cbs_districts.crs != PC4_districts.crs:
    cbs_districts = cbs_districts.to_crs(PC4_districts.crs)

def areal_interpolation(source_gdf, target_gdf, target_area_id, attribute):
    """
    Interpolate attribute values from source areas to target areas using areal interpolation.
    """
    source_gdf = source_gdf.copy()
    source_gdf['source_area'] = source_gdf.geometry.area
    
    intersection = gpd.overlay(source_gdf, target_gdf, how="intersection")
    intersection["intersect_area"] = intersection.geometry.area
    intersection['ratio'] = intersection['intersect_area'] / intersection['source_area']
    intersection[attribute + '_interp'] = intersection[attribute] * intersection['ratio']
    
    result = intersection.groupby(target_area_id)[attribute + '_interp'].sum().reset_index()
    result.rename(columns={attribute + '_interp': attribute}, inplace=True)
    
    return result

# Interpolate P_65_EO_JR
attribute = "P_65_EO_JR"
target_area_id = "Postcode4"

interpolated = areal_interpolation(cbs_districts, PC4_districts, target_area_id, attribute)

# Merge back to PC4
PC4_districts = PC4_districts.merge(interpolated, on=target_area_id, how='left')

print("Numerical Results (Top 5 PC4 with highest population 65+):")
print(PC4_districts[[target_area_id, attribute]].sort_values(by=attribute, ascending=False).head())

# Save map
PC4_districts_wgs84 = PC4_districts.to_crs(4326)
m = PC4_districts_wgs84.explore(column=attribute, cmap='viridis', legend=True, tooltip=[target_area_id, attribute])
m.save("assignment_2_2_map.html")
print("Assignment 2.2 Map saved to assignment_2_2_map.html")


print("\nStarting Assignment 2.3: Zonal Map Algebra")
# Load data
landuse_data = gpd.read_file("data/GRONDGEBRUIK_2017_RDNew.shp")
# PC4_districts is already loaded

def area_proportion(stats, size, targetattr="green_area", pixelcount="green_area_cells"):
    stats[targetattr] = stats[pixelcount] * size * size
    stats[targetattr + "_prop"] = stats[targetattr] / stats.geometry.area
    return stats

def rasterize_and_analyze_landuse(landuse, sum_areas, attribute, pixel_size, green_area_id):
    xmin, ymin, xmax, ymax = landuse.total_bounds
    width = int((xmax - xmin) / pixel_size)
    height = int((ymax - ymin) / pixel_size)
    transform = from_origin(xmin, ymax, pixel_size, pixel_size)
    out_shape = (height, width)
    
    landuse_shapes = ((geom, value) for geom, value in zip(landuse.geometry, landuse[attribute]))
    burned = features.rasterize(landuse_shapes, out_shape=out_shape, transform=transform, fill=0, dtype=np.uint8)
    
    green_areas_raster = np.where(burned == green_area_id, 1, 0)
    
    zs = rs.zonal_stats(sum_areas, green_areas_raster, affine=transform, stats="sum", nodata=0, geojson_out=True)
    
    zonal_stats = gpd.GeoDataFrame.from_features(zs)
    zonal_stats.rename(columns={"sum": "green_area_cells"}, inplace=True)
    zonal_stats.crs = sum_areas.crs # Ensure CRS is preserved
    
    zonal_stats = area_proportion(zonal_stats, pixel_size, targetattr="green_area", pixelcount="green_area_cells")
    
    return zonal_stats

# Analyze Park en plantsoen (id 40)
id_green = 40
pixel_s = 50
type_column = 'CBScode2' 

if 'CBScode2' not in landuse_data.columns:
    print("Warning: CBScode2 not found in landuse_data. Columns:", landuse_data.columns)

pc4_parks = rasterize_and_analyze_landuse(landuse_data, PC4_districts, type_column, pixel_s, id_green)

print("Numerical Results (Top 5 PC4 with highest park proportion):")
print(pc4_parks[[target_area_id, 'green_area_prop']].sort_values(by='green_area_prop', ascending=False).head())

# Save map
pc4_parks_wgs84 = pc4_parks.to_crs(4326)
m = pc4_parks_wgs84.explore(column="green_area_prop", cmap='Greens', legend=True, tooltip=[target_area_id, 'green_area_prop'])
m.save("assignment_2_3_map.html")
print("Assignment 2.3 Map saved to assignment_2_3_map.html")

print("\nAll assignments completed successfully.")
