"""
This script analyzes chunk-averaged data generated by LAMMPS
The chunk files should be SPlitted before using Chunk_Splitter.sh

It generates a file "Averages.dat" that has the averages of all data and then if there are stresses per atom, it multiplies them properly by the density





"""

import os
import sys
import pandas as pd
import numpy as np
import re
import argparse
from scipy import optimize
import glob
import warnings
import seaborn as sns
from tqdm import tqdm


warnings.filterwarnings("ignore")
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../')) #This falls into Utilities path
import Lammps.core_functions as cf



try:
    import matplotlib
    matplotlib.use('agg')
    import matplotlib.pyplot as plt
except ImportError as err:
    print(err)



"""
Functions
"""
def read_times(nmin):
    """
    Reads the times.dat file created from the splitter
    args:
        nmin the number of steps to skip
    Returns:
        times an array with all the timesteps to analyise
    """
    times=np.sort(pd.read_csv("Times.dat",header=None).values,axis=0)
    if nmin<1:
        print("Discarding %d%% of the timesteps for the analysis"%(int(nmin*100)))
        discard=int(nmin*len(times))
        times=times[discard:]
    else: 
        print("Discarding %d out of %d timesteps for the analysis" %(nmin,len(times)))
        times=times[int(nmin):]
        
    return times


def get_zshift():
    try:
        f=open("Zshift.dat")
        zshift=np.float(f.readline())
        f.close()
    except IOError:  #If the file does not exist
        print("No 'Zshift.dat' found, assuming Zshift=0")
        zshift=0
    return zshift


def split_trajectory(split):
    
    if split==True:
        print("\nSplitting the chunk series")
        #make a general csplitter
        #out,err=cf.bash_command("""bash %s/Trajectory_poly.sh -i %s bash"""%(dir_path,file_name))
    else:
        print("\nThe chunk file was not splitted")


def get_parameters():
    """
    Reads the parameters in the header, the header was obtained from the splitter
    
    
    Returns:
        Parameters the list of relevant parameters
    """
    #Reading the header
    f=open("header", 'r')
    parameters=f.readlines()[2].split()
    f.close()
    parameters.remove("#")
    print("The parameters are:\n")
    for f in parameters:
        print(f)
    return parameters

""" main"""

parser = argparse.ArgumentParser(description='This script analyses a times series of data from chunks',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('FileName', metavar='InputFile',help='Input filename',type=lambda x: cf.is_valid_file(parser, x))
parser.add_argument('-split', help='True if trajectory file need to be splitter', default=False, type=bool)
parser.add_argument('-nmin', help='Number or percentage (between 0-1) of timesteps to be discarded', default=300, type=float)

args = parser.parse_args()


nmin=args.nmin

split_trajectory(args.split)

times=read_times(nmin)
x=len(times)
zshift=get_zshift()

parameters=get_parameters()

index_stress=cf.parameter_finder(parameters,"stress")
index_avoid=cf.parameter_finder(parameters,["Chunk","coord"])
index_density=cf.parameter_finder(parameters,"density")[0]

#Getting the shape of the data array
    
file_name=str(int(times[0]))+".chunk"
data=pd.read_csv(file_name,sep=" ",header=None,skiprows=1).dropna(axis=1,how='all')
n,m=np.shape(data)


"""
Computing the averages and other parameters
"""
averages=np.zeros((n,m))
averages[:,index_avoid]=data.values[:,index_avoid]

print("\nGathering all the data\n")

for k in tqdm(range(x),file=sys.stdout): 
   # print("Reading configuration %d of %d" %(k,x-1))
    file_name=str(int(times[k]))+".chunk"
    data=pd.read_csv(file_name,sep=" ",header=None,skiprows=1).dropna(axis=1,how='all')
    data=data.values
    for l in range(m): #Runs over the parameter
        if l in index_stress:
            averages[:,l]=averages[:,l]-data[:,l]*data[:,index_density] #Stress per atom*mass/density
        elif l not in index_avoid:
            averages[:,l]=averages[:,l]+data[:,l]

#Building the final array
for i in range(m):
    if i not in index_avoid:
        averages[:,i]=averages[:,i]/(x)


averages[:,1]=averages[:,1]-zshift #Adding the shift due the surface
"""
Creating the output file
"""
header=" ".join(parameters)
np.savetxt("Averages.dat",averages, header=header)


#For Testing Porpuses
#import matplotlib.pyplot as plt
#
#plt.plot(Averages[:,1],Averages[:,3])
#plt.xlim([0,25])

