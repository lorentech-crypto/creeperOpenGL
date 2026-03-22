"""
Actividad 1 – Dibujo de objetos 3D, visualización y proyección Creeper de Minecraft con OpenGL y GLUT
Dimensiones (en cubos unitarios):
  Pies   : 8 x 4 x 6  c/u, separados 2 cubos entre sí
  Cuerpo : 8 x 4 x 12 (solapa 1 cubo con cada pie)
  Cabeza : 8 x 8 x 8  (centrada con el cuerpo)
  Cara   : elementos negros superpuestos en cara frontal
Ventana: 4 viewports
  Superior-Izq  : Proyección paralela ortográfica  – Vista frontal
  Superior-Der  : Proyección paralela ortográfica  – Vista lateral izquierda
  Inferior-Izq  : Proyección en perspectiva        – Vista libre (orbital)
  Inferior-Der  : Proyección paralela oblicua gabinete – Vista isométrica
"""


# Dependencias

try:
    from OpenGL.GL   import *
    from OpenGL.GLU  import *
    from OpenGL.GLUT import *
except ImportError:
    raise SystemExit("Instala PyOpenGL:  pip install PyOpenGL PyOpenGL_accelerate")

import math
import sys


# Colores (tonos verde/negro del Creeper)

GREEN_LIGHT  = (0.18, 0.70, 0.18)   # verde claro cuerpo
GREEN_DARK   = (0.08, 0.42, 0.08)   # verde oscuro detalle
BLACK_FACE   = (0.05, 0.05, 0.05)   # negro cara
GREEN_MID    = (0.12, 0.55, 0.12)   # verde medio pies/cuerpo


# Estado de la cámara orbital (viewport perspectiva)

cam_angle_x = 20.0
cam_angle_y = -40.0
cam_zoom    = 40.0
last_x = last_y = 0
mouse_btn   = None


# PRIMITIVA: cubo unitario centrado en el origen con color uniforme

def color_cube(colorv):
    """
    Función que dibuja un cubo centrado en el origen y de lado 1
    con todas las caras del color pasado por parámetro a la función.
    El color se pasa en una lista de tres componentes.
    """
    he = 0.5   # semilado del cubo (half-edge)

    v1 = [-he, -he,  he]
    v2 = [-he,  he,  he]
    v3 = [ he, -he,  he]
    v4 = [ he,  he,  he]
    v5 = [ he, -he, -he]
    v6 = [ he,  he, -he]
    v7 = [-he,  he, -he]
    v8 = [-he, -he, -he]

    glColor3fv(colorv)

    # CARA POSTERIOR
    glBegin(GL_POLYGON)
    glVertex3fv(v8)
    glVertex3fv(v7)
    glVertex3fv(v6)
    glVertex3fv(v5)
    glEnd()

    # CARA FRONTAL
    glBegin(GL_POLYGON)
    glVertex3fv(v1)
    glVertex3fv(v3)
    glVertex3fv(v4)
    glVertex3fv(v2)
    glEnd()

    # CARA DERECHA
    glBegin(GL_POLYGON)
    glVertex3fv(v3)
    glVertex3fv(v5)
    glVertex3fv(v6)
    glVertex3fv(v4)
    glEnd()

    # CARA IZQUIERDA
    glBegin(GL_POLYGON)
    glVertex3fv(v1)
    glVertex3fv(v2)
    glVertex3fv(v7)
    glVertex3fv(v8)
    glEnd()

    # CARA INFERIOR
    glBegin(GL_POLYGON)
    glVertex3fv(v1)
    glVertex3fv(v3)
    glVertex3fv(v5)
    glVertex3fv(v8)
    glEnd()

    # CARA SUPERIOR
    glBegin(GL_POLYGON)
    glVertex3fv(v2)
    glVertex3fv(v4)
    glVertex3fv(v6)
    glVertex3fv(v7)
    glEnd()

