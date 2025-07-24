#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Printandscan - Fake the print and scan process. Inspired by falsisign
"""

import argparse
import pathlib
import random
import re
import shutil
import subprocess
import sys
import tempfile
import random
import datetime

def check_dependencies():
    """
    Checks if required command-line tools (gs, pdftk, magick) are installed
    and available in the system's PATH. Exits if any are missing.
    """
    dependencies = ['gs', 'pdftk', 'magick']
    missing = [dep for dep in dependencies if shutil.which(dep) is None]
    if missing:
        print(
            f"Error: Missing required dependencies: {', '.join(missing)}.",
            file=sys.stderr
        )
        print(
            "Please install them and ensure they are in your system's PATH.",
            file=sys.stderr
        )
        sys.exit(1)

def get_pdf_page_count(pdf_path: pathlib.Path) -> int:
    """
    Gets the total number of pages in a PDF file using pdftk.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        The number of pages as an integer.
    """
    try:
        result = subprocess.run(
            ['pdftk', str(pdf_path), 'dump_data'],
            capture_output=True,
            text=True,
            check=True
        )
        match = re.search(r'NumberOfPages:\s*(\d+)', result.stdout)
        if match:
            return int(match.group(1))
        raise RuntimeError("Could not determine number of pages from pdftk output.")
    except (subprocess.CalledProcessError, FileNotFoundError, RuntimeError) as e:
        print(f"Error getting page count: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to parse arguments and orchestrate the scanning process."""
    parser = argparse.ArgumentParser(
        description="Printandscan: Apply a scanned look to a PDF.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-d', '--document',
        required=True,
        type=pathlib.Path,
        help="The PDF document you want to process"
    )
    parser.add_argument(
        '-o', '--output-fname',
        required=True,
        type=pathlib.Path,
        help="The output file name"
    )
    parser.add_argument(
        '--density',
        type=int,
        default=300,
        help="The DPI for rasterizing the PDF (default: 300)"
    )

    args = parser.parse_args()

    check_dependencies()

    doc_basename = args.document.stem

    with tempfile.TemporaryDirectory(prefix="printandscan-") as tmpdir:
        tmp_path = pathlib.Path(tmpdir)

        # 1. Preprocess the PDF to make sure we get an RGB pdf
        print("Preprocessing PDF to RGB color space...")
        rgb_pdf = tmp_path / f"{doc_basename}_RGB.pdf"
        subprocess.run([
            'gs', '-sDEVICE=pdfwrite', '-dBATCH', '-dNOPAUSE', '-dCompatibilityLevel=1.4',
            '-dColorConversionStrategy=/sRGB', '-dProcessColorModel=/DeviceRGB',
            '-dUseCIEColor=true', f'-sOutputFile={rgb_pdf}', str(args.document)
        ], check=True, capture_output=True)

        # 2. Extract each page of the PDF
        print("Extracting pages...")
        subprocess.run(
            ['pdftk', str(rgb_pdf), 'burst', 'output', str(tmp_path / f'{doc_basename}-%04d.pdf')],
            check=True, capture_output=True
        )

        num_pages = get_pdf_page_count(rgb_pdf)
        scanned_pdfs = []

        print("Applying 'scanned' effect to pages...")
        for i in range(1, num_pages + 1):
            page_pdf = tmp_path / f"{doc_basename}-{i:04d}.pdf"
            page_png = tmp_path / f"{doc_basename}-{i:04d}.png"
            scanned_pdf = tmp_path / f"{doc_basename}-{i:04d}-scanned.pdf"

            # Convert page to PNG
            subprocess.run([
                'magick', '-density', str(args.density), str(page_pdf),
                '-resize', '2480x3508!', str(page_png)
            ], check=True, capture_output=True)

            rotation = random.uniform(-.5, .5)

            # Apply "scanned" effect
            # Command breakdown:
            # -background white:      Sets the background to white for rotation.
            # -rotate {rotation}:     Rotates the image slightly.
            # +repage:                Resets the page geometry after rotation.
            # -blur 0x.7:              Applies a slight blur.
            # -attenuate 0.25:        Reduces single pixel noise.
            # +noise Gaussian:        Adds gaussian noise.
            # -brightness-contrast -10x-40: Adjusts brightness and contrast for a scanned look.
            # -modulate 100,60,100:   Desaturates the image.
            cmd = [
                'magick', str(page_png),
                '-background', 'white', '-rotate', f'{rotation:.4f}', '+repage',
                '-blur', '0x.6', '-attenuate', '0.4', '+noise', 'Gaussian',
                '-brightness-contrast', '-10x-20', '-modulate', '100,80,100',
                str(scanned_pdf)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            scanned_pdfs.append(scanned_pdf)
            print(f"done {i}/{num_pages}")

        print("Assembling final PDF...")
        large_pdf = tmp_path / f"{doc_basename}_large.pdf"
        subprocess.run(
            ['magick', '-density', str(args.density)] + [str(p) for p in scanned_pdfs] + [str(large_pdf)],
            check=True, capture_output=True
        )

        print(f"Compressing final PDF to {args.output_fname}...")
        subprocess.run([
            'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            '-dPDFSETTINGS=/default', '-dNOPAUSE', '-dQUIET', '-dBATCH',
            '-dDetectDuplicateImages', '-dCompressFonts=true', f'-r{args.density}',
            f'-sOutputFile={args.output_fname}', str(large_pdf)
        ], check=True, capture_output=False)

    print("Done.")


if __name__ == "__main__":
    main()
