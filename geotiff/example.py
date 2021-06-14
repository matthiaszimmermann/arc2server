from typing import Dict, List, Tuple
import numpy as np # type: ignore
import os
# from geotiff import GeoTiff # type: ignore
#from geotiff import

import geotiff

#--
import pycountry

print("len(pycountry.countries) {}".format(len(pycountry.countries)))
print("list(pycountry.countries)[0] {}".format(list(pycountry.countries)[0]))
print("pycountry.countries.get(alpha_2='KE') {}".format(pycountry.countries.get(alpha_2='KE')))
#---

def read_location(geotiff: geotiff.GeoTiff, latitude: float, longitude: float):
    bb: List[Tuple[float, float]] = [(latitude-0.1, longitude+0.1), (latitude+0.1, longitude-0.1)]
    print("bb {}".format(bb))
    arr = geotiff.read_box(bb)
    return arr[0][0]
    
def lat_long_to_pixel(geotiff, latitude, longitude):
    pix_lat = gt._get_y_int(latitude)
    pix_lng = gt._get_x_int(longitude)

    return (pix_lat, pix_lng)

filename = "dem.tif"
filename = "africa_arc.20210527.tif"
dir = "../tests/inputs/"
tiff_file = os.path.join(dir, filename)
# tiff_file = "/home/kipling/Programs/pylandsat_sandbox/data/gamma/Radmap2019-grid-k_conc-Filtered-AWAGS_RAD_2019.tif"
# 138.632071411 -32.447310785 138.644218874 -32.456979174
bounding_box: List[Tuple[float, float]] = [(138.632071411, -32.447310785), (138.644218874, -32.456979174)]
bounding_box: List[Tuple[float, float]] = [(14.6, 3.3), (14.9, 3.0)]

# get value for single pixel 14.7, 3.1 (expected value: 10.5)
bounding_box: List[Tuple[float, float]] = [(14.6, 3.2), (14.8, 3.0)]

print(f"reading: {tiff_file}")
print(f"Using bBox: {bounding_box}")
gt: geotiff.GeoTiff = geotiff.GeoTiff(tiff_file, crs_code=4236)
print("geotiff.tifShape: {}".format(gt.tifShape))
print("tif bb: {}".format(gt.tif_bBox))
tiff_bb1, tiff_bb2 = gt.tif_bBox
tiff_bb = [tiff_bb1, tiff_bb2]
print("tiff_bb {}".format(tiff_bb))
print("tif crs code: {}".format(gt.crs_code))
array = gt.read_box(bounding_box)
print("array bBox:\n{}".format(array))
print("array type: {}".format(type(array)))
print("array.shape: {}".format(array.shape))
assert isinstance(array, np.ndarray)
print("geotiff.tif_bBox_wgs_84: {}".format(gt.tif_bBox_wgs_84))
print("read_location(geotiff, 14.7, 3.1): {}".format(read_location(gt, 14.7, 3.1)))

location = gt._convert_from_wgs_84(gt.crs_code, [14.7, 3.1])
print("location {}".format(location))

# latitude (N)
# longitude (E)
lat = 3.1
lng = 14.7
(pix_lat, pix_lng) = lat_long_to_pixel(gt, lat, lng)
print("geotiff.read()[{},{}]: {}".format(pix_lat, pix_lng, gt.read()[pix_lat, pix_lng]))

print("array bBox:\n{}".format(array))
