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
from PIL import Image
import os

class Labirinto3D:
    def __init__(self, largura=1200, altura=800):
        pygame.init()
        self.largura = largura
        self.altura = altura
        self.display = (largura, altura)
        self.clock = pygame.time.Clock()
        self.fps = 60

        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Labirinto 3D - Navegação")

        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.15, 1.0)

        # Dimensões e constantes
        self.TAMANHO_CELULA = 1.0
        self.ALTURA_PAREDE = 2.7
        self.ESPESSURA_PAREDE = 0.25
        self.ALTURA_JOGADOR = 1.7

        self.ALTURA_JANELA = 1.0
        self.ALTURA_PORTA = 2.1
        self.ALTURA_BASE_JANELA = 0.9

        # Estado do mundo
        self.mapa = []
        self.mapa_largura = 0
        self.mapa_altura = 0
        self.janelas = []
        self.portas = []
        self.inimigos = []
        self.objetos_estaticos = []
        self.capsulas = []
        
        # Texturas do piso
        self.texturas_piso = {}  # Dicionário: tipo_piso -> ID_textura_OpenGL
        self.mapa_tipos_piso = []  # Armazena o tipo de textura para cada célula
        self.nomes_texturas = {
            0: 'CROSS.png',
            1: 'DL.png',
            2: 'DLR.png',
            3: 'DR.png',
            4: 'LR.png',
            5: 'None.png',
            6: 'UD.png',
            7: 'UDL.png',
            8: 'UDR.png',
            9: 'UL.png',
            10: 'ULR.png',
            11: 'UR.png'
        }

        # Jogador: velocidade e energia
        self.velocidade_jogador = 10.0
        self.energia = 100.0
        self.energia_max = 100.0
        self.consumo_por_segundo = 1.0
        self.pontos = 0

        # Carregar mapa (isso pode definir self.posicao_jogador se o mapa tiver '3')
        self.carregarMapa("mapa_labirinto_texturas.txt")
        
        # Carregar texturas do piso
        self.carregarTexturasPiso()

        # Garantir que posicao_jogador exista (carregarMapa já define se tiver '3')
        if not hasattr(self, 'posicao_jogador') or self.posicao_jogador is None:
            self.posicao_jogador = np.array([1.5, 0.0, 1.5], dtype=float)

        # Agora instancia inimigos/cápsulas respeitando a posição do jogador
        self.instanciarInimigos(0)
        self.instanciarCapsulas(10)

        # Posição/rot. final do jogador (já garantida acima)
        # self.posicao_jogador = np.array([1.5, 0.0, 1.5], dtype=float)  # removido (não sobrescrever)

        self.angulo_rotacao = 0.0
        self.velocidade_jogador = 8.0
        self.movimento_ativo = True
        self.espaco_pressionado = False

        self.modo_camera = 1
        self.alvo_camera = 1

        self.running = True
        self.tempo_anterior = 0

        print(f"Jogador iniciado em: {self.posicao_jogador}")

    # --------------------- captura de cápsulas (corrigida) ---------------------
    def verificarCapturaCapsulas(self):
        """
        Verifica e processa captura de cápsulas:
         - itera de trás pra frente para poder remover elementos com segurança
         - usa raio de captura razoável (ajustável)
         - atualiza energia e pontos, remove cápsula da lista
        """
        jogador_x = self.posicao_jogador[0]
        jogador_z = self.posicao_jogador[2]

        raio_captura = 1  # <- ajuste aqui se quiser menor/maior

        # iterar de trás para frente para permitir pop sem quebrar o loop
        for i in range(len(self.capsulas) - 1, -1, -1):
            cap = self.capsulas[i]
            dx = jogador_x - cap["x"]
            dz = jogador_z - cap["z"]
            dist = math.hypot(dx, dz)

            if dist <= raio_captura:
                # efeito da cápsula
                antes = self.energia
                ganho = 30
                self.energia = min(self.energia + ganho, self.energia_max)
                self.pontos += 1
                print(f"[DEBUG] Cápsula idx={i} coletada: energia {antes} -> {self.energia} | pontos={self.pontos}")

                # remover do mundo (não haverá mais colisão)
                self.capsulas.pop(i)

                # opcional: reposicionar ao invés de remover (comente pop e use reposicionarCapsula)
                # self.reposicionarCapsula(i)

                # não retorna; permite coletar múltiplas cápsulas no mesmo frame
        # fim verificarCapturaCapsulas

    # --------------------- funções de instanciação e utilitários ---------------------
    def instanciarInimigos(self, quantidade):
        import random
        self.inimigos = []
        livres = []
        jogador_cel = (int(self.posicao_jogador[0]), int(self.posicao_jogador[2]))

        for y in range(self.mapa_altura):
            for x in range(self.mapa_largura):
                if self.ehCelulaLivre(x, y) and (x, y) != jogador_cel:
                    livres.append((x, y))

        caps = set((int(c['x']), int(c['z'])) for c in self.capsulas)
        livres = [p for p in livres if p not in caps]

        random.shuffle(livres)
        for i in range(quantidade):
            if i < len(livres):
                pos = livres[i]
                self.inimigos.append({
                    'x': pos[0] + 0.5,
                    'y': 0.0,
                    'z': pos[1] + 0.5
                })

    def escolherCelulaLivreAleatoria(self):
        import random
        def _inner(avoid_positions=None):
            livres = []
            for yy in range(self.mapa_altura):
                for xx in range(self.mapa_largura):
                    if self.ehCelulaLivre(xx, yy):
                        if avoid_positions and (xx, yy) in avoid_positions:
                            continue
                        livres.append((xx, yy))
            if not livres:
                return None
            return random.choice(livres)
        return _inner

    def instanciarCapsulas(self, quantidade):
        import random
        chooser = self.escolherCelulaLivreAleatoria()
        while len(self.capsulas) < quantidade:
            avoid = set()
            jogador_cel = (int(self.posicao_jogador[0]), int(self.posicao_jogador[2]))
            avoid.add(jogador_cel)

            for c in self.capsulas:
                avoid.add((int(c['x']), int(c['z'])))

            for inim in self.inimigos:
                avoid.add((int(inim['x']), int(inim['z'])))

            cel = chooser(avoid_positions=avoid)
            if cel is None:
                break

            self.capsulas.append({
                'x': cel[0] + 0.5,
                'y': 0.0,
                'z': cel[1] + 0.5
            })

    def carregarTexturasPiso(self):
        """Carrega as texturas PNG do diretório TexturaAsfalto/ para uso no piso"""
        caminho_texturas = os.path.join(os.path.dirname(__file__), "TexturaAsfalto")
        
        if not os.path.exists(caminho_texturas):
            print(f"[AVISO] Diretório de texturas não encontrado: {caminho_texturas}")
            return
        
        for tipo_id, nome_arquivo in self.nomes_texturas.items():
            caminho_completo = os.path.join(caminho_texturas, nome_arquivo)
            
            if not os.path.exists(caminho_completo):
                print(f"[AVISO] Arquivo de textura não encontrado: {caminho_completo}")
                continue
            
            try:
                # Carregar imagem com PIL
                img = Image.open(caminho_completo).convert("RGBA")
                img_data = img.tobytes()
                
                # Criar textura OpenGL
                textura_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, textura_id)
                
                # Definir parâmetros de textura
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                
                # Enviar dados da textura para GPU
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
                
                # Armazenar ID da textura
                self.texturas_piso[tipo_id] = textura_id
                print(f"[OK] Textura carregada: {nome_arquivo} (tipo {tipo_id})")
                
            except Exception as e:
                print(f"[ERRO] Falha ao carregar textura {nome_arquivo}: {e}")

    def reposicionarCapsula(self, idx):
        """Move a cápsula de índice idx para outra célula livre aleatória"""
        chooser = self.escolherCelulaLivreAleatoria()
        # Evitar jogador, outras cápsulas e inimigos
        avoid = set()
        jogador_cel = (int(self.posicao_jogador[0]), int(self.posicao_jogador[2]))
        avoid.add(jogador_cel)
        for i, c in enumerate(self.capsulas):
            if i == idx:
                continue
            avoid.add((int(c['x']), int(c['z'])))
        for inim in self.inimigos:
            avoid.add((int(inim['x']), int(inim['z'])))

        cel = chooser(avoid_positions=avoid)
        if cel:
            self.capsulas[idx]['x'] = cel[0] + 0.5
            self.capsulas[idx]['z'] = cel[1] + 0.5
            return True
        return False

    def reposicionarInimigoAleatorio(self, inimigo):
        chooser = self.escolherCelulaLivreAleatoria()
        avoid = set()
        jogador_cel = (int(self.posicao_jogador[0]), int(self.posicao_jogador[2]))
        avoid.add(jogador_cel)
        for c in self.capsulas:
            avoid.add((int(c['x']), int(c['z'])))
        for inim in self.inimigos:
            if inim is inimigo:
                continue
            avoid.add((int(inim['x']), int(inim['z'])))

        cel = chooser(avoid_positions=avoid)
        if cel:
            inimigo['x'] = cel[0] + 0.5
            inimigo['z'] = cel[1] + 0.5

    # --------------------- carregamento / criação de mapa ---------------------
    def carregarMapa(self, nome_arquivo):
        """Carrega o mapa do arquivo de texto, preservando as texturas definidas."""
        try:
            with open(nome_arquivo, 'r') as f:
                linhas = f.readlines()
            linhas_validas = [l.strip() for l in linhas if l.strip() and not l.strip().startswith('#')]
            dimensoes = linhas_validas[0].split()
            self.mapa_largura = int(dimensoes[0])
            self.mapa_altura = int(dimensoes[1])
            self.mapa = []
            self.mapa_tipos_piso = [] 
            posicao_inicial_encontrada = False
            self.janelas = []
            self.portas = []
            self.objetos_estaticos = []
            self.capsulas = []
            
            for y in range(self.mapa_altura):
                linha = linhas_validas[y + 1].split()
                linha_mapa = []
                linha_texturas = []
                
                for x, val in enumerate(linha):
                    # 1. TENTA LER A TEXTURA DO ARQUIVO
                    if ':' in val:
                        tipo_celula, tipo_textura_str = val.split(':')
                        tipo_celula = int(tipo_celula)
                        tipo_textura = int(tipo_textura_str) # Usa a textura do arquivo
                    else:
                        tipo_celula = int(val)
                        tipo_textura = 5  # Usa padrão APENAS se não houver definição
                    
                    # 2. PROCESSA O TIPO DE CÉLULA
                    # (Removidos os "tipo_textura = 5" que causavam o bug)
                    
                    if tipo_celula == 3:
                        self.posicao_jogador = np.array([x + 0.5, 0.85, y + 0.5], dtype=float)
                        linha_mapa.append(1) 
                        posicao_inicial_encontrada = True
                        print(f"Posição inicial encontrada em: ({x}, {y})")
                        
                    elif tipo_celula == 1 or tipo_celula == 2:
                        linha_mapa.append(tipo_celula)
                        
                    elif tipo_celula == 4:
                        self.janelas.append({'x': x, 'y': y, 'altura': self.ALTURA_JANELA})
                        linha_mapa.append(1)
                        
                    elif tipo_celula == 5:
                        self.portas.append({'x': x, 'y': y, 'altura': self.ALTURA_PORTA})
                        linha_mapa.append(1)
                        
                    elif tipo_celula == 6:
                        self.objetos_estaticos.append({'x': x, 'y': y, 'tipo': 'obj'})
                        linha_mapa.append(1)
                        
                    elif tipo_celula == 7:
                        self.capsulas.append({'x': x + 0.5, 'y': 0.0, 'z': y + 0.5})
                        linha_mapa.append(1) # Converte para chão físico
                        
                    else:
                        linha_mapa.append(tipo_celula)
                    
                    # 3. GRAVA A TEXTURA FINAL (Seja a lida do arquivo ou a padrão)
                    linha_texturas.append(tipo_textura)
                
                self.mapa.append(linha_mapa)
                self.mapa_tipos_piso.append(linha_texturas)
            
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
        # Criar mapa de tipos de textura (5 = padrão)
        self.mapa_tipos_piso = []
        for y in range(self.mapa_altura):
            linha_texturas = [5 if self.mapa[y][x] in [1, 2, 3] else 0 for x in range(self.mapa_largura)]
            self.mapa_tipos_piso.append(linha_texturas)
        self.posicao_jogador = np.array([1.5, 0.0, 1.5], dtype=float)

    # --------------------- colisões / movimentos / desenho (restante) ---------------------
    def ehCelulaLivre(self, x, y):
        if x < 0 or x >= self.mapa_largura or y < 0 or y >= self.mapa_altura:
            return False
        celula = self.mapa[int(y)][int(x)]
        return celula in [1, 2, 3]

    def verificarColisao(self, pos_x, pos_z):
        raio_colisao = 0.2
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
        if dt <= 0:
            return
        if not self.espaco_pressionado:
            return
        if self.energia <= 0:
            return

        deslocamento = self.velocidade_jogador * dt
        rad = math.radians(self.angulo_rotacao)

        nova_x = self.posicao_jogador[0] + deslocamento * math.sin(rad)
        nova_z = self.posicao_jogador[2] + deslocamento * math.cos(rad)

        self.energia -= self.consumo_por_segundo * dt
        if self.energia < 0:
            self.energia = 0

        if not self.verificarColisao(nova_x, nova_z):
            self.posicao_jogador[0] = nova_x
            self.posicao_jogador[2] = nova_z

    def desenharPisoComTexturas(self):
        """Desenha o piso de cada célula livre com textura correspondente"""
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        
        for y in range(self.mapa_altura):
            for x in range(self.mapa_largura):
                # Desenhar apenas célula livre (corredor ou sala)
                if not self.ehCelulaLivre(x, y):
                    continue
                
                # Obter tipo de textura para esta célula
                tipo_texto = self.mapa_tipos_piso[y][x] if y < len(self.mapa_tipos_piso) and x < len(self.mapa_tipos_piso[y]) else 5
                
                # Obter ID da textura OpenGL
                textura_id = self.texturas_piso.get(tipo_texto, None)
                
                # Sempre habilitar e fazer bind da textura antes de desenhar
                if textura_id is not None:
                    glBindTexture(GL_TEXTURE_2D, textura_id)
                    glEnable(GL_TEXTURE_2D)
                    glColor3f(1.0, 1.0, 1.0)  # Branco (não modula cor)
                else:
                    # Fallback: desenhar sem textura em cinza
                    glDisable(GL_TEXTURE_2D)
                    glColor3f(0.5, 0.5, 0.5)
                
                # Desenhar quadrado (célula) no plano XZ (altura Y = 0)
                cx = x + 0.5
                cz = y + 0.5
                tamanho = self.TAMANHO_CELULA / 2.0
                
                glBegin(GL_QUADS)
                # Textura: (0,0) no canto inferior-esquerdo, (1,1) no canto superior-direito
                glTexCoord2f(0.0, 0.0); glVertex3f(cx - tamanho, 0.01, cz - tamanho)
                glTexCoord2f(1.0, 0.0); glVertex3f(cx + tamanho, 0.01, cz - tamanho)
                glTexCoord2f(1.0, 1.0); glVertex3f(cx + tamanho, 0.01, cz + tamanho)
                glTexCoord2f(0.0, 1.0); glVertex3f(cx - tamanho, 0.01, cz + tamanho)
                glEnd()
        
        glDisable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)  # Resetar cor

    def desenharParede(self, x, z, altura, espessura, face_norte=True, face_sul=True,
                       face_leste=True, face_oeste=True):
        cx = x + 0.5
        cz = z + 0.5
        tamanho = self.TAMANHO_CELULA
        esp = espessura / 2
        glColor3f(0.7, 0.7, 0.7)
        if face_norte:
            glBegin(GL_QUADS)
            glVertex3f(cx - tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx + tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz - tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz - tamanho/2)
            glEnd()
        if face_sul:
            glBegin(GL_QUADS)
            glVertex3f(cx + tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx - tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz + tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz + tamanho/2)
            glEnd()
        if face_oeste:
            glBegin(GL_QUADS)
            glVertex3f(cx - tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx - tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz - tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz + tamanho/2)
            glEnd()
        if face_leste:
            glBegin(GL_QUADS)
            glVertex3f(cx + tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx + tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz + tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz - tamanho/2)
            glEnd()

    def desenharLabirinto(self):
        # Desenhar piso com texturas
        self.desenharPisoComTexturas()
        
        # Desenhar paredes
        for y in range(self.mapa_altura):
            for x in range(self.mapa_largura):
                if self.mapa[y][x] == 0:
                    self.desenharParede(x, y, self.ALTURA_PAREDE, self.ESPESSURA_PAREDE)
        
        # Desenhar janelas
        for janela in self.janelas:
            self.desenharJanela(janela['x'], janela['y'], janela['altura'])
        
        # Desenhar portas
        for porta in self.portas:
            self.desenharPorta(porta['x'], porta['y'], porta['altura'])
        
        # Desenhar objetos estáticos
        for obj in self.objetos_estaticos:
            self.desenharObjetoEstatico(obj['x'], obj['y'])
        for cap in self.capsulas:
            self.desenharCapsula(cap)
        for inimigo in self.inimigos:
            self.desenharInimigo(inimigo)

    def desenharInimigo(self, inimigo):
        glPushMatrix()
        glTranslatef(inimigo['x'], inimigo['y'] + 0.5, inimigo['z'])
        glColor3f(1.0, 0.0, 0.0)
        quad = gluNewQuadric()
        gluSphere(quad, 0.4, 16, 16)
        glPopMatrix()

    def desenharCapsula(self, cap):
        glPushMatrix()
        glTranslatef(cap['x'], cap['y'] + 0.2, cap['z'])
        glColor3f(0.0, 1.0, 0.0)
        quad = gluNewQuadric()
        gluSphere(quad, 0.2, 12, 12)
        glPopMatrix()

    def desenharObjetoEstatico(self, x, y):
        cx = x + 0.5
        cz = y + 0.5
        glPushMatrix()
        glTranslatef(cx, 0.0, cz)
        glColor3f(0.6, 0.4, 0.2)
        tamanho = 0.2
        glBegin(GL_QUADS)
        glVertex3f(-tamanho, 0.4, -tamanho)
        glVertex3f(tamanho, 0.4, -tamanho)
        glVertex3f(tamanho, 0.4, tamanho)
        glVertex3f(-tamanho, 0.4, tamanho)
        # Frente
        glVertex3f(-tamanho, 0.0, -tamanho)
        glVertex3f(tamanho, 0.0, -tamanho)
        glVertex3f(tamanho, 0.4, -tamanho)
        glVertex3f(-tamanho, 0.4, -tamanho)
        # Costas
        glVertex3f(tamanho, 0.0, tamanho)
        glVertex3f(-tamanho, 0.0, tamanho)
        glVertex3f(-tamanho, 0.4, tamanho)
        glVertex3f(tamanho, 0.4, tamanho)
        # Laterais
        glVertex3f(-tamanho, 0.0, tamanho)
        glVertex3f(-tamanho, 0.0, -tamanho)
        glVertex3f(-tamanho, 0.4, -tamanho)
        glVertex3f(-tamanho, 0.4, tamanho)
        glVertex3f(tamanho, 0.0, -tamanho)
        glVertex3f(tamanho, 0.0, tamanho)
        glVertex3f(tamanho, 0.4, tamanho)
        glVertex3f(tamanho, 0.4, -tamanho)
        glEnd()
        glPopMatrix()

    def atualizarInimigos(self, dt):
        velocidade = 20.0
        for inimigo in self.inimigos:
            dx = self.posicao_jogador[0] - inimigo['x']
            dz = self.posicao_jogador[2] - inimigo['z']
            dist = (dx**2 + dz**2) ** 0.5
            if dist < 0.7:
                quantidade_roubada = 20.0
                roubado = min(self.energia, quantidade_roubada)
                self.energia -= roubado
                self.pontos -= 10
                self.reposicionarInimigoAleatorio(inimigo)
                continue
            if dist > 0.01:
                dir_x = dx / dist
                dir_z = dz / dist
                novo_x = inimigo['x'] + dir_x * velocidade * dt
                novo_z = inimigo['z'] + dir_z * velocidade * dt
                if self.ehCelulaLivre(int(novo_x), int(novo_z)):
                    inimigo['x'] = novo_x
                    inimigo['z'] = novo_z
                else:
                    if self.ehCelulaLivre(int(novo_x), int(inimigo['z'])):
                        inimigo['x'] = novo_x
                    elif self.ehCelulaLivre(int(inimigo['x']), int(novo_z)):
                        inimigo['z'] = novo_z

    def desenharJanela(self, x, y, altura_janela):
        cx = x + 0.5
        cz = y + 0.5
        tamanho = self.TAMANHO_CELULA
        esp = self.ESPESSURA_PAREDE / 2
        base = self.ALTURA_BASE_JANELA
        h = altura_janela
        glColor3f(0.2, 0.7, 1.0)
        glBegin(GL_QUADS)
        glVertex3f(cx - tamanho/2, base, cz - tamanho/2 + esp)
        glVertex3f(cx + tamanho/2, base, cz - tamanho/2 + esp)
        glVertex3f(cx + tamanho/2, base + h, cz - tamanho/2 + esp)
        glVertex3f(cx - tamanho/2, base + h, cz - tamanho/2 + esp)
        glEnd()

    def desenharPorta(self, x, y, altura_porta):
        cx = x + 0.5
        cz = y + 0.5
        tamanho = self.TAMANHO_CELULA
        esp = self.ESPESSURA_PAREDE / 2
        h = altura_porta
        glColor3f(0.7, 0.5, 0.2)
        glBegin(GL_QUADS)
        glVertex3f(cx - tamanho/2, 0, cz - tamanho/2 + esp)
        glVertex3f(cx + tamanho/2, 0, cz - tamanho/2 + esp)
        glVertex3f(cx + tamanho/2, h, cz - tamanho/2 + esp)
        glVertex3f(cx - tamanho/2, h, cz - tamanho/2 + esp)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(cx + tamanho/2, 0, cz + tamanho/2 - esp)
        glVertex3f(cx - tamanho/2, 0, cz + tamanho/2 - esp)
        glVertex3f(cx - tamanho/2, h, cz + tamanho/2 - esp)
        glVertex3f(cx + tamanho/2, h, cz + tamanho/2 - esp)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(cx + tamanho/2 - esp, 0, cz - tamanho/2)
        glVertex3f(cx + tamanho/2 - esp, 0, cz + tamanho/2)
        glVertex3f(cx + tamanho/2 - esp, h, cz + tamanho/2)
        glVertex3f(cx + tamanho/2 - esp, h, cz - tamanho/2)
        glEnd()
        glBegin(GL_QUADS)
        glVertex3f(cx - tamanho/2 + esp, 0, cz + tamanho/2)
        glVertex3f(cx - tamanho/2 + esp, 0, cz - tamanho/2)
        glVertex3f(cx - tamanho/2 + esp, h, cz - tamanho/2)
        glVertex3f(cx - tamanho/2 + esp, h, cz + tamanho/2)
        glEnd()

    def desenharJogador(self):
        glPushMatrix()
        glTranslatef(self.posicao_jogador[0], self.posicao_jogador[1], self.posicao_jogador[2])
        glRotatef(self.angulo_rotacao, 0, 1, 0)
        glColor3f(0.0, 0.5, 1.0)
        glPushMatrix()
        glTranslatef(0, 0.6, 0)
        quad = GLUquadric()
        gluCylinder(quad, 0.2, 0.2, 0.6, 16, 16)
        glPopMatrix()
        glColor3f(1.0, 0.2, 0.2)
        glPushMatrix()
        glTranslatef(0, 1.3, 0)
        quad = GLUquadric()
        gluSphere(quad, 0.25, 16, 16)
        glPopMatrix()
        glColor3f(0.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0, 1.35, 0.2)
        quad = GLUquadric()
        gluSphere(quad, 0.08, 8, 8)
        glPopMatrix()
        glColor3f(1.0, 1.0, 0.0)
        glPushMatrix()
        glTranslatef(0, 0.5, 0.4)
        glRotatef(90, 1, 0, 0)
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluQuadricTexture(quad, False)
        gluCylinder(quad, 0.12, 0.0, 0.3, 16, 16)
        glPopMatrix()
        glPopMatrix()

    def configurarPerspectiva(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.largura / self.altura), 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        if self.modo_camera == 0:
            camera_x = self.posicao_jogador[0]
            camera_y = self.posicao_jogador[1] + self.ALTURA_JOGADOR
            camera_z = self.posicao_jogador[2]
            rad = math.radians(self.angulo_rotacao)
            alvo_x = camera_x + math.sin(rad) * 5
            alvo_z = camera_z + math.cos(rad) * 5
            gluLookAt(camera_x, camera_y, camera_z, alvo_x, camera_y, alvo_z, 0, 1, 0)
        else:
            if self.alvo_camera == 1:
                camera_x = self.posicao_jogador[0] - math.sin(math.radians(self.angulo_rotacao)) * 8
                camera_y = self.posicao_jogador[1] + 5
                camera_z = self.posicao_jogador[2] - math.cos(math.radians(self.angulo_rotacao)) * 8
                gluLookAt(camera_x, camera_y, camera_z,
                          self.posicao_jogador[0], self.posicao_jogador[1] + 1, self.posicao_jogador[2],
                          0, 1, 0)
            else:
                centro_x = self.mapa_largura / 2
                centro_z = self.mapa_altura / 2
                gluLookAt(centro_x, 15, centro_z + 10,
                          centro_x, 0, centro_z, 0, 1, 0)

    def procesarEventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.running = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.running = False
                elif evento.key == pygame.K_1:
                    self.modo_camera = 0
                elif evento.key == pygame.K_2:
                    self.modo_camera = 1
                elif evento.key == pygame.K_3:
                    self.alvo_camera = (self.alvo_camera + 1) % 2
                elif evento.key == pygame.K_SPACE:
                    self.espaco_pressionado = True
            elif evento.type == pygame.KEYUP:
                if evento.key == pygame.K_SPACE:
                    self.espaco_pressionado = False

        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]:
            self.angulo_rotacao += 3
        if teclas[pygame.K_RIGHT]:
            self.angulo_rotacao -= 3

    def desenharHUD(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.largura, self.altura, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        try:
            glPushAttrib(GL_ENABLE_BIT)
            glDisable(GL_TEXTURE_2D)
            barra_x = 10
            barra_y = 5
            barra_larg = 200
            barra_alt = 16
            frac = 0.0
            try:
                frac = max(0.0, min(1.0, float(self.energia) / float(self.energia_max)))
            except Exception:
                frac = 0.0
            glColor3f(0.2, 0.2, 0.2)
            glBegin(GL_QUADS)
            glVertex2f(barra_x, barra_y)
            glVertex2f(barra_x + barra_larg, barra_y)
            glVertex2f(barra_x + barra_larg, barra_y + barra_alt)
            glVertex2f(barra_x, barra_y + barra_alt)
            glEnd()
            glColor3f(0.0, 1.0, 0.0)
            glBegin(GL_QUADS)
            glVertex2f(barra_x + 2, barra_y + 2)
            glVertex2f(barra_x + 2 + (barra_larg - 4) * frac, barra_y + 2)
            glVertex2f(barra_x + 2 + (barra_larg - 4) * frac, barra_y + barra_alt - 2)
            glVertex2f(barra_x + 2, barra_y + barra_alt - 2)
            glEnd()
            glPopAttrib()
            font = pygame.font.SysFont(None, 24)
            texto = f"Energia: {int(self.energia)}  Pontos: {self.pontos}"
            surf = font.render(texto, True, (255, 255, 255))
            surf = surf.convert_alpha()
            w, h = surf.get_size()
            data = pygame.image.tostring(surf, "RGBA", True)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glRasterPos2i(10, 20)
            glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, data)
            glDisable(GL_BLEND)
        except Exception:
            pass
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)

    def executar(self):
        print("\n=== LABIRINTO 3D ===")
        print("Controles: BARRA - Avançar | ESQ/DIR - Girar | 1/2 - Câmera | ESC - Sair")
        while self.running:
            self.procesarEventos()
            tempo_atual = pygame.time.get_ticks() / 1000.0
            dt = tempo_atual - self.tempo_anterior
            self.tempo_anterior = tempo_atual
            if dt > 0.05:
                dt = 0.05
            self.atualizarMovimento(dt)
            self.atualizarInimigos(dt)
            # verificar captura (chamada corrigida)
            self.verificarCapturaCapsulas()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.configurarPerspectiva()
            self.desenharLabirinto()
            self.desenharJogador()
            self.desenharHUD()
            pygame.display.flip()
            self.clock.tick(self.fps)
        pygame.quit()
        print("\nPrograma encerrado!")

def main():
    jogo = Labirinto3D()
    jogo.executar()

if __name__ == "__main__":
    main()
