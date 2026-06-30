import os
import sys
import shutil
from multiprocessing import cpu_count

#Handels all input/output
class SettingReader():
    '''Reads in settings from given file'''

    def __init__(self, path):
        print("Reading settings file...\n")

        #Holds a list of variables that will be used as replacements with $variable
        self.variables = []

        #Holds all environment variables to be exported later
        self.exportlist = []

        self.xmlSettings = {}

        self.prog = ""
        self.iroot = ""
        self.output = ""
        self.refoutput = ""
        self.scrroot = ""
        self.threads = -1
        self.timeout = -1
        self.jobtable = ""
        self.memTrack = True
        self.note = ""  #Holds notes in the setting file

        self.defaultInputs = [] #Holds a list of inputs which will be added to each job
        self.defaultOptInputs = [] #Holds a list of optional inputs which will be added to each job if input exists
        self.defaultOutputs = [] #Holds a list of outputs which will be added to each job
        self.defaultOptOutputs = [] #Holds a list of optional outputs which will be added to each job

        self.vTuneCommandLineModify = {}
        try:
            file = open(path, 'r')
        except:
            print("ERROR: Unable to open settings file : " + path + "\n")

        self.__parse(file)
        self.__variablerep()
        
        # copy settings and jobtable into new run folder
        os.makedirs(self.output, exist_ok=True)
        shutil.copy(path, os.path.join(self.output, os.path.basename(path) + ".used"))
        shutil.copy(self.jobtable, os.path.join(self.output, os.path.basename(self.jobtable) + ".used"))

        file.close()
        
        if self.xmlSettings:
            print("XML settings: ", self.xmlSettings)

        if self.prog == "":
            print("ERROR: No prog path set in settings file\n")
        if self.iroot == "":
            print("ERROR: No iroot path set in settings file\n")
        if self.output == "":
            print("ERROR: No output path set in settings file\n")
        if self.refoutput == "":
            print("ERROR: No refoutput path set in settings file\n")
        if self.scrroot == "":
            print("ERROR: No scrroot path set in settings file\n")
        if self.threads < 1:
            print("ERROR: No threads set in settings file\n")
            print("Setting threads to default: 6\n")
            self.threads = 6
        if self.timeout < 0:
            print("ERROR: No timeout set in settings file\n")
            print("Setting timeout to default: 1 minute\n")
            self.timeout = 60
        if self.jobtable == "":
            print("ERROR: No jobtable path set in settings file\n")
        if self.note =="":
            print("WARNING: No '0_testing_notes.txt' file found in the working directory.")

    #Parses file, ignoring comments and empty lines
    def __parse(self, file):
        lineNumber = -1

        for line in file:
            lineNumber += 1
            line = line.strip()

            if len(line) == 0 or line[0] == '#':
                continue

            #Split on whitespace*
            tokens = line.split(None)

            if len(tokens) < 2:
                self.__printError(line, lineNumber)
                continue

            if tokens[0] == 'env': #Environment variables
                string = ''

                for i in range(1, len(tokens)):
                    string += tokens[i] + ' '

                string = string.strip()

                if len(string) > 0:
                    self.exportlist.append(string)
                else:
                    self.__printError(line, lineNumber)

            elif tokens[0] == 'kw':
                string = ''

                for i in range(2, len(tokens)):
                    string += tokens[i] + ' '

                string = string.strip()

                if len(string) > 0:
                    self.__registerVariable(tokens[1], string)
                elif tokens[1]!='optional_input_file' and tokens[1]!='optional_output_file':
                    self.__printError(line, lineNumber)

            elif tokens[0] == 'xml':
                string = ''
                for i in range(2, len(tokens)):
                    string += tokens[i] + ' '

                string = string.strip()

                if len(string) > 0 and string != 'DEFAULT':
                    self.xmlSettings[tokens[1]] = string

            else:
                self.__printError(line, lineNumber)

        # read note file from the working directory
        if os.path.exists(self.scrroot + "/" + "0_testing_notes.txt"):
            with open(self.scrroot + "/" + "0_testing_notes.txt", "r") as f:
                self.note = f.read()

    #Parses variables and adds predefined ones to the class
    def __registerVariable(self, name, value):


        for var, val in self.variables:
            value = value.replace('$' + var, val)
        self.variables.append((name, value))
        if name == 'vtune':
            self.vTuneCommandLineModify[name]=value
        if name == 'prog':
            self.prog = value
        elif name == 'iroot':
            self.iroot = value
        elif name == 'output':
            self.output = value
        elif name == 'refoutput':
            self.refoutput = value
        elif name == 'scrroot':
            self.scrroot = value
        elif name == 'memory_track':
            self.memTrack = value.lower() in ['true', '1', 't', 'y', 'yes']
        elif name == 'threads':
            self.threads = int(value)
            if self.threads > cpu_count():
                print("Number of threads exceeded CPU cores. Setting the value to system CPU count: ",cpu_count(),'\n')
                self.threads = cpu_count()

        elif name == 'timeout':
            self.timeout = self.__parseTimeout(value)
        elif name == 'jobtable':
            self.jobtable = value
        elif name == 'input_file':
            self.defaultInputs = value.split(' ')
        elif name == 'optional_input_file' and value!='':
            self.defaultOptInputs = value.split(' ')
        elif name == 'output_file':
            self.defaultOutputs = value.split(' ')
        elif name == 'optional_output_file' and value!='':
            self.defaultOptOutputs = value.split(' ')

    #Replaces variables with their given constants
    def __variablerep(self):
        for name, value in self.variables:
            for i in range(0, len(self.exportlist)):
                self.exportlist[i] = self.exportlist[i].replace('$'+name, value)

    def __printError(self, line, lineNumber):
        print('ERROR: Unable to parse line ' + str(lineNumber) + ' : ' + line + "\n")

    #Allows timeout to be written as hh:mm:ss
    def __parseTimeout(self, value):
        timeout = value.split(':')
        timeout.reverse()
        output = 0
        output += int(timeout[0])
        if len(timeout) > 1:
            output += int(timeout[1]) * 60
        if len(timeout) > 2:
            output += int(timeout[2]) * 60 * 60

        return output

