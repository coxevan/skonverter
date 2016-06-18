"""
Contains the core methods of the skin converter.

Author : Evan Cox, coxevan90@gmail.com
"""

# Maya sdk imports
import maya.cmds
import pymel.core
import maya.api.OpenMaya as om2

# Python std lib imports
import pprint
import json
import os

# Skonverter module imports
import const


BONE_DELTA = const.BONE_DELTA # The amount of distance each bone should be moved to determine weighting.
FAILURE_THRESHOLD = const.FAILURE_THRESHOLD # How many bones can fail before user is prompted with warning
DEBUG = const.DEBUG
NORMALIZE = const.NORMALIZE


##################
## Main methods ##
##################


def determine_weighting( transform, root_bone = None, tolerance = -1 ):	
	"""
	Main method which holds logic for determining the weighting for a given transform.
	"""
	if not transform or not root_bone:
		return False, 'One or both objects were not found. Transform : {0} | Root_bone : {1}'.format( transform, root_bone )
	
	try:
		# If it's not a pymel node, we'll make it one for the early stages of data collection about objects, not verts. 
		if not isinstance( transform, pymel.core.nodetypes.DagNode ):
			transform = pymel.core.PyNode( transform )
		if not isinstance( root_bone, pymel.core.nodetypes.DagNode ):
			root_bone = pymel.core.PyNode( root_bone )
	except pymel.core.MayaNodeError as exception:
		return False, '{0}'.format( exception )
		
	rest_vert_positions = query_vertex_positions( transform )
	ordered_bone_list = get_ordered_bone_list( root_bone, [ root_bone ] )
	bone_vert_association = { }
	
	# Create a list of tuples with each bone and its corresponding locator. We then make an expression locking them. Animation/constraints cannot be on the skeleton.
	#bone_and_locators = create_locators( ordered_bone_list )
	#create_expression( bone_and_locators )
	
	weight_data = { } # Final data to be sent out, Dictionary to associate verts with bones and weights for application to the skin cluster.

	for index, bone in enumerate( ordered_bone_list ):
		bone_name = bone.name( )
		
		# Do our movement and calculation
		print 'Skin Weight Calculation : Processing {0}/{1} | {2}'.format( index + 1, len( ordered_bone_list ), bone_name )
		
		child_bones = [ ]
		# Move the children to counter the movement of the parent.
		_children = bone.getChildren( )
		for _child in _children:
			_child_bone_name = _child.name( ) 
			# Get the starting translation for the child, counter translate the children
			_child_starting_translation = maya.cmds.xform( _child_bone_name, query = True, translation = True, a = True, ws = True )
			_child_new_translation = add_vector3s( _child_starting_translation, [ 0, -BONE_DELTA, 0 ] )
			maya.cmds.xform( _child_bone_name, translation = _child_new_translation, a = True, ws = True )
			
			# Store the childs bone name and the starting position
			child_bones.append( ( _child_bone_name, _child_starting_translation ) )			
		
		# Get the starting translation so we can reset it back after we move it a bit
		starting_translation = maya.cmds.xform( bone_name, query = True, translation = True, a = True, worldSpace = True )
		new_translation = add_vector3s( starting_translation, [ 0, BONE_DELTA, 0 ] )
		maya.cmds.xform( bone_name, translation = new_translation, a = True, worldSpace = True )
		
		# Get the new vert positions and calculate the weights for the specific bone
		new_vert_positions = query_vertex_positions( transform )
		new_vert_weights = calculate_vertex_weights( new_vert_positions, rest_vert_positions )
		
		# Reset the bone
		maya.cmds.xform( bone_name, translation = starting_translation, a = True, worldSpace = True )
		
		# Save the weighting to the association dictionary
		bone_vert_association[ bone_name ] = new_vert_weights
		
		# Reset the children to their starting positions
		if child_bones:
			for _child, vector in child_bones:
				maya.cmds.xform( _child, translation = vector, a = True, ws = True )

		# Get the vert id and it's associated weight for this bone
		for vert_id, weight in bone_vert_association[ bone_name ].iteritems():
			# If the weight is below the tolerance, we skip it
			if weight <= tolerance:
				continue
			
			vert_id_string = str( vert_id )
			if vert_id_string not in weight_data.keys( ):
				weight_data[ vert_id_string ] = [ ]
			weight_data[ vert_id_string ].append( ( bone_name, weight ) )
			
	print 'Skin Weight calculation complete | Organizing data into skinPercent readable format'
	bone_name_list = [ bone.name( ) for bone in ordered_bone_list ] # Make this list so we don't have to keep pymel objs around for the weight application. We only need the names
			
	if NORMALIZE:
		messages = [ ]
		print 'Skin Weight organization complete | Normalizing weight data'
		for vert_id_string in weight_data.keys( ):
			weight_list = weight_data[ vert_id_string ]
			normalized_weight_list, message = normalize_vertex_weighting( weight_list )
			
			weight_data[ vert_id_string ] = normalized_weight_list
			messages.append( message )
		
		# If we failed at all during the normalization step, we want to know.
		if False in messages:
			failures = [ result for result in messages if not result ]
			print 'Even after normalizing: {0} still are not 1.0'.format( len( failures ) )
	
	data = consolidate_data( weight_data, bone_name_list )
	
	print 'Skin Calculation : Complete'
	# Clean up the scene and collect some last minute info.
	return data, 'Success'
	

