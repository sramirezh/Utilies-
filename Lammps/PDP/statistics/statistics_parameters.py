#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
This script gets the results created by dp_poly and the averages of vdata.dat
and computes relevant quantities and generates plots, It has to be run inside every N_X

Args:
    Input filen name
Returns:


@author: simon
"""

import os
import sys
import pandas as pd
import numpy as np
import re
import argparse


sys.path.append(os.path.join(os.path.dirname(__file__), '../../../')) #This falls into Utilities path
import Lammps.core_functions as cf


try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
#    from matplotlib.backends.backend_pdf import PdfPages
except ImportError as err:
    print err


try:
    from uncertainties import ufloat
except ImportError as err2:
    print err2


"""
*******************************************************************************
Functions
*******************************************************************************
"""

def number_properties(lines):
    """
    Gets the number of properties based on the pattern in Statistics_summary.dat
    Args:
        lines are the list of lines in the file.
    Returns:
        nproperties are the number of properties analysed

    """
    indexes=cf.parameter_finder(lines, "dDP")
    nproperties=indexes[1]-indexes[0]-2
    return nproperties

def build_data():
    """
    Function to initialise all the elements of the class
    """

    interactions=[]
    with open("Statistic_summary.dat", 'r') as f:
      lines = f.readlines()

    i=0
    nproperties=10 #The number of properties per force in the input file (TO IMPROVE)
    #Getting the number of properties
    count=0

    while i<len(lines):
        if re.search("\AE_*",lines[i] ): #Finding the LJ parameters
            interactions.append(LJInteraction(re.findall(r"[-+]?\d*\.?\d+", lines[i])))
            print "\nReading data from  %s"%lines[i]
            i=i+1
            count+=1
        else:
            if re.search("\AdDP*",lines[i] ):
                interactions[-1].addforce(lines[i])
                i+=1
                properties=[]
                for j in xrange(nproperties):
                    properties.append(lines[i])
                    i+=1
                interactions[-1].addproperties(properties)
            i+=1

    return interactions


def parameter_finder(List, String):
    """
    Finds a string on a List and returns the position on the list
    """
    cont=0
    indexes=[]
    for s in List:
        if String in s:
            indexes.append(cont)
        cont+=1
    length=len(indexes)
    if length>1: print "There were several ocurrences"
    if length==0: print "No ocurrences found"
    return indexes


def ncols(nparameters, row_per_column):
    """
    Returns the ideal number of columns for the desired number of rows per column
    """
    ncols=nparameters/row_per_column

    return ncols


def plot_force_individuals(interactions):
    """
    Plots the parameters from statistic_summary for each force, for each interaction
    """
    colors=['r','b','k','g','r','b','k','g','r','b','k','g']
    #General plot parameters
    axis_font=24
    tick_font=20
    legend_font=18
    xoffset=0.1
    yoffset=0.1
    error_cap=4

    #This Dict is going to be compared with the variable file_name
    dic_yaxis={'conc_bulk':r'$C_s^B [\sigma^{-3}]$','vx_poly':r'$V_p^x[\sigma/\tau]$','rg_ave':r'$R_g [\sigma]$'}

    print "\nGenerating Plots..."
    directory="plots/individual"

    if not os.path.exists(directory):
        os.makedirs(directory)

    n_properties=len(interactions[0].properties[0]) #Number of properties

    has_error=np.ones((n_properties), dtype=bool)

    for property_index in xrange(n_properties):
        if np.size(interactions[0].properties[0][property_index])==1:
            has_error[property_index]=False

        prop_name=interactions[-1].property_names[0][property_index] #Crude property name
        if "Time" in prop_name: continue #To avoid plotting the timestep
        file_name=re.sub('^_|^v_|^c_',"",prop_name).strip('_')
        name=re.sub('_',' ',file_name)
        print "\nplotting the %s" %name
         
        

        fig,ax=plt.subplots()
        i_interaction=0
        for ljpair in interactions:
            n=0
            yvalue=np.empty(0)
            yerror=np.empty(0)
            force_list=[]
            for force in ljpair.forces:

                if has_error[property_index]==True:
                    yvalue=np.append(yvalue,ljpair.properties[n][property_index][0]) #Be careful np.append inserts in reverse order compared to .append
                    yerror=np.append(yerror,ljpair.properties[n][property_index][1]) #Taking the autocorrelation error
                else:
                    yerror=None
                    yvalue=np.append(yvalue,ljpair.properties[n][property_index])
                force_list.append(force)
                n+=1
            plt.errorbar(force_list,yvalue,yerr=yerror,xerr=None,fmt='o',label='$\epsilon_{ms}$=%s $\sigma_{ms}$=%s '%(ljpair.epsilon,ljpair.sigma),
                         color=colors[i_interaction],capsize=error_cap)
            
            # Adding a linear fit
            x=force_list
            y=yvalue
            ax.plot(np.unique(x), np.poly1d(np.polyfit(x, y, 1))(np.unique(x)),color=colors[i_interaction],linestyle='--')
            #plt.legend("" %(ljpair.epsilon,ljpair.sigma))
            i_interaction+=1



       

        file_name=name.replace(" ","_")

        """Legend"""
        plt.legend(fontsize=legend_font,loc='upper left',labelspacing=0.5,borderpad=0.4,scatteryoffsets=[0.6],
           frameon=True, fancybox=False, edgecolor='k')



        """Axis"""
        try:
            ylabel=dic_yaxis[file_name]
            ax.set_ylabel(ylabel,fontsize=axis_font)
        except:
            ylabel=file_name

        ax.set_xlabel(r'$F_{s}^{\mu}=-\nabla \mu_s [\epsilon/\sigma]$',fontsize=axis_font)
        ax.tick_params(labelsize=tick_font,direction='in',top=True, right=True)
        ylabel=file_name

        ymin,ymax=plt.ylim()
        deltay=ymax-ymin
        ax.set_ylim(ymin-deltay*yoffset,ymax+deltay*0.45)

        xmin,xmax=plt.xlim()
        deltax=xmax-xmin
        ax.set_xlim(xmin-deltax*xoffset,xmax+deltax*xoffset)
        
        
        
        plt.xticks(np.arange(0.02,0.12,0.02))
        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)


        """Lines"""
        if ymin*ymax<0:
            ax.axhline(y=0, xmin=0, xmax=1,ls=':',c='black')

        """General"""

        plt.grid(False)
        plt.rcParams["mathtext.fontset"] = "cm"
        plt.rcParams["text.usetex"] =True
        plt.tight_layout()
        plt.savefig("plots/individual/%s.pdf"%file_name)
        plt.close()
    print "\nGenerated plots for the individual properties vs forces, find them in '%s' " %directory


def is_valid_file(parser,arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!, see source options" % arg)


def extract_digits(string):
    """
    Returns an array of all the digits in a string
    """
    return re.findall(r"[-+]?\d*\.?\d+",string)

def compute_statistics_param(dpolymin):
    """
    Gets the parameters for the dpolymin that should be used to call the compute_statistics.sh
    """
    tfile,err=cf.bash_command("""find . -name "*.lmp" -path "*/dDP*" -print -quit""")#Assuming all the input files have the same parameters.
    print tfile
    out,err=cf.bash_command("""grep -m 1 "myDump equal" %s"""%tfile)
    d=int(extract_digits(out)[0]) #sampling Interval

    out2,err=cf.bash_command("""grep -m 1 "myStepsEach equal"  %s"""%tfile)
    n1=int(extract_digits(out2)[0])
    out3,err=cf.bash_command("""grep -m 1 "myLoop loop"  %s"""%tfile)
    n2=int(extract_digits(out3)[0])

    n=n1*n2    #total number of steps

    s=d*dpolymin
    return [s,d,n]


"""
*******************************************************************************
CLASS DEFINITION
*******************************************************************************
"""
class LJInteraction(object):
    """
    Every pair of LJ interactions has its own
    """

    def __init__(self,lj_parameters):
        self.epsilon=float(lj_parameters[0])
        self.sigma=float(lj_parameters[1])
        self.forces=[]
        self.properties=[]
        self.property_names=[]

    def addforce(self,new_force):
        force=float(new_force.strip('\n/dDP'))/1000
        self.forces.append(force)

    def addproperties(self,properties):
        values=[]
        names=[]
        for element in properties:
            name,value=element.strip("\n").split("=")
            name=name.replace(" ","_")
            if 'NaN' in value:
                value=float('nan')
            elif len(value)>1:
                value=value.split()
            
            values.append(np.double(value))
            names.append(name)
        self.properties.append(values)
        self.property_names.append(names)


    def compute_mobility(self):
        self.mobility=[]
        self.mob_rg=[] #Mobility over Rg
        count=0
        index_vx=parameter_finder(self.property_names[count],"vx_relative")[0]
        index_rg=parameter_finder(self.property_names[count],"rg_ave")[0]
        for force in self.forces:
            if force!=0:
                velocity=ufloat(self.properties[count][index_vx][0],self.properties[count][index_vx][1])
                rg=self.properties[count][index_rg]
                mobility=-velocity/force
                self.mobility.append(mobility)
                if rg==0:
                    self.mob_rg.append(10**8) #To avoid division by 0
                else:
                    self.mob_rg.append(mobility/rg)
            count+=1

    def get_property(self,name):
        """
        function to get the specific property
        """
        index=parameter_finder(self.property_names[0],name)[0]
        count=0
        prop=[]
        for force in self.forces:
            prop_f=self.properties[count][index]
            prop.append(prop_f)
            count+=1

        return prop




"""
###############################################################################
Argument Parser
###############################################################################
"""

cwd = os.getcwd() #current working directory
dir_path = os.path.dirname(os.path.realpath(__file__))#Path of this python script

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This script gets the results created by dp_poly and the averages of vdata.dat and computes relevant quantities and generates plots, It has to be run inside every N_X",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s','--source',choices=['read','run','gather'], default="read",help='Decides if the if the file Statistics_summary.dat needs to be read, run, gather  ')
    parser.add_argument('--vdatamin', help='Number of samples to be discarded in vdata.dat', default=1000, type=int)
    parser.add_argument('--dpolymin', help='Number of samples to be discarded in DPpoly', default=100, type=int)
args = parser.parse_args()
source=args.source

if source=="run":
    print "\nRunning the statistics analysis, using the following parameters"
    dppoly_params=compute_statistics_param(args.dpolymin)
    print "Initial dp_poly step=%d"%dppoly_params[0]
    print "Interval dp_poly=%d"%dppoly_params[1]
    print "Final dp_poly step=%d"%dppoly_params[2]
    print "vdata discarded steps =%d"%args.vdatamin
    print " "
    cf.bash_command("""bash %s/compute_statistics.sh %d %d %d %d"""%(dir_path,dppoly_params[0],dppoly_params[1],dppoly_params[2],args.vdatamin))

elif source=="gather":
    print "\nGathering the statistics analysis results"
    cf.bash_command("""bash %s/gather_statistics.sh"""%dir_path)

else:
    is_valid_file(parser,"Statistic_summary.dat")










"""
*******************************************************************************
Main program
*******************************************************************************
"""

print "\nAnalizing the results"
interactions=build_data()
plot_force_individuals(interactions)




"""
*******************************************************************************
Building the averaged data, excluding force equal=0
*******************************************************************************
"""


ave_data=[]
for interaction in interactions:
    name='E_%s_S_%s '%(interaction.epsilon,interaction.sigma)
    interaction.compute_mobility()

    mobilities=np.array((interaction.mobility))
    ave_mobility=sum(mobilities)/len(mobilities)

    ave_concentration_rg=np.average(interaction.get_property("concentration")[1:]) #Solute concentration inside rg,In order to exlude f=0
    ave_concentration_bulk=np.average(interaction.get_property("conc_bulk")[1:]) #Solute concentration in the bulk
    delta_cs=ave_concentration_rg-ave_concentration_bulk
    ave_rg=np.average(interaction.get_property("rg_ave")[1:]) #Average Rg
    ave_rg=ave_rg+10**-10 #Avoid dividing by zero
    mobility_rg=ave_mobility/ave_rg #Mobility divided by Rg


    data_interaction=[name,ave_mobility.n,ave_mobility.s, ave_concentration_rg, ave_concentration_bulk, delta_cs, ave_rg, mobility_rg.n, mobility_rg.s ]
    ave_data.append(data_interaction)

ave_data=np.array(ave_data)
pd_data=pd.DataFrame(ave_data,columns=['LJ_interaction','ave_mobility','mobility_error', 'ave_concentration_rg','ave_concentration_bulk','delta_cs','ave_rg','mobility_rg','mobility_rg_error'])


pd_data.to_csv("Results.dat",sep=' ',index=False)

"""
###############################################################################
Starting the plot
###############################################################################
"""
axis_font=24
tick_font=20
legend_font=18
annotate_size=12
xoffset=0.16
yoffset=0.1
error_cap=4

directory="plots/all"
if not os.path.exists(directory):
    os.makedirs(directory)
    
    
    
"""
###############################################################################
Mobility vs Delta Cs
###############################################################################
"""
fig,ax=plt.subplots()

ave_data=np.array(ave_data[:,1::],dtype=float) #Avoiding the first column which contains the interactions.
ax.errorbar(ave_data[:,-4],ave_data[:,0],yerr=ave_data[:,1],fmt='o',capsize=error_cap)
x=np.array(ave_data[:,-4])
y=np.array(ave_data[:,0])


for i in xrange(len(interactions)):
    txt="%.2lf,%.2lf"%(interactions[i].epsilon,interactions[i].sigma)
    ax.annotate(txt, (x[i]+0.002,y[i]),horizontalalignment='left',verticalalignment='center',fontsize=annotate_size)

"""Axis"""
ax.set_xlabel(r'$\Delta c_s [1/\sigma^3] $',fontsize=axis_font)
ax.grid(False)
ax.set_ylabel(r'$\Gamma_{ps} [\tau/m]$',fontsize=axis_font)
ax.tick_params(labelsize=tick_font,direction='in')

ymin,ymax=plt.ylim()
deltay=ymax-ymin
ax.set_ylim(ymin-deltay*yoffset,ymax+deltay*yoffset)


xmin,xmax=plt.xlim()
deltax=xmax-xmin
ax.set_xlim(xmin-deltax*xoffset,xmax+deltax*xoffset)







"""Lines"""
ax.axhline(y=0, xmin=0, xmax=1,ls='--',c='black')
ax.axvline(x=0, ymin=0, ymax=1,ls='--',c='black')

"""General"""
plt.rcParams["mathtext.fontset"] = "cm"
plt.rcParams["text.usetex"] =True
plt.tight_layout()
fig.savefig("plots/all/Mobility_Delta_Cs.pdf")
plt.close()




"""
###############################################################################
Mobility vs epsilon ms
###############################################################################
"""
epsilon_vect=[]
for i in xrange(len(interactions)):
    epsilon_vect.append(interactions[i].epsilon)

fig,ax=plt.subplots()

ax.errorbar(epsilon_vect,ave_data[:,0],yerr=ave_data[:,1],fmt='o',capsize=error_cap,color='b')
x=np.array(epsilon_vect)
y=np.array(ave_data[:,0])



"""Axis"""
ax.set_xlabel(r'$\epsilon_{ms} $',fontsize=axis_font)
ax.grid(False)
ax.set_ylabel(r'$\Gamma_{ps} [\tau/m]$',fontsize=axis_font)
ax.tick_params(labelsize=tick_font,direction='in',top=True, right=True)

ymin,ymax=plt.ylim()
deltay=ymax-ymin
ax.set_ylim(ymin-deltay*yoffset,ymax+deltay*yoffset)

xmin,xmax=plt.xlim()
deltax=xmax-xmin
#ax.set_xlim(0,xmax+deltax*xoffset)
ax.set_xlim(0,7)
plt.xticks(np.arange(0,8,1))




"""Lines"""
ax.axhline(y=0, xmin=0, xmax=1,ls='--',c='black')

"""General"""
plt.rcParams["mathtext.fontset"] = "cm"
plt.rcParams["text.usetex"] =True
plt.tight_layout()
fig.savefig("plots/all/Mobility_vs_epsilon.pdf")
plt.close()


#"""
################################################################################
#Mobility/Rg vs Delta Cs
################################################################################
#"""
#
#fig,ax=plt.subplots()
#ax.errorbar(ave_data[:,-4],ave_data[:,-2],yerr=ave_data[:,-1], fmt='o', capsize=error_cap)
#
#
#x=np.array(ave_data[:,-4])
#y=np.array(ave_data[:,-2])
#
#for i in xrange(len(interactions)):
#    txt="%.2lf,%.2lf"%(interactions[i].epsilon,interactions[i].sigma)
#    ax.annotate(txt, (x[i]+0.002,y[i]),horizontalalignment='left',verticalalignment='center',fontsize=annotate_size)
#
#"""Axis"""
#ax.set_xlabel(r'$\Delta c_s [1/\sigma^3] $',fontsize=axis_font)
#ax.grid(False)
#ax.set_ylabel(r'$\Gamma_{ps}/R_g [\tau/m\sigma]$',fontsize=axis_font)
#ax.tick_params(labelsize=tick_font, direction='in')
#
#ymin,ymax=plt.ylim()
#deltay=ymax-ymin
#
#xmin,xmax=plt.xlim()
#deltax=xmax-xmin
#
#ax.set_ylim(ymin-deltay*yoffset,ymax+deltay*yoffset)
#ax.set_xlim(xmin-deltax*xoffset,xmax+deltax*xoffset)
#
#
#"""Lines"""
#ax.axhline(y=0, xmin=0, xmax=1,ls='--',c='black')
#ax.axvline(x=0, ymin=0, ymax=1,ls='--',c='black')
#
#"""General"""
#plt.rcParams["mathtext.fontset"] = "cm"
#plt.rcParams["text.usetex"] =True
#plt.tight_layout()
#fig.savefig("plots/all/Mobility_rg_Delta_Cs.pdf")
#plt.close()




pd_data.to_csv("plots/all/Results.dat",sep=' ',index=False)

print "\nGenerated average results Results.dat and plots in '%s'"%directory
