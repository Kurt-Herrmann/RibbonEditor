import math
from enum import Enum, auto

from PyQt6.QtCore import QRectF, QTimer, Qt
from PyQt6.QtGui import QColor, QPen, QBrush, QPainterPath
from PyQt6.QtWidgets import (QColorDialog, QGraphicsLineItem, QGraphicsPathItem,
                             QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsSimpleTextItem)


class Ribbon():

    def __init__(self, scene, width, length, type):
        self.scene = scene
        # ✅ Attach this Ribbon instance to the scene
        if scene is not None:
            setattr(scene, "ribbon", self)
            # print("✅ Ribbon registered to scene as 'scene.ribbon'")
        # store w and l as class variables
        self.w = width
        self.l = length
        self.type = type
        self.StartKnot_list = []
        self.Kd = 40  # knot diameter
        self.Rd = self.Kd * 0.9
        self.Vd = 35  # factor to define horizontal and vertical distance, 1 . touching quads
        self.Ec = 0.5 * self.Kd  # edge clearance ribbon
        self.cBh = 1.4  # horizontal spacing factor for colour bar
        self.cBv = 3  # vertical spacing factor for color bar
        self.cBx = 0  # horizontal offset ribbon to color bar
        self.f_y = 2  # vertical offset color bar to ribbon
        self.f_x = 1  # horizontal offset of color bar rectangles for 2 thread knots
        self.dis_left = Vector(-self.f_x * self.Vd, -self.f_y * self.Vd)  # x displacement to the left
        self.dis_none = Vector(0, -self.f_y * self.Vd)  # no x displacement
        self.dis_right = Vector(self.f_x * self.Vd, -self.f_y * self.Vd)  # x displacement to the right
        self.cBy = 0  # vertical offset ribbon to color bar cBm = (cBh * self.Vd * (self.w + 1) + self.Kd) / 2
        self.cplW = 0  # complete width
        self.cplL = 0  # complete length
        self.thW = self.Kd // 6
        if self.thW == 0:
            self.thW = 1
        self.thW = int(self.thW)
        self.color = my_Colors()

        # generate relative knot point coordinates
        self.KnPnts = KnotPoints(self.Kd, self.Vd)
        self.make_empty_ribbon()
        x = 0
        for y in range(self.l):
            self.K[x][y].edgeKL = True  # edge knot left
        x = self.w - 1
        for y in range(self.l):
            self.K[x][y].edgeKR = True  # edge knot right

        cBm = (self.cBh * self.Vd * (self.w + 1) + self.Kd) / 2
        self.cBx = (self.w * self.Vd * (self.cBh - 1) + self.Rd + self.Vd - self.Kd) / 2

        # calculate a fitted distance to give a nice arrangement for
        # broad ribbons
        self.cBv = 0.5 * self.w
        self.cBy = self.cBv * self.Vd

        # define different ribbon types
        match type:
            case "L":
                self.set_type_L()
            case "R":
                self.set_type_R()
            case "M":
                self.set_type_M()
            case "A":
                self.set_type_A()
            case _:
                print("Type Error !")
                exit()

        self.draw_color_bar(type)
        # print("**** Draw color bar completed !")
        for i in range(width + 1):
            CS = self.StartKnot_list[i]
            color = CS.color
            Kh = CS.Knot
            direction = CS.direction
            color_name = self.color.print_color_key(color)
            # print(f"Thread {i} color {color_name} 1st pass direction {direction}")
            help = Kh.set_thread(color, direction, self.thW)
        # run it 2 times to make sure all in colors are set.
        for i in range(width + 1):
            CS = self.StartKnot_list[i]
            color = CS.color
            Kh = CS.Knot
            direction = CS.direction
            color_name = self.color.print_color_key(color)
            # print(f"Thread {i} color {color_name} 1st pass direction {direction}")
            help = Kh.set_thread(color, direction, self.thW)
        # print("Setup completed !")
        self.row_labels()

    def set_type_L(self):
        self.make_knot_links(True, 0, self.w)
        self.set_visible(0, self.w, Const.LeftThrdVis)

        # set end knot types and next knot in one direction
        self.set_end_knots(True, 0, self.w - 1)

        for y in range(self.l):
            for x in range(self.w):
                self.K[x][y].gco.x = self.cBx + self.Ec + self.Vd * x
                self.K[x][y].gco.y = self.cBy + self.Ec + self.Vd * (x + 2 * y)
                # print(f"normal, x {x} y {y}  strtK {self.K[x][y].strtK} endK {self.K[x][y].endK}, "
                #       f"type {self.K[x][y].type} eKL {self.K[x][y].edgeKL} eKR {self.K[x][y].edgeKR} "
                #       f"gco.x {self.K[x][y].gco.x:.0f} gco.y {self.K[x][y].gco.y:.0f}")
                color = QColor("black")
                self.K[x][y].draw_graphic_items(color, self.thW, self.Kd, self.scene)

        self.cplW = self.w * self.cBh * self.Vd + self.Rd + 2 * self.Ec
        self.cplL = (self.w - 1) * self.Vd + (self.l - 1) * 2 * self.Vd + 2 * self.Kd + self.cBy
        outline = QGraphicsRectItem(0, 0, self.cplW, self.cplL)
        self.scene.addItem(outline)

    def set_type_R(self):
        self.make_knot_links(False, 0, self.w)
        self.set_visible(0, self.w, Const.RightThrdVis)

        # set end knot types and next knot in one direction
        self.set_end_knots(False, 1, self.w)

        for y in range(self.l):
            for x in range(self.w):
                self.K[x][y].gco.x = self.cBx + self.Ec + self.Vd * x
                self.K[x][y].gco.y = self.cBy + self.Ec + self.Vd * (self.w - 1 - x + 2 * y)
                # print(f"normal, x {x} y {y}  strtK {self.K[x][y].strtK} endK {self.K[x][y].endK}, "
                #       f"type {self.K[x][y].type} eKL {self.K[x][y].edgeKL} eKR {self.K[x][y].edgeKR} "
                #       f"gco.x {self.K[x][y].gco.x:.0f} gco.y {self.K[x][y].gco.y:.0f}")
                color = QColor("black")
                self.K[x][y].draw_graphic_items(color, self.thW, self.Kd, self.scene)

        self.cplW = self.w * self.cBh * self.Vd + self.Rd + 2 * self.Ec
        self.cplL = (self.w - 1) * self.Vd + (self.l - 1) * 2 * self.Vd + 2 * self.Kd + self.cBy
        outline = QGraphicsRectItem(0, 0, self.cplW, self.cplL)
        self.scene.addItem(outline)

    def set_type_M(self):

        mid = self.w // 2

        self.make_knot_links(True, 0, mid)
        self.make_knot_links(False, mid + 1, self.w)
        self.set_type(mid, Const.Rk)
        self.set_visible(mid + 1, self.w, Const.RightThrdVis)
        self.fix_middle_knot_links("M", mid)

        # set end knot types and next knot in one direction
        self.set_end_knots(True, 0, mid)
        self.set_end_knots(False, mid + 1, self.w)

        # normal direction
        for y in range(self.l):
            for x in range(self.w // 2 + 1):
                self.K[x][y].gco.x = self.cBx + self.Ec + self.Vd * x
                self.K[x][y].gco.y = self.cBy + self.Ec + self.Vd * (x + 2 * y)
                # print(f"normal, x {x} y {y}  strtK {self.K[x][y].strtK} endK {self.K[x][y].endK}, "
                #       f"type {self.K[x][y].type} eKL {self.K[x][y].edgeKL} eKR {self.K[x][y].edgeKR} "
                #       f"gco.x {self.K[x][y].gco.x:.0f} gco.y {self.K[x][y].gco.y:.0f}")
                color = QColor("black")
                self.K[x][y].draw_graphic_items(color, self.thW, self.Kd, self.scene)

        # reverse direction
        for y in range(self.l):
            for x in range(self.w // 2 + 1, self.w):
                self.K[x][y].gco.x = self.cBx + self.Ec + self.Vd * x
                self.K[x][y].gco.y = self.cBy + self.Ec + self.Vd * (self.w - 1 - x + 2 * y)
                # print(f"normal, x {x} y {y}  strtK {self.K[x][y].strtK} endK {self.K[x][y].endK}, "
                #       f"type {self.K[x][y].type} eKL {self.K[x][y].edgeKL} eKR {self.K[x][y].edgeKR} "
                #       f"gco.x {self.K[x][y].gco.x:.0f} gco.y {self.K[x][y].gco.y:.0f}")
                color = QColor("black")
                self.K[x][y].draw_graphic_items(color, self.thW, self.Kd, self.scene)

        self.cplW = self.w * self.cBh * self.Vd + self.Rd + 2 * self.Ec
        self.cplL = (self.w - 1) / 2 * self.Vd + (self.l - 1) * 2 * self.Vd + 2 * self.Kd + self.cBy
        outline = QGraphicsRectItem(0, 0, self.cplW, self.cplL)
        self.scene.addItem(outline)

    def set_type_A(self):

        mid = self.w // 2

        self.make_knot_links(False, 0, mid)
        self.make_knot_links(True, mid + 1, self.w)
        self.set_type(mid, Const.Rk)
        self.set_visible(0, mid, Const.RightThrdVis)
        self.fix_middle_knot_links("A", mid)

        # set end knot types and next knot in one direction
        self.set_end_knots(False, 1, mid + 1)
        self.set_end_knots(True, mid, self.w - 1)
        self.K[mid][self.l - 1].endKtype = Const.EndKBoth

        # normal direction
        for y in range(self.l):
            for x in range(mid, self.w):
                self.K[x][y].gco.x = self.cBx + self.Ec + self.Vd * x
                self.K[x][y].gco.y = self.cBy + self.Ec + self.Vd * (x + 2 * y)
                # print(f"normal, x {x} y {y}  strtK {self.K[x][y].strtK} endK {self.K[x][y].endK}, "
                #       f"type {self.K[x][y].type} eKL {self.K[x][y].edgeKL} eKR {self.K[x][y].edgeKR} "
                #       f"gco.x {self.K[x][y].gco.x:.0f} gco.y {self.K[x][y].gco.y:.0f}")
                color = QColor("black")
                self.K[x][y].draw_graphic_items(color, self.thW, self.Kd, self.scene)

        # reverse direction
        for y in range(self.l):
            for x in range(mid):
                self.K[x][y].gco.x = self.cBx + self.Ec + self.Vd * x
                self.K[x][y].gco.y = self.cBy + self.Ec + self.Vd * (self.w - 1 - x + 2 * y)
                # print(f"normal, x {x} y {y}  strtK {self.K[x][y].strtK} endK {self.K[x][y].endK}, "
                #       f"type {self.K[x][y].type} eKL {self.K[x][y].edgeKL} eKR {self.K[x][y].edgeKR} "
                #       f"gco.x {self.K[x][y].gco.x:.0f} gco.y {self.K[x][y].gco.y:.0f}")
                color = QColor("black")
                self.K[x][y].draw_graphic_items(color, self.thW, self.Kd, self.scene)

        self.cplW = self.w * self.cBh * self.Vd + self.Rd + 2 * self.Ec
        self.cplL = (self.w - 1) * self.Vd + (self.l - 1) * 2 * self.Vd + 2 * self.Kd + self.cBy
        outline = QGraphicsRectItem(0, 0, self.cplW, self.cplL)
        self.scene.addItem(outline)

    def make_empty_ribbon(self):
        self.K = [[Knot(self.scene, self.KnPnts) for _ in range(self.l)] for _ in range(self.w)]

        # only for debug ?
        for y in range(self.l):  # y .. index to the rows
            for x in range(self.w):  # x .. index inside each row
                self.K[x][y].co[0] = x
                self.K[x][y].co[1] = y
                # print(f"x {x}, y {y}, type {self.K[x][y].type} "
                #       f"co[0] {self.K[x][y].co[0]} co[1] {self.K[x][y].co[1]}") # for debug

        # set start and end knots
        y = 0
        for x in range(self.w):
            self.K[x][y].strtK = True  # start knot
        y = self.l - 1
        for x in range(self.w):
            self.K[x][y].endK = True  # end knot

    def make_knot_links(self, normal, start, stop):
        # at init all knot are type Nk
        for y in range(self.l):  # y .. index to the rows
            for x in range(start, stop):  # x .. index to columns
                if not self.K[x][y].endK:
                    if normal:
                        nKtoR = Knot(self.scene, self.KnPnts)
                        nKtoL = Knot(self.scene, self.KnPnts)
                        if self.K[x][y].edgeKL:
                            nKtoR = self.K[x + 1][y]
                            nKtoL = self.K[x][y + 1]
                            # print(f"Knot ; x {x} ; y {y} ; edgeKL ; "
                            #       f"nKtoR: ; x {x+1} ; y {y} ; "
                            #       f"nKtoL ; x {x} ; y {y+1} ")
                        elif self.K[x][y].edgeKR:
                            nKtoR = self.K[x][y + 1]
                            nKtoL = self.K[x - 1][y + 1]
                            # print(f"Knot ; x {x} ; y {y} ; edgeKR ; "
                            #       f"nKtoR: ; x {x} ; y {y +1} ; "
                            #       f"nKtoL ; x {x-1} ; y {y+1} ")
                        else:
                            nKtoR = self.K[x + 1][y]
                            nKtoL = self.K[x - 1][y + 1]
                            # print(f"Knot ; x {x} ; y {y} ; inner knot ; "
                            #       f"nKtoR: ; x {x+1} y {y} ; "
                            #       f"nKtoL ; x {x-1} y {y+1} ")
                    else:  # reverse
                        nKtoR = Knot(self.scene, self.KnPnts)
                        nKtoL = Knot(self.scene, self.KnPnts)
                        if self.K[x][y].edgeKL:
                            nKtoR = self.K[x + 1][y + 1]
                            nKtoL = self.K[x][y + 1]
                            # print(f"Knot ; x {x} ; y {y} ; edgeKL ; "
                            #       f"nKtoR: ; x {x+1} ; y {y} ; "
                            #       f"nKtoL ; x {x} ; y {y+1} ")
                        elif self.K[x][y].edgeKR:
                            nKtoR = self.K[x][y + 1]
                            nKtoL = self.K[x - 1][y]
                            # print(f"Knot ; x {x} ; y {y} ; edgeKR ; "
                            #       f"nKtoR: ; x {x+1} ; y {y} ; "
                            #       f"nKtoL ; x {x-1} ; y {y} ")
                        else:
                            nKtoR = self.K[x + 1][y + 1]
                            nKtoL = self.K[x - 1][y]
                            # print(f"Knot ; x {x} ; y {y} ; inner knot ; "
                            #       f"nKtoR: ; x {x+1} y {y} ; "
                            #       f"nKtoL ; x {x-1} y {y} ")

                    self.K[x][y].nKtoR = nKtoR
                    self.K[x][y].nKtoL = nKtoL
                    # print(f"Knot cox {self.K[x][y].co[0]} coy {self.K[x][y].co[1]} ; "
                    #       f"nKtoR: cox {self.K[x][y].nKtoR.co[0]} coy {self.K[x][y].nKtoR.co[1]} ; "
                    #       f"nKtoL: cox {self.K[x][y].nKtoL.co[0]} coy {self.K[x][y].nKtoL.co[1]}")

    def fix_middle_knot_links(self, type, column):
        x = column
        for y in range(self.l):
            # print(f" Knot x ; {self.K[x][y].co[0]} ; {self.K[x][y].co[1]}")
            if not self.K[x][y].endK:
                nKtoR = Knot(self.scene, self.KnPnts)
                nKtoL = Knot(self.scene, self.KnPnts)
                if self.type == "M":
                    nKtoR = self.K[x + 1][y + 1]
                    nKtoL = self.K[x - 1][y + 1]
                elif self.type == "A":
                    nKtoR = self.K[x + 1][y]
                    nKtoL = self.K[x - 1][y]
                else:
                    print("No such type !")

                self.K[x][y].nKtoR = nKtoR
                self.K[x][y].nKtoL = nKtoL
                # print(f" nKtoR  { self.K[x][y].nKtoR.co[0]} ; {self.K[x][y].nKtoR.co[1]} ; "
                #   f"nKtoL {self.K[x][y].nKtoL.co[0]} ;  {self.K[x][y].nKtoL.co[1]}")

    def set_end_knots(self, normal, start, stop):
        y = self.l - 1
        for x in range(start, stop):
            if normal and not self.K[x][y].edgeKR:
                # print(f" Knot x ; {self.K[x][y].co[0]} ; {self.K[x][y].co[1]}")
                self.K[x][y].endKtype = Const.EndKRuLd
                nKtoR = Knot(self.scene, self.KnPnts)
                nKtoR = self.K[x + 1][y]
                self.K[x][y].nKtoR = nKtoR
            else:
                # print(f" Knot x ; {self.K[x][y].co[0]} ; {self.K[x][y].co[1]}")
                self.K[x][y].endKtype = Const.EndKLuRd
                nKtoL = Knot(self.scene, self.KnPnts)
                nKtoL = self.K[x - 1][y]
                self.K[x][y].nKtoL = nKtoL

    def toggle_type(self, column):
        # toggle between NK and Rk
        x = column
        for y in range(self.l):
            if self.K[x][y].type == Const.Nk:
                self.K[x][y].type = Const.Rk
            else:
                self.K[x][y].type = Const.Nk

    def set_type(self, column, type):
        # toggle between NK and Rk
        x = column
        for y in range(self.l):
            self.K[x][y].type = type

    def set_visible(self, start, stop, const):
        for y in range(self.l):
            for x in range(start, stop):
                if const == Const.LeftThrdVis:
                    self.K[x][y].left_thread_vis = True
                elif const == Const.RightThrdVis:
                    self.K[x][y].left_thread_vis = False
                else:
                    print("Error")

    def draw_color_bar(self, type):
        # preset available start colors
        black = QColor("black")
        red = QColor.fromRgb(255, 99, 71)
        green = QColor.fromRgb(0, 255, 0)
        blue = QColor.fromRgb(0, 191, 255)
        grey = QColor("lightgrey")
        darkgrey = QColor("darkgrey")
        cyan = QColor("cyan")
        magenta = QColor.fromRgb(238, 130, 238)
        yellow = QColor("yellow")
        f = [red, green, blue, black, cyan, magenta, yellow, darkgrey]
        colors = []

        outline = black
        penO = QPen()
        penO.setWidth(1)
        penO.setColor(outline)

        if type == "L" or type == "R":
            j = 0
            for i in range(self.w + 1):
                color_name = self.color.print_color_key(f[j % 8])
                # print(f"i {i} j {j} color {color_name}")
                colors.append(f[j % 8])
                j += 1
        else:  # type M or A
            mid = self.w // 2
            j = 0
            for i in range(0, mid + 1):
                color_name = self.color.print_color_key(f[j % 8])
                # print(f"i {i} j {j} color {color_name}")
                colors.append(f[j % 8])
                j += 1
            j = mid
            for i in range(self.w + 1, mid + 1, -1):
                color_name = self.color.print_color_key(f[j % 8])
                # print(f"i {i} j {j} color {color_name}")
                colors.append(f[j % 8])
                j -= 1

        offset = 0  # offset of ColorSelect rectangles
        for i in range(self.w + 1):
            # rotate start colors
            fill = colors[i]

            # draw color bar rectangles
            ref = Vector(offset, 0)
            CB_start = Vector(self.Ec, self.Ec)
            ref1 = ref + CB_start
            rect = ColorRect(ref1.x, ref1.y, self.Rd, self.Rd, i)
            rect.setPen(penO)
            rect.setBrush(fill)
            hK = self.get_start_knot(i, fill)
            # nextKnot = hK[0]  # Knot
            # direction = hK[1]  # input direction to knot
            nextKnot=hK["Knot"]
            direction =hK["Direction"]
            # print(f"x {nextKnot.co[0]} y {nextKnot.co[1]} gco.x {nextKnot.gco.x:.0f} gco.y {nextKnot.gco.y:.0f}")
            cRect = Vector()
            cRect = self.center(rect)
            cCircle = Vector()
            cCircle = self.center(nextKnot.circle)
            line = QGraphicsLineItem(cRect.x, cRect.y, cCircle.x, cCircle.y)
            penL = QPen()
            penL.setColor(fill)
            penL.setWidth(self.thW)
            line.setPen(penL)
            self.scene.addItem(line)
            StKnot = self.KnotList(self.scene, self.KnPnts)  # save start knot
            StKnot.color = fill  # thread color
            StKnot.Knot = hK["Knot"]  # start knot
            StKnot.direction = hK["Direction"]  # start input direction
            StKnot.line = line
            self.StartKnot_list.append(StKnot)
            offset += self.Vd * self.cBh
            self.scene.addItem(rect)

    # def draw_color_bar(self, type):
    #     # preset available start colors
    #     black = QColor("black")
    #     red = QColor.fromRgb(255, 99, 71)
    #     green = QColor.fromRgb(0, 255, 0)
    #     blue = QColor.fromRgb(0, 191, 255)
    #     grey = QColor("lightgrey")
    #     darkgrey = QColor("darkgrey")
    #     cyan = QColor("cyan")
    #     magenta = QColor.fromRgb(238, 130, 238)
    #     yellow = QColor("yellow")
    #     f = [red, green, blue, black, cyan, magenta, yellow, darkgrey]
    #     colors = []
    #
    #     outline = black
    #     penO = QPen()
    #     penO.setWidth(1)
    #     penO.setColor(outline)
    #
    #     if type == "L" or type == "R":
    #         j = 0
    #         for i in range(self.w + 1):
    #             color_name = self.color.print_color_key(f[j % 8])
    #             # print(f"i {i} j {j} color {color_name}")
    #             colors.append(f[j % 8])
    #             j += 1
    #     else:  # type M or A
    #         mid = self.w // 2
    #         j = 0
    #         for i in range(0, mid + 1):
    #             color_name = self.color.print_color_key(f[j % 8])
    #             # print(f"i {i} j {j} color {color_name}")
    #             colors.append(f[j % 8])
    #             j += 1
    #         j = mid
    #         for i in range(self.w + 1, mid + 1, -1):
    #             color_name = self.color.print_color_key(f[j % 8])
    #             # print(f"i {i} j {j} color {color_name}")
    #             colors.append(f[j % 8])
    #             j -= 1
    #
    #     offset = 0  # offset of ColorSelect rectangles
    #     for i in range(self.w + 1):
    #         # rotate start colors
    #         fill = colors[i]
    #         # draw color bar rectangles
    #         ref = Vector(offset, 0)
    #         CB_start = Vector(self.Ec, self.Ec)
    #         ref1 = ref + CB_start
    #         rect = ColorRect(ref1.x, ref1.y, self.Rd, self.Rd, i)
    #         # rect = QGraphicsRectItem(ref1.x, ref1.y, self.Rd, self.Rd)
    #         rect.setPen(penO)
    #         rect.setBrush(fill)
    #         hK = self.get_start_knot(i, fill)
    #         nextKnot = hK[0]  # Knot
    #         direction = hK[1]  # input direction to knot
    #         # print(f"x {nextKnot.co[0]} y {nextKnot.co[1]} gco.x {nextKnot.gco.x:.0f} gco.y {nextKnot.gco.y:.0f}")
    #         cRect = Vector()
    #         cRect = self.center(rect)
    #         cCircle = Vector()
    #         cCircle = self.center(nextKnot.circle)
    #         line = QGraphicsLineItem(cRect.x, cRect.y, cCircle.x, cCircle.y)
    #         penL = QPen()
    #         penL.setColor(fill)
    #         penL.setWidth(self.thW)
    #         line.setPen(penL)
    #         self.scene.addItem(line)
    #         StKnot = self.KnotList(self.scene, self.KnPnts)  # save start knot
    #         StKnot.color = fill  # thread color
    #         StKnot.Knot = hK[0]  # start knot
    #         StKnot.direction = hK[1]  # start input direction
    #         StKnot.line = line
    #         self.StartKnot_list.append(StKnot)
    #         offset += self.Vd * self.cBh
    #         self.scene.addItem(rect)

    def get_start_knot(self, i, fill):
        nextKnot = Knot(self.scene, self.KnPnts)
        colorRect = QGraphicsRectItem
        hK = {"Knot": nextKnot, "Direction": Const.LeftIn, "Rect": ColorRect}
        ref=Vector()
        # hK = [Knot(self.scene, self.KnPnts), Const.LeftIn]  # help Knot and input direction
        match self.type:
            case "L":
                if i == 0:
                    hK["Knot"] = self.K[0][0]
                    hK["Direction"] = Const.LeftIn
                    self.K[0][0].color_in_left = fill
                    ref = self.K[0][0].gco + self.dis_left
                    hK["Rect"]=QGraphicsRectItem(ref.x,ref.y,self.Rd,self.Rd)
                    # hK = [self.K[0][0], Const.LeftIn]  # left input
                    # hK[0].color_in_left = fill
                # k stays same, as knot has two inputs threads
                elif i == 1:
                    hK["Knot"] = self.K[0][0]
                    hK["Direction"] = Const.RightIn
                    self.K[0][0].color_in_right = fill
                    ref = self.K[0][0].gco + self.dis_none
                    hK["Rect"]=QGraphicsRectItem(ref.x,ref.y,self.Rd,self.Rd)
                    # hK = [self.K[0][0], Const.RightIn]  # right input
                    # hK[0].color_in_right = fill
                else:
                    hK["Knot"] = self.K[0][0]
                    hK["Direction"] = Const.RightIn
                    self.K[i - 1][0].color_in_left = fill
                    ref = self.K[0][0].gco + self.dis_none
                    hK["Rect"]=QGraphicsRectItem(ref.x,ref.y,self.Rd,self.Rd)
                    # hK = [self.K[i - 1][0], Const.RightIn]  # right input
                    # hK[0].color_in_left = fill
                return (hK)
            case "R":
                if i < self.w - 1:
                    hK["Knot"] = self.K[i][0]
                    hK["Direction"] = Const.LeftIn
                    self.K[i][0].color_in_left = fill
                    # hK = [self.K[i][0], Const.LeftIn]  # left input
                    # hK[0].color_in_left = fill
                elif i == self.w - 1:
                    hK["Knot"] = self.K[self.w - 1][0]
                    hK["Direction"] = Const.LeftIn
                    self.K[self.w - 1][0].color_in_left = fill
                    # hK = [self.K[self.w - 1][0], Const.LeftIn]  # left input
                    # hK[0].color_in_left = fill
                    # k stays same, as knot has two inputs threads
                elif i == self.w:
                    hK["Knot"] = self.K[self.w - 1][0]
                    hK["Direction"] = Const.RightIn
                    self.K[self.w - 1][0].color_in_right = fill
                    # hK = [self.K[self.w - 1][0], Const.RightIn]  # right input
                    # hK[0].color_in_right = fill
                return (hK)
            case "M":
                mid = int((self.w - 1) // 2)
                # print(f"i {i}")
                if i == 0:
                    hK["Knot"] = self.K[0][0]
                    hK["Direction"] = Const.LeftIn
                    self.K[0][0].color_in_left = fill
                    # hK = [self.K[0][0], Const.LeftIn]  # left input
                    # hK[0].color_in_left = fill
                elif i == 1:
                    hK["Knot"] = self.K[0][0]
                    hK["Direction"] = Const.RightIn
                    self.K[0][0].color_in_right = fill
                    # hK = [self.K[0][0], Const.RightIn]  # right input
                    # hK[0].color_in_right = fill
                elif i <= mid:
                    hK["Knot"] = self.K[i - 1][0]
                    hK["Direction"] = Const.RightIn
                    self.K[i -1][0].color_in_right = fill
                    # hK = [self.K[i - 1][0], Const.RightIn]  # right input
                    # hK[0].color_in_right = fill
                elif i < self.w - 1:
                    hK["Knot"] = self.K[i][0]
                    hK["Direction"] = Const.LeftIn
                    self.K[i][0].color_in_left = fill
                    # hK = [self.K[i][0], Const.LeftIn]  # left input
                    # hK[0].color_in_left = fill
                elif i == self.w - 1:
                    hK["Knot"] = self.K[self.w-1][0]
                    hK["Direction"] = Const.LeftIn
                    self.K[self.w-1][0].color_in_left = fill
                    # hK = [self.K[self.w - 1][0], Const.LeftIn]  # left input
                    # hK[0].color_in_left = fill
                elif i == self.w:
                    hK["Knot"] = self.K[self.w - 1][0]
                    hK["Direction"] = Const.RightIn
                    self.K[self.w - 1][0].color_in_right = fill
                    # hK = [self.K[self.w - 1][0], Const.RightIn]  # right input
                    # hK[0].color_in_right = fill
                return (hK)
            case "A":
                mid = int((self.w - 1) // 2)
                # print(f"mid {mid} i {i}")
                if i < mid + 1:
                    hK["Knot"] = self.K[i][0]
                    hK["Direction"] = Const.LeftIn
                    self.K[i][0].color_in_left = fill
                    # hK = [self.K[i][0], Const.LeftIn]  # left input
                    # hK[0].color_in_left = fill
                elif i < self.w + 1:
                    hK["Knot"] = self.K[i - 1][0]
                    hK["Direction"] = Const.RightIn
                    self.K[i - 1][0].color_in_right = fill
                    # hK = [self.K[i - 1][0], Const.RightIn]  # right input
                    # hK[0].color_in_right = fill
                return (hK)

    def set_thread_color(self, CS):
        # CS color select
        color = QColor()
        color = CS.color
        pen = QPen()
        pen.setColor(color)
        pen.setWidth(self.thW)
        CS.line.setPen(pen)
        CS.line.update()
        knot = CS.nextKnot
        if knot.type == "const.Nk":  # normal knot
            if CS.left_in:
                knot.color_in_left = color
                knot.line_out_right.setPen(pen)
                knot.line_out_right(update)
            else:
                knot.color_in_right = color
                knot.line_out_left.setPen(pen)
                knot.line_out_left(update)
        else:  # reverse knot
            if CS.left_in:
                knot.color_in_left = color
                knot.line_out_left.setPen(pen)
                knot.line_out_left(update)
            else:
                knot.color_in_right = color
                knot.line_out_right.setPen(pen)
                knot.line_out_right(update)

    def center(self, item):
        # calculate center of rectangle or circle
        center = Vector()
        rh = item.rect()
        x = rh.x()
        y = rh.y()
        h = rh.height()
        w = rh.width()
        center.x = x + w / 2
        center.y = y + h / 2
        return (center)

    def extract_KnPar(self):
        All_KnPar = []
        for x in range(self.w):
            column = []
            for y in range(self.l):
                KnPar = {
                    "co": self.K[x][y].co,
                    "left_thread_vis": self.K[x][y].left_thread_vis,
                    "type": self.K[x][y].type,
                    "endK": self.K[x][y].endK
                }
                column.append(KnPar)
            All_KnPar.append(column)
        return All_KnPar

    def row_labels(self):
        for i in range(self.l):
            x = 0
            label_pos = Vector()
            displacement = Vector()
            if i < 10:
                displacement.x = -self.Vd * 0.55
            elif i < 100:
                displacement.x = -self.Vd * 0.9
            else:
                displacement.x = -self.Vd * 1.225
            # displacement.y = -self.Vd
            label_pos = self.K[0][i].gco + displacement
            label = str(i)
            row_label = my_text(label, label_pos)
            self.scene.addItem(row_label)
            x = self.w - 1
            displacement.x = self.Vd * 1.35
            # displacement.y = -self.Vd
            label_pos = self.K[self.w - 1][i].gco + displacement
            label = str(i)
            row_label = my_text(label, label_pos)
            self.scene.addItem(row_label)

    def to_dict(self):
        """Extract all ribbon data for saving to file"""
        return {
            "version": "1.0",
            "ribbon": {
                "width": self.w,
                "length": self.l,
                "type": self.type
            },
            "thread_colors": [
                [sk.color.red(), sk.color.green(), sk.color.blue()]
                for sk in self.StartKnot_list
            ],
            "knots": [[
                {
                    "co": self.K[x][y].co,
                    "type": self.K[x][y].type.name,
                    "left_thread_vis": self.K[x][y].left_thread_vis
                }
                for y in range(self.l)
            ] for x in range(self.w)]
        }

    def restore_from_dict(self, data):
        """Restore knot states and thread colors from saved data"""
        # Restore thread colors
        thread_colors = data.get("thread_colors", [])
        for i, rgb in enumerate(thread_colors):
            if i < len(self.StartKnot_list):
                new_color = QColor(rgb[0], rgb[1], rgb[2])
                self.StartKnot_list[i].color = new_color
                # Update the color rectangle
                color_rect = self.StartKnot_list[i].line.scene().items()
                # Find and update the corresponding ColorRect
                for item in color_rect:
                    if isinstance(item, ColorRect) and hasattr(item, 'index') and item.index == i:
                        item.setBrush(QBrush(new_color))
                        item.color = new_color
                        break

        # Restore knot states
        knots_data = data.get("knots", [])
        for x in range(min(self.w, len(knots_data))):
            for y in range(min(self.l, len(knots_data[x]))):
                knot_data = knots_data[x][y]
                type_str = knot_data.get("type", "Nk")
                self.K[x][y].type = getattr(Const, type_str, Const.Nk)
                self.K[x][y].left_thread_vis = knot_data.get("left_thread_vis", True)
                # Restore coordinates if present
                if "co" in knot_data:
                    self.K[x][y].co = knot_data["co"]

        # Recalculate all thread colors through the pattern
        for i in range(len(self.StartKnot_list)):
            CS = self.StartKnot_list[i]
            color = CS.color
            Kh = CS.Knot
            direction = CS.direction
            Kh.set_thread(color, direction, self.thW)

        # Run twice to ensure all colors propagate
        for i in range(len(self.StartKnot_list)):
            CS = self.StartKnot_list[i]
            color = CS.color
            Kh = CS.Knot
            direction = CS.direction
            Kh.set_thread(color, direction, self.thW)

    def get_ribbon(self):
        scene = self.scene()
        return getattr(scene, "ribbon", None) if scene else None

    class KnotList():
        def __init__(self, scene, KnPnts):
            self.color = QColor()
            self.Knot = Knot(scene, KnPnts)
            self.direction = Const.LeftIn
            self.line = QGraphicsLineItem()


class Vector:  # vector
    def __init__(self, x=0.0, y=0.0):  # x, y float
        self.x = x
        self.y = y

    def __repr__(self):  # print vector v
        return f"vector({self.x}, {self.y})"

    def to_list(self):  # convert vector to list
        return [self.x, self.y]

    # def add(a, b):  # vector add, a, b vector
    #     h = Vector(a.x + b.x, a.y + b.y)
    #     return (h)

    def __add__(a, b):  # vector add, a, b vector
        h = Vector(a.x + b.x, a.y + b.y)
        return (h)

    def i_mult(a, b):  # vector in multiplication, a, b vector
        h = Vector(a.x * b.x + a.y * b.y)
        return (h)

    def s_mult(a, b):  # vector skalar multiplication, a vector vector, b float
        h = Vector()
        h.x = a.x * b
        h.y = a.y * b
        return (h)

    def abs_v(a):  # absolute value
        return (math.sqrt(a.x ** 2 + a.y ** 2))


class Const(Enum):
    LeftIn = auto()
    RightIn = auto()
    LeftOut = auto()
    RightOut = auto()
    # Knots inside ribbon
    Nk = auto()  # Normal not, 0 start threads
    Rk = auto()  # Reverse not, 0 start threads
    # end knots
    EndKLuRd = auto()  # End knot left up to right down
    EndKRuLd = auto()  # End knot right up to left down
    EndKBoth = auto()  # End knot right up to left down and left up to right dow, for type A only
    LeftThrdVis = auto()
    RightThrdVis = auto()
    undefined = auto()
    NA = auto()  # not available
    # line types
    arc = auto()
    line = auto()


class KnotPoints():
    def __init__(self, Kd, Vd):
        Ddi = Vd / Kd  # Ddi made smaller in relation to Kd

        sqrt_2 = math.sqrt(2)  # calculate only once for multiple use

        # left thread entry point, vector=1:(0.1464, 0.1464) for Kd = 1
        self.LftThrEntPt = Vector((sqrt_2 - 1) / 2 / sqrt_2, (sqrt_2 - 1) / 2 / sqrt_2)
        # print(f"LftThrEntPt ({LftThrEntPt.x:.5f}, {LftThrEntPt.y:.5f})")

        # Right thread entry point, vector=1:(0.8536, 0.1464) for Kd = 1
        self.RgtThrEntPt = Vector(1 - (sqrt_2 - 1) / 2 / sqrt_2, (sqrt_2 - 1) / 2 / sqrt_2)
        # print(f"RgtThrEntPt ({RgtThrEntPt.x:.5f}, {RgtThrEntPt.y:.5f})")

        # left exit thread top point, vector=1:(0.1464, 0.8536) for Kd = 1
        self.LftThrTopPt = Vector(0.5 - 0.5 / sqrt_2, 0.5 + 0.5 / sqrt_2)
        # print(f"LftThrTopPt ({LftThrTopPt.x:.5f}, {LftThrTopPt.y:.5f})")

        # left exit thread bottom point,vector=1:(-0.1464, 1.1464) for Kd = 1
        self.LftThrBotPt = Vector(0.5 / sqrt_2 - Ddi + 0.5, Ddi + (sqrt_2 - 1) / 2 / sqrt_2)
        # print(f"gc.LftThrBotPt ({gc.LftThrBotPt.x:.5f}, {gc.LftThrBotPt.y:.5f})")

        # right exit thread top point, vector=1:(0.8536, 0.8536) for Kd = 1
        self.RgtThrTopPt = Vector(0.5 / sqrt_2 + 0.5, 0.5 / sqrt_2 + 0.5)
        # print(f"RgtThrTopPt ({RgtThrTopPt.x:.5f}, {RgtThrTopPt.y:.5f})")

        # right exit thread bottom point, vector=1:(1.1464, 1.1464) for Kd = 1
        self.RgtThrBotPt = Vector(Ddi + (sqrt_2 - 1) / 2 / sqrt_2, Ddi + (sqrt_2 - 1) / 2 / sqrt_2)
        # print(f"RgtThrBotPt ({RgtThrBotPt.x:.5f}, {RgtThrBotPt.y:.5f})")

        # vector from center of arc to RgtThrTopPt for Kd = 1
        self.PMa = Vector(0.5 / sqrt_2 - Ddi, 0.5 / sqrt_2 - Ddi)
        # print(f"PMa ({PMa.x:.5f}, {PMa.y:.5f})")

        # radius of arc for Kd = 1
        self.ArcRad = Vector.abs_v(self.PMa)
        # print(f"ArcRad {ArcRad:.5f}")

        # side of quadrat for circles for arcs, vector=1: 1.8284 for Kd = 1
        self.ArcQuadSide = 2 * self.ArcRad  # side of quadrat for circles for arcs, vector=1: 1.8284
        # print(f"ArcQuadSide {ArcQuadSide:.5f}")

        # reference point of quadrat for circle for arc to the left side, vector=1:(-0.1213, 0.5858)
        #  for Kd = 1
        self.RefPtArcLft = Vector(Ddi - self.ArcRad - 0.5 * sqrt_2 + 0.5, Ddi - self.ArcRad + 0.5)
        # print(f"RefPtArcLft ({RefPtArcLft.x:.5f}, {RefPtArcLft.y:.5f})")

        # reference point of quadrat for circle for arc to the right side, vector=1:(-0.7071, 0.5858)
        # for Kd = 1
        self.RefPtArcRgt = Vector(0.5 * sqrt_2 - Ddi - self.ArcRad + 0.5, Ddi - self.ArcRad + 0.5)
        # print(f"RefPtArcRgt ({RefPtArcRgt.x:.5f}, {RefPtArcRgt.y:.5f})")

        # start angle for arc to the left side
        self.StartAngLft = 135

        # start angle for arc to the right side
        self.StartAngRgt = 45

        # span angle for both arcs (left or right)
        self.SpanAng = 90
        # ***************************************************************************************#

        self.adjust(Kd)

    def adjust(self, Kd):
        # adjust geometric constants to the actual values of self.Vd and Kd
        # ***************************************************************************************#
        # left thread entry point, for Kd = !1
        self.LftThrEntPt = Vector.s_mult(self.LftThrEntPt, Kd)
        # print(f"LftThrEntPt ({LftThrEntPt.x:.5f}, {LftThrEntPt.y:.5f})")

        # Right thread entry point, for Kd != 1
        self.RgtThrEntPt = Vector.s_mult(self.RgtThrEntPt, Kd)
        # print(f"RgtThrEntPt ({RgtThrEntPt.x:.5f}, {RgtThrEntPt.y:.5f})")

        # left exit thread top point, for Kd != 1
        self.LftThrTopPt = Vector.s_mult(self.LftThrTopPt, Kd)
        # print(f"LftThrTopPt ({LftThrTopPt.x:.5f}, {LftThrTopPt.y:.5f})")

        # left exit thread bottom point, for Kd = !1
        self.LftThrBotPt = Vector.s_mult(self.LftThrBotPt, Kd)
        # print(f"gc.LftThrBotPt ({gc.LftThrBotPt.x:.5f}, {gc.LftThrBotPt.y:.5f})")

        # right exit thread top point, for Kd = !1
        self.RgtThrTopPt = Vector.s_mult(self.RgtThrTopPt, Kd)
        # print(f"RgtThrTopPt ({RgtThrTopPt.x:.5f}, {RgtThrTopPt.y:.5f})")

        # right exit thread bottom point, for Kd = !1
        self.RgtThrBotPt = Vector.s_mult(self.RgtThrBotPt, Kd)
        # print(f"RgtThrBotPt ({RgtThrBotPt.x:.5f}, {RgtThrBotPt.y:.5f})")

        # vector from center of arc to RgtThrTopPt for Kd = 1
        self.PMa = Vector.s_mult(self.PMa, Kd)
        # print(f"PMa ({PMa.x:.5f}, {PMa.y:.5f})")

        # side of quadrat for circles for arcs, for Kd != 1
        self.ArcQuadSide = 2 * self.ArcRad * Kd  # side of quadrat for circles for arcs, vector=1: 1.8284
        # print(f"ArcQuadSide {ArcQuadSide:.5f}")

        # reference point of quadrat for circle for arc to the left side, for Kd != 1
        self.RefPtArcLft = Vector.s_mult(self.RefPtArcLft, Kd)
        # print(f"RefPtArcLft ({RefPtArcLft.x:.5f}, {RefPtArcLft.y:.5f})")

        # reference point of quadrat for circle for arc to the right side, for Kd != 1
        self.RefPtArcRgt = Vector.s_mult(self.RefPtArcRgt, Kd)
        # print(f"RefPtArcRgt ({RefPtArcRgt.x:.5f}, {RefPtArcRgt.y:.5f})")
        # ***************************************************************************************#


class Knot():
    def __init__(self, scene, kpts):
        self.scene = scene
        if scene is not None:
            setattr(scene, "knot", self)
            # print("✅ knot registered to scene as 'scene.knot'")
        undefined = QColor("lightgrey")
        self.co = [0, 0]  # knot coordinate
        self.gco = Vector()  # geometric coordinate
        self.left_thread_vis = True
        # left thread visible
        self.knot_color = None  # color of circle fill
        self.strtK = False  # start knot
        self.endK = False  # end knot
        self.edgeKL = False  # edge knot left
        self.edgeKR = False  # edge knot right
        self.color_in_left = QColor("lightgrey")  # input thread from left, QColor
        self.color_in_right = QColor("lightgrey")  # input thread from right, QColor
        self.type = Const.Nk  # normal knot
        self.endKtype = Const.undefined
        self.nKtoL = None  # next knot to left
        self.nKtoR = None  # next knot to right
        self.circle = None  # QgraphicsItem
        # lines and arcs connect to the next knots
        self.line_out_left = None  # QgraphicsItem
        self.line_out_right = None  # QgraphicsItem
        self.arc_out_left = None  # QgraphicsItem
        self.arc_out_right = None  # QgraphicsItem
        self.kp = kpts  # precalculated relative knot points in each knot
        self.colors = my_Colors()

    def KnPar():
        # basic paramters of each knot for json storage
        self.x = 0  # x coordinate
        self.y = 0  # y coordinate
        self.left_thread_visible = True
        self.type = Const.Nk
        self.endK = False

    def draw_graphic_items(self, color, thW, Dc, scene):
        c1 = QColor("black")
        undefined = QColor("lightgrey")
        pen1 = QPen(c1)
        pen2 = QPen(undefined)
        pen1.setWidth(thW)
        pen2.setWidth(thW)
        circle = KnotCircle(self.gco.x, self.gco.y, Dc, Dc, self)
        pen = QPen(color)
        pen.setWidth(1)
        brush = QBrush(undefined)
        circle.setBrush(brush)
        circle.setPen(pen)
        scene.addItem(circle)
        self.circle = circle
        # normal knots and middle reverse knots
        if not self.endK and not (self.edgeKL or self.edgeKR):
            self.line_out_right = self.draw_line(self.gco, self.kp.RgtThrTopPt, self.kp.RgtThrBotPt, pen2,
                                                 Const.RightOut, scene)
            self.line_out_left = self.draw_line(self.gco, self.kp.LftThrTopPt, self.kp.LftThrBotPt, pen2, Const.LeftOut,
                                                scene)

        # edge knots, arcs and lines for left edge
        if not self.endK and self.edgeKL:
            self.line_out_right = self.draw_line(self.gco, self.kp.RgtThrTopPt, self.kp.RgtThrBotPt, pen2,
                                                 Const.RightOut, scene)
            # self.arc_out_left = self.set_arc(self.gco, RefPtArcLft, ArcQuadSide, SrtAngArcLft, SpanAngArc, pen1)
            self.draw_arc(self.gco, self.kp.LftThrTopPt, self.kp.RefPtArcLft, self.kp.ArcQuadSide, self.kp.StartAngLft,
                          self.kp.SpanAng, pen2, Const.LeftOut, scene)

        # edge knots, arcs and lines for right edge
        if not self.endK and self.edgeKR:
            self.line_out_right = self.draw_line(self.gco, self.kp.LftThrTopPt, self.kp.LftThrBotPt, pen2,
                                                 Const.LeftOut, scene)
            # self.arc_out_right = self.set_arc(self.gco, RefPtArcRgt, self.gc.ArcQuadSide, SrtAngArcRgt, SpanAngArc, pen1)
            self.draw_arc(self.gco, self.kp.RgtThrTopPt, self.kp.RefPtArcRgt, self.kp.ArcQuadSide, self.kp.StartAngRgt,
                          -self.kp.SpanAng, pen2, Const.RightOut, scene)

        # end knots
        if self.endK:
            if self.endKtype == Const.EndKRuLd:  # End knot with right exit thread
                self.line_out_right = self.draw_line(self.gco, self.kp.RgtThrTopPt, self.kp.RgtThrBotPt, pen2,
                                                     Const.RightOut, scene)
            if self.endKtype == Const.EndKLuRd:  # End knot with left exit thread
                self.line_out_left = self.draw_line(self.gco, self.kp.LftThrTopPt, self.kp.LftThrBotPt, pen2,
                                                    Const.LeftOut, scene)
            if self.endKtype == Const.EndKBoth:  # End knot with both exit threads
                self.line_out_right = self.draw_line(self.gco, self.kp.RgtThrTopPt, self.kp.RgtThrBotPt, pen2,
                                                     Const.RightOut, scene)
                self.line_out_left = self.draw_line(self.gco, self.kp.LftThrTopPt, self.kp.LftThrBotPt, pen2,
                                                    Const.LeftOut, scene)

    def draw_line(self, gco, p1, p2, pen, direction, scene):
        vStart = gco + p1  # calculate location vector of start point
        vEnd = gco + p2  # calculate location vector of end point
        line = QGraphicsLineItem(vStart.x, vStart.y, vEnd.x, vEnd.y)
        line.setPen(pen)
        if direction == Const.LeftOut:
            self.line_out_left = line
        else:
            self.line_out_right = line
        scene.addItem(line)
        return (line)

    def draw_arc(self, gco, startPt, refPtArc, dia, strAng, spanAng, pen, direction, scene):
        vRef = gco + refPtArc  # calculate location vector of arc reference point
        vStart = gco + startPt  # calculate location vector of arc start point
        QPpath = QPainterPath()
        QPpath.moveTo(vStart.x, vStart.y)  # set start point of arc
        rect = QRectF(vRef.x, vRef.y, dia, dia)  # reference rectangele for arc circle
        QPpath.arcTo(rect, strAng, spanAng)
        path = QGraphicsPathItem()
        path.setPath(QPpath)
        path.setPen(pen)
        if direction == Const.LeftOut:
            self.arc_out_left = path
        else:
            self.arc_out_right = path
        scene.addItem(path)

    def set_thread(self, color, direction, thW):
        inDir = direction
        color_name = self.colors.print_color_key(color)
        # print(f"set_thread, co: {self.co}, type {self.type}, direction: {direction} color {color_name}")
        h = self.next_direction(inDir, color, thW)
        if h["Stop"]:
            return ()
        nxtKnot = h["nxtKnot"]
        nxtDir = h["nxtDir"]
        # print(f"set_thread, co: {nxtKnot.co}, type {nxtKnot.type}, direction: {nxtDir} color {color_name}")
        nxtKnot.set_thread(color, nxtDir, thW)

    def set_knot_color(self):
        if self.left_thread_vis:
            color = self.color_in_left
        else:  # right_thread_visible
            color = self.color_in_right
        self.knot_color = color
        color_in_left_name = self.colors.print_color_key(self.color_in_left)
        color_in_right_name = self.colors.print_color_key(self.color_in_right)
        color_name = self.colors.print_color_key(color)
        # print(f"set_knot_color, co: {self.co}, left_thread_vis: {self.left_thread_vis}, "
        #       f"color_in_left {color_in_left_name} color_in_right {color_in_right_name} "
        #       f"new_knot_color: {color_name}")
        self.circle.setBrush(color)
        self.circle.setZValue(0.3)

    def next_direction(self, direction, color, thW):
        p_color = self.colors.print_color_key(color)
        # print(f"next_direction_in, co {self.co} type {self.type} , "
        #       f"color {p_color}, direction {direction}")
        inDir_actualKnot = direction
        inDir_nKnot = direction
        # nKnot = Knot(self.scene, self.kp)
        pen = QPen(color)
        pen.setWidth(thW)
        rDat = {"Stop": False}

        # set input color in Knot
        if inDir_actualKnot == Const.LeftIn:
            self.color_in_left = color
        else:
            self.color_in_right = color

        self.set_knot_color()

        if not self.endK:  # inner knot
            h = self.next_no_end_knot(inDir_actualKnot, pen)
        elif self.endK:  # end knot
            h = self.next_end_knot(inDir_actualKnot, pen)

        # print(f"next_direction_out, co {nKnot.co} type {nKnot.type} , "
        #         #       f"color {p_color}, direction {inDir_nKnot}")
        #         rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
        #         return (rDat)
        return (h)

    def change_knot_type(self, direction):
        nKnot = Knot(self.scene, self.kp)
        if self.type == Const.Nk:
            if direction == Const.LeftIn:
                outDir_actualKnot = Const.RightOut
                inDir_nKnot = Const.LeftIn
                nKnot = self.nKtoR
            elif direction == Const.RightIn:
                outDir_actualKnot = Const.LeftOut
                inDir_nKnot = Const.RightIn
                nKnot = self.nKtoL
        elif self.type == Const.Rk:
            if direction == Const.LeftIn:
                outDir_actualKnot = Const.LeftOut
                inDir_nKnot = Const.RightIn
                nKnot = self.nKtoL
            elif direction == Const.RightIn:
                outDir_actualKnot = Const.RightOut
                inDir_nKnot = Const.LeftIn
                nKnot = self.nKtoR
        rDat = {"nKnot": nKnot, "inDir_nKnot": inDir_nKnot, "outDir_actualKnot": outDir_actualKnot}
        return (rDat)

    def next_end_knot(self, inDir, pen):
        h = self.change_knot_type(inDir)
        inDir_nKnot = h["inDir_nKnot"]
        outDir_actualKnot = h["outDir_actualKnot"]
        nKnot = h["nKnot"]
        color = pen.color()
        p_color = self.colors.print_color_key(color)
        # print(f"next_end_knot, co {self.co} type {self.type} , "
        #       f"color {p_color}, direction {inDir}")
        # return next endK and input direction to next endK
        nKnot = Knot(self.scene, self.kp)
        if self.edgeKR:
            if outDir_actualKnot == Const.LeftOut:
                if self.nKtoL is None:
                    rDat = {"Stop": True}
                    return (rDat)
                else:
                    nKnot = self.nKtoL
                    self.line_out_left.setPen(pen)
                    self.line_out_left.setZValue(0.4)
                    rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
                    return (rDat)
            elif outDir_actualKnot == Const.RightOut:
                if self.nKtoR is None:
                    rDat = {"Stop": True}
                    return (rDat)
                else:
                    nKnot = self.nKtoR
                    self.line_out_right.setPen(pen)
                    self.right.setZValue(0.4)
                    rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
                    return (rDat)
        elif self.edgeKL:
            if outDir_actualKnot == Const.RightOut:
                if self.nKtoR is None:
                    rDat = {"Stop": True}
                    return (rDat)
                else:
                    nKnot = self.nKtoR
                    self.line_out_right.setPen(pen)
                    self.line_out_right.setZValue(0.4)
                    rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
                    return (rDat)
            elif outDir_actualKnot == Const.LeftOut:
                if self.nKtoL is None:
                    rDat = {"Stop": True}
                    return (rDat)
                elif self.nKtoR is None:
                    rDat = {"Stop": True}
                    return (rDat)
                else:
                    nKnot = self.nKtoR
                    self.line_out_left.setPen(pen)
                    self.left.setZValue(0.4)
                    rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
                    return (rDat)
        else:
            if self.endKtype == Const.EndKLuRd:
                if outDir_actualKnot == Const.LeftOut:
                    nKnot = self.nKtoL
                    self.line_out_left.setPen(pen)
                    self.line_out_left.setZValue(0.4)
                    rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
                    return (rDat)
                elif outDir_actualKnot == Const.RightOut:
                    rDat = {"Stop": True}
            elif self.endKtype == Const.EndKRuLd:
                if outDir_actualKnot == Const.RightOut:
                    nKnot = self.nKtoR
                    self.line_out_right.setPen(pen)
                    self.line_out_right.setZValue(0.4)
                    rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
                    return (rDat)
                elif outDir_actualKnot == Const.LeftOut:
                    rDat = {"Stop": True}
            elif self.endKtype == Const.EndKBoth:
                if outDir_actualKnot == Const.RightOut:
                    nKnot = self.nKtoR
                    self.line_out_right.setPen(pen)
                    self.line_out_right.setZValue(0.4)
                    rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
                elif outDir_actualKnot == Const.LeftOut:
                    nKnot = self.nKtoL
                    self.line_out_left.setPen(pen)
                    self.line_out_left.setZValue(0.4)
                    rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
                else:
                    rDat = {"Stop": True}
            else:
                rDat = {"Stop": True}

        return (rDat)

    def next_no_end_knot(self, direction, pen):
        h = self.change_knot_type(direction)
        inDir_nKnot = h["inDir_nKnot"]
        outDir_actualKnot = h["outDir_actualKnot"]
        nKnot = h["nKnot"]
        color = pen.color()
        p_color = self.colors.print_color_key(color)
        # print(f"next_not_end_knot, co {self.co} type {self.type} , "
        #       f"color {p_color}, direction {direction}")
        # set color to next knot and set next input direction
        # check for arcs
        if self.edgeKR and (nKnot == self.nKtoR) and (outDir_actualKnot == Const.RightOut):
            self.arc_out_right.setPen(pen)
            self.arc_out_right.setZValue(0.4)
            inDir_nKnot = Const.RightIn
        elif self.edgeKL and (nKnot == self.nKtoL) and (outDir_actualKnot == Const.LeftOut):
            self.arc_out_left.setPen(pen)
            self.arc_out_left.setZValue(0.4)
            inDir_nKnot = Const.LeftIn
        else:  # no arcs, only lines
            if outDir_actualKnot == Const.RightOut:
                self.line_out_right.setPen(pen)
                self.line_out_right.setZValue(0.4)
            elif outDir_actualKnot == Const.LeftOut:
                self.line_out_left.setPen(pen)
                self.line_out_left.setZValue(0.4)

        if inDir_nKnot == Const.LeftIn:
            nKnot.color_in_left = color
        elif inDir_nKnot == Const.RightIn:
            nKnot.color_in_right = color
        # print(f"next_direction_out, co {nKnot.co} type {nKnot.type} , "
        #       f"color {p_color}, direction {inDir_nKnot}")
        rDat = {"Stop": False, "nxtKnot": nKnot, "nxtDir": inDir_nKnot}
        return (rDat)


class my_Colors():
    def __init__(self):
        # preset available start colors
        self.black = QColor("black")
        self.red = QColor.fromRgb(255, 99, 71)
        self.green = QColor.fromRgb(0, 255, 0)
        self.blue = QColor.fromRgb(0, 191, 255)
        self.grey = QColor("lightgrey")
        self.darkgrey = QColor("darkgrey")
        self.cyan = QColor("cyan")
        self.magenta = QColor.fromRgb(238, 130, 238)
        self.yellow = QColor("yellow")
        self.f = [self.red, self.green, self.blue, self.black, self.cyan, self.magenta, self.yellow, self.darkgrey]
        self.f_d = {
            "red": self.red,
            "green": self.green,
            "blue": self.blue,
            "black": self.black,
            "cyan": self.cyan,
            "magenta": self.magenta,
            "yellow": self.yellow,
            "darkgrey": self.darkgrey
        }

    def print_color_key(self, color: QColor):
        color_name = [k for k, v in self.f_d.items() if v == color]
        # print(f"print_color_name, {color_name}")
        return (color_name)


class my_text(QGraphicsSimpleTextItem):
    def __init__(self, text, pos, size=18, color=QColor("black")):
        super().__init__(text)
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        self.setBrush(color)
        self.setX(pos.x)
        self.setY(pos.y)


class SceneObjectBase:
    """Base class for all custom scene items."""

    def get_ribbon(self):
        scene = self.scene()
        return getattr(scene, "ribbon", None) if scene else None


class KnotCircle(QGraphicsEllipseItem, SceneObjectBase):
    def __init__(self, x, y, w, h, knot, parent=None):
        super().__init__(x, y, w, h, parent)
        self.knot = knot
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)

        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self._on_single_click_timeout)  # connect ONCE

        self._last_button = None  # store which mouse button was pressed

        # Cross-version constants (PyQt5 vs PyQt6)
        self._Left = getattr(Qt, "LeftButton", getattr(Qt.MouseButton, "LeftButton", 1))
        self._Right = getattr(Qt, "RightButton", getattr(Qt.MouseButton, "RightButton", 2))

    def mousePressEvent(self, event):
        # remember which button was clicked and start the single-click timer
        self._last_button = event.button()
        # print("Mouse pressed")
        self.click_timer.start(300)  # wait to see if a double-click happens
        event.accept()

    def mouseDoubleClickEvent(self, event):
        # cancel the pending single-click
        if self.click_timer.isActive():
            self.click_timer.stop()

        # print(f"Knot Double-clicked on {self.knot.co}")

        event.accept()

        self.change_thread_direction()

        # reset the stored button after handling
        self._last_button = None

    def _on_single_click_timeout(self):
        """Called by QTimer.timeout with no args."""
        btn = self._last_button
        self._last_button = None  # reset

        # If something weird happened (e.g., double-click already consumed it), bail
        if btn is None:
            return

        # Normalize button comparisons across PyQt5/6
        try:
            is_left = (btn == self._Left)
            is_right = (btn == self._Right)
        except Exception:
            # Some environments pass ints; fall back to int compare
            is_left = int(btn) == int(self._Left)
            is_right = int(btn) == int(self._Right)

        if is_left:
            self._do_single_left_click()
        elif is_right:
            self._do_single_right_click()
        else:
            print(f"Other button single-click at {self.knot.co[0]}, {self.knot.co[1]}")

    def _do_single_left_click(self):
        # print(f"Left single-click on {self.knot.co}")
        self.toggle_knot_color()

    def _do_single_right_click(self):
        # print(f"Right single-click on, co {self.knot.co}")
        self.change_thread_direction()

    # def handle_right_click(self):
    #     # Placeholder for your context menu or other right-click behavior
    #     print("Right-click: open context menu / do something else.")

    def toggle_knot_color(self):
        self.knot.left_thread_vis = not self.knot.left_thread_vis
        self.knot.set_knot_color()

    def change_thread_direction(self):
        R = self.get_ribbon()
        # toggle knot type
        if self.knot.type == Const.Nk:
            self.knot.type = Const.Rk
        else:
            self.knot.type = Const.Nk

        # p_color_in_right = self.knot.colors.print_color_key(self.knot.color_in_right)
        # print(f"change_thread_direction, thread from the right, type {self.knot.type} , "
        #       f"color {p_color_in_right} direction {Const.RightIn}")
        self.knot.set_thread(self.knot.color_in_right, Const.RightIn, R.thW)
        # p_color_in_left = self.knot.colors.print_color_key(self.knot.color_in_left)
        # print(f"change_thread_direction, thread from the left, type {self.knot.type} , "
        #       f"color {p_color_in_left} direction {Const.LeftIn}")
        self.knot.set_thread(self.knot.color_in_left, Const.LeftIn, R.thW)


class ColorRect(QGraphicsRectItem, SceneObjectBase):
    def __init__(self, x, y, w, h, index, parent=None):
        super().__init__(x, y, w, h, parent)
        self.index = index
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.do_single_click)

    def mousePressEvent(self, event):
        # Start timer for single click
        # to avoid double event for double-click
        self.click_timer.start(300)  # ms
        event.accept()

    def mouseDoubleClickEvent(self, event):
        # Cancel pending single-click action
        if self.click_timer.isActive():
            self.click_timer.stop()
        # print(f"Color Rect Double-clicked on {self.index}")
        event.accept()

    def do_single_click(self):
        brush = self.brush()
        color = brush.color()
        name = color.name(format=QColor.NameFormat.HexRgb)
        # print(f"Color Rect Single-clicked on index: {self.index} color: {name}")
        # ✅ Get the parent window (so the color dialog stays modal)
        parent_widget = None
        if self.scene() and self.scene().views():
            parent_widget = self.scene().views()[0].window()
        new_color = QColorDialog.getColor(color, parent_widget, "Select Color")
        if not new_color.isValid():
            return  # user cancelled
        self.setBrush(new_color)
        # print(f"New color selected: {new_color.name()}")
        scene = self.scene()
        R = self.get_ribbon()
        CS = R.StartKnot_list[self.index]
        Kh = getattr(CS, "Knot", None)
        direction = getattr(CS, "direction", None)
        Kh.set_thread(new_color, direction, R.thW)
        line = getattr(CS, "line", None)
        pen = QPen()
        pen.setColor(new_color)
        pen.setWidth(R.thW)
        line.setPen(pen)
