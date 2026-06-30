from multiprocessing import Pool, Process, Queue, Pipe, cpu_count
import os
from os import listdir
from os.path import isfile, join
import sys
import glob
import shutil
import subprocess
import time
import psutil
from re import match


def copyFiles(jobName, srcDir, trgDir, files, showErr):
    for file in files:
        fileNames = file.split(':')
        srcFile = trgFile = fileNames[0]
        if len(fileNames) > 1:
            trgFile = fileNames[1]

        if trgFile.find(jobName) == -1:
            trgFile = jobName + '.' + trgFile

        try:
            srcFiles = glob.glob(os.path.join(srcDir, srcFile))
            numFile = len(srcFiles)
            if 0 == numFile:
                if showErr:
                    print(f'ERROR : Required output file "{srcFile}" not found for job "{jobName}"')
                continue

            if numFile > 1:
                print(f'WARNING : Multiple source file copying only first for "{srcFile}": ')
                for f in srcFiles:
                    print(f'\t{os.path.normpath(f)}')
            srcFileName = os.path.normpath(srcFiles[0])
            trgFileName = os.path.normpath(os.path.join(trgDir, trgFile))
            # print(f'Copying file for job {jobName} :\n\tSource : {srcFileName}\n\tTarget : {trgFileName}')
            shutil.copyfile(srcFileName, trgFileName)
        except Exception as e:
            print(f'EXCEPTION : Unable to copy output file "{srcFile}" in job "{jobName}" : {e}')
        except:
            print(f'EXCEPTION : Unable to copy output file "{srcFile}" in job "{jobName}" : Unknown!')
            pass


# Runs each individual job
def run(job, pipe):
    startTime = time.time()

    if os.path.exists(job.scratchPath):
        try:
            shutil.rmtree(job.scratchPath)
        except:
            print("ERROR : Unable to delete scratch folder in job " + job.name)

    try:
        os.mkdir(job.scratchPath)
    except:
        print("ERROR : Unable to create scratch folder in job " + job.name)

    for file in job.input:
        try:
            # copy ECAD-MCAD files into a single folder (edited by Zhuocheng Lin)
            Job.copyModelFiles(job.inputPath, file, job.scratchPath)
        except:
            print('ERROR : Unable to copy input file ' + file + ' in job ' + job.name)

    try:
        optionalFolderPath = join(job.inputPath, job.input[0].split(".")[0])
        optionalFiles = [f for f in listdir(optionalFolderPath) if isfile(join(optionalFolderPath, f))]

        for file in optionalFiles:
            try:
                shutil.copy(join(optionalFolderPath, file), job.scratchPath)
            except:
                pass
    except:
        pass

    for file in job.optInput:
        try:
            shutil.copy(job.optInputPath + '/' + file, job.scratchPath)
        except:
            pass

    os.chdir(job.scratchPath)

    # Do Work
    with open(os.devnull, "w") as devnull:  # This ensures that stdout and stderr wont be printed to screen
        try:

            # Runs python files with the python interpreter
            # In the future, should look for the associated exe given the file type
            # in a platform independant way
            if job.commandLine[0].endswith('.py'):
                job.commandLine = [sys.executable] + job.commandLine

            process = subprocess.Popen(job.commandLine, stdout=devnull, stderr=devnull)
        except FileNotFoundError:
            print('ERROR: Unable to use executable: ' + job.commandLine[0] + '\n')
            return

    while process.poll() is None:
        time.sleep(.5)

        if pipe.poll():
            message = pipe.recv()
            if message == 'kill':
                process.kill()
                print('Job ' + job.name + ' has been killed')
                return
            elif message == 'defer':
                process.kill()
                print('Job ' + job.name + ' has been defered')
                return
            elif message == 'skip':
                process.kill()
                print('Job ' + job.name + ' has been skipped')
                break

        elapsedTime = time.time() - startTime
        if elapsedTime > job.timeout:
            process.kill()
            print('Job ' + job.name + ' has timed out')
            break

    # Copy files over
    copyFiles(job.name, job.scratchPath, job.outputPath, job.output, True)
    copyFiles(job.name, job.scratchPath, job.outputPath, job.optOutput, False)
    # Copy additional file types if they exist in scratch (filtered by SUITE_COPY_FORMATS env var)
    # Set via launcher GUI checkboxes or 'env SUITE_COPY_FORMATS=ngmesh,truesurface' in .settings file
    copy_formats_env = os.environ.get('SUITE_COPY_FORMATS', '')
    enabled_formats = [f.strip() for f in copy_formats_env.split(',') if f.strip()]
    for ext in enabled_formats:
        for srcFile in glob.glob(os.path.join(job.scratchPath, '*.' + ext)):
            try:
                shutil.copyfile(srcFile, os.path.join(job.outputPath, os.path.basename(srcFile)))
            except Exception as e:
                print(f'EXCEPTION : Unable to copy {ext} file in job "{job.name}" : {e}')
    optionalFiles = [f for f in listdir(job.scratchPath) if isfile(f)]


