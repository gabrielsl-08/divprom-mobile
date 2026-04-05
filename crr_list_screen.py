# crr_list_screen.py
"""
Tela de listagem de CRRs - somente online.
Mostra os 10 ultimos CRRs com opcao de reimprimir e editar condutor.
"""
import asyncio
import flet as ft
from datetime import datetime
from print_utils import gerar_linhas_impressao
from print_dialog import mostrar_dialogo_impressao


def build_crr_list_screen(page: ft.Page, on_voltar, api_client, local_db, print_service=None, img_picker=None):
    """Constroi a tela de listagem de CRRs"""

    credenciais = local_db.obter_credenciais()
    matricula = credenciais.get('identificador', '') if credenciais else ''

    lista_crrs = ft.Column(controls=[], spacing=8, scroll=ft.ScrollMode.AUTO)
    status_text = ft.Text("", size=14)
    loading = ft.ProgressRing(visible=False, width=20, height=20)

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
                status_envio.value = "Informe um email valido"
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

    def reimprimir_crr(dados):
        lines = gerar_linhas_impressao(dados)
        sig_b64 = local_db.obter_config('assinatura_base64') or ''
        condutor_sig = dados.get('assinaturaCondutor', '')

        async def _reimprimir():
            await mostrar_dialogo_impressao(
                page=page,
                print_service=print_service,
                lines=lines,
                signature_base64=sig_b64,
                condutor_signature_base64=condutor_sig,
            )

        page.run_task(_reimprimir)

    def abrir_dialogo_editar_condutor(dados):
        crr_id = dados.get('id')
        situacao_atual = dados.get('situacaoEntrega', '') or ''

        assinatura_b64 = {'value': ''}
        preview_column = ft.Column([], spacing=4)

        async def capturar_assinatura(e):
            try:
                resultado = await img_picker.pick_image_camera(image_quality=85)
                if resultado and resultado.base64:
                    assinatura_b64['value'] = resultado.base64
                    preview_column.controls = [
                        ft.Image(
                            src_base64=resultado.base64,
                            width=220,
                            height=110,
                            border_radius=6,
                        ),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_700, size=16),
                                ft.Text("Foto capturada com sucesso!", size=12, color=ft.Colors.GREEN_700),
                            ],
                            spacing=4,
                        ),
                    ]
                    preview_column.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Erro ao capturar foto: {ex}"),
                    bgcolor=ft.Colors.RED,
                )
                page.snack_bar.open = True
                page.update()

        def limpar_assinatura(e):
            assinatura_b64['value'] = ''
            preview_column.controls = []
            preview_column.update()

        btn_foto_assinatura = ft.ElevatedButton(
            "Fotografar Assinatura",
            icon=ft.Icons.CAMERA_ALT,
            on_click=capturar_assinatura,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        assinatura_section = ft.Column([
            ft.Text("Assinatura do Condutor", size=12,
                    weight=ft.FontWeight.W_500, color=ft.Colors.TEAL_700),
            ft.Text("Imprima, o condutor assina no papel, depois fotografe.",
                    size=11, color=ft.Colors.GREY_600),
            btn_foto_assinatura,
            preview_column,
            ft.TextButton("Limpar foto", icon=ft.Icons.CLEAR,
                          on_click=limpar_assinatura),
        ], visible=(situacao_atual == 'assinou e recebeu 2a via'), spacing=6)

        dlg_ref = {'dlg': None}

        def on_rg_change(e):
            eh_assinou = rg_situacao.value == 'assinou e recebeu 2a via'
            assinatura_section.visible = eh_assinou
            if not eh_assinou:
                assinatura_b64['value'] = ''
                preview_column.controls = []
            if dlg_ref['dlg']:
                dlg_ref['dlg'].update()
            else:
                page.update()

        rg_situacao = ft.RadioGroup(
            value=situacao_atual or None,
            on_change=on_rg_change,
            content=ft.Column([
                ft.Radio(value="assinou e recebeu 2a via",
                         label="Assinou e recebeu 2ª via"),
                ft.Radio(value="recusou assinar e recebeu 2a via",
                         label="Recusou assinar e recebeu 2ª via"),
                ft.Radio(value="recusou assinar e a receber 2a via",
                         label="Recusou assinar e a receber 2ª via"),
                ft.Radio(value="condutor ausente",
                         label="Condutor ausente"),
            ], spacing=2),
        )

        def salvar(e):
            if page.overlay:
                page.overlay[-1].open = False
            page.update()

            try:
                resultado = api_client.atualizar_condutor_crr(crr_id, {
                    'situacaoEntrega': rg_situacao.value or '',
                    'assinaturaCondutor': assinatura_b64['value'],
                })
            except Exception as ex:
                resultado = {'sucesso': False, 'erro': str(ex)}

            if resultado.get('sucesso'):
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Condutor atualizado com sucesso"),
                    bgcolor=ft.Colors.GREEN,
                )
                carregar_crrs()
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Erro: {resultado.get('erro', 'Erro ao salvar')}"),
                    bgcolor=ft.Colors.RED,
                )
            page.snack_bar.open = True
            page.update()

        def cancelar(e):
            if page.overlay:
                page.overlay[-1].open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Editar Entrega do Condutor", size=15, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Situacao de Entrega", size=12, weight=ft.FontWeight.W_500,
                            color=ft.Colors.TEAL_700),
                    rg_situacao,
                    assinatura_section,
                ], scroll=ft.ScrollMode.AUTO, spacing=8),
                width=300,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Salvar",
                    icon=ft.Icons.SAVE,
                    on_click=salvar,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.TEAL, color=ft.Colors.WHITE),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        dlg_ref['dlg'] = dlg
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def criar_card_crr(dados):
        numero = dados.get('numeroCrr', '---')
        placa_v = dados.get('placa', '---')
        condutor = dados.get('nomeCondutor', '') or 'Ausente'
        data_raw = dados.get('dataFiscalizacao', '')
        try:
            data = datetime.strptime(data_raw, '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            data = data_raw or '---'
        hora = dados.get('horaFiscalizacao', '')
        medida = dados.get('medidaAdministrativa', '---')
        situacao = dados.get('situacaoEntrega', '')

        return ft.Container(
            content=ft.Column(controls=[
                ft.Row(controls=[
                    ft.Text(numero, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_NOTE,
                        icon_color=ft.Colors.TEAL,
                        icon_size=22,
                        tooltip="Editar entrega do condutor",
                        on_click=lambda e, d=dados: abrir_dialogo_editar_condutor(d),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EMAIL,
                        icon_color=ft.Colors.BLUE,
                        icon_size=20,
                        tooltip="Enviar por email",
                        on_click=lambda e, d=dados: mostrar_dialogo_email(d),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PRINT,
                        icon_color=ft.Colors.BLUE,
                        icon_size=20,
                        tooltip="Reimprimir CRR",
                        on_click=lambda e, d=dados: reimprimir_crr(d),
                    ),
                ]),
                ft.Divider(height=1),
                ft.Row(controls=[
                    ft.Icon(ft.Icons.DIRECTIONS_CAR, size=16, color=ft.Colors.GREY_600),
                    ft.Text(f"Placa: {placa_v}", size=13),
                ], spacing=5),
                ft.Row(controls=[
                    ft.Icon(ft.Icons.PERSON, size=16, color=ft.Colors.GREY_600),
                    ft.Text(f"Condutor: {condutor}", size=13),
                ], spacing=5),
                ft.Row(controls=[
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ft.Colors.GREY_600),
                    ft.Text(f"{data} {hora}", size=13),
                ], spacing=5),
                ft.Row(controls=[
                    ft.Icon(ft.Icons.GAVEL, size=16, color=ft.Colors.GREY_600),
                    ft.Text(medida, size=12, color=ft.Colors.GREY_700),
                ], spacing=5),
                ft.Row(controls=[
                    ft.Icon(ft.Icons.ASSIGNMENT_TURNED_IN, size=16, color=ft.Colors.TEAL_600),
                    ft.Text(
                        situacao.upper() if situacao else "Entrega nao registrada",
                        size=12,
                        color=ft.Colors.TEAL_700 if situacao else ft.Colors.ORANGE_700,
                        italic=not situacao,
                    ),
                ], spacing=5),
            ], spacing=5),
            padding=15, border_radius=10, bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )

    def carregar_crrs(e=None):
        loading.visible = True
        status_text.value = "Carregando..."
        status_text.color = ft.Colors.BLUE
        lista_crrs.controls = []
        page.update()

        async def _carregar():
            try:
                resultado = await asyncio.to_thread(api_client.listar_crrs)
                if resultado.get('sucesso'):
                    crrs = resultado.get('crrs', [])
                    if not crrs:
                        status_text.value = "Nenhum CRR encontrado"
                        status_text.color = ft.Colors.GREY_600
                    else:
                        status_text.value = f"{len(crrs)} CRR(s) encontrado(s)"
                        status_text.color = ft.Colors.GREEN
                        lista_crrs.controls = [criar_card_crr(c) for c in crrs]
                else:
                    erro = resultado.get('erro', 'Erro ao carregar')
                    status_text.value = erro
                    status_text.color = ft.Colors.RED
            except Exception:
                status_text.value = "Sem conexao com o servidor"
                status_text.color = ft.Colors.RED
            loading.visible = False
            page.update()

        page.run_task(_carregar)

    carregar_crrs()

    return ft.Container(
        content=ft.Column(controls=[
            ft.Container(
                content=ft.Row(controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE,
                                  on_click=on_voltar),
                    ft.Text("Meus CRRs", size=20, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.Icons.REFRESH, icon_color=ft.Colors.WHITE,
                                  on_click=carregar_crrs),
                ]),
                bgcolor=ft.Colors.BLUE,
                padding=ft.padding.only(top=40, left=10, right=10, bottom=12),
            ),
            ft.Container(
                content=ft.Row(controls=[
                    ft.Icon(ft.Icons.BADGE, size=18, color=ft.Colors.BLUE),
                    ft.Text(f"Agente: {matricula}", size=14, weight=ft.FontWeight.W_500),
                ], spacing=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
            ),
            ft.Container(
                content=ft.Row(controls=[loading, status_text],
                               alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=20),
            ),
            ft.Container(
                content=lista_crrs,
                padding=ft.padding.symmetric(horizontal=15, vertical=5),
                expand=True,
            ),
        ], spacing=0),
        expand=True,
    )
