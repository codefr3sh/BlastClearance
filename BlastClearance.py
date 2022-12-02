# Investigate the use of the BlockInventory Database to create blast clearance plans

import arcpy
import os

# TODO: Add functionality for file search
# TODO: CAD Export using Seed File for Symbology
# TODO: Create symbology layers
# TODO: Blast ID table
# TODO: Separate script and tools for when additional features such as misfires or toes must be added


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
    arc_output(f"{table_1.split('dbo.')[-1]} and {table_2.split('dbo.')[-1]} Tables joined using {field_string_p}")

    return joined_table


# This function is used to check whether the blocks exist in the BlockInventory database
def blocks_check(block_list_p, sde_table_p, search_field_p):
    arc_output("Checking if blocks exist in the Database...")
    # Empty error list to which all non-existent block numbers are added
    error_list = []
    field = [search_field_p]

    # Loop through the blocks as provided by the user
    for block in block_list_p:
        # Search criteria
        where_clause = f"{search_field_p} = '{block}'"
        # Initiate a Search Cursor
        with arcpy.da.SearchCursor(sde_table_p, field, where_clause) as cur:
            # Provide output if the block is found in the table
            try:
                cur.next()
                arc_output(f"Block {block} Found")
            # Add block number to the error list if it is not found in the table
            except:
                error_list.append(block)
                arc_output(f"Block {block} NOT Found")
    arc_output("Block Check Completed...")

    # If there is any data in the error list, arcgis pro must provide the user with an error message
    # containing the block numbers which must be checked.
    # TODO: Try / Except / Custom Error
    if len(error_list) > 0:
        if len(error_list) == 1:
            arcpy.AddError(f"Block {error_list[0]} does not exist.\nPlease contact the Blasting Team.")
        else:
            error_string = "The following blocks do not exist:\n\n"
            for error_block in error_list:
                error_string += "\t" + str(error_block) + "\n"
            error_string += "\nPlease contact the Blasting Team."
            arcpy.AddError(error_string)
        quit()


# This function creates the SQL string to select blocks
# Return the Search String
def block_search_sql(block_list_p, block_number_p, block_currentstatus_p, blockstatus_status_p):
    search_string = ""
    if len(block_list_p) == 1:
        search_string += f"{block_number_p} = '{block_list_p[0]}'"
    else:
        for count, block in enumerate(block_list_p):
            if count == 0:
                search_string += f"({block_number_p} = '{block}' OR "
            elif count == len(block_list_p)-1:
                search_string += f"{block_number_p} = '{block}')"
            else:
                search_string += f"{block_number_p} = '{block}' OR "
        search_string += f" AND ({block_currentstatus_p} = {blockstatus_status_p})"

    return search_string


# This function is used to display fields within the selected table
# This is useful for testing and troubleshooting purposes
def display_fields(table_p):
    arcpy.AddMessage(f"Fields in table {table_p}:")
    join_fields = arcpy.ListFields(table_p)
    for field in join_fields:
        arcpy.AddMessage(field.name)
    arc_output("Field Display Complete")


# This function is used to select the blocks which need to be blasted
def blocks_to_blast(block_feature_p, search_clause_p, scratch_gdb_p, block_spat_ref_p):

    # TODO: Finalize layer names
    arc_output("Creating Temporary Block Layer")
    initial_blocks = arcpy.MakeFeatureLayer_management(block_feature_p, "CHANGELATER", search_clause_p)
    arc_output("Temporary Block Layer Created")

    # TODO add buffers here

    # TODO: Test output of feature class to see whether blocks were selected
    arc_output("Creating Block Feature Class")
    with arcpy.EnvManager(outputCoordinateSystem=block_spat_ref_p):
        arcpy.FeatureClassToFeatureClass_conversion(initial_blocks, scratch_gdb_p, "TESTBLOCKS")
    arc_output("Block Feature Class Created")


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

# Check whether blocks exist in the Blocks table
blocks_check(block_list_p=block_input,
             sde_table_p=sde_block_path,
             search_field_p="Number")

# Join the BlockStatus and Blocks features
block_status_and_block = join_features(sde_block_status_path, sde_block_path, "BlockId")

# Create the search Query which will be used to select blocks from the joined feature layer
search_query = block_search_sql(block_list_p=block_input,
                                block_number_p="BlockInventory.dbo.Block.Number",
                                block_currentstatus_p="BlockInventory.dbo.Block.CurrentStatusId",
                                blockstatus_status_p="BlockInventory.dbo.BlockStatus.StatusId")


# Select Blocks that will be blasted
blocks_to_blast(block_feature_p=block_status_and_block,
                search_clause_p=search_query,
                scratch_gdb_p=scratch_gdb,
                block_spat_ref_p=block_spat_ref)

# TODO Buffer FC with attribute for clearance type, e.g. machine & People
