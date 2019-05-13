# -*- coding: utf-8 -*-

"""
Class and functions to segment nucleus and cytoplasm in 2-d and 3-d.
"""

from bigfish import stack

from skimage.morphology import remove_small_objects, remove_small_holes
from skimage.measure import label
from scipy import ndimage as ndi
import numpy as np
from skimage.measure import regionprops


# TODO rename functions
# TODO complete documentation methods
# TODO add sanity functions

def nuc_segmentation_2d(tensor, projection_method, r, c, segmentation_method,
                        return_label=False, **kwargs):
    """Segment nuclei from a 2-d projection.

    Parameters
    ----------
    tensor : nd.ndarray, np.uint
        Tensor with shape (r, c, z, y, x).
    projection_method : str
        Method used to project the image in 2-d.
    r : int
        Round index to process.
    c : int
        Channel index of the dapi image.
    segmentation_method : str
        Method used to segment the nuclei.
    return_label : bool
        Condition to count and label the instances segmented in the image.

    Returns
    -------
    image_segmented : np.ndarray, bool
        Binary 2-d image with shape (y, x).
    image_labelled : np.ndarray, np.int64
        Image with labelled segmented instances and shape (y, x).
    nb_labels : int
        Number of different instances segmented.
    """
    # check tensor dimensions and its dtype
    stack.check_array(tensor, ndim=5, dtype=[np.uint8, np.uint16])

    # get a 2-d dapi image
    image_2d = stack.projection(tensor,
                                method=projection_method,
                                r=r,
                                c=c)

    # apply segmentation
    # TODO validate the pipeline with this cast
    image_segmented = stack.cast_img_uint8(image_2d)
    if segmentation_method == "threshold":
        image_segmented = filtered_threshold(image_segmented, **kwargs)
    else:
        pass

    # labelled and count segmented instances
    if return_label:
        image_labelled, nb_labels = label_instances(image_segmented)
        return image_segmented, image_labelled, nb_labels
    else:
        return image_segmented


def filtered_threshold(image, kernel_shape="disk", kernel_size=200,
                       threshold=2, small_object_size=2000):
    """Segment a 2-d image to discriminate object from background.

    1) Compute background noise applying a large mean filter.
    2) remove this background from original image, clipping negative values
    to 0.
    3) Apply a threshold in the image
    4) Remove object with a small pixel area.
    5) Fill in holes in the segmented objects.

    Parameters
    ----------
    image : np.ndarray, np.uint
        A 2-d image to segment with shape (y, x).
    kernel_shape : str
        Shape of the kernel used to compute the filter ('diamond', 'disk',
        'rectangle' or 'square').
    kernel_size : int or Tuple(int)
        The size of the kernel. For the rectangle we expect two integers
        (width, height).
    threshold : int
        Pixel intensity threshold used to discriminate background from nuclei.
    small_object_size : int
        Pixel area of small objects removed after segmentation.

    Returns
    -------
    image_segmented : np.ndarray, bool
        Binary 2-d image with shape (y, x).

    """
    # remove background noise from image
    image = stack.remove_background(image,
                                    kernel_shape=kernel_shape,
                                    kernel_size=kernel_size)

    # discriminate nuclei from background, applying a threshold.
    image_segmented = image >= threshold

    # clean the segmented result
    remove_small_objects(image_segmented,
                         min_size=small_object_size,
                         in_place=True)
    image_segmented = ndi.binary_fill_holes(image_segmented)

    return image_segmented
