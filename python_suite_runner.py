#!/usr/bin/python3
import sys
import os
import inspect

#Ensures that the current directory is added to syspath. This allows lib to be inported using the __init__.py file
currentDirectory = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if currentDirectory not in sys.path:
    sys.path.append(currentDirectory)

import lib.gui as gui

#Entry point for the entire program

def main():
    arguments = sys.argv

    path = ''
    batchRun = True
    
    #Program accepts either 0 or 1 or 2 arguments
    if len(arguments) == 3:
        path = arguments[1]
        if arguments[2] == '--batch':
            batchRun = True
    elif len(arguments) == 2:
        path = arguments[1]
    elif len(arguments) != 1:
        print('ERROR: Incorrect number of arguments\n')
        return

    app = gui.Application(path, batchRun)
    
    app.start() #Halts until window is exited

    app.kill()

if __name__ == '__main__':
    main()
