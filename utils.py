import os
import time
from functools import wraps
import numpy as np
import geopandas as gpd
import rasterio
import rasterio.mask as riomask
from rasterio.warp import (
    aligned_target,
    calculate_default_transform,
    reproject,
    Resampling,
)
from rasterio.merge import merge
from shapely.geometry import Polygon


def sigma_scale(img_array, z_score=4):
    mu, sigma = img_array[img_array != 0].mean(), img_array[img_array != 0].std()

    img_array = np.where(
        (img_array >= mu - (z_score * sigma)) & (img_array <= mu + (z_score * sigma)),
        img_array,
        0,
    )

    return max_scale(img_array)


def min_max_scale(img_array):
    mask = np.where(img_array == 0, True, False)
    min_val = max(img_array.min(), img_array.mean() - 2 * img_array.std())
    max_val = min(img_array.max(), img_array.mean() + 2 * img_array.std())
    img = (img_array - min_val) * 255 / (max_val - min_val)
    img[mask] = 0
    return img


def no_scale(img_array):
    return img_array


def max_scale(img_array):
    max_val = img_array.max()
    img_array = (img_array / max_val) * 255
    return img_array.astype(np.uint8)


def scale_band(img_array):
    mask = np.where(img_array == 0, True, False)
    min_val = max(img_array.min(), img_array.mean() - 2 * img_array.std())
    max_val = min(img_array.max(), img_array.mean() + 2 * img_array.std())
    img = (img_array - min_val) * 255 / (max_val - min_val)
    img[mask] = 0
    return img.astype(np.uint8)


def scale_ndvi(img_array):
    img = (img_array + 1) * 127
    return img.astype(np.uint8)


def timing(f):
    @wraps(f)
    def track_time(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print("func:%r took: %2.4f sec" % (f.__name__, te - ts))
        return result

    return track_time


def transform_resolution(data_path, save_path, resolution=(10, 10)):

    with rasterio.open(data_path) as src:

        transform, width, height = aligned_target(
            transform=src.meta["transform"],
            width=src.width,
            height=src.height,
            resolution=resolution,
        )

        kwargs = src.meta.copy()
        kwargs.update(
            {"transform": transform, "width": width, "height": height, "nodata": 0}
        )

        if ".jp2" in data_path:
            save_path = save_path.replace(".jp2", ".tif")
            kwargs["driver"] = "GTiff"
        with rasterio.open(save_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    resampling=Resampling.nearest,
                )

    return save_path


def transform_crs(data_path, save_path, dst_crs="EPSG:4326", resolution=(10, 10)):
    with rasterio.open(data_path) as src:
        if resolution is None:
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds
            )
        else:
            transform, width, height = calculate_default_transform(
                src.crs,
                dst_crs,
                src.width,
                src.height,
                *src.bounds,
                resolution=resolution,
            )
        kwargs = src.meta.copy()
        kwargs.update(
            {"crs": dst_crs, "transform": transform, "width": width, "height": height}
        )
        with rasterio.open(save_path, "w", **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest,
                )

    return save_path


def polygonize(contours, meta, transform=True, simplify=False, simp_tol=0.001):
    """Credit for base setup: Michael Yushchuk. Thank you!"""
    polygons = []
    for i in range(len(contours)):
        c = contours[i]
        n_s = (c.shape[0], c.shape[2])
        if n_s[0] > 2:
            if transform:
                polys = [tuple(i) * meta["transform"] for i in c.reshape(n_s)]
            else:
                polys = [tuple(i) for i in c.reshape(n_s)]
            polygons.append(Polygon(polys))

    if simplify is not False:
        polys = [x.simplify(simp_tol) for x in polygons]
    return polygons


def exclude_classes(dataframe, column, classes=[], txt_file=None, verbose=False):
    if txt_file is not None:
        if not os.path.exists(txt_file):
            raise FileNotFoundError(f"File {txt_file} not found")
        with open(txt_file, "r") as file:
            classes = file.read().split("\n")
            classes = [class_ for class_ in classes if len(class_) != 0]

    if len(classes) == 0:
        if verbose:
            print("No geometries will be excluded")
        return dataframe

    index_excluded = dataframe[column].isin(classes)
    dataframe = dataframe[~index_excluded]
    if verbose:
        print(f"{len(index_excluded)} geometries excluded.")
    return dataframe


def crop_raster(raster_path, aoi_path, out_raster_name=None):
    aoi = gpd.read_file(aoi_path)
    with rasterio.open(raster_path) as tile:
        meta = tile.meta
        region, region_tfs = riomask.mask(
            tile, aoi.to_crs(tile.crs).geometry, all_touched=False, crop=True
        )

    if out_raster_name is None:
        out_raster_name = raster_path.replace(".tif", "_cropped.tif")
        out_raster_name = out_raster_name.replace(".jp2", "_cropped.tif")
    out_raster_name = out_raster_name.replace(".jp2", ".tif")

    assert out_raster_name != raster_path

    meta["width"] = region.shape[-1]
    meta["height"] = region.shape[-2]
    meta["transform"] = region_tfs
    meta["nodata"] = 0
    meta["driver"] = "GTiff"

    with rasterio.open(out_raster_name, "w", **meta) as dst:
        for band in range(meta['count']):
            dst.write(region[band], band + 1)

    return out_raster_name