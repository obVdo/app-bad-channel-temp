"""
app-set-bad-channels: Mark bad channels in epochs or raw from a BIDS channels.tsv.

Authors : Guiomar Niso (guiomar.niso@gmail.com)
          Antonio Caulín (antoniocaulinatienzar@gmail.com) https://github.com/AntonioCauAt
          Maximilien Chaumon https://github.com/dnacombo
          obVdo https://github.com/obVdo

Inputs : epochs or raw FIF, channels.tsv (neuro/meg/fif-override, status column)
Outputs: epochs or raw FIF with info['bads'] set
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
epo_file     = config.get('epo') or config.get('epochs') or ''
raw_file     = config.get('raw') or config.get('mne') or ''
channels_tsv = config.get('channels') or ''

if not channels_tsv or not os.path.isfile(channels_tsv):
    _fail(f"FATAL: channels.tsv not found: '{channels_tsv}'.")

import mne

# Determine input type
if epo_file and os.path.isfile(epo_file):
    data = mne.read_epochs(epo_file, preload=True, verbose=True)
    data_type = 'epochs'
    out_filename = 'meg-epo.fif'
    add_info_to_product(report_items, f"Loaded {len(data)} epochs, {len(data.ch_names)} channels", 'info')
elif raw_file and os.path.isfile(raw_file):
    data = mne.io.read_raw_fif(raw_file, preload=True, verbose=True)
    data_type = 'raw'
    out_filename = 'meg.fif'
    add_info_to_product(report_items, f"Loaded raw: {len(data.ch_names)} channels, {data.times[-1]:.1f}s", 'info')
else:
    _fail(f"FATAL: No valid epochs or raw file found. epo='{epo_file}', raw='{raw_file}'.")

# == READ BAD CHANNELS FROM TSV ==
bad_channels = []
with open(channels_tsv, newline='') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if row.get('status', '').strip().lower() == 'bad':
            name = row.get('name', '').strip()
            if name and name in data.ch_names:
                bad_channels.append(name)

if bad_channels:
    data.info['bads'] = bad_channels
    add_info_to_product(report_items, f"Marked {len(bad_channels)} bad channels: {', '.join(bad_channels)}", 'info')
else:
    add_info_to_product(report_items, "No bad channels found in channels.tsv", 'info')

# == SAVE ==
out_path = os.path.join('out_dir', out_filename)
if data_type == 'epochs':
    data.save(out_path, overwrite=True)
else:
    data.save(out_path, overwrite=True)
add_info_to_product(report_items, f"Saved {data_type}: {out_path}", 'info')

create_product_json(report_items)
print("Done.")
