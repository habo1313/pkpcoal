"""
A selection of different Pyrolysis models

A model pyrolysis model usually provides method to calculate the yield of
individual species the rates and energy balancing methods

"""
import numpy as np
import pylab as plt
import scipy as sp
import scipy.integrate
import scipy.interpolate
import platform

class BalancedComposition(object):
    """ Class for compostion that ensures componenents sum up to a
        certain value
    """

    def __init__(self, inp, target=100.00):
        """ From a given input dictionary and a target sum a
            dictionary with scaled composition is created
        """
        self.target = target
        scaling_factor = target/sum(inp.values())
        self.elems = {key:value*scaling_factor for key,value in inp.iteritems()}


    def __getitem__(self,item):
        """ """
        try:
            return self.elems[item]
        except:
            print """Warning trying to access {} which was not set in
            input file, assuming 0.0.
            """
            return 0.0

    def remove_elems_rebalance(self, elems_):
        """ To compute daf composition elements can be removed

            Usage:  .remove_elems_rebalance(['Moisture','Ash'])
        """
        return BalancedComposition({
            key:elem for key,elem in self.elems.iteritems()
                if key not in elems_
        })

    def scale(self, factor):
        return BalancedComposition(self.elems, target=self.target*factor)

    def __repr__(self):
        return str(self.elems)


