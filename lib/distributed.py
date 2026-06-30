# Complete hack. If you are a networks guy, please forgive _/\_ for this abomination

import os
from socket import *
from copy import deepcopy

# The following class is used by both the master and the slaves to look up their data
class GlobalSystemToIpAddMap():
    def __init__(self):
        self.systemToIPAddMap = {}
        self.systemToRecvPortMap = {}
        self.systemToSendPortMap = {}
        self.PopulateSystemToIPAddMap()

    def PopulateSystemToIPAddMap(self):
        #host = "10.3.37.37" # w09
        #host = "10.3.68.20" # l13
        #host = "10.3.37.23" # l06
        self.systemToIPAddMap["w09"] = "10.3.37.37"
        self.systemToIPAddMap["l13"] = "10.3.68.20"
        self.systemToIPAddMap["l06"] = "10.3.37.23"

        # These are the ports that each system will listen on. Therefore, these are the ports that messages should be sent to if you want them to get it
        self.systemToRecvPortMap["w09"] = "9000"
        self.systemToRecvPortMap["l13"] = "13000"
        self.systemToRecvPortMap["l06"] = "6000"
        
        # These are the ports that each system will send messages on. Therefore, these are the ports that the server should listen to for acknowledgement
        self.systemToSendPortMap["w09"] = "9001"
        self.systemToSendPortMap["l13"] = "13001"
        self.systemToSendPortMap["l06"] = "6001"

class DistributedSettingsFileParser():
    def __init__(self, pathToDistributedSettingsFile):
        self.distributedSettingsFilePath = pathToDistributedSettingsFile
        self.systems = {}
        self.jobtablePath = ""
        self.envs = {}
        self.systemToLocalPythonPathMap = {}

    def ParseSettingsFile(self, distributedSettingsFile):
        # The master distributed settings file has a list of environment variables, list of systems and number of threads and the master job table path
        print("Here")
        with open(distributedSettingsFile, "r") as f:
            for line in f:
                words = line.split()
                if (len(words)== 0):
                    continue
                if (words[0][0] == "#"):
                    continue
                if (words[0] == "dsn"):
                    # System name
                    self.systems[words[1]] = int(words[2])
                    continue
                if (words[0] == "dkw"):
                    # job table
                    self.jobtablePath = words[2]
                    continue
                if (words[0] == "dpythonpath"):
                    self.systemToLocalPythonPathMap[words[1]] = words[2]
                    continue
                if (words[0] == "env"):
                    newWord = words[1]
                    env = newWord.split("=")
                    self.envs[env[0]] = env[1]
                

class SeparateOutJobTable():
    def __init__(self, jobTablePath, systems):
        nSystems = len(systems)
        listOfLineListsForJobTable = list()
        for i in range(0, nSystems):
            listOfLineListsForJobTable.append(list())
        ll = 0
        with open(jobTablePath, "r") as f:
            for line in f:
                words = line.split()
                if (len(words) == 0):
                    continue
                if (words[0][0] == "#"):
                    continue
                if (words[0][0] != "$"):
                    continue
                # OK, legal line
                index = ll%nSystems #Get the index of the system to assign the job to. Naive. Does not take the number of processesors into account
                listOfLineListsForJobTable[index].append(line)
                ll += 1
        
        
        self.systemToJobsMap = {}
        for listi,key in zip(listOfLineListsForJobTable, systems):
            self.systemToJobsMap[key] = list()
            for j in listi:
                self.systemToJobsMap[key].append(j)
            

