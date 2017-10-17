"""
=============================================================================
This is a script that performs all the analyses only using the Averages values
All the units are scaled in LJ units, it is mentioned explicitly otherwise.
=============================================================================

Inputs:

Averages.dat has the parameters as [This is just for the all fluid]:
Chunk,Coord,Ncout,Vx,Rho,[Pzz,Pxx]
"""

import numpy as np
from subprocess import Popen,PIPE
from shlex import split
#=============================================================================
#Input files and parameters
#=============================================================================

FProperties=np.loadtxt("LAverages.dat") #Solvent properties
SProperties=np.loadtxt("SAverages.dat") #Solute properties
AProperties=np.loadtxt("AAverages.dat") #All properties

n,m=np.shape(AProperties)



IntLow=0    #Lower integration limit
IntUp=8    #Upperintegration limit
BulkMin=15  #Bulk Lower Limit
BulkMax=25  #Bulk Upper Limit

#Getting the Input temperature
p1 = Popen(split('grep "nvt" log.lammps'),stdout=PIPE)
p2 = Popen(split('head -1'), stdin=p1.stdout, stdout=PIPE)
out,err=p2.communicate()
T=np.float(out.split()[-2])
print "\nWorking temperature is %f \n" %T

# =============================================================================
# Function Definition
# =============================================================================
def Integrate(x, y, xmin, xmax):
    """
    Integrate the data in x and y from xmin to xmax
    """
    MinIndex = np.min(np.where(x >= xmin))
    MaxIndex = np.max(np.where(x <= xmax))
    I = np.trapz(y[MinIndex:MaxIndex], x[MinIndex:MaxIndex])

    return I

# =============================================================================
# Computing the bulk Properties
# =============================================================================
def BulkProperties(Properties, BulkMin, BulkMax):
    """
    :param Properties: Has all the averages computed from the chunks
    :param BulkMin: Minimum Position of the Bulk
    :param BulkMax: Maximum Position of the Bulk
    :return:
    Bulkc  Bulk concentration
    N      Number of particles in the bulk
    """

    BulkC=0
    cont=0
    N=0
    for i in xrange(n):
        if (Properties[i,1]>=BulkMin and Properties[i,1]<BulkMax):
            cont=cont+1
            BulkC=BulkC+Properties[i,4]
            N=N+Properties[i,2]
    BulkC=BulkC/cont
    N=N/cont


    return BulkC,N



def Gamma(Properties,BulkC,IntLow,IntUp):
    """
    Computes the Adsorption
    :param Properties:
    :param BulkC:
    :param IntLow:
    :param IntUp:
    :return:
    Gamma Species adsorption
    """
    Integrand = Properties[:, 1] / BulkC - 1.0
    Gamma = Integrate(Properties[:, 0], Integrand, IntLow, IntUp)
    return Gamma


def HForce(Ns,Nb,SProperties,FProperties,AProperties):
    """
    Hiroaki Force Calculation

    :param Ns: Number of Solute Particles in the Bulk
    :param Nb: Number of Fluid Particles in the Bulk
    :param SProperties: Solute Properties
    :param FProperties: Solvent Properties
    :param AProperties: Fluid Properties
    :return:
    The Force distribution
    """
    FsH = (Nb - Ns) / Nb
    FfH = -FsH * (Ns / (Nb - Ns))
    HForce = np.zeros((n, 2))
    HForce[:, 0] = SProperties[:, 1]

    for i in xrange(n):
        if AProperties[i, 4] == 0:
            HForce[i, 1] = 0

        else:
            HForce[i, 1] = (FfH * FProperties[i, 4] + FsH * SProperties[i, 4]) / AProperties[i, 4]

    np.savetxt("Hforce.dat",HForce)
    Ffactor = 1.0 / FsH

    print "The Force Factor is  %f" %Ffactor
    print "Created Hiroaki Force distribution File HForce.dat "


    return HForce



def YForce(Cs,Cf,SProperties,FProperties,AProperties):
    """
    Yawei Force Calculation
    :param Cs: Solute Concentration
    :param Cf: Solvent Concentration
    :param SProperties: Solute Properties
    :param FProperties: Solvent Properties
    :param AProperties: Fluid Properties
    :return:
    The Force distribution

    """
    FsY = -1.0
    FfY = -FsY * Cs / Cf
    YForce = np.zeros((n, 2))
    YForce[:, 0] = FProperties[:, 1]

    for i in xrange(n):
        if AProperties[i, 4] == 0:
            YForce[i, 1] = 0

        else:
            YForce[i, 1] = (FfY * FProperties[i, 4] + FsY * SProperties[i, 4]) / AProperties[i, 4]

    np.savetxt("Yforce.dat", YForce)

    print "Created Yawei Force distribution File YForce.dat "

    return YForce



# ==============================================================================
# Main
# ==============================================================================


# ==============================================================================
# Solvent
# ==============================================================================

print "\nComputing Solvent properties\n"

Cf,Nf=BulkProperties(FProperties, BulkMin, BulkMax)
print "The bulk concentration is %f" %(Cf)
print "The average concentration is %f" %(np.average(FProperties[:,4]))

FGamma= Gamma(FProperties,Cf,IntLow,IntUp)

print "The Solvent adsorption is %f" %FGamma

# ==============================================================================
# Solute
# ==============================================================================

print "\nComputing Solute properties\n"

Cs,Ns=BulkProperties(SProperties, BulkMin, BulkMax)
print "The bulk concentration is %f" %(Cs)
print "The average concentration is %f" %(np.average(SProperties[:,4]))

SGamma = Gamma(SProperties,Cs,IntLow,IntUp)

print "The Solute adsorption is %f" %SGamma

# ==============================================================================
# Fluid
# ==============================================================================

print "\nComputing Fluid properties\n"

C,N=BulkProperties(AProperties, BulkMin, BulkMax)
print "The bulk concentration is %f" %(C)
print "The average concentration is %f" %(np.average(AProperties[:,4]))


# ==============================================================================
# Force Calculations
# ==============================================================================
print "\n Starting the Force Calculations\n"
HForce = HForce(Ns,N,SProperties,FProperties,AProperties)
YForce = YForce(Cs,Cf,SProperties,FProperties,AProperties)
Index = np.where(HForce[:, 0] < BulkMax)
BinSize = HForce[1, 0] - HForce[0, 0]

Zpos = np.append(HForce[Index, 0], HForce[Index[0][-1], 0] + BinSize)
HF = np.transpose(HForce[Index, 1])
YF = np.transpose(YForce[Index, 1])

print "Creating the Files to iterate in Lammps"
np.savetxt("Zpos_iterate.dat", Zpos)
np.savetxt("HForce_iterate.dat", HF)
np.savetxt("YForce_iterate.dat", YF)

