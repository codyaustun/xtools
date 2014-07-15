class Counter:
    """docstring for Counter"""
    def __init__(self, length, start = 1, max_steps = 100, percentage = False):
        self.length = length
        step_size = self.length / max_steps
        self.step_size = step_size if step_size != 0 else 1
        self.start = start
        self.current = self.start
        self._percentage = percentage

    # For backwards compatibility
    def next(self):
        self.step()

    def step(self):
        if (self.current % self.step_size == 0) | (self.current == self.start):
            if self._percentage:
                percentage = self.current*100./self.length
                print "\r{0} percent".format(percentage,100),
            else:
                print "\r{0} out of {1}".format(self.current,self.length),
        self.current = self.current + 1
        