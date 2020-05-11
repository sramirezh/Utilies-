#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 11:26:33 2020
Computes the diffusion coefficient of the molecules using MD analysis to read 
the configuration outputs

I will use copy some of the functions from:
PDP/trajectory_analysis/Diffusion_coefficient
@author: simon
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import MDAnalysis as mda
import MDAnalysis.transformations as tr
import MDAnalysis.analysis.rdf as rdf
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../')) #This falls into Utilities path
import Lammps.core_functions as cf
from scipy.spatial.distance import pdist, squareform
from tqdm import tqdm
from uncertainties import unumpy, ufloat
import Others.Statistics.FastAverager as stat
from scipy import optimize
import glob
from joblib import Parallel, delayed
import multiprocessing

def compute_one_msd(pos_init, pos_final):
    """
    Computes the msd between two positons
    Returns the 3 components and the total
    """

    delta_sqr_components = (pos_final-pos_init)**2
    msd = np.average(delta_sqr_components,axis=0)
    msd = np.append(msd,np.sum(msd))

    return msd
    

def lammps_MSD(delta_t, data):
    """
    delta_t from the simulations
    data is a pandas data frame which contains in the first column the timestep
    and the second the msd
    """


    data = data.values
    times = data[:,0]-data[0,0]
    times = times*delta_t
    msd = data[:,1]

    fig,ax = plt.subplots()

    ax.plot(times,msd,label="LAMMPS")

    out = np.polyfit(times,msd,1)

    ax.plot(times,out[0]*times,label="fit")
    
    ax.legend()
    ax.set_xlabel(r'$\Delta t(fs)$')
    ax.set_ylabel(r'$MSD[{\AA}^2]$')
    plt.savefig("msd.pdf")
    D = out[0]/(2*3)
    error = out[1]/(2*3)

    print("The diffusion coefficient from Lammps MSD is %s +/- %s"%(D,error))
    
    return times,msd


def plot_diffusion(t, msd_average, msd_error,D_inst_ave, D_inst_error, pfinal, D, initial_index):
    """
    
    """

    
    cf.set_plot_appearance()
    plt.close('all')
    fig1,(ax1,ax12)=plt.subplots(2,1, sharex='col')
    ax1.plot(t, msd_average)
    ax1.fill_between(t, msd_average-msd_error, msd_average+msd_error ,alpha=0.4)
    ax1.plot(np.unique(t),fitfunc(pfinal,np.unique(t)),linestyle='--',c='black')
    ax1.plot(t[initial_index], msd_average[initial_index], marker = 'o')
    ax1.set_ylabel(r'$MSD [{\AA}^2]$')
    ax1.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    ax12.plot(t,D_inst_ave)
    ax12.fill_between(t, D_inst_ave-D_inst_error, D_inst_ave+D_inst_error ,alpha=0.4)
    ax12.axhline(y = D, xmin=0, xmax=1,ls='--',c='black', label =r'$D = %2.3f$'%D )
    ax12.set_xlabel(r'$\Delta t[fs]$')
    ax12.set_ylabel(r'$D[{\AA}^2/fs]$')
    ax12.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
    plt.legend(loc = "lower right", fontsize = 10)
    plt.tight_layout()
    plt.subplots_adjust(wspace=0, hspace=0.1)
    plt.savefig("Diffusio_coefficient.pdf")
    
    
fitfunc = lambda p, x: p[0] * x + p[1] #Fitting to a line
errfunc = lambda p, x, y, err: (y - fitfunc(p, x)) / (err+10**-8)

def fit_line(x,y,yerr, initial_index = 50):
    """
    Performs a least square fitting to a line from data including error
    
    Args:
        initial_index to avoid fitting the intial behaviour [Default=50]
        final_ration percentage of the data to be taken into account [Default=0.5]
        step take data every this step [Default=10]
        
    Return:
        pfinal coefficients of the linear fit
        cov covariance matrix of the fit
    """
    pinit=[1,-1]
    out = optimize.leastsq(errfunc, pinit, args=(x[initial_index:],y[initial_index:],yerr[initial_index:]), full_output=1)
    pfinal = out[0] #fitting coefficients
    cov=out[1] #Covariance
    
    return pfinal,cov    
    
    
    
    


def compute_centroids():
    """
    Gets all the positions and images and saves an object with the positions of the centroids
    """
    u = mda.Universe("system.data", "dcd_nvt.dcd")  # The universe for all the atoms
    v = mda.Universe("system.data","per_image.dat", format = "LAMMPSDUMP" ) # Reading all the periodic images
    
    
    n_molecules = u.atoms.n_residues
    time_steps = u.trajectory.n_frames
    centroids_traj = np.empty((time_steps, n_molecules, 3 ))
    
    
    # =============================================================================
    #  wrapping the coordinates
    # =============================================================================
    ag = u.atoms
    transform = tr.wrap(ag)
    u.trajectory.add_transformations(transform)
    
    
    centroids_traj = np.empty((time_steps, n_molecules, 3 )) # Will contain all the centroid including the effect of the image
    
    for i,ts in enumerate(tqdm(u.trajectory[:1000], file = sys.stdout)):
        
        v.trajectory[i]    
        
        # Converting into real units including the images
        u.atoms.positions = u.atoms.positions+v.atoms.positions 
        
        centroids_traj[i, :,:] = u.atoms.residues.atoms.centroid(compound = 'residues')
        
    # universe with the real position of all the centroids 
    # Notice that this can be packed again to be inside the box with u_new.atoms.pack_into_box(box = u.dimensions)
    
