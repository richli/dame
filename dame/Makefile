.PHONY: all clean

all: main_window.py

main_window.py: main_window.ui
	pyside-uic $^ -o $@

clean:
	rm main_window.py
