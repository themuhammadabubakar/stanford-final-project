from graphics import Canvas
import random
import time
import math

CANVAS_WIDTH = 850
CANVAS_HEIGHT = 600

PEN_WIDTH = 140
PEN_HEIGHT = 40

SKETCH_X = 160
SKETCH_Y = 80
SKETCH_WIDTH = 650
SKETCH_HEIGHT = 500

NO_OF_SKETCH_IMAGES = 10
MAX_STROKES = 2000
RESTACK_INTERVAL = 20

PEN_COLORS = {
    'black_pen': '#2e2e2eff',
    'white_pen': '#ffffff',
    'purple_pen': '#6B5B95',
    'dark_blue_pen': '#1B3A6B',
    'light_blue_pen': '#4A90D9',
    'dark_green_pen': '#2D5A3D',
    'light_green_pen': '#5CB85C',
    'yellow_pen': '#F0C040',
    'bubblegum_pen': '#E8A0C8',
    'orange_pen': '#E67E22',
    'pink_pen': '#E91E8C',
    'red_pen': '#e43d2aff',
    'eraser': 'white'
}

CURRENT_PEN_COLOR = None
CURRENT_PEN_SIZE = 30
MAX_PEN_SIZE = 100
MIN_PEN_SIZE = 2
IS_PAINTING = False
WAS_PAINTING = False
ACTIVE_PEN_NAME = None

PENS = {name: None for name in PEN_COLORS}
BUTTONS = {'minus': None, 'plus': None, 'change': None, 'blank': None}
SIZE_TEXT_ID = None
CURSOR_INDICATOR = None

SKETCH_IMAGE = None
CURRENT_SKETCH_ID = 1

PAINT_STROKES = set()
STROKES_SINCE_RESTACK = 0
LAST_RESTACK_TIME = 0

CURRENT_STROKE_POINTS = []
CURRENT_STROKE_ID = None

LEFT_BOUND = SKETCH_X
RIGHT_BOUND = SKETCH_X + SKETCH_WIDTH
TOP_BOUND = SKETCH_Y
BOTTOM_BOUND = SKETCH_Y + SKETCH_HEIGHT


def main():
    canvas = Canvas(CANVAS_WIDTH, CANVAS_HEIGHT)
    change_sketch_image(canvas)
    
    selected_pen = list(PEN_COLORS.keys())[0]
    select_pen(canvas, selected_pen)

    canvas.create_text(20, 30, text='Pen Size', font='Arial', font_size=16, color='black')
    canvas.create_text((CANVAS_WIDTH / 2) - 105, CANVAS_HEIGHT - 18, text='Click to start painting, click again to stop', font='Arial', font_size=14, color='grey')
    
    BUTTONS['minus'] = canvas.create_image_with_size(100, 0, 60, 78, "minus_btn.png")
    SIZE_TEXT_ID = canvas.create_text(165, 25, text=str(CURRENT_PEN_SIZE), font='Arial', font_size=19, color='black')
    BUTTONS['plus'] = canvas.create_image_with_size(200, 0, 65, 78, "plus_btn.png")
    BUTTONS['change'] = canvas.create_image_with_size(300, 8, 190, 55, "change_image_btn.png")
    BUTTONS['blank'] = canvas.create_image_with_size(500, 8, 190, 55, "blank_btn.png")
    
    CURSOR_INDICATOR = canvas.create_oval(-100, -100, -100 + CURRENT_PEN_SIZE, -100 + CURRENT_PEN_SIZE, CURRENT_PEN_COLOR, CURRENT_PEN_COLOR)
    canvas.set_hidden(CURSOR_INDICATOR, True)
    
    run_interaction_loop(canvas, selected_pen, SIZE_TEXT_ID)


def change_sketch_image(canvas, sketch_image_id=None):
    global SKETCH_IMAGE, CURRENT_SKETCH_ID
    if SKETCH_IMAGE is not None: canvas.delete(SKETCH_IMAGE) 
    if sketch_image_id is None: sketch_image_id = random.randint(1, NO_OF_SKETCH_IMAGES)
    CURRENT_SKETCH_ID = sketch_image_id  
    SKETCH_IMAGE = canvas.create_image_with_size(SKETCH_X, SKETCH_Y, SKETCH_WIDTH, SKETCH_HEIGHT, f"{sketch_image_id}.png")


