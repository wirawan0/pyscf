#!/usr/bin/env python
#
# Author: Sandeep Sharma <sanshar@gmail.com>
#         Qiming Sun <osirpt.sun@gmail.com>
#         George Booth <george.booth24@gmail.com>
#

import os, sys
import numpy
import pyscf.tools
import pyscf.lib.logger as logger

try:
    from pyscf.fciqmcscf import settings
except ImportError:
    msg = '''settings.py not found.  Please create %s
''' % os.path.join(os.path.dirname(__file__), 'settings.py')
    sys.stderr.write(msg)

IRREP_MAP = {'D2h': (1,         # Ag
                     4,         # B1g
                     6,         # B2g
                     7,         # B3g
                     8,         # Au
                     5,         # B1u
                     3,         # B2u
                     2),        # B3u
             'C2v': (1,         # A1
                     4,         # A2
                     2,         # B1
                     3),        # B2
             'C2h': (1,         # Ag
                     4,         # Bg
                     2,         # Au
                     3),        # Bu
             'D2' : (1,         # A
                     4,         # B1
                     3,         # B2
                     2),        # B3
             'Cs' : (1,         # A'
                     2),        # A"
             'C2' : (1,         # A
                     2),        # B
             'Ci' : (1,         # Ag
                     2),        # Au
             'C1' : (1,)}

try:
    import settings
except ImportError:
    import os, sys
    msg = '''settings.py not found.  Please create %s
''' % os.path.join(os.path.dirname(__file__), 'settings.py')
    sys.stderr.write(msg)

class FCIQMCCI(object):
    def __init__(self, mol):
        self.mol = mol
        self.verbose = mol.verbose
        self.stdout = mol.stdout

        self.executable = settings.FCIQMCEXE
        self.scratchDirectory = ''  #Shouldn't need scratch dir settings.BLOCKSCRATCHDIR

        self.integralFile = "FCIDUMP"
        self.configFile = "neci.inp"
        self.outputFile = "neci.out"
        self.maxwalkers = 10000
        self.maxIter = -1
        self.RDMSamples = 5000
        self.restart = False
        self.time = 10
        self.tau = -1.0
        self.orbsym = []
        if mol.symmetry:
            self.groupname = mol.groupname
        else:
            self.groupname = None

        self._keys = set(self.__dict__.keys())

    def dump_flags(self, verbose=None):
        if verbose is None:
            verbose = self.verbose
        log = logger.Logger(self.stdout, verbose)
        log.info('******** FCIQMC options ********')
        log.info('Number of walkers = %s', self.maxwalkers)
        log.info('Maximum number of iterations = %d', self.maxIter)

    def make_rdm12(self, fcivec, norb, nelec, link_index=None, **kwargs):
        nelectrons = 0
        if isinstance(nelec, int):
            nelectrons = nelec
        else:
            nelectrons = nelec[0]+nelec[1]

        import os
        f = open(os.path.join(self.scratchDirectory, "spinfree_TwoRDM"), 'r')

        twopdm = numpy.zeros( (norb, norb, norb, norb) )
        #        norb_read = int(f.readline().split()[0])
        #assert(norb_read == norb)

        for line in f.readlines():
            linesp = line.split()

            if(int(linesp[0]) != -1):

                assert(int(linesp[0]) <= norb)
                assert(int(linesp[1]) <= norb)
                assert(int(linesp[2]) <= norb)
                assert(int(linesp[3]) <= norb)

                twopdm[int(linesp[0])-1,int(linesp[2])-1,int(linesp[1])-1,int(linesp[3])-1] = float(linesp[4])

        onepdm = numpy.einsum('ikjj->ik', twopdm)
        onepdm /= (nelectrons-1)

        return onepdm, twopdm

    def kernel(self, h1e, eri, norb, nelec, fciRestart=None, **kwargs):
        if fciRestart is None:
            fciRestart = self.restart
        if isinstance(nelec, int):
            neleca = nelec//2 + nelec%2
            nelecb = nelec - neleca
        else :
            neleca, nelecb = nelec

        writeIntegralFile(h1e, eri, norb, neleca, nelecb, self)
        writeFCIQMCConfFile(neleca, nelecb, fciRestart, self)
        if self.verbose >= logger.DEBUG1:
            inFile = self.configFile   #os.path.join(self.scratchDirectory,self.configFile)
            logger.debug1(self, 'FCIQMC Input file')
            logger.debug1(self, open(inFile, 'r').read())
        executeFCIQMC(self)
        if self.verbose >= logger.DEBUG1:
            outFile = self.outputFile   #os.path.join(self.scratchDirectory,self.outputFile)
            logger.debug1(self, open(outFile))
        calc_e = readEnergy(self)

        return calc_e, None

