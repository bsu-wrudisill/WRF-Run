import os
from accessories import passfail
from SetMeUp import SetMeUp
import logging

'''
Checks that the necessary files, folders, and environments are setup before
starting the procedureThe purpose is to be QUICK -not completely thorough.
The goal is to check for common or likely mistakes
'''


class RunPreCheck(SetMeUp):
    # checks that the config.yaml file is sensible (paths exist, etc)

    def __init__(self, setup, update=None):
        # This is an incredibly handy function all of the self.X attrs.
        # from SetMeUP
        # instance get put into the "self" of this object
        # same as super(RunPreCheck, self).__init__(setup)
        super(self.__class__, self).__init__(setup)  
        self.logger = logging.getLogger(__name__)
        if update:
            self._SetMeUp__update(**update)
#self.setup.__updatepaths(location)

    @passfail
    def test_existenz(self):
        message = 'warning, {} already exists'.format(self.main_run_dirc)
        assert not os.path.exists(self.main_run_dirc), message

    @passfail
    def test_dates(self):
        # Purpose: test that the date ranges passed into the model config
        # (in the .yaml file) are reasonable
        message = "Specified model start date is before the model end date"
        assert (self.end_date > self.start_date), message

    @passfail
    def test_restart(self):
        if (self.restart == 'None') or (self.restart is None):
            assert 1 == 1  # guarentee a sucess...
        if self.restart == True:
            for rst in self.rst_files:
                amihere = self.restart_directory.joinpath(rst)
                message = "Required restart is not found:\n{} ".format(amihere)
                assert amihere.is_file(), message 
        # ASSERT THAT THE RESTART FILE IS FOUND !

    @passfail
    def test_queue(self):
        # queue_list = self.queue_params['queue_list']
        # message = '{} not one of {}'.format(self.queue, queue_list)
        # assert self.queue in queue_list, message
        assert 1 == 1

    @passfail
    def test_lbcdates(self):
        # verify that the LBC dates requested are available
        pass     


    def run_all(self):
        # Emulate behavior of the unittesting module
        # Grab all of the function names beginning with test_
        testList = [method for method in
                    dir(self.__class__) if method.startswith('test_')]

        # Establish the number of tests to pass
        numTests = len(testList)
        numPassedTests = 0

        # Beginning of test message
        message = "====================== Start {}  ========================"
        message = message.format(self.__class__.__name__)
        self.logger.info(message)

        # Loop through every function starting with 'test'
        for test in testList:
            testFunction = getattr(self.__class__, test)
            success, status = testFunction(self)
            if success:
                self.logger.info(status)
            if not success:
                self.logger.error(status)
            numPassedTests += success  # zero or one

        # Log the number of passed tests
        checkStatus = "{} out of {} tests passed".format(
                                numPassedTests, numTests)
        self.logger.info(checkStatus)
        
        # Leave the script
        message = "====================== End {}  ========================"
        message = message.format(self.__class__.__name__)
        self.logger.info(message)

        # return status of test passing
        if numPassedTests != numTests:
            return False
        else:
            return True


if __name__ == '__main__':
    pass
