# Snappr API MCP Server

An MCP (Model Context Protocol) server that provides tools to interact with the Snappr Photography API.

## Features

This MCP server exposes the following Snappr API capabilities:

- **Coverage Checking**: Verify if photography services are available in specific locations
- **Availability Search**: Find open time slots for photoshoots
- **Booking Management**: Create, list, and retrieve photography bookings
- **Photo Editing**: Commission photo editing jobs
- **Media Retrieval**: Download photos and videos from completed bookings

## Setup

### Option 1: Using uvx (Recommended)

This project now supports `uvx` for easy, isolated execution without managing virtual environments.

1. **Install uv/uvx** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Configure API Access**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Snappr API key
   ```

3. **Run directly with uvx**:
   ```bash
   # From the project directory
   uvx --from . snappr-mcp

   # Or use the provided script
   ./run_server.sh
   ```

### Option 2: Traditional Setup

1. **Install Dependencies**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv add "mcp[cli]" httpx
   ```

2. **Configure API Access**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Snappr API key
   ```

3. **Run the server**:
   ```bash
   python app.py
   ```

## Get Your API Key

- Log into your Snappr Photography Portal
- Navigate to API settings
- Generate or copy your API key

## Available Tools

### `list_shoot_types`
Get available photography shoot types from Snappr.

**Parameters:** None

### `list_editing_job_types`
Get available photo editing job types from Snappr.

**Parameters:** None

### `check_coverage`
Check if Snappr photography services are available in a location for a specific shoot type.

**Parameters:**
- `address` (required): Full address or location
- `shoot_type` (required): Type of photoshoot (use list_shoot_types first)
- `latitude` (optional): Latitude coordinate
- `longitude` (optional): Longitude coordinate

### `find_availability`
Find available time slots for photography bookings.

**Parameters:**
- `location` (required): Location for the photoshoot
- `shoot_type` (required): Type of shoot (e.g., "headshots", "event", "product")
- `date_from` (required): Start date (YYYY-MM-DD)
- `date_to` (required): End date (YYYY-MM-DD)
- `duration` (optional): Shoot duration in minutes

### `create_booking`
Create a new photography booking.

**Parameters:**
- `shoot_type` (required): Type of photoshoot
- `location` (required): Shoot location address
- `start_time` (required): Booking start time (ISO 8601)
- `duration` (required): Duration in minutes
- `contact_name` (required): Primary contact name
- `contact_email` (required): Primary contact email
- `contact_phone` (optional): Primary contact phone
- `notes` (optional): Additional requirements

### `list_bookings`
List photography bookings with optional filtering.

**Parameters:**
- `status` (optional): Filter by booking status
- `limit` (optional): Maximum results to return
- `offset` (optional): Number of results to skip

### `get_booking`
Get detailed information about a specific booking.

**Parameters:**
- `booking_id` (required): The unique booking identifier

### `create_editing_job`
Create a photo editing job.

**Parameters:**
- `editing_type` (required): Type of editing
- `booking_id` (optional): Source booking ID
- `instructions` (optional): Specific editing instructions
- `image_urls` (optional): Array of image URLs to edit

### `get_booking_media`
Retrieve media from a completed booking.

**Parameters:**
- `booking_id` (required): The booking ID
- `media_type` (optional): "photos", "videos", or "all"

## Running the Server

### With uvx (Recommended)
```bash
# From project directory
./run_server.sh

# Or directly
uvx --from . snappr-mcp
```

### With Claude Desktop

Add this to your Claude Desktop MCP configuration:

#### Using uvx:
```json
{
  "mcpServers": {
    "snappr-api": {
      "command": "uvx",
      "args": ["--from", "/path/to/snappr-mcp", "snappr-mcp"],
      "env": {
        "SNAPPR_BASE_URL": "https://api.snappr.com/",
        "SNAPPR_API_KEY": "your_api_key_here",
      }
    }
  }
}
```

#### Using shell script:
```json
{
  "mcpServers": {
    "snappr-api": {
      "command": "/path/to/snappr-mcp/run_server.sh",
      "args": [],
      "env": {
        "SNAPPR_BASE_URL": "https://api.snappr.com/",
        "SNAPPR_API_KEY": "your_api_key_here",
      }
    }
  }
}
```

#### Traditional method:
```json
{
  "mcpServers": {
    "snappr-api": {
      "command": "python",
      "args": ["/path/to/snappr-mcp/app.py"],
      "env": {
        "SNAPPR_BASE_URL": "https://api.snappr.com/",
        "SNAPPR_API_KEY": "your_api_key_here",
      }
    }
  }
}
```

## Environment Variables

- `SNAPPR_API_KEY`: Your Snappr API key (required)
- `SNAPPR_BASE_URL`: Set to "https://api.snappr.com/" for production environment (default: "https://api.snappr.com/")

## Example Usage

Once connected to Claude Desktop, you can use natural language:

- "What shoot types are available on Snappr?"
- "Show me the editing job types"
- "Check if Snappr covers headshot photography in downtown San Francisco"
- "Find available headshot appointments next week in New York"
- "Create a product photography booking for next Tuesday at 2 PM"
- "List all my recent bookings"
- "Get the photos from booking ABC123"

## Troubleshooting

### MCP Server Not Working After Updates

**Problem:** Claude Desktop shows "Invalid Snappr API key" or other errors after making code changes.

**Solution:** Clear the uvx/uv cache and restart Claude Desktop:

```bash
# Clear the uv cache (this usually fixes the issue)
uv cache clean

# Restart Claude Desktop completely (quit and reopen)
```

**Why this happens:** uvx caches packages and may use an outdated version even after you make changes to your local code.

## API Documentation

For detailed Snappr API documentation, visit: https://docs.snappr.com/

## Support

This MCP server provides a bridge to Snappr's photography and editing services. For API-specific issues, contact Snappr support through your Photography Portal.