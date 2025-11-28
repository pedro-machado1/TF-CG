# Sistema de Texturas do Chão - Labirinto 3D

## Formato do Mapa com Texturas

O arquivo de mapa agora suporta especificar qual textura usar em cada célula.

### Sintaxe

Cada célula pode ser especificada de duas formas:

1. **Formato antigo (retrocompatível)**: apenas o tipo de célula
   ```
   0 1 2 3 4 5 6 7
   ```

2. **Novo formato com textura**: `tipo_celula:tipo_textura`
   ```
   1:0 1:1 1:4 1:9 2:6 3:5
   ```

### Tipos de Célula

| Valor | Significado |
|-------|------------|
| 0 | Parede (sem textura) |
| 1 | Corredor (com textura) |
| 2 | Sala (com textura) |
| 3 | Posição inicial do jogador |
| 4 | Janela |
| 5 | Porta |
| 6 | Objeto estático |
| 7 | Cápsula de energia |

### Tipos de Textura (Índice 0-11)

| ID | Nome | Arquivo |
|----|------|---------|
| 0 | CROSS | CROSS.png |
| 1 | DL | DL.png |
| 2 | DLR | DLR.png |
| 3 | DR | DR.png |
| 4 | LR | LR.png |
| 5 | None | None.png (padrão) |
| 6 | UD | UD.png |
| 7 | UDL | UDL.png |
| 8 | UDR | UDR.png |
| 9 | UL | UL.png |
| 10 | ULR | ULR.png |
| 11 | UR | UR.png |

### Exemplos

#### Mapa simples com textura padrão (None.png)
```
# Usando formato retrocompatível
20 20
1 1 1 1 1
1 0 0 1 1
1 0 0 1 1
```

#### Mapa com texturas diferentes por área
```
# Corredor com textura CROSS (índice 0)
1:0 1:0 1:0 1:0 1:0

# Sala com textura UD (índice 6)
2:6 2:6 2:6 2:6 2:6

# Mistura de objetos com texturas
1:0 6 1:0 7:0 1:0
```

#### Mapa completo com variação
```
20 20
1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0 1:0
1:1 1:1 1:1 1:1 1:1 7:5 1:1 6 1:1 1:1 1:1 7:1 1:1 1:1 1:1 6 1:1 7:1 1:1 1:1
1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4 1:4
...
```

## Como Usar

### Opção 1: Usar o novo mapa com texturas
```python
# No arquivo Labirinto3D.py, linha ~80:
self.carregarMapa("mapa_labirinto_texturas.txt")  # Novo mapa com texturas
```

### Opção 2: Manter mapa antigo (retrocompatível)
```python
self.carregarMapa("mapa_labirinto.txt")  # Mapa original - usa textura padrão
```

## Observações

- Se um tipo de textura não for especificado, usa-se o padrão: `5` (None.png)
- Objetos estáticos (6), cápsulas (7), janelas (4) e portas (5) ignoram a textura especificada
- O sistema é retrocompatível: mapas antigos funcionam normalmente
- As texturas devem estar no diretório `TexturaAsfalto/` como arquivos PNG

## Exemplo de Mapa Visual

```
# Parede com corredor texturizado
0 0 0 0 0 0 0
0 1:0 1:0 1:0 1:0 1:0 0
0 1:0 1:1 1:1 1:1 1:0 0
0 1:0 1:6 1:6 1:6 1:0 0
0 1:0 1:0 1:0 1:0 1:0 0
0 0 0 0 0 0 0
```

Resultado:
- Bordas: paredes (sem textura)
- Corredor externo: textura CROSS (0)
- Corredor interno: textura DL (1)
- Sala central: textura UD (6)
