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
import matplotlib.pyplot as plt
import numpy as np
from scipy import optimize
import simulation_results as sr
import pickle as pickle
from uncertainties import ufloat,unumpy
import glob
import argparse

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
            print("\ncreating the plot of %s"%prop)
            
            if "vx" in prop: 
                
                sim_bundle.plot_property(prop,fit=fit)
            
            else:
                sim_bundle.plot_property(prop)


fitfunc1 = lambda p, x: p * x  #Fitting to a line that goes through the origin
errfunc1 = lambda p, x, y, err: (y - fitfunc1(p, x)) / err #To include the error in the least squares





def mu_simulations(root_pattern, directory_pattern, box_volume,rho_bulk,cs_bulk,T_qs, T_ss):
    
    global f_mu, Q_array, bund, final_mu
    

    dictionary={'vx_Solv':r'$v^x_{f}$','vx_Solu':r'$v^x_{s}$','vx_Sol':r'$v^x_{sol}$'}

    # TODO This function could be included inside the class simulation_bundle
    #If the object was not saved
    if not glob.glob("mu.pkl"):
        print("\nAnalysing the mu grad simulations\n")
        bundles_mu = sr.initialise_sim_bundles(root_pattern,'mu',directory_pattern,dictionary)
        final_mu = sr.simulation_bundle(bundles_mu,'mu_bundle',3,cwd,dictionary = dictionary, ave = False)
        final_mu.save("mu")

    # =============================================================================
    # Calculations of the transport coefficients from DP problem
    # =============================================================================

    final_mu=cf.load_instance("mu.pkl") 
    
    final_mu.average = False
    f_mu=[] #DP body force
    Q_array=[] #Total flow
    exc_solute=[] #Excess solute flow
    count = 0
    for bund in final_mu.simulations:
        
        #This is just to compute the excess of solute flux
        
        for sim in bund.simulations:
            n_solutes=sim.get_property('cSolu')[1][0][0]
            n_solvents=sim.get_property('cSolv')[1][0][0]
            c_total = (n_solutes+n_solvents)/box_volume
            c_solutes = n_solutes/box_volume
            
            vx_solu=ufloat(sim.get_property('vx_Solu')[1][0][0],sim.get_property('vx_Solu')[1][0][1])
            J_s=c_solutes*vx_solu
            Q=ufloat(sim.get_property('vx_Sol',exact=True)[1][0][0],sim.get_property('vx_Sol',exact=True)[1][0][1])
            pref = c_total*cs_bulk/rho_bulk
            exc_sol_flux = J_s - pref * Q
            
            sim.add_property('Q',Q)
            sim.add_property('J_s',J_s)
            sim.add_property('J_s_exc',exc_sol_flux)


            
            count+=1
            
            
        
        #Getting the applied forces
        bund.add_upd_properties() # To update the bundle
        f_mu.extend(bund.get_property('mu',exact=True)[1])
        Q_array.append(bund.get_property('vx_Sol',exact=True)[1][0])
        exc_solute.append(bund.get_property('J_s_exc',exact=True)[1][0])


    final_mu.add_upd_properties()
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
    print("The transport coefficient \Gamma_{qs} is %.6f +/- %.6f"%(pfinal[0],error[0][0]))
    grad_mu=np.insert(grad_mu,0,0)
    ax.plot(np.unique(grad_mu),fitfunc1(T_qs,np.unique(grad_mu)),linestyle='--')


    ax.set_xlabel(r'$-\nabla \mu^\prime_s$')
    ax.set_ylabel(r'$Q$')
    plt.tight_layout()
    plt.savefig('Gamma_qs.pdf')



    # =============================================================================
    # \Gamma_{ss}
    # =============================================================================
    y=[i[0]for i in exc_solute]
    y_error=[i[1] for i in exc_solute]

    grad_mu=(rho_bulk/(rho_bulk-cs_bulk))*np.array(f_mu)


    fig,ax=plt.subplots()

    plt.errorbar(grad_mu,y,yerr=y_error,xerr=None,fmt='o')



    pinit=[1.0]
    out = optimize.leastsq(errfunc1, pinit, args=(grad_mu, y, y_error), full_output=1)
    pfinal = out[0] #fitting coefficients
    error = np.sqrt(out[1]) 
    print("The transport coefficient \Gamma_{ss} is %.6f +/- %.6f"%(pfinal[0],error[0][0]))
    grad_mu=np.insert(grad_mu,0,0)
    ax.plot(np.unique(grad_mu),fitfunc1(T_ss,np.unique(grad_mu)),linestyle='--')

    ax.set_xlabel(r'$-\nabla \mu^\prime_s$')
    ax.set_ylabel(r'$J_s-c_s^BQ$')
    plt.tight_layout()
    plt.savefig('Gamma_ss.pdf')
    cf.save_instance(ax,"Gamma_ss")