def apply_weighting( transform, skincluster = None, data = None ):
	"""
	Main method which holds logic for applying weighting data
	"""
	# If it's not a pymel node, we'll make it one for the early stages of data collection about objects, not verts. 
	try:
		if not isinstance( transform, pymel.core.nodetypes.DagNode ):
			transform = pymel.core.PyNode( transform )
	except pymel.core.MayaNodeError as exception :
		return False, '{0}'.format( exception )
	
	if not skincluster:
		print 'Skin Weight Application : Getting the skin cluster'
		# Get the objects history and then grab the skincluster from it
		history = maya.cmds.listHistory(  transform.name( ) )
		skinclusters = maya.cmds.ls( history, type = 'skinCluster' )
		
		# If we did not get a skincluster, we need to get out
		if not skinclusters:
			return False, 'No skin cluster found, apply one to the mesh passed in'
		skincluster = skinclusters[ 0 ]
		py_cluster  = pymel.core.PyNode( skincluster )
	
	# Unpack the data from the file
	weight_data = data[ 'weight' ]
	ordered_bone_list = data[ 'order' ]
	
	bone_failure = [ ]    # List to catch our failures :(
	print 'Skin Weight Application : Applying vertex weighting'
	
	# Logging variable declaration/initialization
	notify_total_weights = False
	vertices_evaluated = [ ] 	
	total_weights = [ ]	
	
	# Remove any normalizing that maya will try to do and remove all the weighting on the current skincluster.
	py_cluster.setNormalizeWeights( 0 )
	remove_all_weighting( skincluster, transform, ordered_bone_list, weight_data.keys( ) )	
	
	# For each vert, we'll get the list of ( bone_name, weight ) and apply it to the vertex
	for vert_id in weight_data.keys( ):
		weight_list = weight_data[ vert_id ]
		
		if NORMALIZE:
			weight_list, message = normalize_vertex_weighting( weight_list )
			if not message:
				notify_total_weights = True
			
		if DEBUG:
			total_weight = calculate_total_vertex_weight( weight_list )
			total_weights.append( calculate_total_vertex_weight( weight_list ) )	

		# We apply the weighting to the skin cluster
		try:
			maya.cmds.skinPercent( skincluster, transform + '.vtx[{0}]'.format( vert_id ), tv = weight_data[ vert_id ] )
			vertices_evaluated.append( vert_id )
			
		# If we failed, we catch it and save it to the failure list to notify the user later
		except RuntimeError as excep:
			failure_string = 'Bone Failure: {0}'.format( excep )
			if failure_string not in bone_failure:
				bone_failure.append( failure_string )
	
	# Only notify the user of failure if within this level
	if len( bone_failure ) > FAILURE_THRESHOLD:
		maya.cmds.warning( 'Failed: See console for more info' )
		for failure_string in bone_failure:
			print failure_string
	
	if DEBUG:
		non_one_count = 0
		for weight in total_weights:
			if weight != 1.0:
				non_one_count += 1
		print 'Verts not exactly normalized to 1.0 :', non_one_count
	
		if notify_total_weights:
			pprint.pprint( total_weights )
	print 'Skin Weight Application : Complete'
	
	return True, 'Success'


