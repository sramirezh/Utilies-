"""
Created on 10 October 20202
Including all the functios and classes to fit and predict using fitted polynomials
@author: simon
"""
import os
import sys
import numpy as np
import argparse
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from cycler import cycler
import shutil
import pandas as pd
Utilities_path=os.path.join(os.path.dirname(__file__), '../../')
sys.path.append(Utilities_path) #This falls into Utilities path
import Lammps.core_functions as cf

# =============================================================================
# Class definition
# =============================================================================

# TODO this coulb be the general class that has the sum of polynomials 
class FitClass:
    
    """
    A class to facilitate the fitting by adding parameters that can be called
    with self.foo instead of the traditional fitting function descrived in
    the documentation of curve_fit
    
    https://stackoverflow.com/questions/49813481/how-to-pass-parameter-to-fit-function-when-using-scipy-optimize-curve-fit/49813634#49813634
    """

    def __init__(self, poly):
        """
        poly: Instance from the polynomial class
        """
        self.poly = poly # could be an array of polymers
        self.get_dim()
        
    
    def get_dim(self):
        """
        Extracts the number of independent functions to fit with the same
        parameters
        Assumes that if its not a list, there is just one polynomial
        """
        self.dim = 0 
        if not isinstance(self.poly, Polynomial):
            self.dim = len(self.poly)
    

    def fit_func(self, x, *fit_coeff):
        
        n, m = np.shape(x)
        length = int(m / self.dim)
    
        # Unwrapping the data for each quantity
        data = chunks(x, length)
    
        polynomials = self.poly
        
        total = []
        for i in range(self.dim):
            total.extend(arbitrary_poly([data[i],polynomials[i]], fit_coeff))
        
        return total



class Polynomial(object):
    """
    Class to identify a polynomial 
    
    p(x,y) = \sum_{i,j}^{n,m} [ f1n(i) f2m(j) c_{i,j} x^{f_3n(i)} y^{f_4m(i)}
    
    with fi additional functions that are independen of the fitting coefficient
    """
    
    def __init__(self, n,m,fn,fm,f_expx,f_expy,exc_n=[],exc_m=[]):
        """
        
        Args:
            n is the exponent in x
            m is the exponent in y
            exc_n are the excluded exponents in x
            exc_m are the excluded exponents in y
            fn array describing a poly to describe f(n) that is independent of c_{nm}
            fm array describing a poly to describe f(m) that is independen independent of c_{nm}
            anm is the matrix with the fitting coefficients
            f_expx array describing the function that generates the exponent of x
            f_expy array describing the function that generates the exponent of y
            
            fn,fm,f_an,f_am are going to be evaluated with np.polyval, so see the syntaxis
        
        """
        self.exponents=[get_list(n),get_list(m)]
        self.excluded=[get_list(exc_n),get_list(exc_m)]
        self.get_limits()
        self.get_exponents()
        self.get_dimensions()
        self.func_coeff=[fn,fm]
        self.func_exp=[f_expx,f_expy]
        self.anm = []
        
    
        
    def get_limits(self):
        limits=[]
        for exp in self.exponents:
            if len(exp) == 1:
                exp = [0,exp[0]]
            limits.append(exp)
        self.limits = limits
        
        
    
    def get_exponents(self):
        """
        creates the list of exponents in the i-th dimension, exluding the given exponents
        
        """
        for i,lim in enumerate(self.limits):
            exponents=np.arange(lim[0],lim[-1]+1)
            if len(self.excluded[i])!=0:
                exponents=delete_values(exponents,self.excluded[i])
            self.exponents[i]=exponents
        return self.exponents
    
    def get_dimensions(self):
        self.get_exponents()
        dimensions=[]
        for exp in self.exponents:
            dimensions.append(len(exp))
        self.dim=dimensions
        
    
    def print_function(self):
        """
        Creates a polymer
        pijx^iy^j with i of i=0,...,n, j=0,...,m
        
        Args:
            params: coefficients
            data: contains the the two independent variables x and y
            
            pijx^iy^j
        
        """
        ndim,mdim=self.dim
        for i,n in enumerate(self.exponents[0]):
            for j,m in enumerate(self.exponents[1]):
                
                #Getting the n,m dependent coefficients and exponents
                coeff_n = poly_coeff(self.func_coeff[0],n)
                coeff_m = poly_coeff(self.func_coeff[1],m)
                x_exp = poly_coeff(self.func_exp[0],n)
                y_exp = poly_coeff(self.func_exp[1],m)
                print('%s  %s c_{%s %s} x^{%s} y^{%s} +'%(coeff_n,coeff_m,n,m,x_exp,y_exp))