def p_simulations(root_pattern, directory_pattern, box_volume,rho_bulk,cs_bulk,T_sq,T_qq):
    global c_total, final_p, exc_solute


    dictionary={'vx_Solv':r'$v^x_{f}$','vx_Solu':r'$v^x_{s}$','vx_Sol':r'$v^x_{sol}$'}

    if not glob.glob("p.pkl"):

        bundles_p = sr.initialise_sim_bundles(root_pattern,'p',directory_pattern,dictionary)
        final_p = sr.simulation_bundle(bundles_p,'p_bundle',3,cwd,dictionary = dictionary, ave = False)
        final_p.save("p")


    # =============================================================================
    # Calculations for the pressure driven flow
    # =============================================================================

    final_p=cf.load_instance("p.pkl") 

    f_p=[] #Pressure body force
    exc_solute=[] #Excess solute flow
    Q_array=[] #Total flow
    p_params_dict = {} #Created a dictionary for the solutes for a given initial conf
    for bund in final_p.simulations:
        
        #Getting the applied forces
        pressure_grad = bund.get_property('p',exact=True)[1][0]
        f_p.append(pressure_grad)
        #Getting the solute excess
        for sim in bund.simulations:

            n_solutes=sim.get_property('cSolu')[1][0][0]
            n_solvents=sim.get_property('cSolv')[1][0][0]
            c_total = (n_solutes+n_solvents)/box_volume
            c_solutes = n_solutes/box_volume
            
            vx_solu=ufloat(sim.get_property('vx_Solu')[1][0][0],sim.get_property('vx_Solu')[1][0][1])
            J_s=c_solutes*vx_solu
            Q=ufloat(sim.get_property('vx_Sol',exact=True)[1][0][0],sim.get_property('vx_Sol',exact=True)[1][0][1])
            pref = c_total*cs_bulk/rho_bulk
            exc_sol_flux = J_s - pref * Q
            
            sim.add_property('Q',Q)
            sim.add_property('J_s',J_s)
            sim.add_property('J_s_exc',exc_sol_flux)
                
                
        
        bund.add_upd_properties() # To update the bundle
        Q_array.append(bund.get_property('vx_Sol',exact=True)[1][0])
        exc_solute.append(bund.get_property('J_s_exc',exact=True)[1][0])
        
            
    final_p.add_upd_properties()
    # =============================================================================
    #   \Gamma_sq
    # =============================================================================
    grad_p= np.array(f_p)  #Without the minus
    y=[i[0]for i in exc_solute]
    y_error=[i[1] for i in exc_solute]


    fig,ax=plt.subplots()

    plt.errorbar(grad_p,y,yerr=y_error,xerr=None,fmt='o')

    pinit=[1.0]
    out = optimize.leastsq(errfunc1, pinit, args=(grad_p, y, y_error), full_output=1)
    pfinal = out[0] #fitting coefficients
    error = np.sqrt(out[1]) 
    print("The transport coefficient \Gamma_{sq} is %.6f +/- %.6f"%(pfinal[0],error[0][0]))
    grad_p=np.insert(grad_p,0,0)
    ax.plot(np.unique(grad_p),fitfunc1(T_sq,np.unique(grad_p)),linestyle='--')



    ax.set_xlabel(r'$-\nabla P$')
    ax.set_ylabel(r'$J_s-c_s^BQ$')
    plt.tight_layout()
    plt.savefig('Gamma_sq.pdf')


    # Plotting the time lines 

    for time in list(p_params_dict.keys()):
        data = np.array(p_params_dict[time])
        ax.plot(data[:,0], data[:,2], alpha = 0.2)
        ax.set_xlim(0,0.0011)
        ax.set_ylim(0,0.00006)
        
    plt.savefig('Gamma_sq_times.pdf')



    # =============================================================================
    #  \Gamma_qq
    # =============================================================================
    grad_p=np.array(f_p)  #Without the minus
    y=[i[0] for i in Q_array]
    y_error=[i[1] for i in Q_array]


    fig,ax=plt.subplots()

    plt.errorbar(grad_p,y,yerr=y_error,xerr=None,fmt='o')

    pinit=[1.0]
    out = optimize.leastsq(errfunc1, pinit, args=(grad_p, y, y_error), full_output=1)
    pfinal = out[0] #fitting coefficients
    error = np.sqrt(out[1]) 
    print("The transport coefficient \Gamma_{qq} is %.6f +/- %.6f"%(pfinal[0],error[0][0]))
    grad_p=np.insert(grad_p,0,0)
    ax.plot(np.unique(grad_p),fitfunc1(T_qq,np.unique(grad_p)),linestyle='--')



    ax.set_xlabel(r'$-\nabla P$')
    ax.set_ylabel(r'$Q$')
    plt.tight_layout()
    plt.savefig('Gamma_qq.pdf')


    # Plotting the time lines 

    for time in list(p_params_dict.keys()):
        data = np.array(p_params_dict[time])
        ax.plot(data[:,0], data[:,1], alpha = 0.2)
        
        
    plt.savefig('Gamma_qq_times.pdf')












