from unittest import TestCase

import numpy as np

from fr3d.data import Atom
from fr3d.data.base import AtomProxy


class AtomProxyTest(TestCase):
    def setUp(self):
        self.atoms = [
            Atom(type='C', name='a1', component_number=3,
                 x=1.0, y=0.0, z=0.0),
            Atom(type='C', name='a2', component_number=2,
                 x=2.0, y=0.0, z=0.0),
            Atom(type='N', name='b1', component_number=1,
                 x=3.0, y=0.0, z=0.0),
            Atom(type='N', name='c2', component_number=0,
                 x=0.0, y=1.0, z=0.0)
        ]
        self.proxy = AtomProxy(self.atoms)

    def test_can_set_a_value(self):
        ans = 10
        self.proxy['bob'] = ans
        val = self.proxy['bob']
        self.assertEqual(val, ans)

    def test_can_get_atom_value(self):
        ans = np.array([0.0, 1.0, 0.0])
        val = self.proxy['c2']
        np.testing.assert_almost_equal(ans, val)

    def test_knows_is_missing_a_value(self):
        self.assertFalse('bob' in self.proxy)

    def test_can_test_has_value(self):
        self.proxy['bob'] = 1
        self.assertTrue('bob' in self.proxy)

    def test_knows_has_atom(self):
        self.assertTrue('a1' in self.proxy)

    def test_lets_override_proxy_lookup(self):
        ans = 'a'
        self.proxy['a1'] = ans
        val = self.proxy['a1']
        self.assertEqual(val, ans)

    def test_length_counts_atoms(self):
        self.proxy['steve'] = 3
        ans = 5
        val = len(self.proxy)
        self.assertEqual(val, ans)

    def test_can_find_new_atom_positions(self):
        self.atoms.append(Atom(name='s', x=3.0, y=2.0, z=1.0))
        val = self.proxy['s']
        ans = np.array([3.0, 2.0, 1.0])
        np.testing.assert_almost_equal(ans, val)

    def test_fails_if_given_several_with_missing_name(self):
        self.assertRaises(KeyError, lambda: self.proxy['a1', 'c1'])

    def test_can_get_average_of_several_atoms(self):
        val = self.proxy['a1', 'c2']
        ans = np.array([0.5, 0.5, 0.0])
        np.testing.assert_array_almost_equal(ans, val, decimal=3)

    def test_can_get_average_from_list_of_atoms(self):
        atoms = ['a1', 'c2']
        val = self.proxy[atoms]
        ans = np.array([0.5, 0.5, 0.0])
        np.testing.assert_array_almost_equal(ans, val, decimal=3)

    def test_can_get_average_from_set_of_atoms(self):
        atoms = set(['a1', 'c2'])
        val = self.proxy[atoms]
        ans = np.array([0.5, 0.5, 0.0])
        np.testing.assert_array_almost_equal(ans, val, decimal=3)

    def test_can_define_a_center_for_later_use(self):
        self.proxy.define('bob', ['a1', 'c2'])
        ans = np.array([0.5, 0.5, 0.0])
        val = self.proxy['bob']
        np.testing.assert_array_almost_equal(ans, val, decimal=3)

    def test_can_lookup_with_missing_values(self):
        val = self.proxy.lookup(['a1', 'c2', '3'], allow_missing=True)
        ans = np.array([0.5, 0.5, 0.0])
        np.testing.assert_array_almost_equal(ans, val, decimal=3)

    def test_lookup_unknown_atoms_gives_empty(self):
        val = self.proxy.lookup(['3'], allow_missing=True)
        self.assertEquals([], val)

    def test_lookup_of_unknown_key_gives_empty(self):
        val = self.proxy.lookup('3', allow_missing=True)
        self.assertEquals([], val)

    def test_lookup_defaults_to_allow_missing(self):
        val = self.proxy.lookup(['a1', 'c2', '3'])
        ans = np.array([0.5, 0.5, 0.0])
        np.testing.assert_array_almost_equal(ans, val, decimal=3)
