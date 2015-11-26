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

if const.DEBUG:
	reload( gui )
	reload( methods )
	

def run( ):
	"""
	Runs Skonverter UI.
	"""
	skonverter_window = gui.Skonverter_Interface( )
	skonverter_window.show( )
	
	
def run_skin_calculation( transform, root_bone, tolerance = -1, file_path = None ):
	"""
	Main method call for the skin converter to calculate skin weights from the transform's shape node.
	
	Returns [ data, message ]
	Data    : skin calculation data
	Message : message about the results. If data == False, message holds more info.
	"""
	data, message = methods.determine_weighting( transform, root_bone, tolerance = tolerance )
	
	if file_path:
		methods.save_json( file_path, data )
	
	return data, message


def run_skin_application( transform = None, data = None, file_path = None ):
	"""
	Main method call for the skin converter to apply skin weights to the transform.
	
	Returns [ result, message ]
	Result  : Whether or not the application was successful
	Message : message about the results. If data == False, message holds more info.
	"""
	if not data and not os.path.exists( file_path ):
		# No data passed in, so we must get a filepath
		return False, 'File does not exist: {0}'.format( file_path )
	
	if not data:
		data = methods.load_json( file_path )
		
	if not methods.verify_data( data ):
		return False, 'Data is corrupted'
	
	result, message = methods.apply_weighting( transform, data = data )
	if not result:
		maya.cmds.warning( message )
		
	return result, message


if __name__ not in '__main__':
	print "*** Loaded Skonverter ***"