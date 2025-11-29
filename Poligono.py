import sys

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

from Ponto import Ponto

class Poligono:
    def __init__(self):
        self.Vertices = []
        self.color = (1.0, 1.0, 1.0)

    def addPoint(self, p: Ponto):
        self.Vertices.append(p)

    # Compatibilidade com seus métodos antigos
    def insereVertice(self, p):
        self.Vertices.append(p)

    def insereVerticePos(self, p, pos):
        if pos < 0 or pos > len(self.Vertices):
            return
        self.Vertices.insert(pos, p)

    def getVertice(self, i):
        return self.Vertices[i]

    # Desenha preenchido
    def pintaPoligono(self):
        glColor3f(*self.color)
        glBegin(GL_POLYGON)
        for v in self.Vertices:
            glVertex3f(v.x, v.y, v.z)
        glEnd()

    # Desenha linhas (wireframe)
    def desenhaPoligono(self):
        glColor3f(*self.color)
        glBegin(GL_LINE_LOOP)
        for v in self.Vertices:
            glVertex3f(v.x, v.y, v.z)
        glEnd()

    def draw(self):
        """Desenho compatível com o código do Labirinto."""
        glColor3f(*self.color)
        glBegin(GL_POLYGON)
        for v in self.Vertices:
            glVertex3f(v.x, v.y, v.z)
        glEnd()

    def desenhaVertices(self):
        glBegin(GL_POINTS)
        for v in self.Vertices:
            glVertex3f(v.x, v.y, v.z)
        glEnd()

    def imprime(self):
        for v in self.Vertices:
            v.imprime()

    def getNVertices(self):
        return len(self.Vertices)

    def obtemLimites(self):
        if not self.Vertices:
            return None, None

        Min = Max = self.Vertices[0]
        for v in self.Vertices:
            Min = self.obtemMinimo(v, Min)
            Max = self.obtemMaximo(v, Max)
        return Min, Max

    def obtemMinimo(self, p1, p2):
        return Ponto(min(p1.x, p2.x), min(p1.y, p2.y), min(p1.z, p2.z))

    def obtemMaximo(self, p1, p2):
        return Ponto(max(p1.x, p2.x), max(p1.y, p2.y), max(p1.z, p2.z))

    def LePoligono3D(self, nome):
        try:
            with open(nome, 'r') as input_file:
                qtd = int(input_file.readline())
                for _ in range(qtd):
                    x, y, z = map(float, input_file.readline().split())
                    self.insereVertice(Ponto(x, y, z))
        except FileNotFoundError:
            print(f"Erro ao abrir {nome}.")
            sys.exit(0)

    def getAresta(self, n):
        P1 = self.Vertices[n]
        n1 = (n + 1) % len(self.Vertices)
        P2 = self.Vertices[n1]
        return P1, P2

    def desenhaAresta(self, n):
        P1, P2 = self.getAresta(n)
        glBegin(GL_LINES)
        glVertex3f(P1.x, P1.y, P1.z)
        glVertex3f(P2.x, P2.y, P2.z)
        glEnd()

    def alteraVertice(self, i, P):
        self.Vertices[i] = P

    def imprimeVertices(self):
        for v in self.Vertices:
            v.imprime("", "\n")
