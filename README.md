# TapTapLootDecryptSaves
Python script to decrypt save files for Tap Tap Loot game.

- Uses the game's AES decryption key to decrypt all save files in default save directory (`%USERPROFILE%\AppData\LocalLow\Turtle Knight Games\TapTapLoot`) to a human-readable json file
- The game already supports loading unencrypted saves so there is no need to re-encrypt afterwards
- Automatically backs up your save files to the script's directory before attempting decryption

## Usage
```bash
pip install cryptography
python .\TapTapLootDecryptSaves.py
```
