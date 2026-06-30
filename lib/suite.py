import lib.ebuio as ebuio
import lib.jobrunner as jobrunner
import lib.results as results
import time

import os

class Suite:
    def start(self):
        self.output.load()
        self.jobRunner.start()

    def onStop(self):
        self.res = results.Results(self.settings, self.output, self.__formatTime(time.time() - self.startTime), self.peakMem, self.settings.threads,self.settings.note,self.jobTable)
        #self.pjtable = results.createpjtable(self.res.failMap,'failedPjtable',self.jobTable)
        #os.remove(scrach)

    def __formatTime(self, seconds):
        intSeconds = int(seconds)
        return '%i:%02.i:%02.i' % (intSeconds//(60*60),(intSeconds//60) % 60,intSeconds % 60)

    def openResults(self):
        if self.res != None:
            self.res.open()
    
    def writeXML(self, labelDict):
        if self.res != None:
            self.res.writeXML(labelDict, self.settings.output)
            self.pjtable = results.createpjtable(self.res.failMap,'failed.pjtable',self.jobTable,self.settings)
            


    def __exportVariables(self, exportList): 
        for export in exportList:
            tokens = export.split('=')
            if(len(tokens) != 2):
                continue

            os.environ[tokens[0]] = tokens[1]

            print('Set environment variable: ' + export)

    def __init__(self, path, startTime):
        self.__loadAllFromSettingsPath(path)
        self.res = None
        self.startTime = startTime
        self.peakMem = 0

    def __loadAllFromSettingsPath(self, path):
       
        unloadedJobs = 0

        self.settings = ebuio.SettingReader(path)

        self.__exportVariables(self.settings.exportlist)
        
        self.jobTable = ebuio.JobTableReader(self.settings.jobtable, self.settings.variables)

        scratch = ebuio.ScratchFolder(self.settings.scrroot, [x[0] for x in  self.jobTable.pathList])
        jobDataMap = {}

        jobList = []
        for name,path in self.jobTable.pathList:
            if not path in jobDataMap:
                jobDataMap[path] = ebuio.JobDataReader(path)

                for file in self.settings.defaultInputs:
                    if file not in jobDataMap[path].inputList:
                        jobDataMap[path].inputList.append(file)

                for file in self.settings.defaultOptInputs:
                    if file not in jobDataMap[path].optInputList:
                        jobDataMap[path].optInputList.append(file)

                for file in self.settings.defaultOutputs:
                    if file not in jobDataMap[path].outputList:
                        jobDataMap[path].outputList.append(file)
                
                for file in self.settings.defaultOptOutputs:
                    if file not in jobDataMap[path].optOutputList:
                        jobDataMap[path].optOutputList.append(file)
                    
            
            if jobDataMap[path].commandLine == None:
                print('Unable to load job ' + name + ' in ' + path)
                unloadedJobs += 1
                continue


            #replaces $job and $prog with name for the three job parameters(command,input,output)
            commandLine = [x.replace('$job', name).replace('$prog', self.settings.prog) for x in jobDataMap[path].commandLine]
            inputList = [x.replace('$job', name) for x in jobDataMap[path].inputList]
            optInputList = [x.replace('$job', name) for x in jobDataMap[path].optInputList]
            outputList = [x.replace('$job', name) for x in jobDataMap[path].outputList]
            optOutputList = [x.replace('$job', name) for x in jobDataMap[path].optOutputList]

            #If vtune is specified in the settings file, modify the command line here
            if "vtune" in self.settings.vTuneCommandLineModify:

                commandLine = self.settings.vTuneCommandLineModify["vtune"]+ " " + "-collect" + " " + "hotspots" + " " + commandLine
                print(commandLine)
            job = jobrunner.Job(name, commandLine, inputList, optInputList, outputList, optOutputList)
            job.setScratchPath(scratch.getScratch(name))
            job.setInputPath(path)
            job.setOptInputPath(path)
            job.setOutputPath(self.settings.output)
            job.setOptOutputPath(self.settings.output)
            job.setTimeout(self.settings.timeout)

            jobList.append(job)
        
        self.settings.numberOfJobs = len(jobList)

        print('\nLoaded ' + str(self.settings.numberOfJobs) + ' jobs...\n')
        if unloadedJobs > 0:
            print('Unable to load ' + str(unloadedJobs) + ' jobs...\n')

        self.output = ebuio.OutputFolder(self.settings.output)

        self.jobRunner = jobrunner.JobRunner(self.settings.threads, jobList, self.output, self.onStop, self.settings.memTrack )
