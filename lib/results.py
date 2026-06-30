import lib.ebuio as ebuio
import os
import webbrowser
import datetime
import lib.tb_report_generator as XMLGenerator
from multiprocessing import Process
import socket


class Results():
    """Stores the results from a suite run and is responsible for displaying them"""
    def __init__(self, settings, output, suiteRunTime, peakMem, threads,notes,pathlist):

        self.settings = settings
        self.output = output
        self.peakMem = peakMem
        self.path = self.settings.output
        self.resultsPath = self.path + '/000results.html'
        self.outPath = self.path + '/results.out'
        self.__load(self.path)
        self.threadNumber = self.settings.threads
        self.note = self.settings.note
        
        self.suiteRunTime = suiteRunTime
        self.numberPassed = 0
        self.numberNo = 0
        self.numberFailed = 0

        self.passMap = {}
        self.noMap = {}
        self.failMap = {}
        self.tableDataList = []
        

        self.pathlist = pathlist

        #Get catagories for table data
        for result in self.resultsList:
             for key in result.tableData:
                if key not in self.tableDataList:
                    self.tableDataList.append(key)
        
        #Create table row entry for each row
        for result in self.resultsList:
               
            if len(result.subclasses) == 0:
                result.subclasses.append(('','0','0','No Subclass'))
            
            #Select right map

            workingMap = None
            if result.result == 'pass':
                self.numberPassed += 1
                workingMap = self.passMap

            elif result.result == 'fail':
                self.numberFailed += 1
                workingMap = self.failMap

            else:#nores
                self.numberNo+= 1
                workingMap = self.noMap

            #Read though subclasses and add them to map
            for subclass in result.subclasses:
                    if subclass[3] not in workingMap:
                        workingMap[subclass[3]] = []
                    
                    #Construct table data
                    tableEntry = [result.name]
                    for key in self.tableDataList:
                        if key in result.tableData:
                            tableEntry.append(result.tableData[key])
                        else:
                            tableEntry.append('N/A')
                    tableEntry.append(subclass[1])
                    tableEntry.append(subclass[2])
                    tableEntry.append(self.__ratio(subclass[1], subclass[2]))

                    workingMap[subclass[3]].append(tableEntry)

        
        #Create notes files if they don't exist
        outputNotes = self.settings.output + '/PSR_notes.txt'
        refoutputNotes = self.settings.refoutput + '/PSR_notes.txt'

        if os.path.isdir(self.settings.output) and  not os.path.isfile(outputNotes):
            try:
                file = open(outputNotes, 'a+')
                file.close()
            except:
                print("ERROR: Unable to open output notes: " + outputNotes + "\n")

        if os.path.isdir(self.settings.refoutput) and  not os.path.isfile(refoutputNotes):
            try:
                file = open(refoutputNotes, 'a+')
                file.close()
            except:
                print("ERROR: Unable to open reference output notes: " + refoutputNotes + "\n")
        
        try: 
            htmlFile = open(self.resultsPath, 'w+')
        except:
            print("ERROR: Unable to create 000results.html\n")
            return

        htmlWriter = HTML(htmlFile)
        self.__writeHTML(htmlWriter, settings, output)
        htmlFile.close()


    def format_second_to_hhmmss(self, seconds):
        hours = seconds //(60*60)
        seconds %= (60*60)
        minutes = seconds //60
        seconds &= 60 
        return '%02i:%02i:%02i' %(hours,minutes,seconds)
    

    def __writeHTML(self, htmlWriter, settings, output):
        htmlWriter.writeLine('<html>')

        htmlWriter.newLine()

        #Define Variables
        htmlWriter.JSBegin()
        htmlWriter.writeLine('//Change all variables here')
        htmlWriter.newLine()

        outputPath = settings.output.replace('\\', '/')
        refoutputPath = settings.refoutput.replace('\\', '/')

        htmlWriter.JSVariable('outputPath', '"%s"' % outputPath)
        htmlWriter.JSVariable('refoutputPath', '"%s"' % refoutputPath)
        

        htmlWriter.JSVariable('currentSuiteNotes', 'outputPath + "/PSR_notes.txt"')
        htmlWriter.JSVariable('refSuiteNotes', 'refoutputPath + "/PSR_notes.txt"')

        htmlWriter.JSEnd()

        htmlWriter.newLine()

        htmlWriter.writeScatterPlotScript()

        htmlWriter.newLine()

        htmlWriter.writeLine('<body>')



        htmlWriter.write('<h1>')
        htmlWriter.write('Python Suite Runner Results')
        htmlWriter.writeLine('</h1><hr>')

        ##############################################SUMMARY##############################################
        htmlWriter.write('<h2>')
        htmlWriter.write('Summary')
        htmlWriter.writeLine('</h2>')

        # Info: date, note, threads, runtime, timeout, machine, peak memory, output, reference output, executable, jobs
        tableRowTitles = ["Date", "Note", "Threads", "Total Runtime", "Timeout", "Machine", "Peak Memory", "Output",
                          "Reference Output", "Executable", "Number of Jobs"]
        tableRowValues = [datetime.datetime.now().strftime('%m-%d-%Y %I:%M'), self.note, self.threadNumber, self.suiteRunTime,
                         self.format_second_to_hhmmss(settings.timeout), socket.gethostname(),
                         f'{self.peakMem:6.3f} GB', settings.output, settings.refoutput, settings.prog,
                         len(self.resultsList)]
        tableHTML = '<table style="border: 0px"><tbody>'
        for idx, t in enumerate(tableRowTitles):
            if t == "Timeout":
                tableHTML += f'<tr style="height: 18px; vertical-align: top"> \
                                <td style="height: 18px;"><b>{t}:</b></td> \
                                <td style="height: 18px;">{tableRowValues[idx] if settings.timeout > 0 else "null"}</td> \
                                </tr>'
            else:
                tableHTML += f'<tr style="height: 18px; vertical-align: top"> \
                                <td style="height: 18px;"><b>{t}:</b></td> \
                                <td style="height: 18px;">{tableRowValues[idx]}</td> \
                                </tr>'
        tableHTML += '</tbody></table>'

        htmlWriter.write(tableHTML)

        ###########################################TABLE OF CONTENTS#######################################
        htmlWriter.write('<h2>')
        htmlWriter.write('Table of Contents')
        htmlWriter.writeLine('</h2>')
        
        htmlWriter.write('<a href="#ressummary">')
        htmlWriter.write('1 Summary of Results\n')
        htmlWriter.writeLine('</a>')

        '''htmlWriter.write('<a href="#notes">')
        htmlWriter.write('2 Notes\n')
        htmlWriter.writeLine('</a>')
        htmlWriter.write('<a href="#curnotes" style="margin-left:30px;">')
        htmlWriter.write('2.1 Current Run\n')
        htmlWriter.writeLine('</a>')
        htmlWriter.write('<a href="#refnotes" style="margin-left:30px;">')
        htmlWriter.write('2.2 Reference Run\n')
        htmlWriter.writeLine('</a>')'''

        htmlWriter.write('<a href="#results">')
        htmlWriter.write('2 Results\n')
        htmlWriter.writeLine('</a>')
        htmlWriter.write('<a href="#failedresults" style="margin-left:30px;">')
        htmlWriter.write('2.1 Failed Jobs\n')
        htmlWriter.writeLine('</a>')
        htmlWriter.write('<a href="#noresults" style="margin-left:30px;">')
        htmlWriter.write('2.2 Jobs with No Result\n')
        htmlWriter.writeLine('</a>')
        htmlWriter.write('<a href="#passresults" style="margin-left:30px;">')
        htmlWriter.write('2.3 Passed Jobs\n')
        htmlWriter.writeLine('</a>')

        ############################################SUMMARYOFRESULTS#######################################
        htmlWriter.write(r'<h2 id="ressummary">')
        htmlWriter.write('Summary Of Results')
        htmlWriter.writeLine('</h2>')

        htmlWriter.write('<hr>')

        htmlWriter.write(r'<h3>')
        if len(self.resultsList) != 0:
            htmlWriter.write('%i : Failed Jobs (%.2f%%)\n' % (self.numberFailed ,(100*self.numberFailed/len(self.resultsList))))
        htmlWriter.writeLine('</h3>')
        for category in self.failMap:
            table = self.failMap[category]
            htmlWriter.writeLine('<b style="margin-left:30px">' + str(len(table)) + ' : ')
            htmlWriter.writeLine(category + '\n</b>')
        
        htmlWriter.write('<h3>')
        if len(self.resultsList) != 0:
            htmlWriter.write('%i : Jobs with No Result (%.2f%%)' % (self.numberNo, (100*self.numberNo/len(self.resultsList))))
        htmlWriter.writeLine('</h3>')

        for category in self.noMap:
            table = self.noMap[category]
            htmlWriter.writeLine('<b style="margin-left:30px">' + str(len(table)) + ' : ')
            htmlWriter.writeLine(category + '\n</b>')

        htmlWriter.write('<h3>')
        if len(self.resultsList) != 0:
            htmlWriter.write('%i : Passed Jobs (%.2f%%)' % (self.numberPassed, (100*self.numberPassed/len(self.resultsList))))
        htmlWriter.writeLine('</h3>')

        # write comparison statistics: mesh_size, mesh_time, larger_mesh, smaller_mesh, etc
        if "Well done, New succeeded but old mesher failed " in self.passMap:
            category = "Well done, New succeeded but old mesher failed "
            table = self.passMap[category]
            htmlWriter.writeLine(
                    f'<b style="margin-left:30px">{len(table)} : {category} \n</b>')

        for category in self.passMap:
            if category != "Well done, New succeeded but old mesher failed ":
                table = self.passMap[category]
                percentage = None
            
                if category in ['LARGER_MESH ', 'SMALLER_MESH ']:
                    meshSizeJobNumber = len(self.passMap['MESH_SIZE '])
                    percentage = (len(table) / meshSizeJobNumber) * 100
                elif category in ['FASTER_MESH ', 'SLOWER_MESH ']:
                    meshTimeJobNumber = len(self.passMap['MESHING_TIME '])
                    percentage = (len(table) / meshTimeJobNumber) * 100
                elif category == 'CleanMesh ':
                    percentage = (len(table) / self.numberPassed) * 100
            
                if percentage:
                    htmlWriter.writeLine(
                        f'<b style="margin-left:30px">{len(table)} : {category} ({percentage:.2f}%) \n</b>')
                else:
                    htmlWriter.writeLine(
                        f'<b style="margin-left:30px">{len(table)} : {category} \n</b>')
        
        htmlWriter.write('<hr>')
            
        #################################################NOTES#############################################
        '''htmlWriter.write(r'<h2 id="notes">')
        htmlWriter.write('Notes')
        htmlWriter.writeLine('</h2>')

        htmlWriter.write(r'<h3 id="curnotes">')
        htmlWriter.write('Current Run')
        htmlWriter.writeLine('</h3>')

        htmlWriter.JSwriteScrollBox('currentSuiteNotes')

        htmlWriter.write(r'<h3 id="refnotes">')
        htmlWriter.write('Reference Run')
        htmlWriter.writeLine('</h3>')
        
        htmlWriter.JSwriteScrollBox("refSuiteNotes")'''

        ################################################RESULTS############################################
        htmlWriter.write('<h2 id="results">')
        htmlWriter.write('Results')
        htmlWriter.writeLine('</h2>')

        htmlWriter.write('<h3 id="failedresults">')
        htmlWriter.write('Failed Jobs: %i' % self.numberFailed)
        htmlWriter. writeLine('</h3>')

        for category in self.failMap:
            htmlWriter.writeLine('<b>' + category + '</b>')
            table = self.failMap[category]
            htmlWriter.writeTable(table, self.tableDataList,category)
            htmlWriter.writeLine('\n\n')
            #htmlWriter.callScatterPlotScript(category, 800, 400, 1,2)
            createpjtable(self.failMap,'failed.pjtable',self.pathlist,self.settings)
            

        htmlWriter.write('<h3 id="noresults">')
        htmlWriter.write('Jobs with No Result: %i' % self.numberNo)
        htmlWriter.writeLine('</h3>')

        for category in self.noMap:
            htmlWriter.writeLine('<b>' + category + '</b>')
            table = self.noMap[category]
            htmlWriter.writeTable(table, self.tableDataList,category)
            htmlWriter.writeLine('\n\n')
            #htmlWriter.callScatterPlotScript(category, 800, 400, 1,2)

        htmlWriter.write('<h3 id="passresults">')
        htmlWriter.write('Passed Jobs: %i ' % self.numberPassed )
        htmlWriter.writeLine('</h3>')

        if "Well done, New succeeded but old mesher failed " in self.passMap:
            category = "Well done, New succeeded but old mesher failed "
            htmlWriter.writeLine('<b>' + category + '</b>')
            table = self.passMap[category]
            htmlWriter.writeTable(table, self.tableDataList,category)
            htmlWriter.writeLine('\n\n')
            #htmlWriter.callScatterPlotScript(category, 800, 400, 1,2)

        for category in self.passMap:
            if category != "Well done, New succeeded but old mesher failed ":
                htmlWriter.writeLine('<b>' + category + '</b>')
                table = self.passMap[category]
                htmlWriter.writeTable(table, self.tableDataList,category)
                htmlWriter.writeLine('\n\n')
                #htmlWriter.callScatterPlotScript(category, 800, 400, 1,2)


        htmlWriter.writeLine('</body>')
        htmlWriter.writeTableSortScript()
        htmlWriter.writeLine('</html>')



    def writeXML(self, labelDict, xmlBasePath):
        print("Writing XML file...")

        outfile = open(self.outPath, 'w+')

        #Write out
        outfile.write('Begin_Test\n')

        for key in labelDict:
            outfile.write(key + ' = ' + labelDict[key] + '\n')
        
        conversion = {'pass':'PASSED', 'fail':'FAILED', 'no_result':'ERRORS'}

        for result in self.resultsList:
            outfile.write('Example_Name = ' + result.name + '; ')
            outfile.write('Status = ' + conversion[result.result] + '; ')
            outfile.write('Comparison = PASSED; Message_Log = No Errors\n')

        outfile.write('Passed = ' + str(self.numberPassed) + '\n')
        outfile.write('Failed = ' + str(self.numberFailed) + '\n')
        outfile.write('Errors = ' + str(self.numberNo) + '\n')

        outfile.write('End_Test\n')
        outfile.close()

        #Create XML, run on thread so GUI does not lock

        process = Process(target=XMLGenerator.out_file_parser, args=(self.outPath, xmlBasePath,))
        process.start()

    def __load(self, path):
        self.resultsList = []

        try:
            resultPaths = [f for f in os.listdir(path) if '.testres' in f]
        except PermissionError:
            print("ERROR: Incorrect permissions for " + path + "\n")
            return

        for filename in resultPaths:
            resultFile=ebuio.ResultFile(path, filename)

            jobname = filename.split('.testres')[0]
            
            if jobname in self.output.memMap.keys():
                resultFile.tableData['MaxMem'] = str(self.output.memMap[jobname])
            else:
               resultFile.tableData['MaxMem'] = '-'
            
            self.resultsList.append(resultFile)

    #Calculates ratios that will be used in the ratio column of the results file
    def __ratio(self, a, b):
        inta = int(a)
        intb = int(b)

        if intb == 0:
            return '-1.0'
        else:
            return '%.3f' % (inta/intb)

    def open(self):
        webbrowser.open('file://' + self.resultsPath, new=0)