class JobTableReader():
    'Reads in a job table'

    def __init__(self, path, variableList):
        self.variableList = variableList
        self.pathList = [] #Holds a list of part names and the paths they belong to

        try:
            file = open(path, 'r')
        except:
            print("ERROR: Unable to open Job Table: " + path +  "\n")
            return

        self.__parse(file)
        self.__variablerep(variableList)
        file.close()


    #Parses file, ignoring comments and empty lines
    def __parse(self, file):
        lineNumber = -1

        for line in file:
            lineNumber += 1

            line = line.strip()
            
            if len(line) == 0 or line[0] == '#':
                continue

            tokens = line.split(None, 1)

            if len(tokens) < 2:
                self.__printError(line, lineNumber)
                continue

            if tokens[0] == 'import':

                for name, value in self.variableList:
                    tokens[1] = tokens[1].replace('$'+name, value)

                print('Importing ' + tokens[1] + '\n')
                jobTableReader = JobTableReader(tokens[1], self.variableList)
                for element in jobTableReader.pathList:
                    self.pathList.append(element)
            else:
                self.pathList.append([tokens[1], tokens[0]])

    #Replaces variables with their given constants
    def __variablerep(self, variableList):
        for name, value in variableList:
            for i in range(0, len(self.pathList)):
                self.pathList[i][1] = self.pathList[i][1].replace('$'+name, value)


    def __printError(self, line, lineNumber):
        print('ERROR: Unable to parse line ' + str(lineNumber) + ' : ' + line + "\n")


