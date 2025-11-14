"""Main entry point for running the MCP server or CLI."""

import sys

# Check if CLI mode is requested (any CLI arguments)
if len(sys.argv) > 1:
    # Run CLI
    from lorekeeper_mcp.cli import main

    main()
else:
    # Run MCP server (default)
    from lorekeeper_mcp.server import mcp

    mcp.run()
