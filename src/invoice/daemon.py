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
Daemon class - daemonize execution
"""

__author__ = 'Simone Campagna'
__copyright__ = 'Copyright (c) 2013 Simone Campagna'
__license__ = 'Apache License Version 2.0'
__version__ = '1.0'

import collections
import contextlib
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

DaemonRestoreStatus = collections.namedtuple('DaemonRestoreStatus', ('should_run', 'is_running', 'executed_action'))

class Daemon(object): # pragma: no cover
    """Daemonized execution of a task

       Parameters
       ----------
       lock_file: str
           the lock file name
       name: str, optional
           the daemon's name
       stdin: str, optional
           the stdin file name
       stdout: str, optional
           the stdout file name
       stdout_mode: str, optional
           the stdout file mode (defaults to 'ab+')
       stderr: str, optional
           the stderr file name
       stderr_mode: str, optional
           the stderr file mode (defaults to 'ab+')
       daemonize_immediately: bool, optional
           if True, lock is acquired inside the daemonized process
           (defaults to False)
       lock_blocking: bool, optional
           blocking lock acquisition
       lock_timeout: bool, optional
           timeout for non-blocking lock acquisition
       interactive: bool, optional
           interactive mode (no daemonization)
    """
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
    			daemonize_immediately=False,
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
        self.daemonize_immediately = daemonize_immediately
  
    @contextlib.contextmanager
    def locked(self):
        with self.lock_file as lock:
            self._write_lock_data()
            yield self
            self._clear_lock_file()
        
    def daemonize(self):
        """Does the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16

        Raises
        ------
        DaemonError
            fork failed
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
        #atexit.register(self._release_lock)
        #self.lock_file.acquire(blocking=self.lock_blocking, timeout=self.lock_timeout)
        #self._write_lock_data()
  
    def _hostname(self):
        """Returns the host name."""
        return os.uname()[1]
  
    def _pid(self):
        """Returns the process id."""
        return os.getpid()
  
    def _data(self):
        """Returns (hostnane, process_id)."""
        return self._hostname(), self._pid()
  
    def get_lock_info(self):
        """Returns string information about lock.

           Returns
           -------
           str
               lock information: "<hostname>:<pid>"
        """
        hostname, pid = self._data()
        return "{0}:{1}".format(hostname, pid)
  
    def _write_lock_data(self):
        """Writes lock data to lockfile."""
        self._clear_lock_file()
        self.lock_file.write(bytes("{0}\n".format(self.get_lock_info()), 'utf-8'))
        self.lock_file.flush()
  
    def _read_lock_data(self):
        """Reads lock data from lockfile."""
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
        """Checks if this process is run on the same node where lock was created."""
        l_hostname, l_pid = self._read_lock_data()
        hostname, pid = self._data()
        result = True
        if l_hostname is not None and l_hostname != hostname:
            result = False
            if not ignore_errors:
                raise DaemonError("locked on different node (lock: '{0}', current: '{0}')".format(l_hostname, hostname))
        return result, l_hostname, l_pid, hostname, pid
  
    def _clear_lock_file(self):
        """Clears lock file."""
        self.lock_file.seek(0)
        self.lock_file.truncate()
        self.lock_file.flush()
  
    def is_locked(self):
        """Tells if the lock file is locked.

           Returns
           -------
           bool
               the lock status
        """
        return self.lock_file.is_locked()
  
    def lock_wait(self):
        """Waits as far as the lock is locked."""
        while self.lock_file.is_locked():
            time.sleep(1)
        return True
  
    def lock_info(self):
        """Returns lock info.

           Returns
           -------
           LockInfo
               the lock information
        """
        locked = self.lock_file.is_locked()
        l_hostname, l_pid = self._read_lock_data()
        return LockInfo(locked, l_hostname, l_pid)
  
