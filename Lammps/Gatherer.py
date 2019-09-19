#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
script to be used after running Gatherer.sh
Notice the definition of N, the number of runs to be 
taken into account to compute the averages

@author: sr802
"""
import numpy as np
import matplotlib.pyplot as plt

N=5 #Number of runs to average

Times=np.loadtxt("../times.dat",dtype=int)
x=np.size(Times)

#Opening the first array
data=np.loadtxt("full-mean."+str(int(Times[x-N])))
for k in range(x-N+1,x): #Runs over the sampled times.
               
    print(("Reading configuration %d of %d" %(k,x-1)))
    #Reading the Results 
    name="full-mean."+str(int(Times[k]))
    array=np.loadtxt(name)
    data[:,2::]=data[:,2::]+array[:,2::]
    
#Normalizing
data[:,2::]=data[:,2::]/N
np.savetxt("Averages.dat",data)
plt.plot(data[:,1],data[:,3])
plt.ylim(-0.005,0.005)
plt.xlim(5.0,13.0)

    