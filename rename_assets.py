import os
import shutil

# Source and Destination
SOURCE_DIR = "frontend/public/screenshots"
DEST_DIR = "frontend/public/assets"

# Mapping based on file size (bytes)
# Sizes taken from previous ls output
SIZE_MAP = {
    # Desktop
    585380: "desktop-chat-light.png",
    565568: "desktop-chat-dark.png",
    546095: "desktop-profile-light.png",
    474679: "desktop-profile-dark.png",
    419887: "desktop-settings-light.png",
    407265: "desktop-settings-dark.png",
    
    # Mobile
    220239: "mobile-chat-light.png",
    210966: "mobile-chat-dark.png",
    195836: "mobile-profile-light.png",
    186995: "mobile-profile-dark.png",
    185426: "mobile-settings-light.png",
    170410: "mobile-settings-dark.png"
}

def rename_assets():
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)

    files = os.listdir(SOURCE_DIR)
    
    for filename in files:
        if not filename.endswith(".png"):
            continue
            
        filepath = os.path.join(SOURCE_DIR, filename)
        size = os.path.getsize(filepath)
        
        if size in SIZE_MAP:
            new_name = SIZE_MAP[size]
            dest_path = os.path.join(DEST_DIR, new_name)
            print(f"Moving {filename} ({size}b) -> {new_name}")
            shutil.copy2(filepath, dest_path) # Copy to be safe
        else:
            print(f"Skipping {filename} ({size}b) - No match")

if __name__ == "__main__":
    rename_assets()
