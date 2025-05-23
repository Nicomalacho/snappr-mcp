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

3. **Get Your API Key**:
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

### Standalone Testing
```bash
python app.py
```

### With Claude Desktop

Add this to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "snappr-api": {
      "command": "python",
      "args": ["/path/to/snappr-api/app.py"],
      "env": {
        "SNAPPR_API_KEY": "your_api_key_here",
        "SNAPPR_USE_SANDBOX": "true"
      }
    }
  }
}
```

## Environment Variables

- `SNAPPR_API_KEY`: Your Snappr API key (required)
- `SNAPPR_USE_SANDBOX`: Set to "true" for sandbox environment (default: false)

## Example Usage

Once connected to Claude Desktop, you can use natural language:

- "What shoot types are available on Snappr?"
- "Show me the editing job types"
- "Check if Snappr covers headshot photography in downtown San Francisco"
- "Find available headshot appointments next week in New York"
- "Create a product photography booking for next Tuesday at 2 PM"
- "List all my recent bookings"
- "Get the photos from booking ABC123"

## API Documentation

For detailed Snappr API documentation, visit: https://docs.snappr.com/

## Support

This MCP server provides a bridge to Snappr's photography and editing services. For API-specific issues, contact Snappr support through your Photography Portal.