#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/globocom/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com

import json
from colormath.color_objects import sRGBColor, HSLColor
from colormath.color_conversions import convert_color

from thumbor.engines import BaseEngine
from thumbor.ext.filters import _fill


class JSONEngine(BaseEngine):

    def __init__(self, engine, path, callback_name=None):
        super(JSONEngine, self).__init__(engine.context)
        self._rgb = None
        self.engine = engine
        self.width, self.height = self.engine.size
        self.path = path
        self.callback_name = callback_name
        self.operations = []
        self.focal_points = []
        self.refresh_image()

    def refresh_image(self):
        self.image = self.engine.image

    @property
    def size(self):
        return self.engine.size

    def resize(self, width, height):
        self.operations.append({
            "type": "resize",
            "width": width,
            "height": height
        })
        self.engine.resize(width, height)
        self.refresh_image()

    def crop(self, left, top, right, bottom):
        self.operations.append({
            "type": "crop",
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom
        })
        self.engine.crop(left, top, right, bottom)
        self.refresh_image()

    def focus(self, points):
        for point in points:
            self.focal_points.append(point.to_dict())

    def flip_vertically(self):
        self.operations.append({"type": "flip_vertically"})

    def flip_horizontally(self):
        self.operations.append({"type": "flip_horizontally"})

    def get_target_dimensions(self):
        width = self.width
        height = self.height

        for operation in self.operations:
            if operation['type'] == 'crop':
                width = operation['right'] - operation['left']
                height = operation['bottom'] - operation['top']

            if operation['type'] == 'resize':
                width = operation['width']
                height = operation['height']

        return (width, height)

    def gen_image(self, size, color):
        return self.engine.gen_image(size, color)

    def create_image(self, buffer):
        return self.engine.create_image(buffer)

    def draw_rectangle(self, x, y, width, height):
        return self.engine.draw_rectangle(x, y, width, height)

    def rotate(self, degrees):
        return self.engine.rotate(degrees)

    def read_multiple(self, images, extension=None):
        return self.engine.read_multiple(images, extension)

    def paste(self, other_engine, pos, merge=True):
        return self.engine.paste(other_engine, pos, merge)

    def enable_alpha(self):
        return self.engine.enable_alpha()

    def strip_icc(self):
        return self.engine.strip_icc()

    def get_image_mode(self):
        return self.engine.get_image_mode()

    def get_image_data(self):
        return self.engine.get_image_data()

    def set_image_data(self, data):
        return self.engine.set_image_data(data)

    def image_data_as_rgb(self, update_image=True):
        return self.engine.image_data_as_rgb(update_image)

    def convert_to_grayscale(self):
        pass

    def _get_rgb(self):
        if self._rgb:
            return self._rgb
        mode, data = self.image_data_as_rgb()
        self._rgb = _fill.apply(mode, data)
        return self._rgb

    def get_median_color(self):
        r, g, b = self._get_rgb()
        return '#%02x%02x%02x' % (r, g, b)

    def get_black_percent(self):
        r, g, b = self._get_rgb()
        hsl = convert_color(sRGBColor(r, g, b), HSLColor)
        return hsl.hsl_l / 255

    def read(self, extension, quality):
        target_width, target_height = self.get_target_dimensions()
        thumbor_json = {
            "thumbor": {
                "source": {
                    "url": self.path,
                    "width": self.width,
                    "height": self.height,
                },
                "operations": self.operations,
                "target": {
                    "width": target_width,
                    "height": target_height
                },
                "median_color": {
                    "hex": self.get_median_color(),
                    "white_percent": round(self.get_black_percent(), 3)
                },
            }
        }

        if self.focal_points:
            thumbor_json["thumbor"]["focal_points"] = self.focal_points

        thumbor_json = json.dumps(thumbor_json)

        if self.callback_name:
            return "%s(%s);" % (self.callback_name, thumbor_json)

        return thumbor_json
