# Arcana Restore: Quick Start

Repair glare and shadow damage in photographed documents, then seal the result in an encrypted vault with a tamper-evident custody record. Everything stays on your computer. Nothing is uploaded.

## 1. Install (about a minute)

| System | Do this |
|---|---|
| **Windows** | Double-click `ArcanaRestore-Setup-<version>.exe`. If Windows SmartScreen warns, click **More info**, then **Run anyway**. Tick "Create a desktop shortcut" if you want one. |
| **Mac** | Open `ArcanaRestore-<version>-macos.dmg` and drag **Arcana Restore** to **Applications**. If macOS blocks it, right-click the app, choose **Open**, then confirm. |
| **Linux** | Extract `ArcanaRestore-<version>-linux.tar.gz`, open a terminal in that folder and run `./install.sh --desktop`. |

Check the download against `SHA256SUMS` from the same release page if you want to confirm it is unmodified.

## 2. Seal your evidence

1. Open **Arcana Restore** and stay on the **Seal evidence** tab.
2. **Add images**: drag them into the list, or click **Add files** or **Add folder**. PNG, JPEG, TIFF and BMP are supported.
3. Choose a **vault folder**. Sealed files and the custody ledger are saved there.
4. Type a **passphrase** of at least 12 characters, twice.
5. Leave **Repair glare and shadow** ticked unless you only want to seal untouched originals.
6. Tick the acknowledgement and click **Seal evidence**.

**Write the passphrase down somewhere safe.** It cannot be recovered by anyone, including us. A lost passphrase means the evidence cannot be opened.

When it finishes, the log shows a **ledger head**, a long code. Copy it and keep it somewhere separate (an email to yourself, a case note). It lets you prove later that no record was removed.

## 3. Get your files back

1. Go to the **Open vault** tab.
2. Choose the `.arcr` file, enter the passphrase and pick a folder to save into.
3. Click **Open vault**. You receive four files:
   - `…original…`: your file, **byte for byte unchanged**. Use this as the evidence.
   - `…restored.png`: the repaired version, for easier reading.
   - `…mask.png`: white marks every area the repair may have filled in.
   - `…manifest.json`: file hashes, repair report and reading order.

## 4. Check the custody record

Go to the **Verify ledger** tab, choose the vault folder and click **Verify**. Paste the ledger head you saved into **Expected head** to also detect deleted final entries.

## Good to know

- **Repair is an estimate.** It makes text easier to see but cannot prove what hidden text said. For anything important, rely on the original and the mask.
- Damage covering more than 30% of an image is reported and **not** repaired.
- Existing vaults and exported files are never overwritten.
- A wrong passphrase and a modified file give the same message ("wrong passphrase, or the file was modified").

## Command line (optional)

```
arcana-restore process ./scans -o ./vault
arcana-restore extract ./vault/<file>.arcr -o ./out
arcana-restore verify-ledger --vault ./vault --expect-head <saved head>
```
The passphrase is requested at a prompt (or read from `--passphrase-file`); it is never typed on the command line.

## Support

sales@arcana-forensics.com. Use only on files you are authorized to examine.