class Model(object):
    """ Parent class of the children ConstantRateModel,
        the three Arrhenius Models (notations) and the Kobayashi models.

        Parameter:
                name      = model name e.g constantRate
                parameter = initial parameter which are adapted during
                            optimisation
                species   = Name of the modeled species
                runs      = preProc results as list

        TimeVectorToInterplt allows the option to define the discrete time points,
        where to interpolate the results. If set to False (standard), then is are
        the outputed results equal the dt to solve the ODE. If set
        TimeVectorToInterplt=[t0,t1,t2,t3,t4] (t: floats) then is the
        yields result returned at method calcMass the yields at [t0,t1,t2,t3,t4],
        linear interploated."""

    def __init__(self, name, parameter, parameterBounds, inputs, species, calcMass, recalcMass, runs=False, constDt=False):
        print "Initialised {} Model".format(name)
        self.name = name
        self.initialParameter = parameter
        self.parameter = parameter
        self.parameterBounds = parameterBounds
        self.species = species
        self.constDt = constDt
        self.calcMass = calcMass
        self.finalYield = 1.0
        self.runs = (runs if runs else [])
        self.postGeneticOpt = True
        self.recalcMass = recalcMass

    def fit(self):
        print 'initial parameter: ' + str(self.initialParameter)
        if len(self.runs) > 1:
            from pkp.src import Evolve
            optParams = self.geneticOpt()
            self.initialParameter = optParams
            self.parameterBounds = None #  reset bounds
        if self.postGeneticOpt:
            print 'start gradient based optimization, species: ' + self.species
            from scipy.optimize import minimize
            print "bounds",  self.parameterBounds
            optimizedParameter = minimize(
                    fun  = self.error_func,
                    x0   = self.initialParameter,
                    # method = 'CG',
                    bounds = self.parameterBounds,
                    tol = 1.0e-32,# self.fitTolerance, # FIXME
                    # options = {'maxiter': self.maxIter}
            )
            self.parameter = optimizedParameter
        return optimizedParameter

    def fittedYield(self):
        optParams = self.fit()
        return self.recalcMass(optParams.x, time=self.runs[0]['time'])

    def geneticOpt(self):
        from pyevolve import G1DList, GSimpleGA, Selectors
        from pyevolve import Initializators, Mutators, Consts, DBAdapters
        import numpy as np
        genome = G1DList.G1DList(len(self.parameter))
        # genome.setParams(rangemin=self.parameterBounds[0],
        #                  rangemax=self.parameterBounds[1])
        genome.initializator.set(Initializators.G1DListInitializatorReal)
        genome.mutator.set(Mutators.G1DListMutatorRealRange)
        # The evaluator function (objective function)
        genome.evaluator.set(self.error_func)
        # Genetic Algorithm Instance
        ga = GSimpleGA.GSimpleGA(genome)
        ga.setMinimax(Consts.minimaxType["minimize"])
        # set the population size
        ga.setPopulationSize(500) #FIXME
        # set the number of generation
        ga.setGenerations(200) #FIXME
        # Set the Roulette Wheel selector method,
        # the number of generations and the termination criteria
        ga.selector.set(Selectors.GRouletteWheel)
        ga.terminationCriteria.set(GSimpleGA.ConvergenceCriteria)
        ga.setMutationRate(0.4)
        ga.setCrossoverRate(1.0)
        # parallel processing
        # ga.setMultiProcessing(True)
        # Sets the DB Adapter, the resetDB flag will make the Adapter recreate
        # the database and erase all data every run, you should use this flag
        # just in the first time, after the pyevolve.db was created, you can
        # omit it.
        # sqlite_adapter = DBAdapters.DBSQLite(identify="koba", resetDB=True)
        # ga.setDBAdapter(sqlite_adapter)
        # Do the evolution, with stats dump, frequency of 20 generations
        ga.evolve(freq_stats=10)
        # Gets the best individual
        best = ga.bestIndividual() # update or find best model
        print best[0:]
        return best[0:]

    def updateParameter(self, parameter):
        self.parameter  = parameter
        return self

    def computeTimeDerivative(self, mass, deltaT=False, times=False):
        """ Return time derivatives for a given deltat array
            and a mass array
        """
        from numpy import gradient
        if deltaT:
            return gradient(mass, deltat)
        else:
            return gradient(np.array([mass,times]))

    def calcRate(self, preProcResult, time, temp, species):
        """ computes actual release reates for a given species
            by a time array and temperature array

            the preProcResults are used for initial values
            #TODO GO can time be taken from preProcResult?
        """
        mass = self.calcMass(preProcResult, time, temp, species)
        return self.computeTimeDerivative(mass, times = time)

    @classmethod
    def yieldDelta(cls, mass):
        return max(mass) - min(mass)

    def ErrorYield(self, preProcResult, Species):
        """ Returns the absolute deviation per point between the fitted
            pyrolysis model and the original preprocessor yield
        TODO GO: why only take some arrays from preProcResults
        """
        pass

    def ErrorRate(self, preProcResult, species):
        """ Returns the absolute deviation per point between
            the fitted and the original rate curve.
        """
        pass

    def _mkInterpolatedRes(self,InputVecYields,Time):
        """ Generates the result vector. Outputs the result vector at the
            corresponding time steps corresponding to the imported time at
            method calcMass. Requiered for Pc Coal Lab (only few reported points).
        """
        # t for for interplt, t_points, y_points
        return np.interp(Time,self.constDtVec,InputVecYields)

    def setDt4Intergrate(self,constantDt):
     """ constantDt allows the option to define numerical time step to solve the ODE.

        The outputted results ever equal the imported time list
        (when applying method calcMass Time = [t0,t1,t2,t3,t4]. If these time steps
        are too large, then is this defined dt used to solve the ODE and the results
        are linear interploated that way that they correspond to the imported time
        vector. To reset it, just set constantDt to False.
        """
     if constantDt != False:
         self.constDt = float(constantDt)

    def _mkDt4Integrate(self, Time):
        """ Time is the original time vector calculated by exact model, e.g. CPD.
            This class generates the internal dt vector if the dt defined by the
            user file is too large. A time step must be defined in Method
            setDt4Intergrate before.
        """
        if self.constDt != False:
         self.constDtVec = np.arange(Time[0], Time[-1], self.constDt)

        self.func = func

    def error_func(self, parameter, func="cummulative", weightMass=1.0, weightRate=0.0):
        """ Function for the optimizer, computes model error as a function
            of the input parameter

            Arguments:
            ---------
                    parameter: input parameter for the model e.g.:
                               pre-exp factor and tinit for const rate
                    func:      name of the function for evaluating the
                               error e.g. cummulative, or perpoint
        """
        # collect errors of individual runs
        func = Model.cumulative_error
        ret = [self.errorPerRun(parameter, run, func, weightMass, weightRate) 
                    for run in self.runs]

        # If we have a simple scalar list just sum the errors
        # else we component wise sum the error and return a vector
        # of errors per point
        self.error = (sum(ret) if type(ret[0]) != list else map(np.add, ret))
        return self.error

    def errorPerRun(self, parameter, run, func, weightMass, weightRate):
        """ Evaluate the error per run compared to pre comp

            Computation of the error is based on given function func,
            since we either want a the global error or the error per point
            for least squares
         """
        times      = run['time']
        targetMass = run[self.species]
        targetRate = run[self.species] #FIXME
        modeledMass = self.calcMass(parameter, 0.0, times, run.interpolate('temp'))
        modeledRate = self.computeTimeDerivative(modeledMass, times=times)
        dt = False
        # normalisation factor
        def norm(weight, target):
            return weight/np.power(Model.yieldDelta(target), 2.0)
        normMass = norm(weightMass, targetMass)
        normRate = norm(weightRate, targetRate)
        return func(targetRate, modeledRate,
                    targetMass, modeledMass,
                    normRate, normMass, dt)

    @classmethod
    def perPointError(cls, tr, mr, tm, mm, nr, nm, dt):
        ErrorRate = Model.modelErrorSquared(tr, mr)*dt
        ErrorMass = Model.modelErrorSquared(tm, mm)*dt
        return (ErrorMass * nm + ErrorRate * nr) * self.scaleFactor * dt

    @classmethod
    def cumulative_error(cls, tr, mr, tm, mm, nr, nm, dt):
        """ Parameter tr: target rate
                      mr: model rate
                      tm: target mass
                      mm: model mass
                      nr: weight paramater rate
                      nm: weight parameter mass
        """
        ErrorMass = Model.totModelErrorAbsPerc(tm, mm)
        ErrorRate = Model.totModelErrorAbsPerc(tr, mr)
        return (ErrorMass*nm + ErrorRate*nr)

    @classmethod
    def modelErrori(cls, target, model):
        """ compute the deviation between modeled values and the target values
            from the pre processor
        """
        return abs(target - model)

    @classmethod
    def modelErrorSquared(cls, target, model):
        """ compute the deviation between modeled values and the target values
            from the pre processor
        """
        return np.power(target - model, 2.0)

    @classmethod
    def modelErrorAbs(cls, target, model):
        """ compute the deviation between modeled values and the target values
            from the pre processor
        """
        return np.abs(target - model)

    @classmethod
    def totModelErrorAbsPerc(cls, target, model):
        return np.sum(Model.modelErrorAbs(target, model))/len(target)

    @classmethod
    def summedModelError(cls, target, model):
        return np.sum(Model.modelError(target, model))

    @classmethod
    def totModelErrorSquaredPerc(cls, target, model):
        return np.sum(Model.modelErrorSquared(target, model))/len(target)

