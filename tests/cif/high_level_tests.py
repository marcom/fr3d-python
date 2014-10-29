from tests.cif import ReaderTest


class StructureTest(ReaderTest):
    name = '1GID'

    def test_assigns_pdb_id(self):
        val = self.structure.pdb
        ans = '1GID'
        self.assertEqual(ans, val)

    def test_loads_all_models(self):
        val = len(self.structure.models)
        ans = 1
        self.assertEqual(ans, val)

    def test_loads_all_chains(self):
        val = len(list(self.structure.chains()))
        ans = 2
        self.assertEqual(ans, val)

    def test_loads_all_components(self):
        val = len(list(self.structure.residues()))
        ans = 340
        self.assertEqual(ans, val)

    # def test_loads_all_rna(self):
    #     val = len(list(self.structure.residues(type='rna')))
    #     ans = None
    #     self.assertEqual(ans, val)

    # def test_loads_all_atoms(self):
    #     val = len(list(self.structure.atoms()))
    #     ans = None
    #     self.assertEqual(ans, val)

    def test_can_get_a_model(self):
        val = self.structure.model(1).model
        ans = 1
        self.assertEqual(ans, val)

    def test_fails_getting_invalid_model(self):
        self.assertRaises(IndexError, self.structure.model, 2)

    def test_can_get_a_chain(self):
        val = self.structure.chain(0, 'A').chain
        ans = 'A'
        self.assertEqual(ans, val)

    def test_fails_getting_invalid_chain(self):
        self.assertTrue(self.structure.chain(1, 'C') is None)


class ResidueTest(ReaderTest):
    name = '1GID'

    def setUp(self):
        super(ResidueTest, self).setUp()
        self.residues = list(self.structure.residues())

    def test_assigns_atoms_to_residues(self):
        self.residues.sort(key=lambda r: r.number)
        val = len(self.residues[49].atoms())
        ans = 20
        self.assertEqual(ans, val)

    def test_assigns_numbers_correctly(self):
        self.residues.sort(key=lambda r: r.number)
        val = self.residues[0].number
        ans = 103
        self.assertEqual(ans, val)

    def test_assigns_pdb(self):
        val = self.residues[0].pdb
        ans = '1GID'
        self.assertEqual(ans, val)

    def test_assigns_model(self):
        val = self.residues[0].model
        ans = 1
        self.assertEqual(ans, val)

    def test_assigns_chain(self):
        self.residues.sort(key=lambda r: '%s%s' % (r.chain, r.number))
        val = self.residues[0].chain
        ans = 'A'
        self.assertEqual(ans, val)

    def test_assigns_symmetry(self):
        val = self.residues[0].symmetry
        ans = '1_555'
        self.assertEqual(ans, val)

    def test_assigns_ins_code(self):
        val = self.residues[0].ins_code
        ans = None
        self.assertEqual(ans, val)

    def test_assigns_sequence(self):
        self.residues.sort(key=lambda r: r.number)
        val = self.residues[0].sequence
        ans = 'G'
        self.assertEqual(ans, val)

    def test_can_generate_unit_id(self):
        self.residues.sort(key=lambda r: '%s%s' % (r.chain, r.number))
        val = self.residues[0].unit_id()
        ans = '1GID|1|A|G|103'
        self.assertEqual(ans, val)

    def test_assigns_type(self):
        val = self.residues[0].type
        ans = 'RNA linking'
        self.assertEqual(ans, val)


# class ChainTest(ReaderTest):
#     name = '1FAT'

#     def setUp(self):
#         self.data = self.__class__.structure.chain(1, 'D')

#     def test_it_knows_the_chain_id(self):
#         val = self.data.chain
#         ans = 'D'
#         self.assertEqual(ans, val)

#     def test_it_only_has_rows_from_correct_chain(self):
#         val = list(set([a.chain for a in self.data.atoms()]))
#         ans = ['D']
#         self.assertEqual(ans, val)

#     def test_it_can_find_unit_id_for_index(self):
#         val = self.data[1].unit_id()
#         ans = '1FAT|1|D|ASN|2'
#         self.assertEqual(val, ans)

#     def test_it_can_get_the_first_residue(self):
#         val = self.data.first().unit_id()
#         ans = '1FAT|1|D|SER|1'
#         self.assertEqual(val, ans)

#     def test_it_can_get_the_last_residue(self):
#         val = self.data.last().unit_id()
#         ans = '1FAT|1|D|SER|233'
#         self.assertEqual(val, ans)

#     def tes_it_knows_if_it_has_breaks(self):
#         self.assertTrue(self.data.has_breaks())

#     def test_can_get_all_residues(self):
#         val = len(list(self.data.residues()))
#         ans = 232
#         self.assertEqual(ans, val)


# class BasicChainPolymersTest(ReaderTest):
#     name = '1FAT'

#     def setUp(self):
#         self.chain = self.__class__.structure.chain(1, 'A')

#     def test_can_get_polymers(self):
#         val = [len(p) for p in self.chain.polymers()]
#         ans = [36, 232 - 36]
#         self.assertEqual(ans, val)

