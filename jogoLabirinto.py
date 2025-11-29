from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import time
import math
import numpy as npy
from PIL import Image
import os
import random

class Labirinto3D:
    def __init__(self, largura=1240, altura=800):
        self.largura = largura
        self.altura = altura
        self.tempo_anterior = time.time()
        self.running = True

        # Configuração inicial do OpenGL/GLUT
        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
        glutInitWindowSize(self.largura, self.altura)
        glutInitWindowPosition(10, 0)
        glutCreateWindow(b"Labirinto 3D")

        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.15, 1.0)

        # Definições de tamanho do mundo
        self.TAMANHO_CELULA = 1.0
        self.ALTURA_PAREDE = 2.7
        self.ESPESSURA_PAREDE = 0.25
        self.ALTURA_JANELA = 1.0
        self.ALTURA_PORTA = 2.1
        self.ALTURA_BASE_JANELA = 0.9

        # Estado do mundo e objetos
        self.mapa = []
        self.mapa_largura = 0
        self.mapa_altura = 0
        self.janelas = []
        self.portas = []
        self.inimigos = []
        self.objetos_estaticos = []
        self.capsulas = []
        self.modelos_tri = {}  
        self.objetos_tri = []  
        self.texturas_piso = {}  
        self.mapa_tipos_piso = []  
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
        
        # Estado do jogador
        self.energia = 100.0
        self.pontos = 0
        self.posicao_jogador = npy.array([0.5, 0.85, 0.5], dtype=float)

        # Escalas dos modelos 3D
        self.escalas_modelos = {
            'barrel': 0.01, 'well': 0.007, 'dead_tree_d': 0.005, 'pine_c': 0.004, 
            'fountain_b': 0.0015, 'fire_cage': 0.015, 'box': 0.007, 'fence': 0.01, 
            'street_oil_light': 0.01 , "tent_a": 0.005
        }

        # Carrega modelos 3D
        self.carregarModeloTRI('TRI/barrel.tri', 'barrel')
        self.carregarModeloTRI('TRI/well.tri', 'well')
        self.carregarModeloTRI('TRI/dead_tree_d.tri', 'dead_tree_d')
        self.carregarModeloTRI('TRI/pine_c.tri', 'pine_c')
        self.carregarModeloTRI('TRI/fountain_b.tri', 'fountain_b')
        self.carregarModeloTRI('TRI/fire_cage.tri', 'fire_cage')
        self.carregarModeloTRI('TRI/box.tri', 'box')
        self.carregarModeloTRI('TRI/fence.tri', 'fence')
        self.carregarModeloTRI('TRI/street_oil_light.tri', 'street_oil_light')
        self.carregarModeloTRI('TRI/tent_a.tri', 'tent_a')

        # Carrega mapa e texturas
        self.carregarMapa("mapa_labirinto_texturas.txt")
        self.carregarTexturasPiso()
        
        # Instancia elementos dinâmicos
        self.instanciarInimigos(10)
        self.instanciarCapsulas(10)

        # Controles e câmera
        self.angulo_rotacao = 0.0
        self.movimento_ativo = True
        self.espaco_pressionado = False
        self.modo_camera = 1
        self.alvo_camera = 1

        # Configura callbacks GLUT
        glutDisplayFunc(self.loopPrincipal)
        glutIdleFunc(self.loopPrincipal)
        glutKeyboardFunc(self.teclaNormal)
        
        try:
            glutKeyboardUpFunc(self.teclaNormalSolta)
        except Exception:
            pass
        glutSpecialFunc(self.teclaEspecial)
        glutReshapeFunc(self.reshape)

    # Lida com pressionar de teclas normais
    def teclaNormal(self, key, x, y):
        if key == b'\x1b':
            try:
                glutLeaveMainLoop()
            except Exception:
                os._exit(0)
        elif key == b' ':
            self.espaco_pressionado = True
        elif key == b'1':
            self.modo_camera = 0
        elif key == b'2':
            self.modo_camera = 1
        elif key == b'3':
            self.alvo_camera = (self.alvo_camera + 1) % 2

    # Lida com soltar de teclas normais
    def teclaNormalSolta(self, key, x, y):
        if key == b' ':
            self.espaco_pressionado = False

    # Lida com teclas especiais (setas)
    def teclaEspecial(self, key, x, y):
        if key == GLUT_KEY_LEFT:
            self.angulo_rotacao += 3
        elif key == GLUT_KEY_RIGHT:
            self.angulo_rotacao -= 3

    # Lida com redimensionamento da janela
    def reshape(self, w, h):
        if h == 0:
            h = 1
        self.largura = w
        self.altura = h
        glViewport(0, 0, w, h)

    # Coleta cápsulas de energia
    def verificarCapturaCapsulas(self):
        jogador_x = self.posicao_jogador[0]
        jogador_z = self.posicao_jogador[2]
        for i in range(len(self.capsulas) - 1, -1, -1):
            cap = self.capsulas[i]
            dx = jogador_x - cap["x"]
            dz = jogador_z - cap["z"]
            dist = math.hypot(dx, dz)
            if dist <= 1:
                ganho = 50
                self.energia = min(self.energia + ganho, 100.0)
                self.pontos += 3
                self.reposicionarCapsula(i)

    # Posiciona inimigos em células livres
    def instanciarInimigos(self, quantidade):
        self.inimigos = []
        livres = []
        jogador_cel = (int(self.posicao_jogador[0]), int(self.posicao_jogador[2]))
        for y in range(self.mapa_altura):
            for x in range(self.mapa_largura):
                if self.livre(x, y) and (x, y) != jogador_cel:
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

    # Seleciona uma célula livre aleatória
    def escolherCelulaLivreAleatoria(self, avoid_positions=None):
            livres = []
            for y in range(self.mapa_altura):
                for x in range(self.mapa_largura):
                    if self.livre(x, y):
                        if avoid_positions and (x, y) in avoid_positions:
                            continue
                        livres.append((x, y))
            if not livres:
                return None
            return random.choice(livres)

    # Posiciona cápsulas
    def instanciarCapsulas(self, quantidade):
        while len(self.capsulas) < quantidade:
            avoid = set()
            jogador_cel = (int(self.posicao_jogador[0]), int(self.posicao_jogador[2]))
            avoid.add(jogador_cel)
            for c in self.capsulas:
                avoid.add((int(c['x']), int(c['z'])))
            for inim in self.inimigos:
                avoid.add((int(inim['x']), int(inim['z'])))
            cel = self.escolherCelulaLivreAleatoria(avoid_positions=avoid)
            if cel is None:
                break
            self.capsulas.append({
                'x': cel[0] + 0.5,
                'y': 0.0,
                'z': cel[1] + 0.5
            })

    # Carrega as texturas do piso
    def carregarTexturasPiso(self):
        caminho_texturas = os.path.join(os.path.dirname(__file__), "TexturaAsfalto")
        for tipo_id, nome_arquivo in self.nomes_texturas.items():
            caminho_completo = os.path.join(caminho_texturas, nome_arquivo)
            if not os.path.exists(caminho_completo):
                continue
            img = Image.open(caminho_completo).convert("RGBA")
            img_data = img.tobytes()
            textura_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, textura_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            self.texturas_piso[tipo_id] = textura_id

    # Verifica se a posição é passável
    def ehPassavel(self, pos_x, pos_z):
        if int(pos_x) < 0 or int(pos_x) >= self.mapa_largura or int(pos_z) < 0 or int(pos_z) >= self.mapa_altura:
            return False        
        return self.livre(int(pos_x), int(pos_z))

    # Carrega modelo TRI
    def carregarModeloTRI(self, caminho_arquivo, nome_modelo):
        try:
            if not os.path.exists(caminho_arquivo):
                return False
            triangulos = []
            with open(caminho_arquivo, 'r') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha:
                        continue
                    partes = linha.split()
                    if len(partes) < 10:
                        continue
                    try:
                        v1 = [float(partes[0]), float(partes[1]), float(partes[2])]
                        v2 = [float(partes[3]), float(partes[4]), float(partes[5])]
                        v3 = [float(partes[6]), float(partes[7]), float(partes[8])]
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
            return True
        except Exception as e:
            print(f"Falha ao carregar modelo TRI: {e}")
            return False

    # Reposiciona cápsula coletada
    def reposicionarCapsula(self, indice):
        avoid = set()
        jogador_cel = (int(self.posicao_jogador[0]), int(self.posicao_jogador[2]))
        avoid.add(jogador_cel)
        for c in self.capsulas:
            avoid.add((int(c['x']), int(c['z'])))
        for inim in self.inimigos:
            avoid.add((int(inim['x']), int(inim['z'])))
        cel = self.escolherCelulaLivreAleatoria(avoid_positions=avoid)
        if cel is None:
            return
        self.capsulas[indice]['x'] = cel[0] + 0.5
        self.capsulas[indice]['z'] = cel[1] + 0.5

    # Reposiciona inimigo após colisão
    def reposicionarInimigoAleatorio(self, inimigo):
        avoid = set()
        jogador_cel = (int(self.posicao_jogador[0]), int(self.posicao_jogador[2]))
        avoid.add(jogador_cel)
        for c in self.capsulas:
            avoid.add((int(c['x']), int(c['z'])))
        for inim in self.inimigos:
            avoid.add((int(inim['x']), int(inim['z'])))
        cel = self.escolherCelulaLivreAleatoria(avoid_positions=avoid)
        if cel is None:
            return
        inimigo['x'] = cel[0] + 0.5
        inimigo['z'] = cel[1] + 0.5

    # Carrega a estrutura do mapa
    def carregarMapa(self, nome_arquivo):
        try:
            with open(nome_arquivo, 'r', encoding="utf-8") as f:
                linhas = f.readlines()
            largura, altura = map(int, linhas[0].split())
            self.mapa_largura = largura
            self.mapa_altura = altura
            def normalizar(linha):
                linha = linha.replace("\t", " ")
                while "  " in linha:
                    linha = linha.replace("  ", " ")
                return linha.strip()
            
            for y in range(self.mapa_altura):
                linha_raw = normalizar(linhas[y + 1])
                tokens = linha_raw.split(" ")
                linha_mapa = []
                linha_texturas = []
                for x, val in enumerate(tokens):
                    tipo_textura = 5
                    if ":" in val:
                        tipo_str, textura_str = val.split(":")
                        tipo_celula = int(tipo_str)
                        try:
                            tipo_textura = int(textura_str)
                        except:
                            pass
                    else:
                        tipo_celula = int(val)
                    if tipo_celula == 3:
                        self.posicao_jogador = npy.array([x + 0.5, 0.85, y + 0.5], dtype=float)
                        linha_mapa.append(1)
                    elif tipo_celula in (1, 2):
                        linha_mapa.append(tipo_celula)
                    elif tipo_celula == 4:
                        self.janelas.append({'x': x, 'y': y, 'altura': self.ALTURA_JANELA})
                        linha_mapa.append(1)
                    elif tipo_celula == 5:
                        self.portas.append({'x': x, 'y': y, 'altura': self.ALTURA_PORTA})
                        linha_mapa.append(1)
                    elif tipo_celula == 6:
                        modelo = None
                        if ":" in val:
                            _, modelo = val.split(":", 1)
                            modelo = modelo.strip()
                        self.objetos_estaticos.append({
                            'x': x,
                            'y': y,
                            'tipo': modelo
                        })
                        linha_mapa.append(1)
                    elif tipo_celula == 7:
                        self.capsulas.append({'x': x + 0.5, 'y': 0.0, 'z': y + 0.5})
                        linha_mapa.append(1)
                    else:
                        linha_mapa.append(tipo_celula)
                    linha_texturas.append(tipo_textura)

                self.mapa.append(linha_mapa)
                self.mapa_tipos_piso.append(linha_texturas)
            print(f"Mapa carregado: {self.mapa_largura}x{self.mapa_altura}")
            self.converterTRI()
        except Exception as e:
            print(f"Erro ao carregar mapa: {e}")
            raise

    # Converte objetos estáticos para renderização TRI
    def converterTRI(self):
        self.objetos_tri = []
        for obj in self.objetos_estaticos:
            modelo = obj['tipo']
            escala = self.escalas_modelos.get(modelo, 1.0)
            self.objetos_tri.append({
                'modelo': modelo,
                'x': obj['x'] + 0.5,
                'y': 0.0,
                'z': obj['y'] + 0.5,
                'escala': escala
            })

    # Verifica se a célula é livre
    def livre(self, x, y):
        if x < 0 or x >= self.mapa_largura or y < 0 or y >= self.mapa_altura:
            return False
        celula = self.mapa[int(y)][int(x)]
        return celula in [1, 2, 3]

    # Verifica colisão do jogador
    def verificarColisao(self, pos_x, pos_z):
        pontos = [
            (pos_x, pos_z),
            (pos_x + 0.2, pos_z),
            (pos_x - 0.2, pos_z),
            (pos_x, pos_z + 0.2),
            (pos_x, pos_z - 0.2),
        ]
        for px, pz in pontos:
            janela = any(janela['x'] == int(px) and janela['y'] == int(pz) for janela in self.janelas)
            if janela:
                return True
            objeto = any(obj['x'] == int(px) and obj['y'] == int(pz) for obj in self.objetos_estaticos)
            if objeto:
                return True
            porta = any(porta['x'] == int(px) and porta['y'] == int(pz) for porta in self.portas)
            if porta:
                continue
            if not self.ehPassavel(px, pz):
                return True
        return False
    
    # Atualiza posição e energia do jogador
    def atualizarMovimento(self, dt):
        if dt <= 0:
            return
        if not self.espaco_pressionado:
            return
        if self.energia <= 0:
            return
        deslocamento = 10.0 * dt
        rad = math.radians(self.angulo_rotacao)
        nova_x = self.posicao_jogador[0] + deslocamento * math.sin(rad)
        nova_z = self.posicao_jogador[2] + deslocamento * math.cos(rad)
        self.energia -= 1.0 * dt
        if self.energia < 0:
            self.energia = 0
        if not self.verificarColisao(nova_x, nova_z):
            self.posicao_jogador[0] = nova_x
            self.posicao_jogador[2] = nova_z

    # Desenha o piso com texturas
    def desenharPisoComTexturas(self):
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        for y in range(self.mapa_altura):
            for x in range(self.mapa_largura):
                if not self.livre(x, y):
                    continue
                tipo_texto = self.mapa_tipos_piso[y][x] if y < len(self.mapa_tipos_piso) and x < len(self.mapa_tipos_piso[y]) else 5
                textura_id = self.texturas_piso.get(tipo_texto, None)
                if textura_id is None:
                    continue
                glBindTexture(GL_TEXTURE_2D, textura_id)
                glEnable(GL_TEXTURE_2D)
                glColor3f(1.0, 1.0, 1.0)
                cx = x + 0.5
                cz = y + 0.5
                tamanho = self.TAMANHO_CELULA / 2.0
                glBegin(GL_QUADS)
                glTexCoord2f(0.0, 0.0); glVertex3f(cx - tamanho, 0.01, cz - tamanho)
                glTexCoord2f(1.0, 0.0); glVertex3f(cx + tamanho, 0.01, cz - tamanho)
                glTexCoord2f(1.0, 1.0); glVertex3f(cx + tamanho, 0.01, cz + tamanho)
                glTexCoord2f(0.0, 1.0); glVertex3f(cx - tamanho, 0.01, cz + tamanho)
                glEnd()
        glDisable(GL_TEXTURE_2D)

    # Desenha uma parede
    def desenharParede(self, x, z, altura, espessura, cima=True, baixo=True,
                       direita=True, esquerda=True):
        cx = x + 0.5
        cz = z + 0.5
        tamanho = self.TAMANHO_CELULA
        esp = espessura / 2
        glColor3f(0.7, 0.7, 0.7)
        if cima:
            glBegin(GL_QUADS)
            glVertex3f(cx - tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx + tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz - tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz - tamanho/2)
            glEnd()
        if baixo:
            glBegin(GL_QUADS)
            glVertex3f(cx + tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx - tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz + tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz + tamanho/2)
            glEnd()
        if esquerda:
            glBegin(GL_QUADS)
            glVertex3f(cx - tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx - tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz - tamanho/2)
            glVertex3f(cx - tamanho/2, altura, cz + tamanho/2)
            glEnd()
        if direita:
            glBegin(GL_QUADS)
            glVertex3f(cx + tamanho/2, 0, cz - tamanho/2)
            glVertex3f(cx + tamanho/2, 0, cz + tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz + tamanho/2)
            glVertex3f(cx + tamanho/2, altura, cz - tamanho/2)
            glEnd()

    # Desenha o labirinto
    def desenharLabirinto(self):
        self.desenharPisoComTexturas()
        for y in range(self.mapa_altura):
            for x in range(self.mapa_largura):
                if self.mapa[y][x] == 0:
                    self.desenharParede(x, y, self.ALTURA_PAREDE, self.ESPESSURA_PAREDE)
        for janela in self.janelas:
            self.desenharJanela(janela['x'], janela['y'], janela['altura'])
        for porta in self.portas:
            self.desenharPorta(porta['x'], porta['y'], porta['altura'])
        for obj_tri in self.objetos_tri:
            self.desenharModeloTRI(obj_tri)
        for cap in self.capsulas:
            self.desenharCapsula(cap)
        for inimigo in self.inimigos:
            self.desenharInimigo(inimigo)

    # Desenha inimigo 
    def desenharInimigo(self, inimigo):
        glPushMatrix()
        glTranslatef(inimigo['x'], inimigo['y'] + 0.5, inimigo['z'])
        glColor3f(1.0, 0.0, 0.0)
        quad = gluNewQuadric()
        gluSphere(quad, 0.4, 16, 16)
        glPopMatrix()

    # Desenha cápsula 
    def desenharCapsula(self, cap):
        glPushMatrix()
        glTranslatef(cap['x'], cap['y'] + 0.6, cap['z'])
        glColor3f(0.0, 1.0, 0.0)
        quad = gluNewQuadric()
        gluSphere(quad, 0.4, 10, 12)
        glPopMatrix()

    # Movimenta inimigos em direção ao jogador
    def atualizarInimigos(self, dt):
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
                novo_x = inimigo['x'] + dir_x * 20.0 * dt
                novo_z = inimigo['z'] + dir_z * 20.0 * dt
                if self.livre(int(novo_x), int(novo_z)):
                    inimigo['x'] = novo_x
                    inimigo['z'] = novo_z
                else:
                    if self.livre(int(novo_x), int(inimigo['z'])):
                        inimigo['x'] = novo_x
                    elif self.livre(int(inimigo['x']), int(novo_z)):
                        inimigo['z'] = novo_z

    # Desenha uma janela
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

    # Desenha uma porta
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

    # Desenha o jogador (boneco)
    def desenharJogador(self):
        glPushMatrix()
        glTranslatef(self.posicao_jogador[0], self.posicao_jogador[1] - 1.0 , self.posicao_jogador[2])
        glRotatef(self.angulo_rotacao, 0, 1, 0)
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)

        # Perna esquerda
        glPushMatrix()
        glTranslatef(-0.18, 0.3, 0.0)      
        glRotatef(-10, 1, 0, 0)
        glColor3f(0.15, 0.15, 0.6)         
        gluCylinder(quad, 0.09, 0.09, 0.55, 12, 4)
        glTranslatef(0.0, 0.0, 0.55)
        gluSphere(quad, 0.10, 10, 8)       
        glPopMatrix()

        # Perna direita 
        glPushMatrix()
        glTranslatef(0.18, 0.3, 0.0)
        glRotatef(-10, 1, 0, 0)
        glColor3f(0.15, 0.15, 0.6)
        gluCylinder(quad, 0.09, 0.09, 0.55, 12, 4)
        glTranslatef(0.0, 0.0, 0.55)
        gluSphere(quad, 0.10, 10, 8)
        glPopMatrix()
        
        # Tronco  
        glPushMatrix()
        glTranslatef(0.0, 0.8, 0.0)
        glRotatef(-90, 1, 0, 0)            
        glColor3f(0.2, 0.6, 0.9)           
        gluCylinder(quad, 0.32, 0.28, 0.7, 16, 4)
        glPopMatrix()

        # Cabeça 
        glPushMatrix()
        glTranslatef(0.0, 1.6, 0.0)
        glColor3f(1.0, 0.85, 0.7)          
        gluSphere(quad, 0.28, 18, 16)
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
        glPopMatrix()  

        # Braço esquerdo
        glPushMatrix()
        glTranslatef(-0.42, 1.05, 0.0)
        glRotatef(10, 0, 0, 1)
        glColor3f(0.15, 0.15, 0.6)
        gluCylinder(quad, 0.07, 0.06, 0.45, 12, 4)
        glTranslatef(0.0, 0.0, 0.45)
        gluSphere(quad, 0.06, 8, 6)
        glPopMatrix()

        # Braço direito
        glPushMatrix()
        glTranslatef(0.42, 1.05, 0.0)
        glRotatef(-10, 0, 0, 1)
        glColor3f(0.15, 0.15, 0.6)
        gluCylinder(quad, 0.07, 0.06, 0.45, 12, 4)
        glTranslatef(0.0, 0.0, 0.45)
        gluSphere(quad, 0.06, 8, 6)
        glPopMatrix()
        glPopMatrix()

    # Configura a perspectiva e a câmera
    def configurarPerspectiva(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (self.largura / self.altura), 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        if self.modo_camera == 0:
            camera_x = self.posicao_jogador[0]
            camera_y = self.posicao_jogador[1] + 1.5
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

    # Desenha um modelo TRI
    def desenharModeloTRI(self, obj_tri):
        nome_modelo = obj_tri['modelo']
        if nome_modelo not in self.modelos_tri:
            return
        triangulos = self.modelos_tri[nome_modelo]
        glPushMatrix()
        glTranslatef(obj_tri['x'], obj_tri['y'], obj_tri['z'])
        glScalef(obj_tri['escala'], obj_tri['escala'], obj_tri['escala'])

        glBegin(GL_TRIANGLES)
        for tri in triangulos:
            glColor3f(*tri['cor'])
            glVertex3f(tri['v1'][0], tri['v1'][1], tri['v1'][2])
            glColor3f(*tri['cor'])
            glVertex3f(tri['v2'][0], tri['v2'][1], tri['v2'][2])
            glColor3f(*tri['cor'])
            glVertex3f(tri['v3'][0], tri['v3'][1], tri['v3'][2])
        glEnd()
        glPopMatrix()

    # Desenha o HUD (Energia e Pontos)
    def desenharHUD(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.largura, self.altura, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        barra_x = 10
        barra_y = 5
        barra_larg = 200
        barra_alt = 16
        try:
            frac = max(0.0, min(1.0, float(self.energia) / 100.0))
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

        texto = f"Energia: {int(self.energia)}  Pontos: {self.pontos}"
        glColor3f(1.0, 1.0, 1.0)
        glRasterPos2i(10, 40)  
        for ch in texto:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))

        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    # Loop principal: atualiza e desenha
    def loopPrincipal(self):
        tempo_atual = time.time()
        dt = tempo_atual - self.tempo_anterior
        self.tempo_anterior = tempo_atual
        if dt > 0.05:
            dt = 0.05

        # Atualizações
        self.atualizarMovimento(dt)
        self.atualizarInimigos(dt)
        self.verificarCapturaCapsulas()

        # Desenho
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.configurarPerspectiva()
        self.desenharLabirinto()
        self.desenharJogador()
        self.desenharHUD()

        glutSwapBuffers()

        
def main():
    # Inicializa o jogo e o loop principal GLUT
    jogo = Labirinto3D()
    print("\n=== LABIRINTO 3D (GLUT) ===")
    print("Controles: BARRA - Avançar | ESQ/DIR - Girar | 1/2/3 - Câmera | ESC - Sair")
    glutMainLoop()

if __name__ == "__main__":
    main()