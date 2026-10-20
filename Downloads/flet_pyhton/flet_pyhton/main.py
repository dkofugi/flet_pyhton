from dataclasses import dataclass, field
from typing import Optional

import flet as ft

# =====================================================================
# >>>>>>>>>>>>>>>>>>>>  IMAGENS DAS CARTAS (EDITE AQUI)  <<<<<<<<<<<<<<<<
# =====================================================================

# Uma imagem para cada carta, na ordem: carta 1, carta 2, carta 3, carta 4.
# Troque os nomes pelos arquivos que voce tem na pasta.
# Deixe "" (vazio) para aquela carta ficar so com a caixa colorida e o numero.
IMAGENS = [
    "C:/Users/2601711/Desktop/flet_pyhton/CACHORRINHO.png",  # carta 1
    "C:/Users/2601711/Desktop/flet_pyhton/GATINHO.png",  # carta 2
    "C:/Users/2601711/Desktop/flet_pyhton/PASSARINHO.png",  # carta 3
    "C:/Users/2601711/Desktop/flet_pyhton/COELHINHO.png",  # carta 4
]

# =====================================================================

# Constantes de tamanho
CARD_W = 100 # largura da carta
CARD_H = 130  # altura da carta
OFFSET_Y = 25  # deslocamento vertical entre cartas empilhadas
SNAP = 40  # distancia maxima para "encaixar" num slot
GAP = 38  # espaco entre slots


# ---------- Model (dados) ----------
@ft.observable
@dataclass
class Slot:
    id: str
    left: float = 0
    top: float = 0
    cards: list["Card"] = field(default_factory=list)  # cartas que estao neste slot


@ft.observable
@dataclass
class Card:
    id: str
    label: str
    imagem: str = ""  # <-- NOVO: imagem desta carta
    left: float = 0
    top: float = 0
    home: Optional[Slot] = None  # slot onde a carta esta


@ft.observable
@dataclass
class Board:
    # 3 slots lado a lado
    slots: list[Slot] = field(
        default_factory=lambda: [
            Slot(id="slot1", left=GAP, top=50),
            Slot(id="slot2", left=GAP * 2 + CARD_W, top=50),
            Slot(id="slot3", left=GAP * 3 + CARD_W * 2, top=50),
        ]
    )
    # 4 cartas, cada uma com a sua imagem (carta 1 -> IMAGENS[0], etc.)
    cards: list[Card] = field(
        default_factory=lambda: [
            Card(id=f"c{i}", label=str(i), imagem=IMAGENS[(i - 1) % len(IMAGENS)])
            for i in range(1, 5)
        ]
    )

    def __post_init__(self):
        """Coloca todas as cartas no primeiro slot."""
        for c in self.cards:
            self.place_card_in_slot(c, self.slots[0])

    # ---------- FUNCOES DO DRAG & DROP ----------

    def point_in_card_stack(self, x: float, y: float) -> Optional[list[Card]]:
        """AGRUPAMENTO: devolve a carta clicada + as que estao abaixo dela."""
        for c in reversed(self.cards):  # de tras pra frente = a de cima primeiro
            if (c.left <= x <= c.left + CARD_W) and (c.top <= y <= c.top + CARD_H):
                return [c] + c.home.cards[c.home.cards.index(c) + 1 :]
        return None

    def move_to_top(self, cards: list[Card]):
        """Joga as cartas para o fim da lista (desenhadas por cima)."""
        for card in cards:
            self.cards.remove(card)
            self.cards.append(card)

    def nearest_slot(self, card: Card) -> Optional[Slot]:
        """Devolve o slot perto de onde a carta foi solta (ou None)."""
        for s in self.slots:
            if s != card.home:
                offset = (len(s.cards) - 1) * OFFSET_Y if len(s.cards) > 0 else 0
                near_x = abs(card.left - s.left) < SNAP
                near_y = abs(card.top - (s.top + offset)) < SNAP
                if near_x and near_y:
                    return s
        return None

    def place_card_in_slot(self, card: Card, slot: Slot):
        """Encaixa a carta no slot (atualiza home e posicao)."""
        if card.home is not None:
            card.home.cards.remove(card)  # tira do slot antigo
        card.home = slot
        slot.cards.append(card)  # poe no slot novo
        card.left = slot.left
        card.top = slot.top + OFFSET_Y * (len(slot.cards) - 1)


# ---------- View (desenho) ----------
@ft.component
def CardView(card: Card, key=None) -> ft.Control:
    return ft.Container(
        left=card.left,
        top=card.top,
        width=CARD_W,
        height=CARD_H,
        border_radius=8,
        bgcolor=ft.Colors.BLUE_400,
        border=ft.Border.all(2, ft.Colors.WHITE),
        alignment=ft.Alignment.CENTER,
        content=(
            ft.Image(src=card.imagem, fit=ft.BoxFit.COVER)  # imagem DESTA carta
            if card.imagem
            else ft.Text(card.label, size=24, color=ft.Colors.WHITE)
        ),
    )


@ft.component
def SlotView(slot: Slot, key=None) -> ft.Control:
    return ft.Container(
        left=slot.left,
        top=slot.top,
        width=CARD_W,
        height=CARD_H,
        border=ft.Border.all(2, ft.Colors.BLACK_38),
        border_radius=10,
    )


# ---------- App ----------
@ft.component
def App():
    page = ft.context.page
    page.title = "Drag & Drop"
    page.padding = 0

    board, set_board = ft.use_state(lambda: Board())
    dragging, set_dragging = ft.use_state(None)  # cartas sendo arrastadas
    start_x, set_start_x = ft.use_state(None)  # posicao inicial x
    start_y, set_start_y = ft.use_state(None)  # posicao inicial y

    # 1) PEGAR
    def on_pan_start(e: ft.DragStartEvent):
        grabbed = board.point_in_card_stack(e.local_position.x, e.local_position.y)
        set_dragging(grabbed)
        if grabbed is not None:
            board.move_to_top(grabbed)
            set_start_x(grabbed[0].left)
            set_start_y(grabbed[0].top)

    # 2) MOVER
    def on_pan_update(e: ft.DragUpdateEvent):
        if dragging is None:
            return
        for c in dragging:
            c.left = max(0, c.left + e.local_delta.x)
            c.top = max(0, c.top + e.local_delta.y)
        board.notify()

    # 3) SOLTAR
    def on_pan_end(_: ft.DragEndEvent):
        if dragging is None:
            return

        s = board.nearest_slot(dragging[0])

        if s is not None:
            for c in dragging:
                board.place_card_in_slot(c, s)  # encaixa o grupo
        else:
            for i, c in enumerate(dragging):  # volta pra posicao original
                c.left, c.top = start_x, start_y + i * OFFSET_Y

        board.notify()
        set_dragging(None)

    area = ft.GestureDetector(
        on_pan_start=on_pan_start,
        on_pan_update=on_pan_update,
        on_pan_end=on_pan_end,
        drag_interval=5,
        content=ft.Stack(
            expand=True,
            controls=[ft.Container(expand=True, bgcolor=ft.Colors.GREEN_700, key="bg")]
            + [SlotView(s, key=s.id) for s in board.slots]
            + [CardView(c, key=c.id) for c in board.cards],
        ),
    )

    return ft.Container(expand=True, content=area)


if __name__ == "__main__":
    ft.run(lambda page: page.render(App), assets_dir="assets")