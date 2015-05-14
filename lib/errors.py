#!/usr/bin/env python
#

'''
Error handling facility for pyscf

Exceptions defined

'''

class PyscfError(StandardError):
    '''Generic error related to pyscf.'''
    pass

class PyscfParseError(PyscfError):
    '''Error related data/text parsing in pyscf.'''
    pass
