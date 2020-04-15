#
# Goal generation
#

import copy
import logging
import random
import uuid
from abc import ABC, abstractmethod
from enum import Enum

import geometry
import materials
from geometry import random_position, random_rotation, calc_obj_pos, POSITION_DIGITS
from objects import OBJECTS_PICKUPABLE, OBJECTS_MOVEABLE, OBJECTS_IMMOBILE, OBJECTS_PICKUPABLE_LISTS
from separating_axis_theorem import sat_entry

MAX_TRIES = 20
MAX_OBJECTS = 5
MAX_WALLS = 3
MIN_WALLS = 0
MAX_WALL_WIDTH = 4
MIN_WALL_WIDTH = 1
WALL_Y_POS = 1.25
WALL_HEIGHT = 2.5
WALL_DEPTH = 0.1
WALL_COUNTS = [0,1,2,3]
WALL_PROBS = [60,20,10,10]


def instantiate_object(object_def, object_location):
    """Create a new object from an object definition (as from the objects.json file). object_location will be modified
    by this function."""
    if object_def is None or object_location is None:
        raise ValueError('instantiate_object cannot take None parameters')

    # apply choice if necessary
    if 'choose' in object_def:
        object_def = copy.deepcopy(object_def)
        choice = random.choice(object_def['choose'])
        for key in choice:
            object_def[key] = choice[key]
            
    new_object = {
        'id': str(uuid.uuid4()),
        'type': object_def['type'],
        'info': object_def['info'],
        'mass': object_def['mass']
    }
    for attribute in object_def['attributes']:
        new_object[attribute] = True

    if 'offset' in object_def:
        object_location['position']['x'] -= object_def['offset']['x']
        object_location['position']['z'] -= object_def['offset']['z']

    shows = [object_location]
    new_object['shows'] = shows
    object_location['stepBegin'] = 0
    object_location['scale'] = object_def['scale']
    colors = set()
    if 'materialCategory' in object_def:
        materials_list = [random.choice(getattr(materials, name.upper() + '_MATERIALS')) for name in object_def['materialCategory']]
        new_object['materials'] = [mat[0] for mat in materials_list]
        for material in materials_list:
            for color in material[1]:
                colors.add(color)

    # specific ordering of adjectives for the info list:
    # size weight color(s) material(s) object
    info = object_def['info']
    if 'salientMaterials' in object_def:
        salient_materials = object_def['salientMaterials']
        new_object['salientMaterials'] = salient_materials
        info = info[:1] + salient_materials + info[1:]

    info = info[:1] + list(colors) + info[1:]

    if 'pickupable' in object_def['attributes']:
        size = 'light'
    elif 'moveable' in object_def['attributes']:
        size = 'heavy'
    else:
        size = 'massive'
    info = info[:1] + [size] + info[1:]

    info.append(' '.join(info))
    new_object['info'] = info

    return new_object


def generate_wall(wall_mat_choice, performer_position, other_rects):
    # Wanted to reuse written functions, but this is a bit more of a special snowflake
    # Generates obstacle walls placed in the scene.
    
    tries = 0
    while tries < MAX_TRIES:
        rotation = random_rotation()
        new_x = random_position()
        new_z = random_position()
        new_x_size = round(random.uniform(MIN_WALL_WIDTH, MAX_WALL_WIDTH), POSITION_DIGITS)
        rect = geometry.calc_obj_coords(new_x, new_z, new_x_size, WALL_DEPTH, rotation)
        if not geometry.collision(rect, performer_position) and \
                (len(other_rects) == 0 or not any(sat_entry(rect, other_rect) for other_rect in other_rects)):
            break
        tries += 1

    if tries < MAX_TRIES:
        new_object = {
            'id': 'wall_' + str(uuid.uuid4()),
            'material': wall_mat_choice,
            'type': 'cube',
            'kinematic': 'true',
            'structure': 'true',
            'mass': 100
        }
        shows_object = {}
        shows = [shows_object]
        new_object['shows'] = shows
        
        shows_object['stepBegin'] = 0
        shows_object['scale'] = {'x': new_x_size, 'y': WALL_HEIGHT, 'z' :WALL_DEPTH}
    
        shows_object['rotation'] = { 'x' : 0, 'y': rotation, 'z': 0 }
        shows_object['position'] = { 'x' : new_x, 'y': WALL_Y_POS, 'z' : new_z}
        return new_object
    return None


class GoalException(Exception):
    def __init__(self, message=''):
        super(GoalException, self).__init__(message)


