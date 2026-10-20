# Documentação: Drag & Drop com Flet

*Projeto `main.py`: cartas arrastáveis entre slots, cada carta com sua própria imagem.*

## 1. Visão geral

O programa mostra uma mesa verde com **3 slots** (caixas com borda) e **4 cartas**. O usuário pode clicar numa carta, arrastá-la e soltá-la em outro slot. Ao pegar uma carta, todas as cartas abaixo dela no mesmo slot vão junto (**agrupamento**). Se a carta for solta longe de qualquer slot, ela volta para a posição de origem.

O código é dividido em três partes:

| Parte | Elementos | Papel |
| --- | --- | --- |
| **Model** | `Slot`, `Card`, `Board` | Guarda os dados e a lógica |
| **View** | `CardView`, `SlotView` | Desenha na tela |
| **App** | `App` e eventos de arrastar | Reage ao mouse e liga tudo |

## 2. Configuração e constantes

### 2.1 Lista de imagens

```python
IMAGENS = [
    "C:/Users/2601711/Desktop/flet_pyhton/CACHORRINHO.png",
    "C:/Users/2601711/Desktop/flet_pyhton/GATINHO.png",
    "C:/Users/2601711/Desktop/flet_pyhton/PASSARINHO.png",
    "C:/Users/2601711/Desktop/flet_pyhton/COELHINHO.png",
]
```

Cada posição da lista corresponde a uma carta (posição 0 é a carta 1, e assim por diante). Para deixar uma carta sem imagem, use `""`: ela aparecerá como uma caixa azul com número.

> **Atenção:** em caminhos do Windows, use barras normais (`/`) ou uma *raw string* (`r"C:\..."`). Barras invertidas simples causam `SyntaxError`.

### 2.2 Constantes de tamanho

| Constante | Valor | Significado |
| --- | --- | --- |
| `CARD_W` | 80 | Largura da carta |
| `CARD_H` | 110 | Altura da carta |
| `OFFSET_Y` | 25 | Deslocamento vertical entre cartas empilhadas |
| `SNAP` | 40 | Distância máxima (em pixels) para a carta "grudar" num slot |
| `GAP` | 30 | Espaço entre os slots |

## 3. Classes de dados (Model)

Todas usam `@dataclass` (gera o construtor automaticamente) e `@ft.observable` (permite que o Flet perceba mudanças e redesenhe a tela quando `notify()` é chamado).

### 3.1 `Slot`

Representa um espaço na mesa onde cartas podem ficar.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | `str` | Nome do slot (ex.: `"slot1"`) |
| `left` | `float` | Posição horizontal |
| `top` | `float` | Posição vertical |
| `cards` | `list[Card]` | Cartas que estão neste slot |

### 3.2 `Card`

Representa uma carta.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | `str` | Identificador único (ex.: `"c1"`) |
| `label` | `str` | Número exibido quando não há imagem |
| `imagem` | `str` | Caminho da imagem desta carta |
| `left` | `float` | Posição horizontal atual |
| `top` | `float` | Posição vertical atual |
| `home` | `Slot` ou `None` | Slot onde a carta está agora |

### 3.3 `Board`

É o tabuleiro. Guarda a lista de `slots` e a lista de `cards` e contém toda a lógica do Drag & Drop. Cada carta é criada com sua imagem:

```python
Card(id=f"c{i}", label=str(i), imagem=IMAGENS[(i - 1) % len(IMAGENS)])
```

O operador `%` faz a lista voltar ao início caso existam mais cartas do que imagens.

## 4. Funções do `Board` (lógica)

### 4.1 `__post_init__(self)`

**Objetivo:** preparar o estado inicial do jogo.

**Como funciona:** executa automaticamente ao criar um `Board()`. Percorre todas as cartas e coloca cada uma no primeiro slot usando `place_card_in_slot`.

```python
def __post_init__(self):
    for c in self.cards:
        self.place_card_in_slot(c, self.slots[0])
```

**Resultado:** as 4 cartas começam empilhadas no slot 1.

---

### 4.2 `point_in_card_stack(self, x, y)`: agrupamento

