name = "/"
sort_key = 75

def get_problem(self, difficulty):
    import math
    x = self.generate_number(difficulty)
    y = int(math.ceil(self.generate_number(difficulty) / 2))
    question = "%s / %s" % (x*y, x)
    answer = y
    return question, answer
