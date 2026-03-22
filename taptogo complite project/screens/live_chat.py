"""
screens/live_chat.py — Live Bus Chat feature.
Simple chat UI with dummy messages. No backend.
"""
import flet as ft

# ===== LIVE CHAT COMPONENT START =====

_BG = "#0B1020"
_CARD = "#1A2236"
_GRAD_A = "#3B82F6"
_GRAD_B = "#7C3AED"
_WHITE = "#FFFFFF"
_MUTED = "#8B9AB0"


def build_live_chat(page, uid, trip=None):
    """Build Live Chat page. trip can provide bus info."""
    bus_no = "C-42"
    if trip and trip.get("bus"):
        bus_no = str(trip["bus"].get("bus_no", bus_no))

    messages_ref = ft.Ref[ft.Column]()
    input_ref = ft.Ref[ft.TextField]()

    # Static dummy messages
    dummy_messages = [
        ("Rahul", "Is the bus on time today?"),
        ("Priya", "Yes, just left Thane Station"),
        ("Amit", "Heavy traffic near Ghatkopar"),
    ]

    def send_message(_):
        tf = input_ref.current
        if not tf or not (tf.value or "").strip():
            return
        user = "You"
        msg = (tf.value or "").strip()
        messages_ref.current.controls.append(
            ft.Container(
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                border_radius=12,
                bgcolor=ft.Colors.with_opacity(0.15, _GRAD_A),
                content=ft.Text(f"[{user}]: {msg}", size=13, color=_WHITE),
            ),
        )
        tf.value = ""
        tf.focus()
        page.update()

    message_controls = [
        ft.Container(
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.08, _MUTED),
            content=ft.Text(f"[{name}]: {text}", size=13, color=_WHITE),
        )
        for name, text in dummy_messages
    ]

    input_box = ft.TextField(
        ref=input_ref,
        hint_text="Type a message...",
        border_radius=12,
        filled=True,
        bgcolor=_CARD,
        border_color=ft.Colors.with_opacity(0.15, _WHITE),
        color=_WHITE,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        on_submit=send_message,
    )

    send_btn = ft.Container(
        height=48,
        padding=ft.padding.symmetric(horizontal=20),
        border_radius=12,
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(-1, 0),
            end=ft.alignment.Alignment(1, 0),
            colors=[_GRAD_A, _GRAD_B],
        ),
        alignment=ft.alignment.Alignment(0, 0),
        content=ft.Text("Send", size=14, weight=ft.FontWeight.W_600, color=_WHITE),
        on_click=send_message,
    )

    insight_card = ft.Container(
        padding=16,
        border_radius=12,
        bgcolor=_CARD,
        border=ft.border.all(1, ft.Colors.with_opacity(0.08, _WHITE)),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.LIGHTBULB_OUTLINE_ROUNDED, size=18, color=_GRAD_B),
                        ft.Text("Today's Insight", size=14, weight=ft.FontWeight.W_700, color=_WHITE),
                    ],
                ),
                ft.Text(
                    "• Heavy traffic near Ghatkopar due to roadwork\n"
                    "• Bus delays expected near Sion Circle\n"
                    "• Rain may slow down travel today",
                    size=12,
                    color=_MUTED,
                ),
            ],
        ),
    )

    return ft.Container(
        expand=True,
        bgcolor=_BG,
        padding=ft.padding.symmetric(horizontal=18, vertical=20),
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=18,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text("Live Bus Chat", size=24, weight=ft.FontWeight.W_800, color=_WHITE),
                        ft.Text(
                            "Passengers in your bus can communicate here",
                            size=13,
                            color=_MUTED,
                        ),
                    ],
                ),
                ft.Container(
                    padding=14,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.12, _GRAD_A),
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.DIRECTIONS_BUS_ROUNDED, color=_GRAD_A, size=20),
                            ft.Text(f"You are currently in Bus {bus_no}", size=14, weight=ft.FontWeight.W_600, color=_WHITE),
                        ],
                    ),
                ),
                ft.Container(
                    padding=14,
                    border_radius=12,
                    bgcolor=_CARD,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.08, _WHITE)),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.BAR_CHART_ROUNDED, size=18, color=_GRAD_A),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Bus Status", size=12, weight=ft.FontWeight.W_600, color=_WHITE),
                                    ft.Text("On time • Next stop: Ghatkopar", size=11, color=_MUTED),
                                ],
                            ),
                        ],
                    ),
                ),
                insight_card,
                ft.Text("Messages", size=13, weight=ft.FontWeight.W_600, color=_MUTED),
                ft.Container(
                    expand=True,
                    border_radius=12,
                    bgcolor=ft.Colors.with_opacity(0.05, _WHITE),
                    padding=12,
                    content=ft.Column(
                        ref=messages_ref,
                        spacing=10,
                        scroll=ft.ScrollMode.AUTO,
                        controls=message_controls,
                    ),
                ),
                ft.Row(
                    spacing=10,
                    alignment=ft.MainAxisAlignment.START,
                    controls=[
                        ft.Container(expand=True, content=input_box),
                        send_btn,
                    ],
                ),
            ],
        ),
    )


# ===== LIVE CHAT COMPONENT END =====
