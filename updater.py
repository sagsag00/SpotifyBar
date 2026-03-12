import requests
from pathlib import Path
from zipfile import ZipFile
import shutil
import sys
import subprocess
from typing import Union

from logger import logger

KEEP_FILES = {"config.ini", ".env", "api/info.ini"}
   
class Updater(): 
    def __init__(self, version: float):
        self.__version = version

    def check_new_version(self) -> bool:
        response = requests.get("https://github.com/sagsag00/SpotifyBar/releases/latest")
        new_version = response.url.split("/")[-1].replace("v", "")
        
        return not self.is_bigger_version(self.__version, new_version)
    
    @staticmethod
    def is_bigger_version(version: str, compared_version: str) -> bool:
        """Checks if version is bigger or equals to compared_version"""

        v1 = [int(x) for x in version.split(".")]
        v2 = [int(x) for x in compared_version.split(".")]

        return v1 >= v2

    def download_new_version(self) -> Union[Path, None]:
        """
        Download the new version.
        Returns:
            Extracted directory path, or None on failure.
        """
        
        logger.info("Downloading new version...")
        try:
            response = requests.get("https://api.github.com/repos/sagsag00/SpotifyBar/releases/latest")
            response.raise_for_status()
            data = response.json()
            
            assets = data.get("assets", [])
            if not assets:
                logger.error("No assets found in latest release.")
                return None
            
            asset = assets[0]
            asset_url = asset["browser_download_url"]
            filename: str = asset["name"]
            
            r = requests.get(asset_url, stream=True)
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
                    
            if not filename.endswith(".zip"):
                logger.error(f"Unsupported file format: {filename}")
                return None
                
            extract_dir = Path(filename).with_suffix("")
            extract_dir.mkdir(exist_ok=True)
            with ZipFile(filename, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
                
            Path(filename).unlink()
            logger.info(f"Extracted new version to {extract_dir}")
            return extract_dir
        
        except Exception as e:
            logger.error(f"Failed to download new version: {e}")
            return None
               
    def replace_files(self, new_dir: Path, app_dir: Path):
        """
        Replaces all files in app_dir with files from new_dir,
        except those in KEEP_FILES.
        """
        try:
            for src_path in new_dir.rglob("*"):
                rel_path = src_path.relative_to(new_dir)
                
                if str(rel_path).replace("\\", "/") in KEEP_FILES:
                    continue
                
                dest_path = app_dir / rel_path
                
                if src_path.is_dir():
                    dest_path.mkdir(exist_ok=True)
                else:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dest_path)
                    
            shutil.rmtree(new_dir)  
            logger.info("Files replaced successfully.")
        except Exception as e:
            logger.error(f"Failed to replace files: {e}")
       
    def restart_app(self, app_path: Path):
        if app_path.name == "main.py":
            subprocess.Popen([sys.executable, str(app_path)])
            return
        subprocess.Popen([str(app_path)])
       
def main():
    VERSION = sys.argv[1] if len(sys.argv) > 1 else "0.0"
    manager = Updater(VERSION)
    
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).resolve().parent
        app_path = app_dir / "SpotifyBar.exe"
    else:
        app_dir = Path(__file__).resolve().parent
        app_path = app_dir / "main.py"
        
    new_dir = manager.download_new_version()
    if new_dir is None:
        logger.error("Update failed, aborting.")
        sys.exit(1)
        
    manager.replace_files(new_dir, app_dir)
    manager.restart_app(app_path)
                
if __name__ == "__main__":
    main()