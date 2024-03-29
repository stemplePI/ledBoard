#!/usr/bin/env python3
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

import random
import threading
import time
from math import floor, sqrt
from os.path import exists as file_exists

import font

realBoard = False
if(file_exists("realBoardFlag")):
    import realGrid as grid
    realBoard = True
else:
    import tKinterGrid as grid


def rgbColor(r, g, b):
    return (r << 16)+(g << 8)+b


colors = {
    "red": rgbColor(255, 0, 0),
    "green": rgbColor(0, 255, 0),
    "blue": rgbColor(0, 0, 255),
    "white": rgbColor(200, 200, 200),
    "orange": rgbColor(240, 131, 29),
    "off": 0
}

colList = []
colList.append(0)  # Black
colList.append(rgbColor(255, 0, 0))  # red
colList.append(rgbColor(0, 255, 0))  # green
colList.append(rgbColor(0, 0, 255))  # blue
colList.append(rgbColor(200, 200, 0))  # yellow-green
colList.append(rgbColor(255, 140, 10))  # orange
colList.append(rgbColor(200, 200, 200))  # white
colList.append(rgbColor(255, 0, 200))  # violet

redMask = 0xFF << 16
greenMask = 0xFF << 8
blueMask = 0xFF

modeBtn = (0, 0)

# util functions for drawing


def sumColors(a, b):
    """sums two colors togeather, adding R, G, and B seperatly"""
    rSum = min((a & redMask) + (b & redMask), redMask)
    gSum = min((a & greenMask) + (b & greenMask), greenMask)
    bSum = min((a & blueMask) + (b & blueMask), blueMask)
    return rSum + gSum + bSum


def multColor(col, mult):
    """multiplies the RGB color by a scalar, designed for multiples < 1"""
    rVal = min(int((col & redMask) * mult), redMask) & redMask
    gVal = min(int((col & greenMask) * mult), greenMask) & greenMask
    bVal = min(int((col & blueMask) * mult), blueMask) & blueMask
    return rVal+gVal+bVal


def heatCol(amt):
    """converts 0-255 'heat' value to a RGB value"""
    red = int(min(amt*1.5, 255))
    green = max(2*amt-300, 0)
    blue = int(max(255-2*amt, 0)+green)
    return (red << 16)+(green << 8)+blue