################ children classes ####################

class constantRate(Model):
    """ The model calculating the mass
        with m(t)  =  m_s0+(m_s0-m_s,e)*exp(-k*(t-t_start))
             dm/dt = -k*(m-m_s,e).
        The Parameter to optimize are k and t_start.
    """
    #TODO store initial parameter to see test if parameters have been changed
    #TODO GO parameter[2] is not specified in inputs example

    def __init__(self, inputs, runs, species):
        paramNames  = ['k', 'tstart', 'finalYield']
        parameter   = [inputs['constantRate'][paramName] for paramName in paramNames]
        paramBounds = [inputs['constantRate'].get(paramName+"Bounds",(None,None))
                         for paramName in paramNames] 
        Model.__init__(self, "ConstantRate", parameter, paramBounds, inputs,
            species, self.calcMassConstRate, self.recalcMass, runs)
        # self.k           = parameter["k"]
        # self.start_time  = parameter["tstart"]
        # self.final_yield = parameter.get('finalYield',False)
        # if set to false, the numerical time step corresponding to the outputed
        # by the detailled model (e.g CPD) is used; define a value to use instead this

    def __repr__(self):
        return  "Const Rate k {} tstart {}".format(self.k, self.start_time)

    def recalcMass(self, parameter, time):
        """ recalculate mass release after updateParameter

            reuses init_mass, time and temp from previous
            computation, needed for genetic algorhythm
            since we only get the best parameters back
            and need to adjust the model
        """
        return self.calcMassConstRate(parameter, init_mass=None, time=time)

    def calcMassConstRate(self, parameter, init_mass, time, temp=False):
        """ Computes the released mass over time

            Inputs:
                parameter: array of parameter e.g [k, tstart, finalYield]
                init_mass: not implemented
                time: array of time values from the preproc

            NOTE: the function doesnt implicitly modifiy state of the
                  constantRate Model, to modify the released mass
                  use instance.mass = calcMassConstRate(...)
        """
        # TODO better use a classmethod?
        k = parameter[0]
        start_time = parameter[1]
        final_yield = parameter[2]

        # we care only about time value
        # starting at start time
        time_ = time - start_time

        # NOTE dont compute values for negative times
        # the yield should be zero anyways
        time_ = time_.clip(0)

        # the yield still retained in the coal
        # this should converge to zero at large
        # time
        retained_mass = final_yield * np.exp(-k*time_)
        released_mass = final_yield - retained_mass

        # if we are interested in the solid mass
        # TODO GO what is this solid thing going on here
        if False: #species == 'Solid':
            released_mass += solid_mass*np.exp(-k*time)

        # why choosing between released or solid mass
        # start_time is small then time
        # released_mass = np.where(time > self.start_time, released_mass, solid_mass)
        if self.constDt == False: # TODO GO shouldnt interpolation be used for var dt?
            #print "modeled_mass " + str(released_mass)
            return released_mass
        else: #returns the short, interpolated list (e.g. for PCCL)
            return self._mkInterpolatedRes(released_mass, time)

    @property
    def k(self):
        return self.parameter[0]

    @property
    def start_time(self):
        return self.parameter[1]

