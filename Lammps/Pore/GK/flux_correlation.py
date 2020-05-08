# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 17:22:14 2019
Contains the classes flux and correlation that help to compute correlations
@author: sr802
"""
import multiprocessing
import numpy as np
from tqdm import tqdm
from joblib import Parallel, delayed
import pickle as pickle
import Lammps.core_functions as cf
from scipy.stats import sem
import uncertainties as un
from statsmodels.tsa.stattools import acf, ccf
import time as t
# =============================================================================
# Class definition
# =============================================================================


class flux(object):
    """
    Flux is a vectorial or scalar entity
    """

    def __init__(self, components, times, name):
        """
        Args:
            Components: is a matrix( or vector) containing the time series of 
            the components in [x,y,z]
            Name: Is the name that is going to appear in the plots in latex 
            format, example "r'J_s-c_s^BQ'"
        """

        self.components = components
        self.name = name
        self.times = times
        self._reshape()

    def _reshape(self):
        """
        If it is a single column, it will reshape it into a matrix with one 
        column
        """

        shape = np.shape(self.components)

        if len(shape) == 1:
            self.components = np.reshape(self.components, 
                                         (len(self.components), 1))
            self.dimension = 1

        else:
            self.dimension = shape[1]
        

class correlation(object):
    """
    TODO, I could compute all the correlations for the given delta just with
    one np.cov

    Attributes:
        flux1: Instances from the class flux
        flux2: Instances from the class flux
        max_delta: is the maximum tau to compute correlations <v(\tau) v(0)>
        cor: contains the correlations as an array, the components
            are x,y,z, and total in 3D
        norm: normalisation factor for each dimension  t=0 (var1(0) var2(0))
        cor_norm: list to store the normalised correlations, the last is the
            total




    """
    def __init__(self, flux1, flux2, max_delta):
        """
        Args:
            flux1 and flux2 are instances of the class flux
            max_delta is the index of the maximum \tau for the analysis
            
        """
        self.flux1 = flux1
        self.flux2 = flux2
        self.max_delta = max_delta   
        self.initial_check()
        dimension = self.dimension
        self.cor = (dimension + 1) * [0]  
        self.norm = (dimension + 1) * [0]  
        self.cor_norm = (dimension + 1) * [0]  
        self.dic_label = {0: 'x', 1: 'y', 2: 'z', self.dimension: 'Total'}
        
    def initial_check(self):
        """Checks if the time series are equal and the fluxes have the same
        number of components
        """
        self.dimension = self.flux1.dimension
        if self.flux1.dimension != self.flux2.dimension:
            print("The fluxes do not have the same dimension")
        else:
            self.dimension = self.flux1.dimension
            
        if self.flux1.times.all != self.flux2.times.all:
            print("The fluxes were not measured for the same times")
        else:
            self.times = self.flux1.times[:self.max_delta]
            
    def correlate_one_d(self, dim):
        """Performs a correlation between 1d components by evaluating the
        products at at different delta t.
        Args:
            dim is the component to be evaluated
        """
        num_cores = multiprocessing.cpu_count()
        var1 = self.flux1.components[:, dim]
        var2 = self.flux2.components[:, dim]
        cor = Parallel(n_jobs=num_cores)(delayed(compute_correlation_dt)
                                         (var1, var2, i) for i in tqdm(range(self.max_delta)))
        norm = cor[0]
        self.norm[dim] = norm
        self.cor[dim] = np.array(cor)
        self.cor_norm[dim] = np.array(cor) / norm
   
    def evaluate(self):
        """
        Performs the correlations of the 1d components,calling
        correlate_one_d, and adds them up to the total.
        
        """
        total = np.zeros(self.max_delta)
        for dim in range(self.dimension):
            self.correlate_one_d(dim)
            total = total + self.cor[dim]
        total = total / 3
        self.cor[-1] = total
        self.norm[-1] = total[0]
        self.cor_norm[-1] = total / total[0]

    def evaluate_acf(self):
        """
        Performs the Autocorrelation of the 1d components,using 
        statsmodels.tsa.stattools.acf
        See my ipython about autocorrelation and GK
        TODO: Include the error
        """
        total = np.zeros(self.max_delta)
        for dim in range(self.dimension):
            print("started the analysis for %s"%dim)
            t0 = t.time()
            x = self.flux1.components[:, dim]
            acf_array, confidence = acf(x, nlags = len(self.times[:self.max_delta])-1, fft = True, alpha = 0.05)
            amplitude = np.correlate(x,x)/len(x)
            self.norm[dim] = amplitude
            self.cor[dim] = amplitude * acf_array
            self.cor_norm[dim] = acf_array

            total = total + self.cor[dim]
            print (t.time()-t0)
        
        total = total / 3
        self.cor[-1] = total
        self.norm[-1] = total[0]
        self.cor_norm[-1] = total / total[0]


    def evaluate_ccf(self):
        """
        Performs the correlation of the 1d components,using 
        statsmodels.tsa.stattools.ccf
        See my ipython about autocorrelation and GK
        """
        total = np.zeros(self.max_delta)
        for dim in range(self.dimension):
            print ("started the analysis for %s"%dim)
            t0 = t.time()
            x = self.flux1.components[:, dim]
            y = self.flux2.components[:, dim]
            ccf_array = ccf(x, y)[:len(self.times)]
            amplitude = np.correlate(x,y)/len(x)
            self.norm[dim] = amplitude
            self.cor[dim] = amplitude * ccf_array
            self.cor_norm[dim] = ccf_array

            total = total + self.cor[dim]
            print (t.time()-t0)
        
        total = total / 3
        self.cor[-1] = total
        self.norm[-1] = total[0]
        self.cor_norm[-1] = total / total[0]
        
    def plot_individual(self, fig, ax, dim=0, alpha=0.4, every=1, norm=True):
        """
        Args:
            ax axes object
            fig Figure
            dim is the dimension, for example:in a 3D vector, 0-x, 1-y, 2-z
            and 3-total.
            alpha is the transparency of the filling
            every to not have so many points
            norm True if normalised
            The axis label is given here but it could be renamed later
        """
        if norm == True:
            cor = self.cor_norm[dim]
        else:
            cor = self.cor[dim]
            
        # If the correlation has error estimation    
        if isinstance(cor[0], un.UFloat):
    
            y = np.array([i.n for i in cor])
            y_error = np.array([i.s for i in cor])
            ax.plot(self.times[::every], y[::every], label=self.dic_label[dim])
            ax.fill_between(self.times, y - y_error, y + y_error, alpha=0.4)
        
        else:
            ax.plot(self.times[::every], cor[::every], 
                    label=self.dic_label[dim])
            
        return fig, ax
    
    def plot_all(self, fig, ax, alpha=0.4, norm=True):
        for dim in range(self.dimension + 1):
            fig, ax = self.plot_individual(fig, ax, dim, norm=norm)
        
        ax.axhline(y=0, xmin=0, xmax=1, ls=':', c='black')
        ax.set_ylabel(r'$\langle %s(t)%s(0) \rangle$'%(self.flux1.name, 
                                                       self.flux2.name))
        ax.set_xlabel('time')
        return fig, ax
    
    def save(self, file_name):
        """
        Saves the instance
        """
        afile = open(r'%s.pkl'%file_name, 'wb')
        pickle.dump(self, afile)
        afile.close()

    def transport_coeff(self, pref, xmin, xmax):
        """
        Returns
        The transport coefficient in the
        pref is the prefactor, eg.system volume etc
        xmin
        """
        integral = cf.integrate(self.times, self.cor[-1], xmin, xmax)
        self.coeff = (pref) * integral
        return self.coeff


class bundle_correlation(correlation):
    """
    The bundle is made of an array of correlations
    """
    def __init__(self, array, times, flux1_name, flux2_name):
        self.arrays = array
        self.averaging()
        self.dimension = 1
        self.times = times
        self.norm = self.cor[0].nominal_value
        self.cor_norm = [self.cor / self.norm]
        self.flux1_name = flux1_name
        self.flux2_name = flux2_name

    def averaging(self):
        ddof = 1
        array = self.arrays
        if len(array):
            ddof = 0
        self.cor = un.unumpy.uarray(np.average(array, axis=0), sem(array,
                                    axis=0, ddof=ddof))
           
    def plot(self, fig, ax, dim=0, alpha=0.4, every=1, ax_label=True,
             norm=True):
        """
        Args:
            ax: axes object
            fig: Figure
            dim: is the dimension,
            for example:in a 3D vector, 0-x, 1-y, 2-z and 3-total.
            alpha: is the transparency of the filling
            every: to not have so many points
            norm: True if normalised
            ax_label: The axis label is given here but it could be renamed
                      later
        """
        if norm == True:
            cor = self.cor_norm[dim]
        else:
            cor = self.cor[dim]

        y = np.array([i.n for i in cor])
        y_error = np.array([i.s for i in cor])
        ax.plot(self.times[::every], y[::every])
        ax.fill_between(self.times, y - y_error, y + y_error, alpha=0.4)

        # It mostly means that the plot will not be further used, for example 
        # not used to compare correlations
        if ax_label == True:
            ax.axhline(y=0, xmin=0, xmax=1, ls=':', c='black')
            ax.set_ylabel(r'$\langle %s(t)%s(0) \rangle$'%(self.flux1_name, 
                                                           self.flux2_name))
            ax.set_xlabel(r'$\log (t)$ ')

        return fig, ax
       

def compute_correlation_dt(var1, var2, delta):
    """
    This is a VERY GENERAL function
    
    *****
    It is important to keep it outside the class as it is going to be 
    evaluated in parallel and if it is a method of the class, it would require
    to load the instance on each processor which could be very expensive
    *****
    
    Computes the correlation for two variables for a given delta t
    Args:
        var1: time series for the first variable 
        var2: time series for the first variable
        Note that var1 and var2 have to have the same time series
        delta: every this number of steps, we take the variable 2 to compute 
        the correlation
    """
    # cf.blockPrint()
    if delta != 0:
        cor = np.cov(var1[:-delta], np.roll(var2[:-delta], 
                     - delta, axis=0))[0][1]
    else:
        cor = np.cov(var1, var2)[0][1] 

    # cf.enablePrint()
    # Covariance need to be reduced as it returns a matrix
    return cor
