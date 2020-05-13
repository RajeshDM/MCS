from geometry import ORIGIN
from goals import *
import pytest
import uuid
import math

from geometry import POSITION_DIGITS
from machine_common_sense.mcs_controller_ai2thor import MAX_MOVE_DISTANCE

def test_random_real():
    n = random_real(0, 1, 0.1)
    assert 0 <= n <= 1
    # need to multiply by 10 and mod by 1 instead of 0.1 to avoid weird roundoff
    assert n * 10 % 1 < 1e-8


def test_instantiate_object():
    object_def = {
        'type': str(uuid.uuid4()),
        'info': [str(uuid.uuid4()), str(uuid.uuid4())],
        'mass': random.random(),
        'attributes': ['foo', 'bar'],
        'scale': 1.0
    }
    object_location = {
        'position': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        },
        'rotation': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        }
    }
    obj = instantiate_object(object_def, object_location)
    assert type(obj['id']) is str
    for prop in ('type', 'mass'):
        assert object_def[prop] == obj[prop]
    for attribute in object_def['attributes']:
        assert obj[attribute] is True
    assert obj['shows'][0]['position'] == object_location['position']
    assert obj['shows'][0]['rotation'] == object_location['rotation']


def test_instantiate_object_offset():
    offset = {
        'x': random.random(),
        'z': random.random()
    }
    object_def = {
        'type': str(uuid.uuid4()),
        'info': [str(uuid.uuid4()), str(uuid.uuid4())],
        'mass': random.random(),
        'scale': 1.0,
        'attributes': [],
        'offset': offset
    }
    x = random.random()
    z = random.random()
    object_location = {
        'position': {
            'x': x,
            'y': 0.0,
            'z': z
        },
        'rotation': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        }
    }
    obj = instantiate_object(object_def, object_location)
    position = obj['shows'][0]['position']
    assert position['x'] == x - offset['x']
    assert position['z'] == z - offset['z']


def test_instantiate_object_materials():
    material_category = ['plastic']
    materials_list = materials.PLASTIC_MATERIALS
    object_def = {
        'type': str(uuid.uuid4()),
        'info': [str(uuid.uuid4()), str(uuid.uuid4())],
        'mass': random.random(),
        'scale': 1.0,
        'attributes': [],
        'materialCategory': material_category
    }
    object_location = {
        'position': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        },
        'rotation': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        }
    }
    obj = instantiate_object(object_def, object_location)
    assert obj['materials'][0] in (mat[0] for mat in materials_list)


def test_instantiate_object_salient_materials():
    salient_materials = ["plastic", "hollow"]
    object_def = {
        'type': str(uuid.uuid4()),
        'info': [str(uuid.uuid4()), str(uuid.uuid4())],
        'mass': random.random(),
        'scale': 1.0,
        'attributes': [],
        'salientMaterials': salient_materials
    }
    object_location = {
        'position': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        },
        'rotation': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        }
    }
    obj = instantiate_object(object_def, object_location)
    assert obj['salientMaterials'] == salient_materials
    for sm in salient_materials:
        assert sm in obj['info']


def test_instantiate_object_size():
    object_def = {
        'type': str(uuid.uuid4()),
        'info': [str(uuid.uuid4()), str(uuid.uuid4())],
        'mass': random.random(),
        'scale': 1.0,
        'attributes': [],
    }
    object_location = {
        'position': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        },
        'rotation': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        }
    }
    size_mapping = {
        'pickupable': 'light',
        'moveable': 'heavy',
        'anythingelse': 'massive'
    }
    for attribute in size_mapping:
        size = size_mapping[attribute]
        object_def['attributes'] = [attribute]
        obj = instantiate_object(object_def, object_location)
        assert size in obj['info']


def test_finalize_object_definition():
    object_type = 'type1'
    mass = 12.34
    material_category = ['plastic']
    salient_materials = ['plastic', 'hollow']
    object_def = {
        'type': 'type2',
        'mass': 56.78,
        'choose': [{
            'type': object_type,
            'mass': mass,
            'materialCategory': material_category,
            'salientMaterials': salient_materials
        }]
    }
    obj = finalize_object_definition(object_def)
    assert obj['type'] == object_type
    assert obj['mass'] == mass
    assert obj['materialCategory'] == material_category
    assert obj['salientMaterials'] == salient_materials


