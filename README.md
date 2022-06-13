There is one file that should be present in the same folder: <a href="https://drive.google.com/file/d/17g0xML2n4Cyv7zyXkSkFqLhFQVBoh-gX/view?usp=sharing">sentinel2grid.geojson</a>

# for adding landcover package to sip project:

## Clone repository:
```shell
git clone https://github.com/QuantuMobileSoftware/sip_landcover landcover
cd landcover
git submodule update --init --recursive
```
Repository require additional rights

## for enabling nfs support 
```shell
sudo apt-get install cifs-utils
sudo apt-get install nfs-common
```

#get requirements from NFS server
```shell
sudo mount 192.168.1.58:/volume1/SIP /home/quantum/sip

cp -r --remove-destination /home/quantum/sip/.prod_notebooks_requirements/landcover/Landcover/sentinel2grid.geojson data/notebooks/landcover/Landcover
sudo umount /home/quantum/sip
```

## copy requirements from repository to jupyter folder
```shell
cp -r --remove-destination data/notebooks/landcover/Landcover/requirements.txt jupyter/landcover/requirements.txt
```
# Building images for prod
after updating all files from git repository, go to project SIP root directory

## for building common_pbdnn:latest
```shell
docker build -f ./jupyter/landcover/Dockerfile -t landcover:latest .
```
