import abc

NOT_IMPLEMENTED = 'This method must be implemented'

class IO(object):
    '''
    '''
    __metaclass__ = abc.ABCMeta

    def __init__(self, implementation):
        self.implementation = implementation

    @abc.abstractmethod
    def file_close(self, *args, **kwargs):
        '''Close the file.
        '''
        raise NotImplementedError(NOT_IMPLEMENTED)
    #--- End: def

    @abc.abstractmethod
    def file_open(self, *args, **kwargs):
        '''Open the file.
        '''
        raise NotImplementedError(NOT_IMPLEMENTED)
    #--- End: def

    @abc.abstractmethod
    def file_type(cls, *args, **kwargs):
        '''Return the format of a file.
        '''
        raise NotImplementedError(NOT_IMPLEMENTED)
    #--- End: def
#--- End: class
