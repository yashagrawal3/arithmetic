name = "!"
sort_key = 95

def get_problem(self, difficulty):
    import math
    x = self.generate_number(difficulty)
    question = " %s!" % (x)
    answer = math.factorial(x)
    return question, answer
