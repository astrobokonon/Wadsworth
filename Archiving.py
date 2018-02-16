# -*- coding: utf-8 -*-
"""
  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

  Created on Thu Feb 15 11:10:10 2018

  @author: rhamilton
"""

from __future__ import division, print_function, absolute_import

import sys
import time

from servants.butler import wadsworth
from servants.utils import sshConnection
#from servants.maid import yvette


def checkFreeSpace(ssh, basecmd, sdir):
    """
    """
    fcmd = "%s -f %s" % (basecmd,  sdir)
    res = ssh.sendCommand(fcmd)

    return res


def lookForNewDirectories(ssh, basecmd, sdir, dirmask, age=2):
    """
    """
    fcmd = "%s -l %s -r %s --rangeNew %d" % (basecmd,  sdir, dirmask, age)
    res = ssh.sendCommand(fcmd)

    return res


if __name__ == "__main__":
    rpwfile = './remote.password'
    try:
        with open(rpwfile, 'r') as f:
            rpw = f.readline()
        # Remove any whitespace chars (like \n)
        rpw = rpw.strip()
    except IOError:
        rpw = None

    # idict: dictionary of parsed config file
    # runner: parsed options of wadsworth.py
    # pid: PID of wadsworth.py
    # pidf: location of PID file containing PID of wadsworth.py
    idict, args, runner, pid, pidf = wadsworth.beginButtling()

    # Preamble/contextual messages before we really start
    print("Beginning to archive the following instruments:")
    print("%s\n" % (' '.join(idict.keys())))
    print("Starting the infinite archiving loop.")
    print("Kill PID %d to stop it." % (pid))

    # Note: We need to prepend the PATH setting here because some hosts
    #   (all recent OSes, really) have a more stringent SSHd config
    #   that disallows the setting of random environment variables
    #   at login, and I can't figure out the goddamn pty shell settings
    #   for Ubuntu (Vishnu) and OS X (xcam)
    # Also need to make sure to use the relative path (~/) since OS X
    #   puts stuff in /Users/<username> rather than /home/<username>
    baseYcmd = 'export PATH="~/miniconda3/bin:$PATH";'
    baseYcmd += 'python ~/DataMaid/yvette.py'
    baseYcmd += ' '

    # temp hack
    args.rangeNew = 14

    # Infinite archiving loop
    while runner.halt is False:
        for inst in idict:
            iobj = idict[inst]
            print("Instrument: %s" % (inst))

            # Open the SSH connection; SSHHandler creates a Persistence class
            #   (in sshConnection.py) which has some retries and timeout
            #   logic baked into it so we don't have to deal with it here
            eSSH = sshConnection.SSHHandler(host=iobj.host,
                                            port=iobj.port,
                                            username=iobj.user,
                                            timeout=iobj.timeout,
                                            password=rpw)
            eSSH.openConnection()
            time.sleep(1)
            checkFreeSpace(eSSH, baseYcmd, iobj.srcdir)
            time.sleep(3)
            lookForNewDirectories(eSSH, baseYcmd, iobj.srcdir, iobj.dirmask,
                                  age=args.rangeNew)
            time.sleep(3)
            eSSH.closeConnection()

            # Check to see if someone asked us to quit before continuing
            if runner.halt is True:
                break
            time.sleep(10)

        # Temporary hack to only run through once
        break

    # The above loop is exited when someone sends wadsworth.py SIGTERM...
    #   (via 'kill' or 'wadsworth.py -k') so once we get that, we'll clean
    #   up on our way out the door with one final notification to the log
    print("PID %d is now out of here!" % (pid))

    # The PID file will have already been either deleted or overwritten by
    #   another function/process by this point, so just give back the console
    #   and return STDOUT and STDERR to their system defaults
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    print("Archive loop completed; STDOUT and STDERR reset.")
