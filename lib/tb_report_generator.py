from xml.dom.minidom import Document

import os, time, sys

def out_file_parser(outpath, xmlBasePath):

    file_name =  os.path.basename(outpath).replace('.out', '')

    outfile_handle = open(outpath)

    outfile_data = outfile_handle.readlines()

    outfile_handle.close()

    begin_report = False

    Outfile_status = {}

    Example_status = {}

    for i in range(len(outfile_data)):

        if 'Begin_Test' in outfile_data[i]:

            begin_report = True

        elif 'End_Test' in outfile_data[i]:

            begin_report = False

            xml_file_name = xmlBasePath + '//' + time.strftime ("%y %m %d") + ' ' + file_name + ' ' + Outfile_status['Platform'] + '.xml'

            create_TB_report(Outfile_status, xml_file_name)
            print("Creating report: " + xml_file_name + "\n")
            Outfile_status = {}

        if begin_report:

            test = outfile_data[i].split('=', 1)

            if 'Example_Name' not in test[0]:

                if str.strip(test[0]) not in Outfile_status.keys():

                    if len(test) > 1:

                        Outfile_status[str.strip(test[0])] = str.strip(test[1])

                if 'Example_status' not in Outfile_status.keys():

                    Outfile_status['Example_status'] = Example_status

                if 'NAME' not in Outfile_status.keys():

                    Outfile_status['NAME'] = os.path.basename(outpath).replace('.out', '')

                if 'Passed' in Outfile_status.keys() and 'Errors' in Outfile_status.keys() and 'Failed' in Outfile_status.keys() and 'NTESTS' not in Outfile_status.keys():

                    total_test_case = int(Outfile_status['Passed']) + int(Outfile_status['Errors']) + int(Outfile_status['Failed'])

                    Outfile_status['NTESTS'] = str(total_test_case)

                if 'TBROOTDIR' not in Outfile_status.keys():
            
                    Outfile_status['TBROOTDIR'] = os.path.dirname(outpath)

                if 'APPLICATION' not in Outfile_status.keys():
            
                    Outfile_status['APPLICATION'] = 'ANSOFT'

                if 'CULTURE' not in Outfile_status.keys():

                    Outfile_status['CULTURE']  = 'en-US'

            else:

                Example_data = test[1].split(';')

                ex_status = {}

                for j in range(1, len(Example_data)):

                    Status = Example_data[j].split('=', 1)

                    if str.strip(Status[0]) not in ex_status.keys():

                        ex_status[str.strip(Status[0])] = str.strip(Status[1])
                        
                Example_status[str.strip(Example_data[0])] = ex_status           

