# Example script for loading a GeoTIFF into Rhino as a PointCloud object
#
# Author: Dan Furie
# https://github.com/djfurie/GeoTIFF2Rhino

import GeoTIFF2Rhino
import rhinoscriptsyntax as rs
from System.Drawing import Color

def main():
    tif_path = rs.OpenFileName('Choose TIF file', filter='TIF Files|*.tif', extension='.tif')

    if not tif_path:
        print 'No TIF file path given!'
        return

    tfw_path = rs.OpenFileName('Choose TFW file', filter='TFW Files|*.tfw', extension='.tfw')

    if not tfw_path:
        print 'No TFW file path given!'
        return

    tiff_file = GeoTIFF2Rhino.TIFFFile(tif_path)
    tfw_file = GeoTIFF2Rhino.TFWFile(tfw_path)

    start_x = rs.GetInteger('Upper Left X Pixel Coordinate', 0, 0, tiff_file.tiff_ImageWidth)
    start_y = rs.GetInteger('Upper Left Y Pixel Coordinate', 0, 0, tiff_file.tiff_ImageHeight)

    end_x = rs.GetInteger('Lower Right X Pixel Coordinate', tiff_file.tiff_ImageWidth, 0, tiff_file.tiff_ImageWidth)
    end_y = rs.GetInteger('Lower Right Y Pixel Coordinate', tiff_file.tiff_ImageHeight, 0, tiff_file.tiff_ImageHeight)

    # Figure out the center of our slice of land
    center_x = (start_x + end_x) / 2
    center_y = (start_y + end_y) / 2
    (center_x, center_y) = tfw_file.pixel_to_world(center_x, center_y)
    print center_x, center_y

    # Sample all of the pixels in the desired region of the TIF
    # and generate a point cloud from them
    v = []
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            z1 = tiff_file.get_pixel_val(x, y)

            # Only use valid pixel data
            if z1 != 32767:
                (x1, y1) = tfw_file.pixel_to_world(x, y)

                #Recenter the points about the origin
                x1 -= center_x
                y1 -= center_y
                v.append(x1)
                v.append(y1)
                v.append(z1)

    pc_layer = rs.AddLayer('Imported GeoTIFF PointCloud', Color.SandyBrown)
    rs.CurrentLayer(pc_layer)
    rs.AddPointCloud(v)

if __name__ == "__main__":
    main()