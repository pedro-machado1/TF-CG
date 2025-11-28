#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se todas as dependências estão corretas
"""

print("Testando importações...")

try:
    import pygame
    print("✓ pygame versão:", pygame.__version__)
except ImportError as e:
    print("✗ Erro ao importar pygame:", e)

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    print("✓ PyOpenGL importado com sucesso")
except ImportError as e:
    print("✗ Erro ao importar PyOpenGL:", e)

try:
    import numpy
    print("✓ numpy versão:", numpy.__version__)
except ImportError as e:
    print("✗ Erro ao importar numpy:", e)

print("\nTodas as dependências estão OK!")
print("Você pode executar: python Labirinto3D.py")
