class sValue:
    """Class to represent an sValue format dice and perform calculations on it.

    Example sValue dice:
    "16,1d3,(t-1)d2"
    where t = level // 5 + 1
    "7,1d3,(t-1)d2-1"

    Methods:
        __iter__: Return self as an iterable
        __next__: To implement min(), max() for value range, and int()
        __int__: Return the mean of the possible range
        __str__: Return the source sValue string
    """

    def __init__(self, svalue: str, level: int = 1):
        self.svalue = svalue
        t = level // 5 + 1
        # substitute creature tier in dice
        svalue = svalue.replace('(t)', str(t))
        svalue = svalue.replace('(t-1)', str(t - 1))
        svalue = svalue.replace('(t+1)', str(t + 1))
        self.t_parsed = svalue
        self.low = 0
        self.high = 0
        self.svalstring = self.t_parsed.replace(',', '+')
        for part in self.t_parsed.split(','):
            modified = False
            if '+' in part:
                part, modifier = part.split('+')
                modified = True
            elif '-' in part:
                part, modifier = part.split('-')
                modified = True
            if 'd' not in part:
                self.low += int(part)
                self.high += int(part)
            else:
                num, die = part.split('d')
                self.low += int(num)
                self.high += int(num) * int(die)
            if modified:
                self.low += int(modifier)
                self.high += int(modifier)
        self.current_iter = self.low

    def __iter__(self):
        return self

    def __len__(self):
        return self.high - self.low + 1

    def __next__(self):
        if self.current_iter > self.high:
            self.current_iter = self.low
            raise StopIteration
        else:
            self.current_iter += 1
            return self.current_iter - 1

    def __int__(self):
        return sum(self) // len(self)

    def __str__(self):
        if len(self) == 1:
            return str(self.low)
        else:
            # return str(self.low) + " - " + str(self.high)
            return str(self.svalstring)

    def __repr__(self):
        return "sValue " + self.svalue
