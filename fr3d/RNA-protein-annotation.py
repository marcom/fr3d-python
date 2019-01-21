# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 12:44:30 2014 @author: Poorna
Name: RNA-protein detection
"""

"""Detect and plot RNA base- amino acid interactions."""
from fr3d.cif.reader import Cif
from fr3d.definitions import RNAconnections
from fr3d.definitions import RNAbaseheavyatoms
from fr3d.definitions import Ribophos_connect
from fr3d.definitions import aa_connections
from fr3d.definitions import aa_backconnect
from fr3d.definitions import aa_fg
from fr3d.definitions import tilt_cutoff
from fr3d.definitions import planar_atoms
from fr3d.definitions import HB_donors
from fr3d.definitions import HB_acceptors
import numpy as np
import csv
import urllib

import matplotlib.pyplot as plt
from collections import defaultdict
from mpl_toolkits.mplot3d import Axes3D
# note that fr3d.localpath does not synchronize with Git, so you can change it locally to point to your own directory structure
from fr3d.localpath import outputText
from fr3d.localpath import outputBaseAAFG
from fr3d.localpath import inputPath
from fr3d.localpath import outputHTML

from fr3d.ordering.greedyInsertion import orderWithPathLengthFromDistanceMatrix

#from fr3d.classifiers.base_aafg import distance_metrics
from datetime import datetime
from math import floor
import os.path
from os import path

def get_structure(filename):
    if not os.path.exists(filename):
        mmCIFname = filename[-8:]
        print("Downloading "+mmCIFname)
        f = urllib.urlopen("https://files.rcsb.org/download/%s" % mmCIFname)
        myfile = f.read()
        with open(filename, 'w') as outfile:
            outfile.write(myfile)

    with open(filename, 'rb') as raw:
        structure = Cif(raw).structure()
        """All RNA bases are placed in the standard orientation. All Hydrogen
 atoms are inferred. Rotation matrix is calculated for each base."""
        structure.infer_hydrogens()
        return structure


def atom_dist_basepart(base_residue, aa_residue, base_atoms, c):
    """Calculates atom to atom distance of part "aa_part" of neighboring amino acids
    of type "aa" from each atom of base. Only returns a pair of aa/nt if two
    or more atoms are within the cutoff distance"""
    min_distance = 4
    n = 0
    for base_atom in base_residue.atoms(name=base_atoms):
        for aa_atom in aa_residue.atoms(name=aa_fg[aa_residue.sequence]):
            # aa_atom = atom.coordinates()
            distance = np.subtract(base_atom.coordinates(), aa_atom.coordinates())
            distance = np.linalg.norm(distance)
            #print base_residue.unit_id(), aa_residue.unit_id(), distance
            if distance <= min_distance:
                n = n+1
                #print aa_atom.name
    if n>=c:
        #print aa_residue.unit_id()
        return True

def enough_HBs(base_residue, aa_residue, base_atoms):
    """Calculates number of Hydrogen bonds between amino acid part and base_part
    and determines if they are enough to form a pseudopair"""
    min_distance = 4
    base_key = base_residue.sequence
    aa_key = aa_residue.sequence
    n = 0
    base_HB_atoms = base_atoms + ["O2'"]
    base_donors = HB_donors[base_key]
    base_acceptors = HB_acceptors[base_key]
    aa_donors = HB_donors[aa_key]
    aa_acceptors = HB_acceptors[aa_key]

    for base_atom in base_residue.atoms(name=base_HB_atoms):
        for aa_atom in aa_residue.atoms(name=aa_fg[aa_key]):
            distance = np.subtract(base_atom.coordinates(), aa_atom.coordinates())
            distance = np.linalg.norm(distance)
            if distance <= min_distance:
                #print "HB", base_residue.unit_id(), aa_residue.unit_id(), base_atom.name, aa_atom.name, distance
                if base_atom.name in base_donors and aa_atom.name in aa_acceptors:
                    n = n+1
                elif base_atom.name in base_acceptors and aa_atom.name in aa_donors:
                    n = n+1
#    print base_residue.unit_id(), aa_residue.unit_id(), n
    if n>=2:
        return True

def find_neighbors(bases, amino_acids, aa_part, dist_cent_cutoff):
    """Finds all amino acids of type "aa" for which center of "aa_part" is within
    specified distance of center of bases of type "base" """

    # build a set of cubes and record which bases are in which cube
    # also record which other cubes are neighbors of each cube
    baseCubeList = {}
    baseCubeNeighbors = {}
    for base in bases:
        center = base.centers["base"]
        if len(center) == 3:
#            print(base.unit_id() + str(center))
            x = floor(center[0]/dist_cent_cutoff)
            y = floor(center[1]/dist_cent_cutoff)
            z = floor(center[2]/dist_cent_cutoff)
            key = "%d,%d,%d" % (x,y,z)
            if key in baseCubeList:
                baseCubeList[key].append(base)
            else:
                baseCubeList[key] = [base]
                baseCubeNeighbors[key] = []
                for a in [-1,0,1]:
                    for b in [-1,0,1]:
                        for c in [-1,0,1]:
                            k = "%d,%d,%d" % (x+a,y+b,z+c)
                            baseCubeNeighbors[key].append(k)

    # build a set of cubes and record which amino acids are in which cube
    aaCubeList = {}
    for aa in amino_acids:
        center = aa.centers[aa_part]
        if len(center) == 3:
            x = floor(center[0]/dist_cent_cutoff)
            y = floor(center[1]/dist_cent_cutoff)
            z = floor(center[2]/dist_cent_cutoff)
            key = "%d,%d,%d" % (x,y,z)
            if key in aaCubeList:
                aaCubeList[key].append(aa)
            else:
                aaCubeList[key] = [aa]
        else:
            print("  Missing center coordinates for " + str(aa))

    return baseCubeList, baseCubeNeighbors, aaCubeList

def annotate_interactions(bases, amino_acids, aa_part, dist_cent_cutoff, baseCubeList, baseCubeNeighbors, aaCubeList):

    # loop through base cubes, loop through neighboring cubes,
    # then loop through bases and amino acids in the two cubes,
    # screening distances between them, then annotating interactions
    """Finds all amino acids of type "aa" for which center of "aa_part" is within
    specified distance of center of bases of type "base" and returns superposed bases"""

    #count_total = 0
    count_pair = 0
    list_aa_coord = []
    list_base_coord = []
    aaList_len = None
    new_aaList_len = None
    list_base_aa = []

    for key in baseCubeList:
        for aakey in baseCubeNeighbors[key]:
            if aakey in aaCubeList:
                for base_residue in baseCubeList[key]:
                    base_seq = base_residue.sequence
                    base_atoms = RNAbaseheavyatoms[base_seq]

                    base_center = base_residue.centers["base"]

#                    print("Base center")
#                    print base_center

                    if not base_center.any():
                        continue

                    if not base_residue.centers[planar_atoms[base_seq][0]].any():
                        continue
                    if not base_residue.centers[planar_atoms[base_seq][1]].any():
                        continue
                    if not base_residue.centers[planar_atoms[base_seq][2]].any():
                        continue

                    for aa_residue in aaCubeList[aakey]:
                        aa_center = aa_residue.centers[aa_part]
                        if not aa_center.any():
                            continue

                        if aa_residue.sequence in set (['LYS','SER', 'THR', 'TYR']):
                            c= 1
                        else:
                            c = 2

                        if abs(base_center[0]-aa_center[0]) < dist_cent_cutoff and \
                        abs(base_center[1]-aa_center[1]) < dist_cent_cutoff and \
                        np.linalg.norm(np.subtract(base_center,aa_center)) < dist_cent_cutoff and \
                        atom_dist_basepart(base_residue, aa_residue, base_atoms, c):

                            count_pair = count_pair + 1

                            rotation_matrix = base_residue.rotation_matrix

                            # rotate base atoms into standard orientation
                            base_coordinates = {}
                            standard_base = base_residue.translate_rotate_component(base_residue)
                            for base_atom in standard_base.atoms():
                                base_coordinates[base_atom.name]= base_atom.coordinates()

                            # rotate amino acid atoms into standard orientation
                            aa_coordinates = {}
                            standard_aa = base_residue.translate_rotate_component(aa_residue)
                            for aa_atom in standard_aa.atoms():
                                aa_coordinates[aa_atom.name] = aa_atom.coordinates()

                            standard_aa_center = standard_aa.centers[aa_part]

#                            print aa_residue
#                            print base_residue
                            interaction = type_of_interaction(base_residue, aa_residue, aa_coordinates)

                            base_aa = None
                            if interaction == "pseudopair" and enough_HBs(base_residue, aa_residue, base_atoms):
                                edge = detect_edge(base_residue, base_coordinates,aa_residue, aa_coordinates)
                                base_aa = (base_residue, aa_residue, interaction, edge, standard_aa_center)

                            elif interaction == "SHB":
                                edge = detect_edge(base_residue, base_coordinates,aa_residue, aa_coordinates)
                                base_aa = (base_residue, aa_residue, interaction, edge, standard_aa_center)

                            elif interaction == "perpendicular edge":
                                edge = detect_edge(base_residue, base_coordinates,aa_residue, aa_coordinates)
                                base_aa = (base_residue, aa_residue, interaction, edge, standard_aa_center)

                            elif interaction == "stacked" or interaction == "cation-pi" \
                            or interaction == "perpendicular stacking":
                                edge = detect_face(aa_residue, aa_coordinates)
                                base_aa = (base_residue, aa_residue, interaction, edge, standard_aa_center)

                            if base_aa is not None:
                                list_base_aa.append(base_aa)

                                for base_atom in base_residue.atoms():
                                    list_base_coord.append(base_coordinates)
                                for aa_atom in aa_residue.atoms():
                                    list_aa_coord.append(aa_coordinates)

    return list_base_aa, list_aa_coord, list_base_coord

def type_of_interaction(base_residue, aa_residue, aa_coordinates):
    squared_xy_dist_list = []
    aa_z =[]

    """Defines different sets of amino acids"""
    stacked_planar_aa = set (["TRP", "TYR", "PHE", "HIS", "ARG", "ASN", "GLN", "GLU", "ASP"])
    stacked_aliphatic = set(["LEU", "ILE", "PRO", "THR", "MET", "CYS", "VAL", "ALA", "SER"])
    pseudopair_aa = set (["ASP", "GLU", "ASN", "GLN", "HIS", "ARG", "TYR", "TRP", "PHE", "LYS"])
    shb_aa = set (["SER", "THR", "LYS"])

    for aa_atom in aa_residue.atoms(name=aa_fg[aa_residue.sequence]):
        key = aa_atom.name
        aa_x= aa_coordinates[key][0]
        aa_y= aa_coordinates[key][1]

        squared_xy_dist = (aa_x**2) + (aa_y**2)
        squared_xy_dist_list.append(squared_xy_dist)

        aa_z.append(aa_coordinates[key][2])

    mean_z = np.mean(aa_z)

    #print base_residue.unit_id(), aa_residue.unit_id(), min(squared_xy_dist_list), mean_z
    if min(squared_xy_dist_list) <= 5:
        #print base_residue.unit_id(), aa_residue.unit_id(), min(squared_xy_dist_list), mean_z
        if aa_residue.sequence in stacked_planar_aa:
            #print "stacking?", base_residue.unit_id(), aa_residue.unit_id(), min(squared_xy_dist_list), mean_z
            return stacking_angle(base_residue, aa_residue, min(squared_xy_dist_list))

        elif aa_residue.sequence in stacked_aliphatic:
            return stacking_tilt(aa_residue, aa_coordinates)

    elif -1.8 <= mean_z < 1.8 and aa_residue.sequence in pseudopair_aa:
            angle= calculate_angle(base_residue, aa_residue)
            angle = abs(angle)
            #print "pseudopair?", base_residue.unit_id(), aa_residue.unit_id(), angle
            if 0 <= angle <= 0.75 or 2.5 <= angle <= 3.14:
                return "pseudopair"
            elif 0.95 <= angle <=1.64:
                return "perpendicular edge"

    elif -1.8 <= mean_z < 1.8 and aa_residue.sequence in shb_aa:
        base_seq = base_residue.sequence
        base_atoms = RNAbaseheavyatoms[base_seq]
        if atom_dist_basepart(base_residue, aa_residue, base_atoms, 1):
            return "SHB"

def calculate_angle (base_residue, aa_residue):
    vec1 = vector_calculation(base_residue)
    vec2 = vector_calculation(aa_residue)

    angle = angle_between_planes(vec1, vec2)
    return angle

def stacking_angle (base_residue, aa_residue, min_dist):
    vec1 = vector_calculation(base_residue)
    vec2 = vector_calculation(aa_residue)
    perpendicular_aa = set (["HIS", "ARG", "LYS", "ASN", "GLN"])
    perpendicular_stack_aa = set(["PHE", "TYR"])
    angle = angle_between_planes(vec1, vec2)
    #print "stacked?"
    #print base_residue.unit_id(), aa_residue.unit_id(), min_dist, angle
    angle = abs(angle)
    if angle <=0.68 or 2.45 <= angle <= 3.15:
        return "stacked"
    elif 1.2<= angle <=1.64:
        if aa_residue.sequence in perpendicular_stack_aa:
            return "perpendicular stacking"
        elif aa_residue.sequence in perpendicular_aa:
            return "cation-pi"

def stacking_tilt(aa_residue, aa_coordinates):
    baa_dist_list = []

    for aa_atom in aa_residue.atoms(name=aa_fg[aa_residue.sequence]):
        key = aa_atom.name
        aa_z = aa_coordinates[key][2]
        baa_dist_list.append(aa_z)
    max_baa = max(baa_dist_list)
    min_baa = min(baa_dist_list)
    diff = max_baa - min_baa
    #print aa_residue.unit_id(), diff
    if diff <= tilt_cutoff[aa_residue.sequence]:
        return "stacked"

def vector_calculation(residue):
    key = residue.sequence
    P1 = residue.centers[planar_atoms[key][0]]
    P2 = residue.centers[planar_atoms[key][1]]
    P3 = residue.centers[planar_atoms[key][2]]
#    print key,P1, P2, P3

    vector = np.cross((P2 - P1),(P3-P1))
    return vector

def angle_between_planes (vec1, vec2):
    cosang = np.dot(vec1, vec2)
    sinang = np.linalg.norm(np.cross(vec1, vec2))
    angle = np.arctan2(sinang, cosang)
    return angle

def detect_edge(base_residue, base_coordinates,aa_residue, aa_coordinates):
    aa_x = []
    aa_y = []
    base_x = []
    base_y = []
    for aa_atom in aa_residue.atoms(name=aa_fg[aa_residue.sequence]):
        key = aa_atom.name
        aa_x.append(aa_coordinates[key][0])
        aa_y.append(aa_coordinates[key][1])

    aa_center_x = np.mean(aa_x)
    aa_center_y = np.mean(aa_y)

    for base_atom in base_residue.atoms(name=RNAbaseheavyatoms[base_residue.sequence]):
        key = base_atom.name
        base_x.append(base_coordinates[key][0])
        base_y.append(base_coordinates[key][1])

    base_center_x = np.mean(base_x)
    base_center_y = np.mean(base_y)

    y = aa_center_y - base_center_y
    x = aa_center_x - base_center_x
    angle_aa = np.arctan2(y,x) #values -pi to pi
    #print base_residue.unit_id(), aa_residue.unit_id(),angle_aa
    purine = set(["A", "G"])
    pyrimidine = set(["C", "U"])
    angle_deg = (180*angle_aa)/3.14159 #values -180 to 180

#    print("  Edge angle in rad and deg" +str(angle_aa) + " " + str(angle_deg))

    if base_residue.sequence in purine:
        if -15 <= angle_deg <= 90:
            return "fgWC"
        elif 90 < angle_deg or angle_deg < -160:
            return "fgH"
        else:
            return "fgS"

    elif base_residue.sequence in pyrimidine:
        if -45 <= angle_deg <= 90:
            return "fgWC"
        elif 90 < angle_deg or angle_deg < -150:
            return "fgH"
        else:
            return "fgS"

def detect_face(aa_residue, aa_coordinates):
    aa_z =[]

    for aa_atom in aa_residue.atoms(name=aa_fg[aa_residue.sequence]):
        key = aa_atom.name
        aa_z.append(aa_coordinates[key][2])

    mean_z = np.mean(aa_z)
    if mean_z <= 0:
        return "fgs5"
    else:
        return "fgs3"

def text_output(result_list):
    with open(outputText % PDB, 'wb') as target:
        for result in result_list:
            target.write(str(result))
            target.write("\r\n")
            target.close

def csv_output(result_list):
    with open(outputBaseAAFG % PDB, 'wb') as csvfile:
        fieldnames = ['RNA ID', 'AA ID', 'RNA Chain ID', 'RNA residue','RNA residue number','Protein Chain ID', 'AA residue','AA residue number', 'Interaction', 'Edge']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for base_residue, aa_residue, interaction, edge, standard_aa_center in result_list:
            base = base_residue.unit_id()
            aa = aa_residue.unit_id()
            #print base, aa, interaction
            base_component = str(base).split("|")
            aa_component = str(aa).split("|")
            writer.writerow({'RNA ID': base, 'AA ID': aa, 'RNA Chain ID': base_component[2], 'RNA residue':base_component[3],'RNA residue number': base_component[4],'Protein Chain ID':aa_component[2],'AA residue': aa_component[3],'AA residue number': aa_component[4], 'Interaction': interaction, 'Edge': edge})

        """for base_residue, aa_residue,interaction in result_list:
                    base_component = str(base_residue).split("|")
                    aa_component = str(aa_residue).split("|")
                    writer.writerow({'RNA Chain ID': base_component[2], 'RNA residue':base_component[3],'RNA residue number': base_component[4],'Protein Chain ID':ChainNames[PDB][aa_component[2]],'AA residue': aa_component[3],'AA residue number': aa_component[4], 'Interaction': interaction})"""



def draw_base(base_seq, ax):
    """Connects atoms to draw neighboring bases and amino acids for 3D plots"""
     #creates lists of rotated base coordinates
    for basecoord_list in list_base_coord:
        new_base_x = []
        new_base_y = []
        new_base_z = []

        back_base_x = []
        back_base_y = []
        back_base_z = []


        try:
            for atomname in RNAconnections[base_seq]:
                coord_base = []
                coord_base= basecoord_list[atomname]
                new_base_x.append(coord_base[0])
                new_base_y.append(coord_base[1])
                new_base_z.append(coord_base[2])
            base_lines= ax.plot(new_base_x, new_base_y, new_base_z, label= 'Base')
            #ax.scatter(basecenter[0], basecenter[1], basecenter[2], zdir='y', color='b', marker='o')
            #ax.scatter(x = 0, y= 0, z= 0, color='b', marker='o')
            plt.setp(base_lines, 'color', 'b', 'linewidth', 1.0)

            for atomname in Ribophos_connect[base_seq]:
                back_base=[]
                back_base= basecoord_list[atomname]
                back_base_x.append(back_base[0])
                back_base_y.append(back_base[1])
                back_base_z.append(back_base[2])
            base_lines= ax.plot(back_base_x, back_base_y, back_base_z, label= 'Base')
            plt.setp(base_lines, 'color', 'g', 'linewidth', 1.0)
            #ax.text(9, 1, 1, base_residue)
        except:
            print "Missing residues"
            continue

def draw_aa(aa, ax):
    #Connects atoms to draw neighboring bases and amino acids for 3D plots
    for aacoord_list in list_aa_coord:
        new_aa_x=[]
        new_aa_y=[]
        new_aa_z=[]

        back_aa_x=[]
        back_aa_y=[]
        back_aa_z=[]

        try:
            for atomname in aa_connections[aa]:
                coord_aa=[]
                coord_aa= aacoord_list[atomname]
                new_aa_x.append(coord_aa[0])
                new_aa_y.append(coord_aa[1])
                new_aa_z.append(coord_aa[2])
            aa_lines= ax.plot(new_aa_x, new_aa_y, new_aa_z, label= 'Amino acid')
            plt.setp(aa_lines, 'color', 'r', 'linewidth', 1.0)

            for atomname in aa_backconnect[aa]:
                back_aa=[]
                back_aa= aacoord_list[atomname]
                back_aa_x.append(back_aa[0])
                back_aa_y.append(back_aa[1])
                back_aa_z.append(back_aa[2])
            aa_lines= ax.plot(back_aa_x, back_aa_y, back_aa_z, label= 'Amino acid')
            plt.setp(aa_lines, 'color', 'y', 'linewidth', 1.0)
        except:
            print "Missing residues"
            continue

def draw_aa_cent(aa, aa_part, ax):
    #Connects atoms to draw neighboring bases and amino acids for 3D plots
    for aacoord_list in list_aa_coord:
        new_aa_x=[]
        new_aa_y=[]
        new_aa_z=[]

        aa_center_x = 0
        aa_center_y = 0
        aa_center_z = 0
        n = 0

        if aa_part == 'aa_fg':
            connections = aa_connections
        elif aa_part == 'aa_backbone':
            connections = aa_backconnect
        try:
            for atomname in connections[aa]:
                coord_aa=[]
                coord_aa= aacoord_list[atomname]
                new_aa_x.append(coord_aa[0])
                new_aa_y.append(coord_aa[1])
                new_aa_z.append(coord_aa[2])

                aa_center_x = aa_center_x + coord_aa[0]
                aa_center_y = aa_center_y + coord_aa[1]
                aa_center_z = aa_center_z + coord_aa[2]
                n = n + 1
            ax.scatter(aa_center_x/n, aa_center_y/n, aa_center_z/n, c= 'r', marker = 'o')
        except:
            print "Missing residues"
            continue

def writeInteractionsHTML(allInteractionDictionary,outputHTML):

    for key in allInteractionDictionary:
        pagetitle = key.replace(" ","-")
        htmlfilename = key.replace(" ","-")

#        print("Writing HTML file for "+key+" in "+htmlfilename+".html, found "+ str(len(allInteractionDictionary[key])) + " instances")

        # limit the number of instances shown, to be able to compute and display discrepancy
        numForDiscrepancy = min(300,len(allInteractionDictionary[key]))

        fields = key.split("_")
        print(fields[0]+"\t"+fields[1]+"\t"+fields[2]+"\t"+fields[3]+"\t\t"+str(numForDiscrepancy)+"\t\t"+"http://rna.bgsu.edu/RNAprotein/"+key.replace(" ","-")+".html")

        # calculate discrepancies between all instances, up to 300
        discrepancy = np.zeros((numForDiscrepancy,numForDiscrepancy))
        for i in range(0,numForDiscrepancy):
            instance_1 = allInteractionDictionary[key][i]
            standard_aa_center_1 = instance_1[4]
            for j in range(i+1,numForDiscrepancy):
                instance_2 = allInteractionDictionary[key][j]
                standard_aa_center_2 = instance_2[4]
                discrepancy[i][j] = np.linalg.norm(standard_aa_center_1 - standard_aa_center_2)
                discrepancy[j][i] = np.linalg.norm(standard_aa_center_1 - standard_aa_center_2)

        # base_aa = (base_residue, aa_residue, interaction, edge, standard_aa_center)

        # use greedy insertion 100 times to find a decent ordering of the instances
        newOrder, bestPathLength, distances = orderWithPathLengthFromDistanceMatrix(discrepancy,100)

        # rewrite the list of instances, limiting it to numForDiscrepancy
        newList = []
        for i in range(0,len(newOrder)):
            newList.append(allInteractionDictionary[key][newOrder[i]])
        allInteractionDictionary[key] = newList

        # write out text for radio boxes to display each individual interaction
        instancelist = "<h2>"+pagetitle+"</h2>\n<ol>"
        i = 1
        for base_id, aa_id, interaction, edge, standard_aa_center in allInteractionDictionary[key]:
            instancelist += '<li><label><input type="checkbox" id="'+str(i)+'" class="jmolInline" data-coord="'
            instancelist += base_id +","+ aa_id
            instancelist += '">&nbsp'
            instancelist += base_id +" "+ aa_id +" "+ interaction +" "+ edge
            instancelist += '</label></li>\n'
            i += 1
        instancelist += '</ol>\n'

        # write out text to tell what values to put in the heat map
        discrepancyText = ''
        for c in range(0,numForDiscrepancy):
            instance1 = allInteractionDictionary[key][c][0]  # id of base
            for d in range(0,numForDiscrepancy):
                instance2 = allInteractionDictionary[key][d][0]  # id of base

                discrepancyText += '{"discrepancy": ' + str(discrepancy[newOrder[c]][newOrder[d]])
                discrepancyText += ', "ife1": "' + str(c+1) + "-" + instance1 + '", "ife1_index": ' + str(c)
                discrepancyText += ', "ife2": "' + str(d+1) + "-" + instance2 + '", "ife2_index": ' + str(d) + '}'
                if c < numForDiscrepancy-1 or d < numForDiscrepancy-1:
                    discrepancyText += ',\n'

        # read template.html into one string
#        with open(outputHTML+'/localtemplate.html', 'r') as myfile:
        with open(outputHTML+'/onlinetemplate.html', 'r') as myfile:
            template = myfile.read()

        # replace ###PAGETITLE### with pagetitle
        template = template.replace("###PAGETITLE###",pagetitle)

        # replace ###CANDIDATELIST### with instancelist
        template = template.replace("###CANDIDATELIST###",instancelist)

        # replace ###DISCREPANCYDATA### with discrepancyText
        template = template.replace("###DISCREPANCYDATA###",discrepancyText)

        # write htmlfilename
        with open(outputHTML+'/'+htmlfilename+'.html', 'w') as myfile:
            myfile.write(template)

        # upload the files to /var/www/html/RNAprotein

#=======================================================================

"""Inputs a list of PDBs of interest to generate super-imposed plots"""
PDB_List = ['5AJ3']
PDB_List = ['6hiv']
PDB_List = ['3QRQ','5J7L']
PDB_List = ['5J7L']
PDB_List = ['4V9F','4YBB','4Y4O','6AZ3','4P95']
PDB_List = ['3BT7']
PDB_List = ['5I4A']
PDB_List = ['4V9F']
PDB_List = ['http://rna.bgsu.edu/rna3dhub/nrlist/download/3.48/2.5A/csv']
PDB_List = ['6A2H']

base_seq_list = ['A','U','C','G']      # for RNA
base_seq_list = ['DA','DT','DC','DG']  # for DNA

#base_seq_list = ['A']
aa_list = ['ALA','VAL','ILE','LEU','ARG','LYS','HIS','ASP','GLU','ASN','GLN','THR','SER','TYR','TRP','PHE','PRO','CYS','MET']
#aa_list = ['HIS']

#fig = plt.figure()
#ax = fig.add_subplot(111, projection='3d')

"""Inputs base, amino acid, aa_part of interest and cut-off distance for subsequent functions"""
if __name__=="__main__":

    aa_part = 'aa_fg'
    base_part = 'base'

    allInteractionDictionary = defaultdict(list)
    result_nt_aa = []               # for accumulating a complete list over all PDB files

    PDB_File_List = []              # accumulate all PDB file names
    for PDB in PDB_List:
        if "nrlist" in PDB:           # referring to a list online
            f = urllib.urlopen(PDB)
            myfile = f.read()
            alllines = myfile.split("\n")
            for line in alllines:
                fields = line.split(",")

                if len(fields) > 1 and len(fields[1]) > 4:
                    newPDB = fields[1][1:5]
                    PDB_File_List.append(newPDB)
        else:
            PDB_File_List.append(PDB)

    PDB_File_List = sorted(list(set(PDB_File_List)))

    counter = 0
    for PDB in PDB_File_List:
        counter += 1

        print("Reading file " + PDB + ", which is number "+str(counter)+" out of "+str(len(PDB_File_List)))

        start = datetime.now()
        structure = get_structure(inputPath % PDB)
        bases = structure.residues(sequence= base_seq_list)
#        bases = structure.residues(chain= ["0","9"], sequence= "C")   # will make it possible to load IFEs easily
        amino_acids = structure.residues(sequence=aa_list)
        print("  Time required to load " + PDB + " " + str(datetime.now() - start))

        start = datetime.now()
        baseCubeList, baseCubeNeighbors, aaCubeList = find_neighbors(bases, amino_acids, aa_part, 10)
        print("  Time to find neighboring bases and amino acids " + str(datetime.now() - start))

        start = datetime.now()
        list_base_aa, list_aa_coord, list_base_coord = annotate_interactions(bases, amino_acids, aa_part, 10, baseCubeList, baseCubeNeighbors, aaCubeList)
        print("  Time to annotate interactions " + str(datetime.now() - start))

        # accumulate list of interacting units by base, amino acid, interaction type, and edges
        for base_residue, aa_residue, interaction, edge, standard_aa_center in list_base_aa:
            base = base_residue.unit_id()
            aa = aa_residue.unit_id()
            base_component = str(base).split("|")
            aa_component = str(aa).split("|")

            key = base_component[3]+"_"+aa_component[3]+"_"+interaction+"_"+edge
            allInteractionDictionary[key].append((base,aa,interaction,edge,standard_aa_center))  # store tuples

        """ 3D plots of base-aa interactions
        for base, aa, interaction in list_base_aa:
            base_seq = base.sequence
            aa= aa.sequence

            draw_base(base_seq, ax)
            draw_aa(aa, ax)
            #draw_aa_cent(aa, aa_part, ax)

            ax.set_xlabel('X Axis')
            ax.set_ylabel('Y Axis')
            ax.set_zlabel('Z Axis')
            ax.set_xlim3d(10, -15)
            ax.set_ylim3d(10, -15)
            ax.set_zlim3d(10, -15)
            plt.title('%s with ' % base_seq +'%s' % aa + ' %s' % aa_part)
            plt.show()
                      """
        #accumulate a full list of resultant RNA-aa pairs
#        result_nt_aa.extend(list_base_aa)

        print("Total number of interactions: " + str(len(list_base_aa)))

        #writing out output files
        #text_output(result_nt_aa)

        csv_output(list_base_aa)
        print("  Wrote output to " + outputBaseAAFG % PDB)

    writeInteractionsHTML(allInteractionDictionary,outputHTML)