class arrheniusRate(Model):
    """ The Arrhenius model in the standart notation:
            dm/dt=A*(T**b)*exp(-E/T)*(m_s-m)
        with the parameters a,b,E to optimize.
    """
    ODE_hmax = 1.e-2 #TODO what is this??
    absoluteTolerance = 1.0e-8
    relativeTolerance = 1.0e-6

    def __init__(self, inputs, runs, species):
        paramNames  = ['preExp', 'beta', 'activationEnergy']
        parameter   = [inputs['arrheniusRate'][paramName] for paramName in paramNames]
        paramBounds = [inputs['arrheniusRate'].get(paramName+"Bounds",(None,None))
                         for paramName in paramNames] 
        Model.__init__(self, "ArrheniusRate", parameter, paramBounds, inputs,
            species, self.calcMassArrhenius, runs)
        self.updateParameter(self.parameter)

    def updateParameter(self, parameter):
        self.A    = parameter[0]
        self.beta = parameter[1]
        self.E    = parameter[2]
        ##print "Parameter update " + str(parameter)

    def calcMassArrhenius(self, parameter, init_mass, time, temp=False):
        """Outputs the mass(t) using the model specific equation."""
        """ dm/dt=A*(T**b)*exp(-E/T)*(m_s-m)  """
        def dmdt(m, t):
            T  = temp(t) # so temp is a function that takes t and returns T
            # dm = self.final_yield - m # finalYield
            dm = 1.0 - m # finalYield
            A = self.A
            beta = self.beta
            E = self.E
            # print (A,beta,E,dm)
            if False:
                dmdt_ = (-A * dm  #FIXME this doesnt make sense!
                          * np.power(T, beta)
                          * np.exp(-self.E/T)
                            )
            else:
                dmdt_ = (init_mass + A * dm
                         * np.power(T, beta)
                         * np.exp(-E/T)) # TODO this should be Ta instead of E
            # print dmdt_,t
            # sets values < 0 to 0.0, to avoid further problems
            return dmdt_ #np.where(dmdt_ > 1e-64, dmdt_, 0.0)
        m_out = sp.integrate.odeint(
                func=dmdt,
                y0=[0.0],
                t=time,
                # atol=self.absoluteTolerance,
                # rtol=self.relativeTolerance,
                # hmax=self.ODE_hmax,
            )
        m_out = m_out[:, 0]
        if self.constDt == False: # TODO GO shouldnt interpolation be used for var dt?
            #print "modeled_mass " + str(released_mass)
            return m_out
        else: #returns the short, interpolated list (e.g. for PCCL)
            return self._mkInterpolatedRes(m_out, time)

    def ConvertKinFactors(self,ParameterVector):
        """ Dummy function actual has to convert the
            parameter to standard Arrhenius notation.
        """
        #does nothing, just to have the same way of use for all notations
        return ParameterVector