class Goal(ABC):
    """An abstract Goal. Subclasses must implement compute_objects and
    get_config. Users of a goal object should normally only need to call 
    update_body."""

    def __init__(self):
        self._performer_start = None

    def update_body(self, body):
        """Helper method that calls other Goal methods to set performerStart, objects, and goal."""
        body['performerStart'] = self.compute_performer_start()
        goal_objects, all_objects, bounding_rects = self.compute_objects()
        walls = self.generate_walls(body['wallMaterial'], body['performerStart']['position'],
                                    bounding_rects)
        body['objects'] = all_objects + walls
        body['goal'] = self.get_config(goal_objects)
        return body

    def compute_performer_start(self):
        """Compute the starting location (position & rotation) for the performer. Must return the same thing on
        multiple calls. This default implementation chooses a random location."""
        if self._performer_start is None:
            self._performer_start = {
                'position': {
                    'x': random_position(),
                    'y': 0,
                    'z': random_position()
                },
                'rotation': {
                    'y': random_rotation()
                }
            }
        return self._performer_start

    def choose_object_def(self):
        """Pick one object definition (to be added to the scene) and return a copy of it."""
        object_def_list = random.choices([OBJECTS_PICKUPABLE, OBJECTS_MOVEABLE, OBJECTS_IMMOBILE],
                                         [50, 25, 25])[0]
        return copy.deepcopy(random.choice(object_def_list))

    @abstractmethod
    def compute_objects(self):
        """Compute object instances for the scene. Returns a tuple:
        (objects required for the goal, all objects in the scene including objects required for the goal, bounding rectangles)"""
        pass

    def add_objects(self, object_list, rectangles, performer_position):
        """Add random objects to fill object_list to some random number of objects up to MAX_OBJECTS. If object_list
        already has more than this randomly determined number, no new objects are added."""
        object_count = random.randint(1, MAX_OBJECTS)
        for i in range(len(object_list), object_count):
            object_def = self.choose_object_def()
            obj_location = calc_obj_pos(performer_position, rectangles, object_def)
            if obj_location is not None:
                obj = instantiate_object(object_def, obj_location)
                object_list.append(obj)
        


    @abstractmethod
    def get_config(self, goal_objects):
        """Get the goal configuration. goal_objects is the objects required for the goal (as returned from
        compute_objects)."""
        pass

    def generate_walls(self, material, performer_position, bounding_rects):
        wall_count = random.choices(WALL_COUNTS, weights=WALL_PROBS, k=1)[0]

        walls = []
        for x in range(0, wall_count):
            wall = generate_wall(material, performer_position, bounding_rects)
            if wall is not None:
                walls.append(wall)
            else:
                logging.warning('could not generate wall')
        return walls
        
    @staticmethod
    def find_all_valid_objects(constraint_list, objects):
        """Find all members of objects that satisfy all constraints in constraint_list"""
        valid_objects = []
        for obj in objects:
            obj_ok = True
            for constraint in constraint_list:
                if not constraint.is_true(obj):
                    obj_ok = False
                    break
            if obj_ok:
                valid_objects.append(obj)
        return valid_objects


class EmptyGoal(Goal):
    """An empty goal."""

    def __init__(self):
        super(EmptyGoal, self).__init__()

    def compute_objects(self):
        return [], [], []

    def get_config(self, goal_objects):
        return ''


class RetrievalGoal(Goal):
    """Going to a specified object and picking it up."""

    TEMPLATE = {
        'category': 'retrieval',
        'domain_list': ['objects', 'places', 'object_solidity', 'navigation', 'localization'],
        'type_list': ['interaction', 'action_full', 'retrieve'],
        'task_list': ['navigate', 'localize', 'retrieve'],
    }

    def __init__(self):
        super(RetrievalGoal, self).__init__()

    def compute_objects(self):
        # add objects we need for the goal
        pickupable_defs = random.choice(OBJECTS_PICKUPABLE_LISTS)
        target_def = random.choice(pickupable_defs)
        performer_start = self.compute_performer_start()
        performer_position = performer_start['position']
        bounding_rects = []
        target_location = calc_obj_pos(performer_position, bounding_rects, target_def)
        if target_location is None:
            raise GoalException('could not place target object')

        target = instantiate_object(target_def, target_location)

        all_objects = [target]
        self.add_objects(all_objects, bounding_rects, performer_position)

        return [target], all_objects, bounding_rects

    def get_config(self, objects):
        if len(objects) < 1:
            raise ValueError('need at least 1 object for this goal')

        target = objects[0]

        goal = copy.deepcopy(self.TEMPLATE)
        goal['info_list'] = target['info']
        goal['metadata'] = {
            'target': {
                'id': target['id'],
                'info': target['info'],
                'match_image': True
            }
        }
        goal['description'] = f'Find and pick up the {target["info"][-1]}.'
        return goal


