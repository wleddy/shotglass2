# Web Icon Generator

## About This Project

This Python script generates apple-touch-icon files for use in the shotglass framework

## Credit and Inspiration

Inspired by [macos-icon-generator](https://github.com/qwertzalcoatl/macos-icon-generator) created by Aljoscha Brell. I wanted a very simple version of what he created.

## Usage

### Prerequisites

Ensure you have Python installed on your system along with the required libraries:

```bash
pip install Pillow
```
### Basic Usage

Run the script from the command line with your input image:

```bash
python web-icon-generator.py path/to/your/input/image.png
```

This will generate icons sizes 57X57, 72X72, 114X114, 120X120 and save them in the current directory.

### Specifying Output Directory

To save the generated icons in a specific directory:

```bash
python web-icon-generator.py path/to/your/input/image.png -o path/to/output/directory
```

### Parameters

- `path/to/your/input/image.png`: Path to your high-resolution input image (required)
- `-o` or `--output`: Path to the directory where you want to save the generated icons (optional, defaults to current directory)

### Output

The script will generate the following icon sizes:
- 57X57
- 72X72
- 114X114
- 120X120

Each icon will be saved as a separate PNG file named `apple-touch-icon-SIZE.png` (e.g., `apple-touch-icon-114.png`).
