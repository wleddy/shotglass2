# Overriding Static content

The option to override static content (images, js, css ) makes it possible to use an existing repository as the basis for a site but
still customize it with out altering the repo's files. That way you can still pull from the repo without conflicts.

To use this option, check the config settings for `STATIC_DIRS` and `LOCAL_STATIC_DIRS` search outside of 
the Shotglass2 repository. You can copy the files from the repo's static folder to there and you can modify
them as you wish. Remember to mirror the search path in the of the original file location inside of your static directories.

At runtime, the function [`shotglass2.shotglass.static`](/docs/shotglass.md) will try to construct a path for the file. 


 
[Return to Docs](/docs/shotglass2/README.md)