class Kobayashi(Model):
    """Calculates the devolatilization reaction using the Kobayashi model. The Arrhenius equation inside are in the standard notation."""
    def __init__(self,InitialParameterVector):
        print 'Kobayashi Model initialized'
        self._modelName = 'Kobayashi'
        self._ParamVector=InitialParameterVector
        self.ODE_hmax=1.e-2
        self.constDt = False # if set to false, the numerical time step corresponding to the outputted by the dtailled model (e.g CPD) is used; define a value to use instead this

    def calcMass(self,preProcResult,time,T,Name):
        """Outputs the mass(t) using the model specific equation. The input Vector is [A1,E1,A2,E2,alpha1,alpha2]"""
        # question whether the dt from DetailledModel result file or from a constant dt should be used
        if self.constDt == False: # dt for integrate = dt from DM result file
            timeInt = time
        else: #if dt in DM results file has too large dt
            self._mkDt4Integrate(time)
            timeInt = self.constDtVec
        self.preProcResult=preProcResult
        timeInt=np.delete(timeInt,0)
        self.__Integral=0.0
        tList=[0.0]
        k1k2=[0.0]
        ParamVec=self.ParamVector()
        #
        def dmdt(m,t):
            k1=ParamVec[0]*np.exp(-ParamVec[1]/(T(t)))
            k2=ParamVec[2]*np.exp(-ParamVec[3]/(T(t)))
            tList.append(t)
            k1k2.append(k1+k2)
            self.__Integral+=0.5*(tList[-1]-tList[-2])*(k1k2[-1]+k1k2[-2])
            dmdt_out = ( (ParamVec[4]*k1+ParamVec[5]*k2)*np.exp(-self.__Integral) )
            dmdt_out=np.where(abs(dmdt_out)>1.e-300,dmdt_out,0.0) #sets values<0 =0.0, otherwise it will further cause problem(nan)
            return dmdt_out
        InitialCondition=[0]
        m_out=sp.integrate.odeint(dmdt,InitialCondition,timeInt,atol=1.e-5,rtol=1.e-4,hmax=1.e-2)
        m_out=m_out[:,0]
        m_out=np.insert(m_out,0,0.0)
        if self.constDt == False:
            if (ParamVec[0]<0 or ParamVec[1]<0 or ParamVec[2]<0 or ParamVec[3]<0 or ParamVec[4]<0  or ParamVec[5]>1  ):
                m_out[:]=float('inf')
                return m_out
            else:
                return m_out
        else: #returns the short, interpolated list (e.g. for PCCL)
            return self._mkInterpolatedRes(m_out,time)


class KobayashiPCCL(Model):
    """Calculates the devolatilization reaction using the Kobayashi model. The Arrhenius equation inside are in the standard notation. The fitting parameter are as in PCCL A1,A2,E1,alpha1. TimeVectorToInterplt allows the option to define the discrete time points, where to interpolate the results. If set to False (standard), then is are the outputted results equal the dt to solve the ODE."""
    def __init__(self,InitialParameterVector):
        print 'Kobayashi Model initialized'
        self._modelName = 'KobayashiPCCL'
        self._ParamVector=InitialParameterVector
        self.ODE_hmax=1.e-2
        self.constDt = False # if set to false, the numerical time step corresponding to the outputted by the dtailled model (e.g CPD) is used; define a value to use instead this

    def calcMass(self,preProcResult,time,T,Name):
        """Outputs the mass(t) using the model specific equation."""
        # question whether the dt from DetailledModel result file or from a constant dt should be used
        if self.constDt == False: # dt for integrate = dt from DM result file
            timeInt = time
        else: #if dt in DM results file has too large dt
            self._mkDt4Integrate(time)
            timeInt = self.constDtVec
        self.preProcResult=preProcResult
        timeInt=np.delete(timeInt,0)
        self.__Integral=0.0
        tList=[0.0]
        k1k2=[0.0]
        ParamVec=self.ParamVector()
        #
        def dmdt(m,t):
            k1=ParamVec[0]*np.exp(-ParamVec[2]/(T(t)))
            k2=ParamVec[1]*np.exp(-(ParamVec[2]+self.__E2diff)/(T(t)))
            tList.append(t)
            k1k2.append(k1+k2)
            self.__Integral+=0.5*(tList[-1]-tList[-2])*(k1k2[-1]+k1k2[-2])
            dmdt_out = ( (ParamVec[3]*k1+self.__alpha2*k2)*np.exp(-self.__Integral) )
            dmdt_out=np.where(abs(dmdt_out)>1.e-300,dmdt_out,0.0) #sets values<0 =0.0, otherwise it will further cause problem(nan)
            return dmdt_out
        InitialCondition=[0]
        m_out=sp.integrate.odeint(dmdt,InitialCondition,timeInt,atol=1.e-5,rtol=1.e-4,hmax=1.e-2)
        m_out=m_out[:,0]
        m_out=np.insert(m_out,0,0.0)
        if self.constDt == False:
            if (ParamVec[0]<0 or ParamVec[1]<0 or ParamVec[2]<0 or ParamVec[3]<0):
                m_out[:]=float('inf')
                return m_out
            else:
                return m_out
        else: #returns the short, interpolated list (e.g. for PCCL)
            return self._mkInterpolatedRes(m_out,time)


    def ConvertKinFactors(self,ParameterVector):
        """Outputs the Arrhenius equation factors in the shape [A1,E1,A2,E2]. Here where the real Arrhenius model is in use only a dummy function."""
        P=self.ParamVector()
        return [P[0],P[1],P[2],P[3]]

    def setKobWeights(self,alpha2):
        """Sets the two Kobayashi weights alpha2."""
        self.__alpha2=alpha2

    def KobWeights(self):
        """Returns the two Kobayashi weights alpha2."""
        return self.__alpha2

    def setE2Diff(self,DifferenceE1E2):
        """Sets the dE in E2=E1+dE."""
        self.__E2diff=DifferenceE1E2

    def E2Diff(self):
        """Returns the dE in E2=E1+dE."""
        return self.__E2diff

