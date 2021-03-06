#!/usr/bin/env bash
#############################################
# This code is intended to analyze everything from the Measurement run
#############################################
dir=$(dirname $0) #to get the directory where the script and other source files are.

printf "\n##########################################################################\n"
echo "Analyzing the log file"
echo "##########################################################################"
python $dir/Log_Analysis/Thermo_Analyser.py log.lammps


printf "\n##########################################################################\n"
echo "Analyzing the trajectory File"
echo "##########################################################################"
bash $dir/Trajectory_Analysis/Trajectory_Splitter.sh -i trajectory.xyz -s Initial
python $dir/Trajectory_Analysis/Trajectory_Analyser.py
printf "\nGenerated 0.xyz and Zshift.dat \n"

printf "\n##########################################################################\n"
echo "Analyzing the Chunk properties"
echo "##########################################################################"


printf "\n**************************************************************************\n"
echo "Averaging the Solute properties"
echo "**************************************************************************"
bash $dir/Chunk_Analysis/Chunk_Splitter.sh Sproperties.all
python $dir/Chunk_Analysis/Chunk_Analyser.py
mv Averages.dat SAverages.dat

printf "\nGenerated SAverages.dat  \n"

printf "\n**************************************************************************\n"
echo "Averaging the Solvent properties"
echo "**************************************************************************"
bash $dir/Chunk_Analysis/Chunk_Splitter.sh Lproperties.all
python $dir/Chunk_Analysis/Chunk_Analyser.py
mv Averages.dat LAverages.dat

printf "\nGenerated LAverages.dat  \n"

printf "\n**************************************************************************\n"
echo "Averaging the Fluid properties"
echo "**************************************************************************"
bash $dir/Chunk_Analysis/Chunk_Splitter.sh properties.all
python $dir/Chunk_Analysis/Chunk_Analyser.py
mv Averages.dat AAverages.dat


printf "\nGenerated AAverages.dat \n"

rm *.chunk*

printf "\n##########################################################################\n"
echo "Analyzing the properties"
echo "##########################################################################"

python $dir/Property_Analysis/Property_Analysis.py

#Organizing all the output
mkdir Output
mv *.dat Output/
mv header Output/
mv Analyser.out Output
rm *.o[0-9]*
rm *.cxyz
