# -*- coding: utf-8 -*-
# Copyright (C) 2008-2017, Luis Pedro Coelho <luis@luispedro.org>
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
file_store_monitor : part of file_store to keep locks alive during execution
'''

from os import utime, getppid, kill
from sys import argv
from time import sleep


def parent_gone_or_changed(pid):
    current_parent = getppid()
    if current_parent != pid or current_parent == 1:
        # A different parent means parent died and/or we got disowned, neither
        # of which should happen in normal conditions
        # If PID 1 we are running under init and that also means we got disowned
        return True

    # Test if parent is still alive
    try:
        kill(pid, 0)
    except OSError:
        return True
    else:
        return False


def main():
    lock = argv[1]
    parent = getppid()
    # 5 * 60 = once every 5 minutes
    counter = counter_start = 60

    while True:
        # self check every 5 seconds
        sleep(5)

        # We die if our parent went away
        if parent_gone_or_changed(parent):
            break

        # but only update the lock once every 5 minutes for IO reasons
        counter -= 1

        if counter <= 0:
            counter = counter_start
            try:
                utime(lock, None)
            except OSError:
                # Lock is no longer available
                break


if __name__ == '__main__':
    main()
