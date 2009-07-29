# Copyright (C) 2009, Chris Ball <chris@printf.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""Arithmetic Activity: A quiz activity for arithmetic."""

import logging
import gtk
import pango
import random
from gettext import gettext as _
from olpcgames import mesh
from sugar.activity import activity

# Should be builtin to sugar.graphics.alert.NotifyAlert...
def _notify_response_cb(notify, response, activity):
    activity.remove_alert(notify)

class ArithmeticActivity(activity.Activity):
    """Arithmetic Activity as specified in activity.info"""
    DIFFICULTY_EASY     = False
    DIFFICULTY_MEDIUM   = False
    DIFFICULTY_HARD     = False
    MODE_ADDITION       = False
    MODE_SUBTRACTION    = False
    MODE_MULTIPLICATION = False
    MODE_DIVISION       = False

    def __init__(self, handle):
        """Set up the Arithmetic activity."""
        super(ArithmeticActivity, self).__init__(handle)
        self._logger = logging.getLogger('arithmetic-activity')
        self.numcorrect = 0
        self.numincorrect = 0
        self.answer = ""

        # Main layout
        hbox = gtk.HBox(homogeneous=True)
        vbox = gtk.VBox()

        # Toolbar
        toolbox = self.build_toolbar()

        # Horizontal fields
        difficultybox = gtk.HBox()
        modebox       = gtk.HBox()
        questionbox   = gtk.HBox()
        answerbox     = gtk.HBox()
        decisionbox   = gtk.HBox()
        correctbox    = gtk.HBox()
        incorrectbox  = gtk.HBox()

        # Labels
        difficultylabel = gtk.Label("Difficulty: ")
        modelabel       = gtk.Label("Question types: ")
        questionlabel   = gtk.Label("Question: ")
        answerlabel     = gtk.Label("Answer: ")
        decisionlabel   = gtk.Label("You were: ")

        # ToggleButtons for difficulty
        easytoggle      = gtk.ToggleButton("Easy")
        mediumtoggle    = gtk.ToggleButton("Medium")
        hardtoggle      = gtk.ToggleButton("Hard")

        easytoggle.connect("toggled", self.easy_cb)
        mediumtoggle.connect("toggled", self.medium_cb)
        hardtoggle.connect("toggled", self.hard_cb)

        # ToggleButtons for question type
        addtoggle       = gtk.ToggleButton("Addition")
        subtracttoggle  = gtk.ToggleButton("Subtraction")
        multiplytoggle  = gtk.ToggleButton("Multiplication")
        dividetoggle    = gtk.ToggleButton("Division")

        addtoggle.connect("toggled", self.add_cb)
        subtracttoggle.connect("toggled", self.subtract_cb)
        dividetoggle.connect("toggled", self.divide_cb)
        multiplytoggle.connect("toggled", self.multiply_cb)

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

        # Scorekeeping
        self.correctlabel = gtk.Label("Number of correct answers: ")
        self.incorrectlabel = gtk.Label("Number of incorrect answers: ")

        # Packing
        difficultybox.pack_start(difficultylabel, expand=False)
        difficultybox.pack_start(easytoggle, expand=False)
        difficultybox.pack_start(mediumtoggle, expand=False)
        difficultybox.pack_start(hardtoggle, expand=False)

        modebox.pack_start(modelabel, expand=False)
        modebox.pack_start(addtoggle, expand=False)
        modebox.pack_start(subtracttoggle, expand=False)
        modebox.pack_start(multiplytoggle, expand=False)
        modebox.pack_start(dividetoggle, expand=False)

        questionbox.pack_start(questionlabel, expand=False)
        questionbox.pack_start(self.questionentry)
        answerbox.pack_start(answerlabel, expand=False)
        answerbox.pack_start(self.answerentry)
        decisionbox.pack_start(decisionlabel, expand=False)
        decisionbox.pack_start(self.decisionentry)
        correctbox.pack_start(self.correctlabel, expand=False)
        incorrectbox.pack_start(self.incorrectlabel, expand=False)

        vbox.pack_start(difficultybox, expand=False) 
        vbox.pack_start(modebox, expand=False)
        vbox.pack_start(questionbox, expand=False) 
        vbox.pack_start(answerbox, expand=False)
        vbox.pack_start(decisionbox, expand=False)
        vbox.pack_start(correctbox, expand=False)
        vbox.pack_start(incorrectbox, expand=False)
        vbox.pack_start(hbox)

        # Set defaults for questions.
        easytoggle.set_active(True)
        addtoggle.set_active(True)

        # Make a new question.
        self.generate_new_question()

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
        question, self.answer = self.generate_problem(mode, difficulty)
        self.questionentry.set_text(question)

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
            y = self.generate_number(difficulty)
            question = "%s / %s" % (x, y)
            answer = x / y
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

    """Callbacks."""
    def answer_cb(self, answer):
        try:
            answer = int(answer.get_text())
        except ValueError:
            self.answerentry.set_text("")
            return

        if int(answer) == int(self.answer):
            self.decisionentry.set_text("Correct!")
            self.numcorrect += 1
        else:
            self.decisionentry.set_text("Not correct")
            self.numincorrect += 1

        self.generate_new_question()
        self.answerentry.set_text("")
        self.correctlabel.set_text("Number of correct answers: %s" %
                                   self.numcorrect)
        self.incorrectlabel.set_text("Number of incorrect answers: %s" %
                                     self.numincorrect)

        participants = mesh.get_participants()
        logging.error("participants are: %s" % participants)
        for handle in participants:
            buddy = mesh.get_buddy(handle)
            logging.error(buddy.props.nick)

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

    def build_toolbar( self ):
        """Build our Activity toolbar for the Sugar system

        This is a customisation point for those games which want to
        provide custom toolbars when running under Sugar.
        """
        toolbar = activity.ActivityToolbar(self)
        toolbar.show()
        self.set_toolbox(toolbar)
        def shared_cb(*args, **kwargs):
            logging.error( 'shared: %s, %s', args, kwargs )
            mesh.activity_shared(self)

        def joined_cb(*args, **kwargs):
            logging.error( 'joined: %s, %s', args, kwargs )
            mesh.activity_joined(self)

        self.connect("shared", shared_cb)
        self.connect("joined", joined_cb)

        if self.get_shared():
            # if set at this point, it means we've already joined (i.e.,
            # launched from Neighborhood)
            joined_cb()

        toolbar.title.unset_flags(gtk.CAN_FOCUS)
        return toolbar
