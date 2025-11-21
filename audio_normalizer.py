import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
from pathlib import Path
import subprocess
import threading
import json
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

class AudioNormalizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Нормализация громкости аудио")
        self.root.geometry("800x620")
        
        self.root.resizable(True, True)
        
        self.files = []
        self.processing = False
        self.completed = 0
        self.total = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        # Фрейм для кнопок выбора файлов
        btn_frame = tk.Frame(self.root, pady=3)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="Добавить файлы", 
                 command=self.add_files, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Добавить папку", 
                 command=self.add_folder, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Очистить список", 
                 command=self.clear_files, width=15).pack(side=tk.LEFT, padx=5)
        
        # Список файлов
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=3)
        
        tk.Label(list_frame, text="Файлы для обработки:", font=('Arial', 8)).pack(anchor=tk.W)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=4, font=('Arial', 8))
        self.file_listbox.pack(fill=tk.BOTH, expand=False)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Настройки - ДВЕ КОЛОНКИ
        settings_main = tk.LabelFrame(self.root, text="Настройки", pady=5, font=('Arial', 8))
        settings_main.pack(fill=tk.BOTH, expand=True, padx=10, pady=3)
        
        # Создаем две колонки
        left_column = tk.Frame(settings_main)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
        
        right_column = tk.Frame(settings_main)
        right_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
        
        # ЛЕВАЯ КОЛОНКА
        # Режим обработки
        tk.Label(left_column, text="Режим:", font=('Arial', 8, 'bold')).pack(anchor=tk.W, pady=(0,2))
        
        self.mode_var = tk.StringVar(value="normal")
        tk.Radiobutton(left_column, text="Обычный", variable=self.mode_var, value="normal", font=('Arial', 8)).pack(anchor=tk.W, padx=8, pady=0)
        tk.Radiobutton(left_column, text="Опера/классика", variable=self.mode_var, value="compressed", font=('Arial', 8)).pack(anchor=tk.W, padx=8, pady=0)
        tk.Radiobutton(left_column, text="Вокальный", variable=self.mode_var, value="vocal", font=('Arial', 8)).pack(anchor=tk.W, padx=8, pady=0)
        
        # Защита от перегрузов + ВЧ шум - В ОДНУ СТРОКУ
        opts_frame = tk.Frame(left_column)
        opts_frame.pack(fill=tk.X, pady=2)
        
        self.prevent_clipping_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="🛡️ Защита", 
                      variable=self.prevent_clipping_var, font=('Arial', 7), fg='red').pack(side=tk.LEFT, padx=2)
        
        self.hf_denoise_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="🔇 Шум ВЧ", 
                      variable=self.hf_denoise_var, font=('Arial', 7), fg='purple').pack(side=tk.LEFT, padx=2)
        
        self.exciter_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opts_frame, text="✨ Яркость", 
                      variable=self.exciter_var, font=('Arial', 7), fg='blue').pack(side=tk.LEFT, padx=2)
        
        # EQ - КОМПАКТНО
        tk.Label(left_column, text="EQ (dB):", font=('Arial', 8, 'bold')).pack(anchor=tk.W, pady=(3,1))
        
        eq_frame = tk.Frame(left_column)
        eq_frame.pack(fill=tk.X, padx=8, pady=1)
        
        # Низ, Сред, Верх в одну строку
        eq_bass_frame = tk.Frame(eq_frame)
        eq_bass_frame.pack(fill=tk.X)
        tk.Label(eq_bass_frame, text="Низ:", font=('Arial', 7), width=5, anchor='w').pack(side=tk.LEFT)
        self.eq_bass_var = tk.StringVar(value="0")
        tk.Entry(eq_bass_frame, textvariable=self.eq_bass_var, width=5, font=('Arial', 7)).pack(side=tk.LEFT, padx=2)
        
        tk.Label(eq_bass_frame, text="Сред:", font=('Arial', 7), width=5, anchor='w').pack(side=tk.LEFT, padx=(5,0))
        self.eq_mid_var = tk.StringVar(value="0")
        tk.Entry(eq_bass_frame, textvariable=self.eq_mid_var, width=5, font=('Arial', 7)).pack(side=tk.LEFT, padx=2)
        
        tk.Label(eq_bass_frame, text="Верх:", font=('Arial', 7), width=5, anchor='w').pack(side=tk.LEFT, padx=(5,0))
        self.eq_treble_var = tk.StringVar(value="0")
        tk.Entry(eq_bass_frame, textvariable=self.eq_treble_var, width=5, font=('Arial', 7)).pack(side=tk.LEFT, padx=2)
        
        # Стерео
        tk.Label(left_column, text="Стерео:", font=('Arial', 8, 'bold')).pack(anchor=tk.W, pady=(3,1))
        
        stereo_frame = tk.Frame(left_column)
        stereo_frame.pack(fill=tk.X, padx=8)
        
        self.stereo_width_var = tk.StringVar(value="1.0")
        tk.Entry(stereo_frame, textvariable=self.stereo_width_var, width=5, font=('Arial', 7)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(stereo_frame, text="1.0", command=lambda: self.stereo_width_var.set("1.0"), width=3, font=('Arial', 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(stereo_frame, text="0.7", command=lambda: self.stereo_width_var.set("0.7"), width=3, font=('Arial', 7)).pack(side=tk.LEFT, padx=1)
        tk.Button(stereo_frame, text="0.5", command=lambda: self.stereo_width_var.set("0.5"), width=3, font=('Arial', 7)).pack(side=tk.LEFT, padx=1)
        
        # ПРАВАЯ КОЛОНКА
        # Целевой уровень
        tk.Label(right_column, text="Целевой уровень (dB):", font=('Arial', 8, 'bold')).pack(anchor=tk.W)
        
        target_frame = tk.Frame(right_column)
        target_frame.pack(fill=tk.X, pady=2, padx=8)
        self.target_level_var = tk.StringVar(value="-16")
        tk.Entry(target_frame, textvariable=self.target_level_var, width=8, font=('Arial', 8)).pack(side=tk.LEFT, padx=2)
        tk.Label(target_frame, text="(-16 муз, -18 опера)", font=('Arial', 7), fg='gray').pack(side=tk.LEFT)
        
        # Шумоподавление
        tk.Label(right_column, text="Шумоподавление:", font=('Arial', 8, 'bold')).pack(anchor=tk.W, pady=(3,1))
        
        self.use_gate_var = tk.BooleanVar(value=False)
        
        gate_frame = tk.Frame(right_column)
        gate_frame.pack(fill=tk.X, padx=8)
        
        tk.Checkbutton(gate_frame, text="Вкл", variable=self.use_gate_var, font=('Arial', 7)).pack(side=tk.LEFT)
        tk.Label(gate_frame, text="Порог:", font=('Arial', 7)).pack(side=tk.LEFT, padx=(5,2))
        self.gate_threshold_var = tk.StringVar(value="-50")
        tk.Entry(gate_frame, textvariable=self.gate_threshold_var, width=6, font=('Arial', 7)).pack(side=tk.LEFT, padx=2)
        tk.Label(gate_frame, text="dB", font=('Arial', 7)).pack(side=tk.LEFT)
        
        # MP4
        tk.Label(right_column, text="MP4:", font=('Arial', 8, 'bold')).pack(anchor=tk.W, pady=(3,1))
        
        mp4_frame = tk.Frame(right_column)
        mp4_frame.pack(fill=tk.X, padx=8)
        
        self.mp4_output_var = tk.StringVar(value="mp3")
        tk.Radiobutton(mp4_frame, text="→MP3", variable=self.mp4_output_var, value="mp3", font=('Arial', 7)).pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(mp4_frame, text="→MP4", variable=self.mp4_output_var, value="mp4", font=('Arial', 7)).pack(side=tk.LEFT, padx=2)
        
        # Потоки
        tk.Label(right_column, text="Потоки:", font=('Arial', 8, 'bold')).pack(anchor=tk.W, pady=(3,1))
        
        threads_frame = tk.Frame(right_column)
        threads_frame.pack(fill=tk.X, padx=8)
        
        cpu_count = multiprocessing.cpu_count()
        self.threads_var = tk.StringVar(value=str(cpu_count))
        tk.Entry(threads_frame, textvariable=self.threads_var, width=6, font=('Arial', 7)).pack(side=tk.LEFT, padx=2)
        tk.Label(threads_frame, text=f"(ядер: {cpu_count})", font=('Arial', 7), fg='gray').pack(side=tk.LEFT)
        
        # Суффикс
        tk.Label(right_column, text="Суффикс:", font=('Arial', 8, 'bold')).pack(anchor=tk.W, pady=(3,1))
        
        suffix_frame = tk.Frame(right_column)
        suffix_frame.pack(fill=tk.X, padx=8)
        self.suffix_var = tk.StringVar(value="_normalized")
        tk.Entry(suffix_frame, textvariable=self.suffix_var, width=18, font=('Arial', 7)).pack(side=tk.LEFT)
        
        # Выходная папка
        output_main = tk.Frame(self.root)
        output_main.pack(fill=tk.X, padx=10, pady=3)
        
        tk.Label(output_main, text="Папка:", font=('Arial', 8, 'bold')).pack(anchor=tk.W)
        
        output_entry_frame = tk.Frame(output_main)
        output_entry_frame.pack(fill=tk.X, pady=2)
        
        self.output_var = tk.StringVar(value="")
        tk.Entry(output_entry_frame, textvariable=self.output_var, font=('Arial', 8)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Button(output_entry_frame, text="Выбрать", command=self.select_output_folder, width=8, font=('Arial', 8)).pack(side=tk.LEFT)
        
        # Прогресс-бар
        progress_frame = tk.Frame(self.root)
        progress_frame.pack(fill=tk.X, padx=10, pady=3)
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X)
        
        self.status_label = tk.Label(progress_frame, text="Готов к работе", font=('Arial', 8))
        self.status_label.pack()
        
        # Кнопка обработки
        self.process_btn = tk.Button(self.root, text="НОРМАЛИЗОВАТЬ ФАЙЛЫ", 
                                     command=self.process_files, 
                                     bg='green', fg='white', height=2, font=('Arial', 10, 'bold'))
        self.process_btn.pack(fill=tk.X, padx=10, pady=5)
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Выберите аудио/видео файлы",
            filetypes=[
                ("Все поддерживаемые", "*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.mp4 *.avi *.mkv *.mov"),
                ("Аудио файлы", "*.mp3 *.wav *.flac *.ogg *.m4a *.aac"),
                ("Видео файлы", "*.mp4 *.avi *.mkv *.mov"),
                ("Все файлы", "*.*")
            ]
        )
        for file in files:
            if file not in self.files:
                self.files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
    
    def add_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с аудио/видео файлами")
        if folder:
            audio_video_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.mp4', '.avi', '.mkv', '.mov'}
            for file_path in Path(folder).rglob('*'):
                if file_path.suffix.lower() in audio_video_extensions:
                    file_str = str(file_path)
                    if file_str not in self.files:
                        self.files.append(file_str)
                        self.file_listbox.insert(tk.END, file_path.name)
    
    def clear_files(self):
        self.files = []
        self.file_listbox.delete(0, tk.END)
    
    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Выберите выходную папку")
        if folder:
            self.output_var.set(folder)
    
    def update_progress(self):
        if self.total > 0:
            progress_value = (self.completed / self.total) * 100
            self.progress['value'] = progress_value
            self.status_label.config(text=f"Обработка {self.completed}/{self.total} файлов...")
    
    def is_video_file(self, file_path):
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov'}
        return Path(file_path).suffix.lower() in video_extensions
    
    def build_audio_filters(self, use_gate, gate_threshold, stereo_width, prevent_clipping, target_level, mode, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise):
        """Строит цепочку аудио фильтров"""
        audio_filters = []
        
        # АДАПТИВНОЕ шумоподавление
        if hf_denoise:
            audio_filters.append('afftdn=nr=4:nf=-65:tn=1:om=o')
        
        # EQ - 3-полосный эквалайзер
        if eq_bass != 0:
            audio_filters.append(f'equalizer=f=60:width_type=o:width=2:g={eq_bass}')
        
        if eq_mid != 0:
            audio_filters.append(f'equalizer=f=1000:width_type=o:width=2:g={eq_mid}')
        
        if eq_treble != 0:
            audio_filters.append(f'equalizer=f=10000:width_type=o:width=2:g={eq_treble}')
        
        # Exciter
        if use_exciter:
            audio_filters.append('aexciter=level_in=1:level_out=1:amount=3:drive=8.5:blend=0:freq=7500:ceil=16000:listen=0')
        
        # Шумоподавление (gate)
        if use_gate and gate_threshold < -55:
            if mode == "compressed":
                audio_filters.append(f'agate=threshold={gate_threshold}dB:ratio=5:attack=20:release=200')
            else:
                audio_filters.append(f'agate=threshold={gate_threshold}dB:ratio=10:attack=10:release=100')
        
        # Стерео
        if stereo_width != 1.0:
            audio_filters.append(f'stereotools=mlev={stereo_width}')
        
        # Режимы обработки
        if mode == "compressed":
            # Опера/классика - БЕЗ ДАВЛЕНИЯ, только защита от перегрузов
            
            # 1. ОДНА очень мягкая компрессия (как раньше)
            audio_filters.append('acompressor=threshold=-25dB:ratio=1.5:attack=300:release=1500:makeup=0dB')
            
            # 2. Loudnorm с запасом по пикам (предотвращает перегрузы)
            tp_level = '-4.0' if prevent_clipping else '-3.5'  # Больший запас чем раньше
            lra_value = 14  # Большой динамический диапазон
            audio_filters.append(f'loudnorm=I={target_level}:TP={tp_level}:LRA={lra_value}')
            
            # 3. ДВА мягких лимитера - только страховка, не давят
            # Первый лимитер - очень мягкий
            audio_filters.append('alimiter=limit=0.93:attack=3:release=50')
            # Второй лимитер - финальная защита
            audio_filters.append('alimiter=limit=0.90:attack=2:release=30')
                
        elif mode == "vocal":
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
        else:
            # Обычный режим
            tp_level = '-3.0' if prevent_clipping else '-2.0'
            audio_filters.append(f'loudnorm=I={target_level}:TP={tp_level}:LRA=11')
            
            if prevent_clipping:
                audio_filters.append('alimiter=limit=0.88:attack=2:release=30')
            else:
                audio_filters.append('alimiter=limit=0.95:attack=5:release=50')
        
        return audio_filters
    
    def normalize_audio(self, input_file, output_file, target_level, is_video, keep_video, use_gate, gate_threshold, stereo_width, prevent_clipping, mode, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise):
        """Универсальная функция нормализации"""
        
        base_cmd = ['ffmpeg', '-y', '-threads', '0', '-i', input_file]
        
        audio_filters = self.build_audio_filters(use_gate, gate_threshold, stereo_width, prevent_clipping, target_level, mode, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise)
        
        filter_complex = ','.join(audio_filters)
        
        if is_video and keep_video:
            cmd = base_cmd + ['-af', filter_complex, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', output_file]
        else:
            cmd = base_cmd + ['-af', filter_complex, '-c:a', 'libmp3lame', '-b:a', '320k', '-vn', output_file]
        
        result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='ignore',
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        
        if result.returncode != 0:
            error_msg = f"ffmpeg код ошибки: {result.returncode}\n{result.stderr[-500:]}"
            raise Exception(error_msg)
        
        if not os.path.exists(output_file):
            raise Exception(f"Файл не создан: {output_file}")
        
        if os.path.getsize(output_file) < 1000:
            raise Exception(f"Файл слишком маленький: {os.path.getsize(output_file)} bytes")
    
    def process_files(self):
        if not self.files:
            messagebox.showwarning("Предупреждение", "Добавьте файлы")
            return
        
        output_folder = self.output_var.get()
        if not output_folder:
            messagebox.showwarning("Предупреждение", "Выберите выходную папку")
            return
        
        try:
            target_level = float(self.target_level_var.get())
            gate_threshold = float(self.gate_threshold_var.get())
            stereo_width = float(self.stereo_width_var.get())
            num_threads = int(self.threads_var.get())
            eq_bass = float(self.eq_bass_var.get())
            eq_mid = float(self.eq_mid_var.get())
            eq_treble = float(self.eq_treble_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте числовые значения")
            return
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        self.processing = True
        self.completed = 0
        self.total = len(self.files)
        self.process_btn.config(state='disabled')
        
        mode = self.mode_var.get()
        mp4_output = self.mp4_output_var.get()
        use_gate = self.use_gate_var.get()
        prevent_clipping = self.prevent_clipping_var.get()
        use_exciter = self.exciter_var.get()
        hf_denoise = self.hf_denoise_var.get()
        
        thread = threading.Thread(target=self.process_thread, 
                                 args=(output_folder, target_level, num_threads, mode, mp4_output, use_gate, gate_threshold, stereo_width, prevent_clipping, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise))
        thread.start()
    
    def process_single_file(self, file_path, output_folder, suffix, target_level, mode, mp4_output, use_gate, gate_threshold, stereo_width, prevent_clipping, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise):
        try:
            filename = Path(file_path).stem
            input_extension = Path(file_path).suffix.lower()
            
            is_video = self.is_video_file(file_path)
            
            if is_video and mp4_output == "mp4":
                output_extension = input_extension
                keep_video = True
            else:
                output_extension = '.mp3'
                keep_video = False
            
            output_file = os.path.join(output_folder, f"{filename}{suffix}{output_extension}")
            
            self.normalize_audio(file_path, output_file, target_level, is_video, keep_video, use_gate, gate_threshold, stereo_width, prevent_clipping, mode, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise)
            
            return True, file_path
        except Exception as e:
            return False, (file_path, str(e))
    
    def process_thread(self, output_folder, target_level, num_threads, mode, mp4_output, use_gate, gate_threshold, stereo_width, prevent_clipping, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise):
        suffix = self.suffix_var.get()
        
        self.root.after(0, self.update_progress)
        
        success_count = 0
        error_count = 0
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for file_path in self.files:
                future = executor.submit(self.process_single_file, file_path, output_folder, suffix, target_level, mode, mp4_output, use_gate, gate_threshold, stereo_width, prevent_clipping, eq_bass, eq_mid, eq_treble, use_exciter, hf_denoise)
                futures.append((future, file_path))
            
            for future, file_path in futures:
                try:
                    success, result = future.result()
                    self.completed += 1
                    
                    if not success:
                        error_count += 1
                        error_file, error_msg = result
                        self.root.after(0, lambda f=error_file, e=error_msg: 
                            messagebox.showerror("Ошибка", f"{os.path.basename(f)}:\n\n{e}"))
                    else:
                        success_count += 1
                    
                    self.root.after(0, self.update_progress)
                    
                except Exception as e:
                    error_count += 1
                    self.root.after(0, lambda e=e: messagebox.showerror("Ошибка", str(e)))
        
        def finish():
            self.status_label.config(text=f"Готово! Успешно: {success_count}, Ошибок: {error_count}")
            self.process_btn.config(state='normal')
            self.processing = False
            
            if success_count > 0:
                messagebox.showinfo("Готово", 
                    f"Успешно: {success_count}\nОшибок: {error_count}\n\nПапка:\n{output_folder}")
            else:
                messagebox.showerror("Ошибка", "Ни один файл не обработан!")
        
        self.root.after(0, finish)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioNormalizer(root)
    root.mainloop()