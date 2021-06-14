from datetime import datetime, timedelta
from arc2server import Arc2Cache
from flask import Flask, request

app = Flask(__name__)
cache = Arc2Cache()

@app.after_request
def treat_as_plain_text(response):
    response.headers["content-type"] = "text/plain"
    return response

@app.route("/arc2")
def arc2():
    # validate latitude from query param 'lat'
    try:
        if not 'lat' in request.args:
            raise Exception("query parameter 'lat' missing. mandatory query parameters: 'lat', 'long', 'date', 'days'")
        
        latitude = float(request.args.get('lat'))

        if not (latitude >= -40.0 and latitude <= 40.0):
            raise Exception("provided latitude {} not in range (-40.0 .. 40.0)".format(latitude))
    except Exception as e:
        return "latitude value exception: {}".format(e), 400

    # validate longitude from query param 'lng'
    try:
        longitude = float(request.args.get('long'))

        if not (longitude >= -20.0 and longitude <= 55.0):
            raise Exception("provided longitude {} not in range (-20.0 .. 55.0)".format(longitude))
    except Exception as e:
        return "longitude value exception: {}".format(e), 400
    

    begin = datetime.strptime(Arc2Cache.CACHE_START_DATE, Arc2Cache.DATE_FORMAT).date()
    end = datetime.strptime(Arc2Cache.CACHE_END_DATE, Arc2Cache.DATE_FORMAT).date()
 
    # validate start date from query param 'date'
    try:
        from_date = datetime.strptime(request.args.get('date'), Arc2Cache.DATE_FORMAT).date()

        if not (from_date >= begin and from_date <= end):
            raise Exception("provided date {} not in range ({} .. {})".format(from_date, Arc2Cache.CACHE_START_DATE, Arc2Cache.CACHE_END_DATE))
        
    except Exception as e:
        return "date value exception {}".format(e), 400

    # validate days from query param 'days'
    try:
        days = int(request.args.get('days'))

        if not (days >= 1 and days <= 365):
            raise Exception("provided days value {} not in range (1 .. 365)".format(days))
            
    except Exception as e:
        return "days value exception {}".format(e), 400
        
    try:
        return cache.rainfall(latitude, longitude, from_date.strftime(Arc2Cache.DATE_FORMAT), days), 200

    except Exception as e:
        return "rainfall cache exception {}".format(e), 400

if __name__ == '__main__':
    app.run()