class DistributedJobTableCreator():
    def __init__(self, in_systemToJobsMap, in_envs, in_systemToLocalPythonPathMap):
        # Put in the names and ip addresses of the different systems here
        self.systemToIPAddMap = {}
        self.systemToRecvPortMap = {}
        self.systemToSendPortMap = {}
        self.systemToJobsMap = in_systemToJobsMap
        self.envs = in_envs
        self.systemToLocalPythonPathMap = in_systemToLocalPythonPathMap
        self.PopulateSystemToIPAddMap()
        #self.DistributeJobTableAndSetupEnvs()

    def PopulateSystemToIPAddMap(self):
        globalSystemToIpAddMapObj = GlobalSystemToIpAddMap()
        ## For each system, populate the IP, RecvPort and SendPort
        self.systemToIPAddMap     = deepcopy(globalSystemToIpAddMapObj.systemToIPAddMap)
        self.systemToRecvPortMap  = deepcopy(globalSystemToIpAddMapObj.systemToRecvPortMap)
        self.systemToSendPortMap  = deepcopy(globalSystemToIpAddMapObj.systemToSendPortMap)

        #for system in self.systemToJobsMap:
        #   if system not in globalSystemToIpAddMapObj.systemToIPAddMap:
        #       raise Exception("Please provide an IP address for system {}. It can be found by running ifconfig/ipconfig".format(system))
        #   self.systemToIPAddMap[system] = globalSystemToIpAddMapObj.systemToIPAddMap[system]
        #   
        #   if system not in globalSystemToIpAddMapObj.systemToRecvPortMap:
        #       raise Exception("Please provide a receiving port for system {}. It has to be unique and available".format(system))
        #   self.systemToRecvPortMap[system] = globalSystemToIpAddMapObj.systemToRecvPortMap[system]
        #   
        #   if system not in globalSystemToIpAddMapObj.systemToSendPortMap:
        #       raise Exception("Please provide a sending port for system {}. It has to be unique and available".format(system))
        #   self.systemToSendPortMap[system] = globalSystemToIpAddMapObj.systemToSendPortMap[system]
        
        
        ##host = "10.3.37.37" # w09
        ##host = "10.3.68.20" # l13
        ##host = "10.3.37.23" # l06
        #self.systemToIPAddMap["w09"] = "10.3.37.37"
        #self.systemToIPAddMap["l13"] = "10.3.68.20"
        #self.systemToIPAddMap["l06"] = "10.3.37.23"

        ## These are the ports that each system will listen on. Therefore, these are the ports that messages should be sent to if you want them to get it
        #self.systemToRecvPortMap["w09"] = "9000"
        #self.systemToRecvPortMap["l13"] = "13000"
        #self.systemToRecvPortMap["l06"] = "6000"
        
        ## These are the ports that each system will send messages on. Therefore, these are the ports that the server should listen to for acknowledgement
        #self.systemToSendPortMap["w09"] = "9001"
        #self.systemToSendPortMap["l13"] = "13001"
        #self.systemToSendPortMap["l06"] = "6001"

    def DistributeJobTableAndSetupEnvs(self):
        # This class should first, for all systems, send the list of jobs. The client on each system will get them as messages
        # The client has to populate the "jt_slave.pjtable" with the contents of the messages
        # This class should then send the envs to the client as messages
        # The client will then populate the slave_distributed_default.settings file with the contents of the messages
        # This class should then populate the current system's slave_distributed_default.settings and jt_slave.pjtable with the contents of the messages if the current system is also to be used
        
        if (self.AllSystemsAreMappedToIPAddresses()):
            for system in self.systemToJobsMap:
                jobs = self.systemToJobsMap[system]
                for i in jobs:
                    self.send_message(self.systemToRecvPortMap[system], self.systemToIPAddMap[system], i)
                    rec = self.rec_message(self.systemToSendPortMap[system])
                    if (rec == "-1"):
                        # Did not receive acknowledgement. Try resending
                        cc = 1
                        while True:
                            if (cc > 10):
                                raise Exception("Could not get acknowledgement from {} for data {} despite 10 attempts".format(system, i))
                            self.send_message(self.systemToRecvPortMap[system], self.systemToIPAddMap[system], i)
                            rec = self.rec_message(self.systemToSendPortMap[system])
                            if (rec != "-1"):
                                # OK. Resend succeeded
                                print("Resend succeeded!!")
                                break
                            cc +=1
                    if (rec != i):
                        raise Exception("Did not receive acknowledgement of sent message. Code to retry sending is not written yet! FATAL")
                # Send the envs now
                for env,value in self.envs.items():
                    data = "@ " + env + " = " + value
                    self.send_message(self.systemToRecvPortMap[system], self.systemToIPAddMap[system], data)
                    rec = self.rec_message(self.systemToSendPortMap[system])
                    if (rec == "-1"):
                        self.HandleResend(system, data)
                #Send the python path if specified
                if system in self.systemToLocalPythonPathMap:
                    data = "^ " + system + " " + self.systemToLocalPythonPathMap[system]
                    self.send_message(self.systemToRecvPortMap[system], self.systemToIPAddMap[system], data)
                    rec = self.rec_message(self.systemToSendPortMap[system])
                    if (rec == "-1"):
                        self.HandleResend(system, data)

                self.send_message(int(self.systemToRecvPortMap[system]), self.systemToIPAddMap[system], "exit")
            print("All jobs and envs sent and acks received.")      
        else:
            raise Exception("All requested distributed systems are not mapped to their IP addresses. Please fix this in lib/distributed.py's PopulateSystemToIPAddMap function")

    def HandleResend(systemToSendDataTo:str, dataToResend):
        # Did not receive acknowledgement. Try resending
        system = systemToSendDataTo
        cc = 1
        while True:
            if (cc > 10):
                raise Exception("Could not resend data to {} for data {} despite 10 attempts".format(system, dataToResend))
            self.send_message(self.systemToRecvPortMap[system], self.systemToIPAddMap[system], dataToResend)
            rec = self.rec_message(self.systemToSendPortMap[system])
            if (rec != "-1"):
                # OK. Resend succeeded. But is it correct?
                if (rec == dataToResend):
                    print("Resend succeeded!!")
                    break
                else:
                    print("What? Got a reply from {} with {} but the data sent was {}. How? Resending".format(systemToSendDataTo, rec, dataToResend))
            cc +=1
        return

    def rec_message(self, port):
        host = ""
        buf = 1024
        print("Waiting to receive messages on port", port)
        port = int(port)
        addr = (host, port)
        UDPSock = socket(AF_INET, SOCK_DGRAM)
        UDPSock.bind(addr)
        UDPSock.settimeout(5)
        try:
            (data, addr) = UDPSock.recvfrom(buf)
            print("Received message: ", data.decode('ascii'))
            data = data.decode('ascii')
            UDPSock.close()
            return data
        except timeout:
            print("Received a timeout error when receiving acknowledgement for sending")
            return "-1" # Bug if we send just "-1" in a message. Caller will not know what is correct

    def send_message(self, port, receiverIP, data):
        port = int(port)
        addr = (receiverIP, port)
        UDPSock = socket(AF_INET, SOCK_DGRAM)
        tbsd = str(data).encode('ascii')
        UDPSock.sendto(tbsd, addr)
        print("Sent: {} on port {}", data, port)
        UDPSock.close()

    def AllSystemsAreMappedToIPAddresses(self):
        for system in self.systemToJobsMap:
            if system not in self.systemToIPAddMap:
                print("System {}'s IP address is not populated. Please populate it in lib/distributed.py's PopulateSystemToIPAddMap func".format(system))
                raise Exception("All systems do not have an entry in the system to IP address map") #Custom exception at some point. Hack now
            if system not in self.systemToSendPortMap:
                print("System {}'s send port is not populated. Please populate it in lib/distributed.py's PopulateSystemToIPAddMap func".format(system))
                raise Exception("All systems do not have an entry in the system to send port map") #Custom exception at some point. Hack now
            if system not in self.systemToRecvPortMap:
                print("System {}'s receive port is not populated. Please populate it in lib/distributed.py's PopulateSystemToIPAddMap func".format(system))
                raise Exception("All systems do not have an entry in the system to receive port map") #Custom exception at some point. Hack now

        return True
