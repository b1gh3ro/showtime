import gi.repository

gi.require_version('Budgie', '1.0')
from gi.repository import Budgie, GObject, Gtk, Gio
import os
import clocktools as clt

"""
Budgie ShowTime
Author: Jacob Vlijm
Copyright © 2017-2018 Ubuntu Budgie Developers
Website=https://ubuntubudgie.org
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or any later version. This
program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU General Public License for more details. You
should have received a copy of the GNU General Public License along with this
program.  If not, see <http://www.gnu.org/licenses/>.
"""

css_data = """
.colorbutton {
  border-color: transparent;
  background-color: hexcolor;
  padding: 0px;
  border-width: 1px;
  border-radius: 4px;
}
.colorbutton:hover {
  border-color: hexcolor;
  background-color: hexcolor;
  padding: 0px;
  border-width: 1px;
  border-radius: 4px;
}
"""

colorpicker = os.path.join(clt.app_path, "colorpicker")
cpos_file = clt.pos_file


class BudgieShowTime(GObject.GObject, Budgie.Plugin):
    """ This is simply an entry point into your Budgie Applet implementation.
        Note you must always override Object, and implement Plugin.
    """

    # Good manners, make sure we have unique name in GObject type system
    __gtype_name__ = "BudgieShowTime"

    def __init__(self):
        """ Initialisation is important.
        """
        GObject.Object.__init__(self)

    def do_get_panel_widget(self, uuid):
        """ This is where the real fun happens. Return a new Budgie.Applet
            instance with the given UUID. The UUID is determined by the
            BudgiePanelManager, and is used for lifetime tracking.
        """
        return BudgieShowTimeApplet(uuid)


