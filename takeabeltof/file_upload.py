from pathlib import Path
from shotglass2.shotglass import get_site_config
from werkzeug.utils import secure_filename


class FileUpload:
    """Handle file uploads"""
    def __init__(self,local_path='',resource_path=''):
        from app import app
        site_config = get_site_config()
        
        if not resource_path:
            resource_path = site_config.get('DOWNLOAD_FOLDER','resource/static')
        self.resource_path = Path(app.root_path,site_config.get('DOWNLOAD_FOLDER','resource/static'))
        self.local_path = Path(local_path) # directory below resource_path to separate files from others
        self.filename = None
        self.success = True
        self.error_text = ''
        self.saved_file_path = Path()
        default_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif',}
        self.allowed_extensions = site_config.get("ALLOWED_EXTENSIONS",default_extensions)
        
        
    @property
    def saved_file_path_string(self):
        """The abreviated path and file name as a string"""
        return self.saved_file_path.as_posix()
        
        
    def save(self,file,filename=None):
        """Save the file to disk
        
            file: <object> The request.files object that refers to the file to save
            
            filename: optional file name. Else use file.filename
            
        """
        
            
        if not file:
            self.success = False
            self.error_text = "No file submitted"
            return
            
        self.filename = filename
        
        if not self.filename:
            self.filename = file.filename
            
        if not self.filename:
            # no file Name
            self.success = False
            self.error_text = "No file name specified"
            return
            
        if not self.allowed_file(self.filename):
            self.success = False
            self.error_text = "'{}' is not an allowed file type".format(self.filename)
            return
            
        else:
            self.filename = secure_filename(self.filename).lower()
            destination = Path(self.resource_path,self.local_path)
            if not destination.exists():
                try:
                    destination.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.success = False
                    self.error_text = "Unable to create path for resources at '{}".format(destination.as_posix())
                    return
                    
            file_count = 0
            while (destination / self.filename).exists():
                file_count += 1
                self.filename = self.filename.split('.')[0] + "".join(str(file_count)) + '.' + self.filename.rsplit('.', 1)[1]
                    
            self.saved_file_path = Path(self.local_path,self.filename) # the abbreviated path
            try:
                file.save(destination / self.filename )
            except Exception as e:
                self.success = False
                self.error_text = str(e)
        
        
    def get_file_path(self,filename):
        """Return a Path object for the file name"""
        return Path(self.resource_path,filename)


    def allowed_file(self,filename):
        """Test that file is of an allowed type"""
        
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    
