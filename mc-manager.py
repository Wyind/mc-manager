#!/usr/bin/env python3
"""
Minecraft Manager - A command-line tool for managing Minecraft resource packs, shader packs, and mods
using the Modrinth API.
"""

import os
import sys
import json
import shutil
import zipfile
import argparse
import platform
import requests
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Terminal colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Content types
class ContentType(Enum):
    MOD = "mod"
    RESOURCE_PACK = "resourcepack"
    SHADER_PACK = "shader"

# Default Minecraft paths based on OS
def get_default_minecraft_path() -> Path:
    system = platform.system().lower()
    home = Path.home()
    
    if system == "windows":
        return home / "AppData" / "Roaming" / ".minecraft"
    elif system == "darwin":  # macOS
        return home / "Library" / "Application Support" / "minecraft"
    else:  # Linux and others
        return home / ".minecraft"

class ModrinthAPI:
    """Interface for the Modrinth API"""
    BASE_URL = "https://api.modrinth.com/v2"
    USER_AGENT = "MinecraftManager/1.0.0"
    
    @staticmethod
    def search(query: str, content_type: ContentType, 
               game_versions: List[str] = None, limit: int = 20) -> Dict:
        """Search for content on Modrinth"""
        # Map content type to Modrinth project type
        project_type = None
        if content_type == ContentType.MOD:
            project_type = "mod"
        elif content_type == ContentType.RESOURCE_PACK:
            project_type = "resourcepack"
        elif content_type == ContentType.SHADER_PACK:
            facets = [["project_type:shader"]]
            project_type = None
        
        # Build facets for filtering
        facets = []
        if project_type:
            facets.append([f"project_type:{project_type}"])
        if game_versions:
            versions_facet = [f"versions:{v}" for v in game_versions]
            facets.append(versions_facet)
            
        # Make API request
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        params = {
            "query": query,
            "limit": limit,
            "facets": json.dumps(facets) if facets else None
        }
        
        try:
            response = requests.get(
                f"{ModrinthAPI.BASE_URL}/search", 
                headers=headers, 
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"{Colors.RED}Error searching Modrinth: {e}{Colors.END}")
            return {"hits": []}
    
    @staticmethod
    def get_project(project_id: str) -> Dict:
        """Get project details by ID"""
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        try:
            response = requests.get(
                f"{ModrinthAPI.BASE_URL}/project/{project_id}", 
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"{Colors.RED}Error fetching project: {e}{Colors.END}")
            return {}
    
    @staticmethod
    def get_versions(project_id: str, game_version: str = None) -> List[Dict]:
        """Get versions of a project"""
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        params = {}
        if game_version:
            params["game_versions"] = f"[\"{game_version}\"]"
            
        try:
            response = requests.get(
                f"{ModrinthAPI.BASE_URL}/project/{project_id}/version", 
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"{Colors.RED}Error fetching versions: {e}{Colors.END}")
            return []
    
    @staticmethod
    def download_file(url: str, destination: Path) -> bool:
        """Download a file from URL to destination"""
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        try:
            with requests.get(url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(destination, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return True
        except requests.RequestException as e:
            print(f"{Colors.RED}Error downloading file: {e}{Colors.END}")
            return False

class MinecraftManager:
    """Main class for managing Minecraft content"""
    
    def __init__(self, minecraft_path: Path = None):
        self.minecraft_path = minecraft_path or get_default_minecraft_path()
        self.mods_path = self.minecraft_path / "mods"
        self.resourcepacks_path = self.minecraft_path / "resourcepacks"
        self.shaderpacks_path = self.minecraft_path / "shaderpacks"
        
        # Create directories if they don't exist
        for path in [self.mods_path, self.resourcepacks_path, self.shaderpacks_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Path to our configuration file
        self.config_path = self.minecraft_path / "minecraft_manager_config.json"
        self.installed_content = self._load_installed_content()
        
    def _load_installed_content(self) -> Dict:
        """Load information about installed content"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"{Colors.YELLOW}Warning: Config file corrupted, creating new one{Colors.END}")
        
        # Create default structure if not exists or corrupted
        return {
            "mods": {},
            "resourcepacks": {},
            "shaderpacks": {}
        }
    
    def _save_installed_content(self):
        """Save information about installed content"""
        with open(self.config_path, 'w') as f:
            json.dump(self.installed_content, f, indent=2)
    
    def get_content_path(self, content_type: ContentType) -> Path:
        """Get the path for a content type"""
        if content_type == ContentType.MOD:
            return self.mods_path
        elif content_type == ContentType.RESOURCE_PACK:
            return self.resourcepacks_path
        elif content_type == ContentType.SHADER_PACK:
            return self.shaderpacks_path
        else:
            raise ValueError(f"Unknown content type: {content_type}")
    
    def get_content_dict(self, content_type: ContentType) -> Dict:
        """Get the dictionary for a content type"""
        if content_type == ContentType.MOD:
            return self.installed_content["mods"]
        elif content_type == ContentType.RESOURCE_PACK:
            return self.installed_content["resourcepacks"]
        elif content_type == ContentType.SHADER_PACK:
            return self.installed_content["shaderpacks"]
        else:
            raise ValueError(f"Unknown content type: {content_type}")
    
    def search(self, query: str, content_type: ContentType, game_version: str = None):
        """Search for content and display results"""
        game_versions = [game_version] if game_version else None
        results = ModrinthAPI.search(query, content_type, game_versions)
        
        if not results.get("hits"):
            print(f"{Colors.YELLOW}No results found for '{query}'{Colors.END}")
            return
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}Search Results for '{query}':{Colors.END}")
        print(f"{Colors.UNDERLINE}{'ID':<10} {'Title':<40} {'Downloads':<10} {'Updated':<10}{Colors.END}")
        
        for i, item in enumerate(results["hits"], 1):
            print(f"{Colors.BOLD}{i:<4}{Colors.END} {item['title']:<40} {item.get('downloads', 'N/A'):<10} {item.get('date_modified', 'N/A')[:10]}")
            print(f"    {Colors.CYAN}{item['description'][:80]}...{Colors.END}" if len(item.get('description', '')) > 80 
                  else f"    {Colors.CYAN}{item.get('description', '')}{Colors.END}")
        
        # Allow user to select a result
        try:
            selection = int(input(f"\n{Colors.GREEN}Enter number to install (0 to cancel): {Colors.END}"))
            if 1 <= selection <= len(results["hits"]):
                selected = results["hits"][selection - 1]
                self.install(selected["project_id"], content_type, game_version)
        except ValueError:
            print(f"{Colors.YELLOW}Invalid selection{Colors.END}")
            
    def install(self, project_id: str, content_type: ContentType, game_version: str = None):
        """Install a project"""
        # Get project details
        project = ModrinthAPI.get_project(project_id)
        if not project:
            print(f"{Colors.RED}Project not found{Colors.END}")
            return
            
        print(f"{Colors.HEADER}Installing {project['title']}{Colors.END}")
        
        # Get available versions
        versions = ModrinthAPI.get_versions(project_id, game_version)
        if not versions:
            print(f"{Colors.YELLOW}No compatible versions found{Colors.END}")
            return
        
        # Use the latest version
        version = versions[0]
        
        # Get primary file to download
        if not version.get("files"):
            print(f"{Colors.RED}No files available for download{Colors.END}")
            return
            
        # Find primary file
        primary_file = next((f for f in version["files"] if f.get("primary")), version["files"][0])
        
        # Determine destination path
        content_path = self.get_content_path(content_type)
        filename = primary_file["filename"]
        destination = content_path / filename
        
        # Download the file
        print(f"{Colors.BLUE}Downloading {filename}...{Colors.END}")
        success = ModrinthAPI.download_file(primary_file["url"], destination)
        
        if success:
            print(f"{Colors.GREEN}Successfully installed {project['title']} to {destination}{Colors.END}")
            
            # Update installed content records
            content_dict = self.get_content_dict(content_type)
            content_dict[project_id] = {
                "name": project["title"],
                "version": version["version_number"],
                "filename": filename,
                "installed_at": version["date_published"]
            }
            self._save_installed_content()
        else:
            print(f"{Colors.RED}Failed to install {project['title']}{Colors.END}")
    
    def list_installed(self, content_type: ContentType):
        """List installed content of a specified type"""
        content_dict = self.get_content_dict(content_type)
        
        if not content_dict:
            print(f"{Colors.YELLOW}No {content_type.value}s installed{Colors.END}")
            return
            
        print(f"\n{Colors.HEADER}{Colors.BOLD}Installed {content_type.value}s:{Colors.END}")
        print(f"{Colors.UNDERLINE}{'Name':<40} {'Version':<20} {'Installed Date':<20}{Colors.END}")
        
        for project_id, info in content_dict.items():
            print(f"{info['name']:<40} {info['version']:<20} {info['installed_at'][:10]}")
    
    def uninstall(self, name_query: str, content_type: ContentType):
        """Uninstall content by name"""
        content_dict = self.get_content_dict(content_type)
        content_path = self.get_content_path(content_type)
        
        # Find matching content
        matches = [(pid, info) for pid, info in content_dict.items() 
                  if name_query.lower() in info["name"].lower()]
        
        if not matches:
            print(f"{Colors.YELLOW}No matching {content_type.value} found for '{name_query}'{Colors.END}")
            return
            
        if len(matches) > 1:
            print(f"\n{Colors.HEADER}{Colors.BOLD}Multiple matches found:{Colors.END}")
            for i, (_, info) in enumerate(matches, 1):
                print(f"{i}. {info['name']} (version: {info['version']})")
                
            try:
                selection = int(input(f"\n{Colors.GREEN}Enter number to uninstall (0 to cancel): {Colors.END}"))
                if 1 <= selection <= len(matches):
                    project_id, info = matches[selection - 1]
                else:
                    return
            except ValueError:
                print(f"{Colors.YELLOW}Invalid selection{Colors.END}")
                return
        else:
            project_id, info = matches[0]
        
        # Remove the file
        file_path = content_path / info["filename"]
        if file_path.exists():
            try:
                os.remove(file_path)
                print(f"{Colors.GREEN}Removed {info['name']} ({file_path}){Colors.END}")
            except OSError as e:
                print(f"{Colors.RED}Error removing file: {e}{Colors.END}")
                return
        
        # Update records
        del content_dict[project_id]
        self._save_installed_content()

    def update(self, content_type: ContentType = None, name_query: str = None):
        """Update installed content"""
        if content_type is None:
            # Update all content types
            for ct in ContentType:
                self.update(ct, name_query)
            return
        
        content_dict = self.get_content_dict(content_type)
        
        if name_query:
            # Find matching content
            matches = [(pid, info) for pid, info in content_dict.items() 
                      if name_query.lower() in info["name"].lower()]
            if not matches:
                print(f"{Colors.YELLOW}No matching {content_type.value} found for '{name_query}'{Colors.END}")
                return
            items_to_check = matches
        else:
            items_to_check = list(content_dict.items())
        
        if not items_to_check:
            print(f"{Colors.YELLOW}No {content_type.value}s installed to update{Colors.END}")
            return
            
        print(f"{Colors.HEADER}Checking for updates for {len(items_to_check)} {content_type.value}(s)...{Colors.END}")
        
        for project_id, info in items_to_check:
            print(f"Checking {info['name']}...", end="", flush=True)
            
            # Get the latest version
            versions = ModrinthAPI.get_versions(project_id)
            if not versions:
                print(f"{Colors.YELLOW} No versions found{Colors.END}")
                continue
                
            latest = versions[0]
            
            if latest["version_number"] == info["version"]:
                print(f"{Colors.GREEN} Already up to date ({info['version']}){Colors.END}")
                continue
                
            print(f"{Colors.BLUE} Update available: {info['version']} → {latest['version_number']}{Colors.END}")
            
            # Find primary file
            if not latest.get("files"):
                print(f"{Colors.RED} No files available for download{Colors.END}")
                continue
                
            primary_file = next((f for f in latest["files"] if f.get("primary")), latest["files"][0])
            
            # Determine paths
            content_path = self.get_content_path(content_type)
            old_path = content_path / info["filename"]
            new_filename = primary_file["filename"]
            new_path = content_path / new_filename
            
            # Download new version
            success = ModrinthAPI.download_file(primary_file["url"], new_path)
            
            if success:
                # Remove old version if different filename
                if old_path != new_path and old_path.exists():
                    try:
                        os.remove(old_path)
                    except OSError:
                        print(f"{Colors.YELLOW} Warning: Could not remove old file {old_path}{Colors.END}")
                
                # Update record
                content_dict[project_id] = {
                    "name": info["name"],
                    "version": latest["version_number"],
                    "filename": new_filename,
                    "installed_at": latest["date_published"]
                }
                self._save_installed_content()
                
                print(f"{Colors.GREEN} Updated successfully{Colors.END}")
            else:
                print(f"{Colors.RED} Update failed{Colors.END}")

def main():
    # Configure argument parser
    parser = argparse.ArgumentParser(
        description="Minecraft Manager - A tool for managing Minecraft mods, resource packs, and shader packs"
    )
    
    # Global arguments
    parser.add_argument(
        "--minecraft-path", 
        type=Path,
        help="Path to Minecraft installation (default: auto-detect)"
    )
    parser.add_argument(
        "--game-version",
        help="Minecraft game version to filter by"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for content")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--type", 
        choices=[t.value for t in ContentType],
        required=True,
        help="Type of content to search for"
    )
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install content by ID")
    install_parser.add_argument("project_id", help="Project ID to install")
    install_parser.add_argument(
        "--type", 
        choices=[t.value for t in ContentType],
        required=True,
        help="Type of content to install"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List installed content")
    list_parser.add_argument(
        "--type", 
        choices=[t.value for t in ContentType],
        required=True,
        help="Type of content to list"
    )
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall content")
    uninstall_parser.add_argument("name", help="Name of content to uninstall (partial match)")
    uninstall_parser.add_argument(
        "--type", 
        choices=[t.value for t in ContentType],
        required=True,
        help="Type of content to uninstall"
    )
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update installed content")
    update_parser.add_argument(
        "--type", 
        choices=[t.value for t in ContentType],
        help="Type of content to update (default: all)"
    )
    update_parser.add_argument(
        "--name",
        help="Name of specific content to update (partial match)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize manager
    manager = MinecraftManager(args.minecraft_path)
    
    # Handle commands
    if args.command == "search":
        content_type = ContentType(args.type)
        manager.search(args.query, content_type, args.game_version)
    
    elif args.command == "install":
        content_type = ContentType(args.type)
        manager.install(args.project_id, content_type, args.game_version)
    
    elif args.command == "list":
        content_type = ContentType(args.type)
        manager.list_installed(content_type)
    
    elif args.command == "uninstall":
        content_type = ContentType(args.type)
        manager.uninstall(args.name, content_type)
    
    elif args.command == "update":
        content_type = ContentType(args.type) if args.type else None
        manager.update(content_type, args.name)
    
    else:
        # No command or invalid command
        parser.print_help()

if __name__ == "__main__":
    # Use Windows color support if on Windows
    if platform.system() == "Windows":
        os.system("color")
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.END}")
        sys.exit(0)