def clear_all_paint(canvas):
    global PAINT_STROKES, STROKES_SINCE_RESTACK, CURRENT_STROKE_POINTS, CURRENT_STROKE_ID
    for stroke_id in PAINT_STROKES: canvas.delete(stroke_id)
    if CURRENT_STROKE_ID is not None: canvas.delete(CURRENT_STROKE_ID)
    PAINT_STROKES = set()
    STROKES_SINCE_RESTACK = 0
    CURRENT_STROKE_POINTS = []
    CURRENT_STROKE_ID = None


def update_indicator_style(canvas):
    global CURSOR_INDICATOR
    if CURSOR_INDICATOR is not None: canvas.delete(CURSOR_INDICATOR)
    if ACTIVE_PEN_NAME == 'eraser': 
        CURSOR_INDICATOR = canvas.create_oval(-100, -100, -100 + CURRENT_PEN_SIZE, -100 + CURRENT_PEN_SIZE, "white", "red")
    else:
        CURSOR_INDICATOR = canvas.create_oval(-100, -100, -100 + CURRENT_PEN_SIZE, -100 + CURRENT_PEN_SIZE, CURRENT_PEN_COLOR, CURRENT_PEN_COLOR)
    canvas.set_hidden(CURSOR_INDICATOR, True)


def select_pen(canvas, selected_pen):
    global CURRENT_PEN_COLOR, ACTIVE_PEN_NAME, IS_PAINTING, WAS_PAINTING
    ACTIVE_PEN_NAME = selected_pen
    CURRENT_PEN_COLOR = PEN_COLORS[selected_pen]
    IS_PAINTING = False
    WAS_PAINTING = False
    draw_pens(canvas, selected_pen)
    update_indicator_style(canvas)


def draw_pens(canvas, selected_pen):    
    y_offset = (PEN_HEIGHT + CANVAS_HEIGHT - (len(PEN_COLORS) * PEN_HEIGHT)) / 2
    for i, pen_name in enumerate(PEN_COLORS):
        x_offset = 0 if pen_name == selected_pen else -PEN_HEIGHT 
        if PENS[pen_name] is not None: canvas.delete(PENS[pen_name])
        PENS[pen_name] = canvas.create_image_with_size(x_offset, y_offset + (PEN_HEIGHT * i), PEN_WIDTH, PEN_HEIGHT, f"{pen_name}.png")


def check_clicked(canvas, obj_id, click_x, click_y):
    if obj_id is None: return False
    left_x = canvas.get_left_x(obj_id)
    top_y = canvas.get_top_y(obj_id)
    width = canvas.get_object_width(obj_id)
    height = canvas.get_object_height(obj_id)
    return left_x <= click_x <= left_x + width and top_y <= click_y <= top_y + height


def restack_sketch(canvas):
    global SKETCH_IMAGE, STROKES_SINCE_RESTACK, LAST_RESTACK_TIME
    if SKETCH_IMAGE is not None:
        canvas.delete(SKETCH_IMAGE)
        SKETCH_IMAGE = canvas.create_image_with_size(SKETCH_X, SKETCH_Y, SKETCH_WIDTH, SKETCH_HEIGHT, f"{CURRENT_SKETCH_ID}.png")
    STROKES_SINCE_RESTACK = 0
    LAST_RESTACK_TIME = time.time()


