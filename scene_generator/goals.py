#
# Goal generation
#

import copy
import random
import uuid
from abc import ABC, abstractmethod
from enum import Enum

from geometry import random_position, random_rotation, calc_obj_pos

MAX_OBJECTS = 5


def instantiate_object(object_def, object_location):
    new_object = {
        'id': str(uuid.uuid4()),
        'type': object_def['type'],
        'info': object_def['info'],
        'mass': object_def['mass']
    }
    for attribute in object_def['attributes']:
        new_object[attribute] = True

    shows = [object_location]
    new_object['shows'] = shows
    object_location['stepBegin'] = 0
    object_location['scale'] = object_def['scale']
    if 'salientMaterials' in object_def:
        salientMaterialsIndex = object_def['salientMaterials'][0].upper() + '_MATERIALS'
        salientMaterial = random.choice(globals().get(salientMaterialsIndex, None))
        new_object['material'] = salientMaterial
        new_object['info'].append(object_def['salientMaterials'][0])
        new_object['salientMaterials'] = object_def['salientMaterials']
    return new_object


def add_objects(object_defs, object_list, rectangles, performer_position):
    """Add random objects to fill object_list to some random number of objects up to MAX_OBJECTS. If object_list
    already has more than this randomly determined number, no new objects are added."""
    object_count = random.randint(1, MAX_OBJECTS)
    for i in range(len(object_list), object_count):
        object_def = copy.deepcopy(random.choice(object_defs))
        obj_location = calc_obj_pos(performer_position, rectangles, object_def)
        if obj_location is not None:
            obj = instantiate_object(object_def, obj_location)
            object_list.append(obj)


class AttributeConstraint:
    """True iff the object has attribute and predicate is true when applied to the attribute and the arguments."""

    def __init__(self, predicate, attribute, *arguments):
        self.predicate = predicate
        self.attribute = attribute
        self.arguments = arguments

    def is_true(self, obj):
        return self.attribute in obj and self.predicate(obj[self.attribute], *self.arguments)


class GoalException(Exception):
    def __init__(self, message=''):
        super(GoalException, self).__init__(message)


class Goal(ABC):
    """An abstract Goal."""

    def __init__(self):
        self._performer_start = None

    def update_body(self, object_defs, body):
        body['performerStart'] = self.compute_performer_start()
        goal_objects, all_objects = self.compute_objects(object_defs)
        body['objects'] = all_objects
        body['goal'] = self.get_config(goal_objects)
        return body

    def compute_performer_start(self):
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

    @abstractmethod
    def compute_objects(self, object_defs):
        pass

    @abstractmethod
    def get_config(self, goal_objects):
        pass

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


class NullGoal(Goal):
    def __init__(self):
        super(NullGoal, self).__init__()

    def compute_objects(self, object_defs):
        return []

    def get_config(self, goal_objects):
        return ''


class RetrievalGoal(Goal):
    TEMPLATE = {
        'category': 'retrieval',
        'domain_list': ['objects', 'places', 'object_solidity', 'navigation', 'localization'],
        'type_list': ['interaction', 'action_full', 'retrieve'],
        'task_list': ['navigate', 'localize', 'retrieve'],
    }

    def __init__(self):
        super(RetrievalGoal, self).__init__()

    def compute_objects(self, object_defs):
        # add objects we need for the goal
        target_def = copy.deepcopy(random.choice(object_defs))
        performer_start = self.compute_performer_start()
        performer_position = performer_start['position']
        bounding_rects = []
        target_location = calc_obj_pos(performer_position, bounding_rects, target_def)
        if target_location is None:
            raise GoalException('could not place target object')

        target = instantiate_object(target_def, target_location)

        all_objects = [target]
        add_objects(object_defs, all_objects, bounding_rects, performer_position)

        return [target], all_objects

    def get_config(self, objects):
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
        goal['description'] = f'Find and pick up the {" ".join(target["info"])}.'
        return goal


class TransferralGoal(Goal):
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

    def get_object_constraint_lists(self):
        return [[AttributeConstraint(list.__contains__, 'attributes', 'pickupable')], []]

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
        goal[
            'description'] = f'Find and pick up the {" ".join(target1["info"])} and move it {relationship.value} the {" ".join(target2["info"])}.'
        return goal


GOAL_TYPES = {
    'interaction': [RetrievalGoal, TransferralGoal]
}


def choose_goal(goal_type):
    """Return a random class of 'goal' object from within the specified
overall type, or NullGoal if goal_type is None"""
    if goal_type is None:
        return NullGoal()
    else:
        return RetrievalGoal()
#        return random.choice(GOAL_TYPES[goal_type])()


def get_goal_types():
    return GOAL_TYPES.keys()