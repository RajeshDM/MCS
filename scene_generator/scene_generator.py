#!/usr/bin/env python3
#

import sys
import argparse
import os
import os.path
import json
import copy
import random
import uuid
import math


from materials import *
from goals import generate_goal

OUTPUT_TEMPLATE_JSON = """
{
  "name": "",
  "ceilingMaterial": "AI2-THOR/Materials/Walls/Drywall",
  "floorMaterial": "AI2-THOR/Materials/Fabrics/CarpetWhite 3",
  "wallMaterial": "AI2-THOR/Materials/Walls/DrywallBeige",
  "performerStart": {
    "position": {
      "x": 0,
      "z": 0
    },
    "rotation": {
      "y": 0
    }
  },
  "objects": [],
  "goal": {},
  "answer": {}
}
"""

OUTPUT_TEMPLATE = json.loads(OUTPUT_TEMPLATE_JSON)

# the following mins and maxes are inclusive
MIN_PERFORMER_POSITION = -4.8
MAX_PERFORMER_POSITION = 4.8
MIN_SCENE_POSITION = -4.95
MAX_SCENE_POSITION = 4.95
POSITION_DIGITS = 1
MIN_ROTATION = 0
MAX_ROTATION = 359
ROTATION_DIGITS = 0
MAX_TRIES = 6


def random_position():
    return round(random.uniform(MIN_PERFORMER_POSITION, MAX_PERFORMER_POSITION), POSITION_DIGITS)


def random_rotation():
    rotation = round(random.uniform(MIN_ROTATION, MAX_ROTATION), ROTATION_DIGITS)
    if ROTATION_DIGITS == 0:
        rotation = int(rotation)
    return rotation

def load_object_file(object_file_name):
    with open(object_file_name) as object_file:
        objects = json.load(object_file)
    return objects    
        

def dot_prod_dict(v1, v2):
    return sum (v1[key]*v2.get(key,0) for key in v1)

def collision(test_rect, test_point):
    #assuming test_rect is an array4 points in order... Clockwise or CCW does not matter
    #points are {x,y,z}
    #
    # From https://math.stackexchange.com/a/190373
    A=test_rect[0]
    B=test_rect[1]
    C=test_rect[2]
    
    vectorAB={'x': B['x']-A['x'], 'y': B['y']-A['y'], 'z': B['z']-A['z']}
    vectorBC={'x': C['x']-B['x'], 'y': C['y']-B['y'], 'z': C['z']-B['z']}
    
    vectorAM={'x': test_point['x']-A['x'], 'y': test_point['y']-A['y'], 'z': test_point['z']-A['z']}
    vectorBM={'x': test_point['x']-B['x'], 'y': test_point['y']-B['y'], 'z': test_point['z']-B['z']}
    
    return (0<=dot_prod_dict(vectorAB, vectorAM)<=dot_prod_dict(vectorAB, vectorAB)) & (0<=dot_prod_dict(vectorBC, vectorBM)<=dot_prod_dict(vectorBC, vectorBC))


def calc_obj_pos(performer_position, new_object, old_object):
    """"Returns True if we can place the object in the frame, False otherwise. Note modifications will be necessary for multiple objects"""

    dx = old_object['dimensions']['x']
    dz = old_object['dimensions']['z']
    
    #putting in a limit to the number of times we can choose for now
    #hard-coding a limit for now
    
    tries = 0
    while tries< MAX_TRIES:
        rotation_amount = round(random.uniform(MIN_ROTATION,MAX_ROTATION), 0)
        radian_amount = rotation_amount*math.pi/180.0
        new_x = random_position()
        new_z = random_position()
        rotate_sin = math.sin(radian_amount)
        rotate_cos = math.cos(radian_amount)
        a = { 'x': new_x+(dx*rotate_cos)-(dz*rotate_sin) , 'y' : 0 , 'z': new_z+(dx*rotate_sin+dz*rotate_cos)}
        b = { 'x': new_x+(dx*rotate_cos)-(dz*rotate_sin) , 'y' : 0 , 'z': new_z-(dx*rotate_sin+dz*rotate_cos)}
        c = { 'x': new_x-(dx*rotate_cos)+(dz*rotate_sin) , 'y' : 0 , 'z': new_z-(dx*rotate_sin+dz*rotate_cos)}
        d = { 'x': new_x-(dx*rotate_cos)+(dz*rotate_sin) , 'y' : 0 , 'z': new_z+(dx*rotate_sin+dz*rotate_cos)} 
        rect = [a, b, c, d]

        
        if  not collision(rect,performer_position):
            break;
        tries += 1
     
    if tries < MAX_TRIES :
        new_object['rotation'] = { 'x' : 0, 'y': rotation_amount, 'z': 0 }
        new_object['position'] = { 'x' : new_x, 'y': old_object['position_y'], 'z' : new_z}
        return True
    
    return False