def erase_at(canvas, x, y, radius):
    global PAINT_STROKES, CURRENT_STROKE_ID
    eraser_left = x - radius
    eraser_top = y - radius
    eraser_right = x + radius
    eraser_bottom = y + radius
    overlapping = canvas.find_overlapping(eraser_left, eraser_top, eraser_right, eraser_bottom)
    
    to_remove = []
    for obj_id in overlapping:
        if obj_id == CURRENT_STROKE_ID or obj_id not in PAINT_STROKES:
            continue
        try:
            obj_left = canvas.get_left_x(obj_id)
            obj_top = canvas.get_top_y(obj_id)
            obj_width = canvas.get_object_width(obj_id)
            obj_height = canvas.get_object_height(obj_id)
            if obj_left is None or obj_top is None or obj_width is None or obj_height is None: continue
            obj_right = obj_left + obj_width
            obj_bottom = obj_top + obj_height
            overlaps = not (eraser_right < obj_left or eraser_left > obj_right or eraser_bottom < obj_top or eraser_top > obj_bottom)
            if overlaps: to_remove.append(obj_id)
        except:
            continue
    
    for stroke_id in to_remove:
        try: canvas.delete(stroke_id)
        except: pass
        PAINT_STROKES.discard(stroke_id)


def points_to_polygon(points, radius):
    if len(points) < 2: return []
    clean_points = [(x, y) for x, y in points if x is not None and y is not None]
    if len(clean_points) < 2: return []
    
    left_edge = []
    right_edge = []
    
    for i in range(len(clean_points)):
        x, y = clean_points[i]
        if i == 0:
            dx = clean_points[1][0] - x
            dy = clean_points[1][1] - y
        elif i == len(clean_points) - 1:
            dx = x - clean_points[-2][0]
            dy = y - clean_points[-2][1]
        else:
            dx = (clean_points[i+1][0] - clean_points[i-1][0]) / 2
            dy = (clean_points[i+1][1] - clean_points[i-1][1]) / 2
        
        length = math.sqrt(dx*dx + dy*dy)
        if length < 0.001:
            if left_edge and right_edge:
                left_edge.append((x, y))
                right_edge.append((x, y))
            else:
                left_edge.append((x, y - radius))
                right_edge.append((x, y + radius))
            continue
        
        dx, dy = dx / length, dy / length
        px, py = -dy * radius, dx * radius
        
        left_edge.append((x + px, y + py))
        right_edge.append((x - px, y - py))

    polygon = []
    
    start_x, start_y = clean_points[0]
    start_dx = clean_points[1][0] - start_x
    start_dy = clean_points[1][1] - start_y
    start_len = math.sqrt(start_dx*start_dx + start_dy*start_dy)
    
    if start_len > 0.001:
        fx, fy = start_dx/start_len, start_dy/start_len
        lx, ly = -fy, fx

        bx, by = -fx, -fy
        
        for i in range(16, -1, -1):
            theta = math.pi * i / 16
            cap_x = start_x + radius * (lx * math.cos(theta) + bx * math.sin(theta))
            cap_y = start_y + radius * (ly * math.cos(theta) + by * math.sin(theta))
            polygon.extend([cap_x, cap_y])
    else:
        polygon.extend([right_edge[0][0], right_edge[0][1]])
        polygon.extend([left_edge[0][0], left_edge[0][1]])
    

    for x, y in left_edge:
        polygon.extend([x, y])

    end_x, end_y = clean_points[-1]
    end_dx = clean_points[-1][0] - clean_points[-2][0]
    end_dy = clean_points[-1][1] - clean_points[-2][1]
    end_len = math.sqrt(end_dx*end_dx + end_dy*end_dy)
    
    if end_len > 0.001:
        fx, fy = end_dx/end_len, end_dy/end_len
        lx, ly = -fy, fx
        
        for i in range(0, 17):
            theta = math.pi * i / 16
            cap_x = end_x + radius * (lx * math.cos(theta) + fx * math.sin(theta))
            cap_y = end_y + radius * (ly * math.cos(theta) + fy * math.sin(theta))
            polygon.extend([cap_x, cap_y])
    else:
        polygon.extend([left_edge[-1][0], left_edge[-1][1]])
        polygon.extend([right_edge[-1][0], right_edge[-1][1]])
    
    for x, y in reversed(right_edge):
        polygon.extend([x, y])
    
    return polygon


