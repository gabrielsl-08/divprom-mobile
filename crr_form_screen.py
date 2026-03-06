# crr_form_screen.py
"""
Tela de formulario para cadastro de CRR - Layout Carrossel.
Modo online apenas.
"""
import flet as ft
import base64
from datetime import datetime
from print_utils import gerar_texto_impressao, gerar_linhas_impressao
from image_picker_service import ImagePickerService


def build_crr_form_screen(
    page: ft.Page, on_voltar, on_salvar, api_client, local_db,
    print_service=None,
):
    """Constroi o formulario de cadastro de CRR em formato carrossel"""

    pagina_atual = 0
    total_paginas = 7

    titulos_secoes = [
        "Veiculo", "Fiscalizacao", "AITs e Enquadramentos",
        "Outros Dados", "Condutor", "Imagens", "Revisao"
    ]

    # Obtem proximo numero do servidor
    proximo = "Carregando..."
    credenciais = local_db.obter_credenciais()
    matricula_usuario = credenciais.get('identificador', '') if credenciais else ''

    # ==================== FUNCOES DE MASCARA ==================== #

    def aplicar_mascara_placa(e):
        raw = e.control.value.upper().replace("-", "").replace(" ", "")
        # Formato: LLL-NXNN (L=letra, N=numero, X=letra ou numero)
        resultado = ""
        for i, c in enumerate(raw):
            if i < 3:
                if c.isalpha():
                    resultado += c
                else:
                    continue
            elif i == 3:
                if c.isdigit():
                    resultado += c
                else:
                    continue
            elif i == 4:
                if c.isalnum():
                    resultado += c
                else:
                    continue
            elif i <= 6:
                if c.isdigit():
                    resultado += c
                else:
                    continue
            if len(resultado) >= 7:
                break
        if len(resultado) > 3:
            resultado = resultado[:3] + "-" + resultado[3:]
        e.control.value = resultado
        # Teclado igual ao campo senha (VISIBLE_PASSWORD): letras + numeros, sem sugestões
        e.control.keyboard_type = ft.KeyboardType.VISIBLE_PASSWORD
        e.control.capitalization = ft.TextCapitalization.CHARACTERS
        e.control.update()

    def forcar_maiusculo(e):
        if e.control.value:
            e.control.value = e.control.value.upper()
            e.control.update()

    def aplicar_mascara_chassi(e):
        valor = e.control.value.upper().replace(" ", "")
        valor = ''.join(c for c in valor if c.isalnum())[:20]
        e.control.value = valor
        e.control.update()

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

    def aplicar_mascara_enquadramento(e):
        valor = ''.join(c for c in e.control.value if c.isdigit())[:5]
        e.control.value = valor
        e.control.update()

    def aplicar_mascara_cpf(e):
        raw = ''.join(c for c in e.control.value if c.isdigit())[:11]
        if len(raw) > 9:
            resultado = raw[:3] + '.' + raw[3:6] + '.' + raw[6:9] + '-' + raw[9:]
        elif len(raw) > 6:
            resultado = raw[:3] + '.' + raw[3:6] + '.' + raw[6:]
        elif len(raw) > 3:
            resultado = raw[:3] + '.' + raw[3:]
        else:
            resultado = raw
        e.control.value = resultado
        e.control.update()

    def aplicar_mascara_cnh(e):
        valor = ''.join(c for c in e.control.value if c.isdigit())[:11]
        e.control.value = valor
        e.control.update()

    def aplicar_max_chars(e, max_c):
        if len(e.control.value) > max_c:
            e.control.value = e.control.value[:max_c]
            e.control.update()

    # ==================== CAMPOS DO FORMULARIO ==================== #

    numero_crr = ft.TextField(
        label="Numero CRR", value=proximo, read_only=True,
        prefix_icon=ft.Icons.TAG, border_radius=8,
    )

    # Carrega proximo numero do servidor
    def carregar_proximo_numero():
        try:
            resultado = api_client.obter_proximo_numero()
            if resultado.get('sucesso'):
                numero_crr.value = resultado['proximo_numero']
            else:
                numero_crr.value = "SEM LOTE"
            page.update()
        except Exception:
            numero_crr.value = "ERRO"
            page.update()

    carregar_proximo_numero()

    # Pagina 1: Veiculo
    veiculo_sem_id = ft.Checkbox(label="Veiculo s/ identificacao", value=False)
    placa = ft.TextField(
        label="Placa *", prefix_icon=ft.Icons.DIRECTIONS_CAR,
        border_radius=8, capitalization=ft.TextCapitalization.CHARACTERS,
        keyboard_type=ft.KeyboardType.VISIBLE_PASSWORD,
        max_length=8, on_change=aplicar_mascara_placa,
    )
    marca = ft.TextField(label="Marca *", border_radius=8, max_length=20, capitalization=ft.TextCapitalization.CHARACTERS, on_change=forcar_maiusculo)
    modelo = ft.TextField(label="Modelo *", border_radius=8, max_length=20, capitalization=ft.TextCapitalization.CHARACTERS, on_change=forcar_maiusculo)
    cor = ft.TextField(label="Cor *", border_radius=8, max_length=20, capitalization=ft.TextCapitalization.CHARACTERS, on_change=forcar_maiusculo)
    chassi = ft.TextField(
        label="Chassi", border_radius=8, max_length=20,
        on_change=aplicar_mascara_chassi,
        capitalization=ft.TextCapitalization.CHARACTERS,
    )

    def on_veiculo_sem_id_change(e):
        sem_id = veiculo_sem_id.value
        placa.label = "Placa" if sem_id else "Placa *"
        marca.label = "Marca" if sem_id else "Marca *"
        modelo.label = "Modelo" if sem_id else "Modelo *"
        cor.label = "Cor" if sem_id else "Cor *"
        page.update()

    veiculo_sem_id.on_change = on_veiculo_sem_id_change

    # Pagina 2: Fiscalizacao
    local_fiscalizacao = ft.TextField(
        label="Local da Fiscalizacao *", prefix_icon=ft.Icons.LOCATION_ON, border_radius=8,
        capitalization=ft.TextCapitalization.CHARACTERS, on_change=forcar_maiusculo,
    )
    data_fiscalizacao = ft.TextField(
        label="Data *", value=datetime.now().strftime("%d/%m/%Y"),
        prefix_icon=ft.Icons.CALENDAR_TODAY, border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=aplicar_mascara_data,
    )
    hora_fiscalizacao = ft.TextField(
        label="Hora *", value=datetime.now().strftime("%H:%M"),
        prefix_icon=ft.Icons.ACCESS_TIME, border_radius=8,
    )
    medida_administrativa = ft.TextField(
        label="Medida Administrativa",
        value="Remocao do veiculo ao Deposito",
        read_only=True, border_radius=8, bgcolor=ft.Colors.GREY_100,
    )

    # Pagina 3: AITs e Enquadramentos
    MAX_CAMPOS = 4

    def criar_campo_ait(numero):
        prefixo = ft.Dropdown(
            label="Prefixo",
            value="A43",
            options=[
                ft.dropdown.Option("A43"),
                ft.dropdown.Option("Q43"),
            ],
            border_radius=8,
        )
        campo_num = ft.TextField(
            label=f"Auto de Infração {numero}", hint_text="0123456",
            border_radius=8, max_length=7,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: setattr(e.control, 'value', ''.join(c for c in e.control.value if c.isdigit())[:7]) or e.control.update(),
        )
        row = ft.Row(
            [ft.Container(content=prefixo, expand=1), ft.Container(content=campo_num, expand=2)],
            spacing=8, alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        row.prefixo = prefixo
        row.campo_num = campo_num
        return row

    def criar_campo_enquadramento(numero):
        return ft.TextField(
            label=f"Enquadramento {numero}", hint_text="5 digitos",
            border_radius=8, max_length=5, on_change=aplicar_mascara_enquadramento,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

    ait_rows = [criar_campo_ait(1)]
    ait_container = ft.Column(controls=[ait_rows[0]], spacing=8)

    def adicionar_ait(e):
        if len(ait_rows) < MAX_CAMPOS:
            novo = criar_campo_ait(len(ait_rows) + 1)
            ait_rows.append(novo)
            ait_container.controls.append(novo)
            if len(ait_rows) >= MAX_CAMPOS:
                btn_add_ait.visible = False
            page.update()

    btn_add_ait = ft.TextButton("Adicionar AIT", icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=adicionar_ait)

    enq_fields = [criar_campo_enquadramento(1)]
    enq_container = ft.Column(controls=[enq_fields[0]], spacing=8)

    def adicionar_enquadramento(e):
        if len(enq_fields) < MAX_CAMPOS:
            novo = criar_campo_enquadramento(len(enq_fields) + 1)
            enq_fields.append(novo)
            enq_container.controls.append(novo)
            if len(enq_fields) >= MAX_CAMPOS:
                btn_add_enq.visible = False
            page.update()

    btn_add_enq = ft.TextButton("Adicionar Enquadramento", icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=adicionar_enquadramento)

    # Checkbox veiculo abandonado
    veiculo_abandonado = ft.Checkbox(label="Veiculo Abandonado", value=False)

    def on_veiculo_abandonado_change(e):
        abandonado = veiculo_abandonado.value
        if abandonado:
            # Desabilitar e limpar campos de AIT
            for row in ait_rows:
                row.campo_num.value = ''
                row.campo_num.disabled = True
                row.prefixo.disabled = True
            btn_add_ait.visible = False
            # Preencher enquadramento com '00000' e desabilitar adicao
            if enq_fields:
                enq_fields[0].value = '00000'
                enq_fields[0].disabled = True
            # Remover campos extras de enquadramento
            while len(enq_fields) > 1:
                enq_fields.pop()
                enq_container.controls.pop()
            btn_add_enq.visible = False
        else:
            # Reabilitar campos de AIT
            for row in ait_rows:
                row.campo_num.disabled = False
                row.prefixo.disabled = False
            btn_add_ait.visible = len(ait_rows) < MAX_CAMPOS
            # Limpar enquadramento e reabilitar
            if enq_fields:
                enq_fields[0].value = ''
                enq_fields[0].disabled = False
            btn_add_enq.visible = True
        page.update()

    veiculo_abandonado.on_change = on_veiculo_abandonado_change

    # Pagina 4: Outros Dados
    _AV_ODISSEU = "AV ODISSEU 750 - CANTO DO MAR - SAO SEBASTIAO/SP"
    _R_BOLIVIA = "R. BOLIVIA 202 - JARAGUA - SAO SEBASTIAO/SP"
    local_patio_opcao = ft.Dropdown(
        label="Local do Patio", value=_AV_ODISSEU,
        options=[
            ft.dropdown.Option(_AV_ODISSEU),
            ft.dropdown.Option(_R_BOLIVIA),
        ],
        border_radius=8,
    )

    placa_guincho = ft.TextField(
        label="Placa do Guincho", border_radius=8, max_length=8,
        keyboard_type=ft.KeyboardType.VISIBLE_PASSWORD,
        on_change=aplicar_mascara_placa, capitalization=ft.TextCapitalization.CHARACTERS,
    )
    encarregado = ft.TextField(label="Encarregado", border_radius=8, max_length=50, capitalization=ft.TextCapitalization.CHARACTERS, on_change=forcar_maiusculo)
    matricula_agente = ft.TextField(
        label="Matricula do Agente", value=matricula_usuario,
        read_only=True, border_radius=8, bgcolor=ft.Colors.GREY_100,
    )
    observacao = ft.TextField(
        label="Observacao", multiline=True, min_lines=2, max_lines=4, border_radius=8,
        max_length=300,
        capitalization=ft.TextCapitalization.CHARACTERS, on_change=forcar_maiusculo,
    )

    # Pagina 5: Condutor
    condutor_ausente = ft.Checkbox(label="Condutor ausente", value=False)
    nome_condutor = ft.TextField(label="Nome do Condutor *", prefix_icon=ft.Icons.PERSON, border_radius=8, capitalization=ft.TextCapitalization.CHARACTERS, on_change=forcar_maiusculo)
    cpf_condutor = ft.TextField(
        label="CPF *", prefix_icon=ft.Icons.BADGE, border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER, max_length=14,
        on_change=aplicar_mascara_cpf,
    )
    cnh = ft.TextField(
        label="CNH", border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER, max_length=11,
        on_change=aplicar_mascara_cnh,
    )
    cnh_estrangeira = ft.TextField(
        label="CNH Estrangeira", border_radius=8, max_length=11,
        capitalization=ft.TextCapitalization.CHARACTERS, on_change=forcar_maiusculo,
    )

    situacao_entrega = ft.RadioGroup(
        value=None,
        content=ft.Column([
            ft.Radio(value="Assinou e recebeu 2a via",
                     label="Assinou e recebeu 2ª via"),
            ft.Radio(value="Recusou assinar e recebeu 2a via",
                     label="Recusou assinar e recebeu 2ª via"),
            ft.Radio(value="Recusou assinar e a receber 2a via",
                     label="Recusou assinar e a receber 2ª via"),
        ], spacing=2),
    )
    situacao_entrega_section = ft.Column([
        ft.Text("Situacao de Entrega *", size=13, weight=ft.FontWeight.W_500,
                color=ft.Colors.TEAL_700),
        situacao_entrega,
    ], visible=True, spacing=4)

    def on_condutor_ausente_change(e):
        ausente = condutor_ausente.value
        nome_condutor.label = "Nome do Condutor" if ausente else "Nome do Condutor *"
        cpf_condutor.label = "CPF" if ausente else "CPF *"
        situacao_entrega_section.visible = not ausente
        if ausente:
            situacao_entrega.value = None
        page.update()

    condutor_ausente.on_change = on_condutor_ausente_change

    # ==================== PAGINAS DO CARROSSEL ==================== #

    def criar_pagina_veiculo():
        return ft.Container(
            content=ft.Column(controls=[
                ft.Icon(ft.Icons.DIRECTIONS_CAR, size=40, color=ft.Colors.BLUE),
                ft.Text("Dados do Veiculo", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                veiculo_sem_id, ft.Divider(), placa, chassi,
                ft.Row([ft.Container(content=marca, expand=1), ft.Container(content=modelo, expand=1)], spacing=10),
                cor,
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            padding=20, expand=True,
        )

    def criar_pagina_fiscalizacao():
        return ft.Container(
            content=ft.Column(controls=[
                ft.Icon(ft.Icons.LOCATION_ON, size=40, color=ft.Colors.GREEN),
                ft.Text("Dados da Fiscalizacao", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                local_fiscalizacao,
                ft.Row([ft.Container(content=data_fiscalizacao, expand=1), ft.Container(content=hora_fiscalizacao, expand=1)], spacing=10),
                medida_administrativa,
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=20, expand=True,
        )

    def criar_pagina_aits_enquadramentos():
        return ft.Container(
            content=ft.Column(controls=[
                ft.Icon(ft.Icons.DESCRIPTION, size=40, color=ft.Colors.ORANGE),
                ft.Text("AITs e Enquadramentos", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                veiculo_abandonado,
                ft.Divider(),
                ft.Text("AITs:", size=14, weight=ft.FontWeight.W_500),
                ait_container, btn_add_ait, ft.Divider(),
                ft.Text("Enquadramentos:", size=14, weight=ft.FontWeight.W_500),
                enq_container, btn_add_enq,
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            padding=20, expand=True,
        )

    def criar_pagina_outros_dados():
        return ft.Container(
            content=ft.Column(controls=[
                ft.Icon(ft.Icons.MORE_HORIZ, size=40, color=ft.Colors.PURPLE),
                ft.Text("Outros Dados", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                local_patio_opcao, placa_guincho,
                encarregado, matricula_agente, observacao,
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=20, expand=True,
        )

    def criar_pagina_condutor():
        return ft.Container(
            content=ft.Column(controls=[
                ft.Icon(ft.Icons.PERSON, size=40, color=ft.Colors.TEAL),
                ft.Text("Dados do Condutor", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                condutor_ausente, ft.Divider(),
                nome_condutor, cpf_condutor, cnh, cnh_estrangeira,
                ft.Divider(),
                situacao_entrega_section,
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=20, expand=True,
        )

    # Pagina 6: Imagens
    MAX_IMAGENS = 4
    imagens_capturadas = []  # lista de dicts {path, base64}

    imagens_grid = ft.Column(controls=[], spacing=10)
    imagens_contador = ft.Text("0 / 4 imagens", size=13, color=ft.Colors.GREY_600)

    def atualizar_grid_imagens():
        novos_cards = []
        for i, img_data in enumerate(imagens_capturadas):
            def remover_img(e, idx=i):
                imagens_capturadas.pop(idx)
                atualizar_grid_imagens()

            card = ft.Container(
                content=ft.Row([
                    ft.Image(
                        src=img_data['base64'],
                        width=72, height=72,
                        border_radius=6,
                    ),
                    ft.Text(f"Foto {i + 1}", size=13, expand=True, color=ft.Colors.GREY_800),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_400,
                        icon_size=22,
                        tooltip="Remover foto",
                        on_click=remover_img,
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=8, border_radius=10, bgcolor=ft.Colors.WHITE,
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=4, color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK)),
            )
            novos_cards.append(card)
        # Reatribuição dispara o rastreamento de mudanças do Flet
        imagens_grid.controls = novos_cards
        qtd = len(imagens_capturadas)
        imagens_contador.value = f"{qtd} / {MAX_IMAGENS} imagens"
        btn_camera.visible = qtd < MAX_IMAGENS
        btn_galeria.visible = qtd < MAX_IMAGENS
        page.update()

    img_picker = ImagePickerService()
    page.services.append(img_picker)

    async def abrir_camera(e):
        if len(imagens_capturadas) >= MAX_IMAGENS:
            return
        try:
            resultado = await img_picker.pick_image_camera(image_quality=85)
            if resultado:
                imagens_capturadas.append({'path': resultado.name, 'base64': resultado.base64})
                atualizar_grid_imagens()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro camera: {ex}"),
                bgcolor=ft.Colors.RED,
            )
            page.snack_bar.open = True
            page.update()

    async def abrir_galeria(e):
        if len(imagens_capturadas) >= MAX_IMAGENS:
            return
        try:
            resultado = await img_picker.pick_image_gallery(image_quality=85)
            if resultado:
                imagens_capturadas.append({'path': resultado.name, 'base64': resultado.base64})
                atualizar_grid_imagens()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro galeria: {ex}"),
                bgcolor=ft.Colors.RED,
            )
            page.snack_bar.open = True
            page.update()

    btn_camera = ft.ElevatedButton(
        "Camera",
        icon=ft.Icons.CAMERA_ALT,
        on_click=abrir_camera,
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
    )
    btn_galeria = ft.ElevatedButton(
        "Galeria",
        icon=ft.Icons.PHOTO_LIBRARY,
        on_click=abrir_galeria,
        style=ft.ButtonStyle(bgcolor=ft.Colors.TEAL, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
    )

    def criar_pagina_imagens():
        return ft.Container(
            content=ft.Column(controls=[
                ft.Icon(ft.Icons.CAMERA_ALT, size=40, color=ft.Colors.DEEP_ORANGE),
                ft.Text("Imagens", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Capture ate 4 fotos (opcional)", size=12, color=ft.Colors.GREY_600),
                ft.Container(height=5),
                imagens_contador,
                ft.Container(height=10),
                ft.Row([btn_camera, btn_galeria], spacing=10),
                ft.Container(height=10),
                imagens_grid,
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            padding=20, expand=True,
        )

    revisao_content = ft.Column(controls=[], spacing=5, scroll=ft.ScrollMode.AUTO)

    def criar_pagina_revisao():
        return ft.Container(
            content=ft.Column(controls=[
                ft.Icon(ft.Icons.CHECKLIST, size=40, color=ft.Colors.INDIGO),
                ft.Text("Revisao dos Dados", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Confira os dados antes de salvar", size=12, color=ft.Colors.GREY_600),
                ft.Container(height=10),
                revisao_content,
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            padding=20, expand=True,
        )

    def atualizar_revisao():
        aits = []
        for row in ait_rows:
            num = row.campo_num.value
            if num and num.strip():
                prefixo = row.prefixo.value or "A43"
                aits.append(f"{prefixo}-{num.strip()}")
        enquadramentos = [f.value for f in enq_fields if f.value and f.value.strip()]
        local_patio_valor = local_patio_opcao.value

        def item(label, valor):
            return ft.Row([
                ft.Text(f"{label}:", weight=ft.FontWeight.BOLD, size=12, width=120),
                ft.Text(str(valor or "-"), size=12, expand=True),
            ])

        revisao_content.controls = [
            ft.Container(content=ft.Column([
                ft.Text("VEICULO", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                item("Placa", placa.value), item("Marca", marca.value),
                item("Modelo", modelo.value), item("Cor", cor.value), item("Chassi", chassi.value),
            ], spacing=3), bgcolor=ft.Colors.BLUE_50, padding=10, border_radius=8),
            ft.Container(content=ft.Column([
                ft.Text("FISCALIZACAO", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                item("Local", local_fiscalizacao.value), item("Data", data_fiscalizacao.value),
                item("Hora", hora_fiscalizacao.value), item("Medida", medida_administrativa.value),
            ], spacing=3), bgcolor=ft.Colors.GREEN_50, padding=10, border_radius=8),
            ft.Container(content=ft.Column([
                ft.Text("AITs E ENQUADRAMENTOS", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                item("AITs", ", ".join(aits) if aits else "-"),
                item("Enquadr.", ", ".join(enquadramentos) if enquadramentos else "-"),
            ], spacing=3), bgcolor=ft.Colors.ORANGE_50, padding=10, border_radius=8),
            ft.Container(content=ft.Column([
                ft.Text("OUTROS DADOS", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE),
                item("Patio", local_patio_valor), item("Guincho", placa_guincho.value),
                item("Encarregado", encarregado.value), item("Matricula", matricula_agente.value),
                item("Obs", observacao.value),
            ], spacing=3), bgcolor=ft.Colors.PURPLE_50, padding=10, border_radius=8),
            ft.Container(content=ft.Column([
                ft.Text("CONDUTOR", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.TEAL),
                item("Nome", nome_condutor.value), item("CPF", cpf_condutor.value),
                item("CNH", cnh.value), item("CNH Estrang.", cnh_estrangeira.value),
            ], spacing=3), bgcolor=ft.Colors.TEAL_50, padding=10, border_radius=8),
            ft.Container(content=ft.Column([
                ft.Text("IMAGENS", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.DEEP_ORANGE),
                item("Fotos", f"{len(imagens_capturadas)} capturada(s)"),
            ], spacing=3), bgcolor=ft.Colors.ORANGE_50, padding=10, border_radius=8),
        ]
        page.update()

    paginas = [
        criar_pagina_veiculo(), criar_pagina_fiscalizacao(),
        criar_pagina_aits_enquadramentos(), criar_pagina_outros_dados(),
        criar_pagina_condutor(), criar_pagina_imagens(), criar_pagina_revisao(),
    ]

    conteudo_carrossel = ft.Container(content=paginas[0], expand=True)

    def criar_indicadores():
        return ft.Row(
            controls=[
                ft.Container(width=10, height=10, border_radius=5,
                             bgcolor=ft.Colors.BLUE if i == pagina_atual else ft.Colors.GREY_300)
                for i in range(total_paginas)
            ],
            alignment=ft.MainAxisAlignment.CENTER, spacing=8,
        )

    indicadores = criar_indicadores()
    titulo_secao = ft.Text(titulos_secoes[0], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    contador_pagina = ft.Text(f"1 / {total_paginas}", size=14, color=ft.Colors.WHITE70)
    status_text = ft.Text("", size=14)
    loading = ft.ProgressRing(visible=False, width=20, height=20)

    # ==================== NAVEGACAO ==================== #

    def atualizar_pagina():
        nonlocal indicadores
        if pagina_atual == total_paginas - 1:
            atualizar_revisao()
        conteudo_carrossel.content = paginas[pagina_atual]
        titulo_secao.value = titulos_secoes[pagina_atual]
        contador_pagina.value = f"{pagina_atual + 1} / {total_paginas}"
        for i, indicator in enumerate(indicadores.controls):
            indicator.bgcolor = ft.Colors.BLUE if i == pagina_atual else ft.Colors.GREY_300
        btn_anterior.visible = pagina_atual > 0
        btn_proximo.visible = pagina_atual < total_paginas - 1
        btn_salvar.visible = pagina_atual == total_paginas - 1
        page.update()

    def pagina_anterior(e):
        nonlocal pagina_atual
        if pagina_atual > 0:
            pagina_atual -= 1
            atualizar_pagina()

    def proxima_pagina(e):
        nonlocal pagina_atual
        if pagina_atual < total_paginas - 1:
            pagina_atual += 1
            atualizar_pagina()

    # ==================== VALIDACAO E SALVAMENTO ==================== #

    def validar_campos():
        erros = []
        if numero_crr.value in ("SEM LOTE", "ERRO", "Carregando..."):
            erros.append("Sem numero CRR disponivel")
        if not veiculo_sem_id.value:
            if not placa.value:
                erros.append("Placa e obrigatoria")
            if not marca.value:
                erros.append("Marca e obrigatoria")
            if not modelo.value or not modelo.value.strip():
                erros.append("Modelo e obrigatorio")
            if not cor.value or not cor.value.strip():
                erros.append("Cor e obrigatoria")
        if not local_fiscalizacao.value or not local_fiscalizacao.value.strip():
            erros.append("Local da fiscalizacao e obrigatorio")
        if not matricula_agente.value or not matricula_agente.value.strip():
            erros.append("Matricula do agente e obrigatoria")
        if not data_fiscalizacao.value:
            erros.append("Data e obrigatoria")
        if not hora_fiscalizacao.value:
            erros.append("Hora e obrigatoria")
        if not veiculo_abandonado.value:
            aits_preenchidos = any(
                row.campo_num.value and row.campo_num.value.strip()
                for row in ait_rows
            )
            if not aits_preenchidos:
                erros.append("Preencha pelo menos um AIT (ou marque Veiculo Abandonado)")
        if not condutor_ausente.value:
            if not nome_condutor.value or not nome_condutor.value.strip():
                erros.append("Nome do condutor e obrigatorio")
            if not cpf_condutor.value or not cpf_condutor.value.strip():
                erros.append("CPF do condutor e obrigatorio")
            if not situacao_entrega.value:
                erros.append("Situacao de entrega e obrigatoria")
        if erros:
            status_text.value = "\n".join(erros)
            status_text.color = ft.Colors.RED
            page.update()
            return False
        return True

    def obter_dados_formulario():
        aits = []
        for row in ait_rows:
            num = row.campo_num.value
            if num and num.strip():
                prefixo = row.prefixo.value or "A43"
                aits.append(f"{prefixo}-{num.strip()}")
        enquadramentos = [f.value.strip() for f in enq_fields if f.value and f.value.strip()]
        local_patio_valor = local_patio_opcao.value

        # Converte DD/MM/AAAA -> AAAA-MM-DD para a API
        data_raw = data_fiscalizacao.value or ''
        try:
            data_iso = datetime.strptime(data_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            data_iso = data_raw

        return {
            'numeroCrr': numero_crr.value,
            'placa': (placa.value or '').replace('-', ''), 'chassi': chassi.value or '',
            'marca': marca.value or '', 'modelo': modelo.value or '', 'cor': cor.value or '',
            'veiculoSemIdentificacao': veiculo_sem_id.value,
            'nomeCondutor': nome_condutor.value or '', 'cpfCondutor': cpf_condutor.value or '',
            'cnh': cnh.value or '', 'cnhEstrangeira': cnh_estrangeira.value or '',
            'localFiscalizacao': local_fiscalizacao.value or '',
            'dataFiscalizacao': data_iso,
            'horaFiscalizacao': hora_fiscalizacao.value or '',
            'medidaAdministrativa': medida_administrativa.value or '',
            'localPatio': local_patio_valor,
            'placaGuincho': (placa_guincho.value or '').replace('-', ''),
            'encarregado': encarregado.value or '',
            'matriculaAgente': matricula_agente.value or '',
            'observacao': observacao.value or '',
            'aits': aits, 'enquadramentos': enquadramentos,
            'veiculoAbandonado': veiculo_abandonado.value,
            'imagens': [img['base64'] for img in imagens_capturadas],
            'situacaoEntrega': 'Condutor ausente' if condutor_ausente.value else (situacao_entrega.value or ''),
            'assinaturaCondutor': '',
        }

    dados_salvo = {}

    def fechar_dialogo_salvo(ev):
        if page.overlay:
            page.overlay[-1].open = False
        page.update()
        on_salvar(dados_salvo, True)

    def imprimir_crr_click(ev):
        if page.overlay:
            page.overlay[-1].open = False
        page.update()

        lines = gerar_linhas_impressao(dados_salvo)
        sig_b64 = local_db.obter_config('assinatura_base64') or ''
        condutor_sig = dados_salvo.get('assinaturaCondutor', '')

        async def _imprimir():
            if print_service:
                try:
                    await print_service.print_receipt(
                        lines=lines,
                        signature_base64=sig_b64,
                        condutor_signature_base64=condutor_sig,
                    )
                except Exception:
                    pass
            on_salvar(dados_salvo, True)

        page.run_task(_imprimir)

    def mostrar_dialogo_pos_salvar(dados):
        nonlocal dados_salvo
        dados_salvo = dados
        numero = dados.get('numeroCrr', '')

        acoes = [
            ft.ElevatedButton(
                "Imprimir", icon=ft.Icons.PRINT, on_click=imprimir_crr_click,
                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
            ),
            ft.TextButton("Fechar", on_click=fechar_dialogo_salvo),
        ]

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=30),
                ft.Text(f"CRR {numero}", size=16, weight=ft.FontWeight.BOLD),
            ]),
            content=ft.Column([
                ft.Text("CRR salvo com sucesso!", size=14),
                ft.Container(height=10),
            ], tight=True),
            actions=acoes,
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def salvar_crr(e):
        if not validar_campos():
            return
        loading.visible = True
        status_text.value = "Salvando..."
        status_text.color = ft.Colors.BLUE
        page.update()

        dados = obter_dados_formulario()

        try:
            resultado = api_client.criar_crr(dados)
            if resultado.get('sucesso'):
                status_text.value = f"CRR {dados['numeroCrr']} salvo!"
                status_text.color = ft.Colors.GREEN
                loading.visible = False
                page.update()
                mostrar_dialogo_pos_salvar(dados)
            else:
                erro = resultado.get('erros', resultado.get('erro', 'Erro ao salvar'))
                status_text.value = str(erro)
                status_text.color = ft.Colors.RED
                loading.visible = False
                page.update()
        except Exception:
            status_text.value = "Sem conexao com o servidor"
            status_text.color = ft.Colors.RED
            loading.visible = False
            page.update()

    # ==================== BOTOES DE NAVEGACAO ==================== #

    btn_anterior = ft.ElevatedButton(
        "Anterior", icon=ft.Icons.ARROW_BACK, on_click=pagina_anterior,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)), visible=False,
    )
    btn_proximo = ft.ElevatedButton(
        "Proximo", icon=ft.Icons.ARROW_FORWARD, on_click=proxima_pagina,
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10)),
    )
    btn_salvar = ft.ElevatedButton(
        "Salvar CRR", icon=ft.Icons.SAVE, on_click=salvar_crr,
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10)),
        visible=False,
    )

    return ft.Container(
        content=ft.Column(controls=[
            ft.Container(
                content=ft.Column(controls=[
                    ft.Row(controls=[
                        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, on_click=on_voltar),
                        ft.Column(controls=[
                            ft.Text(f"Novo CRR", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            titulo_secao,
                        ], spacing=2, expand=True),
                        contador_pagina,
                    ]),
                    ft.Container(height=10),
                    indicadores,
                ]),
                bgcolor=ft.Colors.BLUE,
                padding=ft.padding.only(top=35, bottom=15, left=15, right=15),
            ),
            conteudo_carrossel,
            ft.Container(
                content=ft.Row(controls=[loading, status_text], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=20),
            ),
            ft.Container(
                content=ft.Row(controls=[btn_anterior, ft.Container(expand=True), btn_proximo, btn_salvar],
                               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=20,
            ),
        ], spacing=0),
        expand=True,
    )
