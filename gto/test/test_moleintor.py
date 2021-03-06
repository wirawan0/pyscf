#!/usr/bin/env python

import unittest
from pyscf import gto

mol = gto.Mole()
mol.verbose = 0
mol.output = None#"out_h2o"
mol.atom = [
    ["C", (-0.65830719,  0.61123287, -0.00800148)],
    ["C1", ( 0.73685281,  0.61123287, -0.00800148)],
    ["C2", ( 1.43439081,  1.81898387, -0.00800148)],
    ["C3", ( 0.73673681,  3.02749287, -0.00920048)],
    ["C4", (-0.65808819,  3.02741487, -0.00967948)],
    ["C5", (-1.35568919,  1.81920887, -0.00868348)],
    ["H", (-1.20806619, -0.34108413, -0.00755148)],
    ["H", ( 1.28636081, -0.34128013, -0.00668648)],
    ["H", ( 2.53407081,  1.81906387, -0.00736748)],
    ["H", ( 1.28693681,  3.97963587, -0.00925948)],
    ["H", (-1.20821019,  3.97969587, -0.01063248)],
    ["H", (-2.45529319,  1.81939187, -0.00886348)],]

mol.basis = {'H': 'cc-pvdz',
             'C1': 'CC PVDZ',
             'C2': 'CC PVDZ',
             'C3': 'cc-pVDZ',
             'C4': gto.basis.parse('''
#BASIS SET: (9s,4p,1d) -> [3s,2p,1d]
C    S
   6665.0000000              0.0006920             -0.0001460        
   1000.0000000              0.0053290             -0.0011540        
    228.0000000              0.0270770             -0.0057250        
     64.7100000              0.1017180             -0.0233120        
     21.0600000              0.2747400             -0.0639550        
      7.4950000              0.4485640             -0.1499810        
      2.7970000              0.2850740             -0.1272620        
      0.5215000              0.0152040              0.5445290        
C    S
      0.1596000              1.0000000        
C    P
      9.4390000              0.0381090        
      2.0020000              0.2094800        
      0.5456000              0.5085570        
C    P
      0.1517000              1.0000000        
C    D
      0.5500000              1.0000000        '''),
             'C': 'CC PVDZ',}
mol.build()

def finger(mat):
    return abs(mat).sum()


class KnowValues(unittest.TestCase):
    def test_intor_nr(self):
        s = mol.intor('cint1e_ovlp_sph')
        self.assertAlmostEqual(finger(s), 497.34740945610434, 11)

    def test_intor_nr1(self):
        s = mol.intor_symmetric('cint1e_ovlp_sph')
        self.assertAlmostEqual(finger(s), 497.34740945610434, 11)

    def test_intor_nr2(self):
        s = mol.intor_asymmetric('cint1e_ovlp_sph')
        self.assertAlmostEqual(finger(s), 497.34740945610434, 11)

    def test_intor_nr_cross(self):
        bra = range(mol.nbas//4)
        ket = range(mol.nbas//4, mol.nbas)
        s = mol.intor_cross('cint1e_ovlp_sph', bra, ket)
        self.assertAlmostEqual(finger(s), 80.608860927958361, 11)

    def test_intor_r(self):
        s = mol.intor('cint1e_ovlp')
        self.assertAlmostEqual(finger(s), 1282.9000123790504, 11)

    def test_intor_r1(self):
        s = mol.intor_symmetric('cint1e_ovlp')
        self.assertAlmostEqual(finger(s), 1282.9000123790504, 11)

    def test_intor_r2(self):
        s = mol.intor_asymmetric('cint1e_ovlp')
        self.assertAlmostEqual(finger(s), 1282.9000123790504, 11)

    def test_intor_r_comp(self):
        s = mol.intor('cint1e_ipkin', comp=3)
        self.assertAlmostEqual(finger(s), 3070.844024815065, 11)


if __name__ == "__main__":
    unittest.main()