class JobDataReader():
    'Reads in job data from jobdata.txt'

    def __init__(self, path):
        self.inputList = []
        self.optInputList = []
        self.outputList = []
        self.optOutputList = []
        self.path = path + '/jobdata.txt'

        self.commandLine = None
        try:
            file = open(self.path, 'r')
            self.__parse(file)
            file.close()
        except:
            print('ERROR: Unable to open jobdata file ' + self.path + "\n")

    #Parses file, ignoring comments and empty lines
    def __parse(self, file):
        lineNumber = -1

        for line in file:
            lineNumber += 1

            line = line.strip()

            if len(line) == 0 or line[0] == '#':
                continue

            tokens = line.split(None, 1)

            if len(tokens) < 2:
                if tokens[0]!='optional_input' and tokens[0]!='optional_output':
                    self.__printError(line, lineNumber)
                continue

            if tokens[0] == 'cmdline':
                self.commandLine = tokens[1].split(None)
            elif tokens[0] == 'input':
                self.inputList += tokens[1].split(None)
            elif len(tokens)>1 and tokens[0] == 'optional_input':
                self.optInputList += tokens[1].split(None)
            elif tokens[0] == 'output':
                self.outputList += tokens[1].split(None)
            elif len(tokens)>1 and tokens[0] == 'optional_output':
                self.optOutputList += tokens[1].split(None)
            else:
                self.__printError(line, lineNumber)

    def __printError(self, line, lineNumber):
        print('ERROR: Unable to parse line ' + str(lineNumber) + ' : '
              + line + ' in job table ' + self.path + "\n")
   


class ScratchFolder():
    'Creates and maintains the scratch folder'

    def __init__(self, path, jobNameList):
        self.workingpath = path + '/scratch'
        self.scratchMap = {}

        try:
            if not os.path.exists(self.workingpath):
                os.mkdir(self.workingpath)
        except:
            print('ERROR: Unable to create scratch folder ' + self.workingpath + "\n")

        for job in jobNameList:
            temppath = self.workingpath + '/' + job
            self.scratchMap[job] = temppath

    def getScratch(self, job):
        return self.scratchMap[job]

    #Cleans up scratch when done, might not be usefull
    def clean(self):
        shutil.rmtree(self.workingpath)

class OutputFolder():
    'Creates and maintains an output folder'
    def __init__(self, path):
        self.completedPath = path + '/completedjobs.txt'
        self.path = path
        self.load()

    def reset(self):
        self.completedJobs = []
        if os.path.exists(self.completedPath):
            try:
                file = open(self.completedPath, 'w+')
                file.close()
            except:
                print("ERROR: Unable to overwrite list of completed jobs: "
                      + self.completedPath + "\n")

    def load(self):
        self.completedJobs = []
        self.memMap = {}
        if os.path.exists(self.path):
            if not os.path.exists(self.completedPath):
                try:
                    file = open(self.completedPath, 'w+')
                    file.close()
                except:
                    print("ERROR: Unable to create completed jobs file: "
                          + self.completedPath + "\n")
            else:
                try:
                    file = open(self.completedPath, 'r+')

                except:
                    print("ERROR: Unable to read completed jobs file: "
                          + self.completedPath + "\n")

                for line in file:
                    jobname, jobMem = line.strip().split(' ')
                    self.completedJobs.append(jobname)
                    self.memMap[jobname] = jobMem

                file.close()

        else:
            try:
                # os.mkdir(self.path)
                self.create_directory()
            except:
                print("ERROR: Unable to create output folder:  " + self.path + "\n")

            try:
                file = open(self.completedPath, 'w+')
                file.close()
            except:
                print("ERROR: Unable to create completed jobs file: " + self.completedPath + "\n")

    def create_directory(self):
        path = self.path.split("/")
        if len(path) < 2:
            raise NotADirectoryError
        path_sum = path[0]
        for p in path[1:]:
            path_sum += "/" + p
            if not os.path.isdir(path_sum):
                os.mkdir(path_sum)


class ResultFile():
    'Stores the info from a results file'

    def __init__(self, path, filename):
        self.name = filename.split('.testres')[0] #filename[:filename.index('.')]
        self.subclasses = []
        self.tableData = {}

        try:
            file = open(path + '/' + filename, 'r')
        except:
            print("ERROR: Unable to open testres file: " + filename + "\n")
            return

        for line in file:
            line = line.strip()
            if len(line) == 0:
                continue

            tokens = line.split(None)

            if tokens[0] == 'TestResult':
                self.result = tokens[1]
            elif tokens[0] == 'ResultSubClass':
                code = tokens[1]
                a = tokens[2]
                b = tokens[3]
                message = ''
                for token in tokens[4:]:
                    message += token + ' '

                self.subclasses.append([code, a, b, message])
            elif tokens[0] == 'tabledata':
                tag = tokens[1]
                value = ""
                for token in tokens[2:]:
                    value += token + ' '

                self.tableData[tag] = value

        file.close()

