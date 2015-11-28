# Skonverter v 0.5
Simple skin converter written for Autodesk Maya. Mostly written for my own learning/experimentation and 
getting back into Maya after working primarily in MotionBuilder for a year or so.

[Read more on my Dev Blog here!]( http://evancox.net/skonverter-what/ ) If you're interested in contributing, please feel free to let me know or just start tinkering on your own and lets merge! :)

## The meat - Get it running
* Download/move/install the Skonverter package into your Maya python path.
* Call the following lines of code for a quick example, or check out the example file provided in the package.
```python
import skonverter
skonverter.run() # Loads with GUI
```
```python
# Template for running the tool headless
import skonverter
data, message = skonverter.run_skin_calculation( transform, root_bone, tolerance = -1, file_path ) # Returns data dictionary
####################
## Your code here ##
####################
result, message = skonverter.run_skin_application( transform, data, file_path )

# Note: file_path kwargs above are optional and only necessary if not passing in a data obj.
```

## Known Limitations
* Does not automatically create a skinCluster
* Does not allow for existing constraints on the bind skeleton. Assumes all bones are free to move and have no dependencies aside from their children

## The Goods
* Pretty fast for a purely python converter
* Requires no existing range of motion animation as it does all the necessary transform manipulation itself.
* Built from the command line up, so it's ready to be implemented into your automagic pipelines. No UI hackery needed.

## Development - Things to do
* The user interface could be more intuitive, but as it stands, it works and is usable.
* Division in the weight calc and normalization methods lead to some rounding issues. Maya doesn't seem to mind, however I would really like to remove them.
