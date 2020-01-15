import sys
import datetime
import subprocess
import time
import traceback
import logging
import threading


#logger = logging.getLogger(__name__)


class test_class:
    def __init__(self):
        loggerx = logging.getLogger(__name__)
        loggerx.info('initialized RunWPS instance')


def passfail(func):
    """
    Very ugly decorator that does weird things. Be warned! This function will
    catch any old exception in a try/except block and do the following:
              1) Return a Bool if the function executed successfully
              2) Return a message showing success or an error with traceback
    It will optionally log to a logger object if one is passed as a kwarg. The
    goal of this decorator is to emulate some of the behavior of the unittest
    module witout all of the extras (for example, you can wrap simple assert
    functions with @passfail and get back their status)
    :param      func:  Any input function
    :type       func:  Description
    :returns:   message, if the function raised an exception or not
    :rtype:     string, True/False
    """

    def wrapped_func(*args, **kwargs):
        desc = kwargs.get('desc', '')
        logger = kwargs.get('logger', None)

        try:
            func(*args)
            message = "{}**{}**Passed".format(str(func), desc)
            if logger:
                logger.info(message)
            return (True, message)

        except Exception as e:
            trace_string = traceback.format_exc()
            message = "{} {} Failed with the following Error: {}\n {}".format(
                       str(func),
                       desc,
                       e,
                       trace_string)
            if logger:
                logger.error(message)
            return (False, message)
    return wrapped_func


def timer(function):
    """
    Add a timer decorator to a given function

    :param      function:  The function
    :type       function:  function

    :returns:   wrapped function. logs time to logger obj.
    :rtype:     function
    """
    def wrapped_function(*args, **kwargs):
        t1 = datetime.datetime.now()
        function_output = function(*args, **kwargs)
        t2 = datetime.datetime.now()
        dt = (t2 - t1).total_seconds()/60   # time in minutes
        message_template = 'function {} took {} minutes complete'
        message = message_template.format(function.__name__, dt)
        return function_output, message
    return wrapped_function

@timer
def test_fx():
    sys.wait(10)


def DateGenerator(start_date, end_date, chunk_size):
    """
    Creates a lsit of dates between start_date, end_date, by interval of
    length 'chunk_size'
    :param      start_date:  The start date
    :type       start_date:  pd.datetime object
    :param      end_date:    The end date
    :type       end_date:    pd.datetime.object
    :param      chunk_size:  The chunk size
    :type       chunk_size:  intger
    :returns:   { description_of_the_return_value }
    :rtype:     { return_type_description }
    """
    if end_date <= start_date:
        logger.error("{} LTE {}".format(end_date, start_date))
        sys.exit()

    # WRF run time
    delta = datetime.timedelta(days=chunk_size)     # length of WRF runs
    DateList = [start_date]                         # list of dates

    # Round to nearest h=00":00 to make things nicer
    if start_date.hour != 0:
        round_up_hour = 24 - start_date.hour
        DateList.append(start_date+datetime.timedelta(hours=round_up_hour))

    # Now create list of <start> <end> date pairs
    next_date = DateList[-1]
    while (next_date+delta) < end_date:
        next_date = next_date + delta
        DateList.append(next_date)

    # Append final date
    DateList.append(end_date)

    # Update list and return. Contains (date_i,date_i+1)
    zippedlist = zip(DateList[:-1], DateList[1:])
    return zippedlist


