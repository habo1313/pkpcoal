import sys
import platform
OSys=platform.system()
#if OSys=='Linux':
#    sys.path.append('../src')
#if OSys=='Linux':
#    sys.path.append('..\\src')
sys.path.append('src')
import shutil
import numpy as np
import InformationFiles

class WriteCoalFile(object):
    """Writes the Coal.inp file using the output of the GUI."""
    def __init__(self,InfosFromGUIObject):
        self.Info=InfosFromGUIObject
        try:
            Obj = InformationFiles.ReadFile('Coal.inp')
            self.CoalDens= Obj.getText(InformationFiles.M_density)
        except IOError:
            print "Please put a information about the coal density into the 'Coal.inp'."
        CoalFile=open('Coal.inp','w')
        CoalFile.write(self.__mkstr())
        CoalFile.close()
        
    
    def __mkstr(self):
        """Writes the content of the coal file"""
        FileStr='#Proximate Analysis (in percent, as recieved):\n'
        PA = InformationFiles.M_PA
        UA = InformationFiles.M_UA
        PAFC,PAVM,PAMoi,PAAsh=self.Info.PA()
        UAC,UAH,UAN,UAO,UAS=self.Info.UA()
        FileStr+=PA[0]+'\n'
        FileStr+=PAFC+'\n'
        FileStr+=PA[1]+'\n'
        FileStr+=PAVM+'\n'
        FileStr+=PA[2]+'\n'
        FileStr+=PAMoi+'\n'
        FileStr+=PA[3]+'\n'
        FileStr+=PAAsh+'\n'
        FileStr+='\n'
        FileStr+= '#Ultimate Analysis (in percent):\n'
        FileStr+=UA[0]+'\n'
        FileStr+=UAC+'\n'
        FileStr+=UA[1]+'\n'
        FileStr+=UAH+'\n'
        FileStr+=UA[2]+'\n'
        FileStr+=UAN+'\n'
        FileStr+=UA[3]+'\n'
        FileStr+=UAO+'\n'
        FileStr+=UA[4]+'\n'
        FileStr+=UAS+'\n'
        FileStr+='\n'
        #
        MTar,HHV=self.Info.MwsHHV()
        FileStr+=InformationFiles.M_HHV+'\n'
        FileStr+=HHV+'\n'
        FileStr+=InformationFiles.M_MTar+'\n'
        FileStr+=MTar+'\n'
        FileStr+='\n'
        FileStr+=InformationFiles.M_density+'\n'
        FileStr+= self.CoalDens+'\n'
        #
        WY,WR = self.Info.WeightYR()
        FileStr+=InformationFiles.M_Weight[0]+'\n'
        FileStr+=WY+'\n'
        FileStr+=InformationFiles.M_Weight[1]+'\n'
        FileStr+=WR+'\n'
        return FileStr


class WriteCPDFile(object):
    """Writes the CPD.inp file using the output of the GUI. The number of print increment is imorted from the previous version of CPD.inp."""
    def __init__(self,InfosFromGUIObject):
        self.Info=InfosFromGUIObject
        #get Nr of CPD print increment
        try:
            NrPrintCPDObj = InformationFiles.ReadFile('CPD.inp')
#            if OSys=='Linux':
#                NrPrintCPDObj = InformationFiles.ReadFile('../CPD.inp')
#            elif OSys=='Windows':
#                NrPrintCPDObj = InformationFiles.ReadFile('..\\CPD.inp')
            self.NrPrintCPD = NrPrintCPDObj.getText(InformationFiles.MC_dt[1])
        except IOError:
            self.NrPrintCPD = '1'
        CPDFile=open('CPD.inp','w')
        CPDFile.write(self.__mkstr())
        CPDFile.close()