def test_move_to_container():
    # find a tiny object so we know it will fit in *something*
    for obj_def in objects.OBJECTS_PICKUPABLE:
        obj_def = finalize_object_definition(obj_def)
        if 'tiny' in obj_def['info']:
            obj = instantiate_object(obj_def, geometry.ORIGIN_LOCATION)
            all_objects = [obj]
            tries = 0
            while tries < 100:
                if move_to_container(obj, all_objects, [], geometry.ORIGIN):
                    break
                tries += 1
            if tries == 100:
                logging.error('could not put the object in any container')
            container_id = all_objects[1]['id']
            assert obj['locationParent'] == container_id
            return
    assert False, 'could not find a tiny object'


def test_RetrievalGoal_get_goal():
    goal_obj = RetrievalGoal()
    obj = {
        'id': str(uuid.uuid4()),
        'info': [str(uuid.uuid4())],
        'type': 'sphere'
    }
    object_list = [obj]
    goal = goal_obj.get_config(object_list, object_list)
    assert goal['info_list'] == obj['info']
    target = goal['metadata']['target']
    assert target['id'] == obj['id']
    assert target['info'] == obj['info']


def test_Goal_duplicate_object():
    goal_obj = RetrievalGoal()
    obj = {
        'id': str(uuid.uuid4()),
        'info': [str(uuid.uuid4())],
        'type': 'sphere',
        "choose": [{
            "mass": 0.25,
            "materialCategory": ["plastic"],
            "salientMaterials": ["plastic", "hollow"]
        }, {
            "mass": 0.5625,
            "materialCategory": ["rubber"],
            "salientMaterials": ["rubber"]
        }, {
            "mass": 0.5625,
            "materialCategory": ["block_blank"],
            "salientMaterials": ["wood"]
        }, {
            "mass": 0.5625,
            "materialCategory": ["wood"],
            "salientMaterials": ["wood"]
        }, {
            "mass": 1,
            "materialCategory": ["metal"],
            "salientMaterials": ["metal"]
        }],
        "attributes": ["moveable", "pickupable"],
        "dimensions": {
            "x": 0.1,
            "y": 0.1,
            "z": 0.1
        },
        "position_y": 0.05,
        "scale": {
            "x": 0.1,
            "y": 0.1,
            "z": 0.1
        }
    }
    object_location = {
        'position': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        },
        'rotation': {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0
        }
    }
    sphere = instantiate_object(obj, object_location)
    object_list = [sphere]
    bounding_rect = [[{'x': 3.7346446609406727, 'y': 0, 'z': 4.23}, {'x': 3.77, 'y': 0, 'z': 4.265355339059328}, {'x': 3.8053553390593273, 'y': 0, 'z': 4.23}, {'x': 3.77, 'y': 0, 'z': 4.194644660940673}], [{'x': 3.846, 'y': 0, 'z': -1.9685000000000001}, {'x': 3.846, 'y': 0, 'z': -2.4715000000000003}, {'x': 3.1340000000000003, 'y': 0, 'z': -2.4715000000000003}, {'x': 3.1340000000000003, 'y': 0, 'z': -1.9685000000000001}]]
    performer_position = {'x': 0.77, 'y': 0, 'z': -0.41}
    goal = goal_obj.get_config(object_list, object_list)
    empty = goal_obj.add_objects(object_list, bounding_rect, performer_position)
    assert empty is None


def test_parse_path_section():
    path_section = ((0, 0), (0.1, 0.1))
    expected_actions = [{
        'action': 'RotateLook',
        'params': {
            'rotation': -45.0,
            'horizon': 0.0
        }
    }, {
        'action': 'MoveAhead',
        'params': {
            'amount': round(math.sqrt(2 * 0.1**2) / MAX_MOVE_DISTANCE, POSITION_DIGITS)
        }
    }]
    actions, new_heading = parse_path_section(path_section, 0)
    assert actions == expected_actions


def test_get_navigation_action():
    expected_actions = [{
        'action': 'RotateLook',
        'params': {
            'rotation': -45.0,
            'horizon': 0.0
        }
    }, {
        'action': 'MoveAhead',
        'params': {
            'amount': round(math.sqrt(2 * 0.1**2) / MAX_MOVE_DISTANCE, POSITION_DIGITS)
        }
    }]
    start = {
        'position': {
            'x': 0,
            'y': 0,
            'z': 0
        },
        'rotation': {
            'y': 0
        }
    }
    goal_object = {
        'shows': [{
            'position': {
                'x': 0.1,
                'y': 0,
                'z': 0.1
            }
        }]
    }
    actions = get_navigation_actions(start, goal_object, [])
    assert actions == expected_actions
    
    