def clip_polygon_to_bounds(polygon, left, right, top, bottom):
    if len(polygon) < 6:
        return polygon
    
    pts = [(polygon[i], polygon[i+1]) for i in range(0, len(polygon), 2)]
    
    def inside(p, edge):
        x, y = p
        if edge == 'left': return x >= left
        if edge == 'right': return x <= right
        if edge == 'top': return y >= top
        if edge == 'bottom': return y <= bottom
    
    def intersect(p1, p2, edge):
        x1, y1 = p1
        x2, y2 = p2
        if edge == 'left':
            t = (left - x1) / (x2 - x1) if x2 != x1 else 0
            return (left, y1 + t * (y2 - y1))
        if edge == 'right':
            t = (right - x1) / (x2 - x1) if x2 != x1 else 0
            return (right, y1 + t * (y2 - y1))
        if edge == 'top':
            t = (top - y1) / (y2 - y1) if y2 != y1 else 0
            return (x1 + t * (x2 - x1), top)
        if edge == 'bottom':
            t = (bottom - y1) / (y2 - y1) if y2 != y1 else 0
            return (x1 + t * (x2 - x1), bottom)
    
    def clip_edge(input_list, edge):
        output = []
        if not input_list:
            return output
        s = input_list[-1]
        for e in input_list:
            if inside(e, edge):
                if not inside(s, edge):
                    output.append(intersect(s, e, edge))
                output.append(e)
            elif inside(s, edge):
                output.append(intersect(s, e, edge))
            s = e
        return output
    
    # Clip against all four edges
    for edge in ['left', 'right', 'top', 'bottom']:
        pts = clip_edge(pts, edge)
        if not pts:
            return []
    
    # Convert back to flat list
    result = []
    for x, y in pts:
        result.extend([x, y])
    return result


def update_stroke_polygon(canvas, points, radius, color):
    global CURRENT_STROKE_ID
    if len(points) < 2: return None
    poly = points_to_polygon(points, radius)
    if len(poly) < 6: return None
    
    # Clip the polygon to canvas bounds so paint never draws outside
    clipped_poly = clip_polygon_to_bounds(poly, LEFT_BOUND, RIGHT_BOUND, TOP_BOUND, BOTTOM_BOUND)
    if len(clipped_poly) < 6:
        return CURRENT_STROKE_ID  # Keep previous if clip removes everything
    
    if CURRENT_STROKE_ID is not None:
        try: canvas.delete(CURRENT_STROKE_ID)
        except: CURRENT_STROKE_ID = None
    CURRENT_STROKE_ID = canvas.create_polygon(*clipped_poly, color=color, outline=color)
    return CURRENT_STROKE_ID


def finalize_stroke(canvas):
    global CURRENT_STROKE_POINTS, CURRENT_STROKE_ID, PAINT_STROKES, STROKES_SINCE_RESTACK
    if CURRENT_STROKE_ID is None or len(CURRENT_STROKE_POINTS) < 2:
        CURRENT_STROKE_POINTS = []
        CURRENT_STROKE_ID = None
        return
    
    xs = [p[0] for p in CURRENT_STROKE_POINTS if p[0] is not None]
    ys = [p[1] for p in CURRENT_STROKE_POINTS if p[1] is not None]
    if not xs or not ys:
        CURRENT_STROKE_POINTS = []
        CURRENT_STROKE_ID = None
        return
    
    PAINT_STROKES.add(CURRENT_STROKE_ID)
    STROKES_SINCE_RESTACK += 1
    restack_sketch(canvas)
    CURRENT_STROKE_POINTS = []
    CURRENT_STROKE_ID = None


