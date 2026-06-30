import lib.suite as suite
import inspect,os
import sys
import tkinter as tk       
from tkinter import filedialog,messagebox
from multiprocessing import cpu_count
import time
import platform
import getpass
import copy

## @package gui
#  This file contains Class application which handles the gui of testsuite runner
#

## This class handles gui of the test suite runner  

class Application(tk.Frame):              
    def __init__(self, path, batchRun, master=None):
        
        #Set tkinter specific settings
        tk.Frame.__init__(self, master)
        self.grid(sticky=tk.N+tk.S+tk.E+tk.W)                  
        self.master.title('Python Suite Runner')
        self.master.resizable(width=False, height=False)
        self.master.protocol("WM_DELETE_WINDOW",func=self.__onClosing)
        
        #Set suite specific settings
        self.time = time
        self.startTime = time.time()
        self.suite = None
        self.path = path
        self.running = False
        self.top = None
        self.isBatchRun = batchRun
        self.runningStatus = "Stopped"
        self.needExit = False
        self.safeToExit = False

        self.runningList = []
        self.jobData = None
        self.autostarted = False

        if self.path != '':
            self.createStaticWidgets()
            self.suite = suite.Suite(self.path,self.startTime)
            self.onSettingsLoad()
            self.__runCallback()
            self.autostarted = True
            self.suite.onStop()

    
    #Creates all static widgits which do not rely on a settings file
    def createStaticWidgets(self):

        ############################# HELP MENU BAR ##########################

        self.menubar = tk.Menu(self)
        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="Help", command=self.__onHelp)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        self.master.config(menu=self.menubar)

        ###############################################LEFTHAND SIDE##############################################
        
        #File Location Pane
        self.fileLocationPane = tk.LabelFrame(self, text='Settings Path')
        self.fileLocationPane.grid(row=0,column=0,sticky=tk.N+tk.S+tk.E+tk.W)

        self.settingsPathLabel = tk.Label(self.fileLocationPane,text='None Loaded\t\t\t')
        self.settingsPathLabel.grid(row=0,column=0,sticky=tk.W)
        self.settingsPathButton = tk.Button(self.fileLocationPane,text='Change/Load',command=self.__loadSuiteFromDialogCallback)
        self.settingsPathButton.grid(row=0,column=1,sticky=tk.E)
        
        #Settings Pane 
        self.settingsPane = tk.LabelFrame(self,text='Settings')
        self.settingsPane.grid(row=1,column=0,sticky=tk.N+tk.S+tk.E+tk.W)

        self.outputLabel = tk.Label(self.settingsPane,text='Output \t:  N/A')
        self.outputLabel.grid(row=0,column=0,sticky=tk.W)
        self.refoutputLabel = tk.Label(self.settingsPane,text='RefOut\t:  N/A')
        self.refoutputLabel.grid(row=1,column=0,sticky=tk.W)
        self.execLabel = tk.Label(self.settingsPane, text='Exec\t:  N/A')
        self.execLabel.grid(row=2,column=0,sticky=tk.W)
        self.buildLabel = tk.Label(self.settingsPane,text='Build\t:  N/A')
        self.buildLabel.grid(row=3,column=0,sticky=tk.W)
        self.jobsLabel = tk.Label(self.settingsPane,text='Jobs\t:  N/A')
        self.jobsLabel.grid(row=4,column=0,sticky=tk.W)
        self.inputLabel = tk.Label(self.settingsPane, text='Input\t:  N/A')
        self.inputLabel.grid(row=5,column=0,sticky=tk.W)
        self.threadLabel= tk.Label(self.settingsPane,text='Threads\t:  N/A')
        self.threadLabel.grid(row=6,column=0,sticky=tk.W)
        self.timeoutLabel = tk.Label(self.settingsPane,text='Timeout\t:  N/A')
        self.timeoutLabel.grid(row=7,column=0,sticky=tk.W)

        #Summary Pane
        self.summaryPane = tk.LabelFrame(self,text='Summary')
        self.summaryPane.grid(row=2,column=0,sticky=tk.N+tk.S+tk.E+tk.W)

        self.summaryDisplay = tk.Label(self.summaryPane,justify=tk.LEFT)
        self.summaryDisplay.grid(row=0,column=0,sticky=tk.W)

        #Control Commands Pane
        self.controlPane = tk.LabelFrame(self,text='Controls')
        self.controlPane.grid(row = 3, column = 0,sticky=tk.N+tk.S+tk.E+tk.W)

        self.dummyControlPane1 = tk.LabelFrame(self.controlPane)
        self.dummyControlPane1.grid(row=0, column=0, sticky=tk.W)

        self.dummyControlPane2 = tk.LabelFrame(self.controlPane)
        self.dummyControlPane2.grid(row=1, column=0, sticky=tk.W)

        self.dummyControlPane3 = tk.LabelFrame(self.controlPane)
        self.dummyControlPane3.grid(row=2, column=0, sticky=tk.W)

        self.startButton = tk.Button(self.dummyControlPane1,text='Run',command=self.__runCallback)
        self.startButton.grid(row=0,column=0, sticky=tk.W, ipadx=10)
        self.pauseButton = tk.Button(self.dummyControlPane1, text='Pause', command=self.__pauseCallback)
        self.pauseButton.grid(row=0,column=1, sticky=tk.W, ipadx=5)
        self.stopButton = tk.Button(self.dummyControlPane1,text='Stop',command=self.__stopCallback)
        self.stopButton.grid(row=0,column=2, sticky=tk.W, ipadx=10)
        self.cleanButton = tk.Button(self.dummyControlPane1,text='Clean Stop',command=self.__cleanStopCallback)
        self.cleanButton.grid(row=0,column=3, sticky=tk.W)
        self.clearButton = tk.Button(self.dummyControlPane1,text='Clear Prev Run',command=self.__clearPrevRunCallback)
        self.clearButton.grid(row=0,column=4, sticky=tk.W)
        
        self.linkButton = tk.Button(self.dummyControlPane2,text='Open Results',command=self.__openSuiteResultsCallback)
        self.linkButton.grid(row=0,column=0, sticky=tk.W, ipadx=15)
        self.testBenchButton = tk.Button(self.dummyControlPane2,text='Create Test Bench XML File and Failed pjtable',command=self.__testBenchCallback)
        self.testBenchButton.grid(row=0,column=1, sticky=tk.W) 

        self.addOneThread = tk.Button(self.dummyControlPane3,text='Add One Thread',command=self.__addthread)
        self.addOneThread.grid(row=0,column=0, sticky=tk.W, ipadx=11) 
        self.removeOneThread = tk.Button(self.dummyControlPane3,text='Remove One Thread',command=self.__removethread)
        self.removeOneThread.grid(row=0,column=1,sticky=tk.W, ipadx=12)


        ###############################################RIGHTHAND SIDE##############################################

        #Status pane
        self.statusPane = tk.LabelFrame(self)
        self.statusPane.grid(row=0,column=1,rowspan=4,sticky=tk.N+tk.S+tk.E+tk.W)

        self.statusFrame = tk.LabelFrame(self.statusPane, text='Status')
        self.statusFrame.grid(row=0,column=0,sticky=tk.N+tk.S+tk.E+tk.W)
        self.numberOfJobs = tk.Label(self.statusFrame, text='Total Number of Jobs\t:\tN/A')
        self.numberOfJobs.grid(row=0,column=0,sticky=tk.W)
        self.previouslyRun = tk.Label(self.statusFrame, text = 'Previously Run\t\t:\tN/A')
        self.previouslyRun.grid(row=1,column=0,sticky=tk.W)
        self.numberCompleted = tk.Label(self.statusFrame, text = 'Completed Now\t\t:\tN/A')
        self.numberCompleted.grid(row=2,column=0,sticky=tk.W)
        self.numberRunning = tk.Label(self.statusFrame, text = 'Running\t\t\t:\tN/A')
        self.numberRunning.grid(row=3,column=0,sticky=tk.W)
        self.numberPending = tk.Label(self.statusFrame, text = 'Pending\t\t\t:\tN/A')
        self.numberPending.grid(row=4,column=0,sticky=tk.W)
        self.suitestatus = tk.Label(self.statusFrame, text='Suite status\t\t\t:\t'+self.runningStatus)
        self.suitestatus.grid(row=5,column=0,sticky=tk.W)
        self.runTime = tk.Label(self.statusFrame, text = 'Suite Runtime\t\t:\t0:00:00')
        self.runTime.grid(row=6,column=0,sticky=tk.W)
        self.currMem = tk.Label(self.statusFrame, text='Current Memory\t\t:\t0 GB')
        self.currMem.grid(row=7,column=0,sticky=tk.W)
        self.peakMem = tk.Label(self.statusFrame, text='Peak Memory\t\t:\t0 GB')
        self.peakMem.grid(row=8,column=0,sticky=tk.W)

        #Set up Kill boxes
        self.runningFrame = tk.LabelFrame(self.statusPane, text='Running Jobs')
        self.runningFrame.grid(row=1,column=0,sticky=tk.N+tk.S+tk.E+tk.W)
        
        
        self.stopButtonFrame = tk.Frame(self.runningFrame)
        self.stopButtonFrame.grid(row=0,column=0,columnspan=2,sticky=tk.E+tk.W)

        self.killCurrentButton = tk.Button(self.stopButtonFrame,text='Kill Current Jobs and Continue',command=self.__killCurrentCallback)
        self.killCurrentButton.grid(row=0,column=0,columnspan=2)

        #generate list
        string = ''

        for i in range(5):
            string += str(i+1) + '\n'


        self.pendingFrame = tk.LabelFrame(self.statusPane, text='Up Next')
        self.pendingFrame.grid(row=2,column=0,sticky=tk.N+tk.S+tk.E+tk.W)
        self.pendingTextBox = tk.Label(self.pendingFrame,text=string,justify=tk.LEFT)
        self.pendingTextBox.grid(row=0, column=0,sticky=tk.W)
        
        self.completedFrame = tk.LabelFrame(self.statusPane, text='Last Few Completed')
        self.completedFrame.grid(row=3,column=0,sticky=tk.N+tk.S+tk.E+tk.W)        
        self.completedTextBoxes = []
        for i in range(5):
            leftText = tk.Label(self.completedFrame,text=str(i+1),justify=tk.LEFT)
            leftText.grid(row=i, column=0,sticky=tk.W)
            time = tk.Label(self.completedFrame,text='',justify=tk.LEFT)
            time.grid(row=i,column=1,sticky=tk.W)
            memory = tk.Label(self.completedFrame,text='',justify=tk.LEFT)
            memory.grid(row=i, column=2,sticky=tk.W)
            self.completedTextBoxes.append((leftText, time, memory))
    
    #Loads all setting dependent widgits
    def onSettingsLoad(self):
        self.__initTestBenchSettings()

        self.settingsPathLabel.config(text=self.__stripPath(self.path))
        
        self.__getSummary(self.suite.settings.jobtable)

        self.runningStatus = "Running"

        #Settings pane:
        self.outputLabel.config(text=   'Output \t:  ' + self.suite.settings.output)
        self.refoutputLabel.config(text='RefOut\t:  ' + self.suite.settings.refoutput)
        self.execLabel.config(text=     'Exec\t:  ' + self.__stripPath(self.suite.settings.prog))
        self.buildLabel.config(text=    'Build\t:  ' + self.__getBuildPath(self.suite.settings.prog))
        self.jobsLabel.config(text=     'Jobs\t:  ' + self.__stripPath(self.suite.settings.jobtable))
        self.inputLabel.config(text=    'Input\t:  ' +self.suite.settings.iroot)
        self.threadLabel.config(text=   'Threads\t:  ' + str(self.suite.settings.threads))
        self.timeoutLabel.config(text=  'Timeout\t:  ' + self.__formatTime(self.suite.settings.timeout))

        
        self.numberCompleted.config(text='Completed Now\t\t:\t0')
        self.numberRunning.config(text='Running\t\t\t:\t0')


        for line in self.runningList:
            for element in line:
                element.grid_forget()

        self.runningList = []

        for i in range(self.suite.settings.threads):
            buttonFrame = tk.Frame(self.runningFrame)
            buttonFrame.grid(row=i, column=0, sticky=tk.W)
            
            killButton = tk.Button(buttonFrame,text='Kill')
            killButton.grid(row=0,column=0,sticky=tk.W)
            deferButton = tk.Button(buttonFrame,text='Defer')
            deferButton.grid(row=0,column=1,sticky=tk.W)
            skipButton = tk.Button(buttonFrame, text = 'Skip')
            skipButton.grid(row=0, column=2,sticky=tk.W)

            text = tk.Label(self.runningFrame,justify=tk.LEFT)
            text.grid(row=i,column=1,sticky=tk.W)
            time = tk.Label(self.runningFrame,justify=tk.LEFT)
            time.grid(row=i,column=2,sticky=tk.W)
            mem = tk.Label(self.runningFrame,justify=tk.LEFT)
            mem.grid(row=i,column=3,sticky=tk.W)
            self.runningList.append((buttonFrame, killButton, deferButton, skipButton, text, time, mem))
        

        self.stopButtonFrame.grid_configure(row=self.suite.settings.threads)

        self.killCurrentButton = tk.Button(self.stopButtonFrame,text='Kill Current Jobs and Continue',command=self.__killCurrentCallback)
        self.killCurrentButton.grid(row=0,column=0,columnspan=2)

        totalJobs = self.suite.settings.numberOfJobs
        completedPrev = len(self.suite.jobRunner.output.completedJobs)
        self.numberPending.config(text='Pending\t\t\t:\t' + str(totalJobs - completedPrev))

    #Runs every x number of seconds to update gui  
    def __GUILoop(self):

        if self.suite == None:
            self.after(500,self.__GUILoop)
            return

        totalJobs = self.suite.settings.numberOfJobs
        completedPrev = len(self.suite.jobRunner.output.completedJobs)
        numThreads = self.suite.settings.threads
        self.numberOfJobs.config(text='Total Number of Jobs\t:\t' + str(totalJobs))
        self.previouslyRun.config(text = 'Previously Run\t\t:\t' + str(completedPrev))
        self.threadLabel.config(text='Threads\t: ' + str(numThreads))
        self.suitestatus.config(text='Suite status\t\t:\t'+self.runningStatus)
        

        #Polls threads for information to add to the gui
        if self.suite.jobRunner.getPipe().poll():
            while self.suite.jobRunner.getPipe().poll():
                newJobData = self.suite.jobRunner.getPipe().recv()
                if len(newJobData.memMap)!=len(self.suite.output.memMap):
                    self.suite.output.memMap = newJobData.memMap
                    self.suite.peakMem = newJobData.peakMem
                    self.suite.onStop()
        else:
            self.after(500,self.__GUILoop)
            return

        self.safeToExit = newJobData.allKilled

        if self.needExit and self.safeToExit:
            sys.exit("\nTest suite closed by the user \n")


        changed = self.jobData == None or len(newJobData.completedJobs) != len(self.jobData.completedJobs) or len(newJobData.runningJobs) != len(self.jobData.runningJobs) or len(newJobData.pendingJobs) != len(self.jobData.pendingJobs)
        
        self.jobData = newJobData

        self.numberCompleted.config(text='Completed Now\t\t:\t' + str(len(self.jobData.completedJobs)))
        self.numberRunning.config(text='Running\t\t\t:\t' + str(len(self.jobData.runningJobs)))
        self.numberPending.config(text='Pending\t\t\t:\t' + str(len(self.jobData.pendingJobs)))
        self.runTime.config(text='Suite Runtime\t\t:\t' + self.__formatTime(self.time.time() - self.startTime))
        self.peakMem.config(text=f'Peak Memory\t\t:\t{self.jobData.peakMem:6.3f} GB')
        self.suite.peakMem = self.jobData.peakMem
        
        if self.runningStatus == 'Running':
           self.currMem.config(text=f'Current Memory\t\t:\t{self.jobData.currMem:6.3f} GB')
        else:
            self.currMem.config(text='Current Memory\t\t:\t0 GB')

        #Status Pane:
        
        #Running jobs pane

        for i in range(len(self.runningList)):
            if i<len(self.jobData.runningJobs):

                job,startTime,mem = self.jobData.runningJobs[i]

                if len(job.name)<=25:
                    self.runningList[i][4].config(text= job.name)
                else:
                    self.runningList[i][4].config(text= job.name[:25]+"..")
                self.runningList[i][5].config(text=':  ' + self.__formatTime(self.time.time()-startTime))
                if mem >= 0.0 :
                    self.runningList[i][6].config(text=f'( {mem:7.3f} GB)')

            elif i<self.suite.settings.threads:
                self.runningList[i][4].config(text='')
                self.runningList[i][5].config(text='')
                self.runningList[i][6].config(text='')

            else:
                for j in range(i,len(self.runningList)):
                    Buttons = self.runningList[j]
                    for item in Buttons:
                        item.destroy()   
                self.runningList = self.runningList[:i]
                break
        
        if changed:
            for j in range(len(self.runningList)):
                #LOCATION OF MEMORY LEAK

                #Calling config on the tkinter button command allocates memory
                #that can be reclaimed until the button has been deleted. The
                #proper fix involes deleting the button on every update.
                self.runningList[j][1].config(command=lambda j=j: self.__killButtonCallback(j))
                self.runningList[j][2].config(command=lambda j=j: self.__deferButtonCallback(j))
                self.runningList[j][3].config(command=lambda j=j: self.__skipButtonCallback(j))
      

        #Pending jobs pane
        string =''
        i = 0

        for job,time in self.jobData.pendingJobs:
            if i >= 5:
                break
            string += str(i+1) + '  ' + job.name + '\n'
            i+=1
        for index in range(i,5):
            string += str(index+1) + '\n'

        self.pendingTextBox.config(text=string)  

        #Completed jobs pane
        string = ''
        i = 0
        for job,time,maxMem in reversed(self.jobData.completedJobs):
            if i >= 5:
                break
            self.completedTextBoxes[i][0].config(text=str(i+1) + ' ' + job.name)
            self.completedTextBoxes[i][1].config(text=':  ' + self.__formatTime(time))
            #self.completedTextBoxes[i][2].config(text=f'( {maxMem:7.3f} GB)')
            i+=1

        for index in range(i,5):
            self.completedTextBoxes[index][0].config(text=str(index+1))
            self.completedTextBoxes[index][1].config(text='')
            self.completedTextBoxes[index][2].config(text='')


        if not self.jobData.runningJobs and not self.jobData.pendingJobs:
            self.running = False
            self.safeToExit = True
            self.runningStatus = "Stopped"
            self.suite.onStop()
            if self.autostarted:
                self.__createXML()

       # if script run, close the window on completion
        if self.isBatchRun:
            if len(self.jobData.runningJobs) == 0:
                self.after(1000)
                self.quit()
            
        self.after(500,self.__GUILoop)
    
    #Opens a file dialog to load suite
    def __loadSuiteFromDialogCallback(self):
        t = filedialog.askopenfile()
        if not t is None: 
            self.suite = suite.Suite(t.name)
            self.suite.onStop()

            self.path = t.name
            self.onSettingsLoad()
    
    #Load a summary of the job suite being run
    def __getSummary(self, path):             
        dict = {}
        for name,path in self.suite.jobTable.pathList:
            if path in dict:
                dict[path] = dict[path] + 1
            else:
                dict[path] = 1

        string=''
        
        for key in dict:
            string += str(dict[key]) + '\t:   ' + key.replace(self.suite.settings.iroot,'') + '\n'
        
        self.summaryDisplay.config(text=string)

    def __runCallback(self):
        if self.suite != None and not self.running:
            self.running = True
            self.runningStatus = "Running"
            self.pauseButton.config(text='Pause', command=self.__pauseCallback)
            self.startTime = self.time.time()
            self.suite.start()

    def __clearPrevRunCallback(self):
        if self.suite != None and not self.running:
            self.suite.output.reset()
            
            totalJobs = self.suite.settings.numberOfJobs
            completedPrev = len(self.suite.jobRunner.output.completedJobs)
            self.numberPending.config(text='Pending\t\t\t:\t' + str(totalJobs - completedPrev))
            self.numberCompleted.config(text='Completed Now\t\t:\t0')

    def __cleanStopCallback(self):
        if self.suite != None and self.running:
            self.runningStatus = "Clean Stopped"
            self.pauseButton.config(text='Pause', command=self.__pauseCallback)
            self.suite.jobRunner.cleanStop()

    def __stopCallback(self):
        if self.suite != None and self.running:
            self.pauseButton.config(text='Pause', command=self.__pauseCallback)
            self.runningStatus = "Stopped"
            self.suite.jobRunner.killAllChildren()
            self.suite.onStop()
            self.running = False

    def __openSuiteResultsCallback(self):
        if self.suite != None:
            self.suite.openResults()
    
    def __addthread(self):

        if self.suite.settings.threads == cpu_count():
            messagebox.showinfo("Error", "Number of threads already equal to max CPU cores: "+str(cpu_count())+". Unable to add more!")
        
        else:

            i = self.suite.settings.threads
            
            buttonFrame = tk.Frame(self.runningFrame)
            buttonFrame.grid(row=i, column=0, sticky=tk.W)
            
            killButton = tk.Button(buttonFrame,text='Kill')
            killButton.grid(row=0,column=0,sticky=tk.W)
            deferButton = tk.Button(buttonFrame,text='Defer')
            deferButton.grid(row=0,column=1,sticky=tk.W)
            skipButton = tk.Button(buttonFrame, text = 'Skip')
            skipButton.grid(row=0, column=2,sticky=tk.W)

            text = tk.Label(self.runningFrame,justify=tk.LEFT)
            text.grid(row=i,column=1,sticky=tk.W)
            time = tk.Label(self.runningFrame,justify=tk.LEFT)
            time.grid(row=i,column=2,sticky=tk.W)
            mem = tk.Label(self.runningFrame,justify=tk.LEFT)
            mem.grid(row=i,column=3,sticky=tk.W)
            self.runningList.append((buttonFrame, killButton, deferButton, skipButton, text, time, mem))
            
            self.stopButtonFrame.grid_configure(row=self.suite.settings.threads + 1)
            
            self.suite.settings.threads += 1
            self.suite.jobRunner.addThread()

    def __removethread(self):

        if self.suite.settings.threads == 1:
            messagebox.showinfo("Error", "Number of threads cannot be less than 1!") 

        else:   

            self.suite.settings.threads -= 1
            self.suite.jobRunner.removeThread()

    def __killButtonCallback(self, j):
        self.suite.jobRunner.killChild(self.jobData.runningJobs[j][0].name)

    def __deferButtonCallback(self, j):
        self.suite.jobRunner.deferChild(self.jobData.runningJobs[j][0].name)

    def __skipButtonCallback(self, j):
        self.suite.jobRunner.skipChild(self.jobData.runningJobs[j][0].name)

    def __killCurrentCallback(self):
        if self.suite != None and self.running:
            self.suite.jobRunner.killCurrentChildren()
    
    
    def start(self):
        self.createStaticWidgets()
        if self.suite != None:
            self.onSettingsLoad()
        self.after(0,self.__GUILoop)
        self.mainloop()

    def kill(self):
        if self.suite != None:
            self.suite.jobRunner.killAllChildren()
            self.suite.jobRunner.join()

    def __stripPath(self, path):
        maxSlashPos = max(path.rfind('\\'), path.rfind('/'))
        return path[maxSlashPos+1:]

    #needs work
    def __getBuildPath(self, path):
        maxSlashPos = max(path.rfind('\\'), path.rfind('/'))
        shortenedPath = path[:maxSlashPos+1]
        return shortenedPath

    def __formatTime(self, seconds):
        intSeconds = int(seconds)
        return '%i:%02.i:%02.i' % (intSeconds//(60*60),(intSeconds//60) % 60,intSeconds % 60)


    #Test Bench Dialogue
    def __initTestBenchSettings(self):
        #Init values for xml dialogue
        self.labelNames = ['Owner_Name', 'Owner_Email', 'Owner_Login',
                          'Product','Version', 'TestName', 
                          'MachineName','Platform','BuildDate',
                          'TestDate']

        self.labelDict = {}
        for key in self.labelNames:
            self.labelDict[key] = ''
        
        #Try to load as much information as possible from the system
        self.labelDict['Owner_Login'] = getpass.getuser()

        lastSlashIndex = max(self.suite.settings.prog.rfind('\\') ,self.suite.settings.prog.rfind('/'))
        self.labelDict['Product'] = self.suite.settings.prog[lastSlashIndex+1:].replace('.exe', '')
        
        lastSlashIndex = max(self.suite.settings.output.rfind('\\') ,self.suite.settings.output.rfind('/'))
        self.labelDict['TestName'] = self.suite.settings.output[lastSlashIndex+1:]

        self.labelDict['MachineName'] = platform.node()


        arch =  platform.machine()
        if arch.lower() == 'amd64':
            arch = '64-bit'
        elif arch.lower() == 'i386':
            arch = '32-bit'

        self.labelDict['Platform'] = platform.system() + platform.release() + ' ' + arch

        self.labelDict['BuildDate'] = self.time.strftime('%Y-%m-%d')
        self.labelDict['TestDate'] = self.time.strftime('%Y-%m-%d')

        for key in self.labelNames:
            if key in self.suite.settings.xmlSettings:
                self.labelDict[key] = self.suite.settings.xmlSettings[key]

    def __testBenchCallback(self):
        if self.suite != None and self.top is None:
            self.top = tk.Toplevel(self)
            self.top.protocol('WM_DELETE_WINDOW', self.__onToplevelClose)

            xroot = self.winfo_rootx() + self.winfo_width()//2
            yroot = self.winfo_rooty() + self.winfo_height()//2

            self.top.geometry('+' + str(xroot) + '+' + str(yroot))

            #Populate grid
            i = 0
            for key in self.labelNames:
                label = tk.Label(self.top, text=key, justify=tk.LEFT)
                label.grid(row=i,column=0,sticky=tk.W)
                entry = tk.Entry(self.top, justify=tk.LEFT)
                entry.grid(row=i,column=1,sticky=tk.W)
                entry.insert(0, self.labelDict[key])
                self.labelDict[key] = entry
                i += 1

            createButton = tk.Button(self.top, text='Create XML', justify=tk.CENTER,command = self.__onXMLCreate)
            createButton.grid(row=i,column=0, columnspan=2, pady=10)

            
    def __onToplevelClose(self):
        for key in self.labelDict:
            self.labelDict[key] = self.labelDict[key].get()

        self.top.destroy()
        self.top = None

    def __onXMLCreate(self):
        for key in self.labelDict:
             self.labelDict[key] = self.labelDict[key].get()

        self.suite.writeXML(self.labelDict)
        self.top.destroy()
        self.top = None

    def __createXML(self):
        self.suite.writeXML(self.labelDict)

    def __pauseCallback(self):
        self.pauseButton.config(text='Resume', command=self.__continueCallback)
        self.runningStatus = "Paused"
        self.suite.jobRunner.pauseProcess()

    def __continueCallback(self):
        self.pauseButton.config(text='Pause', command=self.__pauseCallback)
        self.runningStatus = "Running"
        self.suite.jobRunner.continueProcess()

    def __onClosing(self):

        self.master.withdraw()
        self.needExit = True

        if self.running:
            self.__stopCallback()

        elif self.safeToExit:
            sys.exit("\nTest suite closed by the user \n")

        
    def __onHelp(self):
        filename=os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0],'TestSuiteHelp.txt')
        os.system("notepad.exe "+filename)