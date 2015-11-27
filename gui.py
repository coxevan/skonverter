'''
File contains methods related to gui creation for the simple skin converter.

Not intended for use outside of the run method.

* Author : Evan Cox coxevan90@gmail.com
'''

# Skonverter module imports
import methods
import const

# Maya std lib imports
import pymel.core

# UI Lib imports
import PySide.QtGui

# Python std lib imports
import os



class Skonverter_Interface( ):
	def __init__( self ):
		# UI Elements needed for update
		self.transform_field = None
		self.root_field      = None
		
		# Kwargs for methods
		self.transform = None
		self.root_bone = None
		
		self.tolerance = -1
		
		# To be filled later.
		self.data = None
		
	def show( self ):
		"""
		Method handles the logic for the generation of the UI
		"""
		window_name = 'Skonverter'
		if pymel.core.window( window_name, exists=True ):
			pymel.core.deleteUI( window_name )
			if const.DEBUG:
				print 'Refreshing UI'
				
		# Make the window.
		main_window = pymel.core.window( window_name, wh = ( 200, 200 ), title = 'Skonverter v{0}'.format( const.VERSION ))#, sizeable = False )
		main_layout = pymel.core.columnLayout('main_layout', p = main_window )
		
		button_layout = main_layout
		
		## Make the transform/root_bone selection interface
		# ------ Transform obj ------ #
		transform_layout = pymel.core.horizontalLayout( 'transform_layout', p = main_layout )
		transform_label  = pymel.core.text( 'Transform: ', p = transform_layout )
		self.transform_field  = pymel.core.textField( 'transform_field', text = '...', p = transform_layout )
		self.transform_field.changeCommand( self.on_transform_field_change )
		
		transform_button_command = pymel.core.Callback( self.fill_field, self.transform_field )
		transform_button = pymel.core.button( 'transform_button', label = '<<<', p = transform_layout, c = transform_button_command )
		
		# ----- Root Bone ------ #
		root_layout = pymel.core.horizontalLayout( 'root_layout', p = main_layout )
		root_label  = pymel.core.text( 'Root Bone: ', p = root_layout )
		self.root_field  = pymel.core.textField( 'root_field', text = '...', p = root_layout )
		self.root_field.changeCommand( self.on_root_field_change )
		
		root_button_command = pymel.core.Callback( self.fill_field, self.root_field )
		root_button = pymel.core.button( 'root_button', label = '<<<', p = root_layout, c = root_button_command )		
		
		# ------ Tolerance Field -------#
		tolerance_layout = pymel.core.horizontalLayout( 'tolerance_layout', p = main_layout )
		tolerance_label  = pymel.core.text( 'Tolerance: ', p = tolerance_layout )
		self.tolerance_field  = pymel.core.textField( 'tolerance_field', text = '-1', p = tolerance_layout )
		self.tolerance_field.changeCommand( self.on_tolerance_field_change )		
		
		# ------- File path field -------#
		file_path_layout = pymel.core.horizontalLayout( 'file_path_layout', p = main_layout )
		file_path_label  = pymel.core.text( 'Data Path: ', p = file_path_layout )
		self.file_path_field  = pymel.core.textField( 'tolerance_field', text = 'None', p = file_path_layout )
		self.file_path_field.changeCommand( self.on_file_path_field_change )
		
		path_button_command = self.get_file_path
		path_button = pymel.core.button( 'file_path_button', label = '<<<', p = file_path_layout, c = path_button_command )
	
		# Redistribute the layouts
		horizontal_layouts = [ transform_layout, root_layout, tolerance_layout, file_path_layout ]
		for layout in horizontal_layouts:
			layout.redistribute( )
		
		# Make the Calculate button
		calculate_button_command = pymel.core.Callback( self.run_calculate_weighting_command )
		calculate_button = pymel.core.button('calc_button', l='Calculate Weighting', p = button_layout, c = calculate_button_command )
		
		# Make the Apply button
		apply_button_command = pymel.core.Callback( self.run_apply_weighting_command )
		apply_button = pymel.core.button('apply_button', l='Apply Weighting', p = button_layout, c = apply_button_command )
		
		main_window.show( ) 
		
	######################
	## Callback Methods ##
	######################

	def run_apply_weighting_command( self ):
		data = methods.load_json( self.file_path_field.getText( ) )
		if not data:
			self.warning('Data is invalid')
			return False
		
		methods.apply_weighting( self.transform, data = data )
	
	def run_calculate_weighting_command( self ):
		target_file_path, message = PySide.QtGui.QFileDialog( ).getSaveFileName( None, 'Save Location' )
		data, message = methods.determine_weighting( self.transform, root_bone = self.root_bone, tolerance = self.tolerance )
		if not data:
			self.warning( message )
			self.file_path_field.setText( 'Data invalid' )
			return False
		
		methods.save_json( target_file_path, data )
		if os.path.exists( target_file_path ):
			self.file_path = target_file_path
			self.file_path_field.setText( target_file_path )
		
		return True
		
	def fill_field( self, field ):
		# get the selection
		selection = pymel.core.selected( )
		if not selection:
			self.warning( 'Nothing selected. Please select an object and re-click the <<< button.' )
			return
		
		field.setText( str( selection[ 0 ].name( ) ) )
		
		field_obj_path = field.getFullPathName( ).lower( )
		# TODO: Hard coded value set here. Fix this in another update, but for now, this is all we need to be getting/setting anyway.
		if 'transform' in field_obj_path:
			self.transform = selection[ 0 ]
		elif 'root' in field_obj_path:
			self.root_bone = selection[ 0 ]
		else:
			self.warning('Was expecting transform or root. Obj path : {0}'.format( field_obj_path ) )
		return True
		
	def on_transform_field_change( self, *args ):
		try:
			self.transform = pymel.core.PyNode( self.transform_field.getText( ) )
		except pymel.core.MayaNodeError as excep:
			self.warning( excep )
		return True
			
	def on_root_field_change( self, *args ):
		try:
			self.root_bone = pymel.core.PyNode( self.root_field.getText( ) )
		except pymel.core.MayaNodeError as excep:
			self.warning( excep )	
		return True
			
	def on_tolerance_field_change( self, *args ):
		self.tolerance = float( self.tolerance_field.getText( ) )
		return True
	
	def on_file_path_field_change( self, *args ):
		self.file_path = self.file_path_field.getText( )
		return True
	
	def get_file_path( self, *args ):
		file_path, message = PySide.QtGui.QFileDialog( ).getOpenFileName( None, 'Open file' )
		
		# IF the path does not exist, we reset the UI
		if not os.path.exists( file_path ):
			self.warning( 'filepath not valid' )
			self.file_path_field.setText( 'Invalid file path' )
			self.data = None
			return None			

		self.file_path = file_path
		self.file_path_field.setText( self.file_path )
		
		return self.file_path
	
	
	#####################
	## Utility Methods ##
	#####################
	
	@staticmethod
	def warning( message ):
		if len( message ) > 160:
			print message
			pymel.core.warning( 'Skonverter UI | Check console for more information' )
			return True
		
		pymel.core.warning( 'Skonverter UI | {0}'.format( message ) )
		return True