# =============================================================================
# Things not belonging to the class (This can be adapted to the problem)
# =============================================================================



def chunks(data, l):
    """
    Yield successive n-sized chunks from lst
    Args:
        data numpy array 
        n length of the chunks
    
    """
    n, m = np.shape(data)
    return [data[:, i:i + l] for i in range(0, m, l)]

def poly_coeff(func, point):
    """
    Returns the function f1(n), f2(m), f3(n) and f4(m) that appear in my notebook
    
    function is the list of exponents as described in polyval
    point is the value of n or m
    
    """

    f = np.polyval(func, point)
    
    return f


def arbitrary_poly(data, a_nm):
    """
    evaluates the polynomial
    p(x,y)=\sum_{i,j}^{n,m} [ fn(i) fm(j) c_{i,j} x^{f_expx(i)} y^{f_expy(i)}
    
    at at the point x, y 
    
    Args:
        coefficients: all the fitting coefficients a_nm
        data: contains the the two independent variables x and y and an instance of the polynomial class containing all the information of it

    """
     
    points = data[0]
    x = points[0]
    y = points[1]
    poly = data[1]
    ndim,mdim = poly.dim
    a_nm = np.reshape(a_nm,(ndim,mdim))
    f_eval = 0
    
#    print 'Inside arbitraty poly %s %s'%(np.shape(x),np.shape(y))
    
    for i,n in enumerate(poly.exponents[0]):
        for j,m in enumerate(poly.exponents[1]):
            
            #Getting the n,m dependent coefficients and exponents
            f1_n = poly_coeff(poly.func_coeff[0],n)
            f2_m = poly_coeff(poly.func_coeff[1],m)
            if f1_n  == 0 or f2_m  == 0:
                pass
            else: 
                f3_n = poly_coeff(poly.func_exp[0],n)
                f4_m = poly_coeff(poly.func_exp[1],m)
                f_eval += a_nm[i, j] * f1_n * f2_m * x ** (f3_n) * y ** (f4_m)
    return f_eval


def fit_general(*wrapped_data):
    """
    General fitting that can take any number of polynomials
    
    Args:
        wrapped_data: should contains a list of [data_i]  with data_i = [[x,y,z,zerr],poly]
        where i runs over the number of polynomials 
    """
    #Unwrapping the data and stacking accordingly
    poly = [el[1] for el in wrapped_data]
    data = np.hstack((el[0] for el in wrapped_data))

    x, y, z, zerr = data

    variables = data[:2,:]

    # All the polynomials need to have the same a_nm
    ndim, mdim = poly[0].dim
    
    # TODO this could be moved outside to make it more general
    fit = FitClass(poly)
    
    popt, pcov = curve_fit(fit.fit_func, variables[:,:] , z, sigma = zerr, p0=[0] * ndim * mdim )
    popt_matrix=np.reshape(popt,(ndim,mdim))
    
    return popt_matrix, pcov, variables


def fit_sum_poly(x,y,z,zerr,poly):
    """
    fits a polynomial using least square fitting
    the coefficients are pijx^i*y^j
    Args:
        x array containing the first variable 
        y array containing the second variable
        z array with the dependent variable
        zerr sigma on the dependent variable
        d degree of the polynomial
    
    Returns:
        popt: Optimal fitting coefficients.
        pcov: Covariant matrix of the fitting.
    """

    ndim,mdim=poly[0].dim
    variables=np.stack((x,y),axis=0)
    popt, pcov = curve_fit(poly_sum, variables[:,:], z, sigma=zerr,p0=[0]*ndim*mdim)
    popt_matrix=np.reshape(popt,(ndim,mdim))
    return popt_matrix,pcov,variables

def outputs(popt_matrix, pcov,e_results, n, m, name):
    
    print("\nCreated coefficients.dat containing all the fitting coefficients")
    np.savetxt('coefficients.dat', popt_matrix)
    print("\nCreated covariant.dat with the covariant matrix of the fitting")
    np.savetxt('covariant.dat', pcov)
    print("\nCreated error.dat containing the relative error between the property and the prediction given by the fitting evaluated at the same input points")
    header='%s\t%s_predicted\trelative_error'%(name,name)
    np.savetxt('error_%s.dat'%name,e_results, header=header,fmt='%12.8f')


