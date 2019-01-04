# Overriding Static content

The option to override static content (images, js, css ) makes it possible to use an existing repository as the basis for a site but
still customize it with out altering the repo's files. That way you can still pull from the repo without conflicts.

To use this option, check the config setting for `LOCAL_STATIC_FOLDER` and set the path to somewhere outside of 
the repo (usually /instance...). Then copy the files from the repo's static folder to there and you can modify
them as you wish.

At runtime, the function `takeabeltof.utils.send_static_file` will try to use the value of `local_path` in **kwargs 
to construct a path for the file. If not found there it will look in the root (default) static directory.

 
[Return to Docs](/docs/takeabeltof/README.md)
