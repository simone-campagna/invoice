#!/usr/bin/env python

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

import collections
import os
import fcntl
import time
import errno
import atexit
import signal
import sys

try:
    import prctl
    HAS_PRCTL = True
except ImportError:
    HAS_PRCTL = False

from .lock_file import LockFile

class DaemonError(Exception):
  pass

LockInfo = collections.namedtuple('LockInfo', ('locked', 'host', 'pid'))
class Daemon(object):
  INTERACTIVE_ACTIONS = ['start', 'restart', 'restore']
  ACTIONS = ['start', 'stop', 'abort', 'status', 'restart', 'restore', 'is_running', 'is_locked', 'lock_info', 'lock_wait']
  ACTION_MAP = {}
  def __init__(self,
			lock_file,
			stdin=None,
			stdout=None,
			stdout_mode='ab+',
			stderr=None,
			stderr_mode='ab+',
			name=None,
			lock_blocking=None,
			lock_timeout=None,
			interactive=False
    		):
    self.lock_file = LockFile(lock_file, 'a+')
    self.lock_blocking = lock_blocking
    self.lock_timeout = lock_timeout
    self.interactive = interactive
    self.name = name
    if self.name is None:
        self.label = self.__class__.__name__
    else:
        self.label = self.name
    
    if stdin is None:
      stdin = '/dev/null'
    if stdout is None:
      stdout = '/dev/null'
    if stderr is None:
      stderr = '/dev/null'
    self.stdin = stdin
    self.stdout = stdout
    self.stderr = stderr
    self.stdout_mode = stdout_mode
    self.stderr_mode = stderr_mode

  def daemonize(self):
    """
    do the UNIX double-fork magic, see Stevens' "Advanced
    Programming in the UNIX Environment" for details (ISBN 0201563177)
    http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
    """
    if self.interactive:
      return

    try:
      pid = os.fork()
      if pid > 0:
        # exit first parent
        sys.exit(0)
    except OSError as e:
      sys.stderr.write("fork #1 failed: {0:d} ({1})\n".format(e.errno, e.strerror))
      raise DaemonError("Fork #1 failed")

    # decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # do second fork
    try:
      pid = os.fork()
      if pid > 0:
        # exit from second parent
        sys.exit(0)
    except OSError as e:
      sys.stderr.write("fork #2 failed: {0:d} ({1})\n".format(e.errno, e.strerror))
      raise DaemonError("Fork #2 failed")

    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    self.stderr_mode = 'w+'
    si = open(self.stdin, 'r')
    so = open(self.stdout, self.stdout_mode)
    if 'b' in self.stderr_mode.lower():
        se = open(self.stderr, self.stderr_mode, 0)
    else:
        se = open(self.stderr, self.stderr_mode)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    # set name
    if self.name is not None:
        try:
            if HAS_PRCTL:
                prctl.set_name(self.name)
                prctl.set_proctitle(self.name)
            else:
                from ctypes import cdll
                libc = cdll.LoadLibrary("libc.so.6") 
                libc.prctl(15, self.name, 0, 0, 0)
        except:
            pass
            
    # write lock
    atexit.register(self._release_lock)
    self.lock_file.acquire(blocking=self.lock_blocking, timeout=self.lock_timeout)
    self._write_lock_data()

  def _hostname(self):
    return os.uname()[1]

  def _pid(self):
    return os.getpid()

  def _data(self):
    return self._hostname(), self._pid()

  def get_lock_info(self):
    hostname, pid = self._data()
    return "{0}:{1}".format(hostname, pid)

  def _write_lock_data(self):
    self._empty_lock_file()
    self.lock_file.write(bytes("{0}\n".format(self.get_lock_info()), 'utf-8'))
    self.lock_file.flush()

  def _read_lock_data(self):
    try:
      self.lock_file.seek(0)
      content = str(self.lock_file.readline(), 'utf-8').strip()
    except (IOError, OSError) as e:
      return None, None
    data = content.split(":", 1)
    if len(data) <= 1:
      return None, None
    l_hostname, l_pid_s = data
    try:
      l_pid = int(l_pid_s)
    except ValueError as e:
      raise DaemonError("Invalid lock file content: '{0}'".format(content))
    return l_hostname, l_pid

  def _check_same_node(self, ignore_errors=False):
    l_hostname, l_pid = self._read_lock_data()
    hostname, pid = self._data()
    result = True
    if l_hostname is not None and l_hostname != hostname:
      result = False
      if not ignore_errors:
        raise DaemonError("locked on different node (lock: '{0}', current: '{0}')".format(l_hostname, hostname))
    return result, l_hostname, l_pid, hostname, pid

  def _empty_lock_file(self):
    self.lock_file.seek(0)
    self.lock_file.truncate()
    self.lock_file.flush()

  def is_locked(self):
    return self.lock_file.is_locked()

  def lock_wait(self):
    while self.lock_file.is_locked():
      time.sleep(1)
    return True

  def lock_info(self):
    locked = self.lock_file.is_locked()
    l_hostname, l_pid = self._read_lock_data()
    return LockInfo(locked, l_hostname, l_pid)

  def _release_lock(self):
    #l_hostname, l_pid = self._read_lock_data()
    #hostname, pid = self._data()
    #if l_hostname != hostname:
    #  raise DaemonError, "Cannot release lock acquired by {0}:{1} from {2}".format(l_hostname, l_pid, hostname)
    self.lock_file.release()
    self._empty_lock_file()
    self.lock_file.close()

  def start(self):
    if self.interactive:
      try:
        self._check_same_node(ignore_errors=False)
        acquired = self.lock_file.acquire(blocking=self.lock_blocking, timeout=self.lock_timeout)
        if not acquired:
          raise DaemonError("Lock failed")
        self.run()
      finally:
        self.lock_file.release()
      return True
    try:
      self._check_same_node(ignore_errors=False)
      acquired = self.lock_file.acquire(blocking=self.lock_blocking, timeout=self.lock_timeout)
      if not acquired:
        raise DaemonError("Lock failed")
      #print "P: acquire", os.getpid(), acquired
      child_pid = os.fork() 
      if child_pid > 0:
        # exit first parent
        self.lock_file.release()
        #print "P: released", child_pid
        os.waitpid(child_pid, 0)
        return self.status()
        return True
      else:
        self._check_same_node(ignore_errors=False)
        acquired = self.lock_file.acquire(blocking=self.lock_blocking, timeout=self.lock_timeout)
        #print "C: acquire", os.getpid(), acquired
        if not acquired:
          raise DaemonError("Lock failed")
        self.lock_file.release()
        #print "C: released"
        self.daemonize()
        self.run()
        sys.exit(0)
    except OSError as e:
      sys.stderr.write("fork #1 failed: {0:d} ({1})\n".format(e.errno, e.strerror))
      raise DaemonError("Fork #1 failed")

  def run(self):
    pass

  def soft_stop(self):
    result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
    try:
        os.kill(l_pid, signal.SIGTERM)
    except OSError:
        pass

  def hard_stop(self):
    result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
    try:
        os.kill(l_pid, signal.SIGKILL)
    except OSError:
        pass

  def stop(self, soft_timeout_seconds=20, soft_interval=0.2, hard_timeout_seconds=5, hard_interval=0.2):
    i_time = time.time()
    mode_data = {
	'soft':	(soft_timeout_seconds, soft_interval, self.soft_stop),
	'hard':	(hard_timeout_seconds, hard_interval, self.hard_stop),
    }
    modes = ['soft', 'hard']
    for mode in modes:
        if not self.lock_file.is_locked():
            self._empty_lock_file()
            return self.status()
        timeout_seconds, interval, stop_function = mode_data[mode]
        stop_function()
        while True:
            if not self.lock_file.is_locked():
                self._empty_lock_file()
                return self.status()
            if (time.time() - i_time) > timeout_seconds:
                break
            else:
                time.sleep(interval)
    return self.status()

  def abort(self):
    return self.stop(soft_timeout_seconds=0, soft_interval=0.1, hard_timeout_seconds=0.0, hard_interval=0.1)

  #def __del__(self):
  #  self._empty_lock_file()

  def restart(self):
    result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
    self.stop()
    return self.start()

  def is_running(self):
    result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
    return self.lock_file.is_locked()

  def status(self):
    result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=True)
    if result:
      locked = self.lock_file.is_locked()
      if locked:
        l_hostname, l_pid = self._read_lock_data()
        return "{0} is running by {1}:{2}".format(self.label, l_hostname, l_pid)
      else:
        return "{0} is not running".format(self.label)
    else:
      return "{0} has been started on a different node {1}:{2}, status cannot be checked".format(self.label, l_hostname, l_pid)


  def restore(self):
    result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
    if result:
      locked = self.lock_file.is_locked()
      if locked:
        # running
        return (True, None)
      else:
        l_hostname, l_pid = self._read_lock_data()
        if l_hostname is None and l_pid is None:
          # should not be running
          return (False, None)
        else:
          # should be running, but it isn't
          self.start()
          return (True, 'start')
  
  def apply_action(self, action):
    if not action in self.ACTIONS:
      raise DaemonError("invalid action {0}".format(action))
    if self.interactive and not action in self.INTERACTIVE_ACTIONS:
      raise DaemonError("action {0} is not available in interactive mode".format(action))
    action = self.ACTION_MAP.get(action, action)
    return getattr(self, action)()