def test_prediction(popt,variables,z,poly,ref_prop):
    """
    
    Args:
        popt is the fitting coefficient matrix
        ref_prop is the reference property value
    
    Returns:
        
        Results with [z+z_ref, z_predict+z_ref, error]
    """
    m,n_point=np.shape(variables)
    z_predict=[]
    popt=np.reshape(popt,(np.size(popt)))
    
    for i in range(n_point):
        if np.size(poly)==1:
            z_predict.append(arbitrary_poly([variables[:,i],poly],popt))
        else:
            z_predict.append(poly_sum(variables[:,i],popt))
        
#        print z_predict,z[i]
    z_predict=np.array(z_predict)

    error=np.abs((z-z_predict)/(z+ref_prop))*100
    
    results=np.transpose(np.vstack((z+ref_prop,z_predict+ref_prop,error,variables[0,:],variables[1,:])))
    
    return results


def arbitrary_poly_check(data, *params):
    """
    Creates a polymer
    p(x,y)=\sum_{i,j}^{n,m} [ fn(i) fm(j) c_{i,j} x^{f_expx(i)} y^{f_expy(i)}
    
    Args:
        params: all the fitting parameters
        data: contains the the two independent variables x and y and an instance of the polynomial class containing all the information of it

    """
    
    points=data[0]
    x=points[0]
    y=points[1]
    poly=data[1]
    ndim,mdim=poly.dim
    params=np.reshape(params,(ndim,mdim))
    function=0
    
#    print 'Inside arbitraty poly %s %s'%(np.shape(x),np.shape(y))
    
    for i,n in enumerate(poly.exponents[0]):
        for j,m in enumerate(poly.exponents[1]):
            
            #Getting the n,m dependent coefficients and exponents
            coeff_n = poly_coeff(poly.func_coeff[0],n)
            coeff_m = poly_coeff(poly.func_coeff[1],m)
            if coeff_m==0 or coeff_n==0:
                function+=0
            else: 
                x_exp = poly_coeff(poly.func_exp[0],n)
                y_exp = poly_coeff(poly.func_exp[1],m)
                print(params[i,j]*coeff_n*coeff_m*x**(x_exp)*y**(y_exp))
                function+=params[i,j]*coeff_n*coeff_m*x**(x_exp)*y**(y_exp)
    return function


def poly_sum(data,*params):
    """
    Adds two arbitrary polynomials, 
    BECAREFUL added poly_p by hand
    """
    points=data
    poly=poly_p
    
    res1=arbitrary_poly([points,poly[0]],params)
    res2=rho_ref*arbitrary_poly([points,poly[1]],params)
    return res1+res2



def get_list(a):
    """
    Converts to a list if it is not
    """
    if isinstance(a,list):
        return a
    else:
        return [a]
    
    
def delete_values(vector,delete_val):
    """
    Delete values from a vector 
    
    args:
        vector with all values from which you are going to delete
        delete_val values to delete from value
    """
    indexes = []
    
    for val in delete_val:
        indexes.append(np.where(vector == val)[0])
    
    vector = np.delete(vector, np.array(indexes))
    
    return vector


def p_known(x,y):
    """
    known function for testing porpouses
    """
    z=3*x*y**2+4*y*x**2+5*x**2
    return z


def build_example(n_points=1000):
    """
    creates an example data file with the structure of the input
    """

    x=np.linspace(1,3,n_points)
    y=np.linspace(1,3,n_points)
    z=p_known(x,y)
    zerr= np.random.rand(n_points)
    
    data=np.column_stack([x,y,z,zerr])
    
    header='# density Temperature property sigma_property'
    np.savetxt('input_example.dat',data, header=header)
    
    
def build_example_grid(n_points=20):
    x=np.linspace(1,3,n_points)
    y=np.linspace(1,3,n_points)
    x,y=np.meshgrid(x,y)
    
    z=p_known(x,y)
    zerr= np.random.rand(*np.shape(x))
    
    
    data=np.column_stack([x.flatten(),y.flatten(),z.flatten(),zerr.flatten()])
    
    header='# density Temperature property sigma_property'
    np.savetxt('input_example_grid.dat',data, header=header)
    
