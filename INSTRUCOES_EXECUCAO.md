# Labirinto 3D com OpenGL - Instruções de Execução

## Requisitos de Instalação

### 1. Python 3.8+
Certifique-se de ter Python 3.8 ou superior instalado.

### 2. Instalar Dependências

Abra o PowerShell ou Command Prompt e execute:

```powershell
pip install pygame PyOpenGL PyOpenGL-accelerate numpy
```

Ou se estiver usando pip3:

```powershell
pip3 install pygame PyOpenGL PyOpenGL-accelerate numpy
```

## Como Executar

### Opção 1: Via PowerShell

Navegue até o diretório do projeto:

```powershell
cd "C:\Users\pedro\Documents\TF-CG"
```

Execute o programa:

```powershell
python Labirinto3D.py
```

ou

```powershell
python3 Labirinto3D.py
```

### Opção 2: Duplo clique (se Python estiver registrado)

1. Abra o explorador de arquivos
2. Navegue até: `C:\Users\pedro\Documents\TF-CG`
3. Duplo clique em `Labirinto3D.py`

## Controles do Jogo

| Controle | Função |
|----------|--------|
| **Seta Esquerda** | Girar para esquerda |
| **Seta Direita** | Girar para direita |
| **Espaço** | Iniciar/Parar o movimento |
| **1** | Ativar câmera em primeira pessoa |
| **2** | Ativar câmera em terceira pessoa |
| **3** | Alternar alvo da câmera (Centro do mapa ↔ Jogador) |
| **ESC** | Sair do programa |

## Especificações do Programa

### Personagem do Jogador
- **Velocidade**: 10 m/s
- **Altura**: 1.7 metros
- **Representação**: Esfera verde com indicador de direção (esfera amarela)
- **Controle**: Setas para virar + Espaço para movimento

### Labirinto
- **Células**: 20x20 metros
- **Altura das paredes**: 2.7 metros
- **Espessura das paredes**: 25 cm
- **Piso**: Cinza (0.1m acima do zero)

### Câmeras
1. **Primeira Pessoa**: Visão do ponto de vista do jogador
2. **Terceira Pessoa**: Visão de cima (acima do labirinto)

### Arquivo de Mapa
- O arquivo `mapa_labirinto.txt` contém o layout do labirinto
- Primeira linha: dimensões (largura altura)
- Números na matriz:
  - **0**: Parede
  - **1**: Corredor
  - **2**: Sala
  - **3**: Posição inicial do jogador

## Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'OpenGL'"
Instale as dependências:
```powershell
pip install PyOpenGL PyOpenGL-accelerate
```

### Erro: "No module named 'pygame'"
Instale pygame:
```powershell
pip install pygame
```

### A janela não abre ou crashes
- Certifique-se de que sua placa gráfica suporta OpenGL 2.0+
- Tente atualizar os drivers da placa gráfica

### O programa é muito lento
- Reduza a resolução alterando `largura=800, altura=600` na classe Labirinto3D
- Reduza o FPS alterando `self.fps = 30` ao invés de 60

## Estrutura do Programa

```
Labirinto3D.py
├── Classe Labirinto3D
│   ├── carregarMapa() - Lê o arquivo de mapa
│   ├── ehCelulaLivre() - Verifica se pode passar
│   ├── verificarColisao() - Detecta colisões
│   ├── atualizarMovimento() - Atualiza posição do jogador
│   ├── desenharParede() - Desenha uma parede
│   ├── desenharLabirinto() - Renderiza todo o labirinto
│   ├── desenharJogador() - Renderiza o personagem
│   ├── configurarPerspectiva() - Configura câmera
│   ├── procesarEventos() - Processa entrada do usuário
│   └── executar() - Loop principal
```

## Informações Técnicas

- **Motor Gráfico**: OpenGL
- **Biblioteca GUI**: Pygame
- **Linguagem**: Python 3
- **Resolução Padrão**: 1200x800
- **FPS**: 60

## Notas Importantes

1. **Colisão**: O jogador não pode passar pelas paredes
2. **Movimento Contínuo**: Uma vez iniciado, o movimento continua até colidir ou ser parado
3. **Câmeras**: Alternar entre primeira e terceira pessoa é instantâneo
4. **Alvo da Câmera**: Na terceira pessoa, pode seguir o jogador ou observar o mapa todo

## Próximas Melhorias (Não Implementadas)

- [ ] Inimigos com IA
- [ ] Objetos decorativos carregados de arquivos 3D
- [ ] Cápsulas de energia
- [ ] Sistema de pontuação
- [ ] Efeitos de som
- [ ] Texturas nas paredes

---

**Desenvolvido por**: Seu Nome
**Data**: 27/11/2025
**Disciplina**: 4645Z-4 - Fundamentos de Computação Gráfica