#     def test_it_has_no_breaks(self):
#         self.assertFalse(self.chain.polymer(0).has_breaks())
#         self.assertFalse(self.chain.polymer(1).has_breaks())


# class PolymersTest(ReaderTest):
#     name = '1FAT'

#     def setUp(self):
#         self.cif = self.__class__.cif
#         self.data = self.cif.chain('1_555', '1', 'D').polymers()

#     def test_gets_all_polymers_in_all_chains(self):
#         val = sorted(set([poly['chain'] for poly in self.cif.polymers()]))
#         ans = ['A', 'B', 'C', 'D']
#         self.assertEqual(val, ans)

#     def test_gets_requested_chain_polymer(self):
#         val = [poly['chain'] for poly in self.data]
#         ans = ['D', 'D']
#         self.assertEqual(val, ans)

#     def test_finds_polymer_sequence(self):
#         ans = [
#             ['SER', 'ASN', 'ASP', 'ILE', 'TYR', 'PHE', 'ASN', 'PHE', 'GLN',
#              'ARG', 'PHE', 'ASN', 'GLU', 'THR', 'ASN', 'LEU', 'ILE', 'LEU',
#              'GLN', 'ARG', 'ASP', 'ALA', 'SER', 'VAL', 'SER', 'SER', 'SER',
#              'GLY', 'GLN', 'LEU', 'ARG', 'LEU', 'THR', 'ASN', 'LEU'],
#             ['ASN', 'GLY', 'GLU', 'PRO', 'ARG', 'VAL', 'GLY', 'SER', 'LEU',
#              'GLY', 'ARG', 'ALA', 'PHE', 'TYR', 'SER', 'ALA', 'PRO', 'ILE',
#              'GLN', 'ILE', 'TRP', 'ASP', 'ASN', 'THR', 'THR', 'GLY', 'THR',
#              'VAL', 'ALA', 'SER', 'PHE', 'ALA', 'THR', 'SER', 'PHE', 'THR',
#              'PHE', 'ASN', 'ILE', 'GLN', 'VAL', 'PRO', 'ASN', 'ASN', 'ALA',
#              'GLY', 'PRO', 'ALA', 'ASP', 'GLY', 'LEU', 'ALA', 'PHE', 'ALA',
#              'LEU', 'VAL', 'PRO', 'VAL', 'GLY', 'SER', 'GLN', 'PRO', 'LYS',
#              'ASP', 'LYS', 'GLY', 'GLY', 'PHE', 'LEU', 'GLY', 'LEU', 'PHE',
#              'ASP', 'GLY', 'SER', 'ASN', 'SER', 'ASN', 'PHE', 'HIS', 'THR',
#              'VAL', 'ALA', 'VAL', 'GLU', 'PHE', 'ASP', 'THR', 'LEU', 'TYR',
#              'ASN', 'LYS', 'ASP', 'TRP', 'ASP', 'PRO', 'THR', 'GLU', 'ARG',
#              'HIS', 'ILE', 'GLY', 'ILE', 'ASP', 'VAL', 'ASN', 'SER', 'ILE',
#              'ARG', 'SER', 'ILE', 'LYS', 'THR', 'THR', 'ARG', 'TRP', 'ASP',
#              'PHE', 'VAL', 'ASN', 'GLY', 'GLU', 'ASN', 'ALA', 'GLU', 'VAL',
#              'LEU', 'ILE', 'THR', 'TYR', 'ASP', 'SER', 'SER', 'THR', 'ASN',
#              'LEU', 'LEU', 'VAL', 'ALA', 'SER', 'LEU', 'VAL', 'TYR', 'PRO',
#              'SER', 'GLN', 'LYS', 'THR', 'SER', 'PHE', 'ILE', 'VAL', 'SER',
#              'ASP', 'THR', 'VAL', 'ASP', 'LEU', 'LYS', 'SER', 'VAL', 'LEU',
#              'PRO', 'GLU', 'TRP', 'VAL', 'SER', 'VAL', 'GLY', 'PHE', 'SER',
#              'ALA', 'THR', 'THR', 'GLY', 'ILE', 'ASN', 'LYS', 'GLY', 'ASN',
#              'VAL', 'GLU', 'THR', 'ASN', 'ASP', 'VAL', 'LEU', 'SER', 'TRP',
#              'SER', 'PHE', 'ALA', 'SER', 'LYS', 'LEU', 'SER']
#         ]
#         val = [poly.sequence for poly in self.data]
#         self.assertEqual(val, ans)


# class BuildingStructuresWithBreaks(ReaderTest):
#     name = '2UUA'

#     def test_detects_all_polymers(self):
#         val = len(list(self.structure.chain(1, 'A').polymers()))
#         ans = 2
#         self.assertEqual(ans, val)

#     def test_detects_breaks_correctly(self):
#         polymers = self.structure.polymers()
#         val = [(p.first().unit_id(), p.last.unit_id()) for p in polymers]
#         ans = [('2UUA|1|A|U|5', '2UUA|1|A|A|1531'),
#                ('2UUA|1|A|A|1532', '2UUA|1|A|U|1544')]
#         self.assertEqual(ans, val)