#        if OSys=='Linux':
#            shutil.move('CPD.inp','../CPD.inp')
#        elif OSys=='Windows':
#            shutil.move('CPD.inp','..\\CPD.inp')
    
    def __mkstr(self):
        """Writes the content of the CPD file"""
        FileStr=InformationFiles.MC_sel+'\n'
        #FitDict={0:'None',1:'Run',2:'constantRate',3:'Arrhenius',4:'ArrheniusNoB',5:'Kobayashi',6:'DAEM'}
        CPDsel, FGsel, PCCLsel, PMSKDsel = self.Info.RunPyrolProg()
        if CPDsel=='None':
            FileStr+='No'+'\n'
        else:
            FileStr+='Yes'+'\n'
        FileStr+='\n'
        FileStr+=InformationFiles.M_selFit+'\n'
        if CPDsel=='Run':
            FileStr+='None'+'\n'
        else:
            FileStr+=CPDsel+'\n'
        FileStr+='\n#numerical parameter for CPD:\n'
        FileStr+=InformationFiles.MC_dt[0]+'\n'
        p, dt = self.Info.OperCond()
        FileStr+=dt+'\n'
        FileStr+=InformationFiles.MC_dt[1]+'\n'
        FileStr+=self.NrPrintCPD
        return FileStr


class WriteFGFile(object):
    """Writes the FGDVC.inp file using the output of the GUI. The filepaths are imorted from the previous version of FGDVC.inp."""
    def __init__(self,InfosFromGUIObject):
        self.Info=InfosFromGUIObject
        #get directories for FGDVC
        try:
            Obj = InformationFiles.ReadFile('FGDVC.inp')
#            if OSys=='Linux':
#                Obj = InformationFiles.ReadFile('../FGDVC.inp')
#            elif OSys=='Windows':
#                Obj = InformationFiles.ReadFile('..\\FGDVC.inp')
            self.DirMain= Obj.getText(InformationFiles.MF_dir[0])
            self.DirOut= Obj.getText(InformationFiles.MF_dir[1])
        except IOError:
            print 'Please put a FGDVC.inp file in the directory to allow the program to read the FG-DVC directories.'
        FGFile=open('FGDVC.inp','w')
        FGFile.write(self.__mkstr())
        FGFile.close()
#        if OSys=='Linux':
#            shutil.move('FGDVC.inp','../FGDVC.inp')
#        elif OSys=='Windows':
#            shutil.move('FGDVC.inp','..\\FGDVC.inp')
    
    def __mkstr(self):
        """Writes the content of the FGDVC file"""
        FileStr=InformationFiles.MF_sel+'\n'
        CPDsel, FGsel, PCCLsel, PMSKDsel = self.Info.RunPyrolProg()
        if FGsel=='None':
            FileStr+='No'+'\n'
        else:
            FileStr+='Yes'+'\n'
        FileStr+=InformationFiles.M_selFit+'\n'
        if FGsel=='Run':
            FileStr+='None'+'\n'
        else:
            FileStr+=FGsel+'\n'
        FileStr+='\n'
        FileStr+= InformationFiles.MF_dir[0]+'\n'
        FileStr+=self.DirMain+'\n'
        FileStr+= InformationFiles.MF_dir[1]+'\n'
        FileStr+=self.DirOut+'\n\n'
        FileStr+= InformationFiles.MF_CoalSel+'\n'
        FGCoal, FGTar=self.Info.FGCoalProp()
        FileStr+= FGCoal+'\n'
        FileStr+= InformationFiles.MF_TarCr+'\n'
        FileStr+= FGTar+'\n'
        return FileStr

