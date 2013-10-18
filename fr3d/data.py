"""This is a package that contains the basic data structures that FR3D works
on, such as Atoms and Components.

"""

import numpy as np

from fr3d.unit_ids import encode
from fr3d.definitions import RNAbaseheavyatoms
from fr3d.definitions import RNAbasecoordinates
from fr3d.definitions import RNAbasehydrogens
from fr3d.geometry.superpositions import besttransformation



class Entity(object):
    """This class is the base class for things like atoms and other units. It
    is intended to provide a simple dict like access to the data in it as well
    as have a method for generating its unit id. Currently, the data stored in
    this object is not mutable, but this may need to be changed.
    """

    def __init__(self, **kwargs):
        self._data = kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                raise ValueError("Can't override properites")
            setattr(self, key, value)

    def unit_id(self):
        """Compute the unit id for this Entity.

        :returns: A string of the unit id.
        """

        return encode(self.__rename__())


class EntityContainer(object):
    """This serves as a generic container for entities. We always want to
    provide some methods like getting all entities in a particular order, or
    getting all entities with a particular type. This serves to provide such
    functionality to all classes that contain entities.
    """

    def __getter__(self, obj, **kwargs):
        """This method is a way to sort and filter an object easily. The
        keyword arguments, order_by and cmp are used for sorting while
        everything else is used by __checker__ for filtering. The order_by
        keyword may be either a string or a function. If it is a string
        then we create a function which gets that key from the entities
        in obj and uses that as the key function in sorting. The cmp keyword
        is used as the cmp function in sorting. All other keywords are used as
        described in __checker__. If no keywords are given then the object is
        simply returned.

        :obj: An iterable to filter and sort
        :kwargs: Keyword arguments for filtering and sorting.
        """

        if not kwargs:
            return obj

        orderby = kwargs.pop('order_by', None)
        compare = kwargs.pop('cmp', None)

        checker = self.__checker__(**kwargs)
        raw = [entry for entry in obj if checker(entry)]

        if orderby:
            key = orderby
            if not callable(orderby):
                key = lambda entry: getattr(entry, orderby, None)
            raw.sort(key=key)

        if compare:
            raw.sort(cmp=compare)

        return raw

    def __make_check__(self, key, value):
        """Generate a function for filtering. If the given value is a callable
        then it is used to filter. The function will be given value of key for
        each object it filters. If value is a list then we check to see if
        the value of key in each object is in the list, otherwise we check to
        see if the value of the key in each object equals the given value.

        :key: The key to filter by.
        :value: The value to use as the filter.
        """

        def check(obj):
            given = getattr(obj, key, None)

            if callable(value):
                return value(given)

            if isinstance(value, list):
                return given in value

            return value == given

        return check

    def __checker__(self, **kwargs):
        """This generates a function which is used to filter an iterable.
        """

        checkers = []
        for key, value in kwargs.items():
            checkers.append(self.__make_check__(key, value))

        def checker(entity):
            for checker in checkers:
                if not checker(entity):
                    return False
            return True

        return checker


class Atom(Entity):
    """This class represents atoms in a structure. It provides a simple dict
    like access for data as well as a way to get it's coordiantes, unit id
    and the unit id of the component it belongs to.
    """

    def __init__(self, **kwargs):
        """Create a new Atom.

        :data: A dictonary of data to provide access to.
        """
        super(Atom, self).__init__(**kwargs)

    def component_unit_id(self):
        """Generate the unit id of the component this atom belongs to.

        :returns: A string of the unit id for this atom's component.
        """

        comp_data = self.__rename__()
        if 'atom_name' in comp_data:
            del comp_data['atom_name']
        if 'alt_id' in comp_data:
            del comp_data['alt_id']

        return encode(comp_data)

    def __rename__(self):
        data = dict(self._data)
        data['atom_name'] = data.pop('name')
        return data

    def coordinates(self):
        """Return a numpy array of the x, y, z coordinates for this atom.

        :returns: A numpy array of the x, y, z coordinates.
        """
        return np.array([self.x, self.y, self.z])

    def __repr__(self):
        return '<Atom: %s>' % self._data


