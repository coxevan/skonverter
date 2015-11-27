# Skonverter v 0.5
Simple skin converter written for Autodesk Maya. Mostly written for my own learning/experimentation and 
getting back into Maya after working primarily in MotionBuilder for a year or so.

Still under development on the UI side and a few rounding errors, but should be solid.
# Development - Things to do
* The user interface could be more intuitive, but as it stands, it works and is usable.
* Division in the weight calc and normalization methods lead to some rounding issues. Maya doesn't seem to mind, however I would really like to remove them.

# Known Limitations
* Does not automatically create a skinCluster
* Does not allow for existing constraints on the bind skeleton. Assumes all bones are free to move and have no dependencies aside from their children

# The Goods
* Pretty fast for a purely python converter
* Requires no existing range of motion animation as it does all the necessary transform manipulation itself.
* Built from the command line up, so it's ready to be implemented into your automagic pipelines. No UI hackery needed.
