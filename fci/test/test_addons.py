#!/usr/bin/env python

import unittest
import numpy
from pyscf import gto
from pyscf import scf
from pyscf import ao2mo
from pyscf import fci

mol = gto.Mole()
mol.verbose = 0
mol.atom = '''
      H     1  -1.      0
      H     0  -1.     -1
      H     0  -0.5    -0
      H     0  -0.     -1
      H     1  -0.5     0
      H     0   1.      1'''
mol.basis = 'sto-3g'
mol.build()
m = scf.RHF(mol)
ehf = m.scf()
norb = m.mo_coeff.shape[1]
nelec = mol.nelectron
h1e = reduce(numpy.dot, (m.mo_coeff.T, m.get_hcore(), m.mo_coeff))
g2e = ao2mo.incore.general(m._eri, (m.mo_coeff,)*4, compact=False)
na = fci.cistring.num_strings(norb, nelec//2)
e, ci0 = fci.direct_spin1.kernel(h1e, g2e, norb, nelec)

class KnowValues(unittest.TestCase):
    def test_large_ci(self):
        res = fci.addons.large_ci(ci0, norb, nelec, tol=.1)
        refstr =[('0b111'  , '0b111'  ),
                 ('0b111'  , '0b1011' ),
                 ('0b1011' , '0b111'  ),
                 ('0b1011' , '0b1011' ),
                 ('0b10101', '0b10101')]
        refci = [0.868485545310, 0.151306658009, 0.151306658009,
                 -0.36620091020, -0.10306163008]
        self.assertTrue(numpy.allclose([x[0] for x in res], refci))
        self.assertEqual([x[1:] for x in res], refstr)

    def test_init_triplet(self):
        ci1 = fci.addons.initguess_triplet(norb, nelec, '0b1011')
        self.assertAlmostEqual(abs(ci1 + ci1.T).sum(), 0)
        self.assertTrue(ci1[0,1] < 0)

    def test_credes_ab(self):
        a4 = 10*numpy.arange(4)[:,None]
        a6 = 10*numpy.arange(6)[:,None]
        b4 = numpy.arange(4)
        b6 = numpy.arange(6)
        self.assertTrue(numpy.allclose(fci.addons.des_a(a4+b4, 4, 6, 0),
                                        [[  0.,  0.,  0.,  0.],
                                         [  0.,  0.,  0.,  0.],
                                         [  0.,  1.,  2.,  3.],
                                         [  0.,  0.,  0.,  0.],
                                         [ 10., 11., 12., 13.],
                                         [ 20., 21., 22., 23.]]))
        self.assertTrue(numpy.allclose(fci.addons.des_a(a4+b4, 4, 6, 1),
                                        [[  0.,  0.,  0.,  0.],
                                         [  0., -1., -2., -3.],
                                         [  0.,  0.,  0.,  0.],
                                         [-10.,-11.,-12.,-13.],
                                         [  0.,  0.,  0.,  0.],
                                         [ 30., 31., 32., 33.]]))
        self.assertTrue(numpy.allclose(fci.addons.des_a(a4+b4, 4, 6, 2),
                                        [[  0.,  1.,  2.,  3.],
                                         [  0.,  0.,  0.,  0.],
                                         [  0.,  0.,  0.,  0.],
                                         [-20.,-21.,-22.,-23.],
                                         [-30.,-31.,-32.,-33.],
                                         [  0.,  0.,  0.,  0.]]))
        self.assertTrue(numpy.allclose(fci.addons.des_a(a4+b4, 4, 6, 3),
                                        [[ 10., 11., 12., 13.],
                                         [ 20., 21., 22., 23.],
                                         [ 30., 31., 32., 33.],
                                         [  0.,  0.,  0.,  0.],
                                         [  0.,  0.,  0.,  0.],
                                         [  0.,  0.,  0.,  0.]]))
        self.assertTrue(numpy.allclose(fci.addons.des_b(a6+b4, 4, (2,3), 0),
                                        [[  0.,  0.,  0.,  0.,  1.,  2.],
                                         [  0.,  0., 10.,  0., 11., 12.],
                                         [  0.,  0., 20.,  0., 21., 22.],
                                         [  0.,  0., 30.,  0., 31., 32.],
                                         [  0.,  0., 40.,  0., 41., 42.],
                                         [  0.,  0., 50.,  0., 51., 52.]]))
        self.assertTrue(numpy.allclose(fci.addons.des_b(a6+b4, 4, (2,3), 1),
                                        [[  0.,  0.,  0., -1.,  0.,  3.],
                                         [  0.,-10.,  0.,-11.,  0., 13.],
                                         [  0.,-20.,  0.,-21.,  0., 23.],
                                         [  0.,-30.,  0.,-31.,  0., 33.],
                                         [  0.,-40.,  0.,-41.,  0., 43.],
                                         [  0.,-50.,  0.,-51.,  0., 53.]]))
        self.assertTrue(numpy.allclose(fci.addons.des_b(a6+b4, 4, (2,3), 2),
                                        [[  0.,  0.,  0., -2., -3.,  0.],
                                         [ 10.,  0.,  0.,-12.,-13.,  0.],
                                         [ 20.,  0.,  0.,-22.,-23.,  0.],
                                         [ 30.,  0.,  0.,-32.,-33.,  0.],
                                         [ 40.,  0.,  0.,-42.,-43.,  0.],
                                         [ 50.,  0.,  0.,-52.,-53.,  0.]]))
        self.assertTrue(numpy.allclose(fci.addons.des_b(a6+b4, 4, (2,3), 3),
                                        [[  1.,  2.,  3.,  0.,  0.,  0.],
                                         [ 11., 12., 13.,  0.,  0.,  0.],
                                         [ 21., 22., 23.,  0.,  0.,  0.],
                                         [ 31., 32., 33.,  0.,  0.,  0.],
                                         [ 41., 42., 43.,  0.,  0.,  0.],
                                         [ 51., 52., 53.,  0.,  0.,  0.]]))
        self.assertTrue(numpy.allclose(fci.addons.cre_a(a6+b4, 4, (2,3), 0),
                                        [[ 20., 21., 22., 23.],
                                         [ 40., 41., 42., 43.],
                                         [ 50., 51., 52., 53.],
                                         [  0.,  0.,  0.,  0.]]))
        self.assertTrue(numpy.allclose(fci.addons.cre_a(a6+b4, 4, (2,3), 1),
                                        [[-10.,-11.,-12.,-13.],
                                         [-30.,-31.,-32.,-33.],
                                         [  0.,  0.,  0.,  0.],
                                         [ 50., 51., 52., 53.]]))
        self.assertTrue(numpy.allclose(fci.addons.cre_a(a6+b4, 4, (2,3), 2),
                                        [[  0.,  1.,  2.,  3.],
                                         [  0.,  0.,  0.,  0.],
                                         [-30.,-31.,-32.,-33.],
                                         [-40.,-41.,-42.,-43.]]))
        self.assertTrue(numpy.allclose(fci.addons.cre_a(a6+b4, 4, (2,3), 3),
                                        [[  0.,  0.,  0.,  0.],
                                         [  0.,  1.,  2.,  3.],
                                         [ 10., 11., 12., 13.],
                                         [ 20., 21., 22., 23.]]))
        self.assertTrue(numpy.allclose(fci.addons.cre_b(a6+b6, 4, 4, 0),
                                        [[  2.,  4.,  5.,  0.],
                                         [ 12., 14., 15.,  0.],
                                         [ 22., 24., 25.,  0.],
                                         [ 32., 34., 35.,  0.],
                                         [ 42., 44., 45.,  0.],
                                         [ 52., 54., 55.,  0.]]))
        self.assertTrue(numpy.allclose(fci.addons.cre_b(a6+b6, 4, 4, 1),
                                        [[ -1., -3.,  0.,  5.],
                                         [-11.,-13.,  0., 15.],
                                         [-21.,-23.,  0., 25.],
                                         [-31.,-33.,  0., 35.],
                                         [-41.,-43.,  0., 45.],
                                         [-51.,-53.,  0., 55.]]))
        self.assertTrue(numpy.allclose(fci.addons.cre_b(a6+b6, 4, 4, 2),
                                        [[  0.,  0., -3., -4.],
                                         [ 10.,  0.,-13.,-14.],
                                         [ 20.,  0.,-23.,-24.],
                                         [ 30.,  0.,-33.,-34.],
                                         [ 40.,  0.,-43.,-44.],
                                         [ 50.,  0.,-53.,-54.]]))
        self.assertTrue(numpy.allclose(fci.addons.cre_b(a6+b6, 4, 4, 3),
                                        [[  0.,  0.,  1.,  2.],
                                         [  0., 10., 11., 12.],
                                         [  0., 20., 21., 22.],
                                         [  0., 30., 31., 32.],
                                         [  0., 40., 41., 42.],
                                         [  0., 50., 51., 52.]]))


if __name__ == "__main__":
    print("Full Tests for fci.addons")
    unittest.main()