def draw_orthohedron(cx, cy, cz, W, D, H, color, hollow=True):
    """Dibuja un bloque W×D×H de cubos unitarios centrado en (cx,cy,cz)."""
    ox = cx - W / 2.0 + 0.5   # offset al primer cubo
    oy = cy - H / 2.0 + 0.5
    oz = cz - D / 2.0 + 0.5

    for ix in range(W):
        for iy in range(H):
            for iz in range(D):
                # Modo hueco: sólo dibuja si al menos una cara es exterior
                if hollow:
                    if not (ix == 0 or ix == W-1 or
                            iy == 0 or iy == H-1 or
                            iz == 0 or iz == D-1):
                        continue
                glPushMatrix()
                glTranslatef(ox + ix, oy + iy, oz + iz)
                color_cube(color)
                glPopMatrix()


# ELEMENTOS DE LA CARA (sobre cara frontal Z+ de la cabeza)

def draw_face(head_cx, head_cy, head_cz, head_H):
    """Dibuja los elementos negros de la cara sobre la cara frontal de la cabeza."""
    # Z frontal de la cabeza = head_cz + head_D/2   (head_D=8 → +4)
    head_D = 8
    z_face = head_cz + head_D / 2.0 + 0.01   # ligeramente por delante

    # Centro vertical de la cara: parte superior de la cabeza
    # Ojos: Y = head_cy + 1 y +2  (dos filas)
    # Ojo izquierdo (X negativo)  y ojo derecho (X positivo)

    eye_positions = [
        (-2, head_cy + 1.5),   # ojo izq fila sup
        (-1, head_cy + 1.5),
        (-2, head_cy + 0.5),   # ojo izq fila inf
        (-1, head_cy + 0.5),
        ( 1, head_cy + 1.5),   # ojo der fila sup
        ( 2, head_cy + 1.5),
        ( 1, head_cy + 0.5),   # ojo der fila inf
        ( 2, head_cy + 0.5),
    ]

    # Boca (T invertida): fila central amplia + columna central hacia abajo
    mouth_positions = [
        (-1, head_cy - 0.5), (0, head_cy - 0.5), (1, head_cy - 0.5),   # fila sup boca
        (-2, head_cy - 1.5), (-1, head_cy - 1.5),                        # alas
        ( 1, head_cy - 1.5), ( 2, head_cy - 1.5),
        (0,  head_cy - 1.5),                                              # centro
        (-1, head_cy - 2.5), (0, head_cy - 2.5), (1, head_cy - 2.5),   # fila inf
    ]

    for (x, y) in eye_positions:
        glPushMatrix()
        glTranslatef(head_cx + x, y, z_face)
        glScalef(1.0, 1.0, 0.02)
        color_cube(BLACK_FACE)
        glPopMatrix()

    for (x, y) in mouth_positions:
        glPushMatrix()
        glTranslatef(head_cx + x, y, z_face)
        glScalef(1.0, 1.0, 0.02)
        color_cube(BLACK_FACE)
        glPopMatrix()

# CREEPER COMPLETO

def draw_creeper():
    """Dibuja el creeper completo en el origen."""

    # ── PIES ────────────────────────────────────────────────────────────────
  
    pie_cy = 3.0    # 6/2
    pie_cz = 0.0    # centrado en Z  (fondo=4 → -2 a +2)

    draw_orthohedron(-5, pie_cy, pie_cz, 8, 4, 6, GREEN_MID,  hollow=True)
    draw_orthohedron(+5, pie_cy, pie_cz, 8, 4, 6, GREEN_DARK, hollow=True)

    # ── CUERPO ──────────────────────────────────────────────────────────────

    cuerpo_cy = 11.0
    draw_orthohedron(0, cuerpo_cy, pie_cz, 8, 4, 12, GREEN_LIGHT, hollow=True)

    # ── CABEZA ──────────────────────────────────────────────────────────────
    
    cabeza_cy = 21.0
    cabeza_cz = 0.0   # fondo=8 → -4 a +4
    draw_orthohedron(0, cabeza_cy, cabeza_cz, 8, 8, 8, GREEN_LIGHT, hollow=True)

    # ── CARA ────────────────────────────────────────────────────────────────
    draw_face(0, cabeza_cy, cabeza_cz, 8)


