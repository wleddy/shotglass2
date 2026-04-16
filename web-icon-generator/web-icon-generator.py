from PIL import Image
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Generate macOS app icons from an input image.")
    parser.add_argument("input_image", help="Path to the input image file")
    parser.add_argument("-o", "--output", default=".", help="Output directory for generated icons (default: current directory)")
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)

    original_image = Image.open(args.input_image)
    # Original sizes = [16, 32, 57, 64, 72, 114, 120, 128, 256, 512, 1024]
    sizes = [57, 72, 114, 120]
    for size in sizes:
        icon = original_image.copy()
        icon.thumbnail((size,size))
        icon.save(os.path.join(args.output, f"apple-touch-icon-{size}.png"))
    print(f"Icon generation complete! Icons saved in {args.output}")

if __name__ == "__main__":
    main()