**Objetivo:** descobrir qual carta foi clicada e devolver o grupo que será arrastado.

**Parâmetros:** `x`, `y`: coordenadas do clique.

**Retorno:** lista com a carta clicada mais todas as que estão abaixo dela no mesmo slot; ou `None` se o clique foi em área vazia.

```python
def point_in_card_stack(self, x, y):
    for c in reversed(self.cards):
        if (c.left <= x <= c.left + CARD_W) and (c.top <= y <= c.top + CARD_H):
            return [c] + c.home.cards[c.home.cards.index(c) + 1 :]
    return None
```

**Como funciona:**

1. `reversed(self.cards)` percorre as cartas de trás para frente, testando primeiro a que aparece por cima.
2. O `if` verifica se o ponto (x, y) está dentro do retângulo da carta.
3. Ao encontrar, monta a lista `[carta] + cartas seguintes do slot`.

**Exemplo:** slot com `[1, 2, 3, 4]`. Clicar na carta 2 retorna `[2, 3, 4]`.

---

### 4.3 `move_to_top(self, cards)`

**Objetivo:** fazer as cartas arrastadas serem desenhadas por cima das outras.

**Parâmetro:** `cards`: lista de cartas a levar para frente.

```python
def move_to_top(self, cards):
    for card in cards:
        self.cards.remove(card)
        self.cards.append(card)
```

**Como funciona:** no `Stack` do Flet, o que está no fim da lista é desenhado por cima. A função remove cada carta e a recoloca no final.

---

### 4.4 `nearest_slot(self, card)`

**Objetivo:** descobrir em qual slot a carta foi solta.

**Parâmetro:** `card`: a carta (primeira do grupo) que foi solta.

**Retorno:** o `Slot` próximo, ou `None` se não houver nenhum perto.

```python
def nearest_slot(self, card):
    for s in self.slots:
        if s != card.home:
            offset = (len(s.cards) - 1) * OFFSET_Y if len(s.cards) > 0 else 0
            near_x = abs(card.left - s.left) < SNAP
            near_y = abs(card.top - (s.top + offset)) < SNAP
            if near_x and near_y:
                return s
    return None
```

**Como funciona:**

1. Ignora o slot de origem (`s != card.home`).
2. Calcula `offset`: se o slot já tem cartas, o ponto de encaixe fica junto da última carta.
3. `abs(...) < SNAP` mede a distância sem considerar o sinal. Se for menor que 40 px nos dois eixos, o slot é considerado próximo.

---

### 4.5 `place_card_in_slot(self, card, slot)`

**Objetivo:** mover uma carta para um slot e atualizar sua posição.

**Parâmetros:** `card`: a carta; `slot`: o slot de destino.

```python
def place_card_in_slot(self, card, slot):
    if card.home is not None:
        card.home.cards.remove(card)
    card.home = slot
    slot.cards.append(card)
    card.left = slot.left
    card.top = slot.top + OFFSET_Y * (len(slot.cards) - 1)
```

**Como funciona:**

1. Remove a carta da lista do slot antigo.
2. Atualiza `home` para o novo slot.
3. Adiciona a carta à lista do novo slot.
4. Define `left` igual ao do slot e `top` deslocado conforme a quantidade de cartas, para que fiquem escalonadas.

## 5. Funções de desenho (View)

### 5.1 `CardView(card, key=None)`

**Objetivo:** desenhar uma carta na tela.

```python
@ft.component
def CardView(card, key=None):
    return ft.Container(
        left=card.left, top=card.top,
        width=CARD_W, height=CARD_H,
        content=(
            ft.Image(src=card.imagem, fit=ft.BoxFit.COVER)
            if card.imagem
            else ft.Text(card.label, size=24, color=ft.Colors.WHITE)
        ),
    )
```

**Como funciona:** cria um `Container` posicionado em `card.left` e `card.top`. Se a carta tem `imagem`, exibe-a preenchendo toda a carta (`BoxFit.COVER`); caso contrário, exibe o número. O `@ft.component` transforma a função em um componente que o Flet redesenha quando os dados mudam.

