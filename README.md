# arc2server
rest server for arc2 rainfall data

## run the server

```
python3 server.py
```

## test the server

```
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
