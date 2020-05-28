#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 20 13:42:54 2020
Script to get the theoretical estimation of the diffusio-osmotic velocity

@author: simon
"""

import numpy as np
import sys
import os
from shlex import split
import matplotlib.pyplot as plt
import linecache
import re
import density_analysis as da
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../')) #This falls into Utilities path
import Lammps.core_functions as cf
import Lammps.lammps_utilities as lu


class SimulationEMD(lu.SimulationType):
    def __init__(self, name, T, eta, grad_mu_s):
        """
        name: simulation name, eg Yoshida.
        T: Reduced temperature in LJ units
        eta: viscosity of the bulk fluid
        grad_mu_s: gradient of chemical potential for the solutes
        """
        self.name = name
        self.T = T
        self.eta = eta
        self.grad_mu_s = grad_mu_s
        
       
# TODO this could be added to the class
def inner_integral(low_limit, species):
    """
    Computes the inner integral in equation (16) Anderson1984, from the lower limit
    to the beginning of the bulk as given by species.limits_b[0]
    Args:
        low_limit: The lower limit for the integral
        species: instance of the class da.DensityDistribution
    
    Returns:
        integral: the integral from the lower limit to the the start of the bulk 
    """
    integral = cf.integrate(species.positions, species.data_frame['integrand_k'], low_limit, species.limits_b[0])
    
    return integral


def vx(z, sim, species, grad_c, low_limit = []):
    """
    Computes the velocity in the x direction at the heigth z from the wall,
    as per equation (16) Anderson1984
    
    Args:
        z: Heigth from the wall in which the velocity is computed
        sim: Instance of the class SimulationEMD
        species:  instance of the class da.DensityDistribution
        grad_c: Concentration gradient of the species.
        low_limit: Lower limit of the integral
        
    Returns:
        The velocity at the given position
        
        
    """
    if not low_limit:
        low_limit = species.lower_limit
        
    integral = cf.integrate(species.positions, species.data_frame['vx_integrand'], low_limit, z) 
    vx_z = - (sim.T)*grad_c * integral / sim.eta
    return    vx_z




    
# =============================================================================
# Main
# =============================================================================
logger = cf.log(__file__, os.getcwd())    

# Write all the new types of simulations here
Yoshida = SimulationEMD("Yoshida0125", 1, 1.57, -0.125)

# Reading all the final averaged chunks
solute = da.DensityDistribution("Sproperties_short.dat",'rBulk')
solvent = da.DensityDistribution("Fproperties_short.dat",'rBulk')
fluid = da.DensityDistribution("properties_short.dat",'rBulk')

# Loading the data from the simualtion
sim_log = lu.Simulation("log.lammps")
z_wall = sim_log.limits[0, 2]

# Define the type of simulation
sim = Yoshida
sim.print_params(logger)

# =============================================================================
# Computing the analytic properties
# =============================================================================
solute.compute_all_properties(solute.lower_limit)
solvent.compute_all_properties(solvent.lower_limit)

# =============================================================================
# Getting the velocities as in Anderson1984
# =============================================================================
# For the solutes
grad_c_s = sim.grad_mu_s * solute.rho_bulk
v_0_s = - (sim.T)* solute.l*solute.k/sim.eta
vx_s = v_0_s * grad_c_s

# For the solvents
grad_mu_f = - (solute.rho_bulk / solvent.rho_bulk)* sim.grad_mu_s
grad_c_f = grad_mu_f * solvent.rho_bulk
v_0_f = - (sim.T)* solvent.l*solvent.k/sim.eta
vx_f = v_0_f * grad_c_f

vx_total = vx_s + vx_f

logger.info("The contribution to the velocity due to the solutes is %s"%vx_s)
logger.info("The contribution to the velocity due to the solvents is %s"%vx_f)
logger.info("The predicted DO velocity is  %s" % (vx_total)) 







# =============================================================================
# Getting the velocity distributions
# =============================================================================

# For the solutes
solute.data_frame['vx_integrand'] = [inner_integral(x, solute) for x in solute.positions]
solute.data_frame['vx_z'] = [vx(z, sim, solute, grad_c_s) for z in solute.positions]
    
vx_z_0 = [vx(z, sim, solute, grad_c_s, 0.000000001) for z in solute.positions]
vx_z_f = [vx(z, sim, solute, grad_c_s, solvent.lower_limit) for z in solute.positions]

# Plot comparison
cf.set_plot_appearance()
fig, ax = plt.subplots()

solute.plot_property_dist("vx_z", ax = ax)
ax.plot(solute.positions, vx_z_f)
ax.plot(solute.positions, vx_z_0)

ax.set_xlim(0, 20)
ax.set_ylim(0, None)
ax.set_xlabel(r'$z[\sigma] $')
ax.set_ylabel(r'$v_x(z)$')

fig.tight_layout()
ax.legend([r'$z_0 = %s$'%solute.lower_limit, r'$z_0 = %s$'%solvent.lower_limit, r'$z_0 = 0$'], loc = 'lower right')

fig.savefig('vprofile_theo_solutes.pdf')


# For the solvents
solvent.data_frame['vx_integrand'] = [inner_integral(x, solvent) for x in solvent.positions]
solvent.data_frame['vx_z'] = [vx(z, sim, solvent, grad_c_f) for z in solvent.positions]
    
vx_z_0 = [vx(z, sim, solvent, grad_c_f, 0.000000001) for z in solvent.positions]
vx_z_s = [vx(z, sim, solvent, grad_c_f, solute.lower_limit) for z in solvent.positions]

# Plot comparison
fig, ax = plt.subplots()

ax.plot(solvent.positions, vx_z_s)
solvent.plot_property_dist("vx_z", ax = ax)
ax.plot(solvent.positions, vx_z_0)

ax.set_xlim(0, 20)
ax.set_ylim(0, None)
ax.set_xlabel(r'$z[\sigma] $')
ax.set_ylabel(r'$v_x(z)$')

fig.tight_layout()
ax.legend([r'$z_0 = %s$'%solute.lower_limit, r'$z_0 = %s$'%solvent.lower_limit, r'$z_0 = 0$'], loc = 'lower right')

fig.savefig('vprofile_theo_solvents.pdf')


# =============================================================================
# # Plot total velocity
# =============================================================================
fig, ax = plt.subplots()
solute.plot_property_dist("vx_z", ax = ax)
solvent.plot_property_dist("vx_z", ax = ax)

total_velocity = solute.data_frame['vx_z'] + solvent.data_frame['vx_z']

ax.plot(solvent.positions,total_velocity )

ax.set_xlim(0, 20)
ax.set_ylim(0, None)
ax.set_xlabel(r'$z[\sigma] $')
ax.set_ylabel(r'$v_x(z)$')

ax.legend(["Solute", "Solvent", "Fluid"], loc = 'upper right')

fig.tight_layout()
fig.savefig('vprofile_total.pdf')



# =============================================================================
# Density, Gamma, Integrand K, Integrand L
# =============================================================================
fig,(ax1,ax2,ax3)=plt.subplots(3,1,sharex='col')

solute.plot_property_dist("density/mass", ax = ax1)
solute.plot_property_dist("rho_exc", ax = ax2)
solute.plot_property_dist("integrand_k", ax = ax3)

plt.tight_layout()
plt.subplots_adjust(wspace=0, hspace=0.1)

fig.savefig("distributions.pdf", transparent=True)




# =============================================================================
# Showing L integrand to ephasise the effect of z0
# =============================================================================

fig, ax = plt.subplots()

# Redefines the computation with the lower limit at solute's lower limit
solute.get_l(solute.lower_limit)
solute.plot_property_dist("integrand_first", ax = ax)

solute.get_l(solvent.lower_limit)
solute.plot_property_dist("integrand_first", ax = ax)

solute.get_l(0)
solute.plot_property_dist("integrand_first", ax = ax)


ax.set_xlabel(r'$z[\sigma] $')
ax.set_ylabel(r'$I_L(z)$')


ax.legend([r'$z_0 = %s$'%solute.lower_limit, r'$z_0 = %s$'%solvent.lower_limit, r'$z_0 = 0$'], loc = 'upper right')

ax = cf.plot_zoom(ax, [0,8])
ax.axhline(y=0, xmin=0, xmax=1,ls='--',c='black')
fig.tight_layout()
fig.savefig('first_moment_integrand.pdf')