def test_get_navigation_action_with_locationParent():
    expected_actions = [{
        'action': 'RotateLook',
        'params': {
            'rotation': -45.0,
            'horizon': 0.0
        }
    }, {
        'action': 'MoveAhead',
        'params': {
            'amount': round(math.sqrt(2 * 0.1**2) / MAX_MOVE_DISTANCE, POSITION_DIGITS)
        }
    }]
    start = {
        'position': {
            'x': 0,
            'y': 0,
            'z': 0
        },
        'rotation': {
            'y': 0
        }
    }
    container_object = {
        'id': 'container1',
        'shows': [{
            'position': {
                'x': 0.1,
                'y': 0,
                'z': 0.1
            }
        }]
    }
    goal_object = {
        'id': 'object1',
        'locationParent': 'container1',
        'shows': [{
            'position': {
                'x': -0.1,
                'y': 0,
                'z': 0
            }
        }]
    }
    actions = get_navigation_actions(start, goal_object, [container_object, goal_object])
    assert actions == expected_actions
    
    
def test_TraversalGoal_get_goal():
    goal_obj = TraversalGoal()
    obj = {
        'id': str(uuid.uuid4()),
        'info': [str(uuid.uuid4())],
        'type': 'sphere'
    }
    object_list = [obj]
    goal = goal_obj.get_config(object_list, object_list)
    assert goal['info_list'] == obj['info']
    target = goal['metadata']['target']
    assert target['id'] == obj['id']
    assert target['info'] == obj['info']


def test_TransferralGoal_get_goal_argcount():
    goal_obj = TransferralGoal()
    with pytest.raises(ValueError):
        goal_obj.get_config(['one object'], ['one object'])


def test_TransferralGoal_get_goal_argvalid():
    goal_obj = TransferralGoal()
    with pytest.raises(ValueError):
        goal_obj.get_config([{'attributes': ['']}, {'attributes': ['']}], [])


def test__generate_transferral_goal():
    goal_obj = TransferralGoal()
    extra_info = str(uuid.uuid4())
    pickupable_id = str(uuid.uuid4())
    pickupable_info_item = str(uuid.uuid4())
    pickupable_obj = {
        'id': pickupable_id,
        'info': [pickupable_info_item, extra_info],
        'pickupable': True,
        'type': 'sphere'
    }
    other_id = str(uuid.uuid4())
    other_info_item = str(uuid.uuid4())
    other_obj = {
        'id': other_id,
        'info': [other_info_item, extra_info],
        'attributes': [],
        'type': 'changing_table',
        'stackTarget': True
    }
    obj_list = [pickupable_obj, other_obj]
    goal = goal_obj.get_config(obj_list, obj_list)

    combined_info = goal['info_list']
    assert set(combined_info) == {pickupable_info_item, other_info_item, extra_info}

    target1 = goal['metadata']['target_1']
    assert target1['id'] == pickupable_id
    assert target1['info'] == [pickupable_info_item, extra_info]
    target2 = goal['metadata']['target_2']
    assert target2['id'] == other_id
    assert target2['info'] == [other_info_item, extra_info]

    relationship = goal['metadata']['relationship']
    relationship_type = relationship[1]
    assert relationship_type in [g.value for g in TransferralGoal.RelationshipType]


def test__generate_transferral_goal_with_nonstackable_goal():
    goal_obj = TransferralGoal()
    extra_info = str(uuid.uuid4())
    pickupable_id = str(uuid.uuid4())
    pickupable_info_item = str(uuid.uuid4())
    pickupable_obj = {
        'id': pickupable_id,
        'info': [pickupable_info_item, extra_info],
        'pickupable': True,
        'type': 'sphere',
        'attributes': ['pickupable']
    }
    other_id = str(uuid.uuid4())
    other_info_item = str(uuid.uuid4())
    other_obj = {
        'id': other_id,
        'info': [other_info_item, extra_info],
        'type': 'changing_table',
        'attributes': []
    }
    with pytest.raises(ValueError) as excinfo:
        goal = goal_obj.get_config([pickupable_obj, other_obj], [])
    assert "second object must be" in str(excinfo.value)


def test_GravityGoal_compute_objects():
    goal = GravityGoal()
    target_objs, all_objs, rects = goal.compute_objects('dummy wall material')
    assert len(target_objs) == 0
    assert len(rects) == 0
    # TODO: in a future ticket when all_objs has stuff


# test for MCS-214
def test_GravityGoal__get_ramp_and_objects():
    goal = GravityGoal()
    object_list = goal._get_ramp_and_objects('dummy')
    assert len(object_list) > 0
    for obj in object_list:
        if 'intphys_option' in obj:
            assert obj['intphys_option']['y'] == 0


