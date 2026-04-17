import os
import sys
import shutil
import subprocess
import base64
from datetime import datetime
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAVE_PATH    = Path(os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\Turtle Knight Games\TapTapLoot"))
PROCESS_NAME = "TapTapLoot.exe"
AES_KEY      = b"YoureOnlyRuiningTheFun4Yourself9"
AES_IV       = b"1501202613042026"
SCRIPT_DIR   = Path(__file__).parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_encrypted(content: str) -> bool:
    trimmed = content.strip()
    return not (trimmed.startswith("{") or trimmed.startswith("["))


def decrypt(cipher_text: str) -> str:
    raw = base64.b64decode(cipher_text.strip())
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV))
    decryptor = cipher.decryptor()
    padded_plain = decryptor.update(raw) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    plain = unpadder.update(padded_plain) + unpadder.finalize()
    return plain.decode("utf-8")

def press_any_key(prompt: str = "Press any key to exit...") -> None:
    print(f"\n{prompt}")
    try:
        import msvcrt
        msvcrt.getch()
    except ImportError:
        input()

# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def check_game_not_running() -> None:
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {PROCESS_NAME}"],
        capture_output=True,
        text=True,
    )
    if PROCESS_NAME.lower() in result.stdout.lower():
        print(f"\t{PROCESS_NAME} is currently running.")
        print("\tPlease close the game before decrypting your saves.")
        press_any_key()
        sys.exit(0)


def scan_save_files() -> dict[Path, tuple[str, bool]]:
    if not SAVE_PATH.exists():
        print("ERROR: Save folder not found:")
        print(f"\t{SAVE_PATH}")
        press_any_key()
        sys.exit(1)

    json_files = sorted(SAVE_PATH.glob("*.json"))
    if not json_files:
        print("No JSON save files found in:")
        print(f"\t{SAVE_PATH}")
        press_any_key()
        sys.exit(0)

    print(f"Save folder:  {SAVE_PATH}")
    print()

    file_states: dict[Path, tuple[str, bool]] = {}
    for path in json_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        encrypted = is_encrypted(content)
        file_states[path] = (content, encrypted)
        label = "Encrypted" if encrypted else "Already decrypted"
        print(f"\t{path.name:<30}  {label}")

    return file_states


def backup_files(file_states: dict[Path, tuple[str, bool]], backup_dir: Path) -> None:
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        for path in file_states:
            shutil.copy2(path, backup_dir / path.name)
        print("Backup created:")
        print(f"\t{backup_dir}")
    except Exception as exc:
        print(f"ERROR: Backup failed — {exc}")
        print("No files were modified.")
        press_any_key()
        sys.exit(1)


def decrypt_files(file_states: dict[Path, tuple[str, bool]]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for path, (content, encrypted) in file_states.items():
        if not encrypted:
            print(f"\t{path.name:<30}  Skipped (already decrypted)")
            continue
        try:
            plain_text = decrypt(content)
            path.write_text(plain_text, encoding="utf-8")
            print(f"\t{path.name:<30}  Decrypted")
        except Exception as exc:
            errors.append((path.name, str(exc)))
            print(f"\t{path.name:<30}  FAILED: {exc}")
    return errors

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 52)
    print("\tTapTapLoot Save File Decryptor")
    print("=" * 52)
    print()

    check_game_not_running()

    file_states = scan_save_files()
    print()

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = SCRIPT_DIR / "backup" / timestamp

    print("Current files will be backed up to:")
    print(f"\t{backup_dir}")
    print()

    answer = input("Do you want to decrypt all of your save files? [Y/n]: ").strip().lower()
    if answer not in ("", "y", "yes"):
        print("\nCancelled. No files were modified.")
        press_any_key()
        sys.exit(0)

    print()
    backup_files(file_states, backup_dir)
    print()

    errors = decrypt_files(file_states)
    print()

    if errors:
        print(f"Completed with {len(errors)} error(s). See messages above.")
    else:
        print("All save files decrypted successfully!")

    print("\nOpening save folder...")
    os.startfile(SAVE_PATH)

    press_any_key()


if __name__ == "__main__":
    main()
