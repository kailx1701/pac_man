import turtle
from src.core.config import THEME
from src.core.debug import log_exception


def _mouse(screen, event):
    canvas = screen.getcanvas()
    return (canvas.canvasx(event.x) / screen.xscale,
            -canvas.canvasy(event.y) / screen.yscale)


def clear_ui(screen):
    state = getattr(screen, "_pastel_ui", None)
    if not state:
        return
    state["alive"] = False
    canvas = state["canvas"]
    for sequence, funcid in state["bindings"]:
        try:
            canvas.unbind(sequence, funcid)
        except Exception:
            log_exception(f"unbind failed for {sequence}")
    for pen in state["pens"]:
        try:
            pen.clear()
            pen.hideturtle()
        except Exception:
            log_exception("UI pen cleanup failed")
    screen._pastel_ui = None


def _state(screen):
    clear_ui(screen)
    state = {"alive": True, "canvas": screen.getcanvas(), "bindings": [], "pens": []}
    screen._pastel_ui = state
    return state


def _bind(state, sequence, callback):
    funcid = state["canvas"].bind(sequence, callback, add="+")
    state["bindings"].append((sequence, funcid))


def _shade(color, amount):
    try:
        value = int(color.lstrip("#"), 16)
        channels = [(value >> shift) & 255 for shift in (16, 8, 0)]
        channels = [max(0, min(255, int(c + (255-c)*amount))) for c in channels]
        return "#%02x%02x%02x" % tuple(channels)
    except (ValueError, AttributeError):
        log_exception("invalid button color")
        return color


class Button:
    def __init__(self, screen, state, x, y, label, action, color, width=230, height=48,
                 font=("Courier", 16, "bold"), selected=False):
        self.screen, self.state = screen, state
        self.x, self.y, self.label, self.action = x, y, label, action
        self.color, self.width, self.height, self.font = color, width, height, font
        self.selected = selected
        self.status = "selected" if selected else "normal"
        self.pen = turtle.Turtle()
        self.pen.hideturtle(); self.pen.penup(); self.pen.speed(0)
        state["pens"].append(self.pen)
        self.draw()

    def hit(self, x, y):
        return (self.x-self.width/2 <= x <= self.x+self.width/2
                and self.y-self.height/2 <= y <= self.y+self.height/2)

    def draw(self):
        pen = self.pen
        pen.clear()
        pressed = self.status == "pressed"
        hover = self.status in ("hover", "selected")
        cy = self.y - 3 if pressed else self.y
        fill = _shade(self.color, .15) if hover else (_shade(self.color, -.15) if pressed else self.color)
        x0, x1 = self.x-self.width/2, self.x+self.width/2
        y0, y1 = cy-self.height/2, cy+self.height/2
        if not pressed:
            pen.goto(x0, y0-4); pen.color(THEME["shadow"]); pen.begin_fill()
            for x, y in ((x1,y0-4),(x1,y1-4),(x0,y1-4)):
                pen.goto(x,y)
            pen.goto(x0,y0-4); pen.end_fill()
        pen.goto(x0+8,y0); pen.color("white" if hover else fill, fill)
        pen.pensize(1 if hover else 0); pen.begin_fill(); pen.pendown()
        pen.goto(x1-8,y0); pen.goto(x1,y0+8); pen.goto(x1,y1-8)
        pen.goto(x1-8,y1); pen.goto(x0+8,y1); pen.goto(x0,y1-8)
        pen.goto(x0,y0+8); pen.goto(x0+8,y0); pen.end_fill(); pen.penup()
        pen.goto(self.x, cy-self.height*.25); pen.color(THEME["dark_text"])
        pen.write(self.label, align="center", font=self.font)


