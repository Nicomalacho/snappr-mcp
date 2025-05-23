#!/usr/bin/env python3
"""
Snappr API MCP Server

This MCP server provides tools to interact with the Snappr API for:
- Photography coverage checking
- Availability scheduling
- Booking management
- Photo editing services
- Media retrieval

Based on Snappr API documentation: https://docs.snappr.com/

DEBUGGING NOTES:
================
If list_shoot_types is not returning data, check these common issues:

1. **API Key Missing**: Make sure SNAPPR_API_KEY environment variable is set
   - Run: export SNAPPR_API_KEY=your_api_key_here

2. **Wrong Environment**: Check if you need sandbox vs production
   - For sandbox: export SNAPPR_USE_SANDBOX=true
   - For production: export SNAPPR_USE_SANDBOX=false (or leave unset)

3. **API Endpoint Issues**: The /shoottypes endpoint should work according to docs
   - Production: https://api.snappr.com/shoottypes
   - Sandbox: https://sandbox.snappr.com/shoottypes

4. **Authentication Problems**: Check if the API key has proper permissions
   - The key should start with Bearer authentication
   - Check the logs for HTTP status codes (401 = unauthorized, 404 = endpoint not found)

5. **Response Structure**: Official docs show results in "results" array
   - Expected: {"results": [{"name": "food", "display_name": "Food"}], "count": 10}

Look for SNAPPR_DEBUG and SNAPPR_ERROR log messages for detailed debugging info.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, Resource, Prompt, ServerCapabilities
import mcp.server.stdio
from pydantic import BaseModel


# Snappr API Configuration
SNAPPR_BASE_URL = "https://api.snappr.com/"
SNAPPR_SANDBOX_URL = "https://sandbox.snappr.com/"


class SnapprClient:
    """HTTP client for Snappr API interactions"""

    def __init__(self, api_key: str, use_sandbox: bool = False):
        self.api_key = api_key
        self.base_url = SNAPPR_SANDBOX_URL if use_sandbox else SNAPPR_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Snappr-MCP-Server/1.0",
            "accept-version": "1.0.0"
        }

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to Snappr API"""
        print(f"SNAPPR_HTTP_DEBUG: Starting GET request to endpoint: {endpoint}")
        print(f"SNAPPR_HTTP_DEBUG: Params: {params}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = urljoin(self.base_url, endpoint)
                print(f"SNAPPR_HTTP_DEBUG: Full URL: {url}")
                print(f"SNAPPR_HTTP_DEBUG: Headers: {self.headers}")

                response = await client.get(url, headers=self.headers, params=params)

                print(f"SNAPPR_HTTP_DEBUG: Response status: {response.status_code}")
                print(f"SNAPPR_HTTP_DEBUG: Response headers: {dict(response.headers)}")
                print(f"SNAPPR_HTTP_DEBUG: Response text: {response.text}")

                response.raise_for_status()

                result = response.json()
                print(f"SNAPPR_HTTP_DEBUG: Parsed JSON: {result}")
                return result

        except httpx.ConnectError as e:
            error_msg = f"SNAPPR_HTTP_ERROR: Failed to connect to Snappr API: {str(e)}"
            print(error_msg)
            raise ConnectionError(error_msg)
        except httpx.TimeoutException as e:
            error_msg = f"SNAPPR_HTTP_ERROR: Snappr API request timed out: {str(e)}"
            print(error_msg)
            raise TimeoutError(error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"SNAPPR_HTTP_ERROR: HTTP {e.response.status_code}: {e.response.text}"
            print(error_msg)
            if e.response.status_code == 401:
                raise ValueError("Invalid Snappr API key. Please check your SNAPPR_API_KEY environment variable.")
            elif e.response.status_code == 404:
                raise ValueError(f"Snappr API endpoint not found: {endpoint}")
            else:
                raise ValueError(f"Snappr API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            error_msg = f"SNAPPR_HTTP_ERROR: Unexpected error: {str(e)}"
            print(error_msg)
            raise

    async def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request to Snappr API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = urljoin(self.base_url, endpoint)
                response = await client.post(url, headers=self.headers, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to Snappr API: {str(e)}")
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Snappr API request timed out: {str(e)}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid Snappr API key. Please check your SNAPPR_API_KEY environment variable.")
            elif e.response.status_code == 404:
                raise ValueError(f"Snappr API endpoint not found: {endpoint}")
            else:
                raise ValueError(f"Snappr API error ({e.response.status_code}): {e.response.text}")


# Initialize the MCP server
app = Server("snappr-api")

# Global client instance
snappr_client: Optional[SnapprClient] = None


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available Snappr API tools"""
    return [
        Tool(
            name="list_shoot_types",
            description="Get available photography shoot types",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_editing_job_types",
            description="Get available photo editing job types",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="check_coverage",
            description="Check if Snappr photography services are available in a specific location for a shoot type",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Address of the shoot location. Must be a Google Maps valid address."
                    },
                    "shoot_type": {
                        "type": "string",
                        "description": "Type of photoshoot (use list_shoot_types to see available options)"
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Optional latitude coordinate"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Optional longitude coordinate"
                    }
                },
                "required": ["address", "shoot_type"]
            }
        ),
        Tool(
            name="find_availability",
            description="Find available time slots for photography bookings",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location for the photoshoot"
                    },
                    "shoot_type": {
                        "type": "string",
                        "description": "Type of photoshoot (e.g., 'headshots', 'event', 'product')"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date for availability search (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date for availability search (YYYY-MM-DD)"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Shoot duration in minutes"
                    }
                },
                "required": ["location", "shoot_type", "date_from", "date_to"]
            }
        ),
        Tool(
            name="create_booking",
            description="Create a new photography booking",
            inputSchema={
                "type": "object",
                "properties": {
                    "shoot_type": {
                        "type": "string",
                        "description": "Type of photoshoot"
                    },
                    "location": {
                        "type": "string",
                        "description": "Shoot location address"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Booking start time (ISO 8601 format)"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Duration in minutes"
                    },
                    "contact_name": {
                        "type": "string",
                        "description": "Primary contact name"
                    },
                    "contact_email": {
                        "type": "string",
                        "description": "Primary contact email"
                    },
                    "contact_phone": {
                        "type": "string",
                        "description": "Primary contact phone number"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes or requirements"
                    }
                },
                "required": ["shoot_type", "location", "start_time", "duration", "contact_name", "contact_email"]
            }
        ),
        Tool(
            name="list_bookings",
            description="List photography bookings with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by booking status"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of results to skip"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_booking",
            description="Get detailed information about a specific booking",
            inputSchema={
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The unique booking identifier"
                    }
                },
                "required": ["booking_id"]
            }
        ),
        Tool(
            name="create_editing_job",
            description="Create a photo editing job",
            inputSchema={
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "Booking ID to edit photos from"
                    },
                    "editing_type": {
                        "type": "string",
                        "description": "Type of editing (e.g., 'basic', 'advanced', 'retouching')"
                    },
                    "instructions": {
                        "type": "string",
                        "description": "Specific editing instructions"
                    },
                    "image_urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "URLs of images to edit"
                    }
                },
                "required": ["editing_type"]
            }
        ),
        Tool(
            name="get_booking_media",
            description="Retrieve media (photos/videos) from a completed booking",
            inputSchema={
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": "The booking ID to get media from"
                    },
                    "media_type": {
                        "type": "string",
                        "description": "Type of media to retrieve ('photos', 'videos', 'all')"
                    }
                },
                "required": ["booking_id"]
            }
        )
    ]


def get_client() -> SnapprClient:
    """Get configured Snappr client"""
    global snappr_client
    if snappr_client is None:
        print("SNAPPR_CLIENT_DEBUG: Initializing new Snappr client")

        api_key = os.getenv("SNAPPR_API_KEY")
        print(f"SNAPPR_CLIENT_DEBUG: API Key found: {'Yes' if api_key else 'No'}")

        if not api_key:
            print("SNAPPR_CLIENT_ERROR: SNAPPR_API_KEY environment variable is not set!")
            print("SNAPPR_CLIENT_ERROR: Please set your API key with: export SNAPPR_API_KEY=your_api_key_here")
            raise ValueError("SNAPPR_API_KEY environment variable is required")

        if api_key:
            print(f"SNAPPR_CLIENT_DEBUG: API Key length: {len(api_key)}")
            print(f"SNAPPR_CLIENT_DEBUG: API Key starts with: {api_key[:10]}...")

        use_sandbox = os.getenv("SNAPPR_USE_SANDBOX", "false").lower() == "true"
        print(f"SNAPPR_CLIENT_DEBUG: Using sandbox: {use_sandbox}")

        snappr_client = SnapprClient(api_key, use_sandbox)
        print(f"SNAPPR_CLIENT_DEBUG: Client initialized with base URL: {snappr_client.base_url}")
        print(f"SNAPPR_CLIENT_DEBUG: Authorization header: Bearer {api_key[:10]}...")

    return snappr_client


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle tool calls to Snappr API"""
    try:
        client = get_client()

        if name == "list_shoot_types":
            return await handle_list_shoot_types(client, arguments)
        elif name == "list_editing_job_types":
            return await handle_list_editing_job_types(client, arguments)
        elif name == "check_coverage":
            return await handle_check_coverage(client, arguments)
        elif name == "find_availability":
            return await handle_find_availability(client, arguments)
        elif name == "create_booking":
            return await handle_create_booking(client, arguments)
        elif name == "list_bookings":
            return await handle_list_bookings(client, arguments)
        elif name == "get_booking":
            return await handle_get_booking(client, arguments)
        elif name == "create_editing_job":
            return await handle_create_editing_job(client, arguments)
        elif name == "get_booking_media":
            return await handle_get_booking_media(client, arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [{"type": "text", "text": f"Error: {str(e)}"}]


async def handle_list_shoot_types(client: SnapprClient, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get available photography shoot types"""
    print("SNAPPR_DEBUG: Starting list_shoot_types request")

    try:
        # Log the API call details - using the correct endpoint from docs
        endpoint = "shoottypes"
        full_url = urljoin(client.base_url, endpoint)
        print(f"SNAPPR_DEBUG: Making GET request to: {full_url}")
        print(f"SNAPPR_DEBUG: Using headers: {client.headers}")

        result = await client.get(endpoint)

        print(f"SNAPPR_DEBUG: API response received: {result}")
        print(f"SNAPPR_DEBUG: Response type: {type(result)}")

        # Debug: Show raw API response
        message = f"📸 Available Photography Shoot Types:\n\n"
        message += f"Raw API Response: {result}\n\n"

        # Based on official Snappr API docs, the response structure is:
        # {
        #   "results": [
        #     {"name": "food", "display_name": "Food"},
        #     {"name": "real-estate", "display_name": "Real Estate"}
        #   ],
        #   "count": 10,
        #   "limit": 100,
        #   "offset": 0,
        #   "total": 10
        # }

        if isinstance(result, dict) and "results" in result:
            shoot_types = result.get("results", [])
            total = result.get("total", 0)
            count = result.get("count", 0)

            print(f"SNAPPR_DEBUG: Found {len(shoot_types)} shoot types in results")

            if shoot_types and len(shoot_types) > 0:
                message += f"Found {count} of {total} shoot types:\n\n"
                for i, shoot_type in enumerate(shoot_types):
                    print(f"SNAPPR_DEBUG: Processing shoot_type {i}: {shoot_type}")
                    if isinstance(shoot_type, dict):
                        name = shoot_type.get("name", "Unknown")
                        display_name = shoot_type.get("display_name", name)

                        message += f"• **{display_name}** (`{name}`)\n"
                    else:
                        message += f"• {str(shoot_type)}\n"
            else:
                message += "No shoot types found in results array."
        else:
            # Fallback - try other possible structures
            shoot_types = None
            if isinstance(result, dict):
                # Try different possible keys
                shoot_types = (
                    result.get("data", []) or
                    result.get("shoot_types", []) or
                    result.get("shoottypes", []) or
                    result.get("types", [])
                )
                print(f"SNAPPR_DEBUG: Fallback - extracted shoot_types: {shoot_types}")
            elif isinstance(result, list):
                shoot_types = result
                print(f"SNAPPR_DEBUG: Response is a list directly: {shoot_types}")

            if shoot_types and len(shoot_types) > 0:
                message += f"Found {len(shoot_types)} shoot types (fallback parsing):\n\n"
                for i, shoot_type in enumerate(shoot_types):
                    print(f"SNAPPR_DEBUG: Processing shoot_type {i}: {shoot_type}")
                    if isinstance(shoot_type, dict):
                        name = shoot_type.get("name", shoot_type.get("id", "Unknown"))
                        display_name = shoot_type.get("display_name", shoot_type.get("title", name))

                        message += f"• **{display_name}** (`{name}`)\n"
                    elif isinstance(shoot_type, str):
                        message += f"• {shoot_type}\n"
                    else:
                        message += f"• {str(shoot_type)}\n"
            else:
                message += "No shoot types found in response."
                message += f"\nDebugging info:\n"
                message += f"- Response type: {type(result)}\n"
                message += f"- Response keys (if dict): {list(result.keys()) if isinstance(result, dict) else 'N/A'}\n"
                message += f"- Response length (if list): {len(result) if isinstance(result, list) else 'N/A'}\n"

        print(f"SNAPPR_DEBUG: Returning message: {message}")
        return [{"type": "text", "text": message}]

    except Exception as e:
        error_msg = f"SNAPPR_ERROR: Exception in handle_list_shoot_types: {str(e)}"
        print(error_msg)
        return [{"type": "text", "text": error_msg}]


async def handle_list_editing_job_types(client: SnapprClient, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get available photo editing job types"""
    result = await client.get("editing-job-types")

    # Debug: Show raw API response
    message = f"🎨 Available Photo Editing Job Types:\n\n"
    message += f"Raw API Response: {result}\n\n"

    # Try different possible response structures
    editing_types = (
        result.get("editing_job_types", []) or
        result.get("data", []) or
        result.get("types", []) or
        result.get("editing_types", []) or
        (result if isinstance(result, list) else [])
    )

    if editing_types:
        message += "Found editing job types:\n\n"
        for editing_type in editing_types:
            if isinstance(editing_type, str):
                message += f"• {editing_type}\n"
            elif isinstance(editing_type, dict):
                name = editing_type.get("name", editing_type.get("display_name", editing_type.get("type", "Unknown")))
                description = editing_type.get("description", "")
                price = editing_type.get("price", "")

                message += f"• **{name}**"
                if price:
                    message += f" - ${price}"
                if description:
                    message += f"\n  {description}"
                message += "\n\n"
    else:
        message += "No editing job types found in response."

    return [{"type": "text", "text": message}]


async def handle_check_coverage(client: SnapprClient, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check photography coverage for a location and shoot type"""
    params = {
        "address": args["address"],
        "shoottype": args["shoot_type"]  # Snappr API uses 'shoottype' not 'shoot_type'
    }

    if "latitude" in args and "longitude" in args:
        params.update({
            "latitude": args["latitude"],
            "longitude": args["longitude"]
        })

    result = await client.get("coverage", params)

    # Use the correct field name from actual Snappr API response
    coverage_available = result.get("coverage", False)
    coverage_status = "✅ Available" if coverage_available else "❌ Not Available"

    message = f"📍 Snappr Photography Coverage Check:\n\n"
    message += f"**Location:** {args['address']}\n"
    message += f"**Shoot Type:** {args['shoot_type']}\n"
    message += f"**Status:** {coverage_status}\n\n"

    # Add location coordinates if available in response
    if "latitude" in result and "longitude" in result:
        message += f"**Coordinates:** {result['latitude']}, {result['longitude']}\n"

    if not coverage_available:
        message += "ℹ️ Unfortunately, Snappr photography services are not available in this location for this shoot type.\n"
        message += "You may want to try a nearby location or contact Snappr directly for alternatives."
    else:
        message += "🎉 Great! Snappr photography services are available in this location for this shoot type.\n"
        message += "You can proceed with booking a photographer."

    return [{"type": "text", "text": message}]


async def handle_find_availability(client: SnapprClient, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find available time slots"""
    params = {
        "location": args["location"],
        "shoot_type": args["shoot_type"],
        "date_from": args["date_from"],
        "date_to": args["date_to"]
    }

    if "duration" in args:
        params["duration"] = args["duration"]

    result = await client.get("availability", params)

    message = f"Available Time Slots for {args['shoot_type']} in {args['location']}:\n\n"

    slots = result.get("available_slots", [])
    if slots:
        for slot in slots[:10]:  # Show first 10 slots
            message += f"📅 {slot.get('date')} at {slot.get('time')}\n"
    else:
        message += "No available slots found for the specified criteria."

    return [{"type": "text", "text": message}]


async def handle_create_booking(client: SnapprClient, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create a new photography booking"""
    booking_data = {
        "shoot_type": args["shoot_type"],
        "location": args["location"],
        "start_time": args["start_time"],
        "duration": args["duration"],
        "contact": {
            "name": args["contact_name"],
            "email": args["contact_email"],
            "phone": args.get("contact_phone", "")
        }
    }

    if "notes" in args:
        booking_data["notes"] = args["notes"]

    result = await client.post("bookings", booking_data)

    booking_id = result.get("booking_id")
    status = result.get("status", "pending")

    message = f"✅ Booking Created Successfully!\n\n"
    message += f"Booking ID: {booking_id}\n"
    message += f"Status: {status.title()}\n"
    message += f"Shoot Type: {args['shoot_type']}\n"
    message += f"Location: {args['location']}\n"
    message += f"Scheduled: {args['start_time']}\n"
    message += f"Duration: {args['duration']} minutes\n"

    return [{"type": "text", "text": message}]


async def handle_list_bookings(client: SnapprClient, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """List photography bookings"""
    params = {}

    if "status" in args:
        params["status"] = args["status"]
    if "limit" in args:
        params["limit"] = args["limit"]
    if "offset" in args:
        params["offset"] = args["offset"]

    result = await client.get("bookings", params)

    bookings = result.get("bookings", [])
    total = result.get("total", len(bookings))

    message = f"Photography Bookings (Total: {total}):\n\n"

    if bookings:
        for booking in bookings:
            message += f"📷 {booking.get('booking_id')} - {booking.get('shoot_type')}\n"
            message += f"   Status: {booking.get('status', 'unknown').title()}\n"
            message += f"   Location: {booking.get('location', 'N/A')}\n"
            message += f"   Date: {booking.get('scheduled_date', 'N/A')}\n\n"
    else:
        message += "No bookings found."

    return [{"type": "text", "text": message}]


async def handle_get_booking(client: SnapprClient, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get detailed booking information"""
    booking_id = args["booking_id"]
    result = await client.get(f"bookings/{booking_id}")

    message = f"Booking Details - {booking_id}:\n\n"
    message += f"Shoot Type: {result.get('shoot_type', 'N/A')}\n"
    message += f"Status: {result.get('status', 'unknown').title()}\n"
    message += f"Location: {result.get('location', 'N/A')}\n"
    message += f"Scheduled: {result.get('start_time', 'N/A')}\n"
    message += f"Duration: {result.get('duration', 'N/A')} minutes\n"
    message += f"Photographer: {result.get('photographer', {}).get('name', 'TBD')}\n"

    if result.get('notes'):
        message += f"Notes: {result['notes']}\n"

    if result.get('status') == 'completed':
        message += f"\n📸 Photos Ready: {result.get('photo_count', 0)} images available\n"

    return [{"type": "text", "text": message}]


async def handle_create_editing_job(client: SnapprClient, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create a photo editing job"""
    editing_data = {
        "editing_type": args["editing_type"]
    }

    if "booking_id" in args:
        editing_data["booking_id"] = args["booking_id"]
    if "instructions" in args:
        editing_data["instructions"] = args["instructions"]
    if "image_urls" in args:
        editing_data["image_urls"] = args["image_urls"]

    result = await client.post("editing-jobs", editing_data)

    job_id = result.get("job_id")
    status = result.get("status", "pending")
    estimated_completion = result.get("estimated_completion", "N/A")

    message = f"🎨 Editing Job Created Successfully!\n\n"
    message += f"Job ID: {job_id}\n"
    message += f"Status: {status.title()}\n"
    message += f"Editing Type: {args['editing_type']}\n"
    message += f"Estimated Completion: {estimated_completion}\n"

    if "booking_id" in args:
        message += f"Source Booking: {args['booking_id']}\n"

    return [{"type": "text", "text": message}]


async def handle_get_booking_media(client: SnapprClient, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Retrieve media from a booking"""
    booking_id = args["booking_id"]
    media_type = args.get("media_type", "all")

    params = {"type": media_type} if media_type != "all" else {}
    result = await client.get(f"bookings/{booking_id}/media", params)

    media_items = result.get("media", [])

    message = f"Media from Booking {booking_id}:\n\n"

    if media_items:
        photos = [item for item in media_items if item.get("type") == "photo"]
        videos = [item for item in media_items if item.get("type") == "video"]

        if photos:
            message += f"📸 Photos ({len(photos)}):\n"
            for photo in photos:
                message += f"   • {photo.get('filename', 'Unknown')} - {photo.get('url', 'No URL')}\n"

        if videos:
            message += f"\n🎥 Videos ({len(videos)}):\n"
            for video in videos:
                message += f"   • {video.get('filename', 'Unknown')} - {video.get('url', 'No URL')}\n"
    else:
        message += "No media available for this booking."

    return [{"type": "text", "text": message}]


if __name__ == "__main__":
    async def main():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            initialization_options = InitializationOptions(
                server_name="snappr-api",
                server_version="1.0.0",
                capabilities=ServerCapabilities()
            )
            await app.run(read_stream, write_stream, initialization_options)

    asyncio.run(main())