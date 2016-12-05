# GeoTIFF2Rhino
Reads in a GeoTIFF file and generates a correctly scaled Rhino 5 point cloud
Currently the script only supports 16-bit Grayscale TIFs using Tiles

Place both files into C:\Users\<your username>\AppData\Roaming\McNeel\Rhinoceros\5.0\scripts

Start Rhino, go to Tools | PythonScript | Run... and select the geotiff2rhino_example.py script.

Prompts should come up to:
 - Select the *.tif file
 - Select the *.tfw file
 - Specify a starting pixel for the data to import
 - Specify an ending pixel for the data to import
 
 If the script completes, you should end up with a new layer and a point cloud representing the GeoTIFF data
