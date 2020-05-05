#
# Function for creating ramps
#

import copy
import random
import uuid

RAMP_30_TEMPLATE = [{
    "id": "ramp_part1_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": 0.451,
            "y": -0.549,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 30
        },
        "scale": {
            "x": 3,
            "y": 3,
            "z": 2.2
        }
    }]
}, {
    "id": "ramp_part2_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": 6,
            "y": 0,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 0
        },
        "scale": {
            "x": 10,
            "y": 3,
            "z": 2.2
        }
    }]
}]

RAMP_45_TEMPLATE = [{
    "id": "ramp_part1_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": -1,
            "y": 0,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 45
        },
        "scale": {
            "x": 2,
            "y": 2,
            "z": 2.2
        }
    }]
}, {
    "id": "ramp_part2_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": 4,
            "y": 0.4142,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 0
        },
        "scale": {
            "x": 10,
            "y": 2,
            "z": 2.2
        }
    }]
}]

RAMP_90_TEMPLATE = [{
    "id": "ramp_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": 3,
            "y": 0.5,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 0
        },
        "scale": {
            "x": 10,
            "y": 2,
            "z": 2.2
        }
    }]
}]

RAMP_30_90_TEMPLATE = [{
    "id": "ramp_part1_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": -0.366,
            "y": 0.384,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 30
        },
        "scale": {
            "x": 2,
            "y": 2,
            "z": 2.2
        }
    }]
}, {
    "id": "ramp_part2_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": 5,
            "y": 1.25,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 0
        },
        "scale": {
            "x": 10,
            "y": 1,
            "z": 2.2
        }
    }]
}, {
    "id": "ramp_part3_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": 3.268,
            "y": 0.25,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 0
        },
        "scale": {
            "x": 10,
            "y": 1,
            "z": 2.2
        }
    }]
}]

RAMP_45_90_TEMPLATE = [{
    "id": "ramp_part1_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": -1,
            "y": 1,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 45
        },
        "scale": {
            "x": 1,
            "y": 1,
            "z": 2.2
        }
    }]
}, {
    "id": "ramp_part2_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": 4,
            "y": 1.2071,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 0
        },
        "scale": {
            "x": 10,
            "y": 1,
            "z": 2.2
        }
    }]
}, {
    "id": "ramp_part3_",
    "type": "cube",
    "materials": [],
    "kinematic": True,
    "structure": True,
    "mass": 100,
    "shows": [{
        "stepBegin": 0,
        "position": {
            "x": 3.2929,
            "y": 0.5,
            "z": 2.1
        },
        "rotation": {
            "x": 0,
            "y": 0,
            "z": 0
        },
        "scale": {
            "x": 10,
            "y": 1,
            "z": 2.2
        }
    }]
}]

RAMP_TEMPLATE_INFO = [(RAMP_30_TEMPLATE, 1), (RAMP_45_TEMPLATE, 3), (RAMP_90_TEMPLATE, 4),
                      (RAMP_30_90_TEMPLATE, 2), (RAMP_45_90_TEMPLATE, 3)]
"""Each type of ramp has a specific amount of variation allowed in
its final X position based on keeping the ramp and some space at the
bottom of the ramp within the camera's viewport.

"""

def create_ramp(material_string, x_position_percent, left_to_right = False):
    """Create a ramp of a random type. Returns a list of objects that make
    up the ramp."""
    if x_position_percent < 0 or x_position_percent > 1:
        raise ValueError(f'x_position_percent must be between 0 and 1 (inclusive), was {x_position_percent}')
    template_info = random.choice(RAMP_TEMPLATE_INFO)
    ramp = []
    x_term = x_position_percent * template_info[1]
    for obj_template in template_info[0]:
        obj = copy.deepcopy(obj_template)
        obj['id'] += str(uuid.uuid4())
        obj['materials'].append(material_string)
        obj['shows'][0]['position']['x'] += x_term
        if left_to_right:
            obj['shows'][0]['position']['x'] *= -1
            obj['shows'][0]['rotation']['z'] *= -1
        ramp.append(obj)
    return ramp
