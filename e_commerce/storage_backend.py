from ftplib import FTP
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
import os
from django.conf import settings

class FTPStorage(Storage):
    def __init__(self):
        opts = settings.FTP_STORAGE_OPTIONS
        self.host = opts["host"]
        self.username = opts["username"]
        self.password = opts["password"]
        self.base_path = opts.get("base_path", "/")
        self.port = opts.get("port", 21)
        self.passive = opts.get("passive", True)

    def _connect(self):
        ftp = FTP()
        ftp.connect(self.host, self.port)
        ftp.login(self.username, self.password)
        ftp.set_pasv(self.passive)
        if self.base_path:
            try:
                ftp.cwd(self.base_path)
            except:
                # Try to create base path if it doesn't exist
                try:
                    ftp.mkd(self.base_path)
                    ftp.cwd(self.base_path)
                except:
                    pass
        return ftp

    def _save(self, name, content):
        ftp = self._connect()
        
        # Ensure we're in the base path
        if self.base_path:
            try:
                ftp.cwd(self.base_path)
            except:
                pass
        
        # Split path and create directories
        path_parts = name.split("/")
        directory_parts = path_parts[:-1]
        filename = path_parts[-1]
        
        # Create directory structure
        current_path = self.base_path.rstrip("/")
        for part in directory_parts:
            if part:
                current_path = f"{current_path}/{part}" if current_path else part
                try:
                    ftp.cwd(current_path)
                except:
                    try:
                        ftp.mkd(current_path)
                        ftp.cwd(current_path)
                    except Exception as e:
                        # Directory might already exist or permission issue
                        pass
        
        # Ensure we're in the right directory before saving
        if directory_parts:
            dir_path = "/".join(directory_parts)
            try:
                ftp.cwd(f"{self.base_path.rstrip('/')}/{dir_path}" if self.base_path != "/" else dir_path)
            except:
                pass
        
        # Save the file
        try:
            content.seek(0)
            ftp.storbinary(f"STOR {filename}", content)
            ftp.quit()
        except Exception as e:
            ftp.quit()
            raise
        
        return name

    def exists(self, name):
        try:
            ftp = self._connect()
            try:
                size = ftp.size(name)
                ftp.quit()
                return size is not None
            except:
                # Try with full path
                if self.base_path:
                    full_path = f"{self.base_path.rstrip('/')}/{name}" if self.base_path != "/" else name
                    try:
                        size = ftp.size(full_path)
                        ftp.quit()
                        return size is not None
                    except:
                        ftp.quit()
                        return False
                ftp.quit()
                return False
        except:
            return False

    def url(self, name):
        # Remove leading slash from name if present
        name = name.lstrip("/")
        # Ensure MEDIA_URL doesn't have trailing slash
        media_url = settings.MEDIA_URL.rstrip("/")
        return f"{media_url}/{name}"
    
    def delete(self, name):
        """Delete a file from FTP server"""
        if not name:
            return
        try:
            ftp = self._connect()
            # Remove leading slash if present
            name = name.lstrip("/")
            
            # Try to delete with base_path
            if self.base_path and self.base_path != "/":
                # Change to base_path directory
                try:
                    ftp.cwd(self.base_path)
                except:
                    pass
                # Try deleting the file
                try:
                    ftp.delete(name)
                except Exception as e:
                    # Try with full path
                    try:
                        full_path = f"{self.base_path.rstrip('/')}/{name}"
                        ftp.delete(full_path)
                    except:
                        # Try changing to directory containing the file
                        path_parts = name.split("/")
                        if len(path_parts) > 1:
                            dir_path = "/".join(path_parts[:-1])
                            filename = path_parts[-1]
                            try:
                                ftp.cwd(f"{self.base_path.rstrip('/')}/{dir_path}")
                                ftp.delete(filename)
                            except:
                                pass
            else:
                # Base path is root, try direct deletion
                try:
                    # Try changing to the directory containing the file
                    path_parts = name.split("/")
                    if len(path_parts) > 1:
                        dir_path = "/".join(path_parts[:-1])
                        filename = path_parts[-1]
                        try:
                            ftp.cwd(dir_path)
                            ftp.delete(filename)
                        except:
                            # Try from root
                            ftp.cwd("/")
                            ftp.delete(name)
                    else:
                        ftp.delete(name)
                except:
                    pass
            
            ftp.quit()
        except Exception as e:
            # Silently fail - file might already be deleted or not exist
            pass
    
    def size(self, name):
        try:
            ftp = self._connect()
            try:
                size = ftp.size(name)
                ftp.quit()
                return size
            except:
                if self.base_path:
                    full_path = f"{self.base_path.rstrip('/')}/{name}" if self.base_path != "/" else name
                    size = ftp.size(full_path)
                    ftp.quit()
                    return size
                ftp.quit()
                return None
        except:
            return None