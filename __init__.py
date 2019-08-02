#!/usr/bin/env python

from collections import OrderedDict
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock


class Adaptive_GridLayout(GridLayout):
    """
    Adaptive height and row heights for grid layouts.

    Note this should not be used as a root layout and '_refresh_grids_y_dimension()' method should be used by
    children widgets that change height to update all attached instances of Adaptive_GridLayout (this layout).

    Copyright AGPL-3.0 2019 S0AndS0
    """

    def __init__(self, grow_cols = False, grow_rows = False, **kwargs):
        super(Adaptive_GridLayout, self).__init__(**kwargs)
        self.grow_cols = grow_cols
        self.grow_rows = grow_rows
        self.trigger_refresh_y_dimension = Clock.create_trigger(lambda _: self._refresh_grids_y_dimension(), 0)

    def _yield_tallest_of_each_row(self):
        """ Yields tallest child of each row within gridlayout. """
        current_tallest = None
        for i, c in enumerate(list(reversed(self.children))):
            if current_tallest is None:
                current_tallest = c

            if c.height > current_tallest.height:
                current_tallest = c

            ## Should work around grids without value for 'cols'
            if self.cols is None or self.cols is 0:
                yield current_tallest
                current_tallest = None
            ## Reached last item of current row... Fizzbuzz!
            elif ((i + 1) % self.cols == 0) is True:
                yield current_tallest
                current_tallest = None

    def _calc_child_padding_y(self, child):
        """ Returns total padding for a given child. """
        ## May be faster than asking permission with an if statement as most widgets seem to have padding
        try:
            child_padding = child.padding
        except AttributeError as e:
            child_padding = [0]

        len_child_padding = len(child_padding)
        if len_child_padding is 1:
            padding = child_padding[0] * 2
        elif len_child_padding is 2:
            padding = child_padding[1] * 2
        elif len_child_padding > 2:
            padding = child_padding[1] + child_padding[3]
        else:
            padding = 0

        return padding

    def _calc_min_height(self):
        """ Returns total height required to display tallest children of each row plus spacing between widgets. """
        min_height = 0
        for c in self._yield_tallest_of_each_row():
            min_height += c.height + self._calc_child_padding_y(child = c) + self.spacing[1]
        return min_height

    def _calc_rows_minimum(self):
        """ Returns ordered dictionary of how high each row should be to accommodate tallest children of each row. """
        rows_minimum = OrderedDict()
        for i, c in enumerate(self._yield_tallest_of_each_row()):
            rows_minimum.update({i: c.height + self._calc_child_padding_y(child = c)})
        return rows_minimum

    def _refresh_height(self):
        """ Resets 'self.height' using value returned by '_calc_min_height' method. """
        self.height = self._calc_min_height()

    def _refresh_rows_minimum(self):
        """ Resets 'self.rows_minimum' using value returned by '_calc_rows_minimum' method. """
        self.rows_minimum = self._calc_rows_minimum()

    def _refresh_grids_y_dimension(self):
        """ Updates 'height' and 'rows_minimum' first for spawn, then for self, and finally for any progenitors. """
        spawn = [x for x in self.walk(restrict = True) if hasattr(x, '_refresh_grids_y_dimension') and x is not self]
        for item in spawn:
            item._refresh_rows_minimum()
            item._refresh_height()

        self._refresh_rows_minimum()
        self._refresh_height()

        progenitors = [x for x in self.walk_reverse() if hasattr(x, '_refresh_grids_y_dimension') and x is not self]
        for progenitor in progenitors:
            progenitor._refresh_rows_minimum()
            progenitor._refresh_height()

    def on_children(self, instance, value):
        """ If 'grow_cols' or 'grow_rows' is True this will grow layout that way if needed instead of erroring out. """
        smax = self.get_max_widgets()
        widget_count = len(value)
        if smax and widget_count > smax:
            increase_by = widget_count - smax
            if self.grow_cols is True:
                self.cols += increase_by
            elif self.grow_rows is True:
                self.rows += increase_by
        super(Adaptive_GridLayout, self).on_children(instance, value)

    def on_parent(self, instance, value):
        """ Some adjustments maybe needed to get top row behaving on all platforms. """
        self.trigger_refresh_y_dimension()
