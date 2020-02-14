#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 13:50:16 2020

Plots all the density distributions generated by density distribution from atom that are in 16. DCV-SGCMC
@author: sr802
"""
import argparse
import pandas as pd
import numpy as np
import warnings
import sys
import os
import glob
from scipy import optimize

warnings.filterwarnings("ignore")


sys.path.append(os.path.join(os.path.dirname(__file__), '../../')) #This falls into Utilities path
import Lammps.core_functions as cf

import matplotlib.pyplot as plt

# Input data
Lx = 51.29928 
#External parameters 
lattice_constant = (4/0.8)**(1/3)
r_colloid  = 3.23


files = glob.glob("distribution*")

cf.set_plot_appearance()

fig,ax = plt.subplots()

markers = ['v','^','<','>','s','o','D','p']
ax.axhline(y=0.6, xmin = 0, xmax=1, ls='--',c='black')
ax.axhline(y=0.15, xmin = 0, xmax=1, ls='--',c='black')

# sorting the files by the n
a = cf.extract_digits(files)
index_files = a[1]
files = [files[i] for i in index_files]


for i,file in enumerate(files):

    data = cf.read_data_file(file).values
    x = data[:,0]
    solute_dist  = data[:,1]
    epsilon = file.strip('.dat').split('_')[-1]
    ax.plot(x,solute_dist, label=r'$\varepsilon_{cs} = %s$'%epsilon, ls = '--', marker = markers[i], ms = 5)


ax.axvspan(Lx/2-r_colloid,Lx/2+r_colloid, alpha=0.5, color='green')
ax.set_xlabel(r"$x$")
ax.set_ylabel(r"$c_s^B(x)$")
xmin,xmax = ax.get_xlim()
ymin,ymax = ax.get_ylim()
ax.set_xlim(0, x[-1]) 
ax.set_ylim(0,0.87)
#ax.axvspan(6*lattice_constant,9*lattice_constant, alpha=0.5, color='blue')
#ax.axvspan(21*lattice_constant,24*lattice_constant, alpha=0.5, color='red')

#ax.legend(loc='upper left',labelspacing=0.5,borderpad=0.4,scatteryoffsets=[0.6],
#           frameon=True, fancybox=False, edgecolor='k',ncol=2, fontsize = 10)

# For more information about the legendloc
# https://stackoverflow.com/questions/39803385/what-does-a-4-element-tuple-argument-for-bbox-to-anchor-mean-in-matplotlib
#ax.legend(loc= 1,labelspacing=0.2,borderpad=0.4,scatteryoffsets=[0.2],
#           frameon=True, fancybox=False, edgecolor='k',ncol=3, fontsize = 14, 
#           columnspacing = 0.5, bbox_to_anchor=(0.025, 0.42, 0.95, 0.6), mode="expand")
plt.tight_layout()
plt.savefig("conc_chunks_%s.pdf"%(i+1), transparent = True)



#ax.plot(x,rho_solu_c, label='Solutes', ls = '--')
#ax.plot(x,rho_solv_c, label='Solvents', ls = '--')
##ax.plot(x, rho_total_c, label='Total')  
#ax.axhline(y=0.6, xmin = 0, xmax=1, ls='--',c='black')
#ax.axhline(y=0.15, xmin = 0, xmax=1, ls='--',c='black')
##ax.axvline(x=L[0]/2, ymin = 0, ymax=1, ls=':',c='black')
#ax.set_xlim(0, L[0])   
#
##ax.axvspan(6*lattice_constant,9*lattice_constant, alpha=0.5, color='blue')
##ax.axvspan(21*lattice_constant,24*lattice_constant, alpha=0.5, color='red')
#
#ymin,ymax=ax.get_ylim()
#ax.set_ylim(0,ymax*1.3)
#

#ax.legend()
#plt.tight_layout()
#plt.savefig("conc_chunks.pdf")
#
#
#epsilon =os.getcwd().split('/')[-1]