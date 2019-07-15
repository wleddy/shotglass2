# takeabeltof.utils.py

This module is a catch all for a number of functions.

___
> #### cleanRecordID(*id*): => int

Use this to ensure that a value evaluates to an integer. If not, it returns -1.

This is useful anytime you receive what you hope is a record id from the web. The goal is to prevent some sort of code injection.

> #### printException(*mes="An Unknown Error Occurred",level="error",err=None*): => str

Log an error and return `mes` with optional debug information. Usually I call this as:

`flash(printException("some message",err=e))` where e is the Exception class if there is one.


---
> #### render_markdown_for(*file_name,bp=None,**kwargs*): => str or None

Attempts to find the file_name specified (may be a path) and render it from markdown to html.

:param bp is an optional blueprint object.

Requires global g.template_list (from [shotglass2.shotglass.set_template_dirs](/docs/shotglass.md)) to 
provide the initial list of template directories to search.

The lookup sequence is:
1. Try the paths in g.template_list.
2. Try the /docs/ directory.
3. Try in the templates directory of the calling blueprint (If bp is not None).
    
If the file is not found, return None.

---
> #### render_markdown_text(*text_to_render,**kwargs*): => str

This will render the text supplied from markdown to html. 
Before it tries to render it, the text is passed through 
Flask.render_template_string with **kwargs as context.

if 'escape' is in kwargs, and is False the result will not be escaped and any html
passed in the text will be returned as is. ***This is Dangerous!***

___
> #### send_static_file(*filename,**kwargs*): => Flask.Response

Returns a Flask response object for the first file found. If `path_list` in the kwargs the list will
be used to search each directory. If not provided, 'static' and 'shotglass2/static' directories are
searched.

The option to override static content (images, js, css ) makes it possible to use an existing repository as the basis for a site but
still customize it with out altering the repo's files. That way you can still pull from the repo without conflicts.

To use this option, check the config settings for `STATIC_DIRS` and `LOCAL_STATIC_DIRS`.\
Set the path to somewhere outside of the repo (usually /resource...). 
Then copy the files from the repo's static folder to there and you can modify
them as you wish.

  
---
[Return to Docs](/docs/shotglass2/README.md)


