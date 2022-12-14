This is a test component

### Build image

`docker build -t registry.quantumobile.co/sip_landcover:0.0.1-dev .`

### Push to registry

`docker push registry.quantumobile.co/sip_landcover:0.0.1-dev`

### Docker run command

```
docker run \
    -e "AOI=POLYGON ((-85.299088 40.339368, -85.332047 40.241477, -85.134979 40.229427, -85.157639 40.34146, -85.299088 40.339368))" \
    -e "START_DATE=2016-05-01" \
    -e "END_DATE=2023-06-30" \
    -e "SENTINEL2_CACHE=/input/SENTINEL2_CACHE" \
    -e "OUTPUT_FOLDER=/output" \
    -v `pwd`/data/SENTINEL2_CACHE:/input/SENTINEL2_CACHE \
    -v `pwd`/data/results:/output \
    registry.quantumobile.co/sip_landcover:0.0.1-dev
```
