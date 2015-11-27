'''
File holds initialization logic for the simple skin converter.

* Author : Evan Cox coxevan90@gmail.com
'''
# Skonverter module imports
import gui
import methods
import const

# Maya lib imports
import maya.cmds

# Python std lib imports
import os

if const.DEBUG:
	reload( gui )
	reload( methods )
	

def run( ):
	"""
	Runs Skonverter UI.
	"""
	skonverter_window = gui.Skonverter_Interface( )
	skonverter_window.show( )
	
	
def run_skin_calculation( transform, root_bone, tolerance = -1, file_path = '' ):
	"""
	Main method call for the skin converter to calculate skin weights from the transform's shape node.
	
	Returns [ data, message ]
	Data    : skin calculation data
	Message : message about the results. If data == False, message holds more info.
	"""
	data, message = methods.determine_weighting( transform, root_bone, tolerance = tolerance )
	
	# Data is valid, so if a file path was provided too, save the data out. 
	if file_path and data:
		methods.save_json( file_path, data )

	return data, message


def run_skin_application( transform = None, data = None, file_path = '' ):
	"""
	Main method call for the skin converter to apply skin weights to the transform.
	
	Returns [ result, message ]
	Result  : Whether or not the application was successful
	Message : message about the results. If data == False, message holds more info.
	"""
	result, data = methods.determine_data_to_source( data, file_path )
	if not result:
		maya.cmds.warning( data )
		return result, data
		
	result, message = methods.apply_weighting( transform, data = data )
	if not result:
		maya.cmds.warning( message )
		
	return result, message


if __name__ not in '__main__':
	print "*** Loaded Skonverter ***"