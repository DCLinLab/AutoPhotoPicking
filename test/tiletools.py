"""
File: TileTools.py
Version: 0.1

This is a collection of little python functions that can be used to modify 
a ZEN Experiment containing one (!) TileRegion yet.
It supposed to be used to automatically adapt a TileRegion to the size of a detected ROI via Image Analysis
inside a RareEvent Detection workflow, but can be used anywhere from a OAD macro

Important : Requires ZEN 2012 SP2 (DVD52)

Example usage from an OAD macro:

import sys
# path to the folder containing tools scripts --> this depends on your machine, but the folder can be placed anywhere ...
scriptfolder = r'C:\Users\...\Documents\Carl Zeiss\ZEN\External_Python_Scripts_for_OAD'
sys.path.append(scriptfolder)

# import the tool script
import TileTools as tt

# load the experiment
exp = Zen.Acquisition.Experiments.GetByName('Tile_Scan.czexp')
tt.ShowTileInfoFromExperiment(exp)
# modify XY(Z) position of the Tile
exp_mod = tt.ModifyXYZ(exp,-4000,-6000, 300)
# modify contour size --> tiles will adapt automatically
exp_mod = tt.ModifyTileSize(exp_mod, 4000, 2000)
# execute the experiment
#Output_Images = Zen.Acquisition.Execute(exp)

"""

# Requirem import stuff
import clr

clr.AddReferenceByPartialName("Zeiss.Micro.Acquisition.Tiles")
from Zeiss.Micro.Acquisition import RegionsSetup, TilesSetup

clr.AddReferenceByPartialName("Zeiss.Micro.LM.Acquisition")
from Zeiss.Micro.Acquisition import MultiTrackSetup

clr.AddReferenceByPartialName("WindowsBase")
from System.Windows import Point
from System.Windows import Size


def GetTileSetups(TileExp):
    # get the first experiment block
    firstblock = TileExp.Core.ExperimentBlocks[0]
    # get the RegionsSetup
    regionssetup = firstblock.GetDimensionSetup(RegionsSetup)
    # get all tracks
    tilessetup = regionssetup.GetDimensionSetup(TilesSetup)
    multiTrackSetup = tilessetup.GetDimensionSetup(MultiTrackSetup)
    # get number of Tile Regions and Tiles
    NumberTileRegions = regionssetup.SampleHolder.TileRegions.Count
    NumberTiles = regionssetup.SampleHolder.TilesCount

    return firstblock, regionssetup, tilessetup, NumberTileRegions, NumberTiles


# Show the tile information using the tileregion object
def ShowTileInfo(tileregion):
    # print 'Tile Center Position XYZ : ', tileregion.Contour, tileregion.CenterPosition.Y, tileregion.Z
    print
    'Tile Center Position XYZ : ', tileregion.CenterPosition.X, tileregion.CenterPosition.Y, tileregion.Z
    print
    'Tile Contour Size        : ', tileregion.ContourSize.Width, tileregion.ContourSize.Height
    print
    'Tile Size XY             : ', tileregion.Columns, ' x ', tileregion.Rows


# Show tile information using the ZEN experiment file
def ShowTileInfoFromExperiment(TileExp):
    [firstblock, regionssetup, tilessetup, NumberTileRegions, NumberTiles] = GetTileSetups(TileExp)

    # show information
    for i in range(0, NumberTileRegions, 1):
        tileregion = regionssetup.SampleHolder.TileRegions[i]
        print
        'Tile Information'
        ShowTileInfo(tileregion)


# modify Tile XYZ Position
def ModifyXYZ(*args):
    TileExp = args[0]  # 1st argument must be the Tile Experiment
    NewX = args[1]  # 2nd argument must be new X-Position
    NewY = args[2]  # 3nd argument must be new Y-Position
    # the Z-Position of the Tile is optional
    if len(args) == 4:
        NewZ = args[3]  # 4th argument can be the new Z-Position; if not used, the Z is not modified

    [firstblock, regionssetup, tilessetup, NumberTileRegions, NumberTiles] = GetTileSetups(TileExp)

    # change the XYZ position of the tile region
    for i in range(0, NumberTileRegions, 1):

        tileregion = regionssetup.SampleHolder.TileRegions[i]
        tileregion.CenterPosition = Point(NewX, NewY)

        # set the new z-Value for the current tile region
        if len(args) == 4:
            tileregion.Z = NewZ
        # show new XYZ positions
        print
        'New Tile Information'
        ShowTileInfo(tileregion)

    return TileExp


def ModifyTileSize(TileExp, NewSizeX, NewSizeY):
    [firstblock, regionssetup, tilessetup, NumberTileRegions, NumberTiles] = GetTileSetups(TileExp)

    # change the Contour --> Tile Number will be adapted automatically
    for i in range(0, NumberTileRegions, 1):
        tileregion = regionssetup.SampleHolder.TileRegions[i]
        # modify the contour size
        tileregion.ContourSize = Size(NewSizeX, NewSizeY)
        # show updated tile information
        print
        'New Tile Information'
        ShowTileInfo(tileregion)

    return TileExp