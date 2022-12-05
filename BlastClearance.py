# Investigate the use of the BlockInventory Database to create blast clearance plans

import arcpy
import os
from datetime import datetime


# TODO: Add functionality for file input (txt file, one block on each line)
# TODO: Choose whether file or list input is used
# TODO: Sanitize inputs (remove "/" if any)
# TODO: Create symbology layers
# TODO: Assign layer symbology to feature class, if possible.
# TODO: Each user has own Project file, hardcode master geodatabase, investigate feature service later on
# TODO: Identify mining area (North / South/ Lylyveld south):
#       Block join to Level using "LevelId"
#       Level join to ElevationDatum using "ElevationDatumId"
#       ElevationDatum - use field "Name"
# TODO: CAD Export using Seed File for Symbology
# TODO: Separate script and tools for when additional features such as misfires or toes must be added
# TODO: Data management assign blast id to user, blocks, clearance zones
# TODO: Single feature class to identify clearance zones
# TODO: Export cad file to relevant folder, e.g. blast > YYYY > X_MMM > YYYYMMDDHHMMSS_USER
#       Check if folder exists, f not, create it
# TODO: Add Blast ID to folder name
# TODO: Master DGN file per Mining Zone for reference purposes
# TODO: Delete Scratch features
# TODO: Static seed file location
# TODO: Test blast clearance ID as hosted table


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
            elif count == len(block_list_p) - 1:
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
def blocks_to_blast(block_feature_p, search_clause_p):
    # TODO: Finalize layer names
    arc_output("Creating Temporary Block Layer")
    blocks_selection = arcpy.MakeFeatureLayer_management(block_feature_p, "TempBlocks", search_clause_p)
    arc_output("Temporary Block Layer Created")

    return blocks_selection


# This function creates the temporary blocks feature class and generates the machine and people clearance zones
# TODO: Append temp features to the master features and delete temp features
def find_clearance_zones(spatref_p, blocks_p, scratch_machine_p, scratch_people_p, scratch_gdb_p, machine_rad_p,
                         people_rad_p, machine_single_p, people_single_p):
    with arcpy.EnvManager(outputCoordinateSystem=spatref_p):
        # Create the two temporary buffer features
        arc_output("Creating Machine Clearance Buffer")
        temp_machine_buff_multi = arcpy.Buffer_analysis(blocks_p, scratch_machine_p, f"{machine_rad_p} Meters", "FULL",
                                                  "ROUND", "ALL", None, "PLANAR")
        arc_output("Machine Clearance Buffer Created")
        arc_output("Creating People Clearance Buffer")
        temp_people_buff_multi = arcpy.Buffer_analysis(blocks_p, scratch_people_p, f"{people_rad_p} Meters", "FULL", "ROUND",
                                                 "ALL", None, "PLANAR")
        arc_output("People Clearance Buffer Created")
        # Create the temporary block feature
        arc_output("Creating Temporary Block Feature")
        temp_block_selection = arcpy.FeatureClassToFeatureClass_conversion(blocks_p, scratch_gdb_p, "TEMP_BLOCKS")
        arc_output("Temporary Block Feature Created")

        # Drop Polygons to Single Part Features
        arc_output("Drop to Single Part - Initializing")
        temp_machine_buff = arcpy.MultipartToSinglepart_management(scratch_machine_p, machine_single_p)
        temp_people_buff = arcpy.MultipartToSinglepart_management(scratch_people_p, people_single_p)
        arc_output("Drop to Single Part - Completed")

        # Delete Multipart Features
        arc_output("Deleting Multipart Features")
        arcpy.Delete_management(temp_people_buff_multi)
        arcpy.Delete_management(temp_machine_buff_multi)
        arc_output("Multipart Features Deleted")

        return temp_machine_buff, temp_people_buff, temp_block_selection

        # TODO: uncomment once function is finished
        # Delete the temporary features
        # arc_output("Deleting Temporary Features")
        # arcpy.Delete_management(temp_machine_buff)
        # arcpy.Delete_management(temp_people_buff)
        # arcpy.Delete_management(temp_block_selection)
        # arc_output("Temporary Features Deleted")


