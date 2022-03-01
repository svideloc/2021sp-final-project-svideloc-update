import simplekml
import datetime, pytz
import pandas as pd
from pyproj import Proj, Transformer

from .prism import Prism


def prisms_projected_output(prisms, in_crs="epsg:3857"):
    """prisms list of bounds

    :param prisms: list of prisms
    :type prisms: List[prism.Prism]
    :param in_crs: input crs
    :type in_crs: str
    ...
    :returns: df, simple kml
    """

    bounds = ll_bounds_from_prisms(prisms, in_crs)
    df = pd.DataFrame.from_records(
        bounds, columns=["xmin", "ymin", "tmin", "xmax", "ymax", "tmax"]
    )

    kml = simplekml.Kml()

    for b in bounds:
        insert_prism(kml, b)

    return df, kml


def create_prisms_by_ll(
    lons,
    lats,
    timestamps,
    names,
    temporal_buffer,
    x_buffer,
    y_buffer,
    out_crs="epsg:3857",
):
    """create a list of prisms given a list of lon/lat/timestampes/names, etc

    :param lons: list of lons
    :type lons: List[float]
    :param lats: list of lats
    :type lats: List[float]
    :param timestamps: list of timestamps
    :type timestamps: List[float]
    :param names: list of names
    :type names: List[Str]
    :param temporal_buffer: temporal buffer to create prism in seconds
    :type temporal_buffer: Int
    :param x_buffer: x_buffer to create prism in meters
    :type x_buffer: Float
    :param y_buffer: y_buffer buffer to create prism in meters
    :type y_buffer: Float
    :param out_crs: the projection to use
    :type out_crs: Str
    ...
    :return: list of prism objects
    :rtype: List[prism.Prism]

    """
    transformer = Transformer.from_proj(
        Proj("epsg:4326"), Proj(out_crs), always_xy=True
    )
    Xs, Ys = transformer.transform(lons, lats)
    data = list(zip(lons, lats, Xs, Ys, timestamps, names))
    prisms = [
        Prism(
            lon=lon,
            lat=lat,
            x=x,
            y=y,
            crs=out_crs,
            timestamp=ts,
            name=name,
            x_buffer=x_buffer,
            y_buffer=y_buffer,
            temporal_buffer=temporal_buffer,
        )
        for lon, lat, x, y, ts, name in data
    ]
    return prisms


def create_prisms_by_proj(bounds, names, in_crs="epsg:3857"):
    """create a list of prisms given a set of bounds, names, and the input_crs

    :param bounds: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type bounds: Tuple
    :param names: list of names
    :type names: List[Str]
    ...
    :return: list of prism objects
    :rtype: List[prism.Prism]

    """

    transformer = Transformer.from_proj(Proj(in_crs), Proj("epsg:4326"), always_xy=True)
    df = pd.DataFrame(bounds, columns=["xmin", "ymin", "tmin", "xmax", "ymax", "tmax"])
    df["x"] = (df["xmax"] + df["xmin"]) / 2.0
    df["y"] = (df["ymax"] + df["ymin"]) / 2.0
    df["t"] = (df["tmax"] + df["tmin"]) / 2.0
    df["name"] = names
    df["lon"], df["lat"] = transformer.transform(df["x"], df["y"])
    prisms = []
    for index, row in df.iterrows():
        prism = Prism(
            lat=row["lat"],
            lon=row["lon"],
            x=row["x"],
            y=row["y"],
            crs=in_crs,
            timestamp=row["t"],
            name=row["name"],
            x_buffer=(row["x"] - row["xmin"]),
            y_buffer=(row["y"] - row["ymin"]),
            temporal_buffer=(row["t"] - row["tmin"]),
        )

        prisms.append(prism)
    return prisms


def ll_bounds_from_prisms(prisms, in_crs="epsg:3857"):
    """prisms list of bounds

    :param prisms: list of prisms
    :type prisms: List[prism.Prism]
    :param in_crs: input crs
    :type in_crs: str
    ...
    :returns: list of bounds [(xmin, ymin tmin, xmax, ymax, tmax)]
    :rtype: List[Tuple]
    """

    projected_bounds = [prism.bounds for prism in prisms]

    df_results = pd.DataFrame.from_records(
        projected_bounds, columns=["xmin", "ymin", "tmin", "xmax", "ymax", "tmax"]
    )

    transformer = Transformer.from_proj(Proj(in_crs), Proj("epsg:4326"), always_xy=True)

    df_results["latmin"], df_results["lonmin"] = transformer.transform(
        df_results.xmin, df_results.ymin
    )
    df_results["latmax"], df_results["lonmax"] = transformer.transform(
        df_results.xmax, df_results.ymax
    )

    return list(
        zip(
            df_results.latmin,
            df_results.lonmin,
            df_results.tmin,
            df_results.latmax,
            df_results.lonmax,
            df_results.tmax,
        )
    )


def datestr(timestamp):
    """datestr from timestamp"""
    return datetime.datetime.fromtimestamp(timestamp, pytz.utc).isoformat()


def insert_prism(kml, bounds_tuple):
    """
    :param kml: a simplekml.Kml
    :param bounds_tuple: (lon-min, lat-min, time-min, lon-max, lat-max, time-max)
    ...
    :returns: the newly inserted kml polygon
    """
    (lon0, lat0, t0, lon1, lat1, t1) = bounds_tuple
    corners = [(lon0, lat0), (lon0, lat1), (lon1, lat1), (lon1, lat0), (lon0, lat0)]
    poly = kml.newpolygon(
        name="query volume", outerboundaryis=corners, innerboundaryis=[]
    )
    poly.timespan.begin = datestr(bounds_tuple[2])
    poly.timespan.end = datestr(bounds_tuple[5])
    poly.style.polystyle.color = "9900ff00"
    return poly
