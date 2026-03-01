# home_screen.py
"""
Tela principal do aplicativo.
"""
import flet as ft


def build_home_screen(page: ft.Page, on_novo_crr, on_meus_crrs, on_logout, api_client, local_db, on_buscar_crr=None):
    """Constroi a tela principal com menu de opcoes"""

    credenciais = local_db.obter_credenciais()
    nome_disp = credenciais.get('identificador', 'Agente') if credenciais else 'Agente'

    def criar_botao_menu(icone, cor, titulo, subtitulo, on_click=None):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icone, size=28, color=ft.Colors.WHITE),
                    bgcolor=cor, border_radius=10, padding=12,
                ),
                ft.Column([
                    ft.Text(titulo, size=15, weight=ft.FontWeight.W_600),
                    ft.Text(subtitulo, size=11, color=ft.Colors.GREY_600),
                ], spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400),
            ], spacing=12, alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            border_radius=12, bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=4, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            on_click=on_click,
        )

    return ft.Container(
        content=ft.Column([
            # Header
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.DIRECTIONS_CAR, size=32, color=ft.Colors.WHITE),
                        ft.Column([
                            ft.Text("DivProm Mobile", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text(f"Agente: {nome_disp}", size=11, color=ft.Colors.WHITE70),
                        ], spacing=0, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT, icon_color=ft.Colors.WHITE70,
                            icon_size=20, on_click=on_logout, tooltip="Sair",
                        ),
                    ]),
                ], spacing=0),
                bgcolor=ft.Colors.BLUE,
                padding=ft.padding.only(top=35, bottom=15, left=15, right=15),
                border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
            ),

            # Menu
            ft.Container(
                content=ft.Column([
                    ft.Container(height=10),
                    # Novo CRR - destaque
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ADD_CIRCLE, size=40, color=ft.Colors.WHITE),
                            ft.Column([
                                ft.Text("Novo CRR", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                ft.Text("Cadastrar registro", size=11, color=ft.Colors.WHITE70),
                            ], spacing=2, expand=True),
                            ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.WHITE),
                        ], spacing=15),
                        padding=ft.padding.symmetric(horizontal=20, vertical=18),
                        border_radius=12,
                        gradient=ft.LinearGradient(
                            colors=[ft.Colors.BLUE_600, ft.Colors.BLUE_400],
                            begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0),
                        ),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.3, ft.Colors.BLUE)),
                        on_click=on_novo_crr,
                    ),
                    ft.Container(height=15),
                    criar_botao_menu(
                        ft.Icons.LIST_ALT, ft.Colors.INDIGO,
                        "Meus CRRs", "Ver registros cadastrados",
                        on_click=on_meus_crrs,
                    ),
                    ft.Container(height=10),
                    criar_botao_menu(
                        ft.Icons.SEARCH, ft.Colors.TEAL,
                        "Pesquisar CRR", "Buscar por placa, marca, modelo ou data",
                        on_click=on_buscar_crr,
                    ),
                ], spacing=0),
                padding=ft.padding.symmetric(horizontal=15),
                expand=True,
            ),

            # Rodape
            ft.Container(
                content=ft.Text("v1.0 - DivProm 2025", size=10, color=ft.Colors.GREY_500),
                padding=ft.padding.only(bottom=10),
                alignment=ft.Alignment(0, 0),
            ),
        ], spacing=0),
        bgcolor=ft.Colors.GREY_100, expand=True,
    )
