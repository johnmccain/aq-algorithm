class VRange:
    """
    A range of values from [low, high)
    """

    def __init__(self, low, high):
        self.low = low
        self.high = high

    def __contains__(self, item):
        return self.low <= item < self.high

    def intersect(self, anotherVRange):
        upper_low = self.low if self.low > anotherVRange.low else anotherVRange.low
        lower_high = self.high if self.high < anotherVRange.high else anotherVRange.highd
        return VRange(upper_low, lower_high)

    def union(self, anotherVRange):
        lower_low = self.low if self.low < anotherVRange.low else anotherVRange.low
        upper_high = self.high if self.high > anotherVRange.high else anotherVRange.highd
        return VRange(lower_low, upper_high)

    def __and__(self, anotherVRange):
        return self.intersect(anotherVRange)

    def __format__(self, anotherVRange):
        return self.union(anotherVRange)

