#Copyright (c) 2011,12 Walter Bender
#Copyright (c) 2012 Ignacio Rodriguez

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA
import gi
gi.require_version('Gdk','3.0')
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, Gdk, GObject

from sugar3.activity import activity
from sugar3 import profile
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbarbox import ToolbarButton

from toolbar_utils import button_factory, label_factory, separator_factory, \
    radio_factory, entry_factory
from utils import json_load, json_dump

from gettext import gettext as _

from collabwrapper import CollabWrapper

from yupana import Yupana

import logging
_logger = logging.getLogger('yupana-activity')


class YupanaActivity(activity.Activity):
    """ Yupana counting device """

    def __init__(self, handle):
        """ Initialize the toolbars and the yupana """
        activity.Activity.__init__(self, handle)

        self.nick = profile.get_nick_name()
        self._reload_custom = False
        if profile.get_color() is not None:
            self.colors = profile.get_color().to_string().split(',')
        else:
            self.colors = ['#A0FFA0', '#FF8080']

        self._setup_toolbars()

        # Create a canvas
        canvas = Gtk.DrawingArea()
        canvas.set_size_request(Gdk.Screen.width(), \
                                Gdk.Screen.height())
        self.set_canvas(canvas)
        canvas.show()
        self.show_all()

        self._yupana = Yupana(canvas, parent=self, colors=self.colors)
        self._setup_collab()

        if 'dotlist' in self.metadata:
            self._restore()
        else:
            self._yupana.new_yupana(mode='ten')

        self._make_custom_toolbar()
        if self._reload_custom:
            self._custom_cb()

    def _setup_toolbars(self):
        """ Setup the toolbars. """

        self.max_participants = 4

        yupana_toolbar = Gtk.Toolbar()
        self.custom_toolbar = Gtk.Toolbar()
        toolbox = ToolbarBox()

        # Activity toolbar
        activity_button = ActivityToolbarButton(self)

        toolbox.toolbar.insert(activity_button, 0)
        activity_button.show()

        yupana_toolbar_button = ToolbarButton(
            label=_("Mode"), page=yupana_toolbar,
            icon_name='preferences-system')
        yupana_toolbar.show()
        toolbox.toolbar.insert(yupana_toolbar_button, -1)
        yupana_toolbar_button.show()

        custom_toolbar_button = ToolbarButton(
            label=_("Custom"), page=self.custom_toolbar,
            icon_name='view-source')
        self.custom_toolbar.show()
        toolbox.toolbar.insert(custom_toolbar_button, -1)
        custom_toolbar_button.show()

        self.set_toolbar_box(toolbox)
        toolbox.show()
        self.toolbar = toolbox.toolbar

        self._new_yupana_button = button_factory(
            'edit-delete', self.toolbar, self._new_yupana_cb,
            tooltip=_('Clear the yupana.'))

        separator_factory(yupana_toolbar, False, True)

        self.ten_button = radio_factory(
            'ten', yupana_toolbar, self._ten_cb, tooltip=_('decimal mode'),
            group=None)
        self.twenty_button = radio_factory(
            'twenty', yupana_toolbar, self._twenty_cb,
            tooltip=_('base-twenty mode'),
            group=self.ten_button)
        self.factor_button = radio_factory(
            'factor', yupana_toolbar, self._factor_cb,
            tooltip=_('prime-factor mode'),
            group=self.ten_button)
        self.fibonacci_button = radio_factory(
            'fibonacci', yupana_toolbar, self._fibonacci_cb,
            tooltip=_('Fibonacci mode'),
            group=self.ten_button)
        self.custom_button = radio_factory(
            'view-source', yupana_toolbar, self._custom_cb,
            tooltip=_('custom mode'),
            group=self.ten_button)

        separator_factory(self.toolbar, False, False)
        self.status = label_factory(self.toolbar, '', width=200)
        self.status.set_label(_('decimal mode'))

        separator_factory(toolbox.toolbar, True, False)

        stop_button = StopButton(self)
        stop_button.props.accelerator = '<Ctrl>q'
        toolbox.toolbar.insert(stop_button, -1)
        stop_button.show()

    def _make_custom_toolbar(self):
        self._ones = entry_factory(str(self._yupana.custom[0]),
                                   self.custom_toolbar,
                                   tooltip=_('one row'))
        self._twos = entry_factory(str(self._yupana.custom[1]),
                                   self.custom_toolbar,
                                   tooltip=_('two row'))
        self._threes = entry_factory(str(self._yupana.custom[2]),
                                     self.custom_toolbar,
                                     tooltip=_('three row'))
        self._fives = entry_factory(str(self._yupana.custom[3]),
                                    self.custom_toolbar,
                                    tooltip=_('five row'))

        separator_factory(self.custom_toolbar, False, True)
        self._base = entry_factory(str(self._yupana.custom[4]),
                                   self.custom_toolbar,
                                   tooltip=_('base'))

        separator_factory(self.custom_toolbar, False, True)
        button_factory('view-refresh', self.custom_toolbar, self._custom_cb,
                       tooltip=_('Reload custom values.'))

    def _new_yupana_cb(self, button=None):
        ''' Start a new yupana. '''
        self._yupana.new_yupana()

    def _ten_cb(self, button=None):
        self._yupana.new_yupana(mode='ten')
        self.status.set_label(_('decimal mode'))

    def _twenty_cb(self, button=None):
        self._yupana.new_yupana(mode='twenty')
        self.status.set_label(_('base-twenty mode'))

    def _factor_cb(self, button=None):
        self._yupana.new_yupana(mode='factor')
        self.status.set_label(_('prime-factor mode'))

    def _fibonacci_cb(self, button=None):
        self._yupana.new_yupana(mode='fibonacci')
        self.status.set_label(_('Fibonacci mode'))

    def _custom_cb(self, button=None):
        if hasattr(self, '_ones'):
            self._yupana.custom[0] = int(self._ones.get_text())
            self._yupana.custom[1] = int(self._twos.get_text())
            self._yupana.custom[2] = int(self._threes.get_text())
            self._yupana.custom[3] = int(self._fives.get_text())
            self._yupana.custom[4] = int(self._base.get_text())
            self._reload_custom = False
        else:
            self._reload_custom = True
        self._yupana.new_yupana(mode='custom')
        self.status.set_label(_('custom mode'))

    def write_file(self, file_path):
        """ Write the grid status to the Journal """
        [mode, dot_list] = self._yupana.save_yupana()
        self.metadata['mode'] = mode
        self.metadata['custom'] = ''
        for i in range(5):
            self.metadata['custom'] += str(self._yupana.custom[i])
            self.metadata['custom'] += ' '
        self.metadata['dotlist'] = ''
        for dot in dot_list:
            self.metadata['dotlist'] += str(dot)
            if dot_list.index(dot) < len(dot_list) - 1:
                self.metadata['dotlist'] += ' '
        self.metadata['label'] = self._yupana.get_label()

    def _restore(self):
        """ Restore the yupana state from metadata """
        if 'custom' in self.metadata:
            values = self.metadata['custom'].split()
            for i in range(5):
                self._yupana.custom[i] = int(values[i])
        if 'mode' in self.metadata:
            if self.metadata['mode'] == 'ten':
                self.ten_button.set_active(True)
            elif self.metadata['mode'] == 'twenty':
                self.twenty_button.set_active(True)
            elif self.metadata['mode'] == 'factor':
                self.factor_button.set_active(True)
            elif self.metadata['mode'] == 'fibonacci':
                self.fibonacci_button.set_active(True)
            else:
                self.custom_button.set_active(True)
        if 'dotlist' in self.metadata:
            dot_list = []
            dots = self.metadata['dotlist'].split()
            for dot in dots:
                dot_list.append(int(dot))
            self._yupana.restore_yupana(self.metadata['mode'],dot_list)
        self._yupana.set_label(self.metadata['label'])

    # Collaboration-related methods

    def _setup_collab(self):
        """ Setup the Presence Service. """
        self.initiating = None  # sharing (True) or joining (False)

        self.connect('shared', self._shared_cb)
        self.connect('joined', self._joined_cb)
        self._collab = CollabWrapper(self)
        self._collab.connect('message', self._message_cb)
        self._collab.connect('joined', self._joined_cb)
        self._collab.setup()

    def set_data(self, data):
        pass

    def get_data(self):
        return None

    def _shared_cb(self, activity):
        """ Either set up initial share..."""
        self.after_share_join(True)

    def _joined_cb(self, activity):
        """ ...or join an exisiting share. """
        self.after_share_join(False)

    def after_share_join(self, sharer):
        """ Joining and sharing are mostly the same... """
        self.initiating = sharer
        self.waiting_for_hand = not sharer

        self._yupana.set_sharing(True)

    def _message_cb(self, collab, buddy, msg):
        command = msg.get('command')
        payload = msg.get('payload')
        if command == 'new_game':
            '''Get a new yupana grid'''
            self._receive_new_yupana(payload)
        elif command == 'played':
            '''Get a dot click'''
            self._receive_dot_click(payload)
        elif command == 'label':
            self._yupana.set_label(payload)

    def send_new_yupana(self):
        ''' Send a new orientation, grid to all players '''
        self._collab.post(dict(
            command='new_game',
            payload=json_dump(self._yupana.save_yupana())
        ))

    def _receive_new_yupana(self, payload):
        ''' Sharer can start a new yupana. '''
        mode,dot_list = json_load(payload)
        self._yupana.restore_yupana(mode,dot_list)

    def send_dot_click(self, dot, color):
        ''' Send a dot click to all the players '''
        self._collab.post(dict(
            command='played',
            payload=json_dump([dot, color])
        ))

    def _receive_dot_click(self, payload):
        ''' When a dot is clicked, everyone should change its color. '''
        (dot, color) = json_load(payload)
        self._yupana.remote_button_press(dot, color)

    def send_label(self, label):
        self.last_label = label
        self._collab.post(dict(
            command='label',
            payload=label
        ))