if __name__ == '__main__':
  import sys
  import optparse
  root_file = "__daemon__"
  lock_file = os.path.abspath(root_file+'.lock')
  eo_file = os.path.abspath(root_file+'.eo')
  option_list = [
			optparse.Option(
						"-n","--name",
						dest="name",
						default=None,
						help="set the daemon name [default: %default]"
                        ),
			optparse.Option(
						"-l","--lock-file",
						dest="lock_file",
						default=lock_file,
						help="set the lock file name [default: %default]"
                        ),
			optparse.Option(
						"-i","--stdin",
						dest="stdin",
						default=None,
						help="set the standard input file name [default: %default]"
                        ),
			optparse.Option(
						"-I","--interactive",
						dest="interactive",
						action="store_true",
						default=False,
						help="interactive mode",
                        ),
			optparse.Option(
						"-o","--stdout",
						dest="stdout",
						default=eo_file,
						help="set the standard output file name [default: %default]"
                        ),
			optparse.Option(
						"-e","--stderr",
						dest="stderr",
						default=eo_file,
						help="set the standard error file name [default: %default]"
                        ),

  ]
  help_formatter=optparse.IndentedHelpFormatter(max_help_position=38)
  parser = optparse.OptionParser(option_list=option_list,formatter=help_formatter)

  (options, args) = parser.parse_args(sys.argv[1:])
  if args:
    action = args[0]
  else:
    action = 'is_running'

  #f = LockFile('a.lock')
  #print "is locked? ", f.is_locked()
  #print "acquiring: ", f.acquire()
  #print "is locked? ", f.is_locked()
  #raw_input('...')
  #print "releasing: ", f.release()
  #raw_input('...')
  #print "is locked? ", f.is_locked()
  #f.close()
  #sys.exit(0)

  class MyDaemon(Daemon):
    def run(self):
      c = 0
      while True:
        print("%8d %s" % (c, c*0.2))
        time.sleep(0.2)
        c += 1
        if c > 100:
          return

  d = MyDaemon(
		lock_file=options.lock_file,
		stdin=options.stdin,
		stdout=options.stdout,
		stderr=options.stderr,
		name=options.name, 
		interactive=options.interactive,
  )
  #print ":::", d.get_lock_info()
  #print args
  
  def dbody():
    c = 0
    while True:
      print("%8d %s" % (c, c*0.2))
      time.sleep(0.2)
      c += 1
      if c > 100:
        return

  print("### ACTION: %s" % action)
  result = d.apply_action(action)
  print("### ACTION: %s -> %s" % (action, result))
  #if action == 'start' or (action == 'restore' and result[1] == 'start'):
  #  dbody()
  #  d.stop()
    

