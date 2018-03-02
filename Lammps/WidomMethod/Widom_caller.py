#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
This scripts performs Widom insertion method in a series of configurarions.
The widom method is performed calling an external C++ code that is compiled and then run for each configuration.

Generates the
@author: simon
"""

import numpy as np
import subprocess

#Getting the absolut path to the python file i,e also the cpp file
import os
dir_path = os.path.dirname(os.path.realpath(__file__))

#Compiling the code

args = ['g++', 'Widom.cpp','-o','Widom.o']
FNULL = open(os.devnull, 'w') #To hide the output
subprocess.call(args,stdout=FNULL, stderr=subprocess.STDOUT)


#Reading the times to make it easier to read the file by chunks
Times=np.loadtxt("Times.dat",dtype=int)
x=np.size(Times)

print "Creating the Sigma and Epsilon Matrices files"
Epsilon=np.matrix('1.0 1.0; 1.0 1.0')
Sigma=np.matrix('1.0 1.0; 1.0 1.0')

np.savetxt("Epsilon.param",Epsilon)
np.savetxt("Sigma.param",Sigma)

Results=[]
for k in xrange(x): #Runs over the sampled times.

    print("Reading configuration %d of %d" %(k+1,x))
    File_Name=str(int(Times[k]))+".cxyz"
    args=[dir_path+'/Widom.o', File_Name]
    subprocess.call(args,stdout=FNULL, stderr=subprocess.STDOUT)
    row=Times[k]
    row=np.append(row,np.loadtxt("Output.dat"))
    Results.append(row)

Results=np.array(Results)
np.savetxt("Results.dat", Results)
Av=np.average(Results[:,1::],axis=0)
error=np.sqrt(np.var(Results[:,1::],axis=0)/x)

np.savetxt("Statistics.dat",np.append(Av,error))

print "\nGenerated Results.dat with the time series of the chemical potentials and Statistics.dat with the averages and errors"
