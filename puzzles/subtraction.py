name = "-"
sort_key = 25

def get_problem(self, difficulty):
    x = self.generate_number(difficulty)
    y = self.generate_number(difficulty)
    question = "%s - %s" % (x, y)
    answer = x - y
    return question, answer
