# -*- coding: utf-8 -*-
# Copyright (C) 2011-2013, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

'''
This module details all the operations that are necessary to implement a jug
backend.

It can be used as a starting point (template) for writing new backends.
'''

from abc import ABCMeta, abstractmethod

class base_store(object):
    __metaclass__ = ABCMeta
    def __init__(self, name):
        '''
        base_store(name)

        Initialise a backend

        Parameters
        ----------
        name : str
            Internal name to use
        '''

    @abstractmethod
    def dump(self, object, name):
        '''
        store.dump(object, name)

        Saves the object to the backend

        Parameters
        ----------
        object : anything
        name : str
            Key to use
        '''

    @abstractmethod
    def list(self):
        '''
        for key in store.list():
            ...

        Iterates over all the keys in the store
        '''


    @abstractmethod
    def can_load(self, name):
        '''
        can = store.can_load(name)

        Parameters
        ----------
        name : str
            Key to use

        Returns
        -------
        can : bool
        '''

    @abstractmethod
    def load(self, name):
        '''
        obj = store.load(name)

        Loads one object from the store.

        Parameters
        ----------
        name : str
            Key to use

        Returns
        -------
        obj : any
            The object that was saved under ``name``
        '''

    @abstractmethod
    def remove(self, name):
        '''
        was_removed = store.remove(name)

        Remove the entry associated with ``name``.

        Returns whether any entry was actually removed.

        Parameters
        ----------
        name : str
            Key

        Returns
        -------
        was_removed : bool
            Whether the key was present
        '''

    @abstractmethod
    def cleanup(self, active):
        '''
        nr_removed = store.cleanup(active)

        Implement 'cleanup' command

        Parameters
        ----------
        active : sequence
            files *not to remove*

        Returns
        -------
        nr_removed : integer
            number of removed files
        '''


    @abstractmethod
    def remove_locks(self):
        '''
        removed = store.remove_locks()

        Remove all locks

        Returns
        -------
        removed : int
            Number of locks removed
        '''


    @abstractmethod
    def getlock(self, name):
        '''
        lock = store.getlock(name)

        Retrieve a lock object associated with ``name``.

        Parameters
        ----------
        name : str
            Key

        Returns
        -------
        lock : Lock object
            This should obey the Lock Interface

        See Also
        --------
        base_lock : Generic lock
        '''

    @abstractmethod
    def close(self):
        '''
        store.close()

        Close the connection.

        Mayb be a no-op.
        '''

    @staticmethod
    def remove_store(jugdir):
        '''
        store_class.remove_store(jugdir)

        Removes all that is associated with the store identified by ``jugdir``.

        For example, it might remove files on disk, drop tables on the
        database, &c
        '''

    def metadata(self, t):
        return None


class base_lock(object):
    __metaclass__ = ABCMeta
    '''

    Functions:
    ----------

    - get(): acquire the lock
    - release(): release the lock
    - is_locked(): check lock state
    '''

    def __init__(self):
        '''
        A lock class does not need to have an __init__ method with any specific
        signature. It is only to be used from *within* store.lock().
        '''

    @abstractmethod
    def get(self):
        '''
        locked = lock.get()

        Try to atomically create a lock

        Parameters
        ----------
        None

        Returns
        -------
        locked : bool
            Whether the lock was created
        '''

    @abstractmethod
    def release(self):
        '''
        lock.release()

        Releases lock
        '''

    @abstractmethod
    def is_locked(self):
        '''
        locked = lock.is_locked()

        Returns whether a lock exists for name. Note that the answer can
        be invalid by the time this function returns. Only by trying to
        acquire the lock can you avoid race-conditions. See the get() function.

        This function is provided only because it might be possible to have a
        fast check before calling the expensive locking operation.

        Returns
        -------
        locked : boolean
        '''

