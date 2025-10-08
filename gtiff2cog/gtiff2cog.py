import os
import shutil

import gdal
import subprocess

src_gtiff_file = "/home/jtomicek/Documents/slim_cog/lc/gtiff/SLIM_LC_LandCover_2024_10m.tif"
dst_cog_dir = "/home/jtomicek/Documents/slim_cog/lc/cog/"

tmp_dir = os.path.join(dst_cog_dir, "tmp")
NoDataValue = 255
output_name_prefix = "SLIM_LC_LandCover_2024_10m.tif"

# create tmp dir if not exist
if not os.path.isdir(tmp_dir):
    os.makedirs(tmp_dir)
else:
    shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

# reproject to EPSG:3857
gtiff_reprojected = os.path.join(tmp_dir, output_name_prefix.replace(".tif", "_repr.tif"))
cmd_reprojecing = ["gdalwarp",
                   "-t_srs", "EPSG:3857",
                   "-srcnodata", str(NoDataValue),
                   "-dstnodata", str(NoDataValue),
                   "-ot", "Byte",
                   "-r", "near",
                   "-tr", "30", "30",
                   "-co", "COMPRESS=DEFLATE",
                   "-co", "TILED=YES",
                   "-co", "BIGTIFF=YES",
                   "-overwrite",
                   str(src_gtiff_file),
                   str(gtiff_reprojected)]
subprocess.check_output(cmd_reprojecing)

# clean potential existing overviews
gdaladdo_clean_cmd = ["gdaladdo",
                      "-clean",
                      gtiff_reprojected]
subprocess.check_output(gdaladdo_clean_cmd)

# generate external overviews
gdaladdo_cmd = ["gdaladdo", "-ro",
                "--config", "COMPRESS_OVERVIEW", "DEFLATE",
                "--config", "GDAL_CACHEMAX", "2048",
                gtiff_reprojected,
                ]
subprocess.check_output(gdaladdo_cmd)


# apply compression to final product
dst_cog_file = os.path.join(dst_cog_dir, output_name_prefix.replace(".tif", "_EPSG3857.tif"))
cmd_co = ["gdal_translate",
          gtiff_reprojected,
          dst_cog_file,
          "-co", "TILED=YES",
          "-co", "COMPRESS=DEFLATE",
          "-co", "COPY_SRC_OVERVIEWS=YES",
          "-co", "NUM_THREADS=ALL_CPUS",
          "-co", "BIGTIFF=YES",
          "--config", "GDAL_CACHEMAX", "2048"
          ]
subprocess.check_output(cmd_co)

# validate COG
cmd_validate_cog = ["python3", "./validate_cloud_optimized_geotiff.py", "--full-check=yes", dst_cog_file]
try:
    cog_validation_output = str(subprocess.check_output(cmd_validate_cog, stderr=subprocess.STDOUT))
except subprocess.CalledProcessError as e:
    cog_validation_output = str(e.output)
print(cog_validation_output)
# finally, delete tmp dir
if os.path.isdir(tmp_dir):
    shutil.rmtree(tmp_dir)