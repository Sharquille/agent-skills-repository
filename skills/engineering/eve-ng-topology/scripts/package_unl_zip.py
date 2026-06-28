#!/usr/bin/env python3
"""package_unl_zip.py — package an EVE-NG .unl as an import-ready zip.

EVE-NG import expects the .unl at the archive root. This helper avoids accidental
directory nesting when packaging generated labs.

Usage:
  scripts/package_unl_zip.py topology/lab.unl -o topology/lab-import.zip
"""

import argparse
import os
import zipfile


def package(unl_path: str, output_path: str):
    arcname = os.path.basename(unl_path)
    if not arcname.endswith(".unl"):
        raise SystemExit(f"expected a .unl file, got: {unl_path}")
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(unl_path, arcname=arcname)


def main():
    ap = argparse.ArgumentParser(description="Package a root-level .unl EVE-NG import zip")
    ap.add_argument("unl", help="input .unl file")
    ap.add_argument("-o", "--output", required=True, help="output import zip")
    args = ap.parse_args()
    package(args.unl, args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