# This function is used for data management purposes
# TODO: Elaborate
def data_management(blocks_p, machine_p, people_p, date_sql_p, mine_p, blast_clear_id_p):
    # Create lists to enable iteration for adding and calculating fields
    clearance_list = [machine_p, people_p]
    feature_list = [blocks_p, machine_p, people_p]

    # Create string to display useful output to user (block feature name)
    blocks_p_name = str(blocks_p).split("\\")[-1]

    # Loop through all features and add fields
    for feature in clearance_list:
        # Create string to display useful output to user (feature name)
        feature_name = str(feature).split("\\")[-1]
        arc_output(f"Adding Fields to {feature_name}")
        arcpy.AddFields_management(feature, [["BlastClearId", "TEXT"], ["DateTime", "DATE"], ["Mine", "TEXT"],
                                             ["ClearanceType", "TEXT"], ["Level", "TEXT"]])
        arc_output(f"Fields added to {feature_name}")

    # Add fields to block feature specifically
    arc_output(f"Adding Fields to {blocks_p_name}")
    arcpy.AddFields_management(blocks_p, [["BlastClearId", "TEXT"], ["DateTime", "DATE"], ["Mine", "TEXT"],
                                          ["Level", "TEXT"]])
    arc_output(f"Fields added to {blocks_p_name}")

    # Calculate Fields in all features
    arc_output(f"Calculating Fields")
    for feature in feature_list:
        feature_name = str(feature).split("\\")[-1]
        if feature == blocks_p:
            arcpy.CalculateField_management(feature, "Level", "'500'", "PYTHON3")
            arc_output(f"{feature_name} Level Calculated")
        elif feature == machine_p:
            arcpy.CalculateFields_management(feature, "PYTHON3", [["Level", "'501'"], ["ClearanceType", "'Machine'"]])
            arc_output(f"{feature_name} Level & ClearanceType Calculated")
        elif feature == people_p:
            arcpy.CalculateFields_management(feature, "PYTHON3", [["Level", "'502'"], ["ClearanceType", "'People'"]])
            arc_output(f"{feature_name} Level & ClearanceType Calculated")
        arcpy.CalculateField_management(feature, "DateTime", date_sql_p, "PYTHON3")
        arc_output(f"{feature_name} DateTime Calculated")
        arcpy.CalculateField_management(feature, "Mine", "'" + mine_p + "'", "PYTHON3")
        arc_output(f"{feature_name} Mine Calculated")
        arcpy.CalculateField_management(feature, "BlastClearId", "'" + blast_clear_id_p + "'", "PYTHON3")
        arc_output(f"{feature_name} BlastClearId Calculated")
    arc_output(f"Fields Calculated")

    # Calculate Fields in separate features (CAD Levels used for Exports)


# This features adds a row to the SishenBlasts table to generate a BlastID
def get_blast_id(blast_table_p, mine_p, date_p):
    # Insert a new row to the SishenBlasts Table
    # The Mine as well as Date and time is added
    # BlastClearId is automatically set equal to ObjectId by using an attribute rule
    # TODO: Test to see if attribute rules work on other user's PCs as well
    with arcpy.da.InsertCursor(blast_table_p, ['Mine', 'DateTime']) as cur:
        cur.insertRow([mine_p, date_p])

    # Return the latest BlastClearId and provide output to the user
    # This ID is used to identify different blast clearance plans
    where_clause = "DateTime = timestamp " + "'" + date_p + "'"
    with arcpy.da.SearchCursor(blast_table_p, ['DateTime', 'BlastClearId', 'created_user'], where_clause) as cur:
        for row in cur:
            arc_output(f"Blast Clearance ID >>> {row[1]} <<< assigned to user >>> {row[2]} <<<")
            return str(row[1]), str(row[2])


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
date_string = datetime.today().strftime('%Y%m%d%H%M%S')
arc_date_string = datetime.today().strftime('%m/%d/%Y %I:%M:%S %p')
query_date_string = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
arc_sql_date = "'" + arc_date_string + "'"

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
machine_radius_input = arcpy.GetParameterAsText(1)
people_radius_input = arcpy.GetParameterAsText(2)
mine_input = arcpy.GetParameterAsText(3)

# Derived Variables
sde_block_status_path = os.path.join(block_inventory_sde, "BlockInventory.dbo.BlockStatus")
sde_block_path = os.path.join(block_inventory_sde, "BlockInventory.dbo.Block")
machine_clear_scratch_fc = os.path.join(scratch_gdb, "TEMP_MACHINE")
machine_clear_single_scratch_fc = os.path.join(scratch_gdb, "TEMP_MACHINE_SINGLE")
people_clear_scratch_fc = os.path.join(scratch_gdb, "TEMP_PEOPLE")
people_clear__single_scratch_fc = os.path.join(scratch_gdb, "TEMP_PEOPLE_SINGLE")
sis_blasts_table = os.path.join(working_gdb, "SishenBlasts")


current_blast_id, current_user = get_blast_id(blast_table_p=sis_blasts_table,
                                              mine_p=mine_input,
                                              date_p=query_date_string)

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
selected_blocks = blocks_to_blast(block_feature_p=block_status_and_block,
                                  search_clause_p=search_query)

# Create the buffer & blocks features
machine_buff, people_buff, block_selection = find_clearance_zones(spatref_p=block_spat_ref,
                                                                  blocks_p=selected_blocks,
                                                                  scratch_machine_p=machine_clear_scratch_fc,
                                                                  scratch_people_p=people_clear_scratch_fc,
                                                                  scratch_gdb_p=scratch_gdb,
                                                                  machine_rad_p=machine_radius_input,
                                                                  people_rad_p=people_radius_input,
                                                                  machine_single_p=machine_clear_single_scratch_fc,
                                                                  people_single_p=people_clear__single_scratch_fc)

# Perform some data management tasks, append and export to CAD
data_management(blocks_p=block_selection,
                machine_p=machine_buff,
                people_p=people_buff,
                date_sql_p=arc_sql_date,
                mine_p=mine_input,
                blast_clear_id_p=current_blast_id)
