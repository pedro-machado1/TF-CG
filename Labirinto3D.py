#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Labirinto 3D com OpenGL
Trabalho II - Fundamentos de Computação Gráfica
Desenvolvido em Python com OpenGL
"""

from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *
import math
import numpy as np
from collections import deque

class Labirinto3D:
    def __init__(self, largura=1200, altura=800):
        pygame.init()
        self.largura = largura
        self.altura = altura
        self.display = (largura, altura)
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Configurar OpenGL
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Labirinto 3D - Navegação em Primeira e Terceira Pessoa")
        
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.15, 1.0)
        
        # Variáveis do mapa
        self.mapa = []
        self.mapa_largura = 0
        self.mapa_altura = 0
        self.carregarMapa("mapa_labirinto.txt")
        
        # Dimensões do labirinto
        self.TAMANHO_CELULA = 1.0  # 1 metro
        self.ALTURA_PAREDE = 2.7
        self.ESPESSURA_PAREDE = 0.25
        self.ALTURA_JOGADOR = 1.7
        
        # Posição e rotação do jogador
        self.posicao_jogador = np.array([1.5, 0.0, 1.5], dtype=float)
        self.angulo_rotacao = 0.0  # Rotação em graus
        self.velocidade_jogador = 8.0  # m/s
        self.movimento_ativo = True  # Sempre ativo
        self.espaco_pressionado = False  # Para movimento com espaço
        
        # Câmera - COMEÇAR EM TERCEIRA PESSOA
        self.modo_camera = 1  # 0=primeira pessoa, 1=terceira pessoa
        self.alvo_camera = 1  # 0=centro do mapa, 1=jogador
        
        # Estados de controle
        self.running = True
        self.tempo_anterior = 0
        
        print(f"Jogador iniciado em: {self.posicao_jogador}")
    def carregarMapa(self, nome_arquivo):
        """Carrega o mapa do arquivo de texto"""
        try:
            with open(nome_arquivo, 'r') as f:
                linhas = f.readlines()
            
            # Ignorar linhas de comentário e linhas vazias
            linhas_validas = [l.strip() for l in linhas if l.strip() and not l.strip().startswith('#')]
            
            # Primeira linha válida contém dimensões
            dimensoes = linhas_validas[0].split()
            self.mapa_largura = int(dimensoes[0])
            self.mapa_altura = int(dimensoes[1])
            
            # Carregar mapa
            self.mapa = []
            posicao_inicial_encontrada = False
            
            for y in range(self.mapa_altura):
                linha = linhas_validas[y + 1].split()
                linha_mapa = [int(x) for x in linha]
                self.mapa.append(linha_mapa)
                
                # Procurar pelo 3 (posição inicial)
                for x in range(self.mapa_largura):
                    if linha_mapa[x] == 3:
                        self.posicao_jogador = np.array([x + 0.5, 0.85, y + 0.5], dtype=float)
                        self.mapa[y][x] = 1  # Converter para corredor
                        posicao_inicial_encontrada = True
                        print(f"Posição inicial encontrada em: ({x}, {y}) -> {self.posicao_jogador}")
            
            if not posicao_inicial_encontrada:
                print("Aviso: Nenhuma posição inicial (3) encontrada no mapa!")
                self.posicao_jogador = np.array([1.5, 0.85, 1.5], dtype=float)
            
            print(f"Mapa carregado: {self.mapa_largura}x{self.mapa_altura}")
            
        except FileNotFoundError:
            print(f"Erro: Arquivo {nome_arquivo} não encontrado!")
            self.criarMapaPadrao()
        except Exception as e:
            print(f"Erro ao carregar mapa: {e}")
            self.criarMapaPadrao()

    def criarMapaPadrao(self):
        """Cria um mapa padrão se o arquivo não existir"""
        self.mapa_largura = 10
        self.mapa_altura = 10
        self.mapa = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 3, 1, 1, 1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 1, 1, 1, 1, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        self.posicao_jogador = np.array([1.5, 0.0, 1.5], dtype=float)
    
    def ehCelulaLivre(self, x, y):
        """Verifica se uma célula do mapa é livre (corredor ou sala)"""
        if x < 0 or x >= self.mapa_largura or y < 0 or y >= self.mapa_altura:
            return False
        celula = self.mapa[int(y)][int(x)]
        # 1=corredor, 2=sala, 3=posição inicial (convertida pra 1)
        return celula in [1, 2, 3]
    
    def verificarColisao(self, pos_x, pos_z):
        """Verifica colisão com paredes"""
        # Verificar raio de colisão (20cm)
        raio_colisao = 0.2
        
        # Verificar 4 pontos ao redor da posição
        pontos = [
            (pos_x, pos_z),
            (pos_x + raio_colisao, pos_z),
            (pos_x - raio_colisao, pos_z),
            (pos_x, pos_z + raio_colisao),
            (pos_x, pos_z - raio_colisao),
        ]
        
        for px, pz in pontos:
            celula_x = int(px)
            celula_z = int(pz)
            if not self.ehCelulaLivre(celula_x, celula_z):
                return True
        return False
    
    def atualizarMovimento(self, dt):
        """Atualiza a posição do jogador baseado no movimento"""
        if dt <= 0 or not self.espaco_pressionado:
            return
            
        # Calcular deslocamento
        deslocamento = self.velocidade_jogador * dt
        rad = math.radians(self.angulo_rotacao)
        
        # Movimento para frente (quando espaço está pressionado)
        nova_x = self.posicao_jogador[0] + deslocamento * math.sin(rad)
        nova_z = self.posicao_jogador[2] + deslocamento * math.cos(rad)
        
        if not self.verificarColisao(nova_x, nova_z):
            self.posicao_jogador[0] = nova_x
            self.posicao_jogador[2] = nova_z

    def desenharParede(self, x, z, altura, espessura, face_norte=True, face_sul=True, 
                       face_leste=True, face_oeste=True):
        """Desenha uma parede em uma posição específica do mapa"""
        # Centro da célula
        cx = x + 0.5
        cz = z + 0.5
        tamanho = self.TAMANHO_CELULA
        esp = espessura / 2
        
        glColor3f(0.7, 0.7, 0.7)
        
        # Face frente (eixo Z negativo)
        if face_norte:
            glBegin(GL_QUADS)
            glVertex3f(cx - tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx + tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz - tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz - tamanho/2)
            glEnd()
        
        # Face trás (eixo Z positivo)
        if face_sul:
            glBegin(GL_QUADS)
            glVertex3f(cx + tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx - tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz + tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz + tamanho/2)
            glEnd()
        
        # Face esquerda (eixo X negativo)
        if face_oeste:
            glBegin(GL_QUADS)
            glVertex3f(cx - tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx - tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz - tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz + tamanho/2)
            glEnd()
        
        # Face direita (eixo X positivo)
        if face_leste:
            glBegin(GL_QUADS)
            glVertex3f(cx + tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx + tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz + tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz - tamanho/2)
            glEnd()
    
    def desenharLabirinto(self):
        """Desenha o labirinto completo"""
        # Desenhar piso
        glColor3f(0.5, 0.5, 0.5)
        glBegin(GL_QUADS)
        glVertex3f(0, -0.1, 0)
        glVertex3f(self.mapa_largura, -0.1, 0)
        glVertex3f(self.mapa_largura, -0.1, self.mapa_altura)
        glVertex3f(0, -0.1, self.mapa_altura)
        glEnd()
        
        # Desenhar paredes
        for y in range(self.mapa_altura):
            for x in range(self.mapa_largura):
                if self.mapa[y][x] == 0:  # Parede
                    self.desenharParede(x, y, self.ALTURA_PAREDE, self.ESPESSURA_PAREDE)
    
    def desenharJogador(self):
        """Desenha o personagem do jogador com corpo e cabeça"""
        glPushMatrix()
        glTranslatef(self.posicao_jogador[0], self.posicao_jogador[1], self.posicao_jogador[2])
        glRotatef(self.angulo_rotacao, 0, 1, 0)
        
        # Corpo (cilindro azul)
        glColor3f(0.0, 0.5, 1.0)
        glPushMatrix()
        glTranslatef(0, 0.6, 0)
        quad = GLUquadric()
        gluCylinder(quad, 0.2, 0.2, 0.6, 16, 16)  # Corpo
        glPopMatrix()
        
        # Cabeça (esfera vermelha)
        glColor3f(1.0, 0.2, 0.2)
        glPushMatrix()
        glTranslatef(0, 1.3, 0)
        quad = GLUquadric()
        gluSphere(quad, 0.25, 16, 16)  # Cabeça
        glPopMatrix()
        
        # Olho (pequena esfera preta na frente)
        glColor3f(0.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0, 1.35, 0.2)
        quad = GLUquadric()
        gluSphere(quad, 0.08, 8, 8)  # Olho
        glPopMatrix()
        
        # Seta de direção (cone amarelo apontando para frente)
        glColor3f(1.0, 1.0, 0.0)
        glPushMatrix()
        glTranslatef(0, 0.5, 0.4)
        glRotatef(90, 1, 0, 0)

        # Criar o quadric
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluQuadricTexture(quad, False)

        # Cone (base = 0.12, topo = 0.0, altura = 0.3)
        gluCylinder(quad, 0.12, 0.0, 0.3, 16, 16)

        glPopMatrix()

        
        glPopMatrix()

    def configurarPerspectiva(self):
        """Configura a perspectiva da câmera"""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.largura / self.altura), 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        if self.modo_camera == 0:  # Primeira pessoa
            # Câmera na altura dos olhos do jogador
            camera_x = self.posicao_jogador[0]
            camera_y = self.posicao_jogador[1] + self.ALTURA_JOGADOR
            camera_z = self.posicao_jogador[2]
            
            rad = math.radians(self.angulo_rotacao)
            alvo_x = camera_x + math.sin(rad) * 5
            alvo_z = camera_z + math.cos(rad) * 5
            
            gluLookAt(camera_x, camera_y, camera_z,
                     alvo_x, camera_y, alvo_z,
                     0, 1, 0)
        
        else:  # Terceira pessoa
            if self.alvo_camera == 1:  # Câmera segue o jogador
                camera_x = self.posicao_jogador[0] - math.sin(math.radians(self.angulo_rotacao)) * 8
                camera_y = self.posicao_jogador[1] + 5
                camera_z = self.posicao_jogador[2] - math.cos(math.radians(self.angulo_rotacao)) * 8
                
                gluLookAt(camera_x, camera_y, camera_z,
                         self.posicao_jogador[0], self.posicao_jogador[1] + 1, self.posicao_jogador[2],
                         0, 1, 0)
            else:  # Câmera fixa no centro
                centro_x = self.mapa_largura / 2
                centro_z = self.mapa_altura / 2
                gluLookAt(centro_x, 15, centro_z + 10,
                         centro_x, 0, centro_z,
                         0, 1, 0)
    
    def procesarEventos(self):
        """Processa eventos do teclado e mouse"""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.running = False
            
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.running = False
                
                elif evento.key == pygame.K_1:
                    self.modo_camera = 0
                    print("Câmera: Primeira Pessoa")
                
                elif evento.key == pygame.K_2:
                    self.modo_camera = 1
                    print("Câmera: Terceira Pessoa")
                
                elif evento.key == pygame.K_3:
                    self.alvo_camera = (self.alvo_camera + 1) % 2
                    alvo = "Centro do Mapa" if self.alvo_camera == 0 else "Jogador"
                    print(f"Alvo da Câmera: {alvo}")
                
                elif evento.key == pygame.K_SPACE:
                    self.espaco_pressionado = True
            
            elif evento.type == pygame.KEYUP:
                if evento.key == pygame.K_SPACE:
                    self.espaco_pressionado = False
        
        # Verificar teclas pressionadas para rotação
        teclas = pygame.key.get_pressed()
        
        if teclas[pygame.K_LEFT]:
            self.angulo_rotacao += 3
        if teclas[pygame.K_RIGHT]:
            self.angulo_rotacao -= 3

    def desenharHUD(self):
        """Desenha informações na tela"""
        # Mudar para modo ortho para desenhar texto
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.largura, self.altura, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        
        # Aqui você poderia adicionar texto usando pygame.font
        # Por enquanto, apenas restauramos o estado
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
    
    def executar(self):
        """Loop principal do programa"""
        print("\n=== LABIRINTO 3D ===")
        print("Controles:")
        print("  BARRA DE ESPAÇO - Avançar")
        print("  SETA ESQUERDA/DIREITA - Girar")
        print("  1 - Câmera em Primeira Pessoa")
        print("  2 - Câmera em Terceira Pessoa")
        print("  3 - Alternar alvo da câmera")
        print("  ESC - Sair")
        print("================\n")
        
        while self.running:
            self.procesarEventos()
            
            # Calcular delta time
            tempo_atual = pygame.time.get_ticks() / 1000.0
            dt = tempo_atual - self.tempo_anterior
            self.tempo_anterior = tempo_atual
            
            if dt > 0.05:  # Limitar para evitar saltos grandes
                dt = 0.05
            
            # Atualizar lógica
            self.atualizarMovimento(dt)
            
            # Limpar tela
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Configurar câmera
            self.configurarPerspectiva()
            
            # Desenhar cena
            self.desenharLabirinto()
            self.desenharJogador()
            self.desenharHUD()
            
            # Atualizar display
            pygame.display.flip()
            self.clock.tick(self.fps)
        
        pygame.quit()
        print("\nPrograma encerrado!")

def main():
    jogo = Labirinto3D()
    jogo.executar()

if __name__ == "__main__":
    main()
