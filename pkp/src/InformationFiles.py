import numpy as np
import scipy
import sys
#from scipy import interpolate
######
#Markers for the input File:
#Markers for the Reading procedure of the coal input file:
M_PA   = ['Fixed Carbon:','Volatile Matter:','Moisture:','Ash:']
M_UA=['UA Carbon:','UA Hydrogen:','UA Nitrogen:','UA Oxygen:','UA Sulphur:'] #for UA input
M_HHV='Higher Heating Value, as recieved, in J/kg:'
M_MTar='Tar Molecule weight, MTar:'
M_Weight=['Weight-Parameter yields for fitting the kinetics:','Weight-Parameter rates for fitting the kinetics:']
M_density='Coal dry density in kg/m3:'
#Markers for the Reading procedure of the coal input file:
MC_sel='useCPD?:'
M_selFit="selected fitting Approximation: 'constantRate', 'Arrhenius', 'ArrheniusNoB', 'Kobayashi', 'DAEM' or 'None'; selectedFit:"
M_selArrhSpec="Species of to Fit (when Arrhenius is selected): 'Total', 'MainSpecies', 'allSpecies'"
MC_dt=['initial time step in s:','print increment, writeValue:']
#Markers for the Reading procedure of the PMSKD input file:
MP_sel='usePMSKD?:'
MP_npoint='number of step:'
MP_mechfile = 'Mechanism file:'
#Markers for the Reading procedure of the coal input file:
MF_sel='use FG-DVC?:'
MF_CoalSel='Choose Coal: 0 interpolate between library coals and generate own coal. Set 1 to 8 for a library coal.'
MF_dir=['main directory FG-DVC:','directory fgdvc-output:']
MF_TarCr='Model tar cracking? If no, set tar residence time equal 0. For a partial tar cracking enter the tar residence time in s. For full tar cracking write -1.'
#Markers for the Reading procedure of the PC COAL LAB input file:
MPC_sel  = 'use PC Coal Lab?:'
MPC_dir  = 'PC Coal Lab Main Path:'
MPC_exe  = 'PC Coal Lab executable name:'
MPC_CoalCal  = 'Known PC Coal Lab Coal Calibration Factor? None or Value(float):'
MPC_partSize = 'Particle Size in micrometer:'
#Markers for the Reading procedure of the operating condition input file:
M_Pressure='pressure in atm:'
M_NrRuns='Number of Temperature Histories to include:'
#to extend when more cases:
M_TimePoints1=['Start Time History 1','End Time History 1']
M_TimePoints2=['Start Time History 2','End Time History 2']
M_TimePoints3=['Start Time History 3','End Time History 3']
M_TimePoints4=['Start Time History 4','End Time History 4']
M_TimePoints5=['Start Time History 5','End Time History 5']
M_dt='FG-DVC: constant (numerical) time step; CPD: maximum time step'


                   
class WriteFGDVCCoalFile(object):
    """writes the file, which will be inputted into the FG-DVC coal generator"""
    def __init__(self,CoalGenFile):
        self.__FileName=CoalGenFile

    def setCoalComp(self,Carbon,Hydrogen,Oxygen,Nitrogen,Sulfur,SulfurPyrite):
        """Enter the coal composition with values in percent which have to sum up to 100""" 
        self.__C=Carbon
        self.__H=Hydrogen
        self.__O=Oxygen
        self.__N=Nitrogen
        self.__S=Sulfur
        self.__Sp=SulfurPyrite
        
    def write(self,CoalsDirectory,CoalResultFileName,option=0):
        """writes the FG-DVC coal generator input file"""
        self.__File = open(CoalsDirectory+self.__FileName, 'w')
        self.__File.write(str(self.__C)+' '+str(self.__H)+' '+str(self.__O)+' '+str(self.__N)+' '+str(self.__S)+' '+str(self.__Sp)+'\n')
        self.__File.write(str(option)+'\n4\n'+CoalResultFileName+'_com.dat\n'+CoalResultFileName+'_kin.dat\n'+CoalResultFileName+'_pol.dat\n'+'5')
        self.__File.close()
        
class OperCondInput(ReadFile):
    """Reads the input file for the operating conditions and also writes the temperature-history file, required by FG-DVC."""
    def __init__(self,InputFile):
        self.InputFile=InputFile
        self.Input=np.array(self.readLines())
            
    def getTimePoints(self,FileNoteBegin,FileNoteEnd):
        """reads the time points in the shape 'time, temperature' for the lines between the line with the FileNoteBegin and the line with the FileNoteEnd"""
        try:
            BeginLine=np.where(self.Input[:]==FileNoteBegin)
            BeginLine=BeginLine[0]+1; BeginLine=BeginLine[0]
            ###
            EndLine=np.where(self.Input[:]==FileNoteEnd)
            EndLine=EndLine[0]; EndLine=EndLine[0]
    #        TimeTemp=np.genfromtxt(self.InputFile,skip_header=BeginLine,skip_footer=self.NumberOfLines()-EndLine, delimiter=',')
            TimeTemp=np.genfromtxt(self.Input[BeginLine:EndLine], delimiter=',')
            return TimeTemp
        except IndexError:
            print 'Please check the Marker:',FileNoteBegin, FileNoteEnd, '\nin the file: ',self.InputFile
            sys.exit()
        
    def writeFGDVCtTHist(self,tTPoints,dt,OutputFilePath):
        """Writes output file for FG-DVC containing in first column time in s, in the second tempearure in degree Celsius. FG-DVC will import this file. The time-temperature array has to be a numpy.array, dt a float, OutputFilePath a string."""
        tTFile=open(OutputFilePath,'w')
        #Transforms the T in degree Celsius, as required as input in FG-DVC t-T File (see manual V8.2.3 page 12)
        tTPoints[:,1]=tTPoints[:,1]-273.15
        THist=scipy.interpolate.interp1d(tTPoints[:,0],tTPoints[:,1],kind='linear')
        t=0.0
        while t<tTPoints[-1,0]:
            tTFile.write('%.4f  %.2f \n' % (t,THist(t)))
            t+=dt
        tTFile.close()

    def NumberOfLines(self):
        return int(len(self.Input[:]) )
