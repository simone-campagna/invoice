#!/usr/bin/env python3

# 
#  Copyright 2013 Simone Campagna
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
LockFile class - opens and locks a file.
"""
__author__ = 'Simone Campagna'
__copyright__ = 'Copyright (c) 2013 Simone Campagna'
__license__ = 'Apache License Version 2.0'
__version__ = '1.0'

import os
import fcntl
import time
import errno
import signal
import sys
import io


__author__ = "Simone Campagna"

class LockError(Exception): # pragma: no cover
    """Lock error"""
    pass


class LockFile(io.FileIO): # pragma: no cover
    """Open and locks a file.

       Parameters
       ----------
       name: str
           the file name
       mode: str, optional
           the open mode (defaults to 'w')
       blocking: bool, optional
           enables blocking acquisition
       timeout: float, optional
           timeout for non-blocking acquisition
    """
    def __init__(self, name, mode='w', blocking=True, timeout=10.0):
      super().__init__(name, mode)
      self.blocking = blocking
      self.timeout = timeout
  
    def acquire(self, blocking=None, timeout=None):
        """Acquires the lock.

           Parameters
           ----------
           blocking: bool, optional
               if True blocks until lock can be acquired
           timeout: float, optional
               timeout used when blocking == False
        """

        if blocking is None:
            blocking = self.blocking
        if timeout is None:
            timeout = self.timeout
    
        lock_op = fcntl.LOCK_EX
        if not blocking:
            lock_op += fcntl.LOCK_NB
        count = 0
        interval = 0.1
        if timeout is not None:
            count = int(round(timeout/interval, 0))
        if count <= 0:
            count = 1
        for i in range(count):
            try:
                #fcntl.fcntl(self.fileno(), lock_op, os.O_NDELAY)
                fcntl.lockf(self.fileno(), lock_op)
                return True
            except IOError as e:
                if e.errno in (errno.EACCES, errno.EAGAIN):
                    if timeout:
                        time.sleep(interval)
                    continue
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                import traceback
                traceback.print_exc()
                time.sleep(interval)
        return False
  
    def release(self):
        """Releases the lock."""
        fcntl.lockf(self, fcntl.LOCK_UN)
  
    def is_locked(self):
        """Tells if file is locked.
           Returns
           -------
           bool
               True if file is locked
        """
        try:
            fcntl.lockf(self.fileno(), fcntl.LOCK_EX + fcntl.LOCK_NB)
            return False
        except IOError as e:
            if e.errno in (errno.EACCES, errno.EAGAIN):
              return True
  
    def close(self):
        """Closes the file."""
        self.release()
        super(LockFile, self).close()
  
    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
