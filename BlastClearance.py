# Investigate the use of the BlockInventory Database to create blast clearance plans

import arcpy
import os


# Functions
# This functions gets the path where the '.aprx' file is located and returns the working directory
def new_path():
    aprx = arcpy.mp.ArcGISProject(r"CURRENT")
    pathname = os.path.dirname(aprx.filePath)
    full_path = os.path.abspath(pathname)
    return full_path


# This function provides a standard message output to users using ArcGIS Pro
def arc_output(message_p):
    arcpy.AddMessage(f"--- {message_p} ---")


# Main Program

# Workspace Variables
# TODO: Uncomment once testing is done
# workspace = new_path()
workspace = r"S:\Mining\MRM\SURVEY\DME\NEWGME\ARC\TRIAL_PROJECTS\BlastClearance"
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True  # TODO: Change to False after testing
working_gdb = os.path.join(workspace, 'BlastClearance.gdb')
scratch_gdb = os.path.join(workspace, 'scratch.gdb')
archive_gdb = os.path.join(workspace, 'Archive.gdb')
block_inventory_sde = r"S:\Mining\MRM\SURVEY\DME\NEWGME\ARC\SDE_CONNECTIONS\BlockInventory.sde"

# User Input Parameters
block_input = arcpy.GetParameter(0)

# TODO: Test printouts
arc_output(block_input)


# TODO: Create function
# Create a search clause file  # TODO: Change PushBackPolygon to the relevant term
# Generate Search Query using list
# First clear the search text file
with open("searchfile.txt", "w") as file:
    file.write("")

# Create the search parameters - append to a text file
with open("searchfile.txt", "a") as file:
    if len(block_input) > 1:
        counter = 1
        file.write("BlockInventory.dbo.PushBackPolygon.PushBackPolygonId = {} OR ".format(block_input[0]))
        while counter < len(block_input) - 1:
            file.write("BlockInventory.dbo.PushBackPolygon.PushBackPolygonId = {} OR ".format(block_input[counter]))
            counter += 1
        file.write("BlockInventory.dbo.PushBackPolygon.PushBackPolygonId = {}".format(
            block_input[len(block_input) - 1]))
    elif len(block_input) == 1:
        file.write("BlockInventory.dbo.PushBackPolygon.PushBackPolygonId = {}".format(block_input[0]))

# Generate the Search Clause for use in Make Feature Layer
f = open("searchfile.txt", "r")
if f.mode == "r":
    search_clause = f.read()
f.close()

# TODO Test print
print(search_clause)