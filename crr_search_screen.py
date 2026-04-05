# crr_search_screen.py
"""
Tela de pesquisa de CRRs por filtros: CRR, Placa, Marca, Modelo, Data.
"""
import asyncio
import flet as ft
from print_utils import gerar_linhas_impressao
from print_dialog import mostrar_dialogo_impressao


def build_crr_search_screen(page: ft.Page, on_voltar, api_client, local_db, print_service=None):
    """Constroi a tela de pesquisa de CRRs"""

    def aplicar_mascara_data(e):
        raw = ''.join(c for c in e.control.value if c.isdigit())[:8]
        if len(raw) > 4:
            resultado = raw[:2] + '/' + raw[2:4] + '/' + raw[4:]
        elif len(raw) > 2:
            resultado = raw[:2] + '/' + raw[2:]
        else:
            resultado = raw
        e.control.value = resultado
        e.control.update()

    # Campos de filtro
    campo_crr = ft.TextField(
        label="Numero CRR", border_radius=8,
        capitalization=ft.TextCapitalization.CHARACTERS,
        keyboard_type=ft.KeyboardType.VISIBLE_PASSWORD,
    )
    campo_placa = ft.TextField(
        label="Placa", border_radius=8,
        capitalization=ft.TextCapitalization.CHARACTERS,
        max_length=8,
    )
    campo_marca = ft.TextField(
        label="Marca", border_radius=8,
        capitalization=ft.TextCapitalization.CHARACTERS,
    )
    campo_modelo = ft.TextField(
        label="Modelo", border_radius=8,
        capitalization=ft.TextCapitalization.CHARACTERS,
    )
    campo_data = ft.TextField(
        label="Data (DD/MM/AAAA)", border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text="Ex: 15/01/2024",
        on_change=aplicar_mascara_data,
    )

    lista_resultados = ft.Column(controls=[], spacing=8, scroll=ft.ScrollMode.AUTO)
    status_text = ft.Text("", size=14)
    loading = ft.ProgressRing(visible=False, width=20, height=20)

    def reimprimir_crr(dados):
        lines = gerar_linhas_impressao(dados)
        sig_b64 = local_db.obter_config('assinatura_base64') or ''

        async def _reimprimir():
            await mostrar_dialogo_impressao(
                page=page,
                print_service=print_service,
                lines=lines,
                signature_base64=sig_b64,
            )

        page.run_task(_reimprimir)

    def mostrar_dialogo_email(dados):
        crr_id = dados.get('id')
        if not crr_id:
            return
        campo_email = ft.TextField(
            label="Email do condutor",
            keyboard_type=ft.KeyboardType.EMAIL,
            border_radius=8,
        )
        status_envio = ft.Text("", size=12)
        loading_envio = ft.ProgressRing(visible=False, width=16, height=16)

        def fechar_dlg(ev):
            dlg.open = False
            page.update()

        def enviar_click(ev):
            email_val = campo_email.value.strip() if campo_email.value else ''
            if not email_val or '@' not in email_val:
                status_envio.value = "Informe um email válido"
                status_envio.color = ft.Colors.RED
                page.update()
                return

            loading_envio.visible = True
            status_envio.value = "Enviando..."
            status_envio.color = ft.Colors.BLUE
            page.update()

            async def _enviar():
                resultado = await asyncio.to_thread(
                    api_client.enviar_email_condutor, crr_id, email_val
                )
                loading_envio.visible = False
                if resultado.get('sucesso'):
                    status_envio.value = "Email enviado com sucesso!"
                    status_envio.color = ft.Colors.GREEN
                else:
                    erro = resultado.get('erro', 'Erro ao enviar')
                    status_envio.value = erro
                    status_envio.color = ft.Colors.RED
                page.update()

            page.run_task(_enviar)

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.EMAIL, color=ft.Colors.BLUE, size=24),
                ft.Text("Enviar CRR por Email", size=16, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Column([
                ft.Text(f"CRR: {dados.get('numeroCrr', '')}", size=13),
                campo_email,
                ft.Row([loading_envio, status_envio], spacing=8),
            ], tight=True, spacing=10),
            actions=[
                ft.ElevatedButton(
                    "Enviar", icon=ft.Icons.SEND,
                    on_click=enviar_click,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
                ),
                ft.TextButton("Fechar", on_click=fechar_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def criar_card_crr(dados):
        placa_v = dados.get('placa', '---')
        marca = dados.get('marca', '-')
        modelo = dados.get('modelo', '-')
        cor = dados.get('cor', '-')
        data_raw = dados.get('dataFiscalizacao', '---')
        try:
            from datetime import datetime as dt
            data = dt.strptime(data_raw, '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            data = data_raw
        hora = dados.get('horaFiscalizacao', '')
        status = dados.get('status', '')
        local_patio = dados.get('localPatio', '-')

        status_label = 'Liberado' if status == 'liberado' else 'Retido'
        status_color = (ft.Colors.GREEN_700 if status == 'liberado'
                        else ft.Colors.RED_700)

        return ft.Container(
            content=ft.Column(controls=[
                ft.Row(controls=[
                    ft.Icon(ft.Icons.DIRECTIONS_CAR, size=16,
                            color=ft.Colors.BLUE),
                    ft.Text(f"Placa: {placa_v}", size=15,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(
                            status_label, size=12,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=status_color,
                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                        border_radius=4,
                    ),
                ]),
                ft.Divider(height=1),
                ft.Text(f"{marca} {modelo} • {cor}", size=13,
                        color=ft.Colors.GREY_700),
                ft.Row(controls=[
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=14,
                            color=ft.Colors.GREY_500),
                    ft.Text(f"{data} {hora}", size=12,
                            color=ft.Colors.GREY_600),
                ], spacing=4),
                ft.Row(controls=[
                    ft.Icon(ft.Icons.WAREHOUSE, size=14,
                            color=ft.Colors.GREY_500),
                    ft.Text(f"Pátio: {local_patio}", size=12,
                            color=ft.Colors.GREY_600),
                ], spacing=4),
                ft.Row(controls=[
                    ft.IconButton(
                        icon=ft.Icons.PRINT, icon_size=18,
                        tooltip="Reimprimir",
                        on_click=lambda e, d=dados: reimprimir_crr(d),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EMAIL, icon_size=18,
                        tooltip="Enviar por email",
                        on_click=lambda e, d=dados: mostrar_dialogo_email(d),
                    ),
                ], spacing=0),
            ], spacing=6),
            padding=15, border_radius=10, bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=5,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            ),
        )

    def pesquisar(e=None):
        crr = campo_crr.value.strip() if campo_crr.value else ''
        placa = campo_placa.value.strip() if campo_placa.value else ''
        marca = campo_marca.value.strip() if campo_marca.value else ''
        modelo = campo_modelo.value.strip() if campo_modelo.value else ''
        data_display = campo_data.value.strip() if campo_data.value else ''

        if not any([crr, placa, marca, modelo, data_display]):
            status_text.value = "Informe ao menos um filtro"
            status_text.color = ft.Colors.ORANGE
            page.update()
            return

        # Converte DD/MM/AAAA -> AAAA-MM-DD para a API
        data_api = ''
        if data_display:
            try:
                from datetime import datetime
                data_api = datetime.strptime(data_display, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                data_api = data_display

        loading.visible = True
        status_text.value = "Buscando..."
        status_text.color = ft.Colors.BLUE
        lista_resultados.controls.clear()
        page.update()

        async def _buscar():
            try:
                resultado = await asyncio.to_thread(
                    api_client.buscar_crrs,
                    placa=placa, marca=marca, modelo=modelo,
                    data=data_api, numero_crr=crr,
                )
                if resultado.get('sucesso'):
                    crrs = resultado.get('crrs', [])
                    if not crrs:
                        status_text.value = "Nenhum CRR encontrado"
                        status_text.color = ft.Colors.GREY_600
                    else:
                        status_text.value = f"{len(crrs)} CRR(s) encontrado(s)"
                        status_text.color = ft.Colors.GREEN
                        for c in crrs:
                            lista_resultados.controls.append(criar_card_crr(c))
                else:
                    erro = resultado.get('erro', 'Erro ao buscar')
                    status_text.value = erro
                    status_text.color = ft.Colors.RED
            except Exception:
                status_text.value = "Sem conexao com o servidor"
                status_text.color = ft.Colors.RED
            loading.visible = False
            page.update()

        page.run_task(_buscar)

    def limpar_filtros(e=None):
        campo_crr.value = ''
        campo_placa.value = ''
        campo_marca.value = ''
        campo_modelo.value = ''
        campo_data.value = ''
        lista_resultados.controls.clear()
        status_text.value = ''
        page.update()

    return ft.Container(
        content=ft.Column(controls=[
            # Header
            ft.Container(
                content=ft.Row(controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=ft.Colors.WHITE,
                        on_click=on_voltar,
                    ),
                    ft.Text(
                        "Pesquisar CRR", size=20,
                        weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLEAR_ALL,
                        icon_color=ft.Colors.WHITE,
                        tooltip="Limpar filtros",
                        on_click=limpar_filtros,
                    ),
                ]),
                bgcolor=ft.Colors.INDIGO,
                padding=ft.padding.only(top=40, left=10, right=10, bottom=12),
            ),
            # Filtros
            ft.Container(
                content=ft.Column(controls=[
                    ft.Text("Filtros de busca", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                    ft.Row([
                        ft.Container(content=campo_crr, expand=1),
                        ft.Container(content=campo_placa, expand=1),
                    ], spacing=10),
                    ft.Row([
                        ft.Container(content=campo_marca, expand=1),
                        ft.Container(content=campo_modelo, expand=1),
                    ], spacing=10),
                    campo_data,
                    ft.ElevatedButton(
                        "Buscar",
                        icon=ft.Icons.SEARCH,
                        on_click=pesquisar,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.INDIGO,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ], spacing=10),
                padding=ft.padding.symmetric(horizontal=15, vertical=12),
                bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(
                    spread_radius=0, blur_radius=4,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)
                ),
            ),
            # Status e resultados
            ft.Container(
                content=ft.Row(
                    controls=[loading, status_text],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=8),
            ),
            ft.Container(
                content=lista_resultados,
                padding=ft.padding.symmetric(horizontal=15, vertical=5),
                expand=True,
            ),
        ], spacing=0),
        expand=True,
    )
