#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 14 09:58:32 2020
Utilities to analyse density distributions

See an example of the use in DO/EMD/analytic_resutls.py
@author: simon
"""
import numpy as np
import sys
import os
from shlex import split
import matplotlib.pyplot as plt
import linecache
import re
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../')) #This falls into Utilities path
import Lammps.core_functions as cf
import Lammps.General.Thermo_Analyser as ta
import Lammps.lammps_utilities as lu


class PropertyDistribution(object):
    """
    TODO This could be the parent class of the timestep class in chunk utilities
    """

    def __init__(self, filename, log_file = []):
        """
        
        """
        self.filename = filename
        self._get_data()
        self.log_file = []
        self._initial_check()
        self._properties()
    
    def _initial_check(self):
        """
        Checks if the required files were given
        TODO check if the filename also exists
        """
        if len(self.log_file) !=0:
            self.sim = lu.Simulation(self.log_file)


    def _get_data(self):
        self.data_frame = cf.read_data_file(self.filename)
        
    def _properties(self):
        self.properties = self.data_frame.columns



class DensityDistribution(PropertyDistribution):
    """
    Child including the simulation inside and a possible bulk region definition
    """
    
    def __init__(self, filename, bulk_name, log_file = []):
        """
        
        
        Attributes:
            properties: returns the name of the properties in the chunk
        """
        super().__init__(filename, log_file)
        self.bulk_name = bulk_name
        self._set_bulk()
        self.rho_dist = self.data_frame['density/mass'].values
        self.positions = self.data_frame['Coord1'].values
        self.rho_bulk = self.get_bulk_property('density/mass')
        self._lower_limit()
        
    
    def _lower_limit(self):
        """
        Estimates the position of the last chunk without any particles,
        Getting this for the entire fluid, gives the lower limit of the
        integrals
        """
        index = np.min(np.where(self.rho_dist>0))
        self.lower_limit = self.positions[index]
        
        
        
    def _get_data(self):
        self.data_frame = cf.read_data_file(self.filename)
        
    
    def _set_bulk(self):
        """
        
        
        """
        self.h_b, self.limits_b = lu.read_region_height(self.bulk_name,geom_file = "log.lammps")
    
    def get_bulk_property(self, name):
        """
        name is the column name, eg. density/mass
        """
        
        data = self.data_frame[name].values
        indexes = np.where((self.positions> self.limits_b[0]) & (self.positions<self.limits_b[1]))
        
        ave_property = np.average(data[indexes])
        
        return ave_property
    
    def _get_exc_con(self):
        """
        Excess concentration
        """
        self.exc_con = self.rho_dist-self.rho_bulk
        self.data_frame['exc_con'] = self.exc_con
        
        return self.exc_con
    
    def plot_property(self, property_name):
        cf.set_plot_appearance()
        fig,ax = plt.subplots()
        ax.plot(self.positions, self.data_frame[property_name].values)
        #ax.set_ylabel(r'$C_s(y)-C_s^B$')
        #ax.set_xlabel(r'$y $')
        #xmin,xmax=plt.xlim()
        #ax.set_xlim(0,zmax)
        #ax.axhline(y=0, xmin=xmin, xmax=xmax,ls='--',c='black')
        fig.tight_layout()
        property_name = property_name.replace('/','_')
        plt.savefig("%s.pdf" % (property_name) )
        
        return 0
    
    def get_gamma(self, lower_limit = 0.5, upper_limit = []):
        """
        lower_limit: For the integration, has to be from the wall.
        upper_limit: If not assumed, it will be the position of the 
        """
        
        if not upper_limit:
            upper_limit = self.limits_b[0]
            
        self._get_exc_con()
        gamma = cf.integrate(self.positions, self.exc_con, lower_limit, upper_limit)
        
        self.gamma = gamma
        
        return gamma
    
    def get_k(self, lower_limit = 0.5, upper_limit = []):
        """
        lower_limit: For the integration, has to be from the wall.
        upper_limit: If not assumed, it will be the position of the 
        """
        
        if not upper_limit:
            upper_limit = self.limits_b[0]
            
        self._get_exc_con()
        
        integrand = self.exc_con/self.rho_bulk
        k = cf.integrate(self.positions, integrand , lower_limit, upper_limit)
        
        self.k = k
        
        return k
    
    
    def get_l(self, lower_limit = 0.5, upper_limit = []):
        """
        Computes l* as described by Anderson1984
        lower_limit: For the integration, has to be from the wall.
        upper_limit: If not assumed, it will be the position of the 
        """
        
        if not upper_limit:
            upper_limit = self.limits_b[0]
            
        self._get_exc_con()
        self.get_k()
        
        integrand = self.positions * (self.exc_con/self.rho_bulk)
        l = cf.integrate(self.positions, integrand , lower_limit, upper_limit)/self.k
        
        self.l = l
        
        return l
    
    def compute_all_properties(self, lower_limit, upper_limit = []):
        
        if not upper_limit:
            upper_limit = self.limits_b[0]
            
        self.get_gamma(lower_limit, upper_limit) 
        self.get_k(lower_limit, upper_limit) 
        self.get_l(lower_limit, upper_limit) 
        
    
        
    
    def print_summary(self):
        return 0
    
    
    
    
        
