# Copyright (C) 2009, Chris Ball <chris@printf.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
"""Arithmetic Activity: A quiz activity for arithmetic."""

import logging
import gtk
import pango
import random
import gobject
import math
import time
import groupthink
import groupthink.sugar_tools

from gettext import gettext as _
from sugar.activity import activity
from sugar import profile

def score_codec(score_or_opaque, pack_or_unpack):
    v = score_or_opaque
    if pack_or_unpack:
        return (v.cumulative_score, v.last_score, v.last_time)
    else:
        return ImmutableScore(cumulative_score=v[0],
                              last_score=v[1],
                              last_time=v[2],
                              )

class ImmutableScore(object):
    """An immutable representation of scores suitable for
    synchronization through Groupthink. The codec function
    is named score_codec."""
    
    def __init__(self, old_score = None, cumulative_score=0, last_score=0, last_time=0.0):
        """Immutable objects may be constructed in absolute or relative terms.
        Absolute terms are used when old_score is None.
        Relative terms are used when old_score is an ImmutableScore.
        """
        attrs = [("cumulative_score", lambda a,b: a+b),
                 ("last_score", lambda a,b: b),
                 ("last_time", lambda a,b: b)]
        if old_score is not None:
            for a, u in attrs:
                setattr(self, '_'+a, u(getattr(old_score, a), locals()[a]))
        else:
            for a, u in attrs:
                setattr(self, '_'+a, locals()[a])
        
    def _get_cumulative_score(self):
        return self._cumulative_score
    cumulative_score = property(_get_cumulative_score)

    def _get_last_score(self):
        return self._last_score
    last_score = property(_get_last_score)
        
    def _get_last_time(self):
        return self._last_time
    last_time = property(_get_last_time)
               
