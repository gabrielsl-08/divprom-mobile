"""Script para executar flet build apk com suporte a image_picker (camera)."""
import sys
import os
import io
import subprocess
import shutil
import zipfile
import tempfile

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Forca stdout/stderr para UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ["NO_COLOR"] = "1"
os.environ["TERM"] = "dumb"
os.environ["PYTHONIOENCODING"] = "utf-8"

import rich.console
rich.console.WINDOWS = False

flutter_path = r"C:\Users\gabriel\flutter\3.38.6\bin"
os.environ["PATH"] = flutter_path + ";" + os.environ.get("PATH", "")

flutter_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "flutter")
app_zip_path = os.path.join(flutter_dir, "app", "app.zip")
app_zip_hash_path = os.path.join(flutter_dir, "app", "app.zip.hash")

# Remover arquivos Dart de extensoes extras do flutter/lib antes da FASE 1
# (podem estar desatualizados de um build anterior e causar erro de compilacao)
_lib_dir = os.path.join(flutter_dir, "lib")
for _dart_extra in [
    "image_picker_service.dart",
    "bluetooth_printer_service.dart",
    "android_print_service.dart",
]:
    _dart_path = os.path.join(_lib_dir, _dart_extra)
    if os.path.exists(_dart_path):
        os.remove(_dart_path)

# Remover imports das extensoes do main.dart antes da FASE 1
# (evita erro de compilacao por arquivos .dart ausentes durante o build inicial)
_main_dart_path = os.path.join(_lib_dir, "main.dart")
if os.path.exists(_main_dart_path):
    with open(_main_dart_path, "r", encoding="utf-8") as _f:
        _main_content = _f.read()
    _lines_to_remove = [
        'import "image_picker_service.dart";',
        'import "bluetooth_printer_service.dart";',
        'import "android_print_service.dart";',
        '  ImagePickerFletExtension(),',
        '  BluetoothPrinterFletExtension(),',
        '  AndroidPrintFletExtension(),',
    ]
    _cleaned = "\n".join(
        line for line in _main_content.splitlines()
        if line.strip() not in [ln.strip() for ln in _lines_to_remove]
    )
    if _cleaned != _main_content:
        with open(_main_dart_path, "w", encoding="utf-8") as _f:
            _f.write(_cleaned)

# ============================================================
# FASE 1: Rodar flet build apk normalmente
# ============================================================
print("=== FASE 1: Executando flet build apk ===")
sys.argv = ["flet", "build", "apk", "--verbose"]
from flet_cli.cli import main
try:
    main()
except SystemExit:
    pass  # flet cli chama sys.exit() apos sucesso

if not os.path.exists(app_zip_path):
    print("ERRO: app.zip nao encontrado apos FASE 1")
    sys.exit(1)

# ============================================================
# FASE 1.5: Corrigir app.zip - mover pacotes para raiz
# ============================================================
print("\n=== FASE 1.5: Corrigindo app.zip (site-packages para raiz) ===")