def read_data(fname,prop_ref):
    """
    Reads the data from the input file that has [Temperature rho Property errorProperty]
    Args:
        fname: name of the file containing the data, run build example to see the structure 
        of the input_example.dat
        rho_ref: reference density
        beta_ref: reference beta
        prop_ref: Property at the reference point
        
    Returns:
        rho, beta, pro-prop_ref, sigma_prop
    """
    
    header, data = read_file(fname)
    rho=data[:,1]
    temperature=data[:,0]
    prop=data[:,2]-prop_ref
    sigma_prop=data[:,3]
    beta=(1/temperature)


    # #    #Restricting to a range of temperatures
    
    # indexes=np.where(temperature<1.4)[0]
    
    # beta=beta[indexes]
    # rho=rho[indexes]
    # sigma_prop=sigma_prop[indexes]
    # prop=prop[indexes]
    
    
    return rho, beta, prop, sigma_prop


def read_file(file_name):
    """
    Reads a file assuming that the the first line is the header
    
    Args:
        file_name: Name of the file
        
    Returns:
        header: the header as an array of strings
        data: is a pandas dataframe
    """
    
    with open(file_name, 'r') as data_file:
        header = data_file.readline().split()
        data = pd.read_csv(data_file,delim_whitespace=True, header=None).dropna(axis=1, how='all')
        data =data.to_numpy()
    return header, data

def read_coeff_file(input_file):
    """
    Reads the fitting coefficients and the exponents for the polymer fit
    
    """
    
    header, data = read_file(input_file)
    m_values = [int(el.split('=')[-1]) for el in header]
    n_values = [int(el.split('=')[-1]) for el in data[:,0]]
        
    coefficients = data[:,1:].astype('float')
        
    
    return m_values, n_values, coefficients
    

# def plot_slices():
    
    
#     cf.set_plot_appearance()
#     dir_name="slices_beta_p"
#     shutil.rmtree(dir_name,ignore_errors=True) 
    
#     os.mkdir(dir_name)
#     slices=np.unique(y_p)
#     print("\nPerforming the Pressure slices\n")
#     for i,sli in enumerate(slices):
        
#         fig3=plt.figure()
#         ax3=fig3.add_subplot(111)
#         error_cap=4
#         indexes=np.where(y_p==sli)
#         ax3.errorbar(x_p[indexes],z_p[indexes]+p_ref,yerr=zerr_p[indexes],fmt='o',capsize=error_cap,label='beta=%s'%sli)
#         ax3.plot(x_p[indexes],er_results_p[indexes[0],1],label='Fit 3')
#         ax3.plot(x_p[indexes],single_results_p[indexes[0],1],label='Fit 1')
#         fig3.legend(loc='upper right')
#         fig3.tight_layout()
#         fig3.savefig("%s/slice_%s.pdf"%(dir_name,i))
        
        
#     dir_name="slices_beta_e"
#     shutil.rmtree(dir_name,ignore_errors=True) 
#     os.mkdir(dir_name)
    
    
#     slices=np.unique(y_e)
#     print("\nPerforming the Energy slices\n")
#     for i,sli in enumerate(slices):
        
#         fig3=plt.figure()
#         ax3=fig3.add_subplot(111)
#         error_cap=4
#         indexes=np.where(y_e==sli)
#         ax3.errorbar(x_e[indexes],z_e[indexes]+e_ref,yerr=zerr_e[indexes],fmt='o',capsize=error_cap,label='beta=%s'%sli)
    
#         ax3.plot(x_e[indexes],er_results_e[indexes[0],1],label='Fit 3')
#         ax3.plot(x_e[indexes],single_results_e[indexes[0],1],label='Fit 1')
#         fig3.legend(loc='upper right')
#         fig3.tight_layout()
#         fig3.savefig("%s/slice_%s.pdf"%(dir_name,i))
        
        
#     dir_name="slices_beta_a"
#     shutil.rmtree(dir_name,ignore_errors=True) 
#     os.mkdir(dir_name)
    
#     slices=np.unique(y_a)
#     print("\nPerforming the Free energy slices\n")
#     for i,sli in enumerate(slices):
        
#         fig3=plt.figure()
#         ax3=fig3.add_subplot(111)
#         error_cap=4
#         indexes=np.where(y_a==sli)
#         ax3.errorbar(x_a[indexes],z_a[indexes]+a_ref,yerr=zerr_a[indexes],fmt='o',capsize=error_cap,label='beta=%s'%sli)
        
#         ax3.plot(x_a[indexes],er_results_a[indexes[0],1],label='Fit 3')
#         ax3.plot(x_a[indexes],single_results_a[indexes[0],1],label='Fit 1')
        
        
#         fig3.legend(loc='upper right')
#         fig3.tight_layout()
#         fig3.savefig("%s/slice_%s.pdf"%(dir_name,i))

