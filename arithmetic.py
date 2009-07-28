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

import os
import logging
import re
import gtk
import pango
import gobject
import random
from gettext import gettext as _

from sugar.activity import activity
from sugar import env
from sugar.graphics import iconentry
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics.toggletoolbutton import ToggleToolButton
from sugar.graphics.palette import Palette
from sugar.graphics.alert import NotifyAlert

# Should be builtin to sugar.graphics.alert.NotifyAlert...
def _notify_response_cb(notify, response, activity):
    activity.remove_alert(notify)

SERVICE = "org.laptop.Arithmetic"
IFACE = SERVICE
PATH = "/org/laptop/Arithmetic"

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

        from sugar.graphics.menuitem import MenuItem
        from sugar.graphics.icon import Icon

        # Main layout
        hbox = gtk.HBox(homogeneous=True)
        vbox = gtk.VBox()

        # Toolbar
        toolbox = activity.ActivityToolbox(self)
        self.set_toolbox(toolbox)
        toolbox.show()

        # Horizontal fields
        difficultybox = gtk.HBox()
        modebox       = gtk.HBox()
        questionbox   = gtk.HBox()
        answerbox     = gtk.HBox()

        # Labels
        difficultylabel = gtk.Label("Difficulty: ")
        modelabel       = gtk.Label("Question types: ")
        questionlabel   = gtk.Label("Question: ")
        answerlabel     = gtk.Label("Answer:")

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
        self.question = gtk.Entry(max=50)
        self.question.modify_font(pango.FontDescription("Sans 14"))
        self.question.set_property("editable", False)
        
        # Text entry box for answer
        self.answer = gtk.Entry(max=50)
        self.answer.modify_font(pango.FontDescription("Sans 14"))
        self.answer.connect("activate", self.answer_cb)

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
        questionbox.pack_start(self.question)
        answerbox.pack_start(answerlabel, expand=False)
        answerbox.pack_start(self.answer)

        vbox.pack_start(difficultybox, expand=False) 
        vbox.pack_start(modebox, expand=False)
        vbox.pack_start(questionbox, expand=False) 
        vbox.pack_start(answerbox, expand=False)
        vbox.pack_start(hbox)

        # Set defaults for questions.
        easytoggle.set_active(True)
        addtoggle.set_active(True)

        # Make a new question.
        self.generate_new_question()

        self.set_canvas(vbox)
        self.answer.grab_focus()
        self.show_all()

    def generate_new_question(self):
        modelist = list()
        if self.MODE_ADDITION:
            possible_modes.append("addition")
        if self.MODE_SUBTRACTION:
            possible_modes.append("subtraction")
        if self.MODE_MULTIPLICATION:
            possible_modes.append("multiplication")
        if self.MODE_DIVISION:
            possible_modes.append("division")

        difficultylist = list()
        if self.DIFFICULTY_EASY:
            possible_difficulties.append("easy")
        if self.DIFFICULTY_MEDIUM:
            possible_difficulties.append("medium")
        if self.DIFFICULTY_HARD:
            possible_difficulties.append("hard")
        
        mode = random.choice(modelist)
        logging.debug("mode: " + mode)
        difficulty = random.choice(difficultylist)
        logging.debug("difficulty choice: " + difficulty)

        if mode == "addition":
            self.question.set_text("%s + %s" % self.generate_add(difficulty))
        elif mode == "subtraction":
            self.question.set_text("%s - %s" % (self.generate_subtract(difficulty)))
        elif mode == "multiplication":
            self.question.set_text("%s x %s" % (self.generate_multiply(difficulty)))
        elif mode == "division":
            self.question.set_text("%s / %s" % (self.generate_divide(difficulty)))

    def generate_add(self, difficulty):
        if difficulty == "easy":
            return (random.randint(1, 9), random.randint(1, 9))
        elif difficulty == "medium":
            return (random.randint(1, 19), random.randint(1, 19))
        elif difficulty == "hard":
            return (random.randint(1, 50), random.randint(1,50))
        
    def generate_subtract(self, difficulty):
        if difficulty == "easy":
            return (random.randint(1, 9), random.randint(1, 9))
        elif difficulty == "medium":
            return (random.randint(1, 19), random.randint(1, 19))
        elif difficulty == "hard":
            return (random.randint(1, 50), random.randint(1,50))

    def generate_multiply(self, difficulty):
        if difficulty == "easy":
            return (random.randint(1, 9), random.randint(1, 9))
        elif difficulty == "medium":
            return (random.randint(1, 19), random.randint(1, 19))
        elif difficulty == "hard":
            return (random.randint(1, 50), random.randint(1,50))

    def generate_divide(self, difficulty):
        if difficulty == "easy":
            return (random.randint(1, 9), random.randint(1, 9))
        elif difficulty == "medium":
            return (random.randint(1, 19), random.randint(1, 19))
        elif difficulty == "hard":
            return (random.randint(1, 50), random.randint(1,50))


    """Callbacks."""
    def answer_cb(self, answer):
        if not answer:
            return
        logging.debug("in answer_cb, answer is " + answer.get_text())
        self.generate_new_question()
        self.answer.set_text("")

    def easy_cb(self, toggled):
        self.DIFFICULTY_EASY = toggled.get_active()
        self.answer.grab_focus()

    def medium_cb(self, toggled):
        self.DIFFICULTY_MEDIUM = toggled.get_active()
        self.answer.grab_focus()

    def hard_cb(self, toggled):
        self.DIFFICULTY_HARD = toggled.get_active()
        self.answer.grab_focus()

    def add_cb(self, toggled):
        self.MODE_ADDITION = toggled.get_active()
        self.answer.grab_focus()

    def subtract_cb(self, toggled):
        self.MODE_SUBTRACTION = toggled.get_active()
        self.answer.grab_focus()

    def multiply_cb(self, toggled):
        self.MODE_MULTIPLICATION = toggled.get_active()
        self.answer.grab_focus()

    def divide_cb(self, toggled):
        self.MODE_DIVISION = toggled.get_active()
        self.answer.grab_focus()
