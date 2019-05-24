#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu May  9 11:10:12 2019

@author: simon
"""
import numpy as np
import argparse
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

#Lets create the known polynomial

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
    print np.shape(x),np.shape(y),np.shape(z),np.shape(zerr)
    
    
    data=np.column_stack([x.flatten(),y.flatten(),z.flatten(),zerr.flatten()])
    
    header='# density Temperature property sigma_property'
    np.savetxt('input_example_grid.dat',data, header=header)
    



def arbitrary_poly(data, *params):
    """
    Creates a polymer
    pijx^iy^j with i of i=0,...,n, j=0,...,m
    
    Args:
        params: coefficients
        point: contains the the two independent variables x and y
        
        pijx^iy^j
    
    """
    points=data[0]
    x=points[0]
    y=points[1]
    n=data[1]
    m=data[2]
    params=np.reshape(params,(n+1,m+1))
    poly=0
    for i in xrange(n+1):
        for j in xrange(m+1):
            poly+=params[i,j]*x**i*y**j
    return poly



def read_data(fname,rho_ref,beta_ref):
    """
    Reads the data from the input file
    Args:
        fname: name of the file containing the data, run build example to see the structure 
        of the input_example.dat
        rho_ref: reference density
        beta_ref
        
    Returns:
        variables
    """
    data=np.loadtxt(fname)
    
    
    rho=data[:,1]-rho_ref
    temperature=data[:,0]
    prope=data[:,2]
    sigma_prope=data[:,3]
    beta=1/temperature-beta_ref
    
    
    
    return rho,beta, prope, sigma_prope



def test_prediction(popt,variables,z,deg_x,deg_y):
    """
    Returns the points generated by the predicted function
    Args:
        popt is the fitting coefficient matrix
    """
    m,n_point=np.shape(variables)
    z_predict=[]
    popt=np.reshape(popt,(np.size(popt)))
    for i in xrange(n_point):
        z_predict.append(arbitrary_poly([variables[:,i],deg_x,deg_y],popt))
    z_predict=np.array(z_predict)

    error=np.abs(z-z_predict)/z
    
    return z_predict,error


def outputs(popt_matrix,pcov,error,n,m):
    
    print "\nCreated coefficients.dat containing all the fitting coefficients"
    np.savetxt('coefficients.dat', popt_matrix)
    print "\nCreated covariant.dat with the covariant matrix of the fitting"
    np.savetxt('covariant.dat', pcov)
    print "\nCreated error.dat containing the relative error between the property and the prediction given by the fitting evaluated at the same input points"
    np.savetxt('error.dat',error)
    
def coefficient_guide(n,m,exclude_n,exclude_m):
    """
    Prints a guide showing the coefficients lets say i=0,..,n , j=0,...n
    """
    

def fit_poly(x,y,z,zerr,n,m):
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
    variables=np.stack((x,y),axis=0)
    popt, pcov = curve_fit(arbitrary_poly, [variables[:,:],n,m], z, sigma=zerr,p0=[1]*(n+1)*(m+1))
    popt_matrix=np.reshape(popt,((n+1),(m+1)))
    return popt_matrix,pcov,variables
    
    

# =============================================================================
# MAIN
# =============================================================================
    
def main(input_file,rho_ref,beta_ref,deg_x,deg_y):
    
    print '\nRunning the script assuming:\nrho_ref = %s\nbeta_ref = %s\ndegree in rho= %s \ndegree in beta= %s'%(rho_ref,beta_ref,deg_x,deg_y)
    global x,y,z,z_mesh,popt
    x,y,z, zerr=read_data(input_file,rho_ref,beta_ref)
    
    popt, pcov,variables=fit_poly(x,y,z,zerr,deg_x,deg_y)
    
    z_predict,error=test_prediction(popt,variables,z,deg_x,deg_y)
    
    outputs(popt,pcov,error, deg_x, deg_y)
    
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(x, y, z, zdir='z',marker='.',label="Simulation",color='r')
#    ax.scatter(x, y, z_predict, zdir='z',label="Fitting",color='black')
    
    #Creating the surface
    x,y=np.meshgrid(np.linspace(np.min(x),np.max(x),20),np.linspace(np.min(y),np.max(y),20))
    z=np.asarray(x)
    variables=np.stack((x.flatten(),y.flatten()),axis=0)
    z_mesh,error=test_prediction(popt,variables,z.flatten(),deg_x,deg_y)
    z_mesh=np.reshape(z_mesh,np.shape(x))
    ax.plot_wireframe(x,y,z_mesh,color='b')
    ax.set_xlabel("rho")
    ax.set_ylabel("T")
    
    fig.legend()
    fig.savefig("3Dplot.pdf")
    
    




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This script fits a 2 variable data to a poly of deg n',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file_name', metavar='input file',help='Input filename', type=str)
    parser.add_argument('-beta_ref', metavar='beta reference',help='reference beta',default=0,type=float)
    parser.add_argument('-rho_ref',metavar='rho reference',help='reference rho',default=0,type=float )
    parser.add_argument('-deg_x',metavar='poly degree in rho',help='Degree of the poly', default=3,type=int)
    parser.add_argument('-deg_y',metavar='poly degree in beta',help='Degree of the poly', default=2,type=int)
    args = parser.parse_args()
    
    main(args.file_name,args.rho_ref,args.beta_ref,args.deg_x,args.deg_y)
    
    
    





##Diagonal matrix test
#
#n=4 
#vec=np.random.rand(4)
#mat=np.diag(vec)
#inv=np.linalg.inv(mat)
#
#mat_a=np.random.rand(4,4)
#diag=np.diagonal(mat_a)