class HTML():
    'Writes html to file'
    def __init__(self, file):
        self.f= file

    def write(self, string):
        #Replace new lines with line breaks
        self.f.write(str(string).replace('\n', '<br>'))

    def writeLine(self, string):
        #Replace new lines with line breaks
        self.f.write(str(string).replace('\n', '<br>') + '\n')

    def writeRaw(self, string):
        self.f.write(str(string))

    def writeTable(self, list, tableDataList, name):
        self.JSBegin()
        string = '['


        #Heading
        string += '["<b>Job Name</b>",'

        for key in tableDataList:
            string += '"<b>' + str(key) + '</b>",'
        flag = False

                
        
        for sublist in list:
            # if last three item in list is -1 not wrte last three item on the list
            if int(float(sublist[len(sublist)-2])) == -1 and int(float(sublist[len(sublist)-3])) == -1:
                flag = True
                sublist.pop(len(sublist)-1)
                sublist.pop(len(sublist)-1)
                sublist.pop(len(sublist)-1)
                
        if flag == False:
            string += '"<b>RunData</b>", "<b>RefData</b>", "<b>Ratio</b>", "<b>Job Link</b>", "<b>Ref Link</b>"],\n'
        else:
            string += ' "<b>Job Link</b>", "<b>Ref Link</b>"],\n'
        for sublist in list:
            string += '['

            for element in sublist:
                string += '"' + element +'",'
            
            #Output debug
            # string +=  '\'<a href="file://\' + outputPath + \'/' + sublist[0] + '.debug.runlog">[Log]</a> \'' 
            # string += " + "

            # #Output profile
            # string +=  '\'<a href="file://\' + outputPath + \'/' + sublist[0] + '.profile">[Profile]</a>\'' 
            # string += ", "

            #Output debug
            string +=  '\'<a href="'+ sublist[0] + '.debug.runlog">[Log]</a> \'' 
            string += " + "

            # #Output profile
            string +=  '\'<a href="' + sublist[0] + '.profile">[Profile]</a>\'' 
            string += ", "
            
            # #refOutput debug
            # string +=  '\'<a href="file://\' + refoutputPath + \'/' + sublist[0] + '.debug.runlog">[Log]</a> \'' 
            # string += " + "

            # #refOutput profile
            # string +=  '\'<a href="file://\' + refoutputPath + \'/' + sublist[0] + '.profile">[Profile]</a>\'' 
            
            # string += '],\n'

            #refOutput debug
            string +=  '\'<a href="file://\' + refoutputPath + \'/' + sublist[0] + '.debug.runlog">[Log]</a> \'' 
            string += " + "

            #refOutput profile
            string +=  '\'<a href="file://\' + refoutputPath + \'/' + sublist[0] + '.profile">[Profile]</a>\'' 
            
            string += '],\n'

        string += ']'

        #Adds the string above as a variable, which will be a 2D Array
        self.JSVariable('table', string)

        #Writes Javascript which takes the 2D array above and creates a table
        jsTableCode = '''
        document.write(\'<table id="'''+name+'''" class="sortable" border="1" style="width:80%;border-collapse:collapse">\');
        for(var i = 0; i < table.length; i++) {
            document.write("<tr>");

            for(var j = 0; j < table[i].length; j++) {
                document.write("<td>" + table[i][j] + "</td>");
            }

            document.write("</tr>");
        }

        document.write("</table>");
        '''
        self.writeRaw(jsTableCode)


        self.JSEnd()
       

    #For formatting html, will not carry through markup
    def newLine(self):
        self.f.write('\n')


    #JavaScript
    def JSBegin(self):
        self.writeLine(r'<script language="javascript" type="text/javascript">')
    
    def JSEnd(self):
        self.writeLine('</script>')

    def JSWrite(self, string):
        self.writeLine(r'document.write(%s);' % string)

    def JSVariable(self, variableName, value):
        self.writeRaw('var %s = %s;\n' % (variableName, value))


    def JSwriteScrollBox(self, variableName):
        self.newLine()
        self.JSBegin()

        #Email me at wnichols2012@my.fit.edu
        self.JSWrite('\'<iframe src="\' + ' + variableName + ' + \'" style="height:300px;width:100%">\'')
        self.JSWrite('"</iframe>"')
        self.JSEnd()
        self.newLine()

    #Writes javascript to HTML results file that will sort a table by column
    def writeTableSortScript(self):
        self.writeRaw("""<script>
    //Sortable Script

    var sortableList = document.getElementsByClassName("sortable");

    for(var i = 0; i < sortableList.length; i++) {
	makeTableSortable(sortableList[i]);
    }

    function makeTableSortable(table) {
    	firstRowCells = table.rows[0].cells;
	    
	    for(var i = 0; i < firstRowCells.length; i++) {
		    firstRowCells[i].style.cursor = "pointer";
		    (function (i, table) {
		    	firstRowCells[i].onclick = function() {
			    	onclick(i, table);
			    }
		    })(i, table);
	    }
    }

    function onclick(column, table) {
	    var rows = table.rows;
	    var firstRow = table.rows[0];	
	    var firstCellsList = firstRow.cells;
	
	    //Get Class Name
	    var currrentClassName = firstCellsList[column].className
	    var sortMultiplier = 0;
	
	    clearClassNames(firstCellsList);

	    if(currrentClassName === "sorted") {
	    	firstCellsList[column].className = "reversesorted";
	    	firstCellsList[column].innerHTML += "  &#8593;"
	    	sortMultiplier = -1;
	    } else { //Not sorted or reverse sorted
	    	firstCellsList[column].className = "sorted";
	    	firstCellsList[column].innerHTML += "  &#8595;"
	    	sortMultiplier = 1;
	    }

	    var elements = [];
	    for(var i = 1; i < rows.length; i++) {
	    	elements.push([i, rows[i].cells[column].innerHTML]);
	    }	
	    elements.sort(function(aElement, bElement) {
			var a = aElement[1];
			var b = bElement[1];
			var out;
			if(isNaN(+a) && isNaN(+b)) {
				out = a.localeCompare(b);
			} else if (isNaN(+a)) {
				out = 1;
			} else if(isNaN(+b)) {
				out = -1;
			} else {
				out = a-b;
			}
	    	return out * sortMultiplier;
	    });

	    for(var i = 0; i < elements.length; i++) {
	    	var row = table.insertRow(table.rows.length);
	    	row.innerHTML = table.rows[elements[i][0]].innerHTML;
	    }

	    for(var i = 0; i < elements.length; i++) {
	    	table.deleteRow(1);
	    }
    };

    function clearClassNames(cellList) {
    	for(var i = 0; i < cellList.length; i++) {
    		if(cellList[i].className !== "") {
	    		cellList[i].innerHTML = cellList[i].innerHTML.slice(0, -1);
	    	}
	    	cellList[i].className = "";	
	    }
    }
 </script>
    """)

    #def callScatterPlotScript(self, name, width, height, xCol, yCol):
    #    self.writeRaw("<script>" +'createScatterGraph("'+name+ '",' + str(width) + "," + str(height) + "," + str(xCol) + "," + str(yCol) + ");</script>")
    
        #Writes javascript to HTML results file that will generate scatterplots
    def writeScatterPlotScript(self):
        self.writeRaw("""<script>
//ScatterPlot Script
function createScatterGraph(tableName,width,height, xCol, yCol) {
	//Get table
	var table = document.getElementById(tableName); 
	var rows = table.rows;
	
	//Divide
	var div = document.createElement("DIV");
	div.style.height = +(height);
	div.style.width = +(width);
	div.style.position ="relative";
	
	//Canvas
	var canvas = document.createElement("CANVAS");
	div.appendChild(canvas);
	
	//Callback for button change
	function changeCallback(e) {
		var value = +e.currentTarget.value
		if(value < 1) {
			e.currentTarget.value = "1"
		}
		if(value > rows[0].cells.length - 1) {
			e.currentTarget.value = +(rows[0].cells.length - 1);
		}
		render();
	};
	
	
	//Control
	var xControl = document.createElement("SELECT");
	
	for(var i = 1; i < rows[0].cells.length; i++) {
		var option = document.createElement("OPTION");
		option.text = rows[0].cells[i].innerHTML.replace("<b>", "").replace("</b>", "");
		xControl.add(option);
	}
	xControl.selectedIndex=xCol-1	
	xControl.onchange = changeCallback;
	xControl.style.position = "absolute"	
	div.appendChild(xControl);
	
	var yControl = document.createElement("SELECT");
	
	for(var i = 1; i < rows[0].cells.length; i++) {
		var option = document.createElement("OPTION");
		option.text = rows[0].cells[i].innerHTML.replace("<b>", "").replace("</b>", "");
		yControl.add(option);
	}
	yControl.selectedIndex=yCol-1;
	yControl.onchange = changeCallback;
	yControl.style.position = "absolute"
	div.appendChild(yControl);
	
	//Log scale checkbox
	function logCallback() {
		render();
	};
	
	var logScale = document.createElement("INPUT");
	logScale.onchange = logCallback;
	logScale.type = "checkbox"
	logScale.style.position = "absolute";
	div.appendChild(logScale);
	
	document.body.appendChild(div);
	
	render();
	
	function render() {
	//Render
	canvas.width = +width;
	canvas.height = +height;
	var context = canvas.getContext("2d");
	context.fillStyle = "#000000";
	
	//Draw axis labels
	
	yControl.style.bottom = +(canvas.height/2) + "px";
	yControl.style.left = "0px";
	
	xControl.style.bottom = "0px";
	xControl.style.left = +(canvas.width/2) + "px";
	
	
	//Log button
	logScale.style.bottom = "0px";
	var logText = "Log Scale";
	var logLength = context.measureText(logText).width;
	logScale.style.left = +(canvas.width-(logScale.offsetWidth + logLength + 5)) + "px";
	context.fillText(logText, canvas.width - logLength, canvas.height-6);
	
	var xStart = yControl.offsetWidth + 35;
	var yStart = xControl.offsetHeight + 25;
	
	
	//Calculate	
	var xList = [];
	var yList = [];
	var xMax = 0;
	var yMax = 0;
	var xMin = 1;
	
	if(logScale.checked) {
		for(var i = 1; i < rows.length; i++) {
			var x = +rows[i].cells[xControl.selectedIndex+1].innerHTML
			if(x !== 0) {
				xMin = Math.min(x,xMin);
			}
		}
	}
	
	for(var i = 1; i < rows.length; i++) {
		var x = +rows[i].cells[xControl.selectedIndex+1].innerHTML
		var y = +rows[i].cells[yControl.selectedIndex+1].innerHTML
		
		if(logScale.checked && x !== 0) {
			x = ((Math.log(x) / Math.log(10))) - (Math.log(xMin)/Math.log(10));
		}
		
		xMax = Math.max(x,xMax);
		yMax = Math.max(y,yMax);

		
		if(!(logScale.checked && x == 0)){
			xList.push(x);
			yList.push(y);
		}
	}
	
	var xRatio = (canvas.width - xStart - 50) / xMax;
	var yRatio = (canvas.height - yStart - 50) / yMax;
	
	
	//Draw lines
	context.beginPath();
	context.lineWidth="1";
	context.strokeStyle="black";
	context.moveTo(xStart,0);
	context.lineTo(xStart,canvas.height-yStart);
	context.lineTo(canvas.width, canvas.height-yStart);
	context.stroke();	
	
	//Draw scale
	context.fillStyle = "#000000";
	context.strokeStyle= "#EEEEEE";
	
	var yLabels = 20;
	var ySpacing = (height-yStart) / (yLabels-1);
	for(var i = 1; i < yLabels; i++) {
		var pos = height - (ySpacing * i) - yStart;
		var string = (pos / yRatio).toFixed(1);
		var strWidth = context.measureText(string).width;
		
		context.fillText(string, xStart-strWidth-3, height - pos - yStart+2.5);
		
		context.moveTo(xStart, height - pos - yStart);
		context.lineTo(width, height - pos - yStart);
		context.stroke();
	}
	
	
	var xLabels = 15;
	var xSpacing = (width-xStart) / (xLabels);
	for(var i = 0; i < xLabels; i++) {
		var pos = (xSpacing * i);
		
		var value = pos / xRatio;
		var string;
		
		if(logScale.checked) {
			value = Math.pow(10,value + (Math.log(xMin) / Math.log(10)));
		} 
		if(value >= .1 || value <= 0) {
			string = value.toFixed(1);
		} else {
			string = value.toExponential(1);
		}
		
		
		var strWidth = context.measureText(string).width;
		context.fillText(string, pos+xStart - (strWidth/2), height - yStart + 15);
		
		context.moveTo(pos+xStart, height - yStart);
		context.lineTo(pos+xStart, 0);
		context.stroke();
	}
	
	
	
	//Draw points
	context.fillStyle = "#FF0000";
	for(var i = 1; i < rows.length; i++) {
		var x = xList[i-1];
		var y = yList[i-1];
			
		context.fillRect(xStart + (x * xRatio) - 2.5,canvas.height - yStart - (y * yRatio) - 2.5,5,5);
	}
	}
}
</script>
    """);


 


class createpjtable():
    'writes a new pjtable of failed jobs'
    def __init__(self, failMap, filename,jobtableReader,settings):
        self.f = settings.output+'/'+filename   #filename of the pjtable
        self.failMap = failMap                  #dictionary of failed projects
        self.pathlist = jobtableReader.pathList #read origional projectfile
        self.iroot = settings.iroot             #for recover into origional pjtable
        jobname = []
        jobdir = []
        failedjobname = []
        

        #print('writing pjtable at '+str(self.f))

        f=open(self.f,'w+')


        for catogary in self.failMap:          #list failed projects name
            table = self.failMap[catogary]
            for job in table:
                failedjobname.append(job)

        f.write('#number of models: ' + str(len(failedjobname))+'\n')
        for element in self.pathlist:          # index directory and name 
            jobname.append(element[0])
            jobdir.append(element[1].replace(self.iroot,'$iroot'))  #append revelent dir 
        
      
        for failedmodel in failedjobname: #itrate all of the failed cases
            #print('writing pjtable for model: ' +failedmodel[0])
            i = jobname.index(failedmodel[0])
            f.write('{:<50}{:<70}'.format(jobdir[i],failedmodel[0]) )
            f.write('\n')
            

        f.close()
    
    