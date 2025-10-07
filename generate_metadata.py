#!/usr/bin/env python3
import argparse
import os
import pandas as pd
import uuid
import rasterio
from datetime import datetime
from jinja2 import Template

def get_geographic_bbox(tif_path):
    """Extract geographic bounding box (west, east, south, north) from GeoTIFF."""
    with rasterio.open(tif_path) as src:
        bounds = src.bounds
        if src.crs and src.crs.to_epsg() != 4326:
            import pyproj
            transformer = pyproj.Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
            west, south = transformer.transform(bounds.left, bounds.bottom)
            east, north = transformer.transform(bounds.right, bounds.top)
        else:
            west, south, east, north = bounds.left, bounds.bottom, bounds.right, bounds.top
    return west, east, south, north

def get_spatial_resolution(tif_path):
    """Return spatial resolution as a string with units (meters)."""
    with rasterio.open(tif_path) as src:
        res_x, res_y = src.res
        # handle sign convention and format
        res_x, res_y = abs(res_x), abs(res_y)
        if abs(res_x - res_y) < 1e-6:
            return f"{res_x:g} m"   # e.g. "10 m"
        else:
            return f"{res_x:g} x {res_y:g} m"  # e.g. "10 x 20 m"

def get_coordinate_reference_system(tif_path):
    """Return CRS as EPSG code if available, otherwise WKT."""
    with rasterio.open(tif_path) as src:
        if src.crs:
            epsg = src.crs.to_epsg()
            if epsg:
                return f"EPSG:{epsg}"
            else:
                return src.crs.to_wkt()
        else:
            return "Unknown"

def generate_unique_id(file_identifier):
    """Generate unique resource identifier (UUID-based)."""
    return f"{file_identifier}-{uuid.uuid4()}"

def get_tif_dates(tif_path):
    """Extract file modification date for metadata fields (UTC)."""
    timestamp = os.path.getmtime(tif_path)
    dt = datetime.utcfromtimestamp(timestamp)
    iso_date = dt.strftime("%Y-%m-%d")
    return iso_date, iso_date  # (date_of_last_revision, metadata_date)

def main():
    parser = argparse.ArgumentParser(description="Generate XML metadata files from CSV and template.")
    parser.add_argument("directory", help="Directory containing .tif files")
    parser.add_argument("--csv", default="metadata_values.csv", help="Path to CSV with metadata values")
    parser.add_argument("--template", default="template_cog.xml", help="Path to XML Jinja2 template")
    args = parser.parse_args()

    # Load metadata CSV
    df = pd.read_csv(args.csv, dtype=str).fillna("")
    df_dict = {row["fileIdentifier"]: row.to_dict() for _, row in df.iterrows()}
    print(repr(df_dict))

    # Load XML Jinja2 template
    with open(args.template, encoding="utf-8") as f:
        template = Template(f.read())

    # Iterate over all .tif files
    for root, _, files in os.walk(args.directory):
        for fname in files:
            if fname.lower().endswith(".tif"):
                tif_path = os.path.join(root, fname)
                file_identifier = fname.split(".tif")[0]

                if file_identifier in df_dict:
                    data = df_dict[file_identifier]

                    # Geographic bounding box
                    west, east, south, north = get_geographic_bbox(tif_path)
                    data["west_bounding_longitude"] = west
                    data["east_bounding_longitude"] = east
                    data["south_bounding_latitude"] = south
                    data["north_bounding_latitude"] = north

                    # Unique resource identifier
                    data["unique_resource_identifier"] = generate_unique_id(file_identifier)

                    # Dates (creation/modification)
                    date_of_last_revision, metadata_date = get_tif_dates(tif_path)
                    data["date_of_last_revision"] = date_of_last_revision
                    data["metadata_date"] = metadata_date

                    # Spatial resolution
                    data["spatial_resolution"] = get_spatial_resolution(tif_path)

                    # Coordinate Reference System
                    data["coordinate_reference_system"] = get_coordinate_reference_system(tif_path)

                    # Render and write XML
                    xml_output = template.render(**data)
                    xml_path = os.path.join(root, f"{os.path.splitext(fname)[0]}.xml")

                    with open(xml_path, "w", encoding="utf-8") as out:
                        out.write(xml_output)

                    print(f"Generated: {xml_path}")
                else:
                    print(f"No CSV entry found for {file_identifier}, skipping.")

if __name__ == "__main__":
    main()
