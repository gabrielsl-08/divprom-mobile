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
if "flutter_bluetooth_serial" not in pubspec:
    import re as _re2
    # Remove pacotes BT anteriores
    pubspec = _re2.sub(r'\n\s*blue_thermal_printer: \S+', '', pubspec)
    pubspec = _re2.sub(r'\n\s*datecs_printer: \S+', '', pubspec)
    pubspec = pubspec.replace(
        "  printing: ^5.13.1",
        "  printing: ^5.13.1\n  flutter_bluetooth_serial: ^0.4.0"
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
bluetooth_service_code = r'''import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/foundation.dart';
import 'package:flet/flet.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';

class BluetoothPrinterFletService extends FletService {
  BluetoothPrinterFletService({required super.control});

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(_invokeMethod);
    debugPrint("BluetoothPrinterFletService (ESC/POS) initialized");
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
      case "listar_pareados":
        return await _listarPareados();
      default:
        throw Exception("Unknown BluetoothPrinter method: $name");
    }
  }

  Future<dynamic> _listarPareados() async {
    try {
      List<BluetoothDevice> devices =
          await FlutterBluetoothSerial.instance.getBondedDevices();
      return devices.map((d) => {
        "nome": d.name ?? "",
        "mac": d.address,
      }).toList();
    } catch (e) {
      debugPrint("Erro ao listar pareados: $e");
      return [];
    }
  }

  // ── ESC/POS constants ─────────────────────────────────────────────────────
  static const List<int> _INIT     = [0x1B, 0x40];
  static const List<int> _ALIGN_L  = [0x1B, 0x61, 0x00];
  static const List<int> _ALIGN_C  = [0x1B, 0x61, 0x01];
  static const List<int> _BOLD_ON  = [0x1B, 0x45, 0x01];
  static const List<int> _BOLD_OFF = [0x1B, 0x45, 0x00];
  static const List<int> _LF      = [0x0A];
  static const List<int> _CUT     = [0x1D, 0x56, 0x42, 0x03];
  static List<int> _feedLines(int n) => [0x1B, 0x64, n];

  List<int> _encode(String text) =>
      text.codeUnits.map((c) => c > 255 ? 63 : c).toList();

  List<int> _textLine(String text, {bool center = false, bool bold = false}) {
    final List<int> buf = [];
    if (center) buf.addAll(_ALIGN_C);
    if (bold) buf.addAll(_BOLD_ON);
    buf.addAll(_encode(text));
    buf.addAll(_LF);
    if (bold) buf.addAll(_BOLD_OFF);
    if (center) buf.addAll(_ALIGN_L);
    return buf;
  }

  // ── Image → ESC/POS raster (GS v 0) ──────────────────────────────────────
  Future<List<int>> _imageToEscpos(String base64Str,
      {int? targetWidth, int? targetHeight}) async {
    try {
      final Uint8List bytes = base64Decode(base64Str);
      final ui.Codec codec = await ui.instantiateImageCodec(
        bytes,
        targetWidth: targetWidth,
        targetHeight: targetHeight,
      );
      final ui.FrameInfo fi = await codec.getNextFrame();
      final int w = fi.image.width;
      final int h = fi.image.height;
      final ByteData? bd =
          await fi.image.toByteData(format: ui.ImageByteFormat.rawRgba);
      fi.image.dispose();
      if (bd == null) return [];

      final Uint8List rgba = bd.buffer.asUint8List();
      final int bytesPerRow = (w + 7) ~/ 8;
      final List<int> bitmap = [];

      for (int y = 0; y < h; y++) {
        for (int bx = 0; bx < bytesPerRow; bx++) {
          int byte = 0;
          for (int bit = 0; bit < 8; bit++) {
            final int px = bx * 8 + bit;
            if (px < w) {
              final int offset = (y * w + px) * 4;
              final int r = rgba[offset];
              final int g = rgba[offset + 1];
              final int b = rgba[offset + 2];
              final int lum = (r * 299 + g * 587 + b * 114) ~/ 1000;
              if (lum < 128) byte |= (0x80 >> bit);
            }
          }
          bitmap.add(byte);
        }
      }

      return [
        0x1D, 0x76, 0x30, 0x00,
        bytesPerRow & 0xFF, (bytesPerRow >> 8) & 0xFF,
        h & 0xFF, (h >> 8) & 0xFF,
        ...bitmap,
      ];
    } catch (e) {
      debugPrint("Erro ao converter imagem ESC/POS: $e");
      return [];
    }
  }

  Future<List<int>> _sigToEscpos(String base64Str) async {
    try {
      final Uint8List bytes = base64Decode(base64Str);
      final ui.Codec c1 = await ui.instantiateImageCodec(bytes);
      final ui.FrameInfo f1 = await c1.getNextFrame();
      final int origW = f1.image.width;
      final int origH = f1.image.height;
      f1.image.dispose();
      return await _imageToEscpos(base64Str,
          targetWidth: (origW * 0.5).round(),
          targetHeight: (origH * 0.33).round());
    } catch (_) {
      return [];
    }
  }

  // ── Print receipt ─────────────────────────────────────────────────────────
  Future<dynamic> _printReceipt(dynamic args) async {
    final String mac = (args["mac_address"] ?? "").toString().toUpperCase();
    final List<dynamic> lines = args["lines"] ?? [];
    final String agentSig = (args["signature_base64"] ?? "").toString();
    final String qrBase64 = (args["qr_base64"] ?? "").toString();

    if (mac.isEmpty) {
      return {"sucesso": false, "erro": "MAC da impressora nao configurado"};
    }

    BluetoothConnection? conn;
    try {
      conn = await BluetoothConnection.toAddress(mac);
      await Future.delayed(const Duration(milliseconds: 300));

      final List<int> buf = [];
      buf.addAll(_INIT);
      buf.addAll(_ALIGN_L);

      for (final line in lines) {
        final String s = line.toString();

        if (s == "__AGENTE_SIG__") {
          if (agentSig.isNotEmpty) buf.addAll(await _sigToEscpos(agentSig));
          buf.addAll(_feedLines(2));

        } else if (s == "__SPACER__") {
          buf.addAll(_feedLines(3));

        } else if (s == "__QR_STATIC__") {
          if (qrBase64.isNotEmpty) {
            buf.addAll(await _imageToEscpos(qrBase64, targetWidth: 200));
          }

        } else if (s.startsWith("__CENTRO__")) {
          buf.addAll(_textLine(s.substring(10), center: true, bold: true));

        } else if (s.isNotEmpty &&
            s.split('').every((c) => c == s[0]) &&
            '-=_'.contains(s[0])) {
          buf.addAll(_encode(s));
          buf.addAll(_LF);

        } else if (s.trim().isEmpty) {
          buf.addAll(_LF);

        } else {
          buf.addAll(_encode(s));
          buf.addAll(_LF);
        }
      }

      buf.addAll(_feedLines(5));
      buf.addAll(_CUT);

      conn.output.add(Uint8List.fromList(buf));
      await conn.output.allSent;
      await Future.delayed(const Duration(milliseconds: 500));

      return {"sucesso": true};
    } catch (e) {
      debugPrint("Erro ao imprimir via BT ESC/POS: $e");
      final msg = e.toString().toLowerCase();
      if (msg.contains("connect") || msg.contains("socket") || msg.contains("host")) {
        return {"sucesso": false, "erro": "Impressora desligada ou fora de alcance"};
      }
      return {"sucesso": false, "erro": "Erro: ${e.toString().split("\n").first}"};
    } finally {
      try { conn?.dispose(); } catch (_) {}
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

# 2c2. Patch flutter_bluetooth_serial: namespace no build.gradle
_fbs_gradle = os.path.join(
    os.environ.get('LOCALAPPDATA', ''),
    'Pub', 'Cache', 'hosted', 'pub.dev',
    'flutter_bluetooth_serial-0.4.0', 'android', 'build.gradle',
)
if os.path.exists(_fbs_gradle):
    with open(_fbs_gradle, 'r', encoding='utf-8') as _f:
        _fbsg = _f.read()
    _fbsg_changed = False
    if 'namespace' not in _fbsg:
        _fbsg = _fbsg.replace(
            'android {',
            'android {\n    namespace "com.dexterx.flutter_bluetooth_serial"', 1
        )
        _fbsg_changed = True
    if _fbsg_changed:
        with open(_fbs_gradle, 'w', encoding='utf-8') as _f:
            _f.write(_fbsg)
        print("  -> flutter_bluetooth_serial build.gradle corrigido (namespace)")
    else:
        print("  -> flutter_bluetooth_serial build.gradle ja esta correto")
else:
    print(f"  -> AVISO: flutter_bluetooth_serial nao encontrado no pub cache")

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
