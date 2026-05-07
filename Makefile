# Move Mouse Linux — Makefile
# Build targets para Flatpak y .deb

PYTHON := python3
PIP := pip3
PROJECT := move-mouse
FLATPAK_MANIFEST := flatpak/org.movemouse.MoveMouse.yml
DATA_DIR := data
DEB_NAME := $(PROJECT)_1.0.0-1_all.deb

.PHONY: all install run test clean deb flatpak flatpak-builder help

# ── Default ──────────────────────────────────────────────
all: install

# ── Python ───────────────────────────────────────────────
install:
	$(PIP) install -e .

run:
	$(PYTHON) -m move_mouse

run-gui:
	$(PYTHON) -m move_mouse

run-cli:
	$(PYTHON) -m move_mouse --no-gui

test:
	pytest tests/ -v --tb=short

# ── Debian Package (.deb) ────────────────────────────────
deb: clean-deb
	dpkg-buildpackage -us -uc -b
	@echo ""
	@echo "✅ .deb generado: ../$(DEB_NAME)"

deb-install: deb
	sudo dpkg -i ../$(DEB_NAME)

deb-uninstall:
	sudo dpkg -r $(PROJECT)

clean-deb:
	rm -rf debian/$(PROJECT) debian/.debhelper debian/debhelper-build-stamp debian/files debian/*.log debian/*.substvars
	rm -f ../$(PROJECT)_*.deb ../$(PROJECT)_*.changes ../$(PROJECT)_*.buildinfo

# ── Flatpak ──────────────────────────────────────────────
flatpak: flatpak-builder

flatpak-builder:
	flatpak-builder --user --install --force-clean build-dir $(FLATPAK_MANIFEST)
	@echo ""
	@echo "✅ Flatpak instalado como org.movemouse.MoveMouse"

flatpak-run:
	flatpak run org.movemouse.MoveMouse

flatpak-clean:
	rm -rf build-dir .flatpak-builder

# ── General ──────────────────────────────────────────────
clean: clean-deb flatpak-clean
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete

dist: clean
	$(PYTHON) -m build

# ── Help ─────────────────────────────────────────────────
help:
	@echo "Move Mouse Linux — Build System"
	@echo ""
	@echo "  make install       Instalar en modo desarrollo (pip -e)"
	@echo "  make run           Ejecutar (GUI por defecto)"
	@echo "  make run-cli       Ejecutar sin GUI"
	@echo "  make test          Correr tests"
	@echo ""
	@echo "  make deb           Construir .deb"
	@echo "  make deb-install   Construir e instalar .deb"
	@echo "  make deb-uninstall Desinstalar .deb"
	@echo ""
	@echo "  make flatpak       Construir e instalar Flatpak"
	@echo "  make flatpak-run   Ejecutar Flatpak"
	@echo ""
	@echo "  make clean         Limpiar todo"
	@echo "  make dist          Crear wheel + sdist"
