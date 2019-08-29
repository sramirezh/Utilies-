#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  1 17:35:55 2019

Gathers the flow from diffusio-osmotic simulations, both from Pressure and chemical potential simulations
Uses the classes in simulation_results.py

@author: sr802
"""

import os
import sys
Utilities_path=os.path.join(os.path.dirname(__file__), '../../../')
sys.path.append(Utilities_path) #This falls into Utilities path
import Lammps.core_functions as cf
import Others.Statistics.FastAverager as stat
import Lammps.General.Log_Analysis.Thermo_Analyser as thermo
import matplotlib.pyplot as plt
import numpy as np
import copy
import re
from scipy import optimize
import simulation_results as sr
import cPickle as pickle
from uncertainties import ufloat,unumpy
import glob
try:
    from uncertainties import ufloat
except ImportError as err2:
    print err2

cwd = os.getcwd() #current working directory


def specific_plot_all(sim_bundle,fit=True):
    """
    Very specific function
    Plots all the properties but only fits to a line the velocities
    Args:
        simulation_bundle
    """
    
    #Copy of plot_all_properties
    for i,prop in enumerate(sim_bundle.simulations[-1].property_names):
        
        if prop!="time" and i>0:
            print "\ncreating the plot of %s"%prop
            
            if "vx" in prop: 
                
                sim_bundle.plot_property(prop,fit=fit)
            
            else:
                sim_bundle.plot_property(prop)


fitfunc1 = lambda p, x: p * x  #Fitting to a line that goes through the origin
errfunc1 = lambda p, x, y, err: (y - fitfunc1(p, x)) / err #To include the error in the least squares
        
# =============================================================================
# main 
# =============================================================================
plt.close('all')

## =============================================================================
## Chemical potential simulations
## =============================================================================
#
root_pattern="mu_force*"
directory_pattern='[0-9]*'
parameter_id='mu'

dictionary={'vx_Solv':r'$v^x_{f}$','vx_Solu':r'$v^x_{s}$','vx_Sol':r'$v^x_{sol}$'}

# TODO This function could be included inside the class simulation_bundle
#If the object was not saved
if not glob.glob("mu.pkl"):
    bundles_mu=sr.initialise_sim_bundles(root_pattern,parameter_id,directory_pattern,dictionary)
    final_mu=sr.simulation_bundle(bundles_mu,parameter_id,3,cwd,dictionary=dictionary)
    final_mu.save("mu")











## =============================================================================
## Pressure simulations
## =============================================================================
#

root_pattern="p_force*"
directory_pattern='[0-9]*'
parameter_id='p'

dictionary={'vx_Solv':r'$v^x_{f}$','vx_Solu':r'$v^x_{s}$','vx_Sol':r'$v^x_{sol}$'}

if not glob.glob("p.pkl"):

    bundles_p=sr.initialise_sim_bundles(root_pattern,parameter_id,directory_pattern,dictionary)
    final_p=sr.simulation_bundle(bundles_p,parameter_id,3,cwd,dictionary=dictionary)
    final_p.save("p")


##The following two parameters are obtained from the knowledge of the bulk properties
box_volume=8000 
rho_bulk=0.752375
cs_bulk=0.375332

cf.set_plot_appearance()




# =============================================================================
# Calculations for the pressure driven flow
# =============================================================================

final_p=cf.load_instance("p.pkl") 


f_p=[] #Pressure body force
exc_solute=[] #Excess solute flow
Q_array=[] #Total flow
n_s_array = []
for bund in final_p.simulations:
    
    #Getting the applied forces
    f_p.extend(bund.get_property('p',exact=True)[1])
    #Getting the solute excess
    exc_sol_array=[]
    for sim in bund.simulations:

        n_solutes=sim.get_property('cSolu')[1][0][0]
        n_s_array.append(n_solutes)
        n_solvents=sim.get_property('cSolv')[1][0][0]
        n_total=n_solutes+n_solvents
        vx_solu=ufloat(sim.get_property('vx_Solu')[1][0][0],sim.get_property('vx_Solu')[1][0][1])
        J_s=n_solutes/box_volume*vx_solu
        Q=ufloat(sim.get_property('vx_Sol',exact=True)[1][0][0],sim.get_property('vx_Sol',exact=True)[1][0][1])
        exc_sol_flux=J_s-cs_bulk*Q
        
        exc_sol_array.append(exc_sol_flux)
    Q_array.append(bund.get_property('vx_Sol',exact=True)[1][0])
    exc_solute.append(sum(exc_sol_array)/len(exc_sol_array))
    

# =============================================================================
#   \Gamma_sq
# =============================================================================
grad_p=rho_bulk*np.array(f_p)  #Without the minus
y=[i.n for i in exc_solute]
y_error=[i.s for i in exc_solute]


fig,ax=plt.subplots()

plt.errorbar(grad_p,y,yerr=y_error,xerr=None,fmt='o')

pinit=[1.0]
out = optimize.leastsq(errfunc1, pinit, args=(grad_p, y, y_error), full_output=1)
pfinal = out[0] #fitting coefficients
error = np.sqrt(out[1]) 
print "The transport coefficient \Gamma_{sq} flow is %s +/- %s"%(pfinal[0],error[0][0])
grad_p=np.insert(grad_p,0,0)
ax.plot(np.unique(grad_p),fitfunc1(pfinal,np.unique(grad_p)),linestyle='--')



ax.set_xlabel(r'$-\nabla P$')
ax.set_ylabel(r'$J_s-c_s^BQ$')
plt.tight_layout()
plt.savefig('Gamma_sq.pdf')


# =============================================================================
#  \Gamma_qq
# =============================================================================
grad_p=rho_bulk*np.array(f_p)  #Without the minus
y=[i[0] for i in Q_array]
y_error=[i[1] for i in Q_array]


fig,ax=plt.subplots()

plt.errorbar(grad_p,y,yerr=y_error,xerr=None,fmt='o')

pinit=[1.0]
out = optimize.leastsq(errfunc1, pinit, args=(grad_p, y, y_error), full_output=1)
pfinal = out[0] #fitting coefficients
error = np.sqrt(out[1]) 
print "The transport coefficient \Gamma_{qq} is %s +/- %s"%(pfinal[0],error[0][0])
grad_p=np.insert(grad_p,0,0)
ax.plot(np.unique(grad_p),fitfunc1(pfinal,np.unique(grad_p)),linestyle='--')



ax.set_xlabel(r'$-\nabla P$')
ax.set_ylabel(r'$Q$')
plt.tight_layout()
plt.savefig('Gamma_qq.pdf')


# =============================================================================
# Calculations of the transport coefficients from DP problem
# =============================================================================

final_mu=cf.load_instance("mu.pkl") 

f_mu=[] #DP body force
Q_array=[] #Total flow
exc_solute=[] #Excess solute flow
count = 0
for bund in final_mu.simulations:
    
    #This is just to compute the excess of solute flux
    exc_sol_array=[]
    
    for sim in bund.simulations:
        vx_solu=ufloat(sim.get_property('vx_Solu')[1][0][0],sim.get_property('vx_Solu')[1][0][1])
        J_s=n_s_array[count]/box_volume*vx_solu
        Q=ufloat(sim.get_property('vx_Sol',exact=True)[1][0][0],sim.get_property('vx_Sol',exact=True)[1][0][1])
        exc_sol_flux=J_s-cs_bulk*Q
        exc_sol_array.append(exc_sol_flux)

        
        count+=1
        
        
    
    #Getting the applied forces
    f_mu.extend(bund.get_property('mu',exact=True)[1])
    Q_array.append(bund.get_property('vx_Sol',exact=True)[1][0])
    exc_solute.append(sum(exc_sol_array)/len(exc_sol_array))



# =============================================================================
# \Gamma_{qs}
# =============================================================================


y=[i[0] for i in Q_array]
y_error=[i[1] for i in Q_array]

grad_mu=(rho_bulk/(rho_bulk-cs_bulk))*np.array(f_mu)


fig,ax=plt.subplots()

plt.errorbar(grad_mu,y,yerr=y_error,xerr=None,fmt='o')



pinit=[1.0]
out = optimize.leastsq(errfunc1, pinit, args=(grad_mu, y, y_error), full_output=1)
pfinal = out[0] #fitting coefficients
error = np.sqrt(out[1]) 
print "The transport coefficient \Gamma_{qs} is %s +/- %s"%(pfinal[0],error[0][0])
grad_mu=np.insert(grad_mu,0,0)
ax.plot(np.unique(grad_mu),fitfunc1(pfinal,np.unique(grad_mu)),linestyle='--')


ax.set_xlabel(r'$-\nabla \mu^\prime_s$')
ax.set_ylabel(r'$Q$')
plt.tight_layout()
plt.savefig('Gamma_qs.pdf')



# =============================================================================
# \Gamma_{qq}
# =============================================================================
y=[i.n for i in exc_solute]
y_error=[i.s for i in exc_solute]

grad_mu=(rho_bulk/(rho_bulk-cs_bulk))*np.array(f_mu)


fig,ax=plt.subplots()

plt.errorbar(grad_mu,y,yerr=y_error,xerr=None,fmt='o')



pinit=[1.0]
out = optimize.leastsq(errfunc1, pinit, args=(grad_mu, y, y_error), full_output=1)
pfinal = out[0] #fitting coefficients
error = np.sqrt(out[1]) 
print "The transport coefficient \Gamma_{ss} is %s +/- %s"%(pfinal[0],error[0][0])
grad_mu=np.insert(grad_mu,0,0)
ax.plot(np.unique(grad_mu),fitfunc1(pfinal,np.unique(grad_mu)),linestyle='--')

ax.set_xlabel(r'$-\nabla \mu^\prime_s$')
ax.set_ylabel(r'$J_s-c_s^BQ$')
plt.tight_layout()
plt.savefig('Gamma_ss.pdf')