def show_menu(pen, screen, text_data, on_select, back=None, selected_value=None):
    pen.clear()
    state = _state(screen)
    state["pens"].append(pen)
    screen.bgcolor(THEME["background"])
    buttons = []
    palette = [THEME[k] for k in ("mint", "peach", "pink", "lavender", "lemon", "sky")]
    color_index = 0
    heading_y = None
    items = sorted(([entry[0], entry[1]] for entry in text_data),
                   key=lambda entry: -entry[0][1])
    button_items = [item for item in items if item[1] is not None]
    if button_items:
        heights = [max(42, (item[0][5][1] if len(item[0][5]) > 1 else 16)*2.05)
                   for item in button_items]
        gap = 14
        group_height = sum(heights) + gap * (len(heights)-1)
        center_y = sum(item[0][1] for item in button_items) / len(button_items)
        if heading_y := max((item[0][1] for item in items if item[1] is None), default=None):
            center_y = min(center_y, heading_y - 36 - 50 - group_height / 2)
        top = center_y + group_height / 2
        for item, height in zip(button_items, heights):
            entry = list(item[0]); entry[1] = top - height/2
            item[0] = tuple(entry)
            top -= height + gap
    for item in items:
        x, y, color, msg, align, font = item[0]
        value = item[1]
        if value is None:
            heading_y = y if heading_y is None else max(heading_y, y)
            pen.goto(x+3,y-3); pen.color(THEME["shadow"]); pen.write(msg, align=align, font=font)
            pen.goto(x,y); pen.color(THEME["text"]); pen.write(msg, align=align, font=font)
            continue
        label = str(msg).strip().strip("[]")
        size = font[1] if len(font) > 1 else 16
        width = max(180, min(400, len(label)*size*.72+54))
        color = palette[color_index % len(palette)]; color_index += 1
        buttons.append(Button(screen, state, x, y, label,
                              lambda v=value: on_select(v), color, width=width,
                              height=max(42, size*2.05), font=(font[0], max(12,size-1), "bold"),
                              selected=selected_value is not None and value == selected_value))
    if heading_y is not None:
        decor_y = heading_y - 36
        decor = turtle.Turtle(); decor.hideturtle(); decor.penup(); decor.speed(0)
        state["pens"].append(decor)
        for i in range(7):
            decor.goto(-130+i*16, decor_y); decor.dot(4, THEME["lemon"])
        pac = turtle.Turtle(); pac.penup(); pac.speed(0); pac.shape("pacman_1"); pac.goto(-165,decor_y)
        state["pens"].append(pac)
        for i, color in enumerate(("red", "pink", "cyan", "orange")):
            ghost = turtle.Turtle(); ghost.penup(); ghost.speed(0)
            ghost.setheading(90)
            ghost.shape(f"ghost_{color}_right_0"); ghost.goto(115+i*25,decor_y)
            state["pens"].append(ghost)
    if back is not None:
        from src.core.config import BACK_MARGIN_BOTTOM, BACK_MARGIN_LEFT
        buttons.append(Button(screen, state, -screen.window_width()/2+BACK_MARGIN_LEFT+62.5,
                              -screen.window_height()/2+BACK_MARGIN_BOTTOM+19, "< BACK", back,
                              THEME["sky"], width=125, height=38,
                              font=("Courier", 12, "bold")))

    def guarded(fn):
        def wrapped(event):
            if not state["alive"]:
                return
            try:
                fn(event)
            except Exception:
                log_exception("menu callback failed")
        return wrapped

    pressed = {"button": None}
    def motion(event):
        x,y = _mouse(screen,event)
        hit = next((b for b in buttons if b.hit(x,y)), None)
        for b in buttons:
            status = "pressed" if pressed["button"] is b else ("hover" if b is hit else ("selected" if b.selected else "normal"))
            if status != b.status:
                b.status = status; b.draw()
    def down(event):
        x,y = _mouse(screen,event)
        pressed["button"] = next((b for b in buttons if b.hit(x,y)), None)
        motion(event)
    def up(event):
        x,y = _mouse(screen,event)
        selected = pressed["button"]
        pressed["button"] = None
        if selected:
            selected.status = "hover" if selected.hit(x,y) else ("selected" if selected.selected else "normal")
            selected.draw()
            if selected.hit(x,y):
                clear_ui(screen)
                selected.action()
                return
        motion(event)
    _bind(state,"<Motion>",guarded(motion))
    _bind(state,"<ButtonPress-1>",guarded(down))
    _bind(state,"<ButtonRelease-1>",guarded(up))
    screen.update()


