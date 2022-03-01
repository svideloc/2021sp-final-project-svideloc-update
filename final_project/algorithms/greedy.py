#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import itertools
import pandas as pd

from .algorithm import Algorithm
from .prism import Prism
from .utils import overlapping_boxes, new_boxes, create_rtree, combined_box
from .utils import delta_c, padded_box, box_volume, df_for_greedy, create_uuid_int64
from .generator import create_prisms_by_proj

logger = logging.getLogger(__name__)


class Greedy(Algorithm):
    """Class for running greedy apporach on a list of prisms to optimize
    querey search space

    :param out_prisms: list of prism objects for the optimized space
    :type out_prisms: List[prism.Prism]
    :param in_prism: list of prism objects for the original space
    :type in_prisms: List[prism.Prism]
    :param: boxes_inside: List of dictionaries with internal boxes (for plotting)
    :type: boxes_inside: List[Dict]
    """

    def __init__(self):
        super().__init__("Greedy")
        self.out_prisms = None
        self.boxes_inside = None
        self.in_prisms = None

    def run(self, in_prisms, coef):
        """Takes in a list of prisms, and outputs an optimized list of prisms

        :param in_prisms: list of prisms
        :type in_prisms: List[prism.Prism]
        :param coef: algorithm coeficient for padding
        :type coef: Float
        ...
        :return list of out_prisms
        :rtype: List[prism.Prism]
        """

        # save as an attribute for below properties
        self.in_prisms = in_prisms

        # convert list of prisms to dataframe
        df = df_for_greedy(self.in_prisms)

        # run greedy alg (outputs a df with bounds/unique_id)
        df_results = greedy(df, coef)

        # convert results dataframe back into prisms
        self.out_prisms = create_prisms_by_proj(
            list(df_results.bounds), list(df_results.name), in_crs="epsg:3857"
        )
        self.boxes_inside = list(df_results.boxes_inside)

        return self.out_prisms

    @property
    def inside_uuids(self):
        """Returns a dictionary of result_prism uuids as the key, and input_prism id's as a list of the values
        {result_prism_uuid: [original_prism_uuids]}

        :return: dict of result prisms inside uuids
        :rtype: dict
        """
        uuid_list = [prism.uuid for prism in self.out_prisms]
        return dict(zip(uuid_list, self.boxes_inside))

    @property
    def inside_bounds(self):
        """Returns a dictionary of result_prism bounds as the key, and input_prism id's as a list of the values

        :return: dict of result prisms inside bounds
        :rtype: dict
        """
        new_list = []
        for key, value in self.inside_uuids.items():
            if value == []:
                merged_box = [
                    prism.bounds for prism in self.out_prisms if prism.uuid == key
                ][0]
                d = {
                    "merged_uuid": key,
                    "inner_bounds_uuid": None,
                    "merged_bounds": merged_box,
                    "inner_bounds": None,
                }

                new_list.append(d)
            else:
                merged_box = [
                    prism.bounds for prism in self.out_prisms if prism.uuid == key
                ][0]
                inner_bounds = [
                    prism.bounds for prism in self.in_prisms if prism.uuid in value
                ]

                d = {
                    "merged_uuid": key,
                    "inner_bounds_uuid": value,
                    "merged_bounds": merged_box,
                    "inner_bounds": inner_bounds,
                }

                new_list.append(d)
        return new_list


