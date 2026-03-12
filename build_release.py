"""
Script de build do APK release para divprom-mobile.

Uso:
    python build_release.py

O que faz:
  1. Atualiza os arquivos Python dentro do app.zip
  2. Executa flutter build apk --release
  3. Copia o APK gerado para build/apk/app-release.apk
"""

import os
import shutil
import subprocess
import sys
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLUTTER_DIR = os.path.join(BASE_DIR, "build", "flutter")
APP_ZIP = os.path.join(FLUTTER_DIR, "app", "app.zip")
SITE_PACKAGES = os.path.join(
    FLUTTER_DIR,
    "build", "build_python_3.12.9", "python", "Lib", "site-packages",
)
OUTPUT_APK = os.path.join(
    FLUTTER_DIR,
    "build", "app", "outputs", "flutter-apk", "app-release.apk",
)
DEST_DIR = os.path.join(BASE_DIR, "build", "apk")
DEST_APK = os.path.join(DEST_DIR, "app-release.apk")

# Arquivos Python do app (na raiz de divprom-mobile) que devem ir para o zip
APP_PYTHON_FILES = [
    "main.py",
    "api_client.py",
    "local_db.py",
    "login_screen.py",
    "senha_screen.py",
    "home_screen.py",
    "crr_form_screen.py",
    "crr_list_screen.py",
    "crr_search_screen.py",
    "print_utils.py",
    "android_print_service.py",
    "image_picker_service.py",
    "bluetooth_print_service.py",
    "bluetooth_escpos_service.py",
    "print_dialog.py",
    "qrcode.jpeg",
]

FLUTTER_EXE = shutil.which("flutter") or r"C:\Users\gabriel\flutter\3.38.6\bin\flutter.bat"


def step(msg):
    print(f"\n=== {msg} ===")


def update_app_zip():
    step("Atualizando app.zip com arquivos Python")
    if not os.path.exists(APP_ZIP):
        print(f"ERRO: app.zip nao encontrado em {APP_ZIP}")
        sys.exit(1)

    backup = APP_ZIP + ".bak"
    shutil.copy2(APP_ZIP, backup)

    with zipfile.ZipFile(APP_ZIP, "r") as zin:
        entries = {name: zin.read(name) for name in zin.namelist()}

    updated = []
    for fname in APP_PYTHON_FILES:
        fpath = os.path.join(BASE_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                entries[fname] = f.read()
            updated.append(fname)
        else:
            print(f"  AVISO: {fname} nao encontrado, ignorando")

    with zipfile.ZipFile(APP_ZIP, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)

    for f in updated:
        print(f"  Atualizado: {f}")
    print(f"app.zip atualizado com {len(updated)} arquivo(s)")


def build_apk():
    step("Executando flutter build apk --release")
    env = os.environ.copy()
    env["SERIOUS_PYTHON_SITE_PACKAGES"] = SITE_PACKAGES

    result = subprocess.run(
        [FLUTTER_EXE, "build", "apk", "--release"],
        cwd=FLUTTER_DIR,
        env=env,
    )

    if result.returncode != 0:
        print("ERRO: flutter build falhou")
        sys.exit(result.returncode)

    print("Build concluido com sucesso")


def copy_apk():
    step("Copiando APK para build/apk/")
    if not os.path.exists(OUTPUT_APK):
        print(f"ERRO: APK nao encontrado em {OUTPUT_APK}")
        sys.exit(1)

    os.makedirs(DEST_DIR, exist_ok=True)
    shutil.copy2(OUTPUT_APK, DEST_APK)
    size_mb = os.path.getsize(DEST_APK) / (1024 * 1024)
    print(f"APK copiado para: {DEST_APK} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    update_app_zip()
    build_apk()
    copy_apk()
    print("\n=== Build finalizado! APK em build/apk/app-release.apk ===")