def DateParser(obj, **kwargs):
    """
    Parse a date string into a useable format, using a known list
    of date string types (which can also be passed in as kwarg)
    :param      obj:         The object
    :type       obj:         str
                             pandas._libs.tslibs.timestamps.Timestamp
                             datetime.datetime
    :param      kwargs:      "format=<parsable by strptime()>"
    :type       kwargs:      dictionary
    :returns:   Formatted date object
    :rtype:     pandas._libs.tslibs.timestamps.Timestamp OR
                datetime.datetime
    :raises     Exception:    String format not parsable using listed methods
    :raises     ValueError:   Input type is something other than <str>
    """
    import pandas as pd
    # interpred the date type of an object. return the appropriate format
    acceptable_string_formats = [
                                 "%Y-%m-%d",
                                 "%Y-%m-%d %H",
                                 "%Y %m %d %H",
                                 "%Y-%m-%d_%H",
                                 "%Y-%m-%d-%H",
                                 "%Y-%m-%d:%H",
                                 "%Y-%m-%d:%H:00",
                                 "%Y-%m-%d:%H:00:00"]
    last_chance = len(acceptable_string_formats)-1
    if type(obj) == str:
        for chance, asf in enumerate(acceptable_string_formats):
            try:
                return datetime.datetime.strptime(obj, asf)
            except ValueError:
                if chance == last_chance:
                    raise Exception("Not acceptable string format")

    if type(obj) == pd._libs.tslibs.timestamps.Timestamp:  # ugh that's dumb
        return obj

    if type(obj) == datetime.datetime:
        return obj

    else:
        raise ValueError("type ({}) not accepted".format(type(obj)))


def SystemCmd(cmd):
    '''
    Issue a system (bash or otherwise) command.

    :type       cmd:  string
    :param      cmd:  Command that's executbale by the system (Ex: 'ls -a')

    :returns:   system standard output (out), system standard error (err)
    :rtype:     string
    '''
    proc = subprocess.Popen([cmd],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
    out, err = proc.communicate()
    return out.split(), err


def Submit(subname, scheduler):
    """Submit a batch job script to the scheduler. 

    Parameters
    ----------
    subname : str
        Fullpath to the submission script
    scheduler : str
        Either 'PBS' of 'SLURM'

    Returns
    -------
    jobid : str
        The scheduler system ID
    err : str
        The standar error from the submit process

    Raises
    ------
    ValueError
        If scheduler is not PBS or SLURM
    """

    if scheduler == 'PBS':
        cmd = 'jobid=$(qsub {});echo $jobid'.format(subname)
        proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
        jobid, err = proc.communicate()
        # DOES THIS WORK FOR PBS????
        logger.info("submitting job: {}".format(cmd))
        jobid = jobid.decode("utf-8").rstrip()
        logger.info('jobid: {}'.format(jobid))
        return jobid, err

    if scheduler == 'SLURM':
        cmd = 'sbatch --parsable {}'.format(subname)
        proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)  
        jobid,err = proc.communicate()
        # DOES THIS WORK FOR PBS????
        logger.info("submitting job: {}".format(cmd))
        return jobid.decode("utf-8").rstrip(), err

    if scheduler not in ['PBS','SLURM']:
        logger.error('error')
        raise Exception('unknown scheduler type {}'.format(scheduler))


