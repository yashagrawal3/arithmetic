
name = "+"
sort_key = 0

def get_problem(self, difficulty):
    x = self.generate_number(difficulty)
    y = self.generate_number(difficulty)
    question = "  %2d\n+ %2d" % (x, y)
    answer = x + y
    return question, answer
