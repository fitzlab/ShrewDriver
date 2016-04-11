from __future__ import division
import sys
sys.path.append("..")


import _winreg as winreg
import itertools

def get_serial_ports():
    #Uses the Win32 registry to return a iterator of serial 
    #(COM) ports existing on this computer.
    serialPath = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
    serialPorts = []
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, serialPath)
    except WindowsError:
        print "Error reading serial ports. Typically, this means no serial devices are connected."
        return []
    for i in itertools.count():
        try:
            val = winreg.EnumValue(key, i)
            serialPorts.append(val[1])
        except EnvironmentError:
            break
    return sorted(serialPorts)
    

def get_cameras():
    cameraPath = 'HARDWARE\\DEVICEMAP\\VIDEO'
    cameraIDs = []
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, cameraPath)
    except WindowsError:
        raise IterationError
    for i in itertools.count():
        try:
            val = winreg.EnumValue(key, i)
            cameraIDs.append(val)
        except EnvironmentError:
            break
    return cameraIDs
