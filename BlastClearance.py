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


# This function is used to join two tabled
# Return the joined feature layer
def join_features(table_1, table_2, field_string_p):
    joined_table = arcpy.AddJoin_management(table_1, field_string_p, table_2, field_string_p, "KEEP_COMMON")
    arc_output(f"{table_1} and {table_2} joined using {field_string_p}")

    return joined_table


# This function is used to check whether the blocks exist in the BlockInventory database
def blocks_check(block_list_p, sde_table_p, search_field_p):
    # Empty error list to which all non-existent block numbers are added
    error_list = []
    # TODO: make field a parameter
    field = [search_field_p]
    for block in block_list_p:
        where_clause = f"{search_field_p} = '{block}'"
        with arcpy.da.SearchCursor(sde_table_p, field, where_clause) as cur:
            try:
                cur.next()
                arc_output(f"Block {block} Found")
            except:
                error_list.append(block)
                arc_output(f"Block {block} NOT Found")

    # If there is any data in the error list, arcgis pro must provide the user with an error message
    # containing the block numbers which must be checked.
    if len(error_list) > 0:
        if len(error_list) == 1:
            arcpy.AddError(f"Block {error_list[0]} does not exist.\nPlease contact the Blasting Team.")
        else:
            error_string = "The following blocks do not exist:\n\n"
            for count, error_block in enumerate(error_list):
                error_string += "\t" + str(error_block) + "\n"
            error_string += "\nPlease contact the Blasting Team."
            arcpy.AddError(error_string)


# TODO: Create string for SQL Function, don't use file
# TODO: Create function that joins tables - use this function to return the join
# TODO: Create function that creates a dictionary which will be used to detect whether blocks exist or not.


# This function is used to select the blocks which need to be blasted
def blocks_to_blast(sde_block_status_p, sde_block_p, search_clause_p, scratch_gdb_p, block_spat_ref_p):
    # Join block status and block tables in the BlockInventory Database
    first_join = arcpy.AddJoin_management(sde_block_status_p, "BlockId", sde_block_p, "BlockId", "KEEP_COMMON")
    arc_output("First Join Succesful")
    first_join = join_features(sde_block_status_p, sde_block_p, "BlockId")

    # TODO: Test Print - Print Fields
    join_fields = arcpy.ListFields(first_join)
    for field in join_fields:
        arc_output(field.name)

    # TODO: Finalize layer names
    initial_blocks = arcpy.MakeFeatureLayer_management(first_join, "CHANGELATER", search_clause_p)

    # TODO: Test output of feature class to see whether blocks were selected
    with arcpy.EnvManager(outputCoordinateSystem=block_spat_ref_p):
        arcpy.FeatureClassToFeatureClass_conversion(initial_blocks, scratch_gdb_p, "TESTBLOCKS")


# Main Program

# Workspace Variables
workspace = new_path()
# workspace = r"S:\Mining\MRM\SURVEY\DME\NEWGME\ARC\TRIAL_PROJECTS\BlastClearance"
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

# Check whether blocks exist in the Blocks table
blocks_check(block_list_p=block_input,
             sde_table_p=sde_block_path,
             search_field_p="Number")

# Join the BlockStatus and Blocks features
block_status_and_block = join_features(sde_block_status_path, sde_block_path, "BlockId")


# TODO: Create function
# Create a search clause file
# Generate Search Query using list
# First clear the search text file
with open("searchfile.txt", "w") as file:
    file.write("")

# Create the search parameters - append to a text file
with open("searchfile.txt", "a") as file:
    if len(block_input) > 1:
        counter = 1
        file.write(f"(BlockInventory.dbo.Block.Number = '{block_input[0]}' OR ")
        while counter < len(block_input) - 1:
            file.write(f"BlockInventory.dbo.Block.Number = '{block_input[counter]}' OR ")
            counter += 1
        file.write(f"BlockInventory.dbo.Block.Number = '{block_input[len(block_input) - 1]}')")
    elif len(block_input) == 1:
        file.write(f"BlockInventory.dbo.Block.Number = '{block_input[0]}'")
    file.write(" AND (BlockInventory.dbo.Block.CurrentStatusId = BlockInventory.dbo.BlockStatus.StatusId)")

# Generate the Search Clause for use in Make Feature Layer
f = open("searchfile.txt", "r")
if f.mode == "r":
    search_clause = f.read()
f.close()

# TODO Test print
arc_output(search_clause)



# TODO: Uncomment after testing Dictionaries
# blocks_to_blast(sde_block_status_p=sde_block_status_path,
#                 sde_block_p=sde_block_path,
#                 search_clause_p=search_clause,
#                 scratch_gdb_p=scratch_gdb,
#                 block_spat_ref_p=block_spat_ref)