# Manages all jobs
def processMaster(pipe, processes, jobList, out, onStop, pause, memTrack):
    jobNumber = 0
    processPause = pause
    runningJobs = []
    jobData = JobData()
    needMemUpdate = False

    jobData.pendingJobs += [(job, 0) for job in jobList]

    while jobNumber < len(jobList) or len(runningJobs) > 0:

        jobData.allKilled = False

        # On message command
        if pipe.poll():
            message = pipe.recv()

            if message == 'pause':
                processPause = True

            elif message == 'continue':
                processPause = False

            elif message == 'killall':
                for runningJob in runningJobs:
                    try:
                        runningJob.parentpipe.send('kill')
                    except:
                        pass

                for runningJob in runningJobs:
                    runningJob.process.join()

                jobData.allKilled = True
                pipe.send(jobData)
                return

            elif message == 'killcurrent':
                for runningJob in runningJobs:
                    runningJob.parentpipe.send('kill')
                runningJobs = []

            elif message == 'cleanstop':
                jobNumber = len(jobList)

            elif message == 'addthread':
                processes += 1

            elif message == 'removethread':
                processes -= 1

            else:
                signal, child = message.split(' ')

                for runningJob in runningJobs:
                    if runningJob.job.name == child:
                        runningJob.parentpipe.send(signal)
                        runningJobs.remove(runningJob)
                        if signal == 'defer':
                            jobData.pendingJobs.append((runningJob.job, 0))
                        break

        # Check up on running jobs
        offset = 0
        for i in range(len(runningJobs)):
            if not runningJobs[i - offset].process.is_alive():

                # Add job to completed jobs with correct time
                jobData.completedJobs.append((runningJobs[i - offset].job,
                                              time.time() - runningJobs[i - offset].startTime,
                                              runningJobs[i - offset].maxMem))

                try:
                    completedFile = open(out.completedPath, 'a')
                    completedFile.write(
                        runningJobs[i - offset].job.name + ' ' + str(runningJobs[i - offset].maxMem) + '\n')
                    completedFile.close()
                    out.memMap[runningJobs[i - offset].job.name] = str(runningJobs[i - offset].maxMem)

                except:
                    print("ERROR: Unable to open list of completed jobs: " + out.completedPath + "\n")

                del runningJobs[i - offset]
                offset += 1

                needMemUpdate = True

        # Add jobs if not all available processes are being used and jobrunner is not paused
        while not processPause and len(runningJobs) < processes and (jobNumber < len(jobList) or jobData.pendingJobs):
            # Check if job has been completed

            if jobNumber < len(jobList) and jobList[jobNumber].name in out.completedJobs:
                jobData.pendingJobs.remove((jobList[jobNumber], 0))
                jobNumber += 1
                continue

            if jobNumber < len(jobList):

                parentP, childP = Pipe()

                p = Process(target=run, args=(jobList[jobNumber], childP))
                p.start()

                # Remove added job from pending list
                jobData.pendingJobs.remove((jobList[jobNumber], 0))

                # runningJobs.append((p,jobList[jobNumber],time.time(),parentP))
                runningJobs.append(RunningJobInfo(p, parentP, jobList[jobNumber], time.time(), 0, 0))
                jobNumber += 1

            elif jobData.pendingJobs:

                parentP, childP = Pipe()

                # Remove job from pending list
                job = jobData.pendingJobs.pop(0)[0]

                p = Process(target=run, args=(job, childP))
                p.start()

                # Add it to running list
                # runningJobs.append((p,job,time.time(),parentP))
                runningJobs.append(RunningJobInfo(p, parentP, jobList[jobNumber], time.time(), 0, 0))

        # Update and send running jobs list
        jobData.currMem = 0
        for runningJob in runningJobs:
            try:
                if memTrack:
                    currentProcess = psutil.Process(runningJob.process.pid)
                    runningJob.currMem = currentProcess.memory_info().rss
                    for child in currentProcess.children(recursive=True):
                        runningJob.currMem += child.memory_info().rss
                    runningJob.currMem = round(runningJob.currMem / 10 ** 9, 3)
                    jobData.currMem += runningJob.currMem
                else:
                    runningJob.currMem = -1.0
                    jobData.currMem = -1.0
            except:
                pass

            runningJob.maxMem = max(runningJob.maxMem, runningJob.currMem)

        jobData.peakMem = max(jobData.peakMem, jobData.currMem)

        jobData.runningJobs = []

        for runningJob in runningJobs:
            jobData.runningJobs.append((runningJob.job, runningJob.startTime, runningJob.currMem))

        if needMemUpdate:
            jobData.memMap = out.memMap
            needMemUpdate = False

            # Generate html
            # onStop()

        pipe.send(jobData)
        time.sleep(1)