### 5.2 `SlotView(slot, key=None)`

**Objetivo:** desenhar a caixa com borda que marca onde as cartas podem ser soltas. Funciona como `CardView`, mas sem conteúdo.

## 6. Eventos de arrastar (`App`)

Os três eventos são ligados ao `GestureDetector`, que "escuta" o mouse:

```python
ft.GestureDetector(
    on_pan_start=on_pan_start,
    on_pan_update=on_pan_update,
    on_pan_end=on_pan_end,
    ...
)
```

### Estados usados

| Estado | Função |
| --- | --- |
| `board` | O tabuleiro atual |
| `dragging` | Lista de cartas sendo arrastadas (ou `None`) |
| `start_x`, `start_y` | Posição de onde a carta saiu, para poder voltar |

`ft.use_state` devolve o valor e uma função para alterá-lo; ao alterar, a tela é redesenhada.

### 6.1 `on_pan_start(e)`: pegar

```python
def on_pan_start(e):
    grabbed = board.point_in_card_stack(e.local_position.x, e.local_position.y)
    set_dragging(grabbed)
    if grabbed is not None:
        board.move_to_top(grabbed)
        set_start_x(grabbed[0].left)
        set_start_y(grabbed[0].top)
```

1. Lê a posição do clique em `e.local_position`.
2. Descobre o grupo com `point_in_card_stack`.
3. Guarda o grupo em `dragging`.
4. Coloca o grupo na frente com `move_to_top`.
5. Anota a posição inicial.

### 6.2 `on_pan_update(e)`: mover

```python
def on_pan_update(e):
    if dragging is None:
        return
    for c in dragging:
        c.left = max(0, c.left + e.local_delta.x)
        c.top = max(0, c.top + e.local_delta.y)
    board.notify()
```

1. Sem nada sendo arrastado, não faz nada.
2. `e.local_delta` é o quanto o mouse andou desde o último evento.
3. Soma esse valor na posição de **cada carta do grupo**, por isso elas andam juntas.
4. `max(0, ...)` impede a carta de sair pela esquerda ou pelo topo.
5. `notify()` redesenha a tela.

### 6.3 `on_pan_end(_)`: soltar

```python
def on_pan_end(_):
    if dragging is None:
        return
    s = board.nearest_slot(dragging[0])
    if s is not None:
        for c in dragging:
            board.place_card_in_slot(c, s)
    else:
        for i, c in enumerate(dragging):
            c.left, c.top = start_x, start_y + i * OFFSET_Y
    board.notify()
    set_dragging(None)
```

1. Procura um slot perto da primeira carta do grupo.
2. Se achou, encaixa todo o grupo com `place_card_in_slot`.
3. Se não achou, devolve cada carta à posição inicial, mantendo o espaçamento com `i * OFFSET_Y`.
4. Chama `notify()` e limpa `dragging`.

## 7. Fluxo completo

```
CLICA        on_pan_start   -> point_in_card_stack (grupo) + move_to_top + guarda posição inicial
ARRASTA      on_pan_update  -> soma local_delta em todas as cartas do grupo + notify()
SOLTA        on_pan_end     -> nearest_slot (onde?)
                                 achou -> place_card_in_slot (encaixa o grupo)
                                 não   -> volta para start_x / start_y
```

## 8. Como executar

```
pip install flet
python main.py
```

A última linha do arquivo inicia o app:

```python
ft.run(lambda page: page.render(App), assets_dir="assets")
```

## 9. Glossário

| Termo | Significado |
| --- | --- |
| **Slot** | Espaço da mesa onde as cartas são encaixadas |
| **Drag & Drop** | Arrastar e soltar |
| **`notify()`** | Avisa o Flet que os dados mudaram para redesenhar a tela |
| **`home`** | Slot onde a carta está |
| **`SNAP`** | Distância máxima para a carta encaixar num slot |
| **Agrupamento** | Arrastar a carta clicada junto com as cartas abaixo dela |
| **`Stack`** | Componente que sobrepõe elementos com posição absoluta |
