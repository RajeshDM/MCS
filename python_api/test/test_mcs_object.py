import unittest
import textwrap

from machine_common_sense.mcs_object import MCS_Object
from machine_common_sense.mcs_material import MCS_Material


class Test_Default_MCS_Object(unittest.TestCase):

    str_output = '''    {
        "uuid": "",
        "color": {},
        "direction": {},
        "distance": -1.0,
        "held": False,
        "mass": 0.0,
        "material_list": [],
        "position": {},
        "rotation": 0.0,
        "visible": False
    }'''

    @classmethod
    def setUpClass(cls):
        cls.mcs_object = MCS_Object()

    @classmethod
    def tearDownClass(cls):
        # nothing to do
        pass

    def test_uuid(self):
        self.assertEqual(self.mcs_object.uuid, "")
        self.assertIsInstance(self.mcs_object.uuid, str)

    def test_color(self):
        self.assertFalse(self.mcs_object.color)
        self.assertIsInstance(self.mcs_object.color, dict)
        
    def test_direction(self):
        self.assertFalse(self.mcs_object.direction)
        self.assertIsInstance(self.mcs_object.direction, dict)

    def test_distance(self):
        self.assertAlmostEqual(self.mcs_object.distance, -1.0)
        self.assertIsInstance(self.mcs_object.distance, float)

    def test_held(self):
        self.assertFalse(self.mcs_object.held)
        self.assertIsInstance(self.mcs_object.held, bool)

    def test_mass(self):
        self.assertAlmostEqual(self.mcs_object.mass, 0.0)
        self.assertIsInstance(self.mcs_object.mass, float)

    def test_material_list(self):
        self.assertFalse(self.mcs_object.material_list)
        self.assertIsInstance(self.mcs_object.material_list, list)

    def test_position(self):
        self.assertFalse(self.mcs_object.position)
        self.assertIsInstance(self.mcs_object.position, dict)

    def test_rotation(self):
        self.assertAlmostEqual(self.mcs_object.rotation, 0.0)
        self.assertIsInstance(self.mcs_object.rotation, float)

    def test_visible(self):
        self.assertIsInstance(self.mcs_object.visible, bool)
        self.assertFalse(self.mcs_object.visible)

    def test_str(self):
        self.assertEqual(str(self.mcs_object), textwrap.dedent(self.str_output))