def test_IntPhysGoal__get_objects_and_occluders_moving_across():
    class TestGoal(IntPhysGoal):
        pass

    goal = TestGoal()
    wall_material = random.choice(materials.CEILING_AND_WALL_MATERIALS)[0]
    objs, occluders = goal._get_objects_and_occluders_moving_across(wall_material)
    assert 1 <= len(objs) <= 3
    assert 1 <= len(occluders) <= 4 * 2  # each occluder is actually 2 objects
    # the first occluder should be at one of the positions for the first object
    occluder_x = occluders[0]['shows'][0]['position']['x']
    first_obj = objs[0]
    found = False
    multiplier = 0.9 if first_obj['shows'][0]['position']['z'] == 1.6 else 0.8
    for position in first_obj['intphys_option']['position_by_step']:
        adjusted_x = position * multiplier
        if adjusted_x == occluder_x:
            found = True
            break
    assert found
    for o in occluders:
        assert o['materials'] != wall_material


def test_IntPhysGoal__get_objects_moving_across_collisions():
    class TestGoal(IntPhysGoal):
        pass

    goal = TestGoal()
    wall_material = random.choice(materials.CEILING_AND_WALL_MATERIALS)[0]
    objs = goal._get_objects_moving_across(wall_material, 55)
    for obj in objs:
        x = obj['shows'][0]['position']['x']
        z = obj['shows'][0]['position']['z']
        # check for possible collision with all other objects
        for other in (o for o in objs if o != obj):
            other_x = other['shows'][0]['position']['x']
            other_z = other['shows'][0]['position']['z']
            # could other catch up to obj?
            if other_z == z and abs(other_x) > abs(x):
                obj_a = obj['intphys_option']['force']['x'] / obj['mass']
                other_a = other['intphys_option']['force']['x'] / obj['mass']
                assert abs(other_a) <= abs(obj_a)

    
def test_IntPhysGoal__compute_scenery():
    goal = GravityGoal()
    # There's a good chance of no scenery, so keep trying until we get
    # some.
    scenery_generated = False
    while not scenery_generated:
        scenery_list = goal._compute_scenery()
        assert 0 <= len(scenery_list) <= 5
        scenery_generated = len(scenery_list) > 0
        for scenery in scenery_list:
            for point in scenery['shows'][0]['bounding_box']:
                assert -6.5 <= point['x'] <= 6.5
                assert 3.25 <= point['z'] <= 4.95


def test__object_collision():
    r1 = geometry.calc_obj_coords(-1.97, 1.75, .55, .445, -.01, .445, 315)
    r2 = geometry.calc_obj_coords(-3.04, .85, 1.75, .05, 0, 0, 315)
    assert sat_entry(r1, r2)
    r3 = geometry.calc_obj_coords(.04, .85, 1.75, .05, 0, 0, 315)
    assert not sat_entry(r1, r3)


def test__get_objects_falling_down():
    class TestGoal(IntPhysGoal):
        pass

    goal = TestGoal()
    wall_material = random.choice(materials.CEILING_AND_WALL_MATERIALS)[0]
    obj_list, occluders = goal._get_objects_falling_down(wall_material)
    assert 1 <= len(obj_list) <= 2
    assert len(obj_list)*2 <= len(occluders) <= 4
    for obj in obj_list:
        assert -2.5 <= obj['shows'][0]['position']['x'] <= 2.5
        assert obj['shows'][0]['position']['y'] == 3.8
        z = obj['shows'][0]['position']['z']
        assert z == 1.6 or z == 2.7
        assert 13 <= obj['shows'][0]['stepBegin'] <= 20


def test_mcs_209():
    obj_defs = OBJECTS_INTPHYS.copy()
    random.shuffle(obj_defs)
    obj_def = next((od for od in obj_defs if 'rotation' in od))
    obj = instantiate_object(obj_def, {'position': ORIGIN})
    assert obj['shows'][0]['rotation'] == obj_def['rotation']

    class TestGoal(IntPhysGoal):
        TEMPLATE = {'type_list': []}
        pass

    goal = TestGoal()
    objs = goal._get_objects_moving_across('dummy', 55)
    for obj in objs:
        assert obj['shows'][0]['stepBegin'] == obj['forces'][0]['stepBegin']

    body = {'wallMaterial': 'dummy'}
    goal._scenery_count = 0
    goal.update_body(body, False)