class KobayashiA2(Model):
    """Calculates the devolatilization reaction using the Kobayashi model. The Arrhenius equation inside are in the secend alternative notation (see class ArrheniusModelAlternativeNotation2)."""
    def __init__(self,InitialParameterVector):
        print 'Kobayashi Model initialized'
        self._ParamVector=InitialParameterVector
        self.ODE_hmax=1.e-2
        self.constDt = False # if set to false, the numerical time step corresponding to the outputted by the dtailled model (e.g CPD) is used; define a value to use instead this

    def calcMass(self,preProcResult,time,T,Name):
        """Outputs the mass(t) using the model specific equation."""
        # question whether the dt from DetailledModel result file or from a constant dt should be used
        if self.constDt == False: # dt for integrate = dt from DM result file
            timeInt = time
        else: #if dt in DM results file has too large dt
            self._mkDt4Integrate(time)
            timeInt = self.constDtVec
        self.preProcResult=preProcResult
        T_general=preProcResult.Rate('Temp')
        self.T_min=min(T_general)
        self.T_max=max(T_general)
        self.c=1./(1./self.T_max-1./self.T_min)
        #alpha has to be greater equal zero:
        absoluteTolerance = 1.0e-8
        relativeTolerance = 1.0e-6
        self.tList=[0.0]
        #deletes to solve trapezian rule:
        timeInt=np.delete(timeInt,0)
        self.Integral=0.0
        self.k1k2=[0.0]
        ParamVec=self.ParamVector()
        u=preProcResult.Yield(Name)
        #
        def dmdt(m,t):
            k1=np.exp( self.c*( ParamVec[0]*(1./T(t)-1./self.T_min) - ParamVec[1]*(1./T(t)-1./self.T_max) ) )
            k2=np.exp( self.c*( ParamVec[2]*(1./T(t)-1./self.T_min) - ParamVec[3]*(1./T(t)-1./self.T_max) ) )
            self.tList.append(t)
            self.k1k2.append(k1+k2)
            self.Integral+=0.5*(self.tList[-1]-self.tList[-2])*(self.k1k2[-1]+self.k1k2[-2])
            dmdt_out = ( (self.__alpha1*k1+self.__alpha2*k2)*np.exp(-self.Integral) )
            dmdt_out=np.where(abs(dmdt_out)>1.e-300,dmdt_out,0.0) #sets values<0 =0.0, otherwise it will further cause problem(nan)
            return dmdt_out
        InitialCondition=[u[0]]
        m_out=sp.integrate.odeint(dmdt,InitialCondition,timeInt,atol=absoluteTolerance,rtol=relativeTolerance,hmax=self.ODE_hmax)
        m_out=m_out[:,0]
        m_out=np.insert(m_out,0,0.0)
        if self.constDt == False:
            return m_out
        else: #returns the short, interpolated list (e.g. for PCCL)
            return self._mkInterpolatedRes(m_out,time)

    def ConvertKinFactors(self,ParameterVector):
        """Converts the alternative notaion Arrhenius factors into the satndard Arrhenius factors and return them in the shape  [A1,E1], [A2,E2]"""
        A1=np.exp( -self.c*ParameterVector[0]/self.T_min + self.c*ParameterVector[1]/self.T_max )
        E1=self.c*ParameterVector[1]-self.c*ParameterVector[0]
        A2=np.exp( -self.c*ParameterVector[2]/self.T_min + self.c*ParameterVector[3]/self.T_max )
        E2=self.c*ParameterVector[3]-self.c*ParameterVector[2]
        return [A1,E1,A2,E2]

    def setKobWeights(self,alpha1,alpha2):
        """Sets the two Kobayashi weights alpha1 and alpha2."""
        self.__alpha1=alpha1
        self.__alpha2=alpha2

    def KobWeights(self):
        """Returns the two Kobayashi weights alpha1 and alpha2."""
        return self.__alpha1, self.__alpha2


