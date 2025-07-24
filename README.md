# printandscan

A Python script to make a PDF look like it has been printed and scanned.

This tool applies a series of transformations to a clean PDF file to simulate the artifacts and imperfections introduced during a print-and-scan cycle.

## Inspiration

This project is inspired by and based on the concepts from [falsisign](https://github.com/erstazi/falsisign). `printandscan` provides a similar outcome using a Python script and a common set of command-line utilities.

## Features

-   Slightly rotates pages for a natural, hand-placed look.
-   Adds blur and Gaussian noise to simulate scanner sensor effects.
-   Adjusts brightness, contrast, and saturation to mimic a scanned document's appearance.
-   Processes each page individually before reassembling the final PDF.

## Requirements

Before running the script, you need to have the following command-line tools installed and accessible in your system's PATH:

-   **Ghostscript** (`gs`)
-   **pdftk** (`pdftk`)
-   **ImageMagick** (`magick`)

You can typically install these using your system's package manager (e.g., `apt`, `brew`, `yum`).

## Usage

You can run the script directly from the command line.

### Command-Line Arguments

-   `--document` / `-d`: **Required**. The path to the input PDF file you want to process.
-   `--output-fname` / `-o`: **Required**. The desired file name for the output "scanned" PDF.
-   `--density`: Optional. The DPI resolution for rasterizing the PDF. The default is `300`.

### Example

To process a document named `my_contract.pdf` and save the output as `my_contract_scanned.pdf`:

```bash
./printandscan/printandscan.py --document my_contract.pdf --output-fname my_contract_scanned.pdf
```

If the script is not executable, you can run it with `python3`:

```bash
python3 ./printandscan/printandscan.py --document my_contract.pdf --output-fname my_contract_scanned.pdf
```
