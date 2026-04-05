# print_dialog.py
"""
Diálogo de seleção de impressora Bluetooth para impressão de CRR.
Usa BluetoothPrintService (blue_thermal_printer via Dart) para listar
dispositivos BT pareados e imprimir após seleção do usuário.
"""
import asyncio
import flet as ft


def _mensagem_amigavel(erro: str) -> str:
    """Converte erros técnicos em mensagens legíveis."""
    e = (erro or "").lower()
    if "desligada" in e or "fora de alcance" in e:
        return erro
    if "connect_error" in e or "read failed" in e or "ioexception" in e:
        return "Impressora desligada ou fora de alcance"
    if "nao encontrada" in e or "not found" in e:
        return "Impressora não encontrada nos pareados"
    if "mac" in e and "configurado" in e:
        return "MAC da impressora não configurado"
    if erro:
        # Retorna apenas a primeira linha do stack trace
        return erro.split("\n")[0][:80]
    return "Falha desconhecida na impressão"


async def mostrar_dialogo_impressao(
    page: ft.Page,
    print_service,
    lines: list,
    signature_base64: str = "",
    condutor_signature_base64: str = "",
):
    """
    Abre um diálogo que lista impressoras BT pareadas.
    Após seleção, envia o cupom via print_service.print_receipt().
    """
    if not print_service:
        return

    fechado = asyncio.Event()
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            ft.Text("Impressora Bluetooth", expand=True),
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_size=20,
                on_click=lambda e: _fechar(),
            ),
        ]),
    )

    def _fechar():
        dlg.open = False
        page.update()
        fechado.set()

    # Estado inicial: buscando dispositivos
    dlg.content = ft.Column(
        [
            ft.ProgressRing(width=28, height=28),
            ft.Text("Buscando impressoras pareadas...", size=14),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
        tight=True,
    )
    dlg.actions = []
    page.overlay.append(dlg)
    dlg.open = True
    page.update()

    # Busca dispositivos pareados via Dart
    try:
        dispositivos = await print_service.listar_pareados()
    except Exception:
        dispositivos = []

    if not dispositivos:
        dlg.content = ft.Column(
            [
                ft.Icon(
                    ft.Icons.BLUETOOTH_DISABLED,
                    size=40,
                    color=ft.Colors.GREY_400,
                ),
                ft.Text(
                    "Nenhuma impressora Bluetooth pareada.\n"
                    "Pareie a impressora nas configurações do Android.",
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        )
        dlg.actions = [ft.TextButton("Fechar", on_click=lambda e: _fechar())]
        page.update()
        await fechado.wait()
        return

    # Monta lista de dispositivos para seleção
    status_row = ft.Row([], visible=False)
    altura = min(len(dispositivos) * 56, 280)
    lista = ft.Column(
        spacing=4, scroll=ft.ScrollMode.AUTO, height=altura
    )

    async def _imprimir(mac: str, nome: str):
        lista.visible = False
        status_row.visible = True
        status_row.controls = [
            ft.ProgressRing(width=20, height=20),
            ft.Text(f"Imprimindo em {nome}...", size=13),
        ]
        dlg.actions = []
        page.update()

        # Usar protocolo Datecs para ambas as impressoras (com Master Reset)
        _tipo = "datecs"

        try:
            resultado = await print_service.print_receipt(
                lines=lines,
                signature_base64=signature_base64,
                condutor_signature_base64=condutor_signature_base64,
                mac_address=mac,
                printer_type=_tipo,
            )
            if isinstance(resultado, dict):
                sucesso = resultado.get("sucesso", False)
                erro = resultado.get("erro", "")
            else:
                sucesso = False
                erro = str(resultado)
        except Exception as ex:
            sucesso = False
            erro = str(ex)

        if sucesso:
            status_row.controls = [
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=22),
                ft.Text("Impressão enviada com sucesso!", size=13),
            ]
        else:
            status_row.controls = [
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=22),
                ft.Text(_mensagem_amigavel(erro), size=13),
            ]
        dlg.actions = [ft.TextButton("Fechar", on_click=lambda e: _fechar())]
        page.update()

    for dev in dispositivos:
        mac = dev.get("mac", "")
        nome = dev.get("nome", mac) or mac

        def _make_click(m, n):
            def _click(e):
                page.run_task(_imprimir, m, n)
            return _click

        lista.controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.PRINT, color=ft.Colors.BLUE),
                title=ft.Text(nome, size=14),
                subtitle=ft.Text(mac, size=11, color=ft.Colors.GREY_600),
                on_click=_make_click(mac, nome),
            )
        )

    dlg.content = ft.Column(
        [
            ft.Text(
                "Selecione a impressora:",
                size=14,
                weight=ft.FontWeight.BOLD,
            ),
            lista,
            status_row,
        ],
        spacing=8,
        tight=True,
    )
    dlg.actions = [ft.TextButton("Cancelar", on_click=lambda e: _fechar())]
    page.update()
    await fechado.wait()
