#!/usr/bin/env python
"""
This script creates a timestamped database backup,
and cleans backups older than a set number of dates

"""    


## doriginally based on code at http://codereview.stackexchange.com/questions/78643/create-sqlite-backups

from datetime import datetime
import hashlib
import hmac
import os
import sqlite3
import shutil
import sys
sys.path.append('') ##get import to look in the working dir.
import time

from shotglass2.takeabeltof.date_utils import local_datetime_now
from shotglass2.takeabeltof.utils import printException

class SqliteBackup():
    """
    This class creates a timestamped database backup. 
    
    A backup is normally produced if the file has actually changed and it has
    been at least 60 minutes since the last backup.
    
    *Ex:* bac = **SqliteBackup**(absolute_path_to_datafile, _kwargs_)

    *kwargs:*
    * **frequency**: Do not make a backup more often than this many minutes.
    Default is 60 minutes.
    * **backup_dir**: The directory where backups will be stored. Defaults to
    directory 'db_backups' in the same directory as the datafile.
    * **force**: Make a backup regardless of whether the datafile has changed or 
    the frequency period has elapsed.
    
    After execution, the following result properties available:
    * **result_code**: Integer result code. Codes >= 10 are considered 'fatal'.
    * **result**: Text of result code. Includes detailed debugging help in the case of
    fatal errors.
    * **fatal_result**: Returns True if a fatal error occurred. The calling method should
    probably bail out and inform someone about the error.
    
    **Note:** A file named `'data_hash.txt'` is created in the backup directory to store the 
    hash of the last successful backup. This hash is used to determine if the file has 
    actually changed since the file modification date does not seem to be reliable.
        
    """ 
 
    def __init__(self,database_path,**kwargs):
        self.database_path = database_path
        self.frequency = kwargs.pop('frequency',60) # max number of minutes between backups
        
        # self.backup_dir = kwargs.pop('backup_dir','instance/db_backups')
        backup_dir_name = 'db_backups'
        self.backup_dir = kwargs.pop('backup_dir',None)
        if not self.backup_dir:
            try:
                self.backup_dir = os.path.normpath(os.path.join(os.path.split(self.database_path)[0],backup_dir_name))
            except IndexError('unable to split database_path'):
                self.backup_dir =  os.path.join('instance',backup_dir_name)
        
        self.force = kwargs.pop('force',False) # backup regardless of when last one happened
        
        self._results = {0:"Backup Successful",
                        1:"Frequency period has not elapsed",
                        2:"Source Unchanged",
                        3:"Result code not set",
                        10:"Source file not found",
                        11:"Unable to create backup path",
                        12:"Unable to create backup file",
                        13:"Unexpected Backup Error",
                        20:"Unexpected System Error",
                    }
                        
        self.result_code = 0 
        self._set_result(self.result_code)
        
    class BackupSoftError(Exception):
        # It is not time for a backup or the datafile has not changed
        # Just want to exit the SqliteBackup class
        def __init__(self,message,errors):
            super().__init__(message)
            self.errors = errors
        pass
        
    class BackupFatalError(Exception):
        # Something serious when wrong
        # Raising this error will cause the current backup attemp to end
        # The calling function should look at self.fatal_error to see if
        # it might be a good time to stop trying and let someone know...
        def __init__(self,message,errors):
            super().__init__(message)
            self.errors = errors
        pass
        
    @property
    def fatal_error(self):
        if self.result_code >=10:
            return True
            
        return False
            
            
    def backup(self):
        """Create timestamped database copy"""
        
        try:
            # clear any previous errors
            self._set_result(0)
        
            # the data file exists
            if not os.path.isfile(self.database_path):
                self._set_result(10)
                mes = "The source file '{}' was not found.".format(self.database_path)
                raise self.BackupFatalError(mes,self.result_code)
            
            if not os.path.isdir(self.backup_dir):
                #print('Creating Backup Directory')
                try:
                    os.makedirs(self.backup_dir)
                except Exception as e:
                    self._set_result(11)
                    mes = "Unable to access the backup diretory at '{}'.\r\rSystem error: {}".format(self.backup_dir,str(e))                
                    raise self.BackupFatalError(mes,self.result_code)
                        
            # test to see if it's time for a backup
            # do this before checking for data change
            if not self._backup_time():
                self._set_result(1) # too soon
                raise self.BackupSoftError(self.result,self.result_code)
                
            
            # get the hash from the last backup
            if not self.source_changed():
                self._set_result(2) #not changed
                raise self.BackupSoftError(self.result,self.result_code)
        
            # The backup name will be <original file name>-<date and time>.sqlite
            backup_target = os.path.join(self.backup_dir, 
                                        os.path.basename(self.database_path)
                                          + local_datetime_now().strftime("-%Y-%m-%d-%H-%M")
                                          + '.sqlite'
                                         )
            # let's do it!
            try:
                connection = sqlite3.connect(self.database_path)
                cursor = connection.cursor()

                # Lock database before making a backup
                cursor.execute('begin immediate')
                # Make new backup file
                shutil.copyfile(self.database_path, backup_target)
                # print ("\nCreating {0}").format(os.path.basename(backup_file))
                # Unlock database
                connection.rollback()
        
                # rollup
                # self._rollup()
                
                # purge old
                self._purge()
            
            except Exception as e:
                self._set_result(12)
                self.result += " at {} Err: {}".format(self.backup_dir,str(e))
                raise e
                    
        except self.BackupSoftError:
            # not reallly an error. there is nothing to backup
            # The function that raised this error should have set self.result_code
            if self.result_code == 0:
                self._set_result(3)
            pass
            
        except self.BackupFatalError as e:
            # Something auful happened 
            if not self.fatal_error: 
                self._set_result(13)
            self.result = printException(str(e),err=e)
                
        except Exception as e:
            # some unexpected exception...
            self._set_result(20)
            mes = "An unexpected error occurred during backup"
            self.result += '\r\r' + printException(mes,err=e)
                        
        return
            
    def _set_result(self,code):
        if code in self._results:
            self.result_code = code
            self.result = self._results[code]
        else:
            self.result_code = 999
            self.result = "Attempted to set Non existent result code: {}".format(code)
            raise self.BackupFatalError(self.result)
    
        
    def source_changed(self):
        """Test the hash of the data file to see if it has really changed
        
        The modification date does not seem to change reliably when the
        database is updated. So hash the file to know for sure.
        """
        
        hasher = hmac.new(b"My key",digestmod=hashlib.sha256) # the key is not really a secret
        
        #Read in the data file and hash the result
        f = open(self.database_path,'rb')
        while True:
            value = f.read(1024)
            if not value:
                break
            hasher.update(value)
    
        result = hasher.hexdigest()

        f.close()
        file_changed = False
        #import pdb;pdb.set_trace()
        
        # open or create a file to store hash result
        f = open(os.path.join(self.backup_dir,"data_hash.txt"),'a+')
        f.seek(0) # move to the start of the file
        test_hash = f.read()
        if test_hash and test_hash == result:
            #print("File unchanged at:",result)
            file_changed = False # file is unchanged
        else:
            f.truncate(0) # ensure the file is empty
            f.write(result)
            file_changed = True
            #print("New hash:",result)
        f.close()
        
        if self.force: 
            file_changed = True
        
        # do something with this information...
        return file_changed
        
        
    def _backup_time(self):
        """Has enough time passed since the last backup?"""
        
        if self.force: return True
        
        father_time = True
        
        file_list = self._get_backup_list()
        if file_list:
            # get the creation time for item 0 in list
            backup_file = file_list[0]
            father_time = (os.stat(backup_file).st_mtime < (time.time() - (self.frequency*60))) # convert frequency to seconds
        
        return father_time
        
        
    def _get_backup_list(self):
        """Get the list of backup files"""
   
        file_list = os.listdir(self.backup_dir)
        #Put them in order, newest First
        file_list.sort(reverse=True)
        
        # Only include files where the file name starts with FILE_TO_BACKUP name
        file_base = os.path.basename(self.database_path)[:len(os.path.basename(self.database_path))]
        
        for list_element in range(len(file_list)-1, -1,-1):
            if os.path.basename(file_list[list_element])[:len(os.path.basename(self.database_path))] != file_base:
                del file_list[list_element]
            elif not os.path.isfile(os.path.join(self.backup_dir,file_list[list_element])):
                del file_list[list_element]
            else:
                # add path to file_list element
                file_list[list_element] = os.path.join(self.backup_dir,file_list[list_element])
                
        return file_list
                    

    def _rollup(self):
        """If it's an new month since the last backup, make the last
        one for the month the archive, and delete any older files for this month
        
        """
        pass
        # # Always leave at lest the minimum number of backups
