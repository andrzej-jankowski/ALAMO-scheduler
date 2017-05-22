import abc


class DriverBase(object, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def send(self, check):
        """Send the data to the appropriate queue.
        :param dict check: Check data
        """