def greedy(df, coef=0):
    """Greedy algorithm for merging boxes in 3d space

    :param df: pandas Dataframe, with columns unique_id, bounds, bounds is a tuple (xmin, ymin, tmin, xmax, ymax, tmax)
    :type df: pandas.DataFrame
    :param coef: algorithm coeficient for padding
    :type coef: Float
    ...
    :return: pandas Dataframe with new (improved) query space
    :rtype: pandas.DataFrame
    """
    df_master = df.copy()
    total_points = len(df_master)

    # if we have an empty dataframe throw an error
    if df_master.empty:
        return []

    # if we only have 1 value in dataframe, return that as the query list
    if len(df_master) < 2:
        return [df_master.iloc[0].to_dict()]

    # remove duplicates & append a column that contains boxes in boxes
    df_master = df_master.drop_duplicates(subset=["bounds"])
    logger.info(f"{total_points - len(df_master)} duplicates")

    # calculate the padded boxes, returns the original bounds if coef = 0
    df_master["padded_boxes"] = df_master.apply(
        lambda x: padded_box(x.bounds, coef=coef), axis=1
    )

    # create rtree
    logger.info("creating Rtree")
    rtree_index = create_rtree(df_master)

    # find overlapping boxes
    logger.info("finding overlapping boxes")
    df_master["overlap_boxes"] = df_master.apply(
        lambda x: overlapping_boxes(x.padded_boxes, x.unique_id, rtree_index),
        axis=1,
    )

    # calculates all of the overlapping boxes new boxes
    logger.info("calculating overlapping boxes")
    df_master["new_boxes"] = df_master.apply(
        lambda x: new_boxes(x.bounds, x.unique_id, x.overlap_boxes, coef=coef),
        axis=1,
    )

    # get all overlapping boxes as new dataframe (this gets big)
    new_boxes_list = df_master.new_boxes.tolist()
    flat_list = list(itertools.chain(*new_boxes_list))
    df_newboxes = pd.DataFrame(flat_list)

    # if we have no overlapping boxes, we are done
    if df_newboxes.empty:
        df_master = df_master.drop(
            ["overlap_boxes", "new_boxes", "padded_boxes"], axis=1
        )
        return df_master

    # sort by smallest delta_c
    logger.info("sort by delta C")
    df_newboxes = df_newboxes.sort_values(by=["delta_c"])

    logger.info("begin the Greedy loop")
    # loop through until no more overlappin boxes give us
    while len(df_master) > 0:

        # if we have a candidate to merge
        if df_newboxes.iloc[0].delta_c <= 0:

            # the first box in the df will be what we work with (most negative)
            merged_box = df_newboxes.iloc[0]

            # remove the two merged boxes from rtree
            df_delete = df_master.loc[
                (df_master.unique_id == int(merged_box.box_1_uuid))
                | (df_master.unique_id == int(merged_box.box_2_uuid))
            ]
            rtree_index.delete(
                int(df_delete.iloc[0].unique_id), df_delete.iloc[0].bounds
            )
            rtree_index.delete(
                int(df_delete.iloc[1].unique_id), df_delete.iloc[1].bounds
            )

            # remove merged boxes from df_master
            remove = [int(merged_box.box_1_uuid), int(merged_box.box_2_uuid)]
            df_master = df_master[~df_master.unique_id.isin(remove)]

            # append the new box to the rtree
            rtree_index.insert(merged_box.unique_id, merged_box.bounds)

            # append the new box to df_master
            new_box = {
                "unique_id": merged_box.unique_id,
                "bounds": merged_box.bounds,
                "padded_boxes": padded_box(merged_box.bounds, coef=coef),
                "boxes_inside": df_delete.iloc[0].boxes_inside
                + df_delete.iloc[1].boxes_inside
                + [merged_box.box_1_uuid, merged_box.box_2_uuid],
            }
            new_box["overlap_boxes"] = overlapping_boxes(
                new_box["padded_boxes"], new_box["unique_id"], rtree_index
            )
            new_box["new_boxes"] = new_boxes(
                new_box["bounds"],
                new_box["unique_id"],
                new_box["overlap_boxes"],
                coef=coef,
            )

            df2 = pd.DataFrame([new_box])
            df_master = df_master.append(df2, ignore_index=True)

            # remove all boxes from df_newboxes that have the merged uuids
            df_newboxes = df_newboxes[~df_newboxes.box_1_uuid.isin(remove)]
            df_newboxes = df_newboxes[~df_newboxes.box_2_uuid.isin(remove)]

            # append the new box to df_newboxes if it overlaps with anything
            new_boxes_list = df2.new_boxes.tolist()
            if new_boxes_list:
                flat_list = list(itertools.chain(*new_boxes_list))
                df_newboxes_from_df2 = pd.DataFrame(flat_list)
                df_newboxes = df_newboxes.append(
                    df_newboxes_from_df2, ignore_index=True
                )
                df_newboxes = df_newboxes.sort_values(by=["delta_c"])

            # if we have no overlapping boxes, we are done
            if df_newboxes.empty:
                break

        # otherwise no good moreoverlaps exist, and we return the final df_master
        else:
            break

    logger.info(
        f"No more overlapping boxes: {len(df_master)} queries in new search space"
    )
    df_master = df_master.drop(["overlap_boxes", "new_boxes", "padded_boxes"], axis=1)

    return df_master
