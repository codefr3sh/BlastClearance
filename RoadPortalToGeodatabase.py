# This script is used to export roads from the AngloAmerican Portal to a Geodatabase on the S:\Drive
# Created by: Philip van Schalkwyk
# Last updated: 2022-12-09

# TODO: Automate with Task Scheduler
# TODO: Think about where Geodatabase will be stored
# TODO: How often will script be run
# TODO: Consider backups of previous geodatabases
# TODO: Error handling - portal login

# Imports
import arcpy
from arcgis import GIS
import os
from datetime import datetime


# Functions
# This function checks for an active portal connection
# If none is found, return an error message
# If portal is active, return the gis and portal_hostname variables
def check_portal():
    try:
        gis = GIS("pro")
        portal_hostname = gis.properties.portalHostname
        arc_output("Checking Portal Connection")
        if portal_hostname != "gis.angloamerican.com/portal":
            arcpy.AddError("Not signed into the correct portal")
            quit()
        else:
            arc_output("Portal Connection Validated")
            return gis, portal_hostname
    except:
        arcpy.AddError("Not signed in to any Portal")
        quit()


# This function provides a standard message output to users using ArcGIS Pro
def arc_output(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    arcpy.AddMessage(f"---{timestamp}: {message} ---")


def download_as_fgdb(item_list, backup_location):
    for item in item_list:
        try:
            if 'View Service' in item.typeKeywords:
                print(item.title + " is view, not downloading")
            else:
                print("Downloading " + item.title)
                version = datetime.datetime.now().strftime("%d_%b_%Y")
                result = item.export(item.title + "_" + version, "File Geodatabase")
                result.download(backup_location)
                result.delete()
                print("Successfully downloaded " + item.title)
        except:
            print("An error occurred downloading " + item.title)
    print("The function has completed")

# Main Program

# Declare Variables

# Hosted Feature Variables
road_feature_online = "https://gis.angloamerican.com/hosting/rest/services/Sishen/Sishen_Infrastructure/FeatureServer/10"

# Workspace Variables
workspace = r"S:\Mining\MRM\SURVEY\DME\NEWGME\ARC\PORTAL_BACKUPS"
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True
backup_geodatabase = os.path.join(workspace, "PortalBackups.gdb")
road_fc = os.path.join(backup_geodatabase, "Road_Edge")


# Execute Script

gis, portal_hostname = check_portal()

# search_list = ["Sishen Safety", "Sishen Hydrology", "Sishen Survey", "Sishen Land Use and Land Cover", "Sishen Geology",
#                "Sishen Mining", "Sishen Mining Lease", "Sishen Areas of Responsibility", "Sishen Infrastructure"]
# # search_list = "Sishen Geology"
# export_list = []
# search_items = gis.content.search(query="Sishen", item_type="Feature Service", max_items=10000)

# for feature_service in search_items:
#     if feature_service.title in search_list:
#         arc_output(feature_service)
#         export_list.append(feature_service)
#         for layer in feature_service.layers:
#             arc_output(layer)
#
# print(export_list)


# Copy Feature later to Feature
arc_output("Copying Features")
arcpy.CopyFeatures_management(road_feature_online, road_fc)
arc_output("Features Copied")
arc_output("Renaming 'Level_' to 'Level'")
arcpy.AlterField_management(road_fc, "Level_", "Level")
arc_output("Renamed 'Level_' to 'Level'")
