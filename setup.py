"""
UI Hierarchy Inspector

This script connects to the Android device and dumps the UI hierarchy
to hierarchy.xml for inspection.

Usage:
1. Make sure the Android emulator is running
2. Open the target app and navigate to the attendees list
3. Run: python setup.py
4. Open hierarchy.xml in a text editor
5. Find the resourceId values for:
   - List item container
   - List container (for scrolling)
   - Field labels on detail page
6. Update config.py with the discovered selectors
"""

import uiautomator2 as u2
import sys


def main():
    print("=" * 60)
    print("Android UI Hierarchy Inspector")
    print("=" * 60)
    
    try:
        # Connect to device
        print("\n1. Connecting to Android device...")
        device = u2.connect()
        print(f"   ✓ Connected: {device.info['productName']}")
        
        # Get current app
        print("\n2. Getting current app info...")
        current_app = device.app_current()
        package = current_app['package']
        print(f"   ✓ Current app package: {package}")
        
        # Dump hierarchy
        print("\n3. Dumping UI hierarchy...")
        xml = device.dump_hierarchy()
        
        with open("hierarchy.xml", "w", encoding="utf-8") as f:
            f.write(xml)
        
        print("   ✓ Saved to: hierarchy.xml")
        
        # Instructions
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print("1. Open hierarchy.xml in a text editor")
        print("2. Search for the list item elements")
        print("3. Look for 'resource-id' attributes")
        print("4. Find these selectors:")
        print("   - List item: The container for each attendee")
        print("   - List container: The scrollable list")
        print("   - Field labels: Name, Industry, Job Function, Company")
        print("5. Update config.py with the discovered values")
        print("6. Run: python main.py")
        print("=" * 60)
        print(f"\nApp Package: {package}")
        print("(Copy this to config.py -> APP_PACKAGE)")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
