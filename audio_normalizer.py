#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audio Normalizer - Профессиональная нормализация громкости аудио и видео
Версия: 2.0 - Красивый интерфейс
"""

import tkinter as tk
from tkinter import filedialog, ttk, messagebox, font
import os
from pathlib import Path
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

class AudioNormalizer:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 Audio Normalizer Pro")
        self.root.geometry("950x680")
        self.root.resizable(True, True)
        
        # Цветовая схема
        self.colors = {
            'bg': '#1e1e2e',           # Темный фон
            'bg_light': '#2a2a3e',     # Светлее фон
            'accent': '#89b4fa',       # Голубой акцент
            'success': '#a6e3a1',      # Зеленый
            'warning': '#f9e2af',      # Желтый
            'error': '#f38ba8',        # Красный
            'text': '#cdd6f4',         # Светлый текст
            'text_dim': '#9399b2',     # Тусклый текст
            'border': '#45475a',       # Граница
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        self.files = []
        self.processing = False
        self.completed = 0
        self.total = 0
        
        self.setup_fonts()
        self.setup_styles()
        self.setup_ui()
    
    def setup_fonts(self):
        """Настройка шрифтов"""
        self.fonts = {
            'title': font.Font(family='Segoe UI', size=14, weight='bold'),
            'subtitle': font.Font(family='Segoe UI', size=11, weight='bold'),
            'normal': font.Font(family='Segoe UI', size=10),
            'small': font.Font(family='Segoe UI', size=9),
        }
    
    def setup_styles(self):
        """Настройка стилей ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Стиль для LabelFrame
        style.configure('Custom.TLabelframe', 
                       background=self.colors['bg_light'],
                       bordercolor=self.colors['border'],
                       borderwidth=2)
        style.configure('Custom.TLabelframe.Label', 
                       background=self.colors['bg_light'],
                       foreground=self.colors['accent'],
                       font=self.fonts['subtitle'])
        
        # Стиль для Checkbutton
        style.configure('Custom.TCheckbutton',
                       background=self.colors['bg_light'],
                       foreground=self.colors['text'],
                       font=self.fonts['normal'])
        
        # Стиль для Radiobutton
        style.configure('Custom.TRadiobutton',
                       background=self.colors['bg_light'],
                       foreground=self.colors['text'],
                       font=self.fonts['normal'])
        
        # Стиль для Progressbar
        style.configure('Custom.Horizontal.TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['bg_light'],
                       bordercolor=self.colors['border'],
                       lightcolor=self.colors['accent'],
                       darkcolor=self.colors['accent'])
    
    def create_button(self, parent, text, command, bg_color=None, width=15):
        """Создание красивой кнопки"""
        if bg_color is None:
            bg_color = self.colors['accent']
        
        btn = tk.Button(parent, text=text, command=command,
                       bg=bg_color, fg='#000000',
                       font=self.fonts['normal'],
                       relief=tk.FLAT, width=width,
                       cursor='hand2', borderwidth=0,
                       pady=5)
        
        # Hover эффекты
        def on_enter(e):
            btn['bg'] = self.lighten_color(bg_color)
        
        def on_leave(e):
            btn['bg'] = bg_color
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    def lighten_color(self, hex_color, factor=1.2):
        """Осветлить цвет"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c * factor)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def setup_ui(self):
        """Создание интерфейса"""
        
        # === ЗАГОЛОВОК ===
        header_frame = tk.Frame(self.root, bg=self.colors['bg_light'], height=60)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🎵 Audio Normalizer Pro",
                              bg=self.colors['bg_light'],
                              fg=self.colors['accent'],
                              font=self.fonts['title'])
        title_label.pack(pady=(10, 2))
        
        subtitle_label = tk.Label(header_frame, 
                                 text="Профессиональная нормализация громкости",
                                 bg=self.colors['bg_light'],
                                 fg=self.colors['text_dim'],
                                 font=self.fonts['small'])
        subtitle_label.pack()
        
        # === КНОПКИ ДЕЙСТВИЙ ===
        btn_frame = tk.Frame(self.root, bg=self.colors['bg'], pady=5)
        btn_frame.pack(fill=tk.X, padx=10)
        
        self.create_button(btn_frame, "📁 Добавить файлы", 
                          self.add_files, self.colors['accent'], 18).pack(side=tk.LEFT, padx=5)
        self.create_button(btn_frame, "📂 Добавить папку", 
                          self.add_folder, self.colors['accent'], 18).pack(side=tk.LEFT, padx=5)
        self.create_button(btn_frame, "🗑️ Очистить", 
                          self.clear_files, self.colors['error'], 15).pack(side=tk.LEFT, padx=5)
        
        # === СПИСОК ФАЙЛОВ ===
        list_frame = tk.LabelFrame(self.root, text="  Файлы для обработки  ",
                                  bg=self.colors['bg_light'],
                                  fg=self.colors['accent'],
                                  font=self.fonts['subtitle'],
                                  relief=tk.FLAT, borderwidth=2,
                                  highlightbackground=self.colors['border'],
                                  highlightthickness=1)
        list_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(5, 5))
        
        # Scrollbar и Listbox
        list_inner = tk.Frame(list_frame, bg=self.colors['bg_light'])
        list_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(list_inner, bg=self.colors['bg_light'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_inner, yscrollcommand=scrollbar.set,
                                       bg=self.colors['bg'], fg=self.colors['text'],
                                       font=self.fonts['normal'], selectbackground=self.colors['accent'],
                                       selectforeground='#000000', borderwidth=0,
                                       highlightthickness=0, relief=tk.FLAT, height=6)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar.config(command=self.file_listbox.yview)
        
        # === НАСТРОЙКИ (2 КОЛОНКИ) С ПРОКРУТКОЙ ===
        # Создаем Canvas с прокруткой для настроек
        settings_outer = tk.Frame(self.root, bg=self.colors['bg'])
        settings_outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas для прокрутки
        canvas = tk.Canvas(settings_outer, bg=self.colors['bg'], 
                          highlightthickness=0, borderwidth=0)
        scrollbar_settings = tk.Scrollbar(settings_outer, orient="vertical", 
                                         command=canvas.yview, bg=self.colors['bg'])
        
        settings_scrollable = tk.Frame(canvas, bg=self.colors['bg'])
        
        settings_scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=settings_scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_settings.set)
        
        # Прокрутка мышью
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_settings.pack(side="right", fill="y")
        
        settings_container = settings_scrollable
        
        # ЛЕВАЯ КОЛОНКА
        left_column = tk.Frame(settings_container, bg=self.colors['bg'])
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Основные настройки
        main_settings = ttk.LabelFrame(left_column, text="  Основные настройки  ", 
                                       style='Custom.TLabelframe')
        main_settings.pack(fill=tk.X, pady=5)
        
        # Выходная папка
        output_frame = tk.Frame(main_settings, bg=self.colors['bg_light'])
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(output_frame, text="📁 Выходная папка:",
                bg=self.colors['bg_light'], fg=self.colors['text'],
                font=self.fonts['normal']).pack(side=tk.LEFT)
        
        self.output_var = tk.StringVar(value="Не выбрана")
        tk.Label(output_frame, textvariable=self.output_var,
                bg=self.colors['bg_light'], fg=self.colors['text_dim'],
                font=self.fonts['small']).pack(side=tk.LEFT, padx=10)
        
        self.create_button(output_frame, "Выбрать", self.select_output_folder,
                          self.colors['accent'], 10).pack(side=tk.RIGHT)
        
        # Целевой уровень
        target_frame = tk.Frame(main_settings, bg=self.colors['bg_light'])
        target_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(target_frame, text="🎚️ Целевой уровень (LUFS):",
                bg=self.colors['bg_light'], fg=self.colors['text'],
                font=self.fonts['normal']).pack(side=tk.LEFT)
        
        self.target_var = tk.StringVar(value="-16")
        target_entry = tk.Entry(target_frame, textvariable=self.target_var,
                               bg=self.colors['bg'], fg=self.colors['text'],
                               font=self.fonts['normal'], width=8,
                               relief=tk.FLAT, borderwidth=2,
                               highlightbackground=self.colors['border'],
                               highlightthickness=1)
        target_entry.pack(side=tk.LEFT, padx=10)
        
        tk.Label(target_frame, text="dB  (рекомендуется: -16 для музыки, -14 для YouTube)",
                bg=self.colors['bg_light'], fg=self.colors['text_dim'],
                font=self.fonts['small']).pack(side=tk.LEFT)
        
        # Суффикс
        suffix_frame = tk.Frame(main_settings, bg=self.colors['bg_light'])
        suffix_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(suffix_frame, text="✏️ Суффикс файла:",
                bg=self.colors['bg_light'], fg=self.colors['text'],
                font=self.fonts['normal']).pack(side=tk.LEFT)
        
        self.suffix_var = tk.StringVar(value="_normalized")
        suffix_entry = tk.Entry(suffix_frame, textvariable=self.suffix_var,
                               bg=self.colors['bg'], fg=self.colors['text'],
                               font=self.fonts['normal'], width=15,
                               relief=tk.FLAT, borderwidth=2,
                               highlightbackground=self.colors['border'],
                               highlightthickness=1)
        suffix_entry.pack(side=tk.LEFT, padx=10)
        
        # Режим обработки
        mode_frame = ttk.LabelFrame(left_column, text="  🎛️ Режим обработки  ",
                                   style='Custom.TLabelframe')
        mode_frame.pack(fill=tk.X, pady=5)
        
        mode_inner = tk.Frame(mode_frame, bg=self.colors['bg_light'])
        mode_inner.pack(fill=tk.X, padx=10, pady=5)
        
        self.mode_var = tk.StringVar(value="normal")
        
        modes = [
            ("Normal (универсальный)", "normal"),
            ("Music (музыка)", "music"),
            ("Vocal (вокал, подкасты)", "vocal"),
            ("Classic/Opera (классика)", "compressed")
        ]
        
        for text, value in modes:
            ttk.Radiobutton(mode_inner, text=text, variable=self.mode_var,
                           value=value, style='Custom.TRadiobutton').pack(anchor=tk.W, pady=1)
        
        # ПРАВАЯ КОЛОНКА
        right_column = tk.Frame(settings_container, bg=self.colors['bg'])
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Дополнительные настройки
        extra_settings = ttk.LabelFrame(right_column, text="  ⚙️ Дополнительно  ",
                                       style='Custom.TLabelframe')
        extra_settings.pack(fill=tk.X, pady=5)
        
        extra_inner = tk.Frame(extra_settings, bg=self.colors['bg_light'])
        extra_inner.pack(fill=tk.X, padx=10, pady=5)
        
        # Чекбоксы
        self.keep_video_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(extra_inner, text="💾 Сохранить видео в MP4",
                       variable=self.keep_video_var,
                       style='Custom.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        self.prevent_clipping_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(extra_inner, text="🛡️ Предотвращение клиппинга",
                       variable=self.prevent_clipping_var,
                       style='Custom.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        self.use_gate_var = tk.BooleanVar(value=False)
        gate_cb = ttk.Checkbutton(extra_inner, text="🔇 Noise Gate (шумоподавление)",
                                 variable=self.use_gate_var,
                                 style='Custom.TCheckbutton')
        gate_cb.pack(anchor=tk.W, pady=2)
        
        # Gate порог
        gate_threshold_frame = tk.Frame(extra_inner, bg=self.colors['bg_light'])
        gate_threshold_frame.pack(fill=tk.X, padx=20, pady=2)
        
        tk.Label(gate_threshold_frame, text="Порог:",
                bg=self.colors['bg_light'], fg=self.colors['text_dim'],
                font=self.fonts['small']).pack(side=tk.LEFT)
        
        self.gate_threshold_var = tk.StringVar(value="-40")
        gate_entry = tk.Entry(gate_threshold_frame, textvariable=self.gate_threshold_var,
                             bg=self.colors['bg'], fg=self.colors['text'],
                             font=self.fonts['small'], width=6,
                             relief=tk.FLAT, borderwidth=1)
        gate_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(gate_threshold_frame, text="dB",
                bg=self.colors['bg_light'], fg=self.colors['text_dim'],
                font=self.fonts['small']).pack(side=tk.LEFT)
        
        self.use_exciter_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(extra_inner, text="✨ Harmonic Exciter (яркость)",
                       variable=self.use_exciter_var,
                       style='Custom.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        self.hf_denoise_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(extra_inner, text="🎛️ HF Denoiser (старые записи)",
                       variable=self.hf_denoise_var,
                       style='Custom.TCheckbutton').pack(anchor=tk.W, pady=2)
        
        # Стерео-расширение
        stereo_frame = tk.Frame(extra_inner, bg=self.colors['bg_light'])
        stereo_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(stereo_frame, text="🎧 Стерeo-расширение:",
                bg=self.colors['bg_light'], fg=self.colors['text'],
                font=self.fonts['normal']).pack(side=tk.LEFT)
        
        self.stereo_var = tk.StringVar(value="1.0")
        stereo_entry = tk.Entry(stereo_frame, textvariable=self.stereo_var,
                               bg=self.colors['bg'], fg=self.colors['text'],
                               font=self.fonts['normal'], width=6,
                               relief=tk.FLAT, borderwidth=1)
        stereo_entry.pack(side=tk.LEFT, padx=10)
        
        tk.Label(stereo_frame, text="(1.0=норма, 1.5=широко)",
                bg=self.colors['bg_light'], fg=self.colors['text_dim'],
                font=self.fonts['small']).pack(side=tk.LEFT)
        
        # Эквалайзер
        eq_settings = ttk.LabelFrame(right_column, text="  🎚️ Эквалайзер (±12 dB)  ",
                                     style='Custom.TLabelframe')
        eq_settings.pack(fill=tk.X, pady=5)
        
        eq_inner = tk.Frame(eq_settings, bg=self.colors['bg_light'])
        eq_inner.pack(fill=tk.X, padx=10, pady=5)
        
        # Bass
        bass_frame = tk.Frame(eq_inner, bg=self.colors['bg_light'])
        bass_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(bass_frame, text="🔊 Bass (40 Hz):",
                bg=self.colors['bg_light'], fg=self.colors['text'],
                font=self.fonts['normal'], width=15, anchor=tk.W).pack(side=tk.LEFT)
        
        self.eq_bass_var = tk.StringVar(value="0")
        tk.Entry(bass_frame, textvariable=self.eq_bass_var,
                bg=self.colors['bg'], fg=self.colors['text'],
                font=self.fonts['normal'], width=6,
                relief=tk.FLAT, borderwidth=1).pack(side=tk.LEFT, padx=5)
        
        tk.Label(bass_frame, text="dB",
                bg=self.colors['bg_light'], fg=self.colors['text_dim'],
                font=self.fonts['small']).pack(side=tk.LEFT)
        
        # Mid
        mid_frame = tk.Frame(eq_inner, bg=self.colors['bg_light'])
        mid_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(mid_frame, text="🎙️ Mid (1000 Hz):",
                bg=self.colors['bg_light'], fg=self.colors['text'],
                font=self.fonts['normal'], width=15, anchor=tk.W).pack(side=tk.LEFT)
        
        self.eq_mid_var = tk.StringVar(value="0")
        tk.Entry(mid_frame, textvariable=self.eq_mid_var,
                bg=self.colors['bg'], fg=self.colors['text'],
                font=self.fonts['normal'], width=6,
                relief=tk.FLAT, borderwidth=1).pack(side=tk.LEFT, padx=5)
        
        tk.Label(mid_frame, text="dB",
                bg=self.colors['bg_light'], fg=self.colors['text_dim'],
                font=self.fonts['small']).pack(side=tk.LEFT)
        
        # Treble
        treble_frame = tk.Frame(eq_inner, bg=self.colors['bg_light'])
        treble_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(treble_frame, text="🔔 Treble (10 kHz):",
                bg=self.colors['bg_light'], fg=self.colors['text'],
                font=self.fonts['normal'], width=15, anchor=tk.W).pack(side=tk.LEFT)
        
        self.eq_treble_var = tk.StringVar(value="0")
        tk.Entry(treble_frame, textvariable=self.eq_treble_var,
                bg=self.colors['bg'], fg=self.colors['text'],
                font=self.fonts['normal'], width=6,
                relief=tk.FLAT, borderwidth=1).pack(side=tk.LEFT, padx=5)
        
        tk.Label(treble_frame, text="dB",
                bg=self.colors['bg_light'], fg=self.colors['text_dim'],
                font=self.fonts['small']).pack(side=tk.LEFT)
        
        # Количество потоков
        threads_frame = tk.Frame(eq_inner, bg=self.colors['bg_light'])
        threads_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(threads_frame, text="⚡ Потоков:",
                bg=self.colors['bg_light'], fg=self.colors['text'],
                font=self.fonts['normal'], width=15, anchor=tk.W).pack(side=tk.LEFT)
        
        max_threads = max(1, multiprocessing.cpu_count() - 1)
        self.threads_var = tk.StringVar(value=str(max_threads))
        tk.Entry(threads_frame, textvariable=self.threads_var,
                bg=self.colors['bg'], fg=self.colors['text'],
                font=self.fonts['normal'], width=6,
                relief=tk.FLAT, borderwidth=1).pack(side=tk.LEFT, padx=5)
        
        tk.Label(threads_frame, text=f"(макс: {multiprocessing.cpu_count()})",
                bg=self.colors['bg_light'], fg=self.colors['text_dim'],
                font=self.fonts['small']).pack(side=tk.LEFT)
        
        # === ПРОГРЕСС И КНОПКА ===
        bottom_frame = tk.Frame(self.root, bg=self.colors['bg'], pady=5)
        bottom_frame.pack(fill=tk.X, padx=10, side=tk.BOTTOM)
        
        # Прогресс бар
        progress_container = tk.Frame(bottom_frame, bg=self.colors['bg'])
        progress_container.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_container, variable=self.progress_var,
                                           maximum=100, style='Custom.Horizontal.TProgressbar',
                                           length=400)
        self.progress_bar.pack(fill=tk.X)
        
        # Статус
        self.status_var = tk.StringVar(value="Готов к работе")
        self.status_label = tk.Label(bottom_frame, textvariable=self.status_var,
                                     bg=self.colors['bg'], fg=self.colors['text'],
                                     font=self.fonts['normal'])
        self.status_label.pack(pady=3)
        
        # Кнопка запуска
        self.start_button = self.create_button(bottom_frame, "▶️ Нормализовать файлы",
                                               self.start_normalization,
                                               self.colors['success'], 30)
        self.start_button.pack(pady=3)
    
    def add_files(self):
        """Добавить файлы"""
        filetypes = (
            ("Аудио/Видео", "*.mp3 *.mp4 *.wav *.flac *.aac *.ogg *.m4a *.wma *.avi *.mkv *.mov"),
            ("Все файлы", "*.*")
        )
        
        files = filedialog.askopenfilenames(title="Выберите файлы", filetypes=filetypes)
        
        for file in files:
            if file not in self.files:
                self.files.append(file)
                self.file_listbox.insert(tk.END, Path(file).name)
    
    def add_folder(self):
        """Добавить все файлы из папки"""
        folder = filedialog.askdirectory(title="Выберите папку")
        if not folder:
            return
        
        extensions = ['.mp3', '.mp4', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.avi', '.mkv', '.mov']
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                if Path(file).suffix.lower() in extensions:
                    full_path = os.path.join(root, file)
                    if full_path not in self.files:
                        self.files.append(full_path)
                        self.file_listbox.insert(tk.END, file)
    
    def clear_files(self):
        """Очистить список"""
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
    
    def select_output_folder(self):
        """Выбрать выходную папку"""
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.output_var.set(folder)
    
    def build_audio_filters(self, use_gate, gate_threshold, stereo_width, prevent_clipping, 
                           target_level, mode, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise):
        """Строит цепочку аудио фильтров"""
        audio_filters = []
        
        # HF Denoiser
        if hf_denoise:
            audio_filters.append('afftdn=nr=3:nf=-70:tn=1:om=o')
        
        # EQ - 3-полосный эквалайзер
        if eq_bass != 0:
            audio_filters.append(f'equalizer=f=40:width_type=o:width=2:g={eq_bass}')
        
        if eq_mid != 0:
            audio_filters.append(f'equalizer=f=1000:width_type=o:width=2:g={eq_mid}')
        
        if eq_treble != 0:
            audio_filters.append(f'equalizer=f=10000:width_type=o:width=2:g={eq_treble}')
        
        # Exciter
        if use_exciter:
            audio_filters.append('aexciter=level_in=1:level_out=1:amount=3:drive=8.5:blend=0:freq=7500:ceil=16000:listen=0')
        
        # Noise Gate
        if use_gate:
            if mode == "compressed":
                audio_filters.append(f'agate=threshold={gate_threshold}dB:ratio=5:attack=20:release=200')
            else:
                audio_filters.append(f'agate=threshold={gate_threshold}dB:ratio=10:attack=10:release=100')
        
        # Стерео
        if stereo_width != 1.0:
            audio_filters.append(f'stereotools=mlev={stereo_width}')
        
        # Режимы обработки
        if mode == "compressed":
            # Классика/Опера - сохраняет динамику
            audio_filters.append('acompressor=threshold=-25dB:ratio=1.5:attack=300:release=1500:makeup=0dB')
            
            tp_level = '-4.0' if prevent_clipping else '-3.5'
            lra_value = 14
            audio_filters.append(f'loudnorm=I={target_level}:TP={tp_level}:LRA={lra_value}')
            
            audio_filters.append('alimiter=limit=0.93:attack=3:release=50')
            audio_filters.append('alimiter=limit=0.90:attack=2:release=30')
                
        elif mode == "vocal":
            # Вокальный режим
            audio_filters.append('deesser')
            
            if prevent_clipping:
                audio_filters.append('acompressor=threshold=-15dB:ratio=3:attack=80:release=300')
            
            audio_filters.append('acompressor=threshold=-18dB:ratio=2:attack=100:release=400')
            
            tp_level = '-3.0' if prevent_clipping else '-2.5'
            audio_filters.append(f'loudnorm=I={target_level}:TP={tp_level}:LRA=8')
            
            if prevent_clipping:
                audio_filters.append('alimiter=limit=0.88:attack=2:release=30')
            else:
                audio_filters.append('alimiter=limit=0.92:attack=3:release=40')
        
        elif mode == "music":
            # Музыкальный режим
            audio_filters.append('acompressor=threshold=-22dB:ratio=2:attack=150:release=800:makeup=0dB')
            
            tp_level = '-2.5' if prevent_clipping else '-2.0'
            audio_filters.append(f'loudnorm=I={target_level}:TP={tp_level}:LRA=9')
            
            if prevent_clipping:
                audio_filters.append('alimiter=limit=0.90:attack=3:release=40')
            else:
                audio_filters.append('alimiter=limit=0.94:attack=5:release=60')
        
        else:
            # Обычный режим (normal)
            tp_level = '-3.0' if prevent_clipping else '-2.0'
            audio_filters.append(f'loudnorm=I={target_level}:TP={tp_level}:LRA=11')
            
            if prevent_clipping:
                audio_filters.append('alimiter=limit=0.88:attack=2:release=30')
            else:
                audio_filters.append('alimiter=limit=0.95:attack=5:release=50')
        
        return audio_filters
    
    def normalize_audio(self, input_file, output_file, target_level, is_video, keep_video,
                       use_gate, gate_threshold, stereo_width, prevent_clipping, mode,
                       eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise):
        """Нормализация одного файла"""
        
        base_cmd = ['ffmpeg', '-y', '-threads', '0', '-i', input_file]
        
        audio_filters = self.build_audio_filters(use_gate, gate_threshold, stereo_width,
                                                 prevent_clipping, target_level, mode,
                                                 eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise)
        
        filter_complex = ','.join(audio_filters)
        
        if is_video and keep_video:
            cmd = base_cmd + ['-af', filter_complex, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', output_file]
        else:
            cmd = base_cmd + ['-af', filter_complex, '-c:a', 'libmp3lame', '-b:a', '320k', '-vn', output_file]
        
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore',
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        
        if result.returncode != 0:
            error_msg = f"ffmpeg ошибка: {result.returncode}\n{result.stderr[-500:]}"
            raise Exception(error_msg)
        
        if not os.path.exists(output_file):
            raise Exception(f"Файл не создан: {output_file}")
        
        if os.path.getsize(output_file) < 1000:
            raise Exception(f"Файл слишком маленький (возможно пустой)")
    
    def process_file(self, file_path, output_dir, target_level, suffix, keep_video,
                    use_gate, gate_threshold, stereo_width, prevent_clipping, mode,
                    eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise):
        """Обработка одного файла"""
        try:
            file_name = Path(file_path).stem
            file_ext = Path(file_path).suffix.lower()
            
            is_video = file_ext in ['.mp4', '.avi', '.mkv', '.mov']
            
            if is_video and keep_video:
                output_file = os.path.join(output_dir, f"{file_name}{suffix}.mp4")
            else:
                output_file = os.path.join(output_dir, f"{file_name}{suffix}.mp3")
            
            self.normalize_audio(file_path, output_file, target_level, is_video, keep_video,
                               use_gate, gate_threshold, stereo_width, prevent_clipping, mode,
                               eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise)
            
            return True, file_name
        
        except Exception as e:
            return False, f"{file_name}: {str(e)}"
    
    def start_normalization(self):
        """Запуск нормализации"""
        if not self.files:
            messagebox.showwarning("Внимание", "Добавьте файлы для обработки!")
            return
        
        output_dir = self.output_var.get()
        if output_dir == "Не выбрана":
            messagebox.showwarning("Внимание", "Выберите выходную папку!")
            return
        
        if self.processing:
            messagebox.showinfo("Информация", "Обработка уже выполняется!")
            return
        
        try:
            target_level = float(self.target_var.get())
            if target_level > 0:
                messagebox.showwarning("Внимание", "Целевой уровень должен быть отрицательным (например: -16)")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Неверное значение целевого уровня!")
            return
        
        try:
            gate_threshold = float(self.gate_threshold_var.get())
        except ValueError:
            gate_threshold = -40.0
        
        try:
            stereo_width = float(self.stereo_var.get())
        except ValueError:
            stereo_width = 1.0
        
        try:
            eq_bass = float(self.eq_bass_var.get())
            eq_mid = float(self.eq_mid_var.get())
            eq_treble = float(self.eq_treble_var.get())
        except ValueError:
            eq_bass = eq_mid = eq_treble = 0.0
        
        try:
            max_workers = int(self.threads_var.get())
            max_workers = max(1, min(max_workers, multiprocessing.cpu_count()))
        except ValueError:
            max_workers = max(1, multiprocessing.cpu_count() - 1)
        
        self.processing = True
        self.completed = 0
        self.total = len(self.files)
        self.start_button.config(state=tk.DISABLED, bg=self.colors['text_dim'])
        
        def process_all():
            """Обработка всех файлов в потоках"""
            suffix = self.suffix_var.get()
            keep_video = self.keep_video_var.get()
            use_gate = self.use_gate_var.get()
            prevent_clipping = self.prevent_clipping_var.get()
            mode = self.mode_var.get()
            use_exciter = self.use_exciter_var.get()
            hf_denoise = self.hf_denoise_var.get()
            
            errors = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                
                for file_path in self.files:
                    future = executor.submit(
                        self.process_file, file_path, output_dir, target_level, suffix,
                        keep_video, use_gate, gate_threshold, stereo_width, prevent_clipping,
                        mode, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise
                    )
                    futures.append(future)
                
                for future in futures:
                    success, result = future.result()
                    self.completed += 1
                    
                    progress = (self.completed / self.total) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    self.root.after(0, lambda: self.status_var.set(f"Обработка {self.completed}/{self.total}"))
                    
                    if not success:
                        errors.append(result)
            
            def finish():
                """Завершение обработки"""
                self.processing = False
                self.start_button.config(state=tk.NORMAL, bg=self.colors['success'])
                
                if errors:
                    error_msg = "Ошибки при обработке:\n\n" + "\n".join(errors[:10])
                    if len(errors) > 10:
                        error_msg += f"\n\n... и ещё {len(errors) - 10} ошибок"
                    messagebox.showwarning("Завершено с ошибками", error_msg)
                else:
                    messagebox.showinfo("Готово!", f"Успешно обработано файлов: {self.completed}")
                
                self.status_var.set("Готов к работе")
                self.progress_var.set(0)
            
            self.root.after(0, finish)
        
        thread = threading.Thread(target=process_all, daemon=True)
        thread.start()


def check_ffmpeg():
    """Проверка наличия ffmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return result.returncode == 0
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    if not check_ffmpeg():
        import tkinter.messagebox as mb
        root = tk.Tk()
        root.withdraw()
        mb.showerror("FFmpeg не найден",
                    "FFmpeg не установлен или не добавлен в PATH!\n\n"
                    "Скачайте: https://www.gyan.dev/ffmpeg/builds/\n"
                    "Установите и добавьте в PATH системы.\n\n"
                    "Подробные инструкции в README.md")
        exit(1)
    
    root = tk.Tk()
    app = AudioNormalizer(root)
    root.mainloop()
