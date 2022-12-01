# Investigate the use of the BlockInventory Database to create blast clearance plans

import arcpy
import os

# TODO: Error message if block is not found


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


# This function is used to select the blocks which need to be blasted
def blocks_to_blast(sde_block_status_p, sde_block_p, search_clause_p):
    # Join block status and block tables in the BlockInventory Database
    first_join = arcpy.AddJoin_management(sde_block_status_p, "BlockId", sde_block_p, "BlockId", "KEEP_COMMON")
    arc_output("First Join Succesful")

    # TODO: Test Print - Print Fields
    join_fields = arcpy.ListFields(first_join)
    for field in join_fields:
        arc_output(field.name)

    # TODO: Finalize layer names
    initial_blocks = arcpy.MakeFeatureLayer_management(first_join, "CHANGELATER", search_clause_p)


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

# Spatial Reference Variable
spat_ref = "PROJCS['Cape_Lo23_Sishen',GEOGCS['GCS_Cape',DATUM['D_Cape',SPHEROID['Clarke_1880_Arc',6378249.145," \
           "293.466307656]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION[" \
           "'Transverse_Mercator'],PARAMETER['False_Easting',50000.0],PARAMETER['False_Northing',3000000.0]," \
           "PARAMETER['Central_Meridian',23.0],PARAMETER['Scale_Factor',1.0],PARAMETER['Latitude_Of_Origin',0.0]," \
           "UNIT['Meter',1.0]];-5573300 -7002000 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision "

block_spat_ref = "PROJCS['Cape_Lo23_Sishen_Blocks',GEOGCS['GCS_Cape',DATUM['D_Cape',SPHEROID['Clarke_1880_Arc'," \
                 "6378249.145,293.466307656]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]," \
                 "PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',-50000.0]," \
                 "PARAMETER['False_Northing',-3000000.0],PARAMETER['Central_Meridian',23.0]," \
                 "PARAMETER['Scale_Factor',-1.0],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"

# User Input Parameters
block_input = arcpy.GetParameter(0)

# Derived Variables
sde_block_status_path = os.path.join(block_inventory_sde, "BlockInventory.dbo.BlockStatus")
sde_block_path = os.path.join(block_inventory_sde, "BlockInventory.dbo.Block")

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
        file.write(f"BlockInventory.dbo.Block.Number = '{block_input[0]}' OR ")
        while counter < len(block_input) - 1:
            file.write(f"BlockInventory.dbo.Block.Number = '{block_input[counter]}' OR ")
            counter += 1
        file.write(f"BlockInventory.dbo.Block.Number = '{block_input[len(block_input) - 1]}'")
    elif len(block_input) == 1:
        file.write(f"BlockInventory.dbo.Block.Number = '{block_input[0]}'")

# Generate the Search Clause for use in Make Feature Layer
f = open("searchfile.txt", "r")
if f.mode == "r":
    search_clause = f.read()
f.close()

# TODO Test print
arc_output(search_clause)

blocks_to_blast(sde_block_status_p=sde_block_status_path,
                sde_block_p=sde_block_path,
                search_clause_p=search_clause)

