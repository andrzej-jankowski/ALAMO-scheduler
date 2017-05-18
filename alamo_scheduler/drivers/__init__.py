import abc

import six


@six.add_metaclass(abc.ABCMeta)
class DriverBase(object):

    @abc.abstractmethod
    def send(self, check):
        """Send the data to the appropriate queue.
        :param dict check: Check data
        """