def show_ghost_slider(pen, screen, count, on_next, back=None):
    state = _state(screen)
    state["pens"].append(pen)
    pen.clear(); pen.color(THEME["text"])
    title = turtle.Turtle(); title.hideturtle(); title.penup(); state["pens"].append(title)
    slider = {"count": max(0, min(4, int(count))), "drag": False}
    left, right, y = -200, 200, 5
    title.goto(0,125); title.color(THEME["text"]); title.write("GHOSTS: 0", align="center", font=("Courier",30,"bold"))
    for i, color in enumerate(("red","pink","cyan","orange")):
        ghost = turtle.Turtle(); ghost.penup(); ghost.hideturtle(); ghost.speed(0)
        ghost.setheading(90)
        ghost.shape(f"ghost_{color}_right_0"); ghost.goto((i-1.5)*38,82)
        state["pens"].append(ghost)
    track = turtle.Turtle(); track.hideturtle(); track.penup(); track.speed(0); state["pens"].append(track)
    nums = turtle.Turtle(); nums.hideturtle(); nums.penup(); nums.speed(0); state["pens"].append(nums)
    def redraw():
        if not state["alive"]: return
        nums.clear()
        n = slider["count"]
        title.clear(); title.goto(0,125)
        title.color(THEME["text"])
        title.write("NO ENEMIES" if n == 0 else f"GHOSTS: {n}", align="center", font=("Courier",30,"bold"))
        for i, ghost in enumerate(state["pens"][2:6]):
            if i < n: ghost.showturtle()
            else: ghost.hideturtle()
        track.clear(); track.goto(left,y); track.color(THEME["muted"]); track.pensize(8); track.pendown(); track.goto(right,y); track.penup()
        x = left + (right-left)*n/4
        track.goto(left,y); track.color(THEME["mint"]); track.pensize(8); track.pendown(); track.goto(x,y); track.penup()
        track.goto(x,y); track.dot(24,"white"); track.dot(17,THEME["pink"])
        for i in range(5):
            xx=left+(right-left)*i/4; track.goto(xx,y); track.dot(7,THEME["text"])
            nums.goto(xx,y-42); nums.color(THEME["text"]); nums.write(str(i),align="center",font=("Courier",14,"bold"))
        screen.update()
    def set_value(x):
        slider["count"] = max(0,min(4,int(round((x-left)/(right-left)*4))))
        redraw()
    def guarded(fn):
        def call(event):
            if state["alive"]:
                try: fn(event)
                except Exception:
                    log_exception("slider callback failed")
        return call
    def motion(event):
        if slider["drag"]: set_value(_mouse(screen,event)[0])
    def down(event):
        x, yy = _mouse(screen,event)
        if left-18 <= x <= right+18 and abs(yy-y) <= 24:
            slider["drag"] = True; set_value(x)
    def up(event): slider["drag"] = False
    _bind(state,"<Motion>",guarded(motion)); _bind(state,"<ButtonPress-1>",guarded(down)); _bind(state,"<ButtonRelease-1>",guarded(up))
    def key(event):
        if event.keysym in ("Left","Right"):
            slider["count"] = max(0,min(4,slider["count"] + (1 if event.keysym=="Right" else -1))); redraw()
    _bind(state,"<KeyPress-Left>",guarded(key)); _bind(state,"<KeyPress-Right>",guarded(key))
    buttons = [Button(screen,state,0,-90,"NEXT",lambda: (clear_ui(screen),on_next(slider["count"])),THEME["mint"],width=190,height=46)]
    if back:
        from src.core.config import BACK_MARGIN_BOTTOM, BACK_MARGIN_LEFT
        buttons.append(Button(screen,state,-screen.window_width()/2+BACK_MARGIN_LEFT+62.5,-screen.window_height()/2+BACK_MARGIN_BOTTOM+19,"< BACK",lambda:(clear_ui(screen),back()),THEME["sky"],width=125,height=38,font=("Courier",12,"bold")))
    clicked={"item":None}
    def button_down(event):
        xx,yy=_mouse(screen,event); clicked["item"]=next((b for b in buttons if b.hit(xx,yy)),None)
        if clicked["item"]: clicked["item"].status="pressed"; clicked["item"].draw()
    def button_up(event):
        xx,yy=_mouse(screen,event); b=clicked["item"]; clicked["item"]=None
        if b:
            inside=b.hit(xx,yy); b.status="hover" if inside else "normal"; b.draw()
            if inside: b.action()
    _bind(state,"<ButtonPress-1>",guarded(button_down)); _bind(state,"<ButtonRelease-1>",guarded(button_up))
    redraw()