def WaitForJob(jobid, user, scheduler):
    """
    Queries the queue and finds all of the job ids that match the username.
    Create a list of those job ids (different than job names( nd tries to
    match them with the 'jobid' argument. The code will wait until none of
    the jobs in the queue match the jobid that has been passed in

    :param      jobid:      Fullpath to the submission script
    :type       jobid:      string or pathlib.Path
    :param      user:       Username on system ('whoami')
    :type       user:       string 
    :param      scheduler:  The scheduler ('PBS' OR 'SLURM')
    :type       scheduler:  string 

    :raises     Exception:  ValueError if scheduler is not 'PBS' or 'SLURM'
    """

    if scheduler == 'PBS':
        chid = "qstat | grep {} | sed \"s/^ *//\" | cut -d' ' -f1".format(user)
        # the qstat -u option parses the jobname oddly 

    if scheduler == 'SLURM':
        chid = "squeue -u {} | sed \"s/^ *//\" | cut -d' ' -f1".format(user)

    # Issue the parse command and check if the jobid exists
    still_running = 1     # start with 1 for still running
    while still_running == 1:
        # run command and parse output
        chidout, chiderr = SystemCmd(chid)
        chidout = [i.decode("utf-8") for i in chidout]

        # Decode the error, and mange error output --- the qstat
        # command can sometimes time out!!!
        error = chiderr.decode("utf-8")
        logger.info(error, chidout)
        if error != '':  # the error string is non-empty
            logger.error("error encountered in qstat:\n    {}".format(error))
            logger.error("wait additional 20s before retry")
            time.sleep(60)

            # !!!!!!!!!!!!!!!!! TODO !!!!!!!!!!!!!!!!!!!!
            # HOW DO WE HANDLE THIS ERROR ?????
            # Current solution is just to wait longer....
            # unclear what the best option might be
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # Filter the 'chidout' list for elements matching the jobid.
        # If zero, a match was not found!
        still_running_list = list(filter(lambda x: x == jobid, chidout))
        still_running = len(still_running_list)
        message_template = 'JobID {} is still running...Sleep({})'
        message = message_template.format(still_running_list, 10)
        logger.info(message)
        time.sleep(10)

    # TODO
    # !!!! THIS SHOULD BE CAUGHT WAY BEFORE THIS POINT!!!!
    if scheduler not in ['PBS', 'SLURM']:
        logger.error()
        raise Exception('unknown scheduler type {}'.format(scheduler))


def GenericWrite(readpath, replacedata, writepath):
    """
    Replace words in a textfile with items from the corresponding
    key in 'replacedata' dictionary. Writes to writepath


    :param      readpath:     The readpath
    :type       readpath:     string or pathlib.Path
    :param      replacedata:  {"keyword_in_readpath":"replacement_word"}
    :type       replacedata:  Dictionary
    :param      writepath:    The writepath
    :type       writepath:    string or pathlib.Path
    """
    with open(readpath, 'r') as file:
        filedata = file.read()

        # loop thru dictionary and replace items
    for item in replacedata:
        filedata = filedata.replace(item, str(replacedata[item]))

    # Write the file out again
    with open(writepath, 'w') as file:
        file.write(filedata)
    # done


def fetchFile(filepath):
    """
    Fetches a file using wget.

    :param      filepath:  The filepath
    :type       filepath:  string or pathlib.Path
    """
    # wget a file
    SystemCmd('wget --output-file=logfile {}'.format(filepath))  # CHANGE ME...


def multiFileDownload(filepathlist, namelist=None):
    """
    :param      filepathlist:  list of strings to download
    :type       filepathlist:  list containing strings
    :param      namelist: list of filenames for renaming
    :type       namelist: list of strings 
    """
    # wget a file and rename it, if the name is provided
    if namelist:
        for path, name in zip(filepathlist, namelist):
            cmd = 'wget --output-file=logfile --output-document={} {}'.format(name, path)
            SystemCmd(cmd)
    # do not rename the filedownload
    else:
        for path in zip(filepathlist):
            cmd = 'wget --output-file=logfile {}'.format(path)
            SystemCmd(cmd)


def WriteSubmit(queue_params,
                replacedic,
                filename):
    """
    Write out a batch job submit script based on the queue parameter's
    configuration file. Open the output file and write out the options
    line by line. There is a required  'CMD' in replacedic.keys list.

    :param      queue_params:  The queue parameters
    :type       queue_params:  Dictionary
    :param      replacedic:    Contains...
    :type       replacedic:    Dictionary
    :param      filename:      Full path/destination to write to
    :type       filename:      str or pathlib.Path
    """
    with open(filename, 'w') as f:
        f.write('#!/bin/bash \n')  # write the header
        for qp in queue_params:
            if qp.endswith('\n'):
                line = qp
            else:
                line = "{}\n".format(qp)
            # Replace things
            for key in replacedic.keys():
                if key in line:
                    line = line.replace(key, replacedic.get(key))
            f.write(line)
        # write three blank lines
        f.write('\n')
        f.write('\n')
        f.write('\n')
        f.write('# job execute command goes below here\n')
        f.write(replacedic['CMD'])
        f.write('\n')


