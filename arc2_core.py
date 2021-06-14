import logging
import numpy
import os
import shutil
import zipfile

from contextlib import closing
from datetime import datetime, timedelta
from urllib import request

from geotiff.geotiff import GeoTiff
from config import configure_logging

class Arc2Core(object):

    CACHE_START_DATE = '20200101' 
    CACHE_END_DATE = '20251231'
    DATE_FORMAT = '%Y%m%d'

    SIZE_LAT = 801
    SIZE_LONG = 751
    NO_DATA = 999.0

    FTP_SERVER = 'https://ftp.cpc.ncep.noaa.gov/fews/fewsdata/africa/arc2/geotiff'
    ZIP_FILE_TEMPLATE = 'africa_arc.{}.tif'
    ZIP_FILE_TEMPLATE_ZIP = 'africa_arc.{}.tif.zip'

    ZIP_FOLDER = './data'
    TMP_FOLDER = '{}/tmp'.format(ZIP_FOLDER)

    logging.getLogger(__name__).addHandler(logging.NullHandler())
    configure_logging()

    def __init__(self, download_folder=ZIP_FOLDER):
        super().__init__()

        self.download_folder = download_folder

        self.offset_start = datetime.strptime(Arc2Core.CACHE_START_DATE, Arc2Core.DATE_FORMAT).date().toordinal()
        self.offset_end = datetime.strptime(Arc2Core.CACHE_END_DATE, Arc2Core.DATE_FORMAT).date().toordinal()

        # initialize numpy 3d cache
        days = self.offset_end - self.offset_start + 1
        self.cache = numpy.full(
            shape=(Arc2Core.SIZE_LAT, Arc2Core.SIZE_LONG, days), 
            fill_value=Arc2Core.NO_DATA, 
            dtype=float)
        
        self.cache_loaded = days * [False]
        self.arc2sample = None

        logging.info("arc2 core initialized. cache dimension {}".format(self.cache.shape))


    def rainfall(self, latitude, longitude, date, days):
        self._ensure_cached_data(date, days)

        day_first = datetime.strptime(date, '%Y%m%d').date().toordinal()
        (lat, lng) = self._lat_long_to_pixel(latitude, longitude)
        idx = day_first - self.offset_start

        response = self._rainfall_to_txt(day_first, days, self.cache[lat, lng, idx:idx + days])

        return response


    def _ensure_cached_data(self, date, days):
        offset_date = datetime.strptime(date, Arc2Core.DATE_FORMAT).date().toordinal()
        offset_today = datetime.now().date().toordinal()
        offset_upper = min(offset_date + days, offset_today)

        for day in range(offset_date, offset_upper):
            date_string = datetime.strftime(datetime.fromordinal(day), Arc2Core.DATE_FORMAT)
            idx = day - self.offset_start

            if not self.cache_loaded[idx]:
                logging.info("updating cache for '{}'".format(date_string))
                (data, tiff_file) = self._get_rainfall_2d(date_string)
                self.cache[:, :, idx] = data

                os.remove(tiff_file)

                # mark update of cache for this day
                self.cache_loaded[idx] = True


    def _lat_long_to_pixel(self, latitude, longitude):
        location = self.arc2sample._convert_from_wgs_84(self.arc2sample.crs_code, [latitude, longitude])
        pix_lat = self.arc2sample._get_y_int(location[0])
        pix_lng = self.arc2sample._get_x_int(location[1])

        return (pix_lat, pix_lng)


    def _get_rainfall_2d(self, date_string):
        filename_zip = Arc2Core.ZIP_FILE_TEMPLATE_ZIP.format(date_string)
        filename = Arc2Core.ZIP_FILE_TEMPLATE.format(date_string)
        local_file_path_zip = os.path.join(self.download_folder, filename_zip)
        local_file_path = os.path.join(Arc2Core.TMP_FOLDER, filename)

        # ensure we have the zipped geotiff
        if not os.path.exists(local_file_path_zip):
            self._ftp_download_geotiff(filename_zip, local_file_path_zip)
        
        # unzip and load geotiff
        with zipfile.ZipFile(local_file_path_zip, 'r') as f:
            f.extractall(Arc2Core.TMP_FOLDER)

        gt = GeoTiff(local_file_path, crs_code=4236)
        np2d = gt.read()

        # keep (arbitrary) geotiff to call methods later
        if not self.arc2sample:
            self.arc2sample = gt

        return (np2d, local_file_path)


    def _ftp_download_geotiff(self, filename_zip, local_file_path_zip):
        ftp_file_path = '{}/{}'.format(Arc2Core.FTP_SERVER, filename_zip)

        logging.info("fetching {}, saving as {}".format(ftp_file_path, local_file_path_zip))
        with closing(request.urlopen(ftp_file_path)) as r:
            with open(local_file_path_zip, 'wb') as f:
                shutil.copyfileobj(r, f)


    def _rainfall_to_txt(self, day_first, days, rainfall):
        lines = []
        i = 0

        for day in range(day_first, day_first + days):
            date = datetime.fromordinal(day).strftime(Arc2Core.DATE_FORMAT)
            lines.append("{} {}".format(date, rainfall[i]))
            i += 1

        return '\n'.join(lines)


if __name__ == "__main__":
    c = Arc2Core()

    latitude = -0.9
    longitude = 37.7
    day = '20210612'
    days = 5

    print(c.rainfall(latitude, longitude, '20200201', 4))
    print(c.rainfall(latitude, longitude, '20200202', 5))
    print(c.rainfall(latitude, longitude, '20200201', 7))

    print(c.rainfall(latitude, longitude, day, days))