def get_clipped_paint_point(x, y, last_x, last_y, radius):
    """Get paint point with boundary intersection when crossing from inside to outside.
    Returns list of points to add to stroke."""
    
    # Check if point is outside the strict canvas bounds
    out_left = x < LEFT_BOUND
    out_right = x > RIGHT_BOUND
    out_top = y < TOP_BOUND
    out_bottom = y > BOTTOM_BOUND
    is_outside = out_left or out_right or out_top or out_bottom
    
    if not is_outside:
        return [(x, y)]
    
    # Point is outside - check if last was also outside
    last_out = (last_x < LEFT_BOUND or last_x > RIGHT_BOUND or 
                last_y < TOP_BOUND or last_y > BOTTOM_BOUND)
    
    if last_out:
        # Both outside - just clip to nearest boundary for continuity
        cx = max(LEFT_BOUND, min(RIGHT_BOUND, x))
        cy = max(TOP_BOUND, min(BOTTOM_BOUND, y))
        return [(cx, cy)]
    
    # Crossing from inside to outside - find exact intersection with boundary
    dx = x - last_x
    dy = y - last_y
    
    if abs(dx) < 0.001 and abs(dy) < 0.001:
        cx = max(LEFT_BOUND, min(RIGHT_BOUND, x))
        cy = max(TOP_BOUND, min(BOTTOM_BOUND, y))
        return [(cx, cy)]
    
    t_candidates = []
    
    if dx > 0:
        t = (RIGHT_BOUND - last_x) / dx
        if 0 <= t <= 1: t_candidates.append((t, RIGHT_BOUND, None))
    elif dx < 0:
        t = (LEFT_BOUND - last_x) / dx
        if 0 <= t <= 1: t_candidates.append((t, LEFT_BOUND, None))
    
    if dy > 0:
        t = (BOTTOM_BOUND - last_y) / dy
        if 0 <= t <= 1: t_candidates.append((t, None, BOTTOM_BOUND))
    elif dy < 0:
        t = (TOP_BOUND - last_y) / dy
        if 0 <= t <= 1: t_candidates.append((t, None, TOP_BOUND))
    
    if not t_candidates:
        cx = max(LEFT_BOUND, min(RIGHT_BOUND, x))
        cy = max(TOP_BOUND, min(BOTTOM_BOUND, y))
        return [(cx, cy)]
    
    # Get first intersection
    t_candidates.sort(key=lambda c: c[0])
    first_t, bx, by = t_candidates[0]
    
    ix = last_x + dx * first_t if bx is None else bx
    iy = last_y + dy * first_t if by is None else by
    
    # Return intersection point (on boundary) + clipped outside point
    cx = max(LEFT_BOUND, min(RIGHT_BOUND, x))
    cy = max(TOP_BOUND, min(BOTTOM_BOUND, y))
    
    return [(ix, iy), (cx, cy)]


