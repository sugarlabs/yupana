# -*- coding: utf-8 -*-
#Copyright (c) 2011-13 Walter Bender
#Copyright (c) 2012 Ignacio Rodriguez

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from random import uniform

from gettext import gettext as _

import logging
_logger = logging.getLogger('yupana-activity')

try:
    from sugar3.graphics import style
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

        self._canvas.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self._canvas.connect("draw", self.__draw_cb)
        self._canvas.connect("button-press-event", self._button_press_cb)

        self._width = Gdk.Screen.width()
        self._height = Gdk.Screen.height() - (GRID_CELL_SIZE * 1.5)
        self._scale = self._width / (20 * DOT_SIZE * 1.1)
        self._dot_size = int(DOT_SIZE * self._scale)
        self._space = int(self._dot_size / 5.)
        self.we_are_sharing = False
        self._sum = 0
        self._mode = 'ten'
        self.custom = [1, 1, 1, 1, 10]

        # Generate the sprites we'll need...
        self._sprites = Sprites(self._canvas)
        Sprite(self._sprites, 0, 0, self._box(self._width, self._height,
                                              color=colors[1]))

        self._number_box = Sprite(self._sprites, 0, 0, self._box(
                self._width, 2 * self._dot_size, color=colors[1]))
        self._number_box.set_label_attributes(48)

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
                # self._dots[-1].set_label_color('white')
                x += self._dot_size + self._space
            x = int((p * self._width / 6.) + self._dot_size / 2.) + self._space
            y -= self._dot_size + self._space
            for d in range(2):  # top of fives row
                self._dots.append(
                    Sprite(self._sprites, x, y,
                           self._new_dot(self._colors[0])))
                self._dots[-1].type = 0  # not set
                # self._dots[-1].set_label_color('white')
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
                # self._dots[-1].set_label_color('white')
                x += self._dot_size + self._space
            x = int((p * self._width / 6.) + self._dot_size) + self._space
            y -= self._dot_size + self._space
            for d in range(1):  # top of threes row
                self._dots.append(
                    Sprite(self._sprites, x, y,
                           self._new_dot(self._colors[0])))
                self._dots[-1].type = 0  # not set
                # self._dots[-1].set_label_color('white')
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
                # self._dots[-1].set_label_color('white')
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
                # self._dots[-1].set_label_color('white')
                x += self._dot_size + self._space

            y -= self._dot_size
            Sprite(self._sprites, 0, y, self._line(vertical=False))

        for p in range(SIX - 1):
            x = int((p + 1) * self._width / 6)
            Sprite(self._sprites, x - 1, y,
                   self._line(vertical=True))

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
            o = (SIX - 1) * (TEN + 1)  # only label units 
            if mode == 'ten':
                for i in range(TEN + 1):
                    self._dots[o + i].set_label('1')
                self._dots[o - 1].set_label('10')
            elif mode == 'twenty':
                for i in range(TEN + 1):
                    if i in [7, 10]:
                        self._dots[o + i].set_label('1')
                    else:
                        self._dots[o + i].set_label('2')
                self._dots[o - 1].set_label('20')
            elif mode == 'factor':
                for i in range(TEN + 1):
                    if i in [10]:
                        self._dots[o + i].set_label('1')
                    elif i in [8, 9]:
                        self._dots[o + i].set_label('2')
                    elif i in [5, 6, 7]:
                        self._dots[o + i].set_label('3')
                    else:
                        self._dots[o + i].set_label('5')
                self._dots[o - 1].set_label('10')
            elif mode == 'fibonacci':
                for i in range(TEN + 1):
                    if i in [10]:
                        self._dots[o + i].set_label('1')
                    elif i in [8, 9]:
                        self._dots[o + i].set_label('2')
                    elif i in [5, 6, 7]:
                        self._dots[o + i].set_label('5')
                    else:
                        self._dots[o + i].set_label('20')
                self._dots[o - 1].set_label('60')
            else:  # custom
                for i in range(TEN + 1):
                    if i in [10]:
                        self._dots[o + i].set_label(str(self.custom[0]))
                    elif i in [8, 9]:
                        self._dots[o + i].set_label(str(self.custom[1]))
                    elif i in [5, 6, 7]:
                        self._dots[o + i].set_label(str(self.custom[2]))
                    else:
                        self._dots[o + i].set_label(str(self.custom[3]))
                self._dots[o - 1].set_label(str(self.custom[4]))

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
        elif self._mode == 'factor':
            if m in [10]:
                return 10 ** e
            elif m in [8, 9]:
                return (10 ** e) * 2
            elif m in [5, 6, 7]:
                return (10 ** e) * 3
            else:
                return (10 ** e) * 5
        elif self._mode == 'fibonacci':
            if m in [10]:
                return 60 ** e
            elif m in [8, 9]:
                return (60 ** e) * 2
            elif m in [5, 6, 7]:
                return (60 ** e) * 5
            else:
                return (60 ** e) * 20
        else:  # custom
            if m in [10]:
                return (self.custom[4] ** e) * self.custom[0]
            elif m in [8, 9]:
                return (self.custom[4] ** e) * self.custom[1]
            elif m in [5, 6, 7]:
                return (self.custom[4] ** e) * self.custom[2]
            else:
                return (self.custom[4] ** e) * self.custom[3]


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

    def __draw_cb(self, canvas, cr):
	self._sprites.redraw_sprites(cr=cr)

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
        Gtk.main_quit()

    def _new_dot(self, color):
        ''' generate a dot of a color color '''
        def darken(color):
            ''' return a darker color than color '''
            gdk_fill_color = Gdk.color_parse(self._fill)
            gdk_fill_dark_color = Gdk.Color(
                int(gdk_fill_color.red * 0.5),
                int(gdk_fill_color.green * 0.5),
                int(gdk_fill_color.blue * 0.5)).to_string()
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
	    Gdk.cairo_set_source_pixbuf(context, pixbuf, 0, 0)
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
        scale = (DOT_SIZE * self._scale) / 55.
        return '\
  <g transform="matrix(%f,0,0,%f,0,0)">\
  <path\
     d="m 35.798426,4.2187227 c -2.210658,0.9528967 -4.993612,-0.9110169 -7.221856,0 C 23.805784,6.1692574 20.658687,10.945585 17.543179,15.051507 13.020442,21.012013 7.910957,27.325787 6.7103942,34.711004 6.0558895,38.737163 6.434461,43.510925 8.917073,46.747431 c 3.604523,4.699107 15.24614,7.62307 16.048569,7.62307 0.802429,0 8.366957,0.46766 12.036427,-1.203642 2.841316,-1.294111 5.173945,-3.766846 6.820641,-6.419428 2.543728,-4.097563 3.563068,-9.062928 4.21275,-13.841891 C 49.107723,25.018147 48.401726,15.967648 47.433639,9.0332932 47.09109,6.5796321 43.508442,7.2266282 42.329009,5.7211058 41.256823,4.3524824 42.197481,1.860825 40.813604,0.80840168 40.384481,0.48205899 39.716131,0.42556727 39.208747,0.60779459 37.650593,1.1674066 37.318797,3.5633724 35.798426,4.2187227 z"\
     style="fill:none;fill-opacity:1;stroke:%s;stroke-width:3.0" />\
</g>' % (
            scale, scale, self._colors[1])

    def _gradient(self, r, cx, cy):
        scale = (DOT_SIZE * self._scale) / 55.
        return '\
  <defs>\
    <linearGradient\
       id="linearGradient3769">\
      <stop\
         id="stop3771"\
         style="stop-color:#ffff00;stop-opacity:1"\
         offset="0" />\
      <stop\
         id="stop3773"\
         style="stop-color:#ffff00;stop-opacity:0"\
         offset="1" />\
    </linearGradient>\
    <linearGradient\
       x1="10.761448"\
       y1="41.003559"\
       x2="56.70686"\
       y2="41.003559"\
       id="linearGradient2999"\
       xlink:href="#linearGradient3769"\
       gradientUnits="userSpaceOnUse"\
       gradientTransform="matrix(0.93094239,0,0,0.93094239,-3.9217825,-2.4013121)" />\
  </defs>\
  <g transform="matrix(%f,0,0,%f,0,0)">\
  <path\
     d="m 35.798426,4.2187227 c -2.210658,0.9528967 -4.993612,-0.9110169 -7.221856,0 C 23.805784,6.1692574 20.658687,10.945585 17.543179,15.051507 13.020442,21.012013 7.910957,27.325787 6.7103942,34.711004 6.0558895,38.737163 6.434461,43.510925 8.917073,46.747431 c 3.604523,4.699107 15.24614,7.62307 16.048569,7.62307 0.802429,0 8.366957,0.46766 12.036427,-1.203642 2.841316,-1.294111 5.173945,-3.766846 6.820641,-6.419428 2.543728,-4.097563 3.563068,-9.062928 4.21275,-13.841891 C 49.107723,25.018147 48.401726,15.967648 47.433639,9.0332932 47.09109,6.5796321 43.508442,7.2266282 42.329009,5.7211058 41.256823,4.3524824 42.197481,1.860825 40.813604,0.80840168 40.384481,0.48205899 39.716131,0.42556727 39.208747,0.60779459 37.650593,1.1674066 37.318797,3.5633724 35.798426,4.2187227 z"\
     style="fill:#fffec2;fill-opacity:1;stroke:#878600;stroke-width:2px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" />\
  <path\
     d="m 15.11608,18.808876 c 1.271657,-1.444003 4.153991,-3.145785 5.495465,-1.7664 2.950062,3.033434 -6.07961,8.17155 -4.219732,11.972265 0.545606,1.114961 2.322391,1.452799 3.532799,1.177599 5.458966,-1.241154 6.490591,-12.132334 12.070397,-11.677864 1.584527,0.129058 2.526156,2.269906 2.845867,3.827199 0.453143,2.207236 -1.962667,6.182399 -1.570133,6.574932 0.392533,0.392533 2.371401,0.909584 3.140266,0.196266 1.91857,-1.779962 -0.490667,-7.752531 0.09813,-7.850664 0.5888,-0.09813 4.421663,2.851694 5.789865,5.004799 0.583188,0.917747 -0.188581,2.956817 0.8832,3.140266 2.128963,0.364398 1.601562,-5.672021 3.729066,-5.299199 1.836829,0.321884 1.450925,3.532631 1.471999,5.397332 0.06743,5.965698 -0.565586,12.731224 -4.317865,17.369596 -3.846028,4.75426 -10.320976,8.31978 -16.388263,7.556266 C 22.030921,53.720741 16.615679,52.58734 11.485147,49.131043 7.9833717,46.771994 6.8028191,42.063042 6.5784815,37.846738 6.3607378,33.754359 8.3381535,29.765466 10.111281,26.070741 c 1.271951,-2.650408 2.940517,-4.917813 5.004799,-7.261865 z"\
     style="fill:url(#linearGradient2999);fill-opacity:1;stroke:none" />\
  <path\
     d="m 32.382709,4.7758124 c -0.123616,1.0811396 1.753928,2.8458658 2.728329,2.9439992 0.974405,0.098134 6.718874,0.7298319 9.159392,-0.1962668 0.820281,-0.3112699 0.968884,-0.9547989 0.974407,-1.4719993 0.02053,-1.9240971 0.03247,-4.7715376 -3.507853,-5.49546551 C 39.556079,0.11012647 37.217081,1.4131653 35.500801,2.2243463 34.054814,2.9077752 32.496703,3.7788369 32.382709,4.7758124 z"\
     style="fill:#b69556;fill-opacity:1;stroke:#b69556;stroke-width:1.31189477px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" /></g>' % (
            scale, scale)

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
    try:
        pl = GdkPixbuf.PixbufLoader.new_with_type('svg')
        pl.write(svg_string)
        pl.close()
        pixbuf = pl.get_pixbuf()
        return pixbuf
    except:
        print svg_string
        return None