class WritePMSKDFile(object):
    """Writes the PMSKD.inp file using the output of the GUI. The filepaths are imorted from the previous version of PMSKD.inp."""
    def __init__(self,InfosFromGUIObject):
        self.Info=InfosFromGUIObject
        #get directories for FGDVC
        try:
            Obj = InformationFiles.ReadFile('PMSKD.inp')
            #            if OSys=='Linux':
            #                Obj = InformationFiles.ReadFile('../FGDVC.inp')
            #            elif OSys=='Windows':
            #                Obj = InformationFiles.ReadFile('..\\FGDVC.inp')
            #self.DirMain= Obj.getText(InformationFiles.MF_dir[0])
            #self.DirOut= Obj.getText(InformationFiles.MF_dir[1])
            self.npoint = Obj.getText(InformationFiles.MP_npoint)
            self.mechfile = Obj.getText(InformationFiles.MP_mechfile)

        except IOError:
            print 'Please put a PMSKD.inp file in the directory to allow the program to read the FG-DVC directories.'
        FGFile=open('PMSKD.inp','w')
        FGFile.write(self.__mkstr())
        FGFile.close()
    #        if OSys=='Linux':
    #            shutil.move('FGDVC.inp','../FGDVC.inp')
    #        elif OSys=='Windows':
    #            shutil.move('FGDVC.inp','..\\FGDVC.inp')

    def __mkstr(self):
        """Writes the content of the PMSKD file"""
        FileStr=InformationFiles.MP_sel+'\n'
        print FileStr
        CPDsel, FGsel, PCCLsel, PMSKDsel = self.Info.RunPyrolProg()
        if PMSKDsel=='None':
            FileStr+='No'+'\n'
        else:
            FileStr+='Yes'+'\n'
        FileStr+=InformationFiles.M_selFit+'\n'
        if PMSKDsel=='Run':
            FileStr+='None'+'\n'
        else:
            FileStr+=PMSKDsel+'\n'
        FileStr+='\n'
        FileStr+=InformationFiles.M_selArrhSpec+'\n'
        FileStr+=self.Info.ArrhSpec()+'\n\n'
        FileStr+='number of step:\n'
        FileStr+=self.npoint
        FileStr+='\nMechanism file:\n'
        FileStr+=self.mechfile

        return FileStr

    def __repr__(self):
        return super(WritePMSKDFile, self).__repr__()
        
class WritePCCLFile(object):
    """Writes the PCCL.inp file using the output of the GUI. The filepaths and exe name are imorted from the previous version of PCCL.inp."""
    def __init__(self,InfosFromGUIObject):
        self.Info=InfosFromGUIObject
        #get directories for PCCL
        try:
            Obj = InformationFiles.ReadFile('PCCL.inp')
#            if OSys=='Linux':
#                Obj = InformationFiles.ReadFile('../FGDVC.inp')
#            elif OSys=='Windows':
#                Obj = InformationFiles.ReadFile('..\\FGDVC.inp')
            self.DirMain= Obj.getText(InformationFiles.MPC_dir)
            self.Exe = Obj.getText(InformationFiles.MPC_exe)
            self.CalibrFactor = Obj.getText(InformationFiles.MPC_CoalCal)
        except IOError:
            print 'Please put a PCCL.inp file in the directory to allow the program to read the PC Coal Lab directories.'
        PCCLFile=open('PCCL.inp','w')
        PCCLFile.write(self.__mkstr())
        PCCLFile.close()
#        if OSys=='Linux':
#            shutil.move('FGDVC.inp','../FGDVC.inp')
#        elif OSys=='Windows':
#            shutil.move('FGDVC.inp','..\\FGDVC.inp')
    
    def __mkstr(self):
        """Writes the content of the PCCL file"""
        FileStr=InformationFiles.MPC_sel+'\n'
        CPDsel, FGsel, PCCLsel, Polimisel = self.Info.RunPyrolProg()
        if PCCLsel == 'None':
            FileStr+='No'+'\n'
        else:
            FileStr+='Yes'+'\n'
        FileStr+=InformationFiles.M_selFit+'\n'
        if PCCLsel == 'Run':
            FileStr+='None'+'\n'
        else:
            FileStr+=PCCLsel+'\n'
        FileStr+='\n'
        FileStr+= InformationFiles.MPC_dir+'\n'
        FileStr+=self.DirMain+'\n'
        FileStr+= InformationFiles.MPC_exe+'\n'
        FileStr+=self.Exe+'\n\n'
        FileStr+= InformationFiles.MPC_CoalCal+'\n'
        CoalCalFactor=self.CalibrFactor
        FileStr+= CoalCalFactor+'\n'
        PaticleSize=self.Info.PCCLParticleSize()
        FileStr+= InformationFiles.MPC_partSize+'\n'
        FileStr+= PaticleSize+'\n'
        return FileStr
        


class WriteOCFile(object):     
    """Writes the OperCond.inp file using the output of the GUI."""
    def __init__(self,InfosFromGUIObject):
        self.Info=InfosFromGUIObject
        OCFile=open('OperCond.inp','w')
        OCFile.write(self.__mkstr())
        OCFile.close()
#        if OSys=='Linux':
#            shutil.move('OperCond.inp','../OperCond.inp')
#        elif OSys=='Windows':
#            shutil.move('OperCond.inp','..\\OperCond.inp')
    
    def __mkstr(self):
        """Writes the content of the CPD file"""
        FileStr=InformationFiles.M_Pressure+'\n'
        p, dt = self.Info.OperCond()
        FileStr+=p+'\n\n'
        FileStr+=InformationFiles.M_dt+'\n'
        FileStr+=dt+'\n\n'
        FileStr+=InformationFiles.M_selArrhSpec+'\n'
        FileStr+=self.Info.ArrhSpec()+'\n\n'
        FileStr+='Time History: first column time in seconds, second column: Temperature in K. Last point must contain the final time. The final time has to be equal in each case.\n'
        FileStr+=InformationFiles.M_NrRuns+'\n'
        nrT = self.Info.TimeHistories()
        FileStr+=nrT+'\n'
        try:
            T1=np.genfromtxt('TempHist1.dat')
        except IOError:
            T1=np.array([[0.0,300],[0.5,1200]])
        try:
            T2=np.genfromtxt('TempHist2.dat')
        except IOError:
            T2=T1
        try:
            T3=np.genfromtxt('TempHist3.dat')
        except IOError:
            T3=T1
        try:
            T4=np.genfromtxt('TempHist4.dat')
        except IOError:
            T4=T1
        try:
            T5=np.genfromtxt('TempHist5.dat')
        except IOError:
            T5=T1
        FileStr+=InformationFiles.M_TimePoints1[0]+'\n'
        for i in range(len(T1[:,0])):
            FileStr+=str(T1[i,0])+',  '+str(T1[i,1])+'\n'
        FileStr+=InformationFiles.M_TimePoints1[1]+'\n'+'\n'
        #
        FileStr+=InformationFiles.M_TimePoints2[0]+'\n'
        for i in range(len(T2[:,0])):
            FileStr+=str(T2[i,0])+',  '+str(T2[i,1])+'\n'
        FileStr+=InformationFiles.M_TimePoints2[1]+'\n'+'\n'
        #
        FileStr+=InformationFiles.M_TimePoints3[0]+'\n'
        for i in range(len(T3[:,0])):
            FileStr+=str(T3[i,0])+',  '+str(T3[i,1])+'\n'
        FileStr+=InformationFiles.M_TimePoints3[1]+'\n'+'\n'
        #
        FileStr+=InformationFiles.M_TimePoints4[0]+'\n'
        for i in range(len(T4[:,0])):
            FileStr+=str(T4[i,0])+',  '+str(T4[i,1])+'\n'
        FileStr+=InformationFiles.M_TimePoints4[1]+'\n'+'\n'
        #
        FileStr+=InformationFiles.M_TimePoints5[0]+'\n'
        for i in range(len(T5[:,0])):
            FileStr+=str(T5[i,0])+',  '+str(T5[i,1])+'\n'
        FileStr+=InformationFiles.M_TimePoints5[1]+'\n'
        return FileStr
        
        
