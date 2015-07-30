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

class LockFile(io.FileIO): # pragma: no cover
  def __init__(self, name, mode='w'):
    super().__init__(name, mode)

  def acquire(self, blocking=None, timeout=None):
    #sys.stderr.write("LockFile::ACQUIRE\n")
    if blocking is None:
      if timeout is None:
        blocking = True
      else:
        blocking = False

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
      except:
        import traceback
        traceback.print_exc()
        time.sleep(interval)
    return False

  #def acquire_nb(self):
  #  try:
  #    fcntl.lockf(self, fcntl.LOCK_EX + fcntl.LOCK_NB)
  #    return True
  #  except IOError as e:
  #    return False

  def release(self):
    fcntl.lockf(self, fcntl.LOCK_UN)
    pass

  def is_locked(self):
    try:
      fcntl.lockf(self.fileno(), fcntl.LOCK_EX + fcntl.LOCK_NB)
      return False
    except IOError as e:
      if e.errno in (errno.EACCES, errno.EAGAIN):
        return True

  def close(self):
      self.release()
      super(LockFile, self).close()

  def __del__(self):
      try:
          self.release()
      except:
          pass
      try:
          super(LockFile, self).__del__()
      except:
          pass
