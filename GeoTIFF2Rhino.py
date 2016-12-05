# Minimal classes for loading a 16bpp Grayscale TIF and TFW files
# Allows pixel level sampling and basic (somewhat inaccurate) pixel to world coordinate transformations
#
# Author: Dan Furie
# https://github.com/djfurie/GeoTIFF2Rhino

from struct import unpack


class TFWFile:
    """ Loads TFW world files and performs coordinate transforms """

    def __init__(self, tfw_path):
        """
        :param tfw_path: Path to the TFW file to parse
        """
        self.x_res = None
        self.y_res = None
        self.origin_lat = None
        self.origin_lon = None
        self.parse_tfw(tfw_path)

    def parse_tfw(self, path):
        """
        Parses the supplied TFW file

        :param path: Path to the TFW file to parse
        :return: None
        """
        f = open(path)

        self.x_res = float(f.readline())
        f.readline() # Rotation Parameter
        f.readline() # Rotation Parameter
        self.y_res = float(f.readline())
        self.origin_lat = float(f.readline())
        self.origin_lon = float(f.readline())

        f.close()

    def pixel_to_world(self, x, y):
        """
        Transforms a pixel (x,y) coordinate to surface coordinates in meters
        This function assumes that pixel resolution is defined in arc-degrees, and approximates
        distance between pixels by assuming 1 arc-degree = 110km (which is true for latitude at the equator)

        :param x: X Pixel coordinate from the associated GeoTIFF
        :param y: Y Pixel coordinate from the associated GeoTIFF
        :return: (x, y) coordinate in meters, scaled according to the TFW file
        """
        # Res is scaled in degrees, so we can only approximate
        # the distance in meters for Rhino
        # 1 degree latitude is 110km at the equator
        x1 = self.x_res * 110e3 * x
        y1 = self.y_res * 110e3 * y
        return x1, y1

    def latlon_to_pixel_coord(self, lat, lon):
        """ Takes in a latitude and longitude and returns the pixel coordinates for that piece of land
        :param lat: Latitude in degrees
        :param lon: Longitude in degrees
        :return: (x,y) coordinates of the pixels in the GeoTIFF corresponding to the given lat,lon
        """
        offset_lat = lat - self.origin_lat
        offset_lon = lon - self.origin_lon

        x = offset_lat / self.x_res
        y = offset_lon / self.y_res

        return x, y


class TIFFFile:
    """ This TIFF parsing class does the bare minimum for getting pixel sample data from a GeoTIFF file
    The only currently supported format is 16bpp Grayscale using tiles
    No advanced features of the TIFF file format are used

    Args:
        tif_path (str): Path to the *.tif file to load
    """

    def __init__(self, tif_path):
        """
        Parses a TIF file so that pixel data can be read
        :param tif_path: Path to the TIF file to use
        """
        self.file_path = tif_path
        self.f = open(tif_path, 'rb')

        self.tiff_id = None
        self.tiff_version = None
        self.tiff_IFDOffset = None
        self.tiff_BitsPerSample = None
        self.tiff_tilesAcross = None
        self.tiff_tilesDown = None
        self.tiff_tileWidth = None
        self.tiff_tileLength = None
        self.tiff_tileOffsets = None
        self.tiff_ImageWidth = None
        self.tiff_ImageHeight = None

        self.parse_header_info()

    def parse_header_info(self):
        """
        Reads in the header information from a TIF file
        :return: None
        """
        if self.f:
            # Always start at the beginning of the file
            self.f.seek(0)

            # Read in the basic header information
            (self.tiff_id, self.tiff_version, self.tiff_IFDOffset) = unpack('hhi', self.f.read(8))

            # Seek to the start of the tags data
            self.f.seek(self.tiff_IFDOffset)

            # Determine the number of tags present
            (num_tags,) = unpack('H', self.f.read(2))

            # Loop through the available tags
            for tag in range(0, num_tags):
                (tag_id, data_type, data_count, data_offset) = unpack('HHLL', self.f.read(12))

                # These tag_id's are specified in the TIFF spec: http://www.fileformat.info/format/tiff/egff.htm#TIFF.FO
                if tag_id == 256:
                    self.tiff_ImageWidth = int(data_offset)
                elif tag_id == 257:
                    self.tiff_ImageHeight = int(data_offset)
                elif tag_id == 258:
                    self.tiff_BitsPerSample = int(data_offset)
                elif tag_id == 322:
                    self.tiff_tileWidth = int(data_offset)
                elif tag_id == 323:
                    self.tiff_tileLength = int(data_offset)
                elif tag_id == 324:
                    # Save where the file pointer currently is
                    current_file_position = self.f.tell()
                    self.f.seek(data_offset)

                    # Populate a list with all the tile offsets
                    # Tiles are ordered left to right, top to bottom
                    self.tiff_tileOffsets = []
                    for i in range(0, data_count):
                        data = self.f.read(4)
                        (offset,) = unpack('L', data)
                        self.tiff_tileOffsets.append(offset)

                    # Restore the file pointer to where it was
                    self.f.seek(current_file_position)

            (next_idf_offset,) = unpack('i', self.f.read(4)) # Assume this is zero for basic usages

            # Calculate the image dimensions in terms of number of tiles- useful for later calculation
            self.tiff_tilesAcross = (self.tiff_ImageWidth + (self.tiff_tileWidth - 1)) / self.tiff_tileWidth
            self.tiff_tilesDown = (self.tiff_ImageHeight + (self.tiff_tileLength - 1)) / self.tiff_tileLength

    def get_pixel_val(self, x, y):
        """
        :param x: Pixel X coordinate
        :param y: Pixel Y coordinate
        :return: Signed 16-bit integer value representing the grayscale value of the pixel
        """
        # Figure out which tile the pixel is in
        tile_x = x / self.tiff_tileWidth
        tile_y = y / self.tiff_tileLength

        # Figure out the start of the tile data
        tile_idx = tile_y * self.tiff_tilesAcross + tile_x
        tile_offset = self.tiff_tileOffsets[tile_idx]

        # Now get the pixel within the tile
        xt = x % self.tiff_tileWidth
        yt = y % self.tiff_tileLength

        # Calculate the index within the tile
        pixel_idx = (yt * self.tiff_tileWidth + xt) * 2 + tile_offset
        self.f.seek(pixel_idx)
        (pixel_val,) = unpack('h', self.f.read(2))

        return pixel_val