class Component(Entity, EntityContainer):
    """This represents things like nucleic acids, amino acids, small molecules
    and ligands.
    """

    def __init__(self, atoms, **kwargs):
        """Create a new Component.

        :data: The data to provide access to.
        :atoms: The atoms this component is composed of.
        """

        self._atoms = atoms
        super(Component, self).__init__(**kwargs)

        self.centers = {}

        if self.sequence in ['A', 'C', 'G', 'U']:
            atoms = RNAbaseheavyatoms[self.sequence]
            self.centers['base'] = self.__compute_center__(atoms)

    def atoms(self, **kwargs):
        """Get, filter and sort the atoms in this component. Access is as
        described by EntityContainer.__getter__.

        :kwargs: The keyword arguments to filter and sort by.
        :returns: A list of the requested atoms.
        """
        return self.__getter__(self._atoms, **kwargs)

    def coordinates(self, **kwargs):
        """Get the coordaintes of all atoms in this component. This will
        filter to the requested atoms, sort and then provide a numpy array
        of all coordinates for the given atoms.

        :kwargs: Arguments to filter and sort by.
        :returns: A numpy array of the coordinates.
        """
        return np.array([atom.coordinates() for atom in self.atoms(**kwargs)])

    def __rename__(self):
        data = dict(self._data)
        data['component_id'] = data.pop('sequence')
        data['component_number'] = data.pop('number')
        return data

    def is_complete(self, names, key='name'):
        """This checks if we can find all atoms in this entity with the given
        names. This assumes that the names for each atom are unique. If you
        wish to use something other than name use the key argument. However, it
        must provide a unique value for each atom, if several atoms with the
        same value are found will cause the function to behave oddly.

        :names: The list of names to check for.
        :key: The key to use for getting atoms. Defaults to name.
        :returns: True if all atoms with the given name are present.
        """
        kwargs = {key: names}
        found = self.atoms(**kwargs)
        return len(found) == len(names)

    def __compute_center__(self, atoms):
        """Compute the center position for the given set of atoms. This is done
        through taking the mean position of each atom. If a requested atom
        does not exist it is ignored.

        :atoms: Atoms to use to find the center.
        :returns: The x, y, z coordinates of centers.
        """
        coordinates = [atom.coordinates() for atom in self.atoms(name=atoms)]
        if not coordinates:
            return None
        return np.mean(coordinates, axis=0)

    def __len__(self):
        """Compute the length of this Component. This is the number of atoms in
        this residue.

        :returns: The number of atoms.
        """
        return len(self._atoms)

    def __repr__(self):
        return '<Component %s Atoms: %s>' % (self._data, self._atoms)
    
    def infer_hydrogens(self):
        """Infer the coordinates of the hydrogen atoms of this component.
        Currently, it only works for RNA with .sequence 
        """
        if self.sequence not in ['A', 'C', 'G', 'U']:
            return None
        R = []
        S = []
        baseheavy = RNAbaseheavyatoms[self.sequence]
    
        for atom in self.atoms(name=baseheavy):
            coordinates = atom.coordinates()
            R.append(coordinates)
            S.append(RNAbasecoordinates[self.sequence][atom.name])
        
        R = np.array(R)
        R = R.astype(np.float)
        S = np.array(S)
        rotation_matrix, fitted, base_center, rmsd = besttransformation(R, S)
        hydrogens = RNAbasehydrogens[self.sequence]
    
        for hydrogenatom in hydrogens:
            hydrogencoordinates = RNAbasecoordinates[self.sequence][hydrogenatom]
            newcoordinates = base_center + \
            	np.dot(hydrogencoordinates, np.transpose(rotation_matrix))
            self._atoms.append(Atom({'name': hydrogenatom,
            	                    'x': newcoordinates[0,0], 
                    	            'y': newcoordinates[0,1], 
                        	        'z': newcoordinates[0,2]}))

class Structure(Entity, EntityContainer):
    """This represents a structure which is composed of components.
    """

    def __init__(self, residues, **kwargs):
        self._residues = residues
        super(Structure, self).__init__(**kwargs)

    def residues(self, **kwargs):
        """Get residues from this structure. The keyword arguments work as
        described by EntityContainer.__getter__.

        :kwargs: Keywords for filtering and ordering
        :returns: The requested residues.
        """
        return self.__getter__(self._residues, **kwargs)

    def __rename__(self):
        return dict(self._data)

    def __len__(self):
        """Compute the length of this Structure. That is the number of residues
        in this structure.


        :returns: The number of atoms.
        """
        return len(self._residues)

    def infer_hydrogens(self):
    	""" Infers hydrogen atoms for all bases.
    	"""
    	for residue in self.residues(sequence=['A', 'C', 'G', 'U']):
        	residue.infer_hydrogens()



