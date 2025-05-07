# Minecraft Manager

A powerful command-line tool for managing Minecraft resource packs, shader packs, and mods through the Modrinth API.

## Features

- **Simple Command-Line Interface** with colored output for better readability
- **Search** for mods, resource packs, and shader packs directly from Modrinth
- **Install** content with a single command
- **List** all installed content by type
- **Uninstall** content easily
- **Update** individual or all installed content
- **Automatic detection** of Minecraft installation directory
- **Version filtering** to find content compatible with your game version

## Installation

### Requirements
- Python 3.6+
- `requests` library

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/minecraft-manager.git
   cd minecraft-manager
   ```

2. Install dependencies:
   ```bash
   pip install requests
   ```

3. Make the script executable (Linux/macOS):
   ```bash
   chmod +x minecraft_manager.py
   ```

## Usage

### Basic Commands

Search for content:
```bash
python minecraft_manager.py search "query" --type [mod|resourcepack|shader]
```

Install content by ID:
```bash
python minecraft_manager.py install PROJECT_ID --type [mod|resourcepack|shader]
```

List installed content:
```bash
python minecraft_manager.py list --type [mod|resourcepack|shader]
```

Uninstall content:
```bash
python minecraft_manager.py uninstall "name" --type [mod|resourcepack|shader]
```

Update content:
```bash
python minecraft_manager.py update [--type TYPE] [--name "name"]
```

### Examples

Search for a resource pack:
```bash
python minecraft_manager.py search "faithful" --type resourcepack
```

Search for mods for a specific Minecraft version:
```bash
python minecraft_manager.py search "jei" --type mod --game-version 1.19.2
```

List all installed shader packs:
```bash
python minecraft_manager.py list --type shader
```

Update all mods:
```bash
python minecraft_manager.py update --type mod
```

## Custom Minecraft Installation Path

If your Minecraft installation is in a non-standard location, you can specify the path:

```bash
python minecraft_manager.py --minecraft-path "/path/to/minecraft" [command]
```

## How It Works

Minecraft Manager interacts with the Modrinth API to fetch content information and download files. It keeps track of installed content in a configuration file (`minecraft_manager_config.json`) within your Minecraft directory.

The tool automatically organizes downloads into the appropriate folders:
- Mods → `.minecraft/mods/`
- Resource Packs → `.minecraft/resourcepacks/`
- Shader Packs → `.minecraft/shaderpacks/`

## Directory Structure

```
.minecraft/
├── mods/               # Installed mods
├── resourcepacks/      # Installed resource packs
├── shaderpacks/        # Installed shader packs
└── minecraft_manager_config.json  # Installation tracking
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Modrinth](https://modrinth.com/) for providing the API
- Minecraft community for inspiration

---

Made for the Minecraft community
