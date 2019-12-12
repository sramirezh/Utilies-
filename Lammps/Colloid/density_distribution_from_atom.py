#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 14:23:36 2019
Analyse the particle density distribution using ovito:
    
    
Useful links

https://ovito.org/manual/python/modules/ovito_data.html
https://www.ovito.org/manual/python/modules/ovito_modifiers.html

@author: sr802
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../')) #This falls into Utilities path


from Lammps.PDP.Plots.LJ_plotter import LJ
import Lammps.core_functions as cf


from ovito.modifiers import *
from ovito.io import *
import numpy as np

num_bins = 100
cutoff = 5.0

node = import_file("all.atom", multiple_frames = True)
data = node.compute(0)
list(data.particle_properties.keys())

box = data.cell
#get the simulation box sides 
L = np.diag(box.matrix)

pos = data.particle_properties.position.array

#node.add_to_scene()
#
#create_bonds_modifier = CreateBondsModifier(cutoff=cutoff, mode=CreateBondsModifier.Mode.Pairwise)
#create_bonds_modifier.set_pairwise_cutoff('Type 1', 'Type 1', cutoff)
#node.modifiers.append(create_bonds_modifier)
#node.modifiers.append(ComputeBondLengthsModifier())
#
#output = node.compute()
#hist, bin_edges = np.histogram(output.bond_properties.length.array, bins=num_bins)
#
#rho = output.number_of_particles / output.cell.volume
#factor = 4./3. * np.pi * rho * output.number_of_particles
#
#radii = bin_edges[:-1]
#radii_right = bin_edges[1:]
#rdf = hist / (factor * (radii_right**3 - radii**3))
#
#result = np.column_stack((radii,rdf))
#
#print(result)
#np.savetxt("partial_rdf.dat", result)

#
#import MDAnalysis as mda
#from MDAnalysis.coordinates import Lammps