class TransferralGoal(Goal):
    """Moving a specified object to another specified object."""

    class RelationshipType(Enum):
        NEXT_TO = 'next to'
        ON_TOP_OF = 'on top of'

    TEMPLATE = {
        'category': 'transferral',
        'domain_list': ['objects', 'places', 'object_solidity', 'navigation', 'localization'],
        'type_list': ['interaction', 'identification', 'objects', 'places'],
        'task_list': ['navigation', 'identification', 'transportation']
    }

    def __init__(self):
        super(TransferralGoal, self).__init__()

    def compute_objects(self):
        performer_start = self.compute_performer_start()
        performer_position = performer_start['position']
        bounding_rects = []

        pickupable_defs = random.choice(OBJECTS_PICKUPABLE_LISTS)
        target1_def = random.choice(pickupable_defs)
        target1_location = calc_obj_pos(performer_position, bounding_rects, target1_def)
        target1 = instantiate_object(target1_def, target1_location)
        
        
        target2_def = self.choose_object_def()
        target2_location = calc_obj_pos(performer_position, bounding_rects, target2_def)
        target2 = instantiate_object(target2_def, target2_location)

        
        goal_objects = [target1, target2]
        all_objects = goal_objects.copy()
        self.add_objects(all_objects, bounding_rects, performer_position)

        return goal_objects, all_objects, bounding_rects

    def get_config(self, objects):
        if len(objects) < 2:
            raise ValueError(f'need at least 2 objects for this goal, was given {len(objects)}')
        target1, target2 = objects
        if not target1.get('pickupable', False):
            raise ValueError(f'first object must be "pickupable": {target1}')
        relationship = random.choice(list(self.RelationshipType))

        goal = copy.deepcopy(self.TEMPLATE)
        both_info = set(target1['info'] + target2['info'])
        goal['info_list'] = list(both_info)
        goal['metadata'] = {
            'target_1': {
                'id': target1['id'],
                'info': target1['info'],
                'match_image': True
            },
            'target_2': {
                'id': target2['id'],
                'info': target2['info'],
                'match_image': True
            },
            'relationship': ['target_1', relationship.value, 'target_2']
        }
        goal['description'] = f'Find and pick up the {target1["info"][-1]} and move it {relationship.value} ' \
                f'the {target2["info"][-1]}.'
        return goal


class TraversalGoal(Goal):
    """Locating and navigating to a specified object."""

    TEMPLATE = {
        'category': 'traversal',
        'domain_list': ['objects', 'places', 'object_solidity', 'navigation', 'localization'],
        'type_list': ['interaction', 'action_full', 'traversal'],
        'task_list': ['navigate', 'localize', 'traversal'],
    }

    def __init__(self):
        super(TraversalGoal, self).__init__()

    def compute_objects(self):
        # add objects we need for the goal
        target_def = self.choose_object_def()
        performer_start = self.compute_performer_start()
        performer_position = performer_start['position']
        bounding_rects = []
        target_location = calc_obj_pos(performer_position, bounding_rects, target_def)
        if target_location is None:
            raise GoalException('could not place target object')

        target = instantiate_object(target_def, target_location)

        all_objects = [target]
        self.add_objects(all_objects, bounding_rects, performer_position)

        return [target], all_objects, bounding_rects

    def get_config(self, objects):
        if len(objects) < 1:
            raise ValueError('need at least 1 object for this goal')

        target = objects[0]

        goal = copy.deepcopy(self.TEMPLATE)
        goal['info_list'] = target['info']
        goal['metadata'] = {
            'target': {
                'id': target['id'],
                'info': target['info'],
                'match_image': True
            }
        }
        goal['description'] = f'Locate the {" ".join(target["info"])} and move near it.'
        return goal


GOAL_TYPES = {
    'interaction': [RetrievalGoal, TransferralGoal, TraversalGoal]
}


def choose_goal(goal_type):
    """Return a random class of 'goal' object from within the specified
overall type, or EmptyGoal if goal_type is None"""
    if goal_type is None:
        return EmptyGoal()
    else:
        return random.choice(GOAL_TYPES[goal_type])()


def get_goal_types():
    return GOAL_TYPES.keys()
