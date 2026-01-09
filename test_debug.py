"""
Debug script to test Kindle automation startup
"""
import sys
import traceback

def test_kindle_detection():
    """Test if Kindle can be detected"""
    print("=" * 60)
    print("KINDLE AUTOMATION DEBUG TEST")
    print("=" * 60)

    try:
        print("\n[1/6] Testing imports...")
        from src.automation.kindle_controller import KindleController
        print("    [OK] KindleController imported successfully")

        print("\n[2/6] Initializing KindleController...")
        kc = KindleController(
            status_callback=lambda msg: print(f"    STATUS: {msg}"),
            error_callback=lambda msg: print(f"    ERROR: {msg}")
        )
        print("    [OK] KindleController initialized")

        print("\n[3/6] Checking if Kindle is already running...")
        is_running = kc.is_kindle_running()
        print(f"    Result: Kindle is {'RUNNING' if is_running else 'NOT RUNNING'}")

        print("\n[4/6] Finding Kindle.exe installation...")
        kindle_path = kc.find_kindle_exe()
        if kindle_path:
            print(f"    [OK] Found Kindle at: {kindle_path}")
        else:
            print("    [X] Kindle.exe NOT FOUND in standard locations")
            print("    Checked locations:")
            import os
            paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Amazon', 'Kindle', 'Kindle.exe'),
                os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Amazon', 'Kindle', 'Kindle.exe'),
                os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Amazon', 'Kindle', 'Kindle.exe')
            ]
            for path in paths:
                exists = os.path.exists(path)
                print(f"      {'[OK]' if exists else '[X]'} {path}")

        print("\n[5/6] Attempting to detect Kindle window...")
        import pygetwindow as gw
        all_windows = gw.getWindowsWithTitle('Kindle')
        print(f"    Raw search found {len(all_windows)} window(s) with 'Kindle' in title")

        # Apply the same filtering as the controller
        kindle_windows = []
        for win in all_windows:
            title_lower = win.title.lower()
            if ('kindle' in title_lower and
                'kindletopdf' not in title_lower and
                'kindle-to-pdf' not in title_lower and
                not win.title.startswith('C:\\')):
                kindle_windows.append(win)

        if kindle_windows:
            print(f"    [OK] After filtering: Found {len(kindle_windows)} actual Kindle window(s)")
            for i, win in enumerate(kindle_windows):
                try:
                    print(f"      Window {i+1}: '{win.title}'")
                except UnicodeEncodeError:
                    print(f"      Window {i+1}: [Title contains special characters]")
                print(f"        Position: ({win.left}, {win.top})")
                print(f"        Size: {win.width}x{win.height}")
                print(f"        Minimized: {win.isMinimized}")
        else:
            print("    [X] No actual Kindle windows found after filtering")

        print("\n[6/6] Testing start_kindle_app()...")
        success, error = kc.start_kindle_app()
        if success:
            print("    [OK] start_kindle_app() returned SUCCESS")
        else:
            print(f"    [X] start_kindle_app() returned FAILURE")
            if error:
                print(f"      Error: {error}")

        print("\n" + "=" * 60)
        print("DEBUG TEST COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\n[X] EXCEPTION OCCURRED:")
        print(f"  {type(e).__name__}: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_kindle_detection()
    sys.exit(0 if success else 1)