def testHeat():
    """displays the heat gradient as a test"""
    for x in range(8):
        for y in range(8):
            grid.drawPixel(x, y, heatCol(x*32))


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return rgbColor(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return rgbColor(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return rgbColor(0, pos * 3, 255 - pos * 3)


def clearDown(t=.2):
    """wipes the screen from top to bottom, waiting <t> between each row"""
    for y in range(8):
        for x in range(8):
            grid.drawPixel(x, 7-y, 0)
        time.sleep(t)


def transition(col, interval=1/15):
    """Gradually paints a square <col> filling the board, starting at mode btn"""
    for i in range(8):
        for x in range(i):
            grid.drawPixel(x, i, col)
        for y in range(i+1):
            grid.drawPixel(i, y, col)
        grid.stripShow()
        time.sleep(interval)
# Define functions which animate LEDs in various ways.


def calcWavePoint(grid, point):
    """Adds the wave values for a specific seed point, outputing back to grid"""
    for y, row in enumerate(grid):
        for x, val in enumerate(row):
            err = sqrt((point[0]-x)**2+(point[1]-y)**2)-point[2]
            weightErr = .65-.8*err**2
            mult = max(0, max(min(weightErr, 1), 0))
            # add the color, multiplied by ramping
            grid[y][x] = sumColors(val, multColor(point[3], mult))


def wave():
    """creates circular waves that mova away from a button press"""
    seedPoints = []
    drawInterval = 1/15

    while(True):
        nextDrawTime = time.time()+drawInterval
        # 8x8 grid, rgb vals for each pixel
        pixelGrid = [[0 for x in range(8)] for y in range(8)]
        kDownEvents = grid.readKeys()[0]

        if modeBtn in kDownEvents:
            return  # go back to mode switch

        for key in kDownEvents:
            col = colList[random.randint(1, len(colList)-1)]
            seedPoints.append([key[0], key[1], 0.0, col])  # add
            kDownEvents.remove(key)
        for i, seed in enumerate(seedPoints):
            if seed[2] > 10:
                seedPoints.remove(seed)
                continue
            seedPoints[i][2] = seedPoints[i][2]*1.03+.14
            calcWavePoint(pixelGrid, seedPoints[i])
        grid.drawGrid(pixelGrid)

        while(time.time() < nextDrawTime):
            pass


def pressCol():
    """Cycles through list of colors when a button is pressed"""
    drawInterval = 1/40
    # 8x8 grid, color index for each pixel
    pixelGrid = [[0 for x in range(8)] for y in range(8)]
    while(True):
        nextDrawTime = time.time()+drawInterval
        kDownEvents = grid.readKeys()[0]
        if(modeBtn in kDownEvents):
            return
        for x, y in kDownEvents:
            colInd = colList.index(pixelGrid[y][x])  # get current col ind
            colInd = (colInd + 1) % len(colList)  # increment color ind
            pixelGrid[y][x] = colList[colInd]  # set new color
        grid.drawGrid(pixelGrid)
        while(time.time() < nextDrawTime):
            pass


def holdCol():
    """cycles through color wheel while button is held"""
    drawInterval = 1/40
    # 8x8 grid, rgb vals for each pixel
    pixelGrid = [[0 for x in range(8)] for y in range(8)]
    while(True):
        nextDrawTime = time.time()+drawInterval

        heldKeys = grid.readKeys()[1]
        if(modeBtn in heldKeys):
            return
        for x, y in heldKeys:  # find new key presses
            pixelGrid[y][x] = (pixelGrid[y][x]+3) & 255
        for y, row in enumerate(pixelGrid):
            for x, val in enumerate(row):
                grid.drawPixel(x, y, multColor(wheel(val), .7))
        grid.stripShow()
        while(time.time() < nextDrawTime):
            pass


def rainbow(wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    drawInterval = 1/40
    rainbowOffset = 0
    while(True):
        nextDrawTime = time.time()+drawInterval

        k = grid.readKeys()[1]
        if(modeBtn in k):
            return

        rainbowOffset = (rainbowOffset + 2) & 0xFF
        for i in range(8):
            col = wheel((i*32+rainbowOffset) & 255)
            for j in range(8):
                grid.drawPixel(j, i, col)
        grid.stripShow()
        while(time.time() < nextDrawTime):
            pass


def rainbowFine(wait_ms=20, iterations=1):
    """Fades through a rainbow linearly,with full led resolution"""
    drawInterval = 1/40
    rainbowOffset = 0
    while(True):
        nextDrawTime = time.time()+drawInterval

        k = grid.readKeys()[1]
        if(modeBtn in k):
            return

        rainbowOffset = (rainbowOffset + 2) & 0xFF
        for i in range(16):
            col = wheel((i*16+rainbowOffset) & 255)
            for j in range(24):
                grid.setLED(i*24+j, col)
        grid.stripShow()
        while(time.time() < nextDrawTime):
            pass


def heatMap():
    """Turns board into heatmap, pushing a button 'heats' it, then disperses to neighbors"""
    pixelGrid = [[0 for x in range(8)] for y in range(
        8)]  # 8x8 grid, rgb vals for each pixel
    # list of adjacent pixels for each pixel
    adjGrid = [[[] for __ in range(8)] for __ in range(8)]
    for y in range(8):
        for x in range(8):
            if(0 <= x+1 < 8 and 0 <= y < 8):
                adjGrid[y][x].append((x+1, y))
            if(0 <= x-1 < 8 and 0 <= y < 8):
                adjGrid[y][x].append((x-1, y))
            if(0 <= x < 8 and 0 <= y+1 < 8):
                adjGrid[y][x].append((x, y+1))
            if(0 <= x < 8 and 0 <= y-1 < 8):
                adjGrid[y][x].append((x, y-1))

    cHeatTrans = .15  # constant for heat transfer between cells
    cHeatLoss = 0.99  # heat lost per cell per loop
    cHeatAdd = .1  # heat added per button per loop
    transition(heatCol(0), 1/20)
    drawInterval = 1/20
    while(True):
        nextDrawTime = time.time()+drawInterval

        heldKeys = grid.readKeys()[1]
        if(modeBtn in heldKeys):
            return
        for x, y in heldKeys:
            pixelGrid[y][x] += cHeatAdd*(1000-pixelGrid[y][x])
        newGrid = pixelGrid.copy()

        # calculate heat transfer
        for y in range(8):
            for x in range(8):
                for ax, ay in adjGrid[y][x]:
                    # weighted average with neighbor
                    newGrid[y][x] += cHeatTrans * \
                        (pixelGrid[ay][ax] - pixelGrid[y][x])
                # gradually loose heat, to prevent saturation
                newGrid[y][x] *= cHeatLoss
                newGrid[y][x] = min(max(0, newGrid[y][x]), 255)
                grid.drawPixel(x, y, heatCol(round(newGrid[y][x])))
        pixelGrid = newGrid
        grid.stripShow()
        # for row in newGrid:
        #     print(" ".join(["{:02X}".format(int(round(i))) for i in row]))

        while(time.time() < nextDrawTime):
            pass


def simon():
    """Plays the simon game"""
    sColors = []
    sColors.append(rgbColor(255, 0, 0))  # red
    sColors.append(rgbColor(0, 255, 0))  # blue
    sColors.append(rgbColor(0, 0, 255))  # green
    sColors.append(rgbColor(200, 200, 0))  # yellow-green

    simonSequence = []
    while(True):  # looping until modeBtn
        restart = False
        time.sleep(.5)
        grid.setCol()
        simonSequence.append((random.randint(0, 1), random.randint(0, 1)))
        # showing the sequence
        for cx, cy in simonSequence:
            [grid.drawPixel(cx*4 + x+1-cx, cy*4 + y+1-cy, sColors[cy*2+cx])
             for x in range(3) for y in range(3)]
            grid.stripShow()
            time.sleep(.4)
            grid.setCol(c=0)
            grid.stripShow()
            time.sleep(.2)
        for cx, cy in simonSequence:
            # waiting for keypress
            while(True):
                keys = grid.readKeys()[0]
                if(keys):
                    if(modeBtn in keys):
                        return
                    # lose if key not in right region
                    x, y = keys[0]
                    if(floor(x/4) != cx or floor(y/4) != cy):
                        restart = True
                        break
                    else:  # move to next in sequence for correct keypress
                        [grid.drawPixel(cx*4 + x, cy*4 + y, sColors[cy*2+cx])
                         for x in range(4) for y in range(4)]
                        grid.stripShow()
                        time.sleep(.5)
                        grid.setCol(0)
                        grid.stripShow()
                        break
            if(restart):  # break for loop
                break
        if(restart):  # restart game
            time.sleep(.7)
            cx, cy = simonSequence[-1]
            [grid.drawPixel(cx*4 + x+1-cx, cy*4 + y+1-cy, sColors[cy*2+cx])
             for x in range(3) for y in range(3)]
            grid.stripShow()
            time.sleep(.6)
            grid.setCol()
            font.drawNum(len(simonSequence)-1, colors["red"])
            grid.stripShow()
            time.sleep(1.5)
            simonSequence = []


def paintTTT(tGrid):
    for x, row in enumerate(tGrid):
        for y, val in enumerate(row):
            col = "off" if val == 0 else ("red" if val == 1 else "blue")
            grid.drawPixel(x*3, y*3, colors[col])
            grid.drawPixel(x*3+1, y*3, colors[col])
            grid.drawPixel(x*3, y*3+1, colors[col])
            grid.drawPixel(x*3+1, y*3+1, colors[col])


plrWins = [0, 0, 0]


def checkWin(tGrid, winSets):
    """count of wins for each player, index 0 is draws"""

    for test in winSets:
        cols = []
        for x, y in test:
            cols.append(tGrid[x][y])
        if(cols[0] != 0 and cols[0] == cols[1] and cols[0] == cols[2]):
            soln = test
            wCol = cols[0]
            break
    else:
        return False
    wGrid = [[0, 0, 0] for __ in range(3)]
    blank = [[0, 0, 0] for __ in range(3)]
    for x, y in soln:
        wGrid[x][y] = wCol
    for i in range(3):
        paintTTT(wGrid)
        grid.stripShow()
        time.sleep(.3)
        paintTTT(blank)
        grid.stripShow()
        time.sleep(.3)
    time.sleep(.3)
    plrWins[wCol] += 1
    col = "red" if wCol == 1 else "blue"
    grid.setCol()
    font.drawNum(plrWins[wCol], colors[col])
    grid.stripShow()
    time.sleep(1)
    return True


def tictactoe():
    drawInterval = 1/20
    global plrWins
    plrWins = [0, 0, 0]
    winSets = []
    winSets.append([(0, 0), (1, 1), (2, 2)])
    winSets.append([(2, 0), (1, 1), (0, 2)])
    for i in range(3):
        winSets.append([(0, i), (1, i), (2, i)])
        winSets.append([(i, 0), (i, 1), (i, 2)])

    plrToggle = 1
    while(True):
        tGrid = [[0, 0, 0] for __ in range(3)]
        bttnCount = 0
        for i in range(8):
            grid.drawPixel(i, 2, colors["white"])
            grid.drawPixel(i, 5, colors["white"])
            grid.drawPixel(2, i, colors["white"])
            grid.drawPixel(5, i, colors["white"])
        paintTTT(tGrid)
        grid.stripShow()
        grid.readKeys()  # consume input
        while(True):
            nextDrawTime = time.time()+drawInterval
            newKeys = grid.readKeys()[0]
            if(len(newKeys) > 0):
                x, y = newKeys[0]
                if((x, y) == modeBtn):
                    return
                if(x in (2, 5) or y in (2, 5)):
                    continue
                x = floor(x/3)
                y = floor(y/3)
                # print(x,y)
                if(tGrid[x][y] == 0):
                    tGrid[x][y] = plrToggle
                    plrToggle = 1 if plrToggle == 2 else 2
                    bttnCount += 1
                paintTTT(tGrid)
                grid.stripShow()
                if(checkWin(tGrid, winSets)):
                    break
                if(bttnCount == 9):
                    time.sleep(.6) 
                    grid.setCol()
                    plrWins[0] += 1
                    font.drawNum(plrWins[0], colors["white"])
                    grid.stripShow()
                    time.sleep(1) 
                    break
            while(time.time() < nextDrawTime):
                pass


def ysLogo():
    grid.drawPixel(0, 1, colors["orange"])
    grid.stripShow()

    while(True):
        exit = grid.readKeys()[0]

        for x, y in exit:
            if x == 0 and y == 0:
                return


def mainLoop():
    """dispatches control to different operating modes, resetting the grid in between"""
    mode = 0
    modes = [pressCol, wave, simon, tictactoe, rainbow, heatMap]

    while(True):
        # print("Entering mode {}".format(mode))
        modes[mode]()
        # print("exit mode {}".format(mode))
        mode = (mode+1) % len(modes)
        transition(col=0x888888)
        transition(0)
        grid.setCol()
        time.sleep(.25)


if __name__ == '__main__':
    # init either board or tkinter
    print('Starting LED Board')
    print('Press Ctrl-C to quit.')
    print("Ready")
    try:
        grid.startup()
        mainLoopThread = threading.Thread(
            name="funcLoop", target=mainLoop, daemon=True)
        mainLoopThread.start()
        grid.block()
    except:
        grid.setCol()
