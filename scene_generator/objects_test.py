from objects import *
import uuid
import random

def test_create_occluder_normal():
    wall_material = str(uuid.uuid4())
    pole_material = str(uuid.uuid4())
    x_position = random.uniform(-1, 1)
    x_scale = random.uniform(0.1, 2)

    occluder = create_occluder(wall_material, pole_material, x_position, x_scale)
    assert len(occluder) == 2
    wall, pole = occluder
    # make sure we got them back in the right order
    assert wall['type'] == 'cube'
    assert pole['type'] == 'cylinder'
    assert wall['material'] == wall_material
    assert pole['material'] == pole_material
    for x in wall, pole:
        assert x['shows'][0]['position']['x'] == x_position
    
def test_create_occluder_sideways():
    wall_material = str(uuid.uuid4())
    pole_material = str(uuid.uuid4())
    x_position = random.uniform(-1, 1)
    x_scale = random.uniform(0.1, 2)

    occluder = create_occluder(wall_material, pole_material, x_position, x_scale, True)
    assert len(occluder) == 2
    wall, pole = occluder
    # make sure we got them back in the right order
    assert wall['type'] == 'cube'
    assert pole['type'] == 'cylinder'
    assert wall['material'] == wall_material
    assert pole['material'] == pole_material
    