class DAEM(Model):
    """Calculates the devolatilization reaction using the Distributed Activation Energy Model."""
    def __init__(self,InitialParameterVector):
        print 'DAEM initialized'
        self._modelName = 'DAEM'
        self._ParamVector=InitialParameterVector
        self.ODE_hmax=1.e-2
        self.NrOfActivationEnergies=50
        self.constDt = False # if set to false, the numerical time step corresponding to the outputted by the dtailled model (e.g CPD) is used; define a value to use instead this

    def setNrOfActivationEnergies(self,NrOfE):
        """Define for how many activation energies of the range of the whole distribution the integral shall be solved (using Simpson Rule)."""
        self.NrOfActivationEnergies=NrOfE

    def NrOfActivationEnergies(self):
        """Returns the number of activation enrgies the integral shall be solved for (using Simpson Rule)."""
        return self.NrOfActivationEnergies

    def calcMass(self,preProcResult,time,T,Name):
        """Outputs the mass(t) using the model specific equation."""
        self.E_List=np.arange(int(self._ParamVector[1]-3.*self._ParamVector[2]),int(self._ParamVector[1]+3.*self._ParamVector[2]),int((6.*self._ParamVector[2])/self.NrOfActivationEnergies)) #integration range E0 +- 3sigma, see [Cai 2008]
        # question whether the dt from DetailledModel result file or from a constant dt should be used
        if self.constDt == False: # dt for integrate = dt from DM result file
            timeInt = time
        else: #if dt in DM results file has too large dt
            self._mkDt4Integrate(time)
            timeInt = self.constDtVec
        #Inner Integral Funktion
        def II_dt(t,E_i):
            return np.exp( -E_i/T(t) )
        #outer Integral for one activation energy from t0 to tfinal
        #stores all values of the inner Integrals (time,ActivationEnergy) in a 2D-Array
        InnerInts=np.zeros([len(timeInt),len(self.E_List)])
        CurrentInnerInt=np.zeros(len(timeInt))
        for Ei in range(len(self.E_List)):
            CurrentInnerInt[:]=II_dt(timeInt[:],self.E_List[Ei])
            InnerInts[1:,Ei] = sp.integrate.cumtrapz(CurrentInnerInt,timeInt[:])
        #
        def OI_dE(EIndex,tIndex):
            m = np.exp(-self._ParamVector[0]*InnerInts[tIndex,EIndex])*(1./(self._ParamVector[2]*(2.*np.pi)**0.5))*np.exp(-(self.E_List[EIndex]-self._ParamVector[1])**2/(2.*self._ParamVector[2]**2))
#            print 'InnerInt',InnerInt,'mass',dm_dt
            return m
        m_out=np.zeros(np.shape(timeInt))
        mE=np.zeros(np.shape(self.E_List))
        for ti in range(len(timeInt)):
            for Ei in range(len(self.E_List)):
                mE[Ei]=OI_dE(Ei,ti)
            m_out[ti]=sp.integrate.simps(mE,self.E_List)
        #descaling
        m_out = self._ParamVector[3]*(1.-m_out)
        if self.constDt == False:
            return m_out
        else: #returns the short, interpolated list (e.g. for PCCL)
            return self._mkInterpolatedRes(m_out,time)
