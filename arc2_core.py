import logging
import numpy
import os
import shutil
import sys
import zipfile

from contextlib import closing
from datetime import datetime, timedelta
from urllib import request

from geotiff.geotiff import GeoTiff
from config import configure_logging

class Arc2Core(object):

    # no earlier arc2 data available
    # CACHE_MIN_DATE = '19830101'
    CACHE_MIN_DATE = '20210101'

    CACHE_START_DATE = CACHE_MIN_DATE
    CACHE_END_DATE = '20231231'
    DATE_FORMAT = '%Y%m%d'

    SIZE_LAT = 801
    SIZE_LONG = 751
    NO_DATA = 999.0

    FTP_SERVER = 'https://ftp.cpc.ncep.noaa.gov/fews/fewsdata/africa/arc2/geotiff'
    ZIP_FILE_TEMPLATE = 'africa_arc.{}.tif'
    ZIP_FILE_TEMPLATE_ZIP = 'africa_arc.{}.tif.zip'

    ZIP_FOLDER = './data'
    TMP_FOLDER = '{}/tmp'.format(ZIP_FOLDER)

    CACHE_INITIALIZED = 'initialized'
    CACHE_NO_FILE_ON_SERVER ='404 ftp response'

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
            dtype=numpy.half)
            # dtype=float)
        
        self.cache_content = days * [Arc2Core.CACHE_INITIALIZED]
        self.arc2sample = None

        logging.info("arc2 core initialized. cache dimension {}".format(self.cache.shape))


    def cache_status(self, start_date=None, days=None):
        if days < 1:
            return ''
        
        day_first = self.offset_start 
        day_last = self.offset_end

        if start_date:
            day_first = max(day_first, start_date.toordinal())

        if days:
            day_last = min(day_last + 1, day_first + days)

        idx_from = day_first - self.offset_start
        idx_to = day_last - self.offset_start

        return self._data_to_txt(day_first, days, self.cache_content[idx_from:idx_to])


    def rainfall(self, latitude, longitude, date, days):
        self._ensure_cached_data(date, days)

        day_first = datetime.strptime(date, '%Y%m%d').date().toordinal()
        (lat, lng) = self._lat_long_to_pixel(latitude, longitude)
        idx = day_first - self.offset_start

        return self._data_to_txt(day_first, days, self.cache[lat, lng, idx:idx + days])


    def _ensure_cached_data(self, date, days, force_reload=False):
        offset_date = datetime.strptime(date, Arc2Core.DATE_FORMAT).date().toordinal()
        offset_today = datetime.now().date().toordinal()
        offset_upper = min(offset_date + days, offset_today)

        for day in range(offset_date, offset_upper):
            date_string = datetime.strftime(datetime.fromordinal(day), Arc2Core.DATE_FORMAT)
            idx = day - self.offset_start

            if self.cache_content[idx] == Arc2Core.CACHE_INITIALIZED or force_reload: 
                logging.info("updating cache for '{}'".format(date_string))
                (status, message, data, tiff_file, zip_file) = self._get_rainfall_2d(date_string, force_reload)

                if data:
                    self.cache[:, :, idx] = data
                    self.cache_content[idx] = zip_file
                    os.remove(tiff_file)
                else:
                    self.cache_content[idx] = "{} {}".format(message, zip_file)


    def _lat_long_to_pixel(self, latitude, longitude):
        location = self.arc2sample._convert_from_wgs_84(self.arc2sample.crs_code, [latitude, longitude])
        pix_lat = self.arc2sample._get_y_int(location[0])
        pix_lng = self.arc2sample._get_x_int(location[1])

        return (pix_lat, pix_lng)


    def _get_rainfall_2d(self, date_string, force_reload=False):
        filename_zip = Arc2Core.ZIP_FILE_TEMPLATE_ZIP.format(date_string)
        filename = Arc2Core.ZIP_FILE_TEMPLATE.format(date_string)
        local_file_path_zip = os.path.join(self.download_folder, filename_zip)
        local_file_path = os.path.join(Arc2Core.TMP_FOLDER, filename)
        status = -1
        message = ''

        # force reload: removing local zipped geotiff if available to trigger an ftp download
        if force_reload and os.path.exists(local_file_path_zip):
            os.remove(local_file_path_zip)

        # ensure we have the zipped geotiff        
        if not os.path.exists(local_file_path_zip):
            (status, message, file_name) = self._ftp_download_geotiff(filename_zip, local_file_path_zip)

            # something wrong with ftp download
            if status != 200:
                return (status, message, None, None, filename_zip)

        # unzip and load geotiff
        with zipfile.ZipFile(local_file_path_zip, 'r') as f:
            f.extractall(Arc2Core.TMP_FOLDER)

        gt = GeoTiff(local_file_path, crs_code=4236)
        np2d = gt.read()

        # keep (arbitrary) geotiff to call methods later
        if not self.arc2sample:
            self.arc2sample = gt

        return (status, message, np2d, local_file_path, local_file_path_zip)


    def _ftp_download_geotiff(self, filename_zip, local_file_path_zip):
        ftp_file_path = '{}/{}'.format(Arc2Core.FTP_SERVER, filename_zip)

        logging.info("fetching {}, saving as {}".format(ftp_file_path, local_file_path_zip))

        try:
            with closing(request.urlopen(ftp_file_path)) as r:
                with open(local_file_path_zip, 'wb') as f:
                    shutil.copyfileobj(r, f)
            
            return (200, "OK", f)
        
        except Exception as e:
            logging.warning("download failed, check that file exists on ftp server. nested exception: {}".format(e))

            if str(e) == "HTTP Error 404: Not Found":
                return (404, str(e), filename_zip)
            
            return (400, str(e), filename_zip)


    def _data_to_txt(self, day_first, days, data):
        lines = []
        i = 0

        for day in range(day_first, day_first + days):
            date = datetime.fromordinal(day).strftime(Arc2Core.DATE_FORMAT)
            lines.append("{} {}".format(date, data[i]))
            i += 1

        return "{}\n".format('\n'.join(lines))


if __name__ == "__main__":
    c = Arc2Core()

    latitude = -0.9
    longitude = 37.7
    day = '20210612'
    days = 5

    # initialize arc2 sample
    c.rainfall(latitude, longitude, day, 1)

    if len(sys.argv) in [3,4]:
        latitude = float(sys.argv[1])
        longitude = float(sys.argv[2])
        pix_lat, pix_long = c._lat_long_to_pixel(latitude, longitude)

        print("lat/long: {}/{}".format(latitude, longitude))
        print("pixel x (long) {}".format(pix_long))
        print("pixel y (lat) {}".format(pix_lat))

        if len(sys.argv) > 3:
            day = sys.argv[3]

        print(c.rainfall(latitude, longitude, day, 1))

    else:
        print(c.rainfall(latitude, longitude, '20200201', 4))
        print(c.rainfall(latitude, longitude, '20200202', 5))
        print(c.rainfall(latitude, longitude, '20200201', 7))

        print(c.rainfall(latitude, longitude, day, days))
