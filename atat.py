#!/usr/bin/python
# coding: utf-8

from pysnmp.hlapi import *

##########################
#    SHAREABLE VARIABLES
##########################

#WHID = "location"
#CommunityString = "Secret"
#Printers = ["prt-color-1", "prt-2", "3","mfp-2", "plotter-1"]

##########################
#   SNMP Code Descriptions
##########################

#   .1.3.6.1.2.1.43.11.1.1.5.1.1 = product 
#     [6="inkCartridge", 21="tonerCartridge", 15="fuser", 18="cleanerUnit", 20="transferUnit"
#
#   .1.3.6.1.2.1.43.11.1.1.3.1.1 = color
#     toner: [1="Black", 2="Cyan", 3="Magenta", 4="Yellow"]
#     ink:   [1="Cyan", 2="Magenta", 3="Yellow", 4="Gray", 5="Matte Black", 6="Photo Black"]
#
#   .1.3.6.1.2.1.43.11.1.1.7.1.1 = units 
#     [19="percent", 15="tenthsOfMilliliters"]
#
#   .1.3.6.1.2.1.43.11.1.1.8.1.1 = max [int]

##########################
#   Custom error messages
##########################

def HostNotFound(hostname):
    print "Hostname %s not found. \n\t Printer may not exist or CommunityString is not correct." % hostname
    return

def Offline(hostname):
    print "Unable to connect to printer %s.  Printer may be offline." % hostname
    return


class Printer():
    short_name = ""
    hostname = ""
    is_mono = 0
    style = ""
    colors = []
    supplies = []
    
    def __init__(self, short_name, hostname):
        self.short_name = short_name
        self.hostname = hostname
        self.style = getStyle(hostname)
        if self.style =="none":
            return
        self.is_mono = getMono(hostname, self.style)
        
        if self.style == "laser":
            self.supplies_list = ["fuser", "cleaner", "transfer"]
            if self.is_mono:
                self.colors_list = ["black"]
            else:
                self.colors_list = ["black", "cyan", "magenta", "yellow"]
        elif self.style == "plotter":
            self.colors_list = ["gray", "photo black", "matte black", "yellow", "magenta", "cyan"]

        self.colors = [[cl,""] for cl in self.colors_list]
        # If it is a plotter, it won't have supplies.  Just carry on
        try:
            self.supplies = [[sl,""] for sl in self.supplies_list]
        except:
            return

        return


def getStyle(hostname):
    errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
            CommunityData(CommunityString, mpModel=0),
            UdpTransportTarget((hostname, 161)),
            ContextData(),
            ObjectType(ObjectIdentity('.1.3.6.1.2.1.43.11.1.1.5.1.1')))
        )
    
    try: 
        if (varBinds[0][1] == 21):
            return "laser"
        elif (varBinds[0][1] == 6):
            return "plotter"
        else:
            Offline(hostname)
            return "none"
    except IndexError:
        HostNotFound(hostname)
        return "none"


def getMono(hostname, style):    
    if style == "laser":
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
            CommunityData(CommunityString, mpModel=0),
            UdpTransportTarget((hostname, 161)),
            ContextData(),
            ObjectType(ObjectIdentity('.1.3.6.1.2.1.43.11.1.1.5.1.2')))
            )
        if (varBinds[0][1] == 21):
            return False
        return True


def loadColors(thisPrinter):
    for x in range (1, len(thisPrinter.colors)+1):
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
            CommunityData(CommunityString, mpModel=0),
            UdpTransportTarget((thisPrinter.hostname, 161)),
            ContextData(),
            ObjectType(ObjectIdentity('.1.3.6.1.2.1.43.11.1.1.9.1.%s' % x)))
        )
    
        thisPrinter.colors[x-1][1] = int(varBinds[0][1])
        if thisPrinter.style == "plotter":
            thisPrinter.colors[x-1][1] = int(thisPrinter.colors[x-1][1]/1.3)
    return


def loadSupplies(thisPrinter):
    if thisPrinter.style == "plotter":
        # plotters don't have supplies lists
        return
    
    for x in range (len(thisPrinter.colors)+1, len(thisPrinter.colors)+len(thisPrinter.colors)+1):
        errorIndication, errorStatus, errorIndex, supplyType = next(
            getCmd(SnmpEngine(),
            CommunityData(CommunityString, mpModel=0),
            UdpTransportTarget((thisPrinter.hostname, 161)),
            ContextData(),
            ObjectType(ObjectIdentity('.1.3.6.1.2.1.43.11.1.1.5.1.%s' % x)))
        )
        
        errorIndication, errorStatus, errorIndex, supplyValue = next(
                getCmd(SnmpEngine(),
                CommunityData(CommunityString, mpModel=0),
                UdpTransportTarget((thisPrinter.hostname, 161)),
                ContextData(),
                ObjectType(ObjectIdentity('.1.3.6.1.2.1.43.11.1.1.9.1.%s' % x)))
            )
        supplyType = int(supplyType[0][1])
        supplyValue = int(supplyValue[0][1])
# DEBUG:
#        print "\tIndex: %s \n\tType: %s \n\tValue: %s \n" % (x, supplyType, supplyValue)
        
        # printer.supplies = ["fuser", "cleaner", "transfer"]
        # 15="fuser", 18="cleanerUnit", 20="transferUnit"
        if (supplyType == 1):
            return
        if (supplyType == 20):
            thisPrinter.supplies[2][1] = supplyValue
            continue
        if (supplyType == 18):
            thisPrinter.supplies[1][1] = supplyValue
            continue
        if (supplyType == 15):              
            thisPrinter.supplies[0][1] = supplyValue
            continue
        else:
            print supplyType
        
    return


def printOutput(printer):
    for x in range(0,len(printer.colors)):
        print "\t", printer.colors[x]
        
    print "\t-------------------"
    
    if printer.style == "plotter":
        print "\tPlotters do not have supplies"
    else:
        for x in range(0,len(printer.supplies)):
                if not(isinstance(printer.supplies[x][1], basestring)):
                    print "\t", printer.supplies[x]   
                    


if __name__ == "__main__":
    
    for i in Printers:
        # If the user input the printer name starting with 'prt-' then remove the prefix to standardize
        if i.startswith("prt-"):
            i = i[4:]

        short_name = "%s-prt-%s" % (WHID.lower(), i.lower())
        hostname = "%s.%s.amazon.com" % (short_name, WHID.lower())

        thisPrinter = Printer(short_name, hostname)
        if thisPrinter.style != "none":
            print "%s is a %s %s" % (thisPrinter.short_name, "mono" if thisPrinter.is_mono else "color", thisPrinter.style)
        if thisPrinter.style=="none":
            continue
        else:
            loadColors(thisPrinter)
            loadSupplies(thisPrinter)

        printOutput(thisPrinter)