class BudgieShowTimeSettings(Gtk.Grid):
    def __init__(self, setting):

        super().__init__()
        self.setting = setting

        # files & colors
        self.tcolorfile = clt.timecolor
        self.dcolorfile = clt.datecolor
        self.mute_time = clt.mute_time
        self.mute_date = clt.mute_date
        self.twelvehrs = clt.twelve_hrs
        # grid & layout
        self.set_row_spacing(12)
        element_hsizer1 = self.h_spacer(13)
        self.attach(element_hsizer1, 0, 0, 1, 7)
        element_hsizer2 = self.h_spacer(25)
        self.attach(element_hsizer2, 2, 0, 1, 7)
        # time section
        self.runtime = Gtk.CheckButton("Show time")
        self.attach(self.runtime, 1, 1, 1, 1)
        self.twelve_hrs = Gtk.CheckButton("Twelve hours display")
        self.attach(self.twelve_hrs, 1, 2, 1, 1)
        # time color
        self.bholder1 = Gtk.Box()
        self.attach(self.bholder1, 1, 3, 1, 1)
        self.t_color = Gtk.Button()
        self.t_color.connect("clicked", self.pick_color, self.tcolorfile)
        self.t_color.set_size_request(10, 10)
        self.bholder1.pack_start(self.t_color, False, False, 0)
        timelabel = Gtk.Label(" Set time color")
        self.bholder1.pack_start(timelabel, False, False, 0)
        spacer1 = Gtk.Label("")
        self.attach(spacer1, 1, 4, 1, 1)
        # date section
        self.rundate = Gtk.CheckButton("Show date")
        self.attach(self.rundate, 1, 5, 1, 1)
        # date color
        self.bholder2 = Gtk.Box()
        self.attach(self.bholder2, 1, 6, 1, 1)
        self.d_color = Gtk.Button()
        self.d_color.connect("clicked", self.pick_color, self.dcolorfile)
        self.d_color.set_size_request(10, 10)
        self.bholder2.pack_start(self.d_color, False, False, 0)
        datelabel = Gtk.Label(" Set date color")
        self.bholder2.pack_start(datelabel, False, False, 0)
        spacer2 = Gtk.Label("")
        self.attach(spacer2, 1, 7, 1, 1)
        # position section
        # checkbox custom position
        self.setposbutton = Gtk.CheckButton("Set custom position (px)")
        self.attach(self.setposbutton, 1, 8, 1, 1)
        # position
        posholder = Gtk.Box()
        self.xpos = Gtk.Entry()
        self.xpos.set_width_chars(4)
        self.xpos_label = Gtk.Label("x: ")
        self.ypos = Gtk.Entry()
        self.ypos.set_width_chars(4)
        self.ypos_label = Gtk.Label(" y: ")
        self.apply = Gtk.Button("OK")
        for item in [
            self.xpos_label, self.xpos, self.ypos_label, self.ypos,
        ]:
            posholder.pack_start(item, False, False, 0)
        posholder.pack_end(self.apply, False, False, 0)
        self.attach(posholder, 1, 9, 1, 1)
        self.twelve_hrs.set_active(os.path.exists(self.twelvehrs))
        # set intial states
        timeshows = not os.path.exists(self.mute_time)
        dateshows = not os.path.exists(self.mute_date)
        self.runtime.set_active(timeshows)
        self.rundate.set_active(dateshows)
        self.set_timestate(timeshows)
        self.set_datestate(dateshows)
        self.runtime.connect("toggled", self.toggle_show, self.mute_time)
        self.rundate.connect("toggled", self.toggle_show, self.mute_date)
        self.twelve_hrs.connect("toggled", self.toggle_12, self.twelvehrs)
        # color buttons & labels
        distlabel = Gtk.Label("")
        self.attach(distlabel, 1, 10, 1, 1)
        noicon = Gtk.Label("Applet runs without a panel icon")
        self.attach(noicon, 1, 11, 1, 1)
        self.set_initialstate()
        self.setposbutton.connect("toggled", self.toggle_cuspos)
        self.apply.connect("clicked", self.get_xy)
        self.update_color()
        self.show_all()

    def set_timestate(self, val=None):
        val = val if val else not os.path.exists(self.mute_time)
        for item in [
            self.twelve_hrs, self.bholder1, self.t_color,
        ]:
            item.set_sensitive(val)

    def set_datestate(self, val=None):
        # could be included in set_timestate but, well...
        val = val if val else not os.path.exists(self.mute_date)
        for item in [self.bholder2, self.d_color]:
            item.set_sensitive(val)

    def set_initialstate(self):
        # set initial state of items in the custom position section
        state_data = clt.get_textposition()
        state = state_data[0]
        if state:
            self.xpos.set_text(str(state_data[1]))
            self.ypos.set_text(str(state_data[2]))
        for entr in [
            self.ypos, self.xpos, self.apply, self.xpos_label, self.ypos_label
        ]:
            entr.set_sensitive(state)
        self.setposbutton.set_active(state)

    def get_xy(self, button):
        x = self.xpos.get_text()
        y = self.ypos.get_text()
        # check for correct input
        try:
            newpos = [str(int(p)) for p in [x, y]]
            open(cpos_file, "wt").write("\n".join(newpos))
        except (FileNotFoundError, ValueError, IndexError):
            pass
        clt.restart_clock()

    def toggle_cuspos(self, button):
        newstate = button.get_active()
        for widget in [
            self.ypos, self.xpos, self.xpos_label, self.ypos_label, self.apply
        ]:
            widget.set_sensitive(newstate)
        if newstate is False:
            self.xpos.set_text("")
            self.ypos.set_text("")
            try:
                os.remove(cpos_file)
            except FileNotFoundError:
                pass
            else:
                clt.restart_clock()

    def h_spacer(self, addwidth):
        # horizontal spacer
        spacegrid = Gtk.Grid()
        if addwidth:
            label1 = Gtk.Label()
            label2 = Gtk.Label()
            spacegrid.attach(label1, 0, 0, 1, 1)
            spacegrid.attach(label2, 1, 0, 1, 1)
            spacegrid.set_column_spacing(addwidth)
        return spacegrid

    def toggle_12(self, button, file):
        # cannot be included in toggle_show, flipped boolean
        if not button.get_active():
            try:
                os.remove(file)
            except FileNotFoundError:
                pass
        else:
            open(file, "wt").write("")
        clt.restart_clock()

    def toggle_show(self, button, file):
        try:
            corr_file = [self.mute_time, self.mute_date].index(file)
        except ValueError:
            pass
        newstate = button.get_active()
        if newstate:
            try:
                os.remove(file)
            except FileNotFoundError:
                pass
        else:
            open(file, "wt").write("")
        try:
            if corr_file == 0:
                self.set_timestate()
            elif corr_file == 1:
                self.set_datestate()
        except UnboundLocalError:
            pass
        clt.restart_clock()

    def set_css(self, hexcol):
        provider = Gtk.CssProvider.new()
        provider.load_from_data(
            css_data.replace("hexcolor", hexcol).encode()
        )
        return provider

    def color_button(self, button, hexcol):
        provider = self.set_css(hexcol)
        color_cont = button.get_style_context()
        color_cont.add_class("colorbutton")
        Gtk.StyleContext.add_provider(
            color_cont,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def update_color(self, *args):
        self.tcolor = clt.hexcolor(clt.read_color(self.tcolorfile))
        self.dcolor = clt.hexcolor(clt.read_color(self.dcolorfile))
        self.color_button(self.d_color, self.dcolor)
        self.color_button(self.t_color, self.tcolor)

    def pick_color(self, button, f):
        wdata = clt.get(["wmctrl", "-l"])
        if "ShowTime - set color" not in wdata:
            subprocess = Gio.Subprocess.new([colorpicker, f], 0)
            subprocess.wait_check_async(None, self.update_color)
            self.update_color()


class BudgieShowTimeApplet(Budgie.Applet):
    """ Budgie.Applet is in fact a Gtk.Bin """

    def __init__(self, uuid):
        Budgie.Applet.__init__(self)
        self.uuid = uuid
        clt.restart_clock()

    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return BudgieShowTimeSettings(self.get_applet_settings(self.uuid))

    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise.
        """
        return True
