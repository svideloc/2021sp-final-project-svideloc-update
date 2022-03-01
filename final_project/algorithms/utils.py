import uuid
from rtree import index
import pandas as pd


def overlapping_boxes(box, unique_id, rtree_index):
    """Returns a list of dicts of boxes in an rtree overlapping with box

    :param box: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type box: Tuple
    :param unique_id: unique_id
    :type unique_id: Int
    :param rtree_index: rtree_index
    :type rtree_index: rtree.index.Index
    ...
    :return: list of overlapping boxes
    :rtype: List(Tuples)
    """
    overlapping_hits = list(rtree_index.intersection(box, objects=True))
    overlap_boxes = [
        {"unique_id": item.id, "bounds": item.bbox} for item in overlapping_hits
    ]

    box_1_index = next(
        i for i, item in enumerate(overlap_boxes) if item["unique_id"] == unique_id
    )
    overlap_boxes.pop(box_1_index)
    return overlap_boxes


def new_boxes(original_bounds, unique_id, list_overlapping_boxes, coef):
    """Takes in original box, and a list of the overlapping_boxes, and returns a list
    of the calculated new cubes

    :param original_bounds: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type original_bounds: Tuple
    :param unique_id: unique_id
    :type unique_id: Int
    :param list_overlapping_boxes: list of overlapping boxes
    :type list_overlapping_boxes: List(Tuple)
    :param coef: algorithm coeficient for padding
    :type coef: Float
    ...
    :return: list of overlapping boxes
    :rtype: List(Tuple)
    """
    new_cube_list = [
        {
            "unique_id": create_uuid_int64(),
            "bounds": combined_box(original_bounds, overlap_box["bounds"]),
            "box_1_uuid": unique_id,
            "box_2_uuid": overlap_box["unique_id"],
        }
        for overlap_box in list_overlapping_boxes
    ]

    for index, new_cube in enumerate(new_cube_list):
        new_cube.update(
            {
                "delta_c": delta_c(
                    original_bounds,
                    list_overlapping_boxes[index]["bounds"],
                    new_cube["bounds"],
                    coef=coef,
                )
            }
        )

    return new_cube_list


def create_rtree(df):
    """Takes in a dataframe out returns an rtree

    :param df: must contain bounds and unique_id column
    :type df: pandas.DataFrame
    ...
    :return: an rtree index
    :rtype: rtree.Index
    """
    # specify 3d space
    p = index.Property()
    p.dimension = 3

    # create index object
    rtree_index = index.Index(properties=p)

    # add boxes to the rtree index
    [rtree_index.insert(df.unique_id[idx], df.bounds[idx]) for idx in df.index]

    return rtree_index


def combined_box(box_1, box_2):
    """Takes two tuple Prism.bounds and returns a new "combined" box

    :param box_1: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type box_1: Tuple
    :param box_2: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type box_2: Tuple
    ...
    :return: the new box, (xmin, ymin, tmin, xmax, ymax, tmax)
    :rtype: Tuple
    """

    new_box = (
        min(box_1[0], box_2[0]),
        min(box_1[1], box_2[1]),
        min(box_1[2], box_2[2]),
        max(box_1[3], box_2[3]),
        max(box_1[4], box_2[4]),
        max(box_1[5], box_2[5]),
    )

    return new_box


def delta_c(box_1, box_2, merge_box, coef=0):
    """Calculate the deltaC for optimization

    :param box_1: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type box_1: Tuple
    :param box_2: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type box_2: Tuple
    :param merge_box: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type merge_box: Tuple
    :param coef: algorithm coeficient for padding
    :type coef: Float
    ...
    :return: delta_c value
    :rtype: Int
    """
    return box_volume(merge_box) - box_volume(box_1) - box_volume(box_2) - coef


def padded_box(bounds, coef=0):
    """Provides a pad around an exisiting bounding box

    :param bounds: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type bounds: Tuple
    :param coef: algorithm coeficient for padding
    :type coef: Float
    ...
    :return: padded bounds
    :rtype: Tuple
    """

    Lx = bounds[3] - bounds[0]
    Ly = bounds[4] - bounds[1]
    Lt = bounds[5] - bounds[2]

    px = coef / (Ly * Lt)
    py = coef / (Lx * Lt)
    pt = coef / (Lx * Ly)

    return (
        bounds[0] - px,
        bounds[1] - py,
        bounds[2] - pt,
        bounds[3] + px,
        bounds[4] + py,
        bounds[5] + pt,
    )


def box_volume(box_tuple):
    """volume of a prism

    :param box_tuple: (xmin, ymin, tmin, xmax, ymax, tmax)
    :type box_tuple: Tuple
    ...
    :return: volume of the prism
    :rtype: Float
    """

    return (
        (box_tuple[3] - box_tuple[0])
        * (box_tuple[4] - box_tuple[1])
        * (box_tuple[5] - box_tuple[2])
    )


def create_uuid_int64():
    """returns unique id that can be used in rtree index

    :return: uuid
    :rtype: int
    """
    return uuid.uuid1().int >> 65


def df_for_greedy(in_prisms):
    """converts list of prisms into dataframe

    :param in_prisms: [Prism]
    :type in_prisms: List(Prism)
    ...
    :return: dataframe
    :rtype: pandas.DataFrame
    """

    df = pd.DataFrame()
    df["bounds"] = [prism.bounds for prism in in_prisms]
    df["name"] = [prism.name for prism in in_prisms]
    df["unique_id"] = [prism.uuid for prism in in_prisms]
    df["boxes_inside"] = df.apply(lambda x: [], axis=1)

    return df