class RunningJobInfo:
    ''' Holds details of a Running job'''

    def __init__(self, process, parentpipe, job, startTime, currMem, maxMem):
        self.process = process
        self.parentpipe = parentpipe
        self.job = job
        self.startTime = startTime
        self.currMem = currMem
        self.maxMem = maxMem


class Job():
    '''Holds a job'''

    def __init__(self, name, commandLine, input, optInput, output, optOutput):
        self.name = name
        self.commandLine = commandLine
        self.input = input
        self.inputPathFileList = []
        self.optInput = optInput
        self.output = output
        self.optOutput = optOutput

    def setScratchPath(self, scratchPath):
        self.scratchPath = scratchPath

    def setInputPath(self, inputPath):
        self.inputPath = inputPath

    def setOptInputPath(self, optInputPath):
        self.optInputPath = optInputPath

    def setOutputPath(self, outputPath):
        self.outputPath = outputPath

    def setOptOutputPath(self, optOutputPath):
        self.optOutputPath = optOutputPath

    def setTimeout(self, time):
        self.timeout = time

    @classmethod
    def copyModelFiles(cls, inputPath, model, scratchPath):
        """
        Copy needed model files to the /scratch folder. All files of each model should be put in a single folder.
        :param inputPath: source model files path
        :param model: model name
        :param scratchPath: script temp folder
        :return: none
        """
        # reprocess: change model name like "3hp.sm3" to "3hp"
        if len(model.split(".")) > 1:
            model = model.split(".")[0]

        inputFileList = os.listdir(inputPath)
        for f in inputFileList:
            if os.path.isdir(inputPath + "/" + f) and f == model:
                # model files are already inside a folder, copy entire folder
                subPath = inputPath + "/" + f
                subFileList = os.listdir(subPath)
                for subFile in subFileList:
                    if os.path.isdir(subPath + "/" + subFile):
                        shutil.copytree(subPath + "/" + subFile, scratchPath + "/" + subFile)
                    else:
                        shutil.copyfile(subPath + "/" + subFile, scratchPath + "/" + subFile)

            else:
                fSplit = f.split(".")
                # models files are not inside a folder, copy each file into the same folder
                if match(model, fSplit[0]):
                    # model name may be shorter than each model file name,
                    # e.g "01_77174_V7_SPB16.control" and "01_77174_V7_SPB16_S1.g3d"
                    if not os.path.isdir(scratchPath):
                        os.mkdir(scratchPath)
                    else:
                        shutil.copyfile(inputPath + "/" + f, scratchPath + "/" + f)


class JobRunner():
    '''Runs all jobs using multiple processes'''

    def __init__(self, processes, jobList, output, onStop, memTrack):

        self.processes = processes
        self.pause = False
        self.jobList = jobList
        self.parentPipe, self.childPipe = Pipe()
        self.output = output
        self.onStop = onStop
        self.memTrack = memTrack
        self.p = None

    # Runs the jobs using a pool
    def start(self):
        self.p = Process(target=processMaster, args=(
        self.childPipe, self.processes, self.jobList, self.output, self.onStop, self.pause, self.memTrack))
        self.p.start()

    def isAlive(self):
        if self.p != None:
            return self.p.is_alive()
        return False

    def join(self):
        if self.p != None:
            self.p.join()

    def pauseProcess(self):
        self.parentPipe.send('pause')

    def continueProcess(self):
        self.parentPipe.send('continue')

    def killAllChildren(self):
        self.parentPipe.send('killall')

    def killCurrentChildren(self):
        self.parentPipe.send('killcurrent')

    def killChild(self, name):
        self.parentPipe.send('kill ' + name)

    def deferChild(self, name):
        self.parentPipe.send('defer ' + name)

    def skipChild(self, name):
        self.parentPipe.send('skip ' + name)

    def cleanStop(self):
        self.parentPipe.send('cleanstop')

    def getPipe(self):
        return self.parentPipe

    def addThread(self):
        self.processes += 1
        self.parentPipe.send('addthread')

    def removeThread(self):
        self.processes -= 1
        self.parentPipe.send('removethread')


class JobData():
    '''Holds data about all jobs so it can be displayed on screen'''

    def __init__(self):
        self.completedJobs = []
        self.runningJobs = []
        self.pendingJobs = []
        self.allKilled = False
        self.memMap = {}
        self.currMem = 0
        self.peakMem = 0