tmp_dir = tempfile.mkdtemp(prefix="appzip_fix_")
try:
    # Extrair app.zip
    with zipfile.ZipFile(app_zip_path, 'r') as zf:
        zf.extractall(tmp_dir)

    # Verificar se existe venv/Lib/site-packages
    venv_sp = os.path.join(tmp_dir, "venv", "Lib", "site-packages")
    if os.path.isdir(venv_sp):
        # Copiar conteudo de site-packages para a raiz do app
        count = 0
        for item in os.listdir(venv_sp):
            src = os.path.join(venv_sp, item)
            dst = os.path.join(tmp_dir, item)
            # Pular arquivos/dirs que ja existem na raiz (como .DS_Store)
            if os.path.exists(dst):
                continue
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            count += 1
        print(f"  -> {count} pacotes copiados de venv/Lib/site-packages/ para raiz")

        # Remover o diretorio venv inteiro (nao precisa mais)
        shutil.rmtree(os.path.join(tmp_dir, "venv"))
        print("  -> diretorio venv/ removido do app.zip")
    else:
        print("  -> venv/Lib/site-packages nao encontrado, verificando se pacotes ja estao na raiz")
        # Verificar se certifi ja esta na raiz
        if os.path.isdir(os.path.join(tmp_dir, "certifi")):
            print("  -> certifi ja esta na raiz, OK")
        else:
            print("  -> AVISO: certifi nao encontrado em nenhum local!")

    # Recriar app.zip
    new_zip_path = app_zip_path + ".new"
    with zipfile.ZipFile(new_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(tmp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, tmp_dir)
                zf.write(file_path, arcname)

    # Substituir app.zip original
    os.replace(new_zip_path, app_zip_path)

    # Verificar resultado
    with zipfile.ZipFile(app_zip_path, 'r') as zf:
        has_certifi = any('certifi/__init__.py' == f or f == 'certifi/__init__.py' for f in zf.namelist())
        has_httpx = any('httpx/__init__.py' == f or f == 'httpx/__init__.py' for f in zf.namelist())
        total = len(zf.namelist())
    print(f"  -> app.zip recriado: {total} arquivos, certifi={has_certifi}, httpx={has_httpx}")

    # Atualizar hash (se existir)
    if os.path.exists(app_zip_hash_path):
        import hashlib
        with open(app_zip_path, 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest()
        with open(app_zip_hash_path, 'w') as f:
            f.write(h)
        print(f"  -> app.zip.hash atualizado")

finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

# Salvar copia do app.zip corrigido (para restaurar apos FASE 2 se necessario)
app_zip_backup = app_zip_path + ".backup"
shutil.copy2(app_zip_path, app_zip_backup)
if os.path.exists(app_zip_hash_path):
    shutil.copy2(app_zip_hash_path, app_zip_hash_path + ".backup")
print("  -> backup do app.zip salvo")

# ============================================================
# FASE 2: Injetar image_picker + android_print e rebuildar
# ============================================================
pubspec_path = os.path.join(flutter_dir, "pubspec.yaml")
main_dart_path = os.path.join(flutter_dir, "lib", "main.dart")
service_dart_path = os.path.join(flutter_dir, "lib", "image_picker_service.dart")
android_service_dart_path = os.path.join(flutter_dir, "lib", "android_print_service.dart")

with open(pubspec_path, "r", encoding="utf-8") as f:
    pubspec = f.read()

print("\n=== FASE 2: Injetando image_picker + android_print e corrigindo manifest ===")

# 2.0 Corrigir AndroidManifest.xml - permitir HTTP cleartext e camera
manifest_path = os.path.join(
    flutter_dir, "android", "app", "src", "main", "AndroidManifest.xml"
)
if os.path.exists(manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = f.read()
    changed = False
    # Adicionar usesCleartextTraffic
    if "usesCleartextTraffic" not in manifest:
        manifest = manifest.replace(
            'android:icon="@mipmap/ic_launcher"',
            'android:usesCleartextTraffic="true"\n'
            '        android:icon="@mipmap/ic_launcher"'
        )
        changed = True
    # Adicionar permissoes de camera, storage e rede
    # (Bluetooth gerenciado pelo Datecs Print Service, sem necessidade aqui)
    perms = [
        "android.permission.CAMERA",
        "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.READ_MEDIA_IMAGES",
        "android.permission.ACCESS_NETWORK_STATE",
        "android.permission.BLUETOOTH",
        "android.permission.BLUETOOTH_ADMIN",
        "android.permission.BLUETOOTH_CONNECT",
        "android.permission.BLUETOOTH_SCAN",
    ]
    for perm in perms:
        if perm not in manifest:
            manifest = manifest.replace(
                "<!-- flet: end of permission   -->",
                f'    <uses-permission android:name="{perm}" />\n'
                '    <!-- flet: end of permission   -->'
            )
            changed = True
    if changed:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest)
        print("  -> AndroidManifest.xml corrigido (cleartext + permissoes)")
    else:
        print("  -> AndroidManifest.xml ja esta correto")

# 2a. Adicionar pacotes extras ao pubspec.yaml (se ainda nao estiverem)
pubspec_changed = False
if "image_picker" not in pubspec:
    pubspec = pubspec.replace(
        "  file_picker: ^10.3.10",
        "  file_picker: ^10.3.10\n  image_picker: ^1.1.2"
    )
    pubspec_changed = True
if "  pdf:" not in pubspec:
    anchor = "  image_picker: ^1.1.2" if "  image_picker:" in pubspec else "  file_picker: ^10.3.10"
    pubspec = pubspec.replace(anchor, anchor + "\n  pdf: ^3.11.0")
    pubspec_changed = True
if "  printing:" not in pubspec:
    pubspec = pubspec.replace(
        "  pdf: ^3.11.0",
        "  pdf: ^3.11.0\n  printing: ^5.13.1"
    )
    pubspec_changed = True
if "datecs_printer: ^0.0.5" not in pubspec:
    # Remove versao antiga blue_thermal_printer se presente
    import re as _re2
    pubspec = _re2.sub(r'\n\s*blue_thermal_printer: \S+', '', pubspec)
    if "datecs_printer" in pubspec:
        pubspec = _re2.sub(r'datecs_printer: \S+', 'datecs_printer: ^0.0.5', pubspec)
    else:
        pubspec = pubspec.replace(
            "  printing: ^5.13.1",
            "  printing: ^5.13.1\n  datecs_printer: ^0.0.5"
        )
    pubspec_changed = True
if pubspec_changed:
    with open(pubspec_path, "w", encoding="utf-8") as f:
        f.write(pubspec)
    print("  -> pubspec.yaml atualizado com novos pacotes (pdf, printing)")
else:
    print("  -> pubspec.yaml ja esta correto")

# 2b. Criar servico Dart para image_picker
service_code = r'''import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flet/flet.dart';
import 'package:image_picker/image_picker.dart';

class ImagePickerFletService extends FletService {
  ImagePickerFletService({required super.control});

  final ImagePicker _picker = ImagePicker();

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(_invokeMethod);
    debugPrint("ImagePickerFletService initialized for control: ${control.id}");
  }

  @override
  void dispose() {
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    switch (name) {
      case "pick_image_camera":
        return await _pickImage(ImageSource.camera, args);
      case "pick_image_gallery":
        return await _pickImage(ImageSource.gallery, args);
      default:
        throw Exception("Unknown ImagePicker method: $name");
    }
  }

  Future<dynamic> _pickImage(ImageSource source, dynamic args) async {
    final int quality = (args["image_quality"] as num?)?.toInt() ?? 85;
    final double? maxW = (args["max_width"] as num?)?.toDouble();
    final double? maxH = (args["max_height"] as num?)?.toDouble();

    final XFile? image = await _picker.pickImage(
      source: source,
      imageQuality: quality,
      maxWidth: maxW,
      maxHeight: maxH,
    );

    if (image != null) {
      final bytes = await image.readAsBytes();
      return {
        "name": image.name,
        "path": image.path,
        "base64": base64Encode(bytes),
      };
    }
    return null;
  }
}

class ImagePickerFletExtension extends FletExtension {
  @override
  void ensureInitialized() {}

  @override
  FletService? createService(Control control) {
    if (control.type == "flet_image_picker") {
      return ImagePickerFletService(control: control);
    }
    return null;
  }
}
'''

with open(service_dart_path, "w", encoding="utf-8") as f:
    f.write(service_code)
print("  -> image_picker_service.dart criado")

# 2b2. Criar servico Dart para Android Print Framework (via Datecs Print Service)
android_print_service_code = r'''import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flet/flet.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

class AndroidPrintFletService extends FletService {
  AndroidPrintFletService({required super.control});

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(_invokeMethod);
    debugPrint("AndroidPrintFletService initialized");
  }

  @override
  void dispose() {
    control.removeInvokeMethodListener(_invokeMethod);
    super.dispose();
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    switch (name) {
      case "print_receipt":
        return await _printReceipt(args);
      default:
        throw Exception("Unknown AndroidPrint method: $name");
    }
  }

  Future<dynamic> _printReceipt(dynamic args) async {
    final List<dynamic> lines = args["lines"] ?? [];
    final String sigBase64 = args["signature_base64"] ?? "";
    try {
      final Uint8List pdfBytes = await _generatePdf(lines, sigBase64);
      final bool submitted = await Printing.layoutPdf(
        onLayout: (PdfPageFormat format) async => pdfBytes,
        name: 'Cupom CRR',
      );
      return {"sucesso": submitted};
    } catch (e) {
      debugPrint("Erro ao gerar/imprimir PDF: $e");
      return {"sucesso": false, "erro": e.toString()};
    }
  }

  Future<Uint8List> _generatePdf(
      List<dynamic> lines, String sigBase64) async {
    final pdf = pw.Document();

    // Papel 57mm (DDP-250) com margens de 0.5mm
    final pageFormat = PdfPageFormat(
      57 * PdfPageFormat.mm,
      double.infinity,
      marginAll: 0.5 * PdfPageFormat.mm,
    );

    pw.MemoryImage? sigImage;
    if (sigBase64.isNotEmpty) {
      try {
        sigImage = pw.MemoryImage(base64Decode(sigBase64));
      } catch (e) {
        debugPrint("Erro ao decodificar assinatura: $e");
      }
    }

    pdf.addPage(
      pw.Page(
        pageFormat: pageFormat,
        build: (pw.Context context) {
          // Estilo padrao: 10pt negrito
          final textStyle = pw.TextStyle(
            font: pw.Font.courierBold(),
            fontSize: 10,
          );
          // Estilo para o numero do CRR: 12pt negrito (destaque)
          final numStyle = pw.TextStyle(
            font: pw.Font.courierBold(),
            fontSize: 12,
          );
          final children = <pw.Widget>[];
          for (final line in lines) {
            final String lineStr = line.toString();
            if (lineStr == "__AGENTE_SIG__") {
              if (sigImage != null) {
                children.add(pw.SizedBox(height: 2));
                children.add(pw.Text("Assinatura do Agente:", style: textStyle));
                children.add(pw.Container(
                  width: 25 * PdfPageFormat.mm,
                  height: 14 * PdfPageFormat.mm,
                  child: pw.Image(sigImage, fit: pw.BoxFit.contain),
                ));
              }
            } else if (lineStr == "__SPACER__") {
              children.add(pw.SizedBox(height: 8));
            } else {
              final bool isNumero = lineStr.startsWith("NUMERO:");
              children.add(pw.Text(lineStr,
                  style: isNumero ? numStyle : textStyle));
            }
          }
          return pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: children,
          );
        },
      ),
    );
    return pdf.save();
  }
}

class AndroidPrintFletExtension extends FletExtension {
  @override
  void ensureInitialized() {}

  @override
  FletService? createService(Control control) {
    if (control.type == "flet_android_print") {
      return AndroidPrintFletService(control: control);
    }
    return null;
  }
}
'''

with open(android_service_dart_path, "w", encoding="utf-8") as f:
    f.write(android_print_service_code)
print("  -> android_print_service.dart criado")

# 2b3. Criar servico Dart para Bluetooth ESC/POS direto
bluetooth_service_dart_path = os.path.join(flutter_dir, "lib", "bluetooth_printer_service.dart")
bluetooth_service_code = r'''import 'package:flutter/foundation.dart';
import 'package:flet/flet.dart';
import 'package:datecs_printer/datecs_printer.dart';

class BluetoothPrinterFletService extends FletService {
  BluetoothPrinterFletService({required super.control});

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(_invokeMethod);
    debugPrint("BluetoothPrinterFletService initialized");
  }

  @override
  void dispose() {
    control.removeInvokeMethodListener(_invokeMethod);
    DatecsPrinter.disconnect;
    super.dispose();
  }

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    switch (name) {
      case "print_receipt":
        return await _printReceipt(args);
      case "listar_pareados":
        return await _listarPareados();
      default:
        throw Exception("Unknown BluetoothPrinter method: $name");
    }
  }

  Future<dynamic> _listarPareados() async {
    try {
      List<dynamic> devices = await DatecsPrinter.getListBluetoothDevice;
      return devices.map((d) => {
        "nome": (d['name'] ?? d.name ?? "").toString(),
        "mac":  (d['address'] ?? d.address ?? "").toString(),
      }).toList();
    } catch (e) {
      debugPrint("Erro ao listar pareados: $e");
      return [];
    }
  }

  Future<dynamic> _printReceipt(dynamic args) async {
    final String mac = (args["mac_address"] ?? "").toString().toUpperCase();
    final List<dynamic> lines = args["lines"] ?? [];
    final String agentSig = (args["signature_base64"] ?? "").toString();
    final String qrBase64 = (args["qr_base64"] ?? "").toString();

    if (mac.isEmpty) {
      return {"sucesso": false, "erro": "MAC da impressora nao configurado"};
    }

    try {
      // Desconecta antes para garantir conexao com dispositivo correto
      try { await DatecsPrinter.disconnect; } catch (_) {}
      await Future.delayed(const Duration(milliseconds: 400));

      bool connected = false;
      try {
        connected = await DatecsPrinter.connectBluetooth(mac) ?? false;
      } catch (e) {
        final msg = e.toString().toLowerCase();
        if (msg.contains("connect") || msg.contains("ioexception") || msg.contains("read failed")) {
          return {"sucesso": false, "erro": "Impressora desligada ou fora de alcance"};
        }
        return {"sucesso": false, "erro": "Falha ao conectar com $mac"};
      }

      if (!connected) {
        return {"sucesso": false, "erro": "Nao foi possivel conectar a impressora"};
      }

      await Future.delayed(const Duration(milliseconds: 800));

      final DatecsGenerate gen = DatecsGenerate(DatecsPaper.mm58);
      for (final line in lines) {
        final String s = line.toString();
        if (s == "__AGENTE_SIG__") {
          if (agentSig.isNotEmpty) gen.image(agentSig);
          gen.feed(2);
        } else if (s == "__SPACER__") {
          gen.feed(3);
        } else if (s == "__QR_STATIC__") {
          if (qrBase64.isNotEmpty) gen.image(qrBase64);
        } else if (s.startsWith("__CENTRO__")) {
          final String txt = s.substring(10);
          gen.textPrint(txt, style: const DatecsStyle(align: DatecsAlign.center, bold: true));
        } else if (s.isNotEmpty && s.split('').every((c) => c == s[0]) && '-=_'.contains(s[0])) {
          gen.hr(char: s[0]);
        } else if (s.trim().isEmpty) {
          gen.feed(1);
        } else {
          gen.textPrint(s);
        }
      }
      gen.feed(5);

      final bool printed = await DatecsPrinter.printText(gen.args) ?? false;

      try { await DatecsPrinter.disconnect; } catch (_) {}

      if (printed) {
        return {"sucesso": true};
      } else {
        return {"sucesso": false, "erro": "Impressora nao confirmou a impressao"};
      }
    } catch (e) {
      debugPrint("Erro ao imprimir via BT: $e");
      return {"sucesso": false, "erro": "Erro na impressao: ${e.toString().split("\\n").first}"};
    }
  }
}

class BluetoothPrinterFletExtension extends FletExtension {
  @override
  void ensureInitialized() {}

  @override
  FletService? createService(Control control) {
    if (control.type == "flet_bluetooth_print") {
      return BluetoothPrinterFletService(control: control);
    }
    return null;
  }
}
'''
with open(bluetooth_service_dart_path, "w", encoding="utf-8") as f:
    f.write(bluetooth_service_code)
print("  -> bluetooth_printer_service.dart criado")

# 2c. Modificar main.dart para registrar as extensoes
with open(main_dart_path, "r", encoding="utf-8") as f:
    main_dart = f.read()

# Adicionar imports
if "image_picker_service.dart" not in main_dart:
    main_dart = main_dart.replace(
        "import \"python.dart\";",
        "import \"python.dart\";\nimport \"image_picker_service.dart\";"
    )
if "android_print_service.dart" not in main_dart:
    main_dart = main_dart.replace(
        "import \"image_picker_service.dart\";",
        "import \"image_picker_service.dart\";\nimport \"android_print_service.dart\";"
    )
if "bluetooth_printer_service.dart" not in main_dart:
    main_dart = main_dart.replace(
        "import \"android_print_service.dart\";",
        "import \"android_print_service.dart\";\nimport \"bluetooth_printer_service.dart\";"
    )

# Adicionar extensoes na lista
if "ImagePickerFletExtension" not in main_dart:
    import re as _re
    main_dart = _re.sub(
        r'List<FletExtension> extensions = \[[\s\n]*\];',
        "List<FletExtension> extensions = [\n  ImagePickerFletExtension(),\n  AndroidPrintFletExtension(),\n  BluetoothPrinterFletExtension(),\n];",
        main_dart,
    )
elif "BluetoothPrinterFletExtension" not in main_dart:
    main_dart = main_dart.replace(
        "AndroidPrintFletExtension(),\n];",
        "AndroidPrintFletExtension(),\n  BluetoothPrinterFletExtension(),\n];"
    )

with open(main_dart_path, "w", encoding="utf-8") as f:
    f.write(main_dart)
print("  -> main.dart modificado com ImagePicker + AndroidPrint extensions")

# 2c2. Patch datecs_printer: adiciona namespace ao build.gradle no pub cache
_dt_gradle = os.path.join(
    os.environ.get('LOCALAPPDATA', ''),
    'Pub', 'Cache', 'hosted', 'pub.dev',
    'datecs_printer-0.0.5', 'android', 'build.gradle',
)
if os.path.exists(_dt_gradle):
    with open(_dt_gradle, 'r', encoding='utf-8') as _f:
        _dg = _f.read()
    _dg_changed = False
    if 'namespace' not in _dg:
        _dg = _dg.replace('android {', 'android {\n    namespace "com.rezins.datecs_printer"', 1)
        _dg_changed = True
    if 'compileSdkVersion 30' in _dg:
        _dg = _dg.replace('compileSdkVersion 30', 'compileSdkVersion 34')
        _dg_changed = True
    if _dg_changed:
        with open(_dt_gradle, 'w', encoding='utf-8') as _f:
            _f.write(_dg)
        print("  -> datecs_printer build.gradle corrigido (namespace + compileSdk 34)")
    else:
        print("  -> datecs_printer build.gradle ja esta correto")
else:
    print(f"  -> AVISO: datecs_printer nao encontrado no pub cache: {_dt_gradle}")

# 2d. Restaurar app.zip corrigido (caso flutter build o recrie)
shutil.copy2(app_zip_backup, app_zip_path)
if os.path.exists(app_zip_hash_path + ".backup"):
    shutil.copy2(app_zip_hash_path + ".backup", app_zip_hash_path)
print("  -> app.zip restaurado do backup (pre-build)")

# 2e. Rebuildar com flutter
print("\n=== Rebuildando com flutter build apk ===")

import glob
sp_dirs = glob.glob(os.path.join(flutter_dir, "build", "build_python_*", "python", "Lib", "site-packages"))
env = os.environ.copy()
if sp_dirs:
    env["SERIOUS_PYTHON_SITE_PACKAGES"] = sp_dirs[0]
    print(f"  -> SERIOUS_PYTHON_SITE_PACKAGES={sp_dirs[0]}")

result = subprocess.run(
    [os.path.join(flutter_path, "flutter.bat"), "build", "apk", "--release"],
    cwd=flutter_dir,
    env=env,
)

if result.returncode != 0:
    print("ERRO no flutter build apk na FASE 2")
    sys.exit(1)

# ============================================================
# FASE 3: Verificar e restaurar app.zip no APK se necessario
# ============================================================
print("\n=== FASE 3: Verificando app.zip no APK final ===")

apk_src = os.path.join(flutter_dir, "build", "app", "outputs", "flutter-apk", "app-release.apk")

# Verificar se o app.zip dentro do APK tem certifi na raiz
with zipfile.ZipFile(apk_src, 'r') as apk:
    # Encontrar app.zip dentro do APK
    app_zip_entries = [e for e in apk.namelist() if 'app.zip' in e and not e.endswith('.hash')]
    print(f"  -> app.zip encontrado no APK: {app_zip_entries}")

# Verificar o app.zip no diretorio flutter (que foi usado no build)
with zipfile.ZipFile(app_zip_path, 'r') as zf:
    has_certifi = any(f == 'certifi/__init__.py' for f in zf.namelist())
    has_venv = any(f.startswith('venv/') for f in zf.namelist())
    total = len(zf.namelist())
    print(f"  -> app.zip atual: {total} arquivos, certifi_raiz={has_certifi}, tem_venv={has_venv}")

if not has_certifi:
    print("  -> AVISO: certifi nao esta na raiz! Restaurando backup e rebuildando...")
    shutil.copy2(app_zip_backup, app_zip_path)
    if os.path.exists(app_zip_hash_path + ".backup"):
        shutil.copy2(app_zip_hash_path + ".backup", app_zip_hash_path)
    # Rebuild rapido (so assets mudaram)
    result = subprocess.run(
        [os.path.join(flutter_path, "flutter.bat"), "build", "apk", "--release"],
        cwd=flutter_dir,
        env=env,
    )
    if result.returncode != 0:
        print("ERRO no rebuild final")
        sys.exit(1)

# Copiar APK final
apk_dst_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "apk")
os.makedirs(apk_dst_dir, exist_ok=True)
shutil.copy2(apk_src, apk_dst_dir)

# Limpar backups
for bk in [app_zip_backup, app_zip_hash_path + ".backup"]:
    if os.path.exists(bk):
        os.remove(bk)

# Tamanho final
apk_final = os.path.join(apk_dst_dir, "app-release.apk")
size_mb = os.path.getsize(apk_final) / (1024 * 1024)
print(f"\n=== APK final: {size_mb:.1f} MB em {apk_dst_dir} ===")
