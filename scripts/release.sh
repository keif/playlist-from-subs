#!/bin/bash
# Release automation script for yt-sub-playlist
# Generates changelog and creates version tags using conventional commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    echo "Please install Node.js and npm first:"
    echo "  - macOS: brew install node"
    echo "  - Linux: apt-get install nodejs npm"
    exit 1
fi

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

# Display menu
echo -e "${GREEN}=== yt-sub-playlist Release Tool ===${NC}"
echo ""
echo "What would you like to do?"
echo ""
echo "  1) Generate changelog only (no version bump)"
echo "  2) Patch release (4.0.0 -> 4.0.1)"
echo "  3) Minor release (4.0.0 -> 4.1.0)"
echo "  4) Major release (4.0.0 -> 5.0.0)"
echo "  5) Dry-run (see what would change)"
echo "  6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo -e "${GREEN}Generating changelog...${NC}"
        npm run changelog
        echo -e "${GREEN}✓ Changelog updated${NC}"
        ;;
    2)
        echo -e "${GREEN}Creating patch release...${NC}"
        npm run release:patch
        echo -e "${GREEN}✓ Patch release created${NC}"
        echo -e "${YELLOW}Don't forget to: git push --follow-tags origin main${NC}"
        ;;
    3)
        echo -e "${GREEN}Creating minor release...${NC}"
        npm run release:minor
        echo -e "${GREEN}✓ Minor release created${NC}"
        echo -e "${YELLOW}Don't forget to: git push --follow-tags origin main${NC}"
        ;;
    4)
        echo -e "${GREEN}Creating major release...${NC}"
        npm run release:major
        echo -e "${GREEN}✓ Major release created${NC}"
        echo -e "${YELLOW}Don't forget to: git push --follow-tags origin main${NC}"
        ;;
    5)
        echo -e "${GREEN}Running dry-run...${NC}"
        npm run release:dry-run
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
