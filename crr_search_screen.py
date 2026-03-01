# crr_search_screen.py
"""
Tela de pesquisa de CRRs por filtros: Placa, Marca, Modelo, Data.
"""
import flet as ft
from print_utils import gerar_linhas_impressao


def build_crr_search_screen(page: ft.Page, on_voltar, api_client, local_db, print_service=None):
    """Constroi a tela de pesquisa de CRRs"""

    # Campos de filtro
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
        label="Data (AAAA-MM-DD)", border_radius=8,
        keyboard_type=ft.KeyboardType.DATETIME,
        hint_text="Ex: 2024-01-15",
    )

    lista_resultados = ft.Column(controls=[], spacing=8, scroll=ft.ScrollMode.AUTO)
    status_text = ft.Text("", size=14)
    loading = ft.ProgressRing(visible=False, width=20, height=20)

    def reimprimir_crr(dados):
        lines = gerar_linhas_impressao(dados)
        sig_b64 = local_db.obter_config('assinatura_base64') or ''

        async def _reimprimir():
            if print_service:
                try:
                    await print_service.print_receipt(
                        lines=lines,
                        signature_base64=sig_b64,
                    )
                except Exception:
                    pass

        page.run_task(_reimprimir)

    def criar_card_crr(dados):
        placa_v = dados.get('placa', '---')
        marca = dados.get('marca', '-')
        modelo = dados.get('modelo', '-')
        cor = dados.get('cor', '-')
        data = dados.get('dataFiscalizacao', '---')
        hora = dados.get('horaFiscalizacao', '')
        status = dados.get('status', '')

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
            ], spacing=6),
            padding=15, border_radius=10, bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=5,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            ),
        )

    def pesquisar(e=None):
        placa = campo_placa.value.strip() if campo_placa.value else ''
        marca = campo_marca.value.strip() if campo_marca.value else ''
        modelo = campo_modelo.value.strip() if campo_modelo.value else ''
        data = campo_data.value.strip() if campo_data.value else ''

        if not any([placa, marca, modelo, data]):
            status_text.value = "Informe ao menos um filtro"
            status_text.color = ft.Colors.ORANGE
            page.update()
            return

        loading.visible = True
        status_text.value = "Buscando..."
        status_text.color = ft.Colors.BLUE
        lista_resultados.controls.clear()
        page.update()

        try:
            resultado = api_client.buscar_crrs(
                placa=placa, marca=marca, modelo=modelo, data=data
            )
            if resultado.get('sucesso'):
                crrs = resultado.get('crrs', [])
                if not crrs:
                    status_text.value = "Nenhum CRR encontrado"
                    status_text.color = ft.Colors.GREY_600
                else:
                    status_text.value = f"{len(crrs)} CRR(s) encontrado(s)"
                    status_text.color = ft.Colors.GREEN
                    for crr in crrs:
                        lista_resultados.controls.append(criar_card_crr(crr))
            else:
                erro = resultado.get('erro', 'Erro ao buscar')
                status_text.value = erro
                status_text.color = ft.Colors.RED
        except Exception:
            status_text.value = "Sem conexao com o servidor"
            status_text.color = ft.Colors.RED

        loading.visible = False
        page.update()

    def limpar_filtros(e=None):
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
                bgcolor=ft.Colors.INDIGO, padding=15,
            ),
            # Filtros
            ft.Container(
                content=ft.Column(controls=[
                    ft.Text("Filtros de busca", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                    ft.Row([
                        ft.Container(content=campo_placa, expand=1),
                        ft.Container(content=campo_marca, expand=1),
                    ], spacing=10),
                    ft.Row([
                        ft.Container(content=campo_modelo, expand=1),
                        ft.Container(content=campo_data, expand=1),
                    ], spacing=10),
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
