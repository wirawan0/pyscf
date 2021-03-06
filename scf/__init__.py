#!/usr/bin/env python
# -*- coding: utf-8
# Author: Qiming Sun <osirpt.sun@gmail.com>

'''Non-relativistic and relativistic Hartree-Fock

Simple usage::

    >>> from pyscf import gto, scf
    >>> mol = gto.M(atom='H 0 0 0; H 0 0 1')
    >>> mf = scf.RHF(mol)
    >>> mf.scf()

:func:`scf.RHF` returns an instance of SCF class.  There are some parameters
to control the SCF method.

    verbose : int
        Print level.  Default value equals to :class:`Mole.verbose`
    max_memory : float or int
        Allowed memory in MB.  Default value equals to :class:`Mole.max_memory`
    chkfile : str
        checkpoint file to save MOs, orbital energies etc.
    conv_tol : float
        converge threshold.  Default is 1e-10
    max_cycle : int
        max number of iterations.  Default is 50
    init_guess : str
        initial guess method.  It can be one of 'minao', 'atom', '1e', 'chkfile'.
        Default is 'minao'
    DIIS : class listed in :mod:`scf.diis`
        DIIS model.  Default is :class:`diis.SCF_DIIS`. Set it to None to
        turn off DIIS.
    diis_space : int
        DIIS space size.  By default, 8 Fock matrices and errors vector are stored.
    diis_start_cycle : int
        The step to start DIIS.  Default is 3.
    level_shift_factor : float or int
        Level shift (in AU) for virtual space.  Default is 0.
    direct_scf : bool
        Direct SCF is used by default.
    direct_scf_tol : float
        Direct SCF cutoff threshold.  Default is 1e-13.

    nelectron_alpha : int, for UHF class only
        number of alpha electrons.  By default it is determined by the orbital
        energy spectrum.  It only affects UHF class.

    irrep_nelec : dict, for symmetry- RHF/ROHF/UHF class only
        to indicate the number of electrons for each irreps.
        In RHF, give {'ir_name':int, ...} ;
        In ROHF/UHF, give {'ir_name':(int,int), ...} .
        It is effective when :attr:`Mole.symmetry` is set ``True``.

    auxbasis : str, for density fitting SCF only
        Auxiliary basis for density fitting.  Default is 'Weigend' fitting basis.
        It is effective when the SCF class is decoreated by :func:`density_fit`::

        >>> mf = scf.density_fit(scf.UHF(mol))
        >>> mf.scf()

        Density fitting can be applied to all non-relativistic HF class.

    with_ssss : bool, for Dirac-Hartree-Fock only
        If False, ignore small component integrals (SS|SS).  Default is True.
    with_gaunt : bool, for Dirac-Hartree-Fock only
        If False, ignore Gaunt interaction.  Default is False.

Saved results

    converged : bool
        SCF converged or not
    hf_energy : float
        Total HF energy (electronic energy plus nuclear repulsion)
    mo_energy : 
        Orbital energies
    mo_occ
        Orbital occupancy
    mo_coeff
        Orbital coefficients

'''

from pyscf.scf import hf
from pyscf.scf import hf as rhf
from pyscf.scf import hf_symm
from pyscf.scf import hf_symm as rhf_symm
from pyscf.scf import uhf
from pyscf.scf import uhf_symm
from pyscf.scf import dhf
from pyscf.scf import chkfile
from pyscf.scf import diis
from pyscf.scf import addons
from pyscf.scf.dfhf import density_fit, density_fit_
from pyscf.scf.uhf import spin_square
from pyscf.scf.hf import get_init_guess
from pyscf.scf.addons import *



def RHF(mol, *args):
    '''This is a wrap function to decide which SCF class to use, RHF or ROHF
    '''
    if mol.nelectron == 1:
        return rhf.HF1e(mol)
    elif not mol.symmetry or mol.groupname is 'C1':
        if mol.spin > 0:
            return rhf.ROHF(mol, *args)
        else:
            return rhf.RHF(mol, *args)
    else:
        if mol.spin > 0:
            return rhf_symm.ROHF(mol, *args)
        else:
            return rhf_symm.RHF(mol, *args)

def ROHF(mol, *args):
    '''This is a wrap function to decide which ROHF class to use.
    '''
    if mol.nelectron == 1:
        return rhf.HF1e(mol)
    elif not mol.symmetry or mol.groupname is 'C1':
        return rhf.ROHF(mol, *args)
    else:
        return hf_symm.ROHF(mol, *args)

def UHF(mol, *args):
    '''This is a wrap function to decide which UHF class to use.
    '''
    if mol.nelectron == 1:
        return rhf.HF1e(mol)
    elif not mol.symmetry or mol.groupname is 'C1':
        return uhf.UHF(mol, *args)
    else:
        return uhf_symm.UHF(mol, *args)

def DHF(mol, *args):
    '''This is a wrap function to decide which Dirac-Hartree-Fock class to use.
    '''
    if mol.nelectron == 1:
        return dhf.HF1e(mol)
    else:
        return dhf.UHF(mol, *args)


