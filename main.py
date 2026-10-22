import flet as ft
from plyer import tts
import db_manager

def play_tts(word):
    try:
        tts.speak(word)
    except Exception as e:
        print(f"TTS Error: {e}")

# Ensure DB is initialized
db_manager.init_db()

def main(page: ft.Page):
    page.title = "Minimalist Word Machine"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.Colors.BLACK
    # Simulate a phone-like aspect ratio if run on desktop
    page.window.width = 400
    page.window.height = 750

    def nav_to(route):
        page.route = route
        route_change(None)

    def route_change(e):
        page.views.clear()

        # ---------- 1. HOME VIEW ----------
        if True: # Always show home view underneath to prevent black screen
            start_index_field = ft.TextField(
                label="Start from index", 
                width=200, 
                keyboard_type=ft.KeyboardType.NUMBER,
                border_color=ft.Colors.GREY_800
            )
            page.views.append(
                ft.View(
                    "/",
                    [
                        ft.AppBar(title=ft.Text("Home", weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLACK),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.ElevatedButton(
                                        "Resume Learning",
                                        on_click=lambda _: nav_to("/study"),
                                        width=300,
                                        height=100,
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder(radius=15),
                                            bgcolor=ft.Colors.BLUE_700,
                                            color=ft.Colors.WHITE,
                                        ),
                                    ),
                                    ft.Row(
                                        [
                                            start_index_field,
                                            ft.IconButton(
                                                icon=ft.Icons.PLAY_ARROW,
                                                icon_size=35,
                                                icon_color=ft.Colors.WHITE,
                                                on_click=lambda _: print(f"Start from index: {start_index_field.value}")
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER
                                    ),
                                    ft.ElevatedButton(
                                        "Select Dictionary",
                                        on_click=lambda _: nav_to("/dict_select"),
                                        width=300,
                                        height=55,
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREY_900,
                                            color=ft.Colors.WHITE,
                                        ),
                                    ),
                                    ft.ElevatedButton(
                                        "Settings",
                                        on_click=lambda _: nav_to("/settings"),
                                        width=300,
                                        height=55,
                                        style=ft.ButtonStyle(
                                            bgcolor=ft.Colors.GREY_900,
                                            color=ft.Colors.WHITE,
                                        ),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=25,
                            ),
                            alignment=ft.Alignment.CENTER,
                            expand=True,
                        )
                    ],
                    bgcolor=ft.Colors.BLACK,
                    padding=0,
                )
            )

        # ---------- 2. STUDY VIEW ----------
        if page.route == "/study":
            active_dicts = db_manager.get_active_dictionaries()
            active_dict_ids = [d['id'] for d in active_dicts]
            current_word = db_manager.get_next_new_word(active_dict_ids)
            
            def next_word(is_correct):
                if current_word:
                    db_manager.add_to_review(current_word["id"], is_correct)
                    if not is_correct:
                        db_manager.add_to_mistakes(current_word["id"])
                    # Advance progress
                    db_manager.update_progress(current_word["dict_id"], current_word["current_index"] + 1)
                
                # Fetch next word and rebuild view
                nav_to("/study")

            if not current_word:
                page.views.append(
                    ft.View(
                        "/study",
                        [
                            ft.AppBar(title=ft.Text("Study", weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLACK),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text("No more words available.", size=24, color=ft.Colors.WHITE),
                                        ft.Text("Have you selected a dictionary?", size=16, color=ft.Colors.GREY_500),
                                        ft.ElevatedButton("Go Back", on_click=lambda _: nav_to("/"), color=ft.Colors.BLACK, bgcolor=ft.Colors.WHITE)
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=20
                                ),
                                alignment=ft.Alignment.CENTER,
                                expand=True
                            )
                        ],
                        bgcolor=ft.Colors.BLACK
                    )
                )
            else:
                page.views.append(
                ft.View(
                    "/study",
                    [
                        ft.AppBar(title=ft.Text("Study", weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLACK),
                        ft.Container(
                            content=ft.Column(
                                [
                                    # Top: Word and IPA
                                    ft.Container(
                                        content=ft.Column(
                                            [
                                                ft.Text(current_word["word"], size=50, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                                ft.Row(
                                                    [
                                                        ft.Text(current_word["ipa"], size=22, color=ft.Colors.GREY_500),
                                                        ft.IconButton(
                                                            icon=ft.Icons.VOLUME_UP, 
                                                            icon_color=ft.Colors.BLUE_400,
                                                            on_click=lambda _: play_tts(current_word["word"])
                                                        )
                                                    ],
                                                    alignment=ft.MainAxisAlignment.CENTER
                                                )
                                            ],
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                        padding=ft.Padding.only(top=40, bottom=20),
                                    ),
                                    
                                    # Middle: Meaning & Sentences
                                    ft.Container(
                                        content=ft.Column(
                                            [
                                                ft.Text("Meaning", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200, size=16),
                                                ft.Text(current_word["meaning"], size=20, color=ft.Colors.WHITE70),
                                                ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                                                ft.Text("Example", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_200, size=16),
                                                ft.Text(current_word["sentences"][0], size=18, italic=True, color=ft.Colors.WHITE70),
                                            ],
                                            horizontal_alignment=ft.CrossAxisAlignment.START,
                                        ),
                                        padding=ft.Padding.symmetric(horizontal=30),
                                        expand=True, # Pushes bottom controls down
                                    ),
                                    
                                    # Bottom: Single-hand friendly buttons
                                    ft.Container(
                                        content=ft.Row(
                                            [
                                                ft.ElevatedButton(
                                                    "Don't Know",
                                                    on_click=lambda _: next_word(False),
                                                    expand=True,
                                                    height=80,
                                                    style=ft.ButtonStyle(
                                                        bgcolor=ft.Colors.RED_900,
                                                        color=ft.Colors.WHITE,
                                                        shape=ft.RoundedRectangleBorder(radius=15),
                                                        text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)
                                                    )
                                                ),
                                                ft.ElevatedButton(
                                                    "Know",
                                                    on_click=lambda _: next_word(True),
                                                    expand=True,
                                                    height=80,
                                                    style=ft.ButtonStyle(
                                                        bgcolor=ft.Colors.GREEN_800,
                                                        color=ft.Colors.WHITE,
                                                        shape=ft.RoundedRectangleBorder(radius=15),
                                                        text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)
                                                    )
                                                ),
                                            ],
                                            spacing=15,
                                        ),
                                        padding=ft.Padding.only(bottom=30, left=20, right=20),
                                    )
                                ],
                                expand=True,
                            ),
                            expand=True,
                        )
                    ],
                    bgcolor=ft.Colors.BLACK,
                    padding=0,
                )
            )

        # ---------- 3. DICTIONARY SELECTION VIEW ----------
        if page.route == "/dict_select":
            dicts = db_manager.get_all_dictionaries()
            
            def on_dict_toggle(e, dict_id):
                active_ids = [c.data for c in checkboxes if c.value]
                db_manager.set_active_dictionaries(active_ids)
                
            checkboxes = [
                ft.Checkbox(
                    label=d['name'], 
                    value=d['is_active'] == 1, 
                    data=d['id'],
                    fill_color=ft.Colors.BLUE_700,
                    label_style=ft.TextStyle(size=18),
                    on_change=lambda e, did=d['id']: on_dict_toggle(e, did)
                ) for d in dicts
            ]
            
            page.views.append(
                ft.View(
                    "/dict_select",
                    [
                        ft.AppBar(title=ft.Text("Select Dictionary", weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLACK),
                        ft.Container(
                            content=ft.Column(checkboxes, spacing=15),
                            padding=ft.Padding.all(30),
                            expand=True,
                        )
                    ],
                    bgcolor=ft.Colors.BLACK,
                    padding=0,
                )
            )

        # ---------- 4. SETTINGS VIEW ----------
        if page.route == "/settings":
            page.views.append(
                ft.View(
                    "/settings",
                    [
                        ft.AppBar(title=ft.Text("Settings", weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLACK),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.ElevatedButton(
                                        "Import Dict", 
                                        icon=ft.Icons.DOWNLOAD,
                                        on_click=lambda _: print("Import Dict clicked"), 
                                        width=300, height=60,
                                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_900, color=ft.Colors.WHITE)
                                    ),
                                    ft.ElevatedButton(
                                        "Clean Cache", 
                                        icon=ft.Icons.CLEANING_SERVICES,
                                        on_click=lambda _: db_manager.clear_cache(), 
                                        width=300, height=60,
                                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_900, color=ft.Colors.WHITE)
                                    ),
                                    ft.ElevatedButton(
                                        "Reset All Data", 
                                        icon=ft.Icons.WARNING,
                                        on_click=lambda _: db_manager.reset_all(), 
                                        width=300, height=60, 
                                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE)
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=20,
                            ),
                            alignment=ft.Alignment.CENTER,
                            expand=True,
                        )
                    ],
                    bgcolor=ft.Colors.BLACK,
                    padding=0,
                )
            )

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        nav_to(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Initialize the app on the Home route
    nav_to("/")

if __name__ == "__main__":
    ft.app(main)
