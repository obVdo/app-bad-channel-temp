"""
app-set-bad-channels: Mark bad channels in raw FIF from a BIDS channels.tsv.

Authors : Guiomar Niso (guiomar.niso@gmail.com)
          Antonio Caulín (antoniocaulinatienzar@gmail.com) https://github.com/AntonioCauAt
          Maximilien Chaumon https://github.com/dnacombo
          obVdo https://github.com/obVdo

Inputs : raw FIF, channels.tsv (neuro/meg/fif-override, status column)
Outputs: raw FIF with info['bads'] set
"""

import os
import sys
import csv

app_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(app_dir)
for search_path in [app_dir, parent_dir]:
    if os.path.isdir(os.path.join(search_path, 'brainlife_utils')):
        sys.path.insert(0, search_path)
        break

from brainlife_utils import (
    setup_matplotlib_backend,
    load_config,
    ensure_output_dirs,
    add_info_to_product,
    create_product_json,
)

setup_matplotlib_backend()
config = load_config()
ensure_output_dirs('out_dir')

report_items = []

def _fail(msg):
    add_info_to_product(report_items, msg, 'error')
    create_product_json(report_items)
    sys.exit(1)

# == INPUTS ==
raw_file     = config.get('mne') or config.get('raw') or ''
channels_tsv = config.get('channels') or ''

if not raw_file or not os.path.isfile(raw_file):
    _fail(f"FATAL: Raw file not found: '{raw_file}'.")

if not channels_tsv or not os.path.isfile(channels_tsv):
    _fail(f"FATAL: channels.tsv not found: '{channels_tsv}'.")

import mne

raw = mne.io.read_raw_fif(raw_file, preload=True, verbose=True)
add_info_to_product(report_items, f"Loaded raw: {len(raw.ch_names)} channels, {raw.times[-1]:.1f}s", 'info')

# == READ BAD CHANNELS FROM TSV ==
bad_channels = []
with open(channels_tsv, newline='') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if row.get('status', '').strip().lower() == 'bad':
            name = row.get('name', '').strip()
            if name and name in raw.ch_names:
                bad_channels.append(name)

if bad_channels:
    raw.info['bads'] = bad_channels
    add_info_to_product(report_items, f"Marked {len(bad_channels)} bad channels: {', '.join(bad_channels)}", 'info')
else:
    add_info_to_product(report_items, "No bad channels found in channels.tsv", 'info')

# == SAVE ==
out_path = os.path.join('out_dir', 'raw.fif')
raw.save(out_path, overwrite=True)
add_info_to_product(report_items, f"Saved: {out_path}", 'info')

create_product_json(report_items)
print("Done.")
