# takeabeltof.utils.py

This module is a catch all for a number of functions.

___
> #### cleanRecordID(*id*): => int

Use this to ensure that a value evaluates to an integer. If not, it returns -1.

This is useful anytime you receive what you hope is a record id from the web. The goal is to prevent some sort of code injection.

> #### printException(*mes="An Unknown Error Occurred",level="error",err=None*): => str

Log an error and return `mes` with optional debug information. Usually I call this as:

`flash(printException("some message",err=e))` where e is the Exception class if there is one.

> _TODO:_ as of Dec. 2108, it does not actually log anything. Need to fix that.

---
> #### render_markdown_for(*file_name,bp=None*): => str or None

Attempts to find the file_name specified (may be a path) and render it from markdown to html.

module is an optional blueprint object.

The lookup sequence is:
1. Try the path in setting `LOCAL_STATIC_FOLDER` if defined.
2. Try to find the file in the application root directory.
3. Try the /docs/ directory.
4. Try to find the root templates directory. *(Just like Flask does)*
5. Try in the templates directory of the calling blueprint (If both bp is not None).
    
If the file is not found, return None.

---
> #### render_markdown_text(*text_to_render,**kwargs*): => str

This will render the text supplied from markdown to html. Before it tries to render it, the text is passed through 
Flask.render_template_string with **kwargs as context.

___
> #### send_static_file(*filename,**kwargs*): => Flask.Response

This function attempts to locate a file in one or more directories. By including `local_path` in the kwargs it will try
that path first. If not found there, it will look in the root static directory

The option to override static content (images, js, css ) makes it possible to use an existing repository as the basis for a site but
still customize it with out altering the repo's files. That way you can still pull from the repo without conflicts.

To use this option, check the config setting for `LOCAL_STATIC_FOLDER` and set the path to somewhere outside of 
the repo (usually /instance...). Then copy the files from the repo's static folder to there and you can modify
them as you wish.

  
---
[Return to Docs](/docs/shotglass2/README.md)


