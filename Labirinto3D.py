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
    def __init__(self, largura=1240, altura=800):
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
        
        # Modelos TRI
        self.modelos_tri = {}  # Dicionário: nome -> lista de triângulos
        self.objetos_tri = []  # Lista de objetos TRI para renderizar
        
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
        
        # Dados de colisão baseado em imagem
        self.imagem_colisao = None
        self.dados_colisao = None

        # Jogador: velocidade e energia
        self.velocidade_jogador = 10.0
        self.energia = 100.0
        self.energia_max = 100.0
        self.consumo_por_segundo = 1.0
        self.pontos = 0

         # Escalas padrão para cada modelo TRI (ajuste conforme necessário)
        self.escalas_modelos = {
            'barrel': 0.01, #
            'well': 0.007, #
            'dead_tree_d': 0.005, # 
            'pine_c': 0.004, #
            'fountain_b': 0.0015, #
            'fire_cage': 0.015, #
            'box': 0.007, #
            'fence': 0.01, #
            'street_oil_light': 0.01, #
            'default': 0.01  # escala padrão para modelos não especificados
        }

        # Carregar modelos TRI
        self.carregarModeloTRI('TRI/barrel.tri', 'barrel')
        self.carregarModeloTRI('TRI/well.tri', 'well')
        self.carregarModeloTRI('TRI/dead_tree_d.tri', 'dead_tree_d')
        self.carregarModeloTRI('TRI/pine_c.tri', 'pine_c')
        self.carregarModeloTRI('TRI/fountain_b.tri', 'fountain_b')
        self.carregarModeloTRI('TRI/fire_cage.tri', 'fire_cage')
        self.carregarModeloTRI('TRI/box.tri', 'box')
        self.carregarModeloTRI('TRI/fence.tri', 'fence')
        self.carregarModeloTRI('TRI/street_oil_light.tri', 'street_oil_light')


        # Carregar mapa (isso pode definir self.posicao_jogador se o mapa tiver '3')
        self.carregarMapa("mapa_labirinto_texturas.txt")
        
        # Carregar texturas do piso
        self.carregarTexturasPiso()
        
        # Carregar imagem do mapa para colisão (usar como máscara)
        self.carregarImagemMapaColisao("mapa_labirinto.txt")
        
        # Carregar modelos TRI

        # Garantir que posicao_jogador exista (carregarMapa já define se tiver '3')
        if not hasattr(self, 'posicao_jogador') or self.posicao_jogador is None:
            self.posicao_jogador = np.array([1.5, 0.0, 1.5], dtype=float)

        # Agora instancia inimigos/cápsulas respeitando a posição do jogador
        self.instanciarInimigos(1)
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
                ganho = 40
                self.energia = min(self.energia + ganho, self.energia_max)
                self.pontos += 3
                print(f"[DEBUG] Cápsula idx={i} coletada: energia {antes} -> {self.energia} | pontos={self.pontos}")

                # remover do mundo (não haverá mais colisão)
                # self.capsulas.pop(i)

                # opcional: reposicionar ao invés de remover (comente pop e use reposicionarCapsula)
                self.reposicionarCapsula(i)

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

    def carregarImagemMapaColisao(self, nome_arquivo):
        """Carrega a imagem do mapa para usar como máscara de colisão baseada em cores"""
        try:
            # Tenta carregar como arquivo de imagem primeiro
            caminho_imagem = os.path.join(os.path.dirname(__file__), "mapa_labirinto_textura.png")
            if os.path.exists(caminho_imagem):
                self.imagem_colisao = Image.open(caminho_imagem)
                self.dados_colisao = np.array(self.imagem_colisao.convert('RGBA'))
                print(f"[OK] Imagem de colisão carregada: {caminho_imagem}")
                return
            else:
                print("[AVISO] Imagem de colisão não encontrada. Usando mapa textual como base.")
                # Usar o mapa de tipos de piso como referência
                self.imagem_colisao = None
                self.dados_colisao = None
        except Exception as e:
            print(f"[AVISO] Erro ao carregar imagem de colisão: {e}")
            self.imagem_colisao = None
            self.dados_colisao = None

    def ehPassavel(self, pos_x, pos_z):
        """
        Verifica se a posição é passável baseado na imagem ou no mapa.
        Retorna False se a posição é bloqueada (parede).
        """
        # Primeiro, verifica limites do mapa
        celula_x = int(pos_x)
        celula_z = int(pos_z)
        
        if celula_x < 0 or celula_x >= self.mapa_largura or celula_z < 0 or celula_z >= self.mapa_altura:
            return False
        
        # Se temos uma imagem de colisão com dados
        if self.dados_colisao is not None:
            # Mapear posição 3D para pixel na imagem
            img_height, img_width = self.dados_colisao.shape[:2]
            
            # Normalizar coordenadas para tamanho da imagem
            pixel_x = int((pos_x / self.mapa_largura) * img_width)
            pixel_z = int((pos_z / self.mapa_altura) * img_height)
            
            # Limpar limites de pixel
            pixel_x = max(0, min(pixel_x, img_width - 1))
            pixel_z = max(0, min(pixel_z, img_height - 1))
            
            # Verificar alfa (opacidade) - 0 = não passável, 255 = passável
            alpha = self.dados_colisao[pixel_z, pixel_x, 3]
            return alpha > 128  # Se opacidade > 50%, é passável
        
        # Fallback: usar o mapa de células
        return self.ehCelulaLivre(celula_x, celula_z)

    def carregarModeloTRI(self, caminho_arquivo, nome_modelo):
        """Carrega um modelo TRI (formato de triângulos) do arquivo"""
        try:
            if not os.path.exists(caminho_arquivo):
                print(f"[ERRO] Arquivo TRI não encontrado: {caminho_arquivo}")
                return False
            
            triangulos = []
            with open(caminho_arquivo, 'r') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha:
                        continue
                    
                    # Cada linha contém: x1 y1 z1  x2 y2 z2  x3 y3 z3  cor
                    partes = linha.split()
                    if len(partes) < 10:
                        continue
                    
                    try:
                        # Ler coordenadas dos 3 vértices
                        v1 = [float(partes[0]), float(partes[1]), float(partes[2])]
                        v2 = [float(partes[3]), float(partes[4]), float(partes[5])]
                        v3 = [float(partes[6]), float(partes[7]), float(partes[8])]
                        
                        # Ler cor (em hex)
                        cor_hex = partes[9] if len(partes) > 9 else "0xFFFFFF"
                        cor_int = int(cor_hex, 16)
                        r = ((cor_int >> 16) & 0xFF) / 255.0
                        g = ((cor_int >> 8) & 0xFF) / 255.0
                        b = (cor_int & 0xFF) / 255.0
                        cor = [r, g, b]
                        
                        triangulos.append({
                            'v1': v1, 'v2': v2, 'v3': v3, 'cor': cor
                        })
                    except:
                        continue
            
            self.modelos_tri[nome_modelo] = triangulos
            print(f"[OK] Modelo TRI carregado: {nome_modelo} ({len(triangulos)} triângulos)")
            return True
            
        except Exception as e:
            print(f"[ERRO] Falha ao carregar modelo TRI: {e}")
            return False

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
    # ...existing code...
    def carregarMapa(self, nome_arquivo):
        """Carrega o mapa do arquivo de texto, preservando as texturas definidas."""
        try:
            with open(nome_arquivo, 'r', encoding="utf-8") as f:
                linhas = f.readlines()

            # Remove comentários e linhas vazias
            linhas_validas = [l.split("#")[0].strip() for l in linhas]
            linhas_validas = [l for l in linhas_validas if l]

            # Lê dimensões
            largura, altura = map(int, linhas_validas[0].split())
            self.mapa_largura = largura
            self.mapa_altura = altura

            # Verifica se há linhas suficientes no arquivo para o mapa declarado
            if len(linhas_validas) < 1 + self.mapa_altura:
                print(f"[ERRO] Arquivo de mapa contém {len(linhas_validas)-1} linhas de mapa, esperado {self.mapa_altura}. Usando mapa padrão.")
                self.criarMapaPadrao()
                return

            self.mapa = []
            self.mapa_tipos_piso = []
            self.janelas = []
            self.portas = []
            self.objetos_estaticos = []
            self.capsulas = []

            posicao_inicial_encontrada = False

            # ------------------------
            # 💥 PARSER ROBUSTO 💥
            # Normaliza cada linha do mapa
            # ------------------------
            def normalizar(linha):
                linha = linha.replace("\t", " ")
                while "  " in linha:
                    linha = linha.replace("  ", " ")
                return linha.strip()

            # Processa linhas do mapa
            for y in range(self.mapa_altura):
                linha_raw = normalizar(linhas_validas[y + 1])
                tokens = linha_raw.split(" ")

                # Debug se der errado
                if len(tokens) != self.mapa_largura:
                    print(f"[ERRO] Linha {y} tem {len(tokens)} itens, esperado {self.mapa_largura}")
                    print("Linha:", linha_raw)

                linha_mapa = []
                linha_texturas = []

                for x, val in enumerate(tokens):
            # ...existing code...
                    # ----------------------------------------
                    # TIPO + TEXTURA (ex: "6:banner")
                    # ----------------------------------------
                    if ":" in val:
                        tipo_str, textura_str = val.split(":")
                        tipo_celula = int(tipo_str)
                        tipo_textura = 5  # textura default se não converter
                        try:
                            tipo_textura = int(textura_str)
                        except:
                            pass
                    else:
                        tipo_celula = int(val)
                        tipo_textura = 5  # padrão

                    # ----------------------------------------
                    # PROCESSAMENTO DAS CÉLULAS
                    # ----------------------------------------
                    if tipo_celula == 3:
                        self.posicao_jogador = np.array([x + 0.5, 0.85, y + 0.5], dtype=float)
                        linha_mapa.append(1)
                        posicao_inicial_encontrada = True

                    elif tipo_celula in (1, 2):
                        linha_mapa.append(tipo_celula)

                    elif tipo_celula == 4:  # janela
                        self.janelas.append({'x': x, 'y': y, 'altura': self.ALTURA_JANELA})
                        linha_mapa.append(1)

                    elif tipo_celula == 5:  # porta
                        self.portas.append({'x': x, 'y': y, 'altura': self.ALTURA_PORTA})
                        linha_mapa.append(1)

                    elif tipo_celula == 6:  # objeto estático
                        modelo = None
                        if ":" in val:
                            _, modelo = val.split(":", 1)
                            modelo = modelo.strip()

                        if not modelo:
                            print(f"[AVISO] Objeto estático sem modelo na célula ({x},{y})")
                            modelo = "default"

                        self.objetos_estaticos.append({
                            'x': x,
                            'y': y,
                            'tipo': modelo
                        })
                        linha_mapa.append(1)

                    elif tipo_celula == 7:  # cápsula
                        self.capsulas.append({'x': x + 0.5, 'y': 0.0, 'z': y + 0.5})
                        linha_mapa.append(1)

                    else:
                        linha_mapa.append(tipo_celula)

                    linha_texturas.append(tipo_textura)

                self.mapa.append(linha_mapa)
                self.mapa_tipos_piso.append(linha_texturas)

            # Caso não ache posição inicial
            if not posicao_inicial_encontrada:
                print("Aviso: Nenhuma posição inicial (3) encontrada no mapa!")
                self.posicao_jogador = np.array([1.5, 0.85, 1.5], dtype=float)

            print(f"Mapa carregado: {self.mapa_largura}x{self.mapa_altura}")

            print("DEBUG tamanho real do mapa:")
            for i, linha in enumerate(self.mapa):
                print(i, "tamanho:", len(linha))
            print("Dimensões declaradas:", self.mapa_largura, "x", self.mapa_altura)

            # Converte os objetos para TRI
            self.converterObjetosEstaticosParaTRI()

        except FileNotFoundError:
            print(f"Erro: Arquivo {nome_arquivo} não encontrado!")
            self.criarMapaPadrao()

        except Exception as e:
            print(f"Erro ao carregar mapa: {e}")
            self.criarMapaPadrao()

    # ...existing code...
    def converterObjetosEstaticosParaTRI(self):
        """Cria instâncias TRI dependendo do tipo definido no mapa, aplicando a escala correta."""
        self.objetos_tri = []

        # 1. Obter a escala padrão para usar como fallback
        escala_default = self.escalas_modelos.get('default', 1.0) # 1.0 é um fallback seguro

        for obj in self.objetos_estaticos:
            modelo = obj['tipo']  # usa o nome definido no mapa (ex: 'barrel', 'banner')

            # Se o modelo não existe nos modelos carregados, ignora.
            if modelo not in self.modelos_tri:
                print(f"[AVISO] Modelo TRI '{modelo}' não carregado. Ignorando.")
                continue

            # 2. Obter a escala específica para este modelo.
            #    Se o modelo não estiver no dicionário, usa a escala padrão.
            escala_aplicada = self.escalas_modelos.get(modelo, escala_default)

            # 3. Adicionar o objeto à lista de renderização com a escala correta
            self.objetos_tri.append({
                'modelo': modelo,
                'x': obj['x'] + 0.5,
                'y': 0.0,
                'z': obj['y'] + 0.5,
                'escala': escala_aplicada  # <-- **Ajuste aqui: Usa a escala do dicionário**
            })

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
        # Verifica se as coordenadas estão dentro dos limites do mapa
        if x < 0 or x >= self.mapa_largura or y < 0 or y >= self.mapa_altura:
            return False  # Retorna False se fora dos limites
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
            
            # 1. Verificar se há uma JANELA nesta célula (bloqueia)
            eh_janela = any(janela['x'] == celula_x and janela['y'] == celula_z for janela in self.janelas)
            if eh_janela:
                return True

            # 2. Verificar se há um OBJETO ESTÁTICO nesta célula (bloqueia)
            eh_objeto = any(obj['x'] == celula_x and obj['y'] == celula_z for obj in self.objetos_estaticos)
            if eh_objeto:
                return True
            
            # 3. Verificar se há uma PORTA nesta célula (passável)
            eh_porta = any(porta['x'] == celula_x and porta['y'] == celula_z for porta in self.portas)
            if eh_porta:
                continue
            
            # 4. Verificar se é passável pela imagem/mapa (chão)
            if not self.ehPassavel(px, pz):
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
        
        # Desenhar modelos TRI (objetos estáticos + qualquer outro objeto TRI)
        for obj_tri in self.objetos_tri:
            self.desenharModeloTRI(obj_tri)
        
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
        """Nota: Objetos estáticos agora são renderizados como TRI models via desenharModeloTRI()"""
        pass  # Todos os objetos estáticos foram adicionados à lista objetos_tri em converterObjetosEstaticosParaTRI()

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
                self.pontos -= 5
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
        """
        Desenha um personagem estilizado (humano/animal híbrido) em 3ª pessoa.
        Usa formas simples (cilindros/esferas) para um visual limpo e facilmente ajustável.
        """
        # animação simples (bobbing)
        t = pygame.time.get_ticks() / 1000.0
        bob = math.sin(t * 3.0) * 0.04  # amplitude pequena

        # posição e orientação do jogador
        glPushMatrix()
        glTranslatef(self.posicao_jogador[0], self.posicao_jogador[1] + bob, self.posicao_jogador[2])
        glRotatef(self.angulo_rotacao, 0, 1, 0)

        # QUADRIC reutilizável
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)

        # --- Perna esquerda ---
        glPushMatrix()
        glTranslatef(-0.18, 0.3, 0.0)      # posição do quadril esquerdo
        glRotatef(-10, 1, 0, 0)
        glColor3f(0.15, 0.15, 0.6)         # cor da roupa/pele
        gluCylinder(quad, 0.09, 0.09, 0.55, 12, 4)
        glTranslatef(0.0, 0.0, 0.55)
        gluSphere(quad, 0.10, 10, 8)       # pé
        glPopMatrix()

        # --- Perna direita ---
        glPushMatrix()
        glTranslatef(0.18, 0.3, 0.0)
        glRotatef(-10, 1, 0, 0)
        glColor3f(0.15, 0.15, 0.6)
        gluCylinder(quad, 0.09, 0.09, 0.55, 12, 4)
        glTranslatef(0.0, 0.0, 0.55)
        gluSphere(quad, 0.10, 10, 8)
        glPopMatrix()

        # --- Tronco (torso) ---
        glPushMatrix()
        glTranslatef(0.0, 0.8, 0.0)
        glRotatef(-90, 1, 0, 0)            # cilindro eixo Z->Y
        glColor3f(0.2, 0.6, 0.9)           # camisa/pele
        gluCylinder(quad, 0.32, 0.28, 0.7, 16, 4)
        glPopMatrix()

        # --- Cabeça ---
        glPushMatrix()
        glTranslatef(0.0, 1.6, 0.0)
        glColor3f(1.0, 0.85, 0.7)          # tom de pele
        gluSphere(quad, 0.28, 18, 16)
        # olhos (pequenas esferas)
        glPushMatrix()
        glTranslatef(0.12, 0.05, 0.22)
        glColor3f(0.0, 0.0, 0.0)
        gluSphere(quad, 0.04, 8, 8)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.12, 0.05, 0.22)
        glColor3f(0.0, 0.0, 0.0)
        gluSphere(quad, 0.04, 8, 8)
        glPopMatrix()

        # orelhas/orelha (dando um toque animal)
        glPushMatrix()
        glTranslatef(0.18, 0.26, 0.0)
        glRotatef(-40, 0, 0, 1)
        glColor3f(1.0, 0.85, 0.7)
        gluCylinder(quad, 0.06, 0.0, 0.18, 10, 2)  # mini-cone (orelha)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.18, 0.26, 0.0)
        glRotatef(40, 0, 0, 1)
        glColor3f(1.0, 0.85, 0.7)
        gluCylinder(quad, 0.06, 0.0, 0.18, 10, 2)
        glPopMatrix()

        glPopMatrix()  # final cabeça & seus filhos

        # --- Braço esquerdo (antebraço+mão) ---
        glPushMatrix()
        glTranslatef(-0.42, 1.05, 0.0)
        glRotatef(10, 0, 0, 1)
        glColor3f(0.15, 0.15, 0.6)
        gluCylinder(quad, 0.07, 0.06, 0.45, 12, 4)
        glTranslatef(0.0, 0.0, 0.45)
        gluSphere(quad, 0.06, 8, 6)
        glPopMatrix()

        # --- Braço direito ---
        glPushMatrix()
        glTranslatef(0.42, 1.05, 0.0)
        glRotatef(-10, 0, 0, 1)
        glColor3f(0.15, 0.15, 0.6)
        gluCylinder(quad, 0.07, 0.06, 0.45, 12, 4)
        glTranslatef(0.0, 0.0, 0.45)
        gluSphere(quad, 0.06, 8, 6)
        glPopMatrix()

        # --- Cauda curta (elemento animal) ---
        glPushMatrix()
        glTranslatef(0.0, 1.0, -0.34)
        glRotatef(-55, 1, 0, 0)
        glColor3f(0.15, 0.15, 0.15)
        gluCylinder(quad, 0.05, 0.02, 0.4, 10, 2)
        glPopMatrix()

        # limpar
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
                gluLookAt(centro_x, 80, centro_z + 5,
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

    def desenharModeloTRI(self, obj_tri):
        """Desenha um modelo TRI na posição e escala especificada"""
        nome_modelo = obj_tri['modelo']
        if nome_modelo not in self.modelos_tri:
            return
        
        triangulos = self.modelos_tri[nome_modelo]
        
        glPushMatrix()
        glTranslatef(obj_tri['x'], obj_tri['y'], obj_tri['z'])
        glScalef(obj_tri['escala'], obj_tri['escala'], obj_tri['escala'])
        
        glBegin(GL_TRIANGLES)
        for tri in triangulos:
            # Vértice 1
            glColor3f(*tri['cor'])
            glVertex3f(tri['v1'][0], tri['v1'][1], tri['v1'][2])
            
            # Vértice 2
            glColor3f(*tri['cor'])
            glVertex3f(tri['v2'][0], tri['v2'][1], tri['v2'][2])
            
            # Vértice 3
            glColor3f(*tri['cor'])
            glVertex3f(tri['v3'][0], tri['v3'][1], tri['v3'][2])
        glEnd()
        
        glPopMatrix()

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