def run_interaction_loop(canvas, selected_pen, SIZE_TEXT_ID):
    global CURRENT_PEN_SIZE, IS_PAINTING, WAS_PAINTING, PAINT_STROKES, STROKES_SINCE_RESTACK
    global CURRENT_SKETCH_ID, SKETCH_IMAGE, LAST_RESTACK_TIME
    global CURRENT_STROKE_POINTS, CURRENT_STROKE_ID
    
    last_x = None
    last_y = None
    
    while True:
        clicks = canvas.get_new_mouse_clicks()
        
        for click in clicks:
            if not click: continue

            click_x, click_y = click
            clicked_ui = False

            for pen_name, obj_id in PENS.items():
                if check_clicked(canvas, obj_id, click_x, click_y):
                    selected_pen = pen_name
                    select_pen(canvas, selected_pen)
                    clicked_ui = True
                    break

            if not clicked_ui:
                if check_clicked(canvas, BUTTONS['minus'], click_x, click_y):
                    if CURRENT_PEN_SIZE > MIN_PEN_SIZE:
                        CURRENT_PEN_SIZE -= 1
                        canvas.change_text(SIZE_TEXT_ID, str(CURRENT_PEN_SIZE))
                        update_indicator_style(canvas)
                    clicked_ui = True
                elif check_clicked(canvas, BUTTONS['plus'], click_x, click_y):
                    if CURRENT_PEN_SIZE < MAX_PEN_SIZE:
                        CURRENT_PEN_SIZE += 1
                        canvas.change_text(SIZE_TEXT_ID, str(CURRENT_PEN_SIZE))
                        update_indicator_style(canvas)
                    clicked_ui = True

            if not clicked_ui and check_clicked(canvas, BUTTONS['change'], click_x, click_y):
                clear_all_paint(canvas)
                change_sketch_image(canvas)
                clicked_ui = True

            if not clicked_ui and check_clicked(canvas, BUTTONS['blank'], click_x, click_y):
                clear_all_paint(canvas)
                change_sketch_image(canvas, 0)
                clicked_ui = True

            if not clicked_ui:
                if SKETCH_X <= click_x <= SKETCH_X + SKETCH_WIDTH and SKETCH_Y <= click_y <= SKETCH_Y + SKETCH_HEIGHT:
                    if IS_PAINTING and CURRENT_STROKE_POINTS:
                        finalize_stroke(canvas)
                    IS_PAINTING = not IS_PAINTING
                    WAS_PAINTING = IS_PAINTING
                    last_x = None
                    last_y = None

        current_x = canvas.get_mouse_x()
        current_y = canvas.get_mouse_y()
        radius = CURRENT_PEN_SIZE / 2
        
        if current_x is None or current_y is None: continue
        
        # Check if cursor center is within the canvas area (for painting toggle)
        in_sketch_area = LEFT_BOUND <= current_x <= RIGHT_BOUND and TOP_BOUND <= current_y <= BOTTOM_BOUND
        
        # For cursor visibility: show if any part of brush is near canvas
        cursor_visible = (LEFT_BOUND - radius) <= current_x <= (RIGHT_BOUND + radius) and \
                         (TOP_BOUND - radius) <= current_y <= (BOTTOM_BOUND + radius)
        
        # Get paint points with boundary handling
        if last_x is not None and last_y is not None:
            paint_points = get_clipped_paint_point(current_x, current_y, last_x, last_y, radius)
        else:
            # First point - clip to bounds if outside
            if in_sketch_area:
                paint_points = [(current_x, current_y)]
            else:
                cx = max(LEFT_BOUND, min(RIGHT_BOUND, current_x))
                cy = max(TOP_BOUND, min(BOTTOM_BOUND, current_y))
                paint_points = [(cx, cy)]
        
        cursor_x, cursor_y = paint_points[0]
        if cursor_visible:
            canvas.set_hidden(CURSOR_INDICATOR, False)
            canvas.moveto(CURSOR_INDICATOR, cursor_x - radius, cursor_y - radius)
        else:
            canvas.set_hidden(CURSOR_INDICATOR, True)
        
        if WAS_PAINTING and not IS_PAINTING and in_sketch_area:
            IS_PAINTING = True
            last_x = cursor_x
            last_y = cursor_y
        
        if IS_PAINTING:
            if last_x is None:
                last_x = cursor_x
                last_y = cursor_y
                CURRENT_STROKE_POINTS = [(cursor_x, cursor_y)]
            
            for px, py in paint_points:
                dx = px - last_x
                dy = py - last_y
                move_dist = math.sqrt(dx*dx + dy*dy)
                
                if move_dist >= radius * 0.1:
                    if ACTIVE_PEN_NAME == 'eraser':
                        erase_at(canvas, px, py, radius)
                    else:
                        CURRENT_STROKE_POINTS.append((px, py))
                        update_stroke_polygon(canvas, CURRENT_STROKE_POINTS, radius, CURRENT_PEN_COLOR)
                        
                        while len(PAINT_STROKES) > MAX_STROKES:
                            to_remove = list(PAINT_STROKES)[:50]
                            for old_id in to_remove:
                                try: canvas.delete(old_id)
                                except: pass
                                PAINT_STROKES.discard(old_id)
                        
                        if STROKES_SINCE_RESTACK >= RESTACK_INTERVAL: 
                            restack_sketch(canvas)
                    
                    last_x = px
                    last_y = py

        if not in_sketch_area and IS_PAINTING:
            WAS_PAINTING = True
            IS_PAINTING = False
            if CURRENT_STROKE_POINTS:
                finalize_stroke(canvas)


if __name__ == '__main__':
    main()