#    def _release_lock(self):
#        """Releases the lock."""
#        self.lock_file.release()
#        self._clear_lock_file()
#        self.lock_file.close()
  
    def start(self):
        """Starts the daemon and calls the run() method."""
        if self.interactive:
            self._check_same_node(ignore_errors=False)
            #acquired = self.lock_file.acquire(blocking=self.lock_blocking, timeout=self.lock_timeout)
            with self.locked():
                self.run()
            return True
        else:
            try:
                self._check_same_node(ignore_errors=False)
                if not self.daemonize_immediately:
                    with self.locked():
                        pass
                child_pid = os.fork() 
                if child_pid > 0:
                    # exit first parent
                    os.waitpid(child_pid, 0)
                    return self.status()
                else:
                    self.daemonize()
                    with self.locked():
                        self.run()
                    sys.exit(0)
            except OSError as e:
                sys.stderr.write("fork #1 failed: {0:d} ({1})\n".format(e.errno, e.strerror))
                raise DaemonError("Fork #1 failed")
  
    def run(self):
        """Runs the daemon tasks."""
        pass
  
    def soft_stop(self):
        """Stops gracefully the daemon."""
        result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
        try:
            os.kill(l_pid, signal.SIGTERM)
        except OSError:
            pass
  
    def hard_stop(self):
        """Stops gracelessly the daemon."""
        result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
        result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
        try:
            os.kill(l_pid, signal.SIGKILL)
        except OSError:
            pass
  
    def stop(self, soft_timeout_seconds=20, soft_interval=0.2, hard_timeout_seconds=5, hard_interval=0.2):
        """Stops the daemon.

           Parameters
           ----------
           soft_timeout_seconds: float,optional
               soft timeout
           soft_interval: float,optional
               soft interval
           hard_timeout_seconds: float,optional
               hard timeout
           hard_interval: float,optional
               hard interval
        """
        i_time = time.time()
        mode_data = {
  	    'soft':	(soft_timeout_seconds, soft_interval, self.soft_stop),
  	    'hard':	(hard_timeout_seconds, hard_interval, self.hard_stop),
        }
        modes = ['soft', 'hard']
        for mode in modes:
            if not self.lock_file.is_locked():
                self._clear_lock_file()
                return self.status()
            timeout_seconds, interval, stop_function = mode_data[mode]
            stop_function()
            while True:
                if not self.lock_file.is_locked():
                    self._clear_lock_file()
                    return self.status()
                if (time.time() - i_time) > timeout_seconds:
                    break
                else:
                    time.sleep(interval)
        return self.status()
  
    def abort(self):
        """Aborts the daemon process."""
        return self.stop(soft_timeout_seconds=0, soft_interval=0.1, hard_timeout_seconds=0.0, hard_interval=0.1)
  
    def restart(self):
        """Restarts the daemon process."""
        result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
        self.stop()
        return self.start()
  
    def is_running(self):
        """Tells if the daemon is running.

        Returns
        -------
        bool
            the running status
        """
        result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
        result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=False)
        return self.lock_file.is_locked()
  
    def status(self):
        """Returns the daemon's status as string.

        Returns
        -------
        str
            the daemon's status
        """
        result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=True)
        locked = self.lock_file.is_locked()
        if result:
            node_info = ""
        else:
            node_info = " (remote)"
        if locked:
            l_hostname, l_pid = self._read_lock_data()
            return "{0} is running by {1}:{2}{3}".format(self.label, l_hostname, l_pid, node_info)
        else:
            return "{0} is not running".format(self.label)
  
  
    def restore(self):
        """Restarts the daemon process if it was interrupted abnormally.

           Returns
           -------
           tuple
               a 2-tuple containing (restarted, action) where restarted is a bool
               (True if daemon should be running) and action is the executed action.
        """
        result, l_hostname, l_pid, hostname, pid = self._check_same_node(ignore_errors=True)
        locked = self.lock_file.is_locked()
        if locked:
            # running
            return DaemonRestoreStatus(True, True, None)
        else:
            l_hostname, l_pid = self._read_lock_data()
            if l_hostname is None and l_pid is None:
                # should not be running
                return DaemonRestoreStatus(False, False, None)
            else:
                # should be running, but it isn't
                if not result:
                    # empty lock file, since it has been created on a different node
                    self._clear_lock_file()
                self.start()
                return DaemonRestoreStatus(True, True, 'start')
    
    def apply_action(self, action):
        """Apolies an action to the running daemon.

           Parameters
           ----------
           action: str
               the action name

           Returns
           -------
           any
               the action result
        """
        if not action in self.ACTIONS:
            raise DaemonError("invalid action {0}".format(action))
        if self.interactive and not action in self.INTERACTIVE_ACTIONS:
            raise DaemonError("action {0} is not available in interactive mode".format(action))
        action = self.ACTION_MAP.get(action, action)
        return getattr(self, action)()

if __name__ == '__main__':
    import sys
    import argparse
    root_file = "__{name}"
    lock_file = os.path.abspath(root_file+'.lock')
    eo_file = os.path.abspath(root_file+'.eo')
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", "-n",
                        default='DAEMON',
                        help="set the daemon name")
    parser.add_argument("--lock-file", "-l",
                        default=lock_file,
                        help="set the lock file name")
    parser.add_argument("--stdin", "-i",
                        default=None,
                        help="set the standard input file name")
    parser.add_argument("--stdout", "-o",
                        default=eo_file,
                        help="set the standard output file name")
    parser.add_argument("--stderr", "-e",
                        default=eo_file,
                        help="set the standard error file name")
    parser.add_argument("--interactive", "-I",
                        default=False,
                        action="store_true",
                        help="interactive mode")
    parser.add_argument("action",
                        nargs="?",
                        default="is_running",
                        help="action to be executed")

    args = parser.parse_args()


    class MyDaemon(Daemon):
        def run(self):
            c = 0
            while True:
                print("%8d %s" % (c, c*0.2))
                time.sleep(0.2)
                c += 1
                if c > 100:
                    return

    for attr_name in 'lock_file', 'stdin', 'stdout', 'stderr':
        attr_value = getattr(args, attr_name)
        if attr_value is not None:
            setattr(args, attr_name, attr_value.format(name=args.name))
        print("{}={!r}".format(attr_name, getattr(args, attr_name)))
   
    daemon = MyDaemon(
        lock_file=args.lock_file,
        stdin=args.stdin,
        stdout=args.stdout,
        stderr=args.stderr,
        name=args.name, 
        interactive=args.interactive)
    
    print("### ACTION: {}".format(args.action))
    result = daemon.apply_action(args.action)
    print("### ACTION: {} -> {}".format(args.action, result))

