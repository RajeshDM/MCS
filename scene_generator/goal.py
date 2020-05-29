import logging
import uuid
from abc import ABC, abstractmethod
import random
from typing import Dict, Any, Tuple, List, Optional

import geometry
import objects
import separating_axis_theorem
import util

MAX_TRIES = 20
MAX_WALL_WIDTH = 4
MIN_WALL_WIDTH = 1
WALL_Y_POS = 1.5
WALL_HEIGHT = 3
WALL_DEPTH = 0.1
MAX_OBJECTS = 5
MIN_RANDOM_INTERVAL = 0.05
WALL_COUNTS = [0, 1, 2, 3]
WALL_PROBS = [60, 20, 10, 10]


def generate_wall(wall_mat_choice: str, performer_position: Dict[str, float],
                  other_rects: List[List[Dict[str, float]]]) -> Optional[Dict[str, Any]]:
    # Wanted to reuse written functions, but this is a bit more of a special snowflake
    # Generates obstacle walls placed in the scene.

    tries = 0
    while tries < MAX_TRIES:
        rotation = random.choice((0, 90, 180, 270))
        new_x = geometry.random_position()
        new_z = geometry.random_position()
        new_x_size = round(random.uniform(MIN_WALL_WIDTH, MAX_WALL_WIDTH), geometry.POSITION_DIGITS)
        rect = geometry.calc_obj_coords(new_x, new_z, new_x_size, WALL_DEPTH, 0, 0, rotation)
        if not geometry.collision(rect, performer_position) and \
                all(geometry.point_within_room(point) for point in rect) and \
                (len(other_rects) == 0 or not any(
                    separating_axis_theorem.sat_entry(rect, other_rect) for other_rect in other_rects)):
            break
        tries += 1

    if tries < MAX_TRIES:
        new_object = {
            'id': 'wall_' + str(uuid.uuid4()),
            'materials': [wall_mat_choice],
            'type': 'cube',
            'kinematic': 'true',
            'structure': 'true',
            'mass': 100
        }
        shows_object = {
            'stepBegin': 0,
            'scale': {'x': new_x_size, 'y': WALL_HEIGHT, 'z': WALL_DEPTH},
            'rotation': {'x': 0, 'y': rotation, 'z': 0},
            'position': {'x': new_x, 'y': WALL_Y_POS, 'z': new_z},
            'bounding_box': rect
        }
        shows = [shows_object]
        new_object['shows'] = shows

        return new_object
    return None


class Goal(ABC):
    """An abstract Goal. Subclasses must implement compute_objects and
    get_config. Users of a goal object should normally only need to call 
    update_body."""

    def __init__(self):
        self._performer_start = None
        self._targets = []
        self._goal_objects = []

    def update_body(self, body: Dict[str, Any], find_path: bool) -> Dict[str, Any]:
        """Helper method that calls other Goal methods to set performerStart, objects, and goal. Returns the goal body
        object."""
        body['performerStart'] = self.compute_performer_start()
        goal_objects, all_objects, bounding_rects = self.compute_objects(body['wallMaterial'])
        self._goal_objects = goal_objects
        walls = self.generate_walls(body['wallMaterial'], body['performerStart']['position'],
                                    bounding_rects)
        body['objects'] = all_objects + walls
        body['goal'] = self.get_config(goal_objects, all_objects + walls)
        if find_path:
            body['answer']['actions'] = self.find_optimal_path(goal_objects, all_objects + walls)

        return body

    def compute_performer_start(self) -> Dict[str, Dict[str, float]]:
        """Compute the starting location (position & rotation) for the performer. Must return the same thing on
        multiple calls. This default implementation chooses a random location."""
        if self._performer_start is None:
            self._performer_start = {
                'position': {
                    'x': geometry.random_position(),
                    'y': 0,
                    'z': geometry.random_position()
                },
                'rotation': {
                    'y': geometry.random_rotation()
                }
            }
        return self._performer_start

    def choose_object_def(self) -> Dict[str, Any]:
        """Pick one object definition (to be added to the scene) and return a copy of it."""
        object_def_list = random.choices([objects.OBJECTS_PICKUPABLE, objects.OBJECTS_MOVEABLE,
                                          objects.OBJECTS_IMMOBILE],
                                         [50, 25, 25])[0]
        return util.finalize_object_definition(random.choice(object_def_list))

    @abstractmethod
    def compute_objects(self, wall_material_name: str) \
        -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[List[Dict[str, float]]]]:
        """Compute object instances for the scene. Returns a tuple:
        (objects required for the goal, all objects in the scene including objects required for the goal, bounding rectangles)"""
        pass

    def add_objects(self, object_list: List[Dict[str, Any]], rectangles: List[List[Dict[str, float]]],
                    performer_position: Dict[str, float]) -> None:
        """Add random objects to fill object_list to some random number of objects up to MAX_OBJECTS. If object_list
        already has more than this randomly determined number, no new objects are added."""
        object_count = random.randint(1, MAX_OBJECTS)
        for i in range(len(object_list), object_count):
            object_def = self.choose_object_def()
            obj_location = geometry.calc_obj_pos(performer_position, rectangles, object_def)
            obj_info = object_def['info'][-1]
            targets_info = [tgt['info'][-1] for tgt in self._targets]
            if obj_info not in targets_info and obj_location is not None:
                obj = util.instantiate_object(object_def, obj_location)
                object_list.append(obj)

    def _update_goal_info_list(self, goal: Dict[str, Any], all_objects: List[Dict[str, Any]]):
        info_set = set(goal.get('info_list', []))
        for obj in all_objects:
            info_set |= frozenset(obj.get('info', []))
        goal['info_list'] = list(info_set)

    def get_config(self, goal_objects: List[Dict[str, Any]], all_objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get the goal configuration. goal_objects is the objects required for the goal (as returned from
        compute_objects)."""
        pass

    def generate_walls(self, material: str, performer_position: Dict[str, Any],
                       bounding_rects: List[List[Dict[str, float]]]) -> List[Dict[str, Any]]:
        wall_count = random.choices(WALL_COUNTS, weights=WALL_PROBS, k=1)[0]

        walls = []
        for x in range(0, wall_count):
            wall = generate_wall(material, performer_position, bounding_rects)
            if wall is not None:
                walls.append(wall)
            else:
                logging.warning('could not generate wall')
        return walls

    @abstractmethod
    def find_optimal_path(self, goal_objects: List[Dict[str, Any]], all_objects: List[Dict[str, Any]]) -> \
            List[Dict[str, Any]]:
        """Compute the optimal set of moves and update the body object"""
        pass


class EmptyGoal(Goal):
    """An empty goal."""

    def __init__(self):
        super(EmptyGoal, self).__init__()

    def compute_objects(self, wall_material_name: str) \
        -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[List[Dict[str, float]]]]:
        return [], [], []

    def get_config(self, goal_objects: List[Dict[str, Any]], all_objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {}

    def find_optimal_path(self, goal_objects: List[Dict[str, Any]], all_objects: List[Dict[str, Any]]) -> \
            List[Dict[str, Any]]:
        return []


class GoalException(Exception):
    def __init__(self, message=''):
        super(GoalException, self).__init__(message)
