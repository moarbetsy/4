# UB

A modern, web-based dashboard for managing Camoufox anti-detect browser profiles with advanced fingerprinting capabilities.

## Features

### 🎭 Advanced Anti-Detection
- **Invisible to all anti-bot systems** - Camoufox performs better than most commercial anti-bot browsers
- **Fingerprint injection & rotation** without JavaScript injection
- **Complete navigator properties spoofing** (device, OS, hardware, browser, etc.)
- **Screen, resolution, window & viewport properties** spoofing
- **Geolocation, timezone & locale** spoofing
- **Font spoofing & anti-fingerprinting**
- **WebGL parameters, extensions & shader precision** spoofing
- **WebRTC IP spoofing** at the protocol level
- **Media devices, voices, speech playback rate** spoofing

### 🖥️ Dashboard Features
- **Modern dark theme interface** with responsive design
- **Profile management** - Create, edit, delete browser profiles
- **Bulk operations** - Launch or delete multiple profiles at once
- **Real-time status monitoring** - See which profiles are active
- **Search and filtering** - Quickly find specific profiles
- **Advanced configuration** - Customize fingerprinting settings per profile

### 🚀 Quality of Life Features
- **Human-like mouse movement** for natural interaction
- **Ad blocking & circumvention** built-in
- **No CSS animations** for faster loading
- **Memory optimized** for efficiency
- **Auto fingerprint injection** using BrowserForge

## Installation

### Prerequisites
- Python 3.8 or higher
- pip3
- Git

### Quick Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd camoufox-dashboard
   ```

2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Start the dashboard:**
   ```bash
   ./run.sh
   ```

4. **Access the dashboard:**
   - Dashboard: http://localhost:12000
   - API Documentation: http://localhost:12000/docs

### Manual Installation

If you prefer manual installation:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Install Playwright browsers
playwright install firefox

# Start the server
python3 -m uvicorn main:app --host 0.0.0.0 --port 12000 --reload
```

## Usage

### Creating Profiles

1. Click the **"Add Profile"** button in the dashboard
2. Fill in the profile details:
   - **Profile Name**: A unique name for your profile
   - **Operating System**: Windows, macOS, or Linux
   - **Timezone**: Select the appropriate timezone
3. Click **"Create Profile"**

The system will automatically generate advanced fingerprinting configurations based on your selections.

### Managing Profiles

- **Launch Profile**: Click the rocket icon to start a browser instance
- **Delete Profile**: Click the delete icon to remove a profile
- **Bulk Operations**: Select multiple profiles and use the bulk action buttons
- **Search**: Use the search bar to filter profiles by name, OS, or timezone

### API Usage

The dashboard provides a REST API for programmatic access:

```python
import requests

# Get all profiles
response = requests.get('http://localhost:12000/api/profiles')
profiles = response.json()

# Create a new profile
profile_data = {
    "name": "My Profile",
    "os": "Windows",
    "timezone": "GMT+01:00"
}
response = requests.post('http://localhost:12000/api/profiles', json=profile_data)

# Launch a profile
profile_id = "your-profile-id"
response = requests.post(f'http://localhost:12000/api/profiles/{profile_id}/launch')
```

## Configuration

### Profile Configuration

Each profile automatically generates a comprehensive configuration including:

- **Navigator Properties**: User agent, platform, language, hardware concurrency
- **Screen Properties**: Resolution, color depth, pixel ratio
- **WebGL Properties**: Renderer, vendor, extensions, parameters
- **Geolocation**: Coordinates based on timezone
- **Fonts**: OS-appropriate font lists
- **Media Devices**: Cameras, microphones, speakers
- **Timezone & Locale**: Regional settings

### Advanced Configuration

You can customize the fingerprinting behavior by modifying the `generate_camoufox_config` method in `backend/main.py`.

## Architecture

### Backend (FastAPI)
- **main.py**: Main FastAPI application with API endpoints
- **camoufox_manager.py**: Enhanced Camoufox browser session management
- **requirements.txt**: Python dependencies

### Frontend (Vanilla JavaScript)
- **index.html**: Main dashboard interface
- **app.js**: Dashboard functionality and API integration

### Key Components

1. **ProfileManager**: Handles profile CRUD operations and persistence
2. **CamoufoxManager**: Manages browser sessions with advanced fingerprinting
3. **BrowserForge Integration**: Generates realistic fingerprints
4. **Async API**: Non-blocking browser operations

## API Endpoints

### Profiles
- `GET /api/profiles` - List all profiles
- `POST /api/profiles` - Create a new profile
- `GET /api/profiles/{id}` - Get profile details
- `DELETE /api/profiles/{id}` - Delete a profile

### Browser Control
- `POST /api/profiles/{id}/launch` - Launch browser instance
- `POST /api/profiles/{id}/stop` - Stop browser instance
- `GET /api/profiles/{id}/status` - Get profile status
- `POST /api/profiles/{id}/navigate` - Navigate to URL

### System
- `GET /health` - Health check and system status
- `GET /api/sessions` - List active browser sessions

## Troubleshooting

### Common Issues

1. **Camoufox not found**
   ```bash
   pip install camoufox
   ```

2. **Playwright browsers missing**
   ```bash
   playwright install firefox
   ```

3. **Permission denied on scripts**
   ```bash
   chmod +x setup.sh run.sh
   ```

4. **Port already in use**
   - Change the port in `run.sh` and `backend/main.py`
   - Or stop the process using port 12000

### Logs

Check the console output when running `./run.sh` for detailed error messages and debugging information.

## Security Considerations

- This tool is designed for legitimate web scraping and testing purposes
- Ensure compliance with website terms of service and applicable laws
- Use responsibly and ethically
- Consider rate limiting and respectful crawling practices

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check the console logs for error messages
4. Open an issue on the repository

---

**Built with ❤️ using Camoufox, FastAPI, and modern web technologies.**

