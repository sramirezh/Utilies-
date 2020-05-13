#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 11 18:03:55 2020
This set of functions to help in the analysis of the MSD to obtain the Diffusion
coefficient.

It has several different ways of parallelising the analysis to compute the 
MSD analysis.

The main idea in some of the algorithms is to compute

msd (main function)
->msd for one delta t that runs over all pairs of configurations
    -> msd for a pair of configurations


The most effective way of performing everything is to use the numpy way, which
uses the trajectory tensor and operates in the right dimensions,
See msd_np_parallel and one_delta_t_np

Example:
        An example on how to use the functions here is given in the 
        diffusion_coefficient.py inside the transport coefficients project

@author: simon
"""

import sys
import os
import multiprocessing
from tqdm import tqdm
from scipy import optimize
import matplotlib.pyplot as plt
import numpy as np
import joblib as jl
import shutil
from uncertainties import unumpy, ufloat
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))  # This falls into Utilities path
import Lammps.core_functions as cf
import Others.Statistics.FastAverager as stat

fitfunc = lambda p, x: p[0] * x + p[1]  # Fitting to a line
errfunc = lambda p, x, y, err: (y - fitfunc(p, x)) / (err + 10**-8)


def fit_line(x, y, yerr, initial_index=0):
    """
    Performs a least square fitting to a line from data including error
    
    Args:
        initial_index to avoid fitting the intial behaviour [Default=50]
        final_ration percentage of the data to be taken into account [Default=0.5]
        step take data every this step [Default=10]
        intial_index: skips all the entries before this index
        
    Return:
        pfinal coefficients of the linear fit
        cov covariance matrix of the fit
    """
    pinit = [1, -1]
    out = optimize.leastsq(errfunc, pinit, args=(x[initial_index:], y[initial_index:], yerr[initial_index:]), full_output=1)
    pfinal = out[0]  # fitting coefficients
    cov = out[1]  # Covariance
    
    return pfinal, cov    


def lammps_MSD(delta_t, data):
    """
    Function that plots the msd obtained on the fly with lammps, 
    creates "msd.pdf"

    Args:
        delta_t: from the simulations
        data: is a pandas data frame which contains in the first column the timestep
        and the second the msd measured on the fly with lammps

    Returns:
        times: Tau, the difference of times to measure each MSD 
        msd: mean square displacement
    """
    data = data.values
    times = data[:, 0] - data[0, 0]
    times = times * delta_t
    msd = data[:, 1]

    fig, ax = plt.subplots()

    ax.plot(times, msd, label="LAMMPS")

    out = np.polyfit(times, msd, 1)

    ax.plot(times, out[0] * times, label="fit")
    
    ax.legend()
    ax.set_xlabel(r'$\Delta t(fs)$')
    ax.set_ylabel(r'$MSD[{\AA}^2]$')
    plt.savefig("msd.pdf")
    D = out[0] / (2 * 3)
    error = out[1] / (2 * 3)

    print("The diffusion coefficient from Lammps MSD is %s +/- %s"%(D, error))
    
    return times, msd


def plot_diffusion(t, msd_average, msd_error, D_inst_ave, D_inst_error, pfinal, D, initial_index, dim):
    """
    Generates a subplot with the MSD vs tau at the top and the evolution
    of the instantaneous Diffusion coefficient at the bottom.
    """
    cf.set_plot_appearance()
    plt.close('all')
    fig1, (ax1,ax12) = plt.subplots(2, 1, sharex='col')
    ax1.plot(t, msd_average)
    ax1.fill_between(t, msd_average - msd_error, msd_average + msd_error, alpha=0.4)
    ax1.plot(np.unique(t), fitfunc(pfinal, np.unique(t)), linestyle='--', c='black')
    ax1.plot(t[initial_index], msd_average[initial_index], marker='o')
    ax1.set_ylabel(r'$MSD [{\AA}^2]$')
    ax1.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
    ax12.plot(t,D_inst_ave)
    ax12.fill_between(t, D_inst_ave - D_inst_error, D_inst_ave + D_inst_error, alpha=0.4)
    ax12.axhline(y=D, xmin=0, xmax=1, ls='--', c='black', label=r'$D = %2.3f$'%D)
    ax12.set_xlabel(r'$\Delta t[fs]$')
    ax12.set_ylabel(r'$D[{\AA}^2/fs]$')
    ax12.ticklabel_format(style='sci', axis='x', scilimits=(0, 0))
    plt.legend(loc="lower right", fontsize=10)
    plt.tight_layout()
    plt.subplots_adjust(wspace=0, hspace=0.1)
    plt.savefig("Diffusio_coefficient%s.pdf"%dim)
    

def compute_one_msd(pos_init, pos_final):
    """
    Computes the msd between two positons
    Returns the 3 components and the total
    """

    delta_sqr_components = (pos_final - pos_init)**2
    msd = np.average(delta_sqr_components, axis=0)
    msd = np.append(msd, np.sum(msd))

    return msd
    

def one_delta_t(delta, positions, max_delta):
    """
    returns an array with all the msd for a given delta_t
    TODO [Note that it assumes that centroids_traj and max_delta are loaded in memory, so it can be accesed by all the threads, probably not the most efficeint way of doing]
    
    Args:
        delta is the delta in sampling times that is going to be analysed
    """
    num_cores = multiprocessing.cpu_count()    
    pos = zip(positions[:max_delta], positions[delta:max_delta + delta])
    msd_array_t = jl.Parallel(n_jobs=num_cores)(jl.delayed(compute_one_msd)(*p) for p in pos)  # * unzips 

    return np.array(msd_array_t)


def one_delta_t_parallel(delta, centroids_traj, max_delta):
    """
    Returns an array with all the msd for a given delta_t
    
    Args:
        delta is the delta in sampling times that is going to be analysed

    TODO [Note that it assumes that centroids_traj and max_delta are loaded in 
    memory, so it can be accesed by all the threads, probably not the most 
    efficeint way of doing]

    """
    msd_array_t = []
    for j in range(max_delta):        
        msd_array_t.append(compute_one_msd(centroids_traj[j, :, :], centroids_traj[j + delta, :, :]))
    return msd_array_t

def msd(positions, max_delta):
    dim = np.shape(positions)
    msd_array = []
    for i in tqdm(range(1, max_delta)):
        msd_array.append(one_delta_t(i, positions, max_delta))
    # The first one is zero in all dimensions
    msd_array.insert(0,np.zeros((max_delta, dim[-1] + 1))) 
    cf.save_instance(msd_array, "msd_array")
    return msd_array



def one_delta_t_np(delta, centroids_traj, max_delta):
    """
    Numpy way of evaluating the the msd

    Args:
        centroid_traj: an numpy array containing the positions of the particles
        for each time steps, so centroid_traj[0] is an Nx3 array, where N is the
        number of particles analised.
        max delta: is the maximum tau to compute the MSD, usually this should be
        half of the maximum time_step.
        delta: is tau for the analysis in this call, the difference in time
        to measure MSD(tau)

    Retunrns:
        msd_array_t: an array with all the MSD for a given tau(delta)
    """
    
    delta_sqr_components = (centroids_traj[:max_delta][:] - centroids_traj[delta:max_delta + delta][:])**2
    msd_array_t = np.average(delta_sqr_components, axis=1)
    total = np.sum(msd_array_t, axis=1)
    total = np.reshape(total, (len(total), 1))
    
    msd_array_t = np.append(msd_array_t, total, axis=1)

    return msd_array_t


def msd_np(centroids_traj, max_delta):
    """
    Serial version
    Most efficient way using numpy
    """
    import time as t
    
    t0 = t.time()
    msd_array = []
    for i in tqdm(range(max_delta)):
        msd_array.append(one_delta_t_np(i, centroids_traj, max_delta)) 
        
    np.save("msd_array",msd_array)
    print ("the time is %s"%(t.time() - t0))
    return msd_array


def msd_np_parallel(centroids_traj, max_delta):
    """
    USing  https://joblib.readthedocs.io/en/latest/auto_examples/parallel_memmap.html
    """
    import time as t
    
    t0 = t.time()
    num_cores = multiprocessing.cpu_count()
    
    folder = './joblib_memmap'
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass
    
    data_filename_memmap = os.path.join(folder, 'data_memmap')
    jl.dump(centroids_traj, data_filename_memmap)    
    data = jl.load(data_filename_memmap, mmap_mode='r')
    
#    data = centroids_traj
    msd_array = jl.Parallel(n_jobs=num_cores)(jl.delayed(one_delta_t_np)(i, data, max_delta) for i in tqdm(range(max_delta)))
    np.save("msd_array",msd_array)
    
    try:
        shutil.rmtree(folder)
    except:  
        print('Could not clean-up automatically.')
    
    print("the time is %s"%(t.time() - t0))

    return msd_array

def msd_parallel(centroids_traj, max_delta):
    """
    """
    num_cores = multiprocessing.cpu_count()
#    folder = './joblib_memmap'
#    try:
#        os.mkdir(folder)
#    except FileExistsError:
#        pass
#
#    data_filename_memmap = os.path.join(folder, 'data_memmap')
#    jl.dump(centroids_traj, data_filename_memmap)    
#    data = jl.load(data_filename_memmap, mmap_mode='r')
#    
    data = centroids_traj
    
    msd_array = jl.Parallel(n_jobs=num_cores)(jl.delayed(one_delta_t_parallel)(i, data, max_delta) for i in tqdm(range(max_delta)))
    np.save("msd_array", msd_array)
#
#    try:
#        shutil.rmtree(folder)
#    except:  # noqa
#        print('Could not clean-up automatically.')
#        
    return msd_array


def ave_serial_no_autocorr(msd_array):
    """
    Computes the average and error without using autocorrelation or blocking 
    analysis, just np and scipy libraries
    """
    from scipy.stats import sem
    
    average = np.average(msd_array, axis=1)
    error = sem(msd_array, axis=1)
    
    ave_msd = []
    dim = 4 
    for i in range(dim):
        ave_msd.append(unumpy.uarray(average[:, i], error[:, i]))
        
    ave_msd = np.transpose(np.array(ave_msd))
    cf.save_instance(ave_msd, "ave_msd")
    return ave_msd
        
        
    
    
def ave_serial(msd_array):
    """
    Computes the average using fast_averager
    """
    ave_msd = []
    for el in tqdm(msd_array):
        ave = (stat.fast_averager(np.array(el), output_file=[]))
        ave_msd_t = []
        for ave_dim in ave:
            ave_msd_t.append(ufloat(ave_dim[1], ave_dim[3]))  # Average and blocking error 
        
        ave_msd.append(ave_msd_t)
    ave_msd = np.array(ave_msd)
    cf.save_instance(ave_msd, "ave_msd")
    
    return ave_msd