#####################
## Utility methods ##
#####################

def get_ordered_bone_list( bone, bone_list = None ):
	'''
	Recursive search for children of the <bone> and places them in the <bone_list>.
	'''
	# We didn't get a bone_list passed in, so we'll just make one to return later
	if bone_list == None:
		bone_list = [ ]
			
	for child in bone.getChildren( ):
		# If the child we got isn't a Joint, we're going to pass on it.
		if not isinstance( child, pymel.core.nodetypes.Joint ):
			continue
			
		# Add the child to the list and run the method again
		bone_list.append( child )
		get_ordered_bone_list( child, bone_list )
		
	return bone_list


def query_vertex_positions( transform ):
	"""
	Queries all vertex positions from a given transform

	Using Maya Python API 2.0
	"""

	# Create a selectionList and add our transform to it
	sel_list = om2.MSelectionList()
	sel_list.add( transform.name() )

	# Get the dag path of the first item in the selection list
	sel_obj = sel_list.getDagPath( 0 )

	# create a Mesh functionset from our dag object
	mfn_object = om2.MFnMesh( sel_obj )

	return mfn_object.getPoints()


def calculate_vertex_distance( vector1, vector2 ):
	"""
	Calculate the absolute distance between two vectors.
	"""
	#x = ( round_float( vector1[ 0 ] ) - round_float( vector2[ 0 ] ) ) ** 2
	#y = ( round_float( vector1[ 1 ] ) - round_float( vector2[ 1 ] ) ) ** 2
	#z = ( round_float( vector1[ 2 ] ) - round_float( vector2[ 2 ] ) ) ** 2
	
	difference_x = vector1[ 0 ] - vector2[ 0 ]
	difference_y = vector1[ 1 ] - vector2[ 1 ]
	difference_z = vector1[ 2 ] - vector2[ 2 ]
	
	difference_x_sqr = difference_x ** 2
	difference_y_sqr = difference_y ** 2
	difference_z_sqr = difference_z ** 2
	
	sum_of_deltas = difference_x_sqr + difference_y_sqr + difference_z_sqr
	
	distance = sum_of_deltas ** 0.5
	
	return distance


def round_float( number ):
	"""
	Rounds a float by converting it to a string, which can limit the amount of digits past the decimal. Then converts it back into a float.
	"""
	rounded = float( '{0:.3f}'.format( number ) )
	
	return rounded
	

def calculate_vertex_weights( new_positions, rest_positions ):
	"""
	Here we do some really simple math to determine the weights we want to associate with this bone. The weights being spit out here
	will not be perfect as it's the amount of movement th1at this bone causes in the verts ( between 0 and 1 ). 
	
	Why won't it be perfect? The hierarchy says the root bone will move all other bones below, etc. That means, even if the root bone has no weighting to it
	from many of the vertices, it'll stay say all verts will be 1.0 because the root bone moves each bone. We don't worry about this though, as the application 
	process goes from the root bone to the tips, meaning that weight is applied to the root bone at first, and then slowly chipped away by other bones, similar 
	to the way some people choose to paint their weights in a normal situation.
	"""
	# We make a dictionary to store weights in
	list_of_weights = {}

	# Get list of indexes to get distance on
	index_list = [(i) for i, j in enumerate(zip(new_positions, rest_positions)) if j[0] != j[1]]
	
	for index in index_list:
		# Calculate the vertex distance and divide by the bone's movement (Default is 1 unit)
		weight = calculate_vertex_distance( new_positions[index], rest_positions[index] ) / BONE_DELTA
		
		# Round the weighting.
		weight = round_float( weight )
				
		# TODO: Probably need more checks here to ensure that the weighting is valid
		list_of_weights[index] = weight 
		
	return list_of_weights


def add_vector3s( vector1, vector2 ):
	"""
	Adds two vector 3's together.
	"""
	x1, y1, z1 = vector1[ : ]
	x2, y2, z2 = vector2[ : ]
	
	x = x1 + x2
	y = y1 + y2
	z = z1 + z2
	
	return [ x, y, z ]


