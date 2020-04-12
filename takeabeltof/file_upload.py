from pathlib import Path
import random
from shotglass2.shotglass import get_site_config
from werkzeug.utils import secure_filename

class FileUpload:
    """Handle file uploads"""
    def __init__(self,local_path='',storage_path='',filename=None):
        from app import app
        site_config = get_site_config()
        
        if not storage_path:
            storage_path = site_config.get('DOWNLOAD_FOLDER','resource/static')
        self.storage_path = Path(app.root_path,site_config.get('DOWNLOAD_FOLDER','resource/static'))
        self.local_path = Path(local_path) # directory below storage_path to separate files from others
        self.filename = filename
        self.success = True
        self.error_text = ''
        self.saved_file_path = Path()
        self.allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif',}
        
        
    @property
    def saved_file_path_string(self):
        """The abreviated path and file name as a string"""
        return self.saved_file_path.as_posix()
        
        
    def save(self,file):
        """Save the file to disk
        
            file: <object> The request.files object that refers to the file to save
            
        """
        
        if not file:
            self.success = False
            self.error_text = "No file submitted"
            return
            
        if file.filename == '':
            # no file submitted
            self.success = False
            self.error_text = "No file name included"
            return
            
        if not self.allowed_file(file.filename):
            self.success = False
            self.error_text = "'{}' is not an allowed file type".format(file.filename)
            return
            
        else:
            self.filename = secure_filename(file.filename).lower()
            destination = Path(self.storage_path,self.local_path)
            if not destination.exists():
                try:
                    destination.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.success = False
                    self.error_text = "Unable to create path for storage at '{}".format(destination.as_posix())
                    return
                    
            while (destination / self.filename).exists():
                self.filename = self.filename.split('.')[0] + "".join(random.sample('1234567890abcdef',2)) + '.' + self.filename.rsplit('.', 1)[1]
                    
            self.saved_file_path = Path(self.local_path,self.filename) # the abbreviated path
            file.save(destination / self.filename )
        
        
    def get_file_path(self,filename):
        """Return a Path object for the file name"""
        return Path(self.storage_path,filename)
        
    def allowed_file(self,filename):
        site_config = get_site_config()
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in site_config.get("ALLOWED_EXTENSIONS",self.allowed_extensions)

    