#    u_new = mda.Universe.empty(n_molecules, trajectory = True)
#    u_new.load_new(centroids_traj)
    
    np.save("centroids_traj",centroids_traj)
    
    return centroids_traj, time_steps



def one_delta_t(delta, centroids_traj):
    """
    returns an array with all the msd for a given delta_t
    TODO [Note that it assumes that centroids_traj and max_delta are loaded in memory, so it can be accesed by all the threads, probably not the most efficeint way of doing]
    
    Args:
        delta is the delta in sampling times that is going to be analysed
    """
    msd_array_t = []
    for j in range(max_delta):        
        msd_array_t.append(compute_one_msd(centroids_traj[j,:,:],centroids_traj[j+delta,:,:]))
        
    
    return msd_array_t


class simulation(object):
    def __init__(self, name, ts, d, initial_index):
        self.name = name
        self.ts = ts
        self.d = d   # sampling_interval myDump
        
    def print_params(self):
        print (" Using the parameters from %s"%self.name)
        print ("\nUsing a sampling threshold (myDump) of  %s"%self.d)
        print ("Using delta_t = %s fs" %self.ts)


# =============================================================================
# Main
# =============================================================================
    
octane = simulation("octane", 1, 100, 5000 )
nitrogen = simulation("N2", 10, 100, 500 )

# this is the only thing to define
sim = octane

sim.print_params()


# Getting the centroids
if os.path.exists("centroids_traj.npy"):
    print ("Reading 'centroids_traj.npy'")
    centroids_traj = np.load("centroids_traj.npy")
    time_steps = len(centroids_traj)
else:
    centroids_traj, time_steps = compute_centroids()




max_delta = int(time_steps*0.5) #Maximum delta of time to measure the MSD as per Keffer2001

mult_t = sim.d*sim.ts
delta_t_arr = np.arange(max_delta)*mult_t
num_cores = multiprocessing.cpu_count()


# Computing the MSD array
if os.path.exists("msd_array.pkl"):
    print ("Reading msd data")
    msd_array = cf.load_instance("msd_array.pkl")
else:
    print ("Computing the msd array")
    msd_array = Parallel(n_jobs = num_cores)(delayed(one_delta_t)(i,centroids_traj) for i in tqdm(range(max_delta)))
    cf.save_instance(msd_array,"msd_array")


    



# Computing the average msd for each tau
if os.path.exists("ave_msd.pkl"):
    print ("Reading ave msd")
    ave_msd = cf.load_instance("ave_msd.pkl")
else:
    print ("Computing the average msd")
    ave_msd =[]
    for el in msd_array:
        cf.blockPrint()
        ave = (stat.fast_averager(np.array(el)))[0]
        
        ######hdre make it for each direction
        ave_msd.append(ufloat(ave[1],ave[3])) #Average and blocking error 
        cf.enablePrint()
    
    cf.save_instance(ave_msd,"ave_msd")


  
    

D_inst=[0] #Array with the instantaneous diffusion coefficient
for i in range(1,max_delta):
    dt = delta_t_arr[i]
    D_inst.append(ave_msd[i]/dt/(2*3))



#Writing arrays of averages and errors
t = np.array(delta_t_arr)
msd_error = unumpy.std_devs(ave_msd)
msd_average = unumpy.nominal_values(ave_msd)


D_inst_error = unumpy.std_devs(D_inst)
D_inst_ave = unumpy.nominal_values(D_inst)

# TODO This is a rough estimate, check that the blue point in the plot is correct
initial_index = int(len(t)*0.5)

pfinal,cov = fit_line(t,msd_average,msd_error, initial_index  = initial_index)

D = pfinal[0]/(2*3)

D_err=np.sqrt(cov[0][0])*D

plot_diffusion(t,msd_average,msd_error,D_inst_ave,D_inst_error,pfinal, D, initial_index  = initial_index )



print("\nThe diffusion coefficient is %s +/- %s [Angstrom**2/femptoseconds]"%(D,D_err))
f = open("Diffusion.out",'w')
f.write("The diffusion coefficient is %s +/- %s [Angstrom**2/femptoseconds]\n"%(D,D_err))

f.close


## =============================================================================
## From lammps chunk/msd, which only has one origin
## =============================================================================
#
#cf.set_plot_appearance()
#
delta_t = sim.ts # fs
#
#print ("Delta t in the simulations is %s"%delta_t)
#data_lammps = cf.read_data_file('diffusion_data.dat')


#times_l,msd_l = lammps_MSD(delta_t,data_lammps)



fig,ax = plt.subplots()

#ax.plot(times_l,msd_l,label="Single Origin")
ax.plot(t, msd_average, label = "Multiple Origin",ls='--')
ax.legend()
ax.set_xlabel(r'$\Delta t(fs)$')
ax.set_ylabel(r'$MSD[{\AA}^2]$')
plt.tight_layout()
plt.savefig("MSD_Lammps_comparison.pdf", transparent = True)



