class sValue:
    """Class to represent an sValue format dice and perform calculations on it.

    Example sValue dice:
    "16,1d3,(t-1)d2"
    where t = level // 5 + 1

    Methods:
        __iter__: Return self as an iterable
        __next__: To implement min(), max() for value range, and int()
        __int__: Return the mean of the possible range
        __str__: Return the source sValue string
    """
    def __init__(self, svalue: str, qud_object):
        self.svalue = svalue
        self.low = 0  # TODO
        self.high = 1  # TODO
        self.current_iter = self.low

    def __iter__(self):
        return self

    def __next__(self):
        if self.current_iter_index > self.high:
            raise StopIteration
        else:
            self.current_iter += 1
            return self.current_iter - 1

    def __int__(self):
        return sum(self) // 2

    def __str__(self):
        return self.svalue
