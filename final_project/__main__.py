import os
import sys
import logging
import argparse
import datetime

import pandas as pd

from .algorithms.generator import prisms_projected_output, create_prisms_by_ll
from .algorithms.greedy import Greedy

DESC = """
Cronos Greedy Algorithm Script

Example
-------
python -m final_project -f data/test_file.csv --lat=1 --lon=2 --time=3 --name=4 -n NAME -j "justification is here"
"""

parser = argparse.ArgumentParser(description=DESC)


parser.add_argument(
    "--file-path",
    "-f",
    required=True,
    help="location of the csv or excel file containing the columns lat, \
            long, timestamp, names",
)
parser.add_argument(
    "--lat",
    required=True,
    type=int,
    help="location of the latitude column in the excel or csv, for reference 0 is column A in excel",
)
parser.add_argument(
    "--lon",
    required=True,
    type=int,
    help="location of the longitude column in the excel or csv, for reference 0 is column A in excel",
)
parser.add_argument(
    "--time",
    required=True,
    type=int,
    help="location of the timestamp column in the excel or csv, for reference 0 is column A in excel",
)
parser.add_argument(
    "--name",
    required=True,
    type=int,
    help="location of the name col in the excel or csv, for reference 0 is column A in excel",
)
parser.add_argument(
    "--job-name",
    "-n",
    required=True,
    help="name of the job",
)
parser.add_argument(
    "--justification",
    "-j",
    required=True,
    type=str,
    help="justification for running search",
)
parser.add_argument(
    "--coef",
    "-c",
    type=int,
    default=0,
    help="algorithm coefficient, default 0",
)
parser.add_argument(
    "--temporal-buffer",
    "-t",
    type=int,
    default=30 * 60,  # 30 mins
    help="time buffer in seconds",
)
parser.add_argument(
    "--distance-buffer",
    "-d",
    type=int,
    default=100,  # 100 meters
    help="distance buffer in meters",
)
parser.add_argument(
    "--report",
    "-r",
    action="store_true",
    help="Small report will be generated if True",
)
parser.add_argument(
    "--output-path",
    "-o",
    default=".",
    help="output path for the file, will save as output_path/job_name.csv",
)

if __name__ == "__main__":

    args = parser.parse_args()
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

    # Load the configuration
    if not os.path.exists(args.file_path):
        print("Invalid file: %s" % args.file_path)
        sys.exit(-1)

    # read data into pandas df, try reading csv, otherwise excel
    logging.info("Loading data from file: %s" % args.file_path)
    try:
        df = pd.read_csv(args.file_path)
    except:
        df = pd.read_excel(args.file_path)

    logging.info("Configuring lat, long, timestamp, name mappings")
    df = df.iloc[:, [args.lat, args.lon, args.time, args.name]]
    df.columns = ["latitude", "longitude", "timestamp", "name"]

    # remove nans
    df = df.dropna()  # drops rows with nans
    df = df.reset_index(drop=True)  # reset index

    # this will need to be re-worked probably
    if df["timestamp"].dtype == object and isinstance(df.iloc[0]["timestamp"], str):
        df["timestamp"] = df.timestamp.apply(
            lambda date: datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
        )
        timestamps = list(df.timestamp)
        df["timestamp"] = [t.timestamp() for t in timestamps]

    logging.info("Generating prisms")
    in_prisms = create_prisms_by_ll(
        df.longitude,
        df.latitude,
        df.timestamp,
        df.name,
        temporal_buffer=args.temporal_buffer,
        x_buffer=args.distance_buffer,
        y_buffer=args.distance_buffer,
    )

    logging.info("Run Greedy Alg")
    greedy = Greedy()
    out_prisms = greedy.run(in_prisms, args.coef)

    logging.info("Generating kml & csv")
    df_res, kml = prisms_projected_output(out_prisms)

    df_res["tmin"] = df_res.tmin.apply(
        lambda date: datetime.datetime.fromtimestamp(date)
    )
    df_res["tmax"] = df_res.tmax.apply(
        lambda date: datetime.datetime.fromtimestamp(date)
    )
    df_res["status"] = "created"
    df_res["update_time"] = datetime.datetime.now()
    df_res["justification"] = args.justification
    df_res["job_name"] = args.job_name
    df_res["url"] = None

    logging.info(f"Saving files to {args.output_path}")
    kml.save(os.path.join(args.output_path, args.job_name + ".kml"))
    df_res.to_csv(os.path.join(args.output_path, args.job_name + ".csv"), index=False)