class ArithmeticActivity(groupthink.sugar_tools.GroupActivity):
    """Arithmetic Activity as specified in activity.info"""
    DIFFICULTY_EASY     = False
    DIFFICULTY_MEDIUM   = False
    DIFFICULTY_HARD     = False
    MODE_ADDITION       = False
    MODE_SUBTRACTION    = False
    MODE_MULTIPLICATION = False
    MODE_DIVISION       = False

    # The two functions below are abstract.
    #def handle_view_source(self):
    #    pass
    #def initialize_display(self):
    #    pass

    def __init__(self, handle):
        """Set up the Arithmetic activity."""
        super(ArithmeticActivity, self).__init__(handle)
        self._logger = logging.getLogger('arithmetic-activity')
        self.numcorrect = 0
        self.starttime = 0
        self.endtime = 0
        self.secondsleft = ""
        self.question = ""
        self.answer = ""
        self.cloud.scoreboard = groupthink.CausalDict(value_translator=score_codec)
        self.scoreboard = self.cloud.scoreboard
        self.mynickname = profile.get_nick_name()
        self.scoreboard[self.mynickname] = ImmutableScore()

        # Main layout
        vbox = gtk.VBox()
        
        toolbar = activity.ActivityToolbar(self)
        toolbar.show()
        toolbar.title.unset_flags(gtk.CAN_FOCUS)
        self.set_toolbox(toolbar)

        # Scoreboard
        scorebox = gtk.VBox()
        self.model = gtk.TreeStore(gobject.TYPE_STRING, # name
                                   gobject.TYPE_INT,    # last round score
                                   gobject.TYPE_INT,    # total score
                                   gobject.TYPE_FLOAT)  # time for last question
        self.treeview = treeview = gtk.TreeView(self.model)
        cellrenderer = gtk.CellRendererText()
        col1 = gtk.TreeViewColumn(_("Name"), cellrenderer, text=0)
        col2 = gtk.TreeViewColumn(_("Round score"), cellrenderer, text=1)
        col3 = gtk.TreeViewColumn(_("Total score"), cellrenderer, text=2)
        col4 = gtk.TreeViewColumn(_("Time for answering last question"), cellrenderer, text=3)
        treeview.append_column(col1)
        treeview.append_column(col2)
        treeview.append_column(col3)
        treeview.append_column(col4)

        my_score = self.scoreboard[self.mynickname]
        
        self.olditer = self.model.insert_before(None, None)
        self.model.set_value(self.olditer, 0, self.mynickname)
        self.model.set_value(self.olditer, 1, my_score.last_score)
        self.model.set_value(self.olditer, 2, my_score.cumulative_score)
        self.model.set_value(self.olditer, 3, my_score.last_time)
        treeview.expand_all()
        scorebox.pack_start(treeview)

        # Horizontal fields
        difficultybox = gtk.HBox()
        modebox       = gtk.HBox()
        questionbox   = gtk.HBox()
        answerbox     = gtk.HBox()
        decisionbox   = gtk.HBox()
        correctbox    = gtk.HBox()
        countdownbox  = gtk.HBox()
        elapsedbox    = gtk.HBox()

        # Labels
        difficultylabel = gtk.Label("Difficulty: ")
        modelabel       = gtk.Label("Question types: ")
        questionlabel   = gtk.Label("Question: ")
        answerlabel     = gtk.Label("Answer: ")
        decisionlabel   = gtk.Label("You were: ")

        # ToggleButtons for difficulty
        self.cloud.easytoggle      = gtk.ToggleButton("Easy")
        self.cloud.mediumtoggle    = gtk.ToggleButton("Medium")
        self.cloud.hardtoggle      = gtk.ToggleButton("Hard")
        self.cloud.easytoggle.connect("toggled", self.easy_cb)
        self.cloud.mediumtoggle.connect("toggled", self.medium_cb)
        self.cloud.hardtoggle.connect("toggled", self.hard_cb)

        # ToggleButtons for question type
        self.cloud.addtoggle       = gtk.ToggleButton("Addition")
        self.cloud.subtracttoggle  = gtk.ToggleButton("Subtraction")
        self.cloud.multiplytoggle  = gtk.ToggleButton("Multiplication")
        self.cloud.dividetoggle    = gtk.ToggleButton("Division")
 
        self.cloud.addtoggle.connect("toggled", self.add_cb)
        self.cloud.subtracttoggle.connect("toggled", self.subtract_cb)
        self.cloud.dividetoggle.connect("toggled", self.divide_cb)
        self.cloud.multiplytoggle.connect("toggled", self.multiply_cb)

        # Text entry box for question
        self.questionentry = gtk.Entry(max=50)
        self.questionentry.modify_font(pango.FontDescription("Sans 14"))
        self.questionentry.set_property("editable", False)
        
        # Text entry box for answer
        self.answerentry = gtk.Entry(max=50)
        self.answerentry.modify_font(pango.FontDescription("Sans 14"))
        self.answerentry.connect("activate", self.answer_cb)

        # Whether the user was correct
        self.decisionentry = gtk.Entry(max=50)
        self.decisionentry.modify_font(pango.FontDescription("Sans 14"))
        self.decisionentry.set_property("editable", False)

        self.correctlabel = gtk.Label("Number of correct answers: ")
        self.countdownlabel = gtk.Label("Time until next question: ")
        self.elapsedlabel = gtk.Label("Time taken to answer last question: ")

        # Packing
        difficultybox.pack_start(difficultylabel, expand=False)
        difficultybox.pack_start(self.cloud.easytoggle, expand=False)
        difficultybox.pack_start(self.cloud.mediumtoggle, expand=False)
        difficultybox.pack_start(self.cloud.hardtoggle, expand=False)

        modebox.pack_start(modelabel, expand=False)
        modebox.pack_start(self.cloud.addtoggle, expand=False)
        modebox.pack_start(self.cloud.subtracttoggle, expand=False)
        modebox.pack_start(self.cloud.multiplytoggle, expand=False)
        modebox.pack_start(self.cloud.dividetoggle, expand=False)

        questionbox.pack_start(questionlabel, expand=False)
        questionbox.pack_start(self.questionentry)
        answerbox.pack_start(answerlabel, expand=False)
        answerbox.pack_start(self.answerentry)
        decisionbox.pack_start(decisionlabel, expand=False)
        decisionbox.pack_start(self.decisionentry)
        correctbox.pack_start(self.correctlabel, expand=False)
        countdownbox.pack_start(self.countdownlabel, expand=False)
        elapsedbox.pack_start(self.elapsedlabel, expand=False)

        vbox.pack_start(difficultybox, expand=False) 
        vbox.pack_start(modebox, expand=False)
        vbox.pack_start(questionbox, expand=False) 
        vbox.pack_start(answerbox, expand=False)
        vbox.pack_start(decisionbox, expand=False)
        vbox.pack_start(correctbox, expand=False)
        vbox.pack_start(countdownbox, expand=False)
        vbox.pack_start(elapsedbox, expand=False)
        vbox.pack_start(scorebox)

        # Set defaults for questions.
        self.cloud.easytoggle.set_active(True)
        self.cloud.addtoggle.set_active(True)

        # Make a new question.
        self.generate_new_question()
        self.start_question()

        self.set_canvas(vbox)
        self.answerentry.grab_focus()
        self.show_all()

    def generate_new_question(self):
        modelist = list()
        if self.MODE_ADDITION:
            modelist.append("addition")
        if self.MODE_SUBTRACTION:
            modelist.append("subtraction")
        if self.MODE_MULTIPLICATION:
            modelist.append("multiplication")
        if self.MODE_DIVISION:
            modelist.append("division")

        difficultylist = list()
        if self.DIFFICULTY_EASY:
            difficultylist.append("easy")
        if self.DIFFICULTY_MEDIUM:
            difficultylist.append("medium")
        if self.DIFFICULTY_HARD:
            difficultylist.append("hard")

        mode = random.choice(modelist)
        difficulty = random.choice(difficultylist)
        self.question, self.answer = self.generate_problem(mode, difficulty)

    def generate_problem(self, mode, difficulty):
        if mode == "addition":
            x = self.generate_number(difficulty)
            y = self.generate_number(difficulty)
            question = "%s + %s" % (x, y)
            answer = x + y
        elif mode == "subtraction":
            x = self.generate_number(difficulty)
            y = self.generate_number(difficulty, x)
            question = "%s - %s" % (x, y)
            answer = x - y
        elif mode == "multiplication":
            x = self.generate_number(difficulty)
            y = self.generate_number(difficulty)
            question = "%s x %s" % (x, y)
            answer = x * y
        elif mode == "division":
            x = self.generate_number(difficulty)
            y = int(math.ceil(self.generate_number(difficulty) / 2))
            question = "%s / %s" % (x*y, x)
            answer = y
        else:
            raise AssertionError
        return question, answer

    def generate_number(self, difficulty, lessthan=0):
        if difficulty == "easy":
            return random.randint(1, lessthan or 9)
        if difficulty == "medium":
            return random.randint(1, lessthan or 19)
        if difficulty == "hard":
            return random.randint(1, lessthan or 50)
        else:
            raise AssertionError

    def solve (self, answer):
        try:
            answer = int(answer.get_text())
        except ValueError:
            self.answerentry.set_text("")
            return

        self.endtime = time.time()
        self.elapsedlabel.set_text("Time taken to answer last question: %.2f seconds" % (self.endtime - self.starttime))
        self.model.set_value(self.olditer, 3, self.endtime - self.starttime)
        
        if int(answer) == int(self.answer):
            self.decisionentry.set_text("Correct!")
            old_score = self.scoreboard[self.mynickname]
            new_score = ImmutableScore(old_score=old_score,
                                       cumulative_score=1,
                                       last_score=1,
                                       last_time=self.endtime - self.starttime,
                                       )
            self.scoreboard[self.mynickname] = new_score
        else:
            self.decisionentry.set_text("Not correct")

        self.model = gtk.TreeStore(gobject.TYPE_STRING, # name
                                   gobject.TYPE_INT,    # last round score
                                   gobject.TYPE_INT,    # total score
                                   gobject.TYPE_FLOAT)  # time for last question

	for person, score in self.scoreboard.iteritems():
            self.model.append(None, (person, score.last_score, score.cumulative_score, score.last_time))

        self.treeview.set_model(self.model)

    # Callbacks.
    def answer_cb(self, answer):
        self.solve(answer)
        self.generate_new_question()
        self.answerentry.set_text("")
        self.correctlabel.set_text("Number of correct answers: %s" %
                                   self.scoreboard[self.mynickname])
        self.start_countdown()

    def start_countdown(self):
        self.questionentry.set_text("")
        self.secondsleft = 3
        self.countdownlabel.set_text("Time until next question: %s" % self.secondsleft)
        gobject.timeout_add(1000, self.countdown_cb)

    def countdown_cb(self):
        self.secondsleft -= 1
        self.countdownlabel.set_text("Time until next question: %s" % self.secondsleft)
        if self.secondsleft == 0:
            self.start_question()
            return False
        else:
            return True

    def start_question(self):
        self.starttime = time.time()
        self.questionentry.set_text(self.question)

    def easy_cb(self, toggled):
        self.DIFFICULTY_EASY = toggled.get_active()
        self.answerentry.grab_focus()

    def medium_cb(self, toggled):
        self.DIFFICULTY_MEDIUM = toggled.get_active()
        self.answerentry.grab_focus()

    def hard_cb(self, toggled):
        self.DIFFICULTY_HARD = toggled.get_active()
        self.answerentry.grab_focus()

    def add_cb(self, toggled):
        self.MODE_ADDITION = toggled.get_active()
        self.answerentry.grab_focus()

    def subtract_cb(self, toggled):
        self.MODE_SUBTRACTION = toggled.get_active()
        self.answerentry.grab_focus()

    def multiply_cb(self, toggled):
        self.MODE_MULTIPLICATION = toggled.get_active()
        self.answerentry.grab_focus()

    def divide_cb(self, toggled):
        self.MODE_DIVISION = toggled.get_active()
        self.answerentry.grab_focus()
