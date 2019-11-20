#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2019 Next Century Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Read in submission, metadata, and ground truth to create an elastic search
index that can be read by Neon.

"""
import json
import argparse
import shutil
from pathlib import Path
import tempfile
import zipfile
import os
from collections import defaultdict
import traceback


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('zipfile', help='The submission file, a zip file')
    return parser.parse_args()


class MCSEval1Validator:
    """
    Validate a submission file (a zip), making sure that it has all the files in it that it needs and
    that they are all in the right format.
    """

    def __init__(self):
        pass

    def validate(self, filename):

        # Make sure that it exists
        if not os.path.exists(filename):
            print("The file {} does not exist.".format(filename))
            return False

        # Make sure that it ends with .zip
        if not filename.endswith(".zip"):
            print("The file {} does not end with .zip".format(filename))
            return False

        # Make sure it is a valid .zip file
        if not self.valid_zip(filename):
            return False

        # Extract the data to a temp dir
        temp_dir = tempfile.mkdtemp()
        # print("Temp dir: {}".format(temp_dir))

        try:
            my_zip = zipfile.ZipFile(filename)
            my_zip.extractall(temp_dir)

            # Make sure it has an answer.txt file
            if not self.valid_answer(temp_dir):
                return False

            # Make sure that it has a description file
            if not self.valid_description(temp_dir):
                return False

            if not self.valid_location(temp_dir):
                return False

            if not self.valid_voe(temp_dir):
                return False

        except Exception as e:
            print("Unknown exception in validate on file {}: {}".format(filename, e))
            traceback.print_exc()
            return False

        finally:
            shutil.rmtree(temp_dir)
            pass

        # If we have passed all the tests, then return true
        return True

    def valid_location(self, dir):
        dirpath = Path(dir)
        filepath = dirpath / "location.txt"
        if not filepath.exists():
            print("location.txt does not exist in unzipped")
            return False
        return self.parse_location(filepath)

    def parse_location(self, location_filepath):
        with location_filepath.open("r") as location_file:
            line_counter = 0
            for line in location_file:
                # Line should look like:  O1/0005/4 97 46 51
                split_line = line.split()
                if (len(split_line)) != 4:
                    print("Line {}: {} does not have 4 fields in location.txt".format(line_counter, line))
                    return False

                if not self.parse_block_test_scene( split_line[0]):
                    print("Line {} failed to parse block / test / scene".format(line))
                    return False

                for index in [1,2]:
                    val = int(split_line[index])
                    if val == -1:
                        pass
                    elif 0 <= val <= 100:
                        pass
                    else:
                        print("Line {} does not have valid location {}".format(line, val))
                        return False

                val = int(split_line[3])
                if val == -1:
                    pass
                elif 0 <= val <= 256:
                    pass
                else:
                    print("Line {} does not have valid mask value {}".format(line, val))
                    return False

        return True

    def parse_block_test_scene(self, first_part):
        """
        Parse the part of the line from answer.txt and location.txt that has
        the block / test / scene.  It should look like:  O1/0005/4, so block
        is O1, the test is 0005, and the scene is 4.
        """
        key = first_part.split('/')
        if len(key) != 3:
            print("Line {} does not have 3 parts of key".format(first_part))
            return False

        block = str(key[0])
        test = str(key[1])
        scene = str(key[2])
        # print("{} {} {} {}".format(block, test, scene, split_line[1]))

        if block not in ['O1', 'O2', 'O3']:
            print("Line does not have correct block {}".format(first_part))
            return False

        test_as_int = int(test)
        if not 0 < test_as_int < 1081:
            print("Line does not have correct test number {} != {}".format(test, test_as_int))
            return False

        if scene not in ['1', '2', '3', '4']:
            print("Line does not have correct scene {}".format(scene))
            return False

        return True

    def valid_description(self, dir):
        dirpath = Path(dir)
        filepath = dirpath / "description.json"
        if not filepath.exists():
            print("description.json does not exist in unzipped")
            return False
        return self.parse_description(filepath)

    def parse_description(self, description_filepath):
        with description_filepath.open() as description_file:
            try:
                description = json.load(description_file)

                if "Performer" not in description.keys():
                    print("No performer in description {}".format(description))
                    return False

                if "Submission" not in description.keys():
                    print("No submission information in description {}".format(description))
                    return False

            except Exception as e:
                print("Unknown exception in parse_description on file {}: {}".format(description_filepath, e))
                return False

        return True

    def valid_answer(self, dir):
        dirpath = Path(dir)
        filepath = dirpath / "answer.txt"
        if not filepath.exists():
            print("answer.txt does not exist in unzipped")
            return False
        return self.parse_answer(filepath)

    def parse_answer(self, answerpath):
        with answerpath.open("r") as answer_file:
            line_counter = 0
            for line in answer_file:
                # Line should look like:  O3/1076/2 1
                split_line = line.split()
                if len(split_line) != 2:
                    print("Line {}: {} does not have 2 fields in answer.txt".format(line_counter, line))
                    return False

                if not self.parse_block_test_scene( split_line[0]):
                    print("Line {} failed to parse block / test / scene".format(line))
                    return False

                try:
                    val = float( split_line[1])
                    if not 0 <= val <= 1:
                        print("Line {} does not have valid plausibility {}".format(line, val))
                        return False
                except Exception as e:
                    print("Line {} does not have parse-able plausibility {}: {}".format(line, split_line[1], e))
                    return False
                line_counter = line_counter + 1

        correct_line_count = 1080 * 3 * 4
        if not line_counter == correct_line_count:
            print("Wrong number of lines in answer.txt: {}.  Should be {}".format(line_counter, correct_line_count))
            return False

        return True

    def valid_zip(self, filename):
        try:
            my_zip = zipfile.ZipFile(filename)
            ret = my_zip.testzip()
            if ret is not None:
                print(" Bad zip.  Zipfile reports {}".format(ret))
                return False
        except Exception as e:
            print("Caught exception reading zipfile {}:  {}".format(filename, str(e)))
            return False
        return True

if __name__ == "__main__":
    arguments = parse_arguments()
    validator = MCSEval1Validator()
    validator.validate(arguments.zipfile)