def RepN(string, n):
    """
    Repeat a string n times.

    :param      string:  Any old string. Or a list of strings
    :type       string:  String or list
    :param      n:       Number of repetitions
    :type       n:       integer

    :returns:   [string, string ....(n)]
    :rtype:     list
    """

    if type(string) == list:
        return string * n
    elif type(string) == str:
        newlist = [string]
        return newlist*n


def RemoveQuotes(filepathR, filepathW):
    # remove all of the single quotation marks from a file
    # UGH!! THis is terrible. f90nml
    with open(filepathR, 'r') as read_data:
        with open(filepathW, 'w') as write_data:
            d = read_data.read()
            write_data.write(d.replace("'", ""))

def test_logger():
    print('printing')
    logger.info('here i am')


def tail(linenumber, filename):
    """
    Issue a system tail commnad

    :param      linenumber:  The linenumber
    :type       linenumber:  { type_description }
    :param      filename:    The filename
    :type       filename:    { type_description }

    :returns:   { description_of_the_return_value }
    :rtype:     { return_type_description }
    """
    command = 'tail -n {} {}'.format(linenumber, filename)
    returnString, error = SystemCmd(command)
    returnString = ' '.join([x.decode("utf-8") for x in returnString])
    return returnString

# Decorated Functions
@passfail
def file_check(required_files,
               directory,
               value='E'):
    """
    { function_description }
    :param      required_files:  The list of necessary/unnecessary files
    :type       required_files:  list[strings or pathlib.Paths]
    :param      directory:       The directory to check
    :type       directory:       str of pathlib.Path
    :param      value:           'E' (Exist) or 'DnE' (DoesNotExist)
                                 Defaults to 'E'. The DnE  options is
                                 for when we want to confirm files DO
                                 NOT exists in the directory.
    :type       value:           string
    :param      kwargs:          The keywords arguments
    :type       kwargs:          dictionary
    :raises     AssertionError:  { exception_description }
    """

    missing_files = []
    for required in required_files:
        if not directory.joinpath(required).is_file():
            missing_files.append(required)
    num_req = len(required_files)
    num_mis = len(missing_files)

    # ugh this is dumb TODO: make less dumb
    if value == 'E':
        # assert that ALL of the required files have been found in directory
        message = 'missing {} of {} required files'.format(num_req, num_mis)
        assert num_mis == 0, message
    if value == 'DnE':
        # assert that NONE of the files have been found in the directory
        message = 'found {} of {} files'.format(num_req, num_mis)
        assert num_mis == num_req, message


@passfail
def log_check(logfile, message):
    """
    Check that the last line of a particular file contains a given message.
    The log files created by the wrf/wps *.exe files pring a message at the
    end. First verify that the logfile exists (maybe it wasn't created for
    some reason).

    :param      logfile:         The logfile
    :type       logfile:         { type_description }
    :param      message:         The message
    :type       message:         { type_description }

    :raises     AssertionError:  { exception_description }
    """

    # Confirm that it contains a success message
    assert logfile.exists(), "{} not found".format(logfile)

    # Check the last line of the log file.
    string = tail(1, logfile)
    assert message in string, string


@timer
def multi_thread(function, mappable):
    """
    Use with caution-- not working. Generic function applies given function to
    a list, where a list item is the ONLY input arg to that function.

    :param      function:  The function
    :type       function:  { type_description }
    :param      mappable:  The mappable
    :type       mappable:  { type_description }

    :returns:   { description_of_the_return_value }
    :rtype:     { return_type_description }
    """

    thread_chunk_size = 5

    def divide_chunks(l, n):
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i + n]

    # Create a list of lists
    chunked_list = list(divide_chunks(mappable, thread_chunk_size))
    # loop thru the chunked list. max of <thread_chunk_size> threads get opened
    for chunk in chunked_list:
        threads = [threading.Thread(target=function, args=(item,))
                   for item in mappable]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()  #