def remove_all_weighting( skincluster, transform, bone_list, vert_list ):
	"""
	Removes all weighting from the given skin cluster. This method assumes the skincluster has it's normalization mode set to None
	"""
	# Make a weight list with each bone being set to 0.0
	zero_value_list = [ ( bone_name, 0.0 ) for bone_name in bone_list ]
	
	# For each vert in the vert_list passed in, we reset all the weighting to zero. This skin cluster should already be set to not normalize, so the weighting will be completely gone.
	for vert_id in vert_list:
		maya.cmds.skinPercent( skincluster, transform + '.vtx[{0}]'.format( vert_id ), tv = zero_value_list )
	return True


def normalize_vertex_weighting( weight_list ):
	"""
	Normalizes vertex weights if they are above or below 1.0 by dividing each individual weight value by the sum of all the weights associated with that vertex.
	
	weight_list is a list of tuples ( bone_name, weight ).
	"""
	total = calculate_total_vertex_weight( weight_list )
	normalized_weight_list = [ ]
	for bone_name, weight in weight_list:
		# For each bone, divide its corresponding weight value by the total
		normalized_weight = weight / total 
		
		# Make a new tuple and add it to the normalized_weight_list
		normalized_weight_tuple = ( bone_name, normalized_weight )
		normalized_weight_list.append( normalized_weight_tuple )
	
	# If we're in debug mode, we want to recalculate the total weight for these normalized weights. Lets check again to be sure they're fully normalized.
	if DEBUG:
		total = calculate_total_vertex_weight( normalized_weight_list )
		if total != 1.0:
			print '{0}'.format( total )
			return normalized_weight_list, False
		
	return normalized_weight_list, True


def calculate_total_vertex_weight( weight_list ):
	"""
	Given a weightlist, this method will add up the weights.
	"""
	weight = 0
	for bone, bone_weight in weight_list:
		if bone_weight != 0:
			weight += bone_weight
	return weight

############################
## JSON Writing & Loading ##
############################

def save_json( file_path, content ):
	"""
	Saves the content to the file_path in the json format
	"""
	with open( file_path, 'w' ) as data_file:
		json_data = json.dumps( content )
		data_file.write( json_data )
	return True
		
		
def load_json( file_path ):
	"""
	Checks file path, loads json file, returns data
	"""
	if not os.path.exists( file_path ):
		return None
	
	with open( file_path, 'r' ) as data_file:
		data_from_file = data_file.readlines( )[0]
		json_data = json.loads( data_from_file )
		
	return json_data

###########################
## Data handling methods ##
###########################

def consolidate_data( weight_list, bone_list ):
	"""
	Creates the final data dictionary out of the two lists.
	
	Data format is pretty simple right now. Hopefully continues to be in the future.
	"""
	return { 'weight': weight_list, 'order': bone_list }

def verify_data( data ):
	"""
	Checks the validity of the data. 
	
	Very few checks right now as the data is in a very rigid state
	"""
	print 'Skonverter | Verifying data'
	
	if not isinstance( data, dict ):
		return False, 'Data must be a dictionary'
	
	if not 'order' in data.keys( ) or not 'weight' in data.keys( ):
		return False, 'Data either does not contain key "order" or key "weight"'
	
	# Check the order
	for bone_string in data['order']:
		if not isinstance( bone_string, basestring ):
			return False, 'Bone list must be strings'
	
	return True, 'Data is valid'

def determine_data_to_source( data, file_path ):
	"""
	Handles the loading and verification of data. Determines whether or not to get the data from the disk or to use the data passed in.
	"""
	# Check to see if the file path and/or data is even valid.
	file_path_validity = os.path.exists( file_path )
	data_validity, message = verify_data( data )
	
	# If not neither
	if not file_path_validity and not data_validity:
		return False, 'No valid data or file passed in'
	
	# If not file
	if not file_path_validity:
		# The path is not valid. Verify the data and return
		return data_validity, data
	
	# If not data
	if not data_validity:
		# We load the data from the file
		result, data = load_data_from_file( file_path )
	
	# If the file path is valid and the data is valid, check the const to determine preference.
	if data_validity and file_path_validity:
		if const.FILE_PREFERENCE:
			# We go with the file
			return load_data_from_file( file_path )

		else:
			# We go with the data we were passed in.
			return data_validity, data
		

def load_data_from_file( file_path ):
	# Load the data
	file_data = load_json( file_path )
	
	# Verify it
	result, message = verify_data( file_data )
	if result:
		return result, file_data
	else:
		return False, message	