#
#         #the file_list should only contain backup files
#         fileCount = len(file_list)
#         if fileCount > MINIMUM_BACKUPS:
#             for list_element in range(MINIMUM_BACKUPS, fileCount):
#                 backup_file = os.path.join(backup_dir, file_list[list_element])
#                 if os.path.isfile(backup_file):
#                     if os.stat(backup_file).st_mtime < (time.time() - (NO_OF_DAYS * 86400)):
#                         os.remove(backup_file)
#                         print "Deleting {0}".format(os.path.basename(backup_file))
#         else:
#             print('No Backup files to delete')

    def _purge(self,keep_days=7):
        """Remove old backup files older than 'keep_days' days old"""
        
        file_list = self._get_backup_list()
        if file_list:
            for backup_file in file_list:
                    try:
                        if os.stat(backup_file).st_mtime < (time.time() - (keep_days * 86400)):
                            os.remove(backup_file)
                    except Exception as e:
                        printException("Error in backup file purge for {}".format(backup_file),level="error",err=e)
        


if __name__ == "__main__":
    #import pdb;pdb.set_trace()
    
    from app import app
    from shotglass2.takeabeltof.mailer import email_admin
    
    with app.app_context():
        # db_path = os.path.join('/Users/bleddy/Dropbox/Sites/staffing/',app.config['DATABASE_PATH'])
        db_path = os.path.join(app.root_path,app.config['DATABASE_PATH'])
        bac = SqliteBackup(db_path,frequency=5)
        
        print(datetime.now())
        while not bac.fatal_error:
            bac.backup()
            print ("Backup Result: {}, code: {}".format(bac.result,bac.result_code))
            if bac.result_code == 0:
                print(datetime.now())
            if not bac.fatal_error:
                time.sleep(20)
            
        if bac.fatal_error:
            email_admin("Fatal Backup Error",bac.result)
            print("Fatal error occurred\r\r{}".format(bac.result))
            print("Exiting backup system.")
            
        sys.exit()
        
 