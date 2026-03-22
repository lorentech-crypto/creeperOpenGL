import math
import sys
try:
    from OpenGL.GL    import *
    from OpenGL.GLU   import *
    from OpenGL.GLUT  import *
except ImportError:
    raise SystemExit("¡Ups! Necesitas instalar PyOpenGL: pip install PyOpenGL PyOpenGL_accelerate")

# --- AJUSTES VISUALES (Colores del Creeper) ---
GREEN_LIGHT  = (0.18, 0.70, 0.18)
GREEN_DARK   = (0.08, 0.42, 0.08)
GREEN_MID    = (0.12, 0.55, 0.12)
BLACK_FACE   = (0.05, 0.05, 0.05)

# --- ESTADO DE LA CÁMARA (Para la vista libre) ---
cam_angle_x, cam_angle_y = 20.0, -40.0
cam_zoom = 40.0
last_x = last_y = 0
mouse_btn = None

# --- DIBUJO DE PIEZAS BÁSICAS ---

def draw_cube(color):
    """ Dibuja un cubo de 1x1x1. Es nuestro 'átomo' de construcción. """
    r, g, b = color
    glColor3f(r, g, b)

    # Definimos las 6 caras del cubo
    faces = [
        ([0,0,1],  [(-.5,-.5, .5), (.5,-.5, .5), (.5, .5, .5), (-.5, .5, .5)]), # Frontal
        ([0,0,-1], [( .5,-.5,-.5), (-.5,-.5,-.5), (-.5, .5,-.5), ( .5, .5,-.5)]), # Trasera
        ([0,1,0],  [(-.5, .5,-.5), ( .5, .5,-.5), ( .5, .5, .5), (-.5, .5, .5)]), # Superior
        ([0,-1,0], [(-.5,-.5, .5), ( .5,-.5, .5), ( .5,-.5,-.5), (-.5,-.5,-.5)]), # Inferior
        ([1,0,0],  [( .5,-.5, .5), ( .5,-.5,-.5), ( .5, .5,-.5), ( .5, .5, .5)]), # Derecha
        ([-1,0,0], [(-.5,-.5,-.5), (-.5,-.5, .5), (-.5, .5, .5), (-.5, .5,-.5)])  # Izquierda
    ]

    glBegin(GL_QUADS)
    for normal, verts in faces:
        glNormal3fv(normal)
        for v in verts: glVertex3fv(v)
    glEnd()

    # Le ponemos un borde negro para que se note el estilo 'pixel art'
    glColor3f(0, 0, 0)
    glBegin(GL_LINES)
    # (Simplificado: dibujamos los bordes principales)
    for a, b in [((-0.5,-0.5,0.5),(0.5,-0.5,0.5)), ((-0.5,0.5,0.5),(0.5,0.5,0.5))]: # etc.
        glVertex3fv(a); glVertex3fv(b)
    glEnd()

def draw_block(cx, cy, cz, W, D, H, color):
    """ Crea un bloque grande (como el cuerpo) uniendo cubitos pequeños. """
    ox, oy, oz = cx - W/2 + 0.5, cy - H/2 + 0.5, cz - D/2 + 0.5
    for ix in range(W):
        for iy in range(H):
            for iz in range(D):
                # Solo dibujamos la 'cáscara' para que el PC no sufra
                if ix in (0, W-1) or iy in (0, H-1) or iz in (0, D-1):
                    glPushMatrix()
                    glTranslatef(ox + ix, oy + iy, oz + iz)
                    draw_cube(color)
                    glPopMatrix()

# --- CONSTRUCCIÓN DEL CREEPER ---

def draw_creeper():
    # Pies: dos bloques de 8x4x6
    draw_block(-5, 3, 0, 8, 4, 6, GREEN_MID)
    draw_block( 5, 3, 0, 8, 4, 6, GREEN_DARK)

    # Cuerpo: un bloque alargado de 8x4x12
    draw_block(0, 11, 0, 8, 4, 12, GREEN_LIGHT)

    # Cabeza: un cubo de 8x8x8
    draw_block(0, 21, 0, 8, 8, 8, GREEN_LIGHT)

    # Cara: Ojos y boca (láminas negras pegadas al frente)
    z_face = 4.01 
    parts = [(-2, 22.5), (-1, 22.5), (1, 22.5), (2, 22.5), # Ojos
             (0, 20.5), (-1, 19.5), (0, 19.5), (1, 19.5)] # Boca simple
    
    for (x, y) in parts:
        glPushMatrix()
        glTranslatef(x, y, z_face)
        glScalef(1, 1, 0.05)
        draw_cube(BLACK_FACE)
        glPopMatrix()

# --- MANEJO DE VISTAS (PROYECCIONES) ---

def set_projection(w, h, type="ortho"):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = w/h if h>0 else 1
    
    if type == "ortho":
        glOrtho(-30*aspect, 30*aspect, -30, 30, -100, 100)
    elif type == "persp":
        gluPerspective(45, aspect, 0.1, 500)
    elif type == "oblique":
        glOrtho(-30*aspect, 30*aspect, -30, 30, -100, 100)
        # Matriz de cizallamiento para el efecto "Gabinete"
        shear = [1,0,0,0,  0,1,0,0,  -0.35,-0.35,1,0,  0,0,0,1]
        glMultMatrixf(shear)
    glMatrixMode(GL_MODELVIEW)

# --- DIBUJO PRINCIPAL (VIEWPORTS) ---

WIN_W, WIN_H = 1000, 800

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    w, h = WIN_W // 2, WIN_H // 2

    # 1. Vista Frontal (Arriba Izq)
    glViewport(0, h, w, h)
    set_projection(w, h, "ortho")
    glLoadIdentity()
    gluLookAt(0, 12, 50, 0, 12, 0, 0, 1, 0)
    draw_creeper()

    # 2. Vista Lateral (Arriba Der)
    glViewport(w, h, w, h)
    set_projection(w, h, "ortho")
    glLoadIdentity()
    gluLookAt(-50, 12, 0, 0, 12, 0, 0, 1, 0)
    draw_creeper()

    # 3. Vista Orbital Interactiva (Abajo Izq)
    glViewport(0, 0, w, h)
    set_projection(w, h, "persp")
    glLoadIdentity()
    glTranslatef(0, 0, -cam_zoom)
    glRotatef(cam_angle_x, 1, 0, 0)
    glRotatef(cam_angle_y, 0, 1, 0)
    glTranslatef(0, -12, 0)
    draw_creeper()

    # 4. Vista Gabinete (Abajo Der)
    glViewport(w, 0, w, h)
    set_projection(w, h, "oblique")
    glLoadIdentity()
    gluLookAt(0, 12, 50, 0, 12, 0, 0, 1, 0)
    draw_creeper()

    glutSwapBuffers()

# --- CONTROLES Y MAIN ---

def mouse_motion(x, y):
    global cam_angle_x, cam_angle_y, last_x, last_y
    if x < WIN_W//2 and y > WIN_H//2: # Solo si el mouse está en el cuadrante 3
        cam_angle_y += (x - last_x) * 0.5
        cam_angle_x += (y - last_y) * 0.5
    last_x, last_y = x, y
    glutPostRedisplay()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Mundo Creeper: 4 Proyecciones")
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_COLOR_MATERIAL)
    
    # Sencilla luz para dar volumen
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [10, 20, 20, 1])

    glutDisplayFunc(display)
    glutMotionFunc(mouse_motion)
    glutMainLoop()

if __name__ == "__main__":
    main()