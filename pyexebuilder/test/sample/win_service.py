from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
__author__ = 'matth'

import os
import win32service
import win32serviceutil
import win32api
import win32con
import win32event
import win32evtlogutil
import sys, string, time
import servicemanager
import logging


class ProcessFamilyTestService(win32serviceutil.ServiceFramework):
    _svc_name_ = "pyexebuilder_test_service"
    _svc_display_name_ = "py-exe-builder Test Service"
    _svc_description_ = "A testing windows service for py-exe-builder"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.running = True

    def SvcStop(self):
        #We need 12 seconds = cos we might have to wait 10 for a frozen child
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING, waitHint=12000)
        servicemanager.LogInfoMsg("ProcessFamilyTest stopping ..." )
        logging.info("Stop request received")
        self.running = False

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("Test service starting up ..." )
        self.running = True
        try:
            logging.getLogger().setLevel(logging.INFO)
            logging.info("Starting test service")
            servicemanager.LogInfoMsg("test service started")
            try:
                logging.info("Starting busy wait")
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("Stopping...")
        except Exception as e:
            logging.error("Error in windows service: %s\n%s", e, _traceback_str())
        finally:
            logging.info("Stopping")
        servicemanager.LogInfoMsg("ProcessFamilyTest stopped" )


def usage():
    try:
        fname = os.path.split(sys.argv[0])[1]
    except:
        fname = sys.argv[0]
    print("Usage: '%s [options] install|update|remove|start [...]|stop|restart [...]|debug [...]'" % fname)
    print("Options for 'install' and 'update' commands only:")
    print(" --username domain\\username : The Username the service is to run under")
    print(" --password password : The password for the username")
    print(" --startup [manual|auto|disabled|delayed] : How the service starts, default = manual")
    print(" --interactive : Allow the service to interact with the desktop.")
    print(" --perfmonini file: .ini file to use for registering performance monitor data")
    print(" --perfmondll file: .dll file to use when querying the service for")
    print("   performance data, default = perfmondata.dll")
    print("Options for 'start' and 'stop' commands only:")
    print(" --wait seconds: Wait for the service to actually start or stop.")
    print("                 If you specify --wait with the 'stop' option, the service")
    print("                 and all dependent services will be stopped, each waiting")
    print("                 the specified period.")
    sys.exit(1)


def HandleCommandLine():
    win32serviceutil.HandleCommandLine(ProcessFamilyTestService, serviceClassString='pyexebuilder.test.sample.win_service')


if __name__ == '__main__':
    HandleCommandLine()