def writeFCIQMCConfFile(neleca, nelecb, Restart, FCIQMCCI):
    confFile = FCIQMCCI.configFile

    f = open(confFile, 'w')

    f.write('title\n')
    f.write('\n')
    f.write('system read\n')
    f.write('freeformat\n')
    f.write('electrons %i\n'%(neleca+nelecb))
    f.write('nonuniformrandexcits 4ind-weighted\n')
    f.write('hphf 0\n')
    f.write('endsys\n')
    f.write('\n')
    f.write('calc\n')
    f.write('methods\n')
    f.write('method vertex fcimc\n')
    f.write('endmethods\n')
    f.write('time %d\n'%(FCIQMCCI.time))
    f.write('memoryfacpart 2.0\n')
    f.write('memoryfacspawn 1.0\n')
    f.write('totalwalkers %i\n'%(FCIQMCCI.maxwalkers))
    f.write('nmcyc %i\n'%(FCIQMCCI.maxIter))
    if (Restart):
        f.write('readpops')
    else :
        f.write('startsinglepart 500\n')
        f.write('diagshift 0.1\n')
    f.write('rdmsamplingiters %i\n'%(FCIQMCCI.RDMSamples))
    f.write('shiftdamp 0.05\n')
    if (FCIQMCCI.tau != -1.0):
        f.write('tau 0.01\n')
    f.write('truncinitiator\n')
    f.write('addtoinitiator 3\n')
    f.write('allrealcoeff\n')
    f.write('realspawncutoff 0.4\n')
    f.write('semi-stochastic 1000\n')
    f.write('trial-wavefunction 500\n')
    f.write('jump-shift\n')
    f.write('proje-changeref 1.5\n')
    f.write('stepsshift 10\n')
    f.write('maxwalkerbloom 2\n')
    f.write('endcalc\n')
    f.write('\n')
    f.write('integral\n')
    f.write('freeze 0,0\n')
    f.write('endint\n')
    f.write('\n')
    f.write('logging\n')
    f.write('popsfiletimer 60.0\n')
    f.write('binarypops\n')
    f.write('calcrdmonfly 3 100 500\n')
    f.write('write-spin-free-rdm\n') 
    f.write('endlog\n') 
    f.write('end\n')

    f.close()
    #no reorder
    #f.write('noreorder\n')

def writeIntegralFile(h1eff, eri_cas, ncas, neleca, nelecb, FCIQMCCI):
    integralFile = os.path.join(FCIQMCCI.scratchDirectory,FCIQMCCI.integralFile)
# ensure 4-fold symmetry
    eri_cas = pyscf.ao2mo.restore(4, eri_cas, ncas)
    if FCIQMCCI.mol.symmetry and FCIQMCCI.orbsym:
        orbsym = [IRREP_MAP[FCIQMCCI.groupname][i] for i in FCIQMCCI.orbsym]
    else:
        orbsym = []
    pyscf.tools.fcidump.from_integrals(integralFile, h1eff, eri_cas, ncas,
                                       neleca+nelecb, ms=abs(neleca-nelecb),
                                       orbsym=orbsym,tol=1e-10)



def executeFCIQMC(FCIQMCCI):
    inFile = os.path.join(FCIQMCCI.scratchDirectory,FCIQMCCI.configFile)
    outFile = os.path.join(FCIQMCCI.scratchDirectory,FCIQMCCI.outputFile)
    from subprocess import call
    call("%s  %s > %s"%(FCIQMCCI.executable, inFile, outFile), shell=True)

def readEnergy(FCIQMCCI):
    file1 = open(os.path.join(FCIQMCCI.scratchDirectory, FCIQMCCI.outputFile),"r")
    for line in file1:
        if "*TOTAL ENERGY* CALCULATED USING THE" in line:
            calc_e = float(line.split()[-1])
            break
    logger.info(FCIQMCCI, 'total energy from fciqmc: %.15f', calc_e)
    file1.close()

    return calc_e



if __name__ == '__main__':
    from pyscf import gto
    from pyscf import scf
    from pyscf import mcscf

    b = 1.4
    mol = gto.Mole()
    mol.build(
        verbose = 5,
        output = 'out-fciqmc',
        atom = [['H', (0.,0.,i)] for i in range(8)],
        basis = {'H': 'sto-3g'},
        symmetry = True,
    )
    m = scf.RHF(mol)
    m.scf()

    mc = mcscf.CASSCF(m, 4, 4)
    mc.fcisolver = FCIQMCCI(mol)
    mc.fcisolver.tau = 0.01
    mc.fcisolver.RDMSamples = 1000
    mc.max_cycle_macro = 10
    emc_1 = mc.mc2step()[0]

    mc = mcscf.CASCI(m, 4, 4)
    mc.fcisolver = FCIQMCCI(mol)
    mc.fcisolver.tau = 0.01
    mc.fcisolver.RDMSamples = 1000
    emc_0 = mc.casci()[0]

    b = 1.4
    mol = gto.Mole()
    mol.build(
        verbose = 5,
        output = 'out-casscf',
        atom = [['H', (0.,0.,i)] for i in range(8)],
        basis = {'H': 'sto-3g'},
        symmetry = True,
    )
    m = scf.RHF(mol)
    m.scf()

    mc = mcscf.CASSCF(m, 4, 4)
    emc_1ref = mc.mc2step()[0]

    mc = mcscf.CASCI(m, 4, 4)
    emc_0ref = mc.casci()[0]

    print('FCIQMCCI  = %.15g CASCI  = %.15g' % (emc_0, emc_0ref))
    print('FCIQMCSCF = %.15g CASSCF = %.15g' % (emc_1, emc_1ref))

