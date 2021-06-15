# arc2server
rest server for arc2 rainfall data

## run the server

the server may be run using the command line or docker

### command line

run server on command line

``` bash
python3 server.py
```

### docker

build the docker image

``` bash
docker build -t arc2_server .
```

NOTE regarding docker base image. numpy and other things such as pyproj come with non-trivial dependencies.
alpine as a lightweight base image did not work well. the larger ubuntu base image did work.

run server using docker

``` bash
docker run -v <your-local-cache-dir>:/data/arc2 -d -p 5000:5000 arc2_server
```

## test the server

``` bash
curl -X GET "http://localhost:5000/arc2?lat=-0.9&long=37.7&date=20200201&days=7"
```

this should produce the following output

```
20200201 19.597993850708008
20200202 0.0
20200203 1.1990208625793457
20200204 0.31660813093185425
20200205 0.40143030881881714
20200206 1.095880150794983
20200207 0.0
```
## geotiff

geotiff code is by KipCrossing provided with LGPL 2.1 licence
https://github.com/KipCrossing/geotiff
