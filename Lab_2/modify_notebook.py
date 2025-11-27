import json

notebook_path = '/Users/hornet/Documents/coding/SpatialDataAnalysis/Lab_2/lab2_completed.ipynb'

with open(notebook_path, 'r') as f:
    nb = json.load(f)

# Helper to find cell by source content
def find_cell_index(nb, content_snippet):
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if content_snippet in source:
                return i
    return -1

# 1. Modify Buffer Dissolve
idx1 = find_cell_index(nb, 'intersection_gdf = gpd.overlay(districts, buffers_gdf, how="intersection")')
if idx1 != -1:
    nb['cells'][idx1]['source'] = [
        "# Dissolve overlapping buffers to avoid double counting\n",
        "buffers_gdf['const'] = 1\n",
        "buffers_dissolved = buffers_gdf.dissolve(by='const').reset_index(drop=True)\n",
        "\n",
        "# Calculate the spatial intersection of school buffers with districts\n",
        "intersection_gdf = gpd.overlay(districts, buffers_dissolved, how=\"intersection\")\n",
        "intersection_gdf.explore()"
    ]
    print(f"Modified cell {idx1} (Buffer Dissolve)")

# 2. Modify Areal Interpolation Function
idx2 = find_cell_index(nb, 'def area_weighted_sum(intersection: gpd.GeoDataFrame, attribute: str,')
if idx2 != -1:
    nb['cells'][idx2]['source'] = [
        "def areal_interpolation(source_gdf, target_gdf, target_area_id, attribute):\n",
        "    \"\"\"\n",
        "    Interpolate attribute values from source areas to target areas using areal interpolation.\n",
        "    \"\"\"\n",
        "    # Ensure source_gdf has an area column for the original areas\n",
        "    source_gdf = source_gdf.copy()\n",
        "    source_gdf['source_area'] = source_gdf.geometry.area\n",
        "    \n",
        "    # Step 1: Overlay\n",
        "    intersection = gpd.overlay(source_gdf, target_gdf, how=\"intersection\")\n",
        "    \n",
        "    # Step 2: Calculate area of intersection pieces\n",
        "    intersection[\"intersect_area\"] = intersection.geometry.area\n",
        "    \n",
        "    # Step 3: Calculate ratio\n",
        "    intersection['ratio'] = intersection['intersect_area'] / intersection['source_area']\n",
        "    \n",
        "    # Step 4: Calculate value\n",
        "    intersection[attribute + '_interp'] = intersection[attribute] * intersection['ratio']\n",
        "    \n",
        "    # Step 5: Aggregate\n",
        "    result = intersection.groupby(target_area_id)[attribute + '_interp'].sum().reset_index()\n",
        "    \n",
        "    # Rename column\n",
        "    result.rename(columns={attribute + '_interp': attribute}, inplace=True)\n",
        "    \n",
        "    return result"
    ]
    print(f"Modified cell {idx2} (Areal Interpolation Function)")

# 3. Modify Call to Areal Interpolation
idx3 = find_cell_index(nb, 'aggregated = area_weighted_sum(intersection, attribute, target_area_id)')
if idx3 != -1:
    nb['cells'][idx3]['source'] = [
        "# Step 3: Compute the area weighted sum of the target attribute\n",
        "# We use the new areal_interpolation function which handles overlay and interpolation\n",
        "aggregated = areal_interpolation(source_gdf, target_gdf, target_area_id, attribute)\n",
        "aggregated"
    ]
    print(f"Modified cell {idx3} (Call to Areal Interpolation)")

# 4. Modify Area Proportion Function
idx4 = find_cell_index(nb, 'def area_proportion(stats, size, targetattr="green_area", pixelcount="green_area_cells"):')
if idx4 != -1:
    nb['cells'][idx4]['source'] = [
        "def area_proportion(stats, size, targetattr=\"green_area\", pixelcount=\"green_area_cells\"):\n",
        "    # Calculate area in square meters\n",
        "    stats[targetattr] = stats[pixelcount] * size * size\n",
        "    \n",
        "    # Calculate proportion (green area / total polygon area)\n",
        "    stats[targetattr + \"_prop\"] = stats[targetattr] / stats.geometry.area\n",
        "    \n",
        "    return stats"
    ]
    print(f"Modified cell {idx4} (Area Proportion Function)")

with open(notebook_path, 'w') as f:
    json.dump(nb, f, indent=1)

print("Notebook modification complete.")