# CONFIGURACIÓN DE LUZ

def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION,  [1.0,  2.0,  2.0, 0.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT,   [0.35, 0.35, 0.35, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,   [0.85, 0.85, 0.85, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR,  [0.2,  0.2,  0.2,  1.0])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)


# PROYECCIONES

def set_ortho_projection(W, H, extent=30):
    """Proyección ortográfica paralela."""
    ratio = W / H if H > 0 else 1
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-extent * ratio, extent * ratio, -extent, extent, -200, 200)
    glMatrixMode(GL_MODELVIEW)


def set_perspective_projection(W, H):
    """Proyección en perspectiva cónica."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, W / H if H > 0 else 1, 0.1, 500.0)
    glMatrixMode(GL_MODELVIEW)


def set_oblique_cabinet_projection(W, H, extent=30):
    """
    Proyección paralela oblicua – gabinete.
    Se usa la proyección ortográfica base y se aplica una matriz de
    cizallamiento (shear) para simular la proyección de gabinete:
    factor = 0.5 (gabinete), ángulo = 45°
    """
    ratio = W / H if H > 0 else 1
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-extent * ratio, extent * ratio, -extent, extent, -200, 200)

    # Matriz de cizallamiento para proyección de gabinete
    f  = 0.5          # factor gabinete
    a  = math.radians(45)
    sx = -f * math.cos(a)
    sy = -f * math.sin(a)

    shear = [
        1,  0,  0,  0,
        0,  1,  0,  0,
        sx, sy, 1,  0,
        0,  0,  0,  1,
    ]
    glMultMatrixf(shear)
    glMatrixMode(GL_MODELVIEW)

# DIBUJO DE CADA VIEWPORT

WIN_W = 1000
WIN_H = 800

def draw_viewport(x, y, w, h, title,
                  proj_fn,
                  eye=(0, 12, 60), center=(0, 12, 0), up=(0, 1, 0)):
    """Configura viewport, proyección y dibuja el creeper."""
    glViewport(x, y, w, h)
    glScissor(x, y, w, h)
    glEnable(GL_SCISSOR_TEST)
    glClearColor(0.12, 0.12, 0.14, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    proj_fn(w, h)
    glLoadIdentity()
    gluLookAt(*eye, *center, *up)

    setup_lighting()
    draw_creeper()

    # Título del viewport
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, w, 0, h, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(0.9, 0.9, 0.9)
    glRasterPos2f(8, h - 18)
    for ch in title:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)


def display():
    global cam_angle_x, cam_angle_y, cam_zoom

    glClearColor(0.05, 0.05, 0.05, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    half_w = WIN_W // 2
    half_h = WIN_H // 2

    creeper_center = (0, 12, 0)   # centro aproximado del creeper

    # ── VP1 : Superior-Izquierda — Ortográfica Frontal (mirando desde Z+) ──
    draw_viewport(
        0, half_h, half_w, half_h,
        "Proyeccion Ortografica - Vista Frontal",
        lambda w, h: set_ortho_projection(w, h, 22),
        eye=(0, 12, 80), center=creeper_center, up=(0, 1, 0)
    )

    # ── VP2 : Superior-Derecha — Ortográfica Lateral Izquierda (desde X-) ──
    draw_viewport(
        half_w, half_h, half_w, half_h,
        "Proyeccion Ortografica - Vista Lateral Izquierda",
        lambda w, h: set_ortho_projection(w, h, 22),
        eye=(-80, 12, 0), center=creeper_center, up=(0, 1, 0)
    )

    # ── VP3 : Inferior-Izquierda — Perspectiva orbital (cámara libre) ──────
    glViewport(0, 0, half_w, half_h)
    glScissor(0, 0, half_w, half_h)
    glEnable(GL_SCISSOR_TEST)
    glClearColor(0.12, 0.12, 0.14, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_SCISSOR_TEST)

    set_perspective_projection(half_w, half_h)
    glLoadIdentity()
    glTranslatef(0, 0, -cam_zoom)
    glRotatef(cam_angle_x, 1, 0, 0)
    glRotatef(cam_angle_y, 0, 1, 0)
    glTranslatef(0, -12, 0)   # centrar creeper

    setup_lighting()
    draw_creeper()

    # Título VP3
    glDisable(GL_LIGHTING)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, half_w, 0, half_h, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(0.9, 0.9, 0.9)
    glRasterPos2f(8, half_h - 18)
    lbl = "Perspectiva Conica - Vista Orbital (drag para rotar)"
    for ch in lbl:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_LIGHTING)

    # ── VP4 : Inferior-Derecha — Oblicua Gabinete ───────────────────────────
    draw_viewport(
        half_w, 0, half_w, half_h,
        "Proyeccion Oblicua Gabinete - Vista Isometrica",
        lambda w, h: set_oblique_cabinet_projection(w, h, 22),
        eye=(0, 12, 80), center=creeper_center, up=(0, 1, 0)
    )

    # Líneas divisorias entre viewports
    glViewport(0, 0, WIN_W, WIN_H)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, WIN_W, 0, WIN_H, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glDisable(GL_LIGHTING)
    glColor3f(0.6, 0.6, 0.6)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex2f(half_w, 0);     glVertex2f(half_w, WIN_H)   # vertical
    glVertex2f(0, half_h);     glVertex2f(WIN_W, half_h)   # horizontal
    glEnd()
    glLineWidth(1.0)

    glutSwapBuffers()


# INTERACCIÓN RATÓN (sólo para el viewport de perspectiva, VP3)

def mouse_button(button, state, x, y):
    global last_x, last_y, mouse_btn
    last_x, last_y = x, y
    mouse_btn = button if state == GLUT_DOWN else None


def mouse_motion(x, y):
    global cam_angle_x, cam_angle_y, cam_zoom, last_x, last_y
    dx = x - last_x
    dy = y - last_y
    last_x, last_y = x, y

    # Solo actúa si el ratón está en el cuadrante inferior-izquierdo (VP3)
    half_w = WIN_W // 2
    half_h = WIN_H // 2
    if x > half_w or y < half_h:
        return

    if mouse_btn == GLUT_LEFT_BUTTON:
        cam_angle_y += dx * 0.5
        cam_angle_x += dy * 0.5
    elif mouse_btn == GLUT_RIGHT_BUTTON:
        cam_zoom = max(10, cam_zoom - dy * 0.3)

    glutPostRedisplay()

# TECLADO

def keyboard(key, x, y):
    if key == b'\x1b' or key == b'q':   # ESC o 'q' para salir
        sys.exit(0)
    glutPostRedisplay()

def reshape(w, h):
    global WIN_W, WIN_H
    WIN_W, WIN_H = w, h
    glutPostRedisplay()


# MAIN

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(100, 50)
    glutCreateWindow(b"Creeper OpenGL - 4 Viewports")

    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glEnable(GL_NORMALIZE)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse_button)
    glutMotionFunc(mouse_motion)
    glutKeyboardFunc(keyboard)

    print("=" * 55)
    print("  Creeper OpenGL – Controles")
    print("=" * 55)
    print("  Drag izq  (VP inferior-izq) : rotar vista orbital")
    print("  Drag der  (VP inferior-izq) : zoom")
    print("  ESC / q                     : salir")
    print("=" * 55)

    glutMainLoop()


if __name__ == "__main__":
    main()
