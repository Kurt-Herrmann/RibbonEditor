"""
Undo/Redo commands for RibbonEditor using Qt's QUndoCommand framework.
"""

import weakref
from PyQt6.QtGui import QUndoCommand, QColor, QPen, QBrush
from PyQt6.QtCore import Qt


class ToggleKnotColorCommand(QUndoCommand):
    """
    Undo command for toggling knot color visibility (left vs right thread).

    This command toggles the left_thread_vis property of a knot, which determines
    whether the knot displays the left or right thread color.
    """

    def __init__(self, ribbon, knot_co, old_left_thread_vis):
        super().__init__("Toggle Knot Color")
        self.ribbon_ref = weakref.ref(ribbon)
        self.knot_co = knot_co  # [x, y]
        self.old_left_thread_vis = old_left_thread_vis
        self.new_left_thread_vis = not old_left_thread_vis

    def undo(self):
        ribbon = self.ribbon_ref()
        if ribbon is None:
            return
        knot = ribbon.K[self.knot_co[0]][self.knot_co[1]]
        knot.left_thread_vis = self.old_left_thread_vis
        knot.set_knot_color()

    def redo(self):
        ribbon = self.ribbon_ref()
        if ribbon is None:
            return
        knot = ribbon.K[self.knot_co[0]][self.knot_co[1]]
        knot.left_thread_vis = self.new_left_thread_vis
        knot.set_knot_color()


class ChangeKnotTypeCommand(QUndoCommand):
    """
    Undo command for changing knot type (Normal <-> Reverse).

    This command toggles between Nk (Normal knot) and Rk (Reverse knot), which
    changes how threads flow through the knot. This affects all downstream knots
    along both thread paths.
    """

    def __init__(self, ribbon, knot_co):
        super().__init__("Change Knot Type")
        # Import here to avoid circular import
        from ribbon import Const

        self.ribbon_ref = weakref.ref(ribbon)
        self.knot_co = knot_co

        # Capture old state
        knot = ribbon.K[knot_co[0]][knot_co[1]]
        self.old_type = knot.type
        self.old_color_in_left = QColor(knot.color_in_left)  # Deep copy
        self.old_color_in_right = QColor(knot.color_in_right)  # Deep copy

        # New type is opposite of current
        self.new_type = Const.Rk if knot.type == Const.Nk else Const.Nk
        self.Const = Const  # Store for use in undo/redo

    def undo(self):
        ribbon = self.ribbon_ref()
        if ribbon is None:
            return

        knot = ribbon.K[self.knot_co[0]][self.knot_co[1]]
        knot.type = self.old_type
        knot.color_in_left = QColor(self.old_color_in_left)
        knot.color_in_right = QColor(self.old_color_in_right)

        # Recalculate thread propagation
        knot.set_thread(self.old_color_in_right, self.Const.RightIn, ribbon.thW)
        knot.set_thread(self.old_color_in_left, self.Const.LeftIn, ribbon.thW)

    def redo(self):
        ribbon = self.ribbon_ref()
        if ribbon is None:
            return

        knot = ribbon.K[self.knot_co[0]][self.knot_co[1]]
        knot.type = self.new_type

        # Recalculate thread propagation with new type
        # color_in values are already set from previous state or initialization
        knot.set_thread(knot.color_in_right, self.Const.RightIn, ribbon.thW)
        knot.set_thread(knot.color_in_left, self.Const.LeftIn, ribbon.thW)


class ChangeThreadColorCommand(QUndoCommand):
    """
    Undo command for changing thread color from the color bar.

    This command changes the color of an entire thread by updating the start knot
    color and propagating the change through all knots in the thread path.
    """

    def __init__(self, ribbon, thread_index, old_color, new_color):
        super().__init__("Change Thread Color")
        self.ribbon_ref = weakref.ref(ribbon)
        self.thread_index = thread_index
        self.old_color = QColor(old_color)  # Deep copy
        self.new_color = QColor(new_color)  # Deep copy

    def _apply_color(self, color):
        """Apply color to the thread and update all visual elements"""
        ribbon = self.ribbon_ref()
        if ribbon is None:
            return

        # Update StartKnot_list color
        CS = ribbon.StartKnot_list[self.thread_index]
        CS.color = QColor(color)  # Deep copy

        # Update the ColorRect brush
        # Find the ColorRect in the scene
        scene = ribbon.scene
        for item in scene.items():
            # Import here to avoid circular import
            from ribbon import ColorRect
            if isinstance(item, ColorRect) and hasattr(item, 'index') and item.index == self.thread_index:
                item.setBrush(QBrush(color))
                break

        # Update the line pen
        pen = QPen()
        pen.setColor(color)
        pen.setWidth(ribbon.thW)
        CS.line.setPen(pen)

        # Recalculate thread propagation
        Kh = CS.Knot
        direction = CS.direction
        Kh.set_thread(color, direction, ribbon.thW)

    def undo(self):
        self._apply_color(self.old_color)

    def redo(self):
        self._apply_color(self.new_color)