def generate_file(name, objects, add_goal):
    global OUTPUT_TEMPLATE
    body = copy.deepcopy(OUTPUT_TEMPLATE)
    body['name'] = os.path.basename(name)
    body['ceilingMaterial'] = random.choice(CEILING_AND_WALL_MATERIALS)
    body['wallMaterial'] = random.choice(CEILING_AND_WALL_MATERIALS)
    body['floorMaterial'] =random.choice(FLOOR_MATERIALS)
    position = body['performerStart']['position']
    position['x'] = random_position()
    position['y'] = 0
    position['z'] = random_position()
    body['performerStart']['rotation']['y'] = random_rotation()
    
    selected_object = copy.deepcopy(random.choice(objects))
    
    
    shows_object = {}
    
    if calc_obj_pos(position, shows_object, selected_object):
        new_object = {}
        new_object['id'] = selected_object['type']+'_'+str(uuid.uuid4())
        new_object['type'] = selected_object['type']
        new_object['info'] = selected_object['info']
        new_object['mass'] = selected_object['mass']
        for attribute in selected_object['attributes']:
            new_object[attribute]= True
    
        shows = [shows_object]
        new_object['shows'] = shows;
        shows_object['stepBegin'] = 0;
        shows_object['scale'] = selected_object['scale']
        if 'salientMaterials' in selected_object:
            salientMaterialsIndex = selected_object['salientMaterials'][0].upper()+'_MATERIALS'
            salientMaterial = random.choice(globals().get(salientMaterialsIndex, None))
            new_object['material']=salientMaterial;
            new_object['info'].append(selected_object['salientMaterials'][0])
            new_object['salientMaterials'] = selected_object['salientMaterials']
        body['objects'].append(new_object)

    if add_goal:
        body['goal'] = generate_goal([new_object])
        
    with open(name, 'w') as out:
        json.dump(body, out, indent=2)



def generate_one_fileset(prefix, count, objects, add_goal):
    # skip existing files
    index = 1
    dirname = os.path.dirname(prefix)
    if dirname != '':
        os.makedirs(dirname, exist_ok=True)

    while count > 0:
        file_exists = True
        while file_exists:
            name = f'{prefix}-{index:04}.json'
            file_exists = os.path.exists(name)
            index += 1

        generate_file(name, objects, add_goal)
        count -= 1


def main(argv):
    parser = argparse.ArgumentParser(description='Create one or more scene descriptions')
    parser.add_argument('--prefix', required=True, help='Prefix for output filenames')
    parser.add_argument('-c', '--count', type=int, default=1, help='How many scenes to generate [default=1]')
    parser.add_argument('--seed', type=int, default=None, help='Random number seed [default=None]')
    parser.add_argument('--objects', required=True, metavar='OBJECTS_FILE', help='File containing a list of objects to choose from')
    parser.add_argument('--goal', action='store_true', default=False, help='Generate a random goal [default is to not generate a goal]')
        
    args = parser.parse_args(argv[1:])

    random.seed(args.seed)

    objects = load_object_file(args.objects)
    generate_one_fileset(args.prefix, args.count, objects, args.goal)

    

if __name__ == '__main__':
    main(sys.argv)
