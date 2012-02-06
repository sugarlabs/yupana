# -*- coding: utf-8 -*-
#Copyright (c) 2011 Walter Bender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA


import gtk
import cairo

from random import uniform

from gettext import gettext as _

import logging
_logger = logging.getLogger('yupana-activity')

try:
    from sugar.graphics import style
    GRID_CELL_SIZE = style.GRID_CELL_SIZE
except ImportError:
    GRID_CELL_SIZE = 0

from sprites import Sprites, Sprite

# Grid dimensions must be even
TEN = 10
SIX = 6
DOT_SIZE = 20


class Yupana():

    def __init__(self, canvas, parent=None, colors=['#A0FFA0', '#FF8080']):
        self._activity = parent
        self._colors = ['#FFFFFF']
        self._colors.append(colors[0])
        self._colors.append(colors[1])
        self._colors.append('#000000')

        self._canvas = canvas
        if parent is not None:
            parent.show_all()
            self._parent = parent

        self._canvas.set_flags(gtk.CAN_FOCUS)
        self._canvas.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self._canvas.connect("expose-event", self._expose_cb)
        self._canvas.connect("button-press-event", self._button_press_cb)

        self._width = gtk.gdk.screen_width()
        self._height = gtk.gdk.screen_height() - (GRID_CELL_SIZE * 1.5)
        self._scale = self._width / (20 * DOT_SIZE * 1.1)
        self._dot_size = int(DOT_SIZE * self._scale)
        self._space = int(self._dot_size / 5.)
        self.we_are_sharing = False
        self._sum = 0
        self._mode = 'ten'

        # Generate the sprites we'll need...
        self._sprites = Sprites(self._canvas)
        Sprite(self._sprites, 0, 0, self._box(self._width, self._height,
                                              color=colors[1]))

        self._dots = []
        for p in range(SIX):
            y = self._height - self._space
            Sprite(self._sprites, 0, y, self._line(vertical=False))

            x = int(p * self._width / 6) + self._space
            y -= self._dot_size
            for d in range(3):  # bottom of fives row
                self._dots.append(
                    Sprite(self._sprites, x, y,
                           self._new_dot(self._colors[0])))
                self._dots[-1].type = 0  # not set
                x += self._dot_size + self._space
            x = int((p * self._width / 6.) + self._dot_size / 2.) + self._space
            y -= self._dot_size + self._space
            for d in range(2):  # top of fives row
                self._dots.append(
                    Sprite(self._sprites, x, y,
                           self._new_dot(self._colors[0])))
                self._dots[-1].type = 0  # not set
                x += self._dot_size + self._space

            y -= self._dot_size
            Sprite(self._sprites, 0, y, self._line(vertical=False))

            x = int((p * self._width / 6.) + self._dot_size / 2.) + self._space
            y -= self._dot_size
            for d in range(2):  # bottom of threes row
                self._dots.append(
                    Sprite(self._sprites, x, y,
                           self._new_dot(self._colors[0])))
                self._dots[-1].type = 0  # not set
                x += self._dot_size + self._space
            x = int((p * self._width / 6.) + self._dot_size) + self._space
            y -= self._dot_size + self._space
            for d in range(1):  # top of threes row
                self._dots.append(
                    Sprite(self._sprites, x, y,
                           self._new_dot(self._colors[0])))
                self._dots[-1].type = 0  # not set
                x += self._dot_size + self._space

            y -= self._dot_size
            Sprite(self._sprites, 0, y, self._line(vertical=False))

            x = int((p * self._width / 6.) + self._dot_size / 2.) + self._space
            y -= self._dot_size
            for d in range(2):  # twos row
                self._dots.append(
                    Sprite(self._sprites, x, y,
                           self._new_dot(self._colors[0])))
                self._dots[-1].type = 0  # not set
                x += self._dot_size + self._space

            y -= self._dot_size
            Sprite(self._sprites, 0, y, self._line(vertical=False))

            x = int((p * self._width / 6.) + self._dot_size) + self._space
            y -= self._dot_size
            for d in range(1):  # ones row
                self._dots.append(
                    Sprite(self._sprites, x, y,
                           self._new_dot(self._colors[0])))
                self._dots[-1].type = 0  # not set
                x += self._dot_size + self._space

            y -= self._dot_size
            Sprite(self._sprites, 0, y, self._line(vertical=False))

        for p in range(SIX - 1):
            x = int((p + 1) * self._width / 6)
            Sprite(self._sprites, x - 1, y,
                   self._line(vertical=True))

        self._number_box = Sprite(self._sprites, 0, 0, self._box(
                self._width, 3 * self._dot_size, color=colors[1]))
        self._number_box.set_label_attributes(72)

        # and initialize a few variables we'll need.
        self._all_clear()

    def _all_clear(self):
        ''' Things to reinitialize when starting up a new yupana. '''
        self._sum = 0
        for dot in self._dots:
            if dot.type > 0:
                dot.type = 0
                dot.set_shape(self._new_dot(self._colors[0]))
            dot.set_label('')
        self._set_label(str(self._sum))

    def _initiating(self):
        return self._activity.initiating

    def new_yupana(self, mode=None):
        ''' Create a new yupana. '''
        self._all_clear()

        if mode is not None:
            self._mode = mode

        if self.we_are_sharing:
            _logger.debug('sending a new yupana')
            self._parent.send_new_yupana()

    def restore_yupana(self, dot_list):
        ''' Restore a yumpana from the Journal or share '''
        for i, dot in enumerate(dot_list):
            self._dots[i].type = dot
            self._dots[i].set_shape(self._new_dot(
                    self._colors[self._dots[i].type]))
            if self._dots[i].type == 1:
                self._sum += self._calc_bead_value(i)
        self._set_label(str(self._sum))

    def save_yupana(self):
        ''' Return dot list and orientation for saving to Journal or
        sharing '''
        dot_list = []
        for dot in self._dots:
            dot_list.append(dot.type)
        return [self._mode, dot_list]

    def _set_label(self, string):
        ''' Set the label in the toolbar or the window frame. '''
        self._number_box.set_label(string)
        # self._activity.status.set_label(string)

    def _button_press_cb(self, win, event):
        win.grab_focus()
        x, y = map(int, event.get_coords())

        spr = self._sprites.find_sprite((x, y))
        if spr == None:
            return

        if spr.type is not None:
            spr.type += 1
            spr.type %= 2
            spr.set_shape(self._new_dot(self._colors[spr.type]))

            if self.we_are_sharing:
                _logger.debug('sending a click to the share')
                self._parent.send_dot_click(self._dots.index(spr),
                                            spr.type)

            if spr.type == 1:
                self._sum += self._calc_bead_value(self._dots.index(spr))
            else:
                self._sum -= self._calc_bead_value(self._dots.index(spr))
            self._set_label(str(self._sum))
        return True

    def _calc_bead_value(self, i):
        ''' Calculate a bead value based on the index and the mode '''
        e = 5 - i / (TEN + 1)
        m = i % 11
        if self._mode == 'ten':
            return 10 ** e
        elif self._mode == 'twenty':
            if m in [7, 10]:
                return 20 ** e
            else:
                return (20 ** e) * 2
        else:  # factor mode
            if m in [10]:
                return 10 ** e
            elif m in [8, 9]:
                return (10 ** e) * 2
            elif m in [5, 6, 7]:
                return (10 ** e) * 3
            else:
                return (10 ** e) * 5

    def remote_button_press(self, dot, color):
        ''' Receive a button press from a sharer '''
        self._dots[dot].type = color
        self._dots[dot].set_shape(self._new_dot(self._colors[color]))

    def set_sharing(self, share=True):
        _logger.debug('enabling sharing')
        self.we_are_sharing = share

    def _grid_to_dot(self, pos):
        ''' calculate the dot index from a column and row in the grid '''
        return pos[0] + pos[1] * TEN

    def _dot_to_grid(self, dot):
        ''' calculate the grid column and row for a dot '''
        return [dot % TEN, int(dot / TEN)]

    def _expose_cb(self, win, event):
        self.do_expose_event(event)

    def do_expose_event(self, event):
        ''' Handle the expose-event by drawing '''
        # Restrict Cairo to the exposed area
        cr = self._canvas.window.cairo_create()
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()
        # Refresh sprite list
        self._sprites.redraw_sprites(cr=cr)

    def _destroy_cb(self, win, event):
        gtk.main_quit()

    def _new_dot(self, color):
        ''' generate a dot of a color color '''
        def darken(color):
            ''' return a darker color than color '''
            gdk_fill_color = gtk.gdk.color_parse(self._fill)
            gdk_fill_dark_color = gtk.gdk.Color(
                int(gdk_fill_color.red * 0.5),
                int(gdk_fill_color.green * 0.5),
                int(gdk_fill_color.blue * 0.5))
            return str(gdk_fill_dark_color)

        self._dot_cache = {}
        if not color in self._dot_cache:
            self._stroke = color
            self._fill = color
            self._fill_dark = darken(color)
            self._svg_width = self._dot_size
            self._svg_height = self._dot_size
            if color in ['#FFFFFF', '#000000']:
                pixbuf = svg_str_to_pixbuf(
                    self._header() + \
                    self._circle(self._dot_size / 2., self._dot_size / 2.,
                                 self._dot_size / 2.) + \
                    self._footer())
            else:
                pixbuf = svg_str_to_pixbuf(
                    self._header() + \
                    self._def(self._dot_size) + \
                    self._gradient(self._dot_size / 2., self._dot_size / 2.,
                                 self._dot_size / 2.) + \
                    self._footer())

            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                         self._svg_width, self._svg_height)
            context = cairo.Context(surface)
            context = gtk.gdk.CairoContext(context)
            context.set_source_pixbuf(pixbuf, 0, 0)
            context.rectangle(0, 0, self._svg_width, self._svg_height)
            context.fill()
            self._dot_cache[color] = surface

        return self._dot_cache[color]

    def _line(self, vertical=True):
        ''' Generate a center line '''
        if vertical:
            self._svg_width = 3
            self._svg_height = self._dot_size * 10 + self._space * 2
            return svg_str_to_pixbuf(
                self._header() + \
                self._rect(3, self._dot_size * 10 + self._space * 2, 0, 0) + \
                self._footer())
        else:
            self._svg_width = self._width
            self._svg_height = 3
            return svg_str_to_pixbuf(
                self._header() + \
                self._rect(self._width, 3, 0, 0) + \
                self._footer())

    def _box(self, w, h, color='white'):
        ''' Generate a box '''
        self._svg_width = w
        self._svg_height = h
        return svg_str_to_pixbuf(
                self._header() + \
                self._rect(self._svg_width, self._svg_height, 0, 0,
                           color=color) + \
                self._footer())

    def _header(self):
        return '<svg\n' + 'xmlns:svg="http://www.w3.org/2000/svg"\n' + \
            'xmlns="http://www.w3.org/2000/svg"\n' + \
            'xmlns:xlink="http://www.w3.org/1999/xlink"\n' + \
            'version="1.1"\n' + 'width="' + str(self._svg_width) + '"\n' + \
            'height="' + str(self._svg_height) + '">\n'

    def _rect(self, w, h, x, y, color='black'):
        svg_string = '       <rect\n'
        svg_string += '          width="%f"\n' % (w)
        svg_string += '          height="%f"\n' % (h)
        svg_string += '          rx="%f"\n' % (0)
        svg_string += '          ry="%f"\n' % (0)
        svg_string += '          x="%f"\n' % (x)
        svg_string += '          y="%f"\n' % (y)
        if color == 'black':
            svg_string += 'style="fill:#000000;stroke:#000000;"/>\n'
        elif color == 'white':
            svg_string += 'style="fill:#ffffff;stroke:#ffffff;"/>\n'
        else:
            svg_string += 'style="fill:%s;stroke:%s;"/>\n' % (color, color)
        return svg_string

    def _circle(self, r, cx, cy):
        return '<circle style="fill:' + str(self._fill) + ';stroke:' + \
            str(self._stroke) + ';" r="' + str(r - 0.5) + '" cx="' + \
            str(cx) + '" cy="' + str(cy) + '" />\n'

    def _gradient(self, r, cx, cy):
        return '<circle style="fill:url(#radialGradient3761);' + \
            'fill-opacity:1;stroke:none;" r="' + str(r - 0.5) + '" cx="' + \
            str(cx) + '" cy="' + str(cy) + '" />\n'

    def _def(self, r):
        return '  <defs>\
    <linearGradient\
       id="linearGradient3755">\
      <stop\
         id="stop3757"\
         style="stop-color:%s;stop-opacity:1"\
         offset="0" />\
      <stop\
         id="stop3759"\
         style="stop-color:%s;stop-opacity:1"\
         offset="1" />\
    </linearGradient>\
    <radialGradient\
       cx="0"\
       cy="0"\
       r="%f"\
       fx="%f"\
       fy="%f"\
       id="radialGradient3761"\
       xlink:href="#linearGradient3755"\
       gradientUnits="userSpaceOnUse" />\
  </defs>\
' % (self._fill, self._fill_dark, r, r / 3, r / 3)

    def _footer(self):
        return '</svg>\n'


def svg_str_to_pixbuf(svg_string):
    """ Load pixbuf from SVG string """
    pl = gtk.gdk.PixbufLoader('svg')
    pl.write(svg_string)
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf
