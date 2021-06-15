import logging

from datetime import datetime, timedelta
from flask import Flask, request

from arc2_core import Arc2Core
from config import configure_logging

logging.getLogger(__name__).addHandler(logging.NullHandler())
configure_logging()

ARC2_CACHE_DIR = '/data/arc2'

app = Flask(__name__)
cache = Arc2Core(ARC2_CACHE_DIR)

@app.after_request
def treat_as_plain_text(response):
    response.headers["content-type"] = "text/plain"
    return response

@app.route("/arc2")
def arc2():
    # ensure all parameters are provided
    try: 
        if not 'lat' in request.args:
            raise Exception("'lat' missing. mandatory query parameters: 'lat', 'long', 'date', 'days'")
        elif not 'long' in request.args:
            raise Exception("'long' missing. mandatory query parameters: 'lat', 'long', 'date', 'days'")
        elif not 'date' in request.args:
            raise Exception("'date' missing. mandatory query parameters: 'lat', 'long', 'date', 'days'")
        elif not 'days' in request.args:
            raise Exception("'days' missing. mandatory query parameters: 'lat', 'long', 'date', 'days'")
    except Exception as e:
        return http_400_response("required parameter {}".format(e))

    # validate latitude from query param 'lat'
    try:
        latitude = float(request.args.get('lat'))
        if not (latitude >= -40.0 and latitude <= 40.0):
            raise Exception("provided latitude {} not in range (-40.0 .. 40.0)".format(latitude))
    except Exception as e:
        return http_400_response("latitude value exception: {}".format(e))

    # validate longitude from query param 'lng'
    try:
        longitude = float(request.args.get('long'))
        if not (longitude >= -20.0 and longitude <= 55.0):
            raise Exception("provided longitude {} not in range (-20.0 .. 55.0)".format(longitude))
    except Exception as e:
        return http_400_response("longitude value exception: {}".format(e))
    
    begin = datetime.strptime(Arc2Core.CACHE_START_DATE, Arc2Core.DATE_FORMAT).date()
    end = datetime.strptime(Arc2Core.CACHE_END_DATE, Arc2Core.DATE_FORMAT).date()
 
    # validate start date from query param 'date'
    try:
        from_date = datetime.strptime(request.args.get('date'), Arc2Core.DATE_FORMAT).date()
        if not (from_date >= begin and from_date <= end):
            raise Exception("provided date {} not in range ({} .. {})".format(from_date.strftime(Arc2Core.DATE_FORMAT), Arc2Core.CACHE_START_DATE, Arc2Core.CACHE_END_DATE))
    except Exception as e:
        return http_400_response("date value exception {}".format(e))

    # validate days from query param 'days'
    try:
        days = int(request.args.get('days'))
        if not (days >= 1 and days <= 365):
            raise Exception("provided days value {} not in range (1 .. 365)".format(days))            
    except Exception as e:
        return http_400_response("days value exception {}".format(e))
        
    try:
        return cache.rainfall(latitude, longitude, from_date.strftime(Arc2Core.DATE_FORMAT), days), 200
    except Exception as e:
        return http_400_response("rainfall cache exception {}".format(e))

def http_400_response(message):
    logging.error(message)
    return message, 400

if __name__ == '__main__':
    app.run(port=5000)