## =============================================================================
## Some tests
## =============================================================================
#
#
#grad_p=np.array(f_p)
#
#fig,ax=plt.subplots()
#
#
#y=[i[0] for i in Q_array]
#y_error=[i[1] for i in Q_array]
#
#
#plt.errorbar(grad_p,y,yerr=y_error,xerr=None,fmt='o',label=r'$Q^{Total}$')
#
#y=[i[0]for i in exc_solute]
#y_error=[i[1] for i in exc_solute]
#
#
#plt.errorbar(grad_p,y,yerr=y_error,xerr=None,fmt='o',label=r'$J_s^{exc}$')
#
#
#
## Js
#
#y=[i.get_property('J_s',True)[1][0][0] for i in final_p.simulations ]
#plt.plot(grad_p,y,'o',label=r'$J_s^{Total}$')
#
#
## Js_excess bulk
#
#
#y=[i.get_property('J_s_exc_B',True)[1][0][0] for i in final_p.simulations ]
#plt.plot(grad_p,y,'o',label=r'$J_s^{excB}$')
#
#
#ax.set_xlabel(r'$-\nabla P$')
#plt.legend()
#plt.tight_layout()
#plt.savefig('Test.pdf')





# # =============================================================================
# # Peclet number computation
# # =============================================================================

# D = 0.066 # Diffusion coefficient
# L = 2
# pe_p = []
# for bund in final_p.simulations:
#     pe_p.append(bund.get_property('Q')[1][0][0]/D * L)
#     pe_p.sort()
    
    
    
    
# # =============================================================================
# # Peclet number computation
# # =============================================================================

# pe_mu = []
# for bund in final_mu.simulations:
#     pe_mu.append(bund.get_property('Q')[1][0][0]/D * L)
#     pe_mu.sort()



def main(m_pat, p_pat, m_dir, p_dir):
    plt.close('all')
    cf.set_plot_appearance()

    


    # =============================================================================
    # Assumptions and external parameters
    # =============================================================================


    ##The following two parameters are obtained from the knowledge of the bulk properties
    # TODO this can be obtained with lammps_utilities.py, add this property to class

    box_volume = 20**3
    rho_bulk =  0.752375
    cs_bulk = 0.375332

    print("I am using the following parameters:\n box volume = %f\n rho_bulk = %f\n cs_bulk = %f\n"%(box_volume, rho_bulk, cs_bulk ))


    # Transport coefficients from GK

    # # E_3.0
    # T_sq = 0.0601964
    # T_qq = 0.3412958
    # T_qs = 0.0594056
    # T_ss = 0.0167278

    # E_1.5
    T_qq = 0.8860249969715818
    T_sq = 0.05275808785481095
    T_qs = 0.05275808785481095
    T_ss = 0.0154820979540676

    


    p_simulations(p_pat, p_dir, box_volume,rho_bulk,cs_bulk,T_sq,T_qq)
    mu_simulations(m_pat, m_dir, box_volume,rho_bulk,cs_bulk,T_qs,T_ss)


# TODO change group pattern to something more flexible as just file_names
if __name__ == "__main__":
    """
    THIS IS VERY SPECIFIC
    The arguments of this depend on the application
    """
    parser = argparse.ArgumentParser(description='Launch simulations from restart',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m_pat', metavar='m_pat',help='Generic name of the directories with mu gradient',default='mu_force_*')
    parser.add_argument('-p_pat', metavar='p_pat',help='Generic name of the directories with p gradient',default='p_force_*')
    parser.add_argument('-m_dir', metavar='m_dir',help='Patter of the files inside, in this case restart are like 202000',default='[0-9]*')
    parser.add_argument('-p_dir', metavar='p_dir',help='Patter of the files inside, in this case restart are like 202000',default='[0-9]*')
    args = parser.parse_args()

    
    main(args.m_pat,args.p_pat,args.m_dir,args.p_dir)