def create_TB_report(sub_nodes, xml_file_name):

    Example_Data = sub_nodes['Example_status']

    doc = Document()

    TESTSET = doc.createElement('TESTSET')
    
    TESTSET.setAttribute('NAME', sub_nodes['NAME'])
    
    TESTSET.setAttribute('TITLE', sub_nodes['NAME'])
    
    TESTSET.setAttribute('TYPE', 'STABILITY')
    
    TESTSET.setAttribute('NTESTS', sub_nodes['NTESTS'])
    
    doc.appendChild(TESTSET)

    list_data_1 = ['TBROOTDIR', 'APPLICATION', 'VERSION', 'MACHINE', 'UNC_REPORTS_PATH', 'CULTURE', 'FAMILY']
 
    for i in range (len(list_data_1)):

        TBROOTDIR = doc.createElement(list_data_1[i])

        TESTSET.appendChild(TBROOTDIR)

        if list_data_1[i] == 'MACHINE':

            TESTSET_text = doc.createTextNode(str(sub_nodes['MachineName']))

        elif list_data_1[i] == 'VERSION':

            TESTSET_text = doc.createTextNode(str(sub_nodes['Version']))

        elif list_data_1[i] == 'UNC_REPORTS_PATH':

            TESTSET_text = doc.createTextNode(str(sub_nodes['TBROOTDIR']))

        elif list_data_1[i] == 'FAMILY':

            TESTSET_text = doc.createTextNode(str(sub_nodes['Product']))

        else:

            TESTSET_text = doc.createTextNode(str(sub_nodes[list_data_1[i]]))

        TBROOTDIR.appendChild(TESTSET_text)

    OWNER = doc.createElement('OWNER')

    OWNER.setAttribute('OSTYPE', 'ALL')

    OWNER.setAttribute('FULLNAME', sub_nodes['Owner_Name'])

    OWNER.setAttribute('EMAIL', sub_nodes['Owner_Email'])

    TESTSET.appendChild(OWNER)

    OWNER.appendChild(doc.createTextNode(sub_nodes['Owner_Login']))

    report = ['ALLWIN', 'LINUX64']

    for x in range(len(report)):

        REPORT = doc.createElement('ADMIN')

        REPORT.setAttribute('REPORT_TYPE', 'OFFICIAL')

        REPORT.setAttribute('PLATFORM', report[x])

        TESTSET.appendChild(REPORT)

    START_TIME = time.strftime("%d/%m/%Y") + ' ' + time.strftime("%H:%M:%S") + ' -04:00'

    START = doc.createElement('START')

    TESTSET.appendChild(START)

    START_text = doc.createTextNode(START_TIME)

    START.appendChild(START_text)

    SYSTEM_INFO = doc.createElement('SYSTEM_INFO')

    TESTSET.appendChild(SYSTEM_INFO)

    NETID = doc.createElement('NETID')
    
    SYSTEM_INFO.appendChild(NETID)

    NETID_text = doc.createTextNode(sub_nodes['MachineName'])

    NETID.appendChild(NETID_text)

    HARDWARE = doc.createElement('HARDWARE')
    
    SYSTEM_INFO.appendChild(HARDWARE)

    HARDWARE_text = doc.createTextNode('')

    HARDWARE.appendChild(HARDWARE_text)

    SOFTWARE = doc.createElement('SOFTWARE')

    SYSTEM_INFO.appendChild(SOFTWARE)

    OS = doc.createElement('OS')

    SOFTWARE.appendChild(OS)

    NAME = doc.createElement('NAME')

    OS.appendChild(NAME)

    NAME_Text = doc.createTextNode(sub_nodes['Platform'])

    NAME.appendChild(NAME_Text)

    OS_list = ['TYPE', 'VERSION', 'BUILD']

    for y in range(len(OS_list)):
    
        OS_list_types = doc.createElement(OS_list[y])

        OS.appendChild(OS_list_types)

        if OS_list[y] == 'TYPE':

            if 'Win' in sub_nodes['Platform']:

                OS_list_types_Text = doc.createTextNode('WinNTx64')

            else:

                OS_list_types_Text = doc.createTextNode('Linux64')
                
            OS_list_types.appendChild(OS_list_types_Text)

        else:

            OS_list_types_Text = doc.createTextNode('')

            OS_list_types.appendChild(OS_list_types_Text)

    WB = doc.createElement('WB')

    SOFTWARE.appendChild(WB)

    WB_BUILD_DATE = doc.createElement('BUILD_DATE')

    WB.appendChild(WB_BUILD_DATE)

    WB_BUILD_DATE_Text = doc.createTextNode(sub_nodes['BuildDate'])

    WB_BUILD_DATE.appendChild(WB_BUILD_DATE_Text)

    TB = doc.createElement('TB')

    SOFTWARE.appendChild(TB)

    BUILD_DATE = doc.createElement('BUILD_DATE')

    TB.appendChild(BUILD_DATE)

    BUILD_DATE_text = doc.createTextNode('8/15/2013 2:23:26 PM')

    BUILD_DATE.appendChild(BUILD_DATE_text)

    VERSION = doc.createElement('VERSION')

    TB.appendChild(VERSION)

    VERSION_text = doc.createTextNode('1.1.4975')

    VERSION.appendChild(VERSION_text)

    TB_PREFS = doc.createElement('TB_PREFS')

    TB.appendChild(TB_PREFS)

    EnableMultiUserMode = doc.createElement('EnableMultiUserMode')

    TB_PREFS.appendChild(EnableMultiUserMode)

    EnableMultiUserMode_Text = doc.createTextNode('False')

    EnableMultiUserMode.appendChild(EnableMultiUserMode_Text)

    TimeOutAdjustment = doc.createElement('TimeOutAdjustment')

    TB_PREFS.appendChild(TimeOutAdjustment)

    TimeOutAdjustment_Text = doc.createTextNode('1')

    TimeOutAdjustment.appendChild(TimeOutAdjustment_Text)

    DEBUG_MODE_WB_NO_RUN = doc.createElement('DEBUG_MODE_WB_NO_RUN')

    TB_PREFS.appendChild(DEBUG_MODE_WB_NO_RUN)

    DEBUG_MODE_WB_NO_RUN_Text = doc.createTextNode('False')

    DEBUG_MODE_WB_NO_RUN.appendChild(DEBUG_MODE_WB_NO_RUN_Text)

    TIMEOUT_DISABLED = doc.createElement('TIMEOUT_DISABLED')

    TB_PREFS.appendChild(TIMEOUT_DISABLED)

    TIMEOUT_DISABLED_text = doc.createTextNode('False')

    TIMEOUT_DISABLED.appendChild(TIMEOUT_DISABLED_text)

    UPDATE_TBINDEX = doc.createElement('UPDATE_TBINDEX')

    TB_PREFS.appendChild(UPDATE_TBINDEX)

    UPDATE_TBINDEX_text = doc.createTextNode('False')

    UPDATE_TBINDEX.appendChild(UPDATE_TBINDEX_text)

    TestSetLib = doc.createElement('TestSetLib')

    TB_PREFS.appendChild(TestSetLib)

    TestSetLib_text = doc.createTextNode('TestBenchLibrary.TestSetLibraryPrefs')

    TestSetLib.appendChild(TestSetLib_text)

    TESTSETLIBS = doc.createElement('TESTSETLIBS')

    TB_PREFS.appendChild(TESTSETLIBS)

    SETLIB = doc.createElement('SETLIB')

    SETLIB.setAttribute('ID', 'Raj_view')

    TESTSETLIBS.appendChild(SETLIB)

    SETLIB.setAttribute('TB_DIR', 'T:\\TestBench\\testsetlib')

    TESTSETLIBS.appendChild(SETLIB)

    SETLIB.setAttribute('PARTS_DIR', 'T:\\TestBench\\Parts')

    TESTSETLIBS.appendChild(SETLIB)

    TB_DIR = doc.createElement('TB_DIR')

    SETLIB.appendChild(TB_DIR)

    TB_DIR_text = doc.createTextNode('T:\\TestBench\\testsetlib')

    TB_DIR.appendChild(TB_DIR_text)

    TBRootDir = doc.createElement('TBRootDir')

    SETLIB.appendChild(TBRootDir)

    TBRootDir_text = doc.createTextNode('\\\pitcc01\\NEW_SAN_VOL\\kdembows\\TestBench_code\\TestBench_R15')

    TBRootDir.appendChild(TBRootDir_text)

    PARTS_DIR = doc.createElement('PARTS_DIR')

    SETLIB.appendChild(PARTS_DIR)

    PARTS_DIR_text = doc.createTextNode('T:\\TestBench\\Parts')

    PARTS_DIR.appendChild(PARTS_DIR_text)
    
    Version = doc.createElement('VERSION')

    SETLIB.appendChild(Version)

    Version_text = doc.createTextNode(sub_nodes['Version'])

    Version.appendChild(Version_text)

    MachineName = doc.createElement('MACHINE')

    SETLIB.appendChild(MachineName)

    MachineName_text = doc.createTextNode(sub_nodes['MachineName'])

    MachineName.appendChild(MachineName_text)

    RunAt = doc.createElement('RunAt')

    SETLIB.appendChild(RunAt)

    RunAt_text = doc.createTextNode('LOCAL')

    RunAt.appendChild(RunAt_text)

    for keys in Example_Data.keys():

        Example_name = str.split(keys, "\\")

        Example_name = Example_name[len(Example_name)-1]

        TESTCASE = doc.createElement('TESTCASE')
    
        TESTSET.appendChild(TESTCASE)

        TESTCASE.setAttribute('TITLE', Example_name.replace(".", " - "))

        TESTSET.appendChild(TESTCASE)

        TIMEOUT = doc.createElement('TIMEOUT')

        TESTCASE.appendChild(TIMEOUT)

        TIMEOUT.appendChild(doc.createTextNode(''))

        TESTPATH = doc.createElement('TESTPATH')

        TESTCASE.appendChild(TESTPATH)

        TESTPATH.appendChild(doc.createTextNode(keys))

        START = doc.createElement('START')

        TESTCASE.appendChild(START)

        START.appendChild(doc.createTextNode(time.strftime("%d/%m/%Y") + ' ' + time.strftime("%H:%M:%S %Z")))

        ARGUMENT = doc.createElement('ARGUMENT')

        TESTCASE.appendChild(ARGUMENT)

        ARGUMENT.setAttribute('ID', 'arg_ProjectFile')

        ARGUMENT.appendChild(doc.createTextNode(keys))

        SCENARIO = doc.createElement('SCENARIO')

        TESTCASE.appendChild(SCENARIO)

        SCENARIO.setAttribute('DESC', 'Execute Simulation of ' + Example_name)

        RUN_JOURNAL = doc.createElement('RUN_JOURNAL')

        SCENARIO.appendChild(RUN_JOURNAL)

        VALIDATION_RESULTS = doc.createElement('VALIDATION_RESULTS')

        RUN_JOURNAL.appendChild(VALIDATION_RESULTS)

        scenario_count = 0

        for keys_list in Example_Data[keys].keys():

            scenario_count += 1

            senario_description = doc.createElement('SCENARIO')

            VALIDATION_RESULTS.appendChild(senario_description)

            senario_description.setAttribute('ID', str(scenario_count))

            senario_description.setAttribute('DESC', keys_list)

            ELAPSED = doc.createElement('ELAPSED')

            senario_description.appendChild(ELAPSED)

            ELAPSED.appendChild(doc.createTextNode(''))

            RESULT = doc.createElement('RESULT')

            senario_description.appendChild(RESULT)

            RESULT.appendChild(doc.createTextNode(Example_Data[keys][keys_list]))

        SCENARIO_RESULT = doc.createElement('RESULT')

        RUN_JOURNAL.appendChild(SCENARIO_RESULT)

        if Example_Data[keys]['Status'] == 'PASSED' and Example_Data[keys]['Comparison'] == 'PASSED':

            status_key = 'PASSED'

        elif Example_Data[keys]['Status'] == 'PASSED' and Example_Data[keys]['Comparison'] != 'PASSED':

            status_key = 'FAILED'

        elif Example_Data[keys]['Status'] != 'PASSED':

            status_key = 'ERROR'

        SCENARIO_RESULT.appendChild(doc.createTextNode(status_key))

        SCENARIO_FINAL_RESULT = doc.createElement('RESULT')

        SCENARIO.appendChild(SCENARIO_FINAL_RESULT)

        SCENARIO_FINAL_RESULT.appendChild(doc.createTextNode(status_key))

        SCENARIO_ELAPSED = doc.createElement('ELAPSED')

        TESTCASE.appendChild(SCENARIO_ELAPSED)

        SCENARIO_ELAPSED.appendChild(doc.createTextNode(''))

        TESTCASE_FINAL_RESULT = doc.createElement('RESULT')

        TESTCASE.appendChild(TESTCASE_FINAL_RESULT)

        TESTCASE_FINAL_RESULT.appendChild(doc.createTextNode(status_key))

        SCENARIO_ELAPSED = doc.createElement('ELAPSED')

        SCENARIO.appendChild(SCENARIO_ELAPSED)

        SCENARIO_ELAPSED.appendChild(doc.createTextNode(''))

    TESTSET_ELAPSED = doc.createElement('ELAPSED')

    TESTSET.appendChild(TESTSET_ELAPSED)

    TESTSET_ELAPSED.appendChild(doc.createTextNode(''))

    TESTSET_PASSED = doc.createElement('PASSED')

    TESTSET.appendChild(TESTSET_PASSED)

    TESTSET_PASSED.appendChild(doc.createTextNode(sub_nodes['Passed']))

    TESTSET_FAILED = doc.createElement('FAILED')

    TESTSET.appendChild(TESTSET_FAILED)

    TESTSET_FAILED.appendChild(doc.createTextNode(sub_nodes['Failed']))

    TESTSET_ERRORS = doc.createElement('ERRORS')

    TESTSET.appendChild(TESTSET_ERRORS)

    TESTSET_ERRORS.appendChild(doc.createTextNode(sub_nodes['Errors']))

    file_handle = open(xml_file_name, 'w')

    TESTSET.writexml(file_handle, indent="", addindent="\t", newl= os.linesep)

    file_handle.close()

