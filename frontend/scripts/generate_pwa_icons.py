import os
from PIL import Image

def generate_icons():
    # Source image
    source_path = '/Users/mac/Desktop/phhh/frontend/public/Benchside.png'
    public_dir = '/Users/mac/Desktop/phhh/frontend/public'
    icons_dir = os.path.join(public_dir, 'icons')
    
    if not os.path.exists(source_path):
        print(f"Error: Source image not found at {source_path}")
        return

    try:
        img = Image.open(source_path)
        print(f"Opened source image: {source_path} ({img.size})")

        # 1. Generate Manifest Icons
        sizes = [72, 96, 128, 144, 152, 192, 384, 512]
        
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir)
            
        for size in sizes:
            # Resize with LANCZOS for high quality
            icon = img.resize((size, size), Image.Resampling.LANCZOS)
            output_path = os.path.join(icons_dir, f'icon-{size}x{size}.png')
            icon.save(output_path, 'PNG')
            print(f"Generated {output_path}")

        # 2. Generate Apple Icon (180x180 is standard, but layout.tsx might just need a file)
        # layout.tsx refers to /apple-icon.png.
        apple_icon = img.resize((180, 180), Image.Resampling.LANCZOS)
        apple_path = os.path.join(public_dir, 'apple-icon.png')
        apple_icon.save(apple_path, 'PNG')
        print(f"Generated {apple_path}")
        
        # 3. Generate proper Favicon.ico
        # PIL can save as ICO with multiple sizes
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        favicon_path = os.path.join(public_dir, 'favicon.ico')
        img.save(favicon_path, format='ICO', sizes=icon_sizes)
        print(f"Generated {favicon_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generate_icons()
