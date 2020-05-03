import camelot.parsers.lattice
import cv2
import numpy as np
import copy


from camelot.utils import (
    scale_image,
    scale_pdf,
    segments_in_bbox,
    text_in_bbox,
    merge_close_lines,
    get_table_index,
    compute_accuracy,
    compute_whitespace,
)
from camelot.image_processing import (
    adaptive_threshold,
    find_lines,
    find_contours,
    find_joints,
)


class LatticeEx(camelot.parsers.lattice.Lattice):
    def __init__(
        self,
        table_regions=None,
        table_areas=None,
        process_background=False,
        line_scale=15,
        copy_text=None,
        shift_text=["l", "t"],
        split_text=False,
        flag_size=False,
        strip_text="",
        line_tol=2,
        joint_tol=2,
        threshold_blocksize=15,
        threshold_constant=-2,
        iterations=0,
        resolution=300,
        image_proc=None,
        **kwargs
    ):
        super().__init__(
            table_regions = table_regions,
            table_areas = table_areas,
            process_background = process_background,
            line_scale = line_scale,
            copy_text = copy_text,
            shift_text = shift_text,
            split_text = split_text,
            flag_size = flag_size,
            strip_text = strip_text,
            line_tol = line_tol,
            joint_tol = joint_tol,
            threshold_blocksize = threshold_blocksize,
            threshold_constant = threshold_constant,
            iterations = iterations,
            resolution = resolution,
             **kwargs
        )
        self.image_proc = image_proc


    def _generate_table_bbox(self):
        def scale_areas(areas):
            scaled_areas = []
            for area in areas:
                x1, y1, x2, y2 = area.split(",")
                x1 = float(x1)
                y1 = float(y1)
                x2 = float(x2)
                y2 = float(y2)
                x1, y1, x2, y2 = scale_pdf((x1, y1, x2, y2), image_scalers)
                scaled_areas.append((x1, y1, abs(x2 - x1), abs(y2 - y1)))
            return scaled_areas

        self.image, self.threshold = adaptive_threshold(
            self.imagename,
            process_background=self.process_background,
            blocksize=self.threshold_blocksize,
            c=self.threshold_constant,
        )

        image_width = self.image.shape[1]
        image_height = self.image.shape[0]
        image_width_scaler = image_width / float(self.pdf_width)
        image_height_scaler = image_height / float(self.pdf_height)
        pdf_width_scaler = self.pdf_width / float(image_width)
        pdf_height_scaler = self.pdf_height / float(image_height)
        image_scalers = (image_width_scaler, image_height_scaler, self.pdf_height)
        pdf_scalers = (pdf_width_scaler, pdf_height_scaler, image_height)

        ############
        # ここだけベースクラスと異なる処理
        if self.image_proc:
            self.threshold = self.image_proc(self.threshold)
        ############

        if self.table_areas is None:
            regions = None
            if self.table_regions is not None:
                regions = scale_areas(self.table_regions)

            vertical_mask, vertical_segments = find_lines(
                self.threshold,
                regions=regions,
                direction="vertical",
                line_scale=self.line_scale,
                iterations=self.iterations,
            )
            horizontal_mask, horizontal_segments = find_lines(
                self.threshold,
                regions=regions,
                direction="horizontal",
                line_scale=self.line_scale,
                iterations=self.iterations,
            )

            contours = find_contours(vertical_mask, horizontal_mask)
            table_bbox = find_joints(contours, vertical_mask, horizontal_mask)
        else:
            vertical_mask, vertical_segments = find_lines(
                self.threshold,
                direction="vertical",
                line_scale=self.line_scale,
                iterations=self.iterations,
            )
            horizontal_mask, horizontal_segments = find_lines(
                self.threshold,
                direction="horizontal",
                line_scale=self.line_scale,
                iterations=self.iterations,
            )

            areas = scale_areas(self.table_areas)
            table_bbox = find_joints(areas, vertical_mask, horizontal_mask)

        self.table_bbox_unscaled = copy.deepcopy(table_bbox)

        self.table_bbox, self.vertical_segments, self.horizontal_segments = scale_image(
            table_bbox, vertical_segments, horizontal_segments, pdf_scalers
        )
