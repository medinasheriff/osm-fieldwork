#!/usr/bin/python3

# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of odkconvert.
#
#     ODKConvert is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Underpass is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with odkconvert.  If not, see <https:#www.gnu.org/licenses/>.
#

import yaml
import argparse
import logging
import sys
import os
import pandas as pd
from geojson import Point, Feature, FeatureCollection, dump
import geojson


# Instantiate logger
log = logging.getLogger(__name__)


class FilterData(object):
    def __init__(self):
        self.tags = dict()

    def parse(self, filespec):
        data = pd.read_excel(filespec, sheet_name="Overview - all Tags", usecols=["key", "value"])
        
        entries = data.to_dict()
        total = len(entries['key'])
        index = 1
        while index < total:
            key = entries['key'][index]
            value = entries['value'][index]
            if value == "<text>":
                index += 1
                continue
            if key not in self.tags:
                self.tags[key] = list()
            self.tags[key].append(value)
            index += 1
        return self.tags

    def cleanData(self, filespec):
        # tmpfile = f"tmp-{filespec}"
        tmpfile = filespec
        #os.rename(filespec, tmpfile)
        outfile = open(f"new-{filespec}", "x")
        infile = open(tmpfile, "r")
        indata = geojson.load(infile)
        keep = ("name",
                "name:en",
                "id",
                "operator",
                "addr:street",
                "addr:housenumber",
                "osm_id",
                "title",
                "label",
                )
        collection = list()
        for feature in indata['features']:
            properties = dict()
            for key, value in feature['properties'].items():
                if key in keep:
                    properties[key] = value
                else:
                    if key in self.tags.keys():
                        if value in self.tags[key]:
                            properties[key] = value
                        else:
                            log.warning(f"Value {value} not in the data model!")
                            continue
                    else:
                        log.warning(f"Tag {key} not in the data model!")
                        continue
            newfeature = Feature(geometry=feature['geometry'], properties=properties)
            collection.append(newfeature)

        geojson.dump(FeatureCollection(collection), outfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert ODK XML instance file to CSV format"
    )
    parser.add_argument("-v", "--verbose", nargs="?", const="0", help="verbose output")
    parser.add_argument("-i", "--infile", help="The data extract for ODK Collect")
    parser.add_argument("-x", "--xform", help="The XForm for ODK Collect")
    args = parser.parse_args()

    # if verbose, dump to the termina
    if not args.verbose:
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        root.addHandler(ch)

    xls = FilterData()
    data = xls.parse(args.xform)
    xls.cleanData(args.infile)

