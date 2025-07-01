# build_exe.py - Исправленный скрипт для создания OZONScrappy.exe
import os
import sys
import subprocess
import shutil
from pathlib import Path

def get_selenium_stealth_path():
    """Динамически находит путь к selenium_stealth"""
    try:
        import selenium_stealth
        stealth_path = os.path.dirname(selenium_stealth.__file__)
        js_path = os.path.join(stealth_path, 'js')
        
        print(f"✅ Найден путь к selenium_stealth: {stealth_path}")
        print(f"✅ Путь к JS файлам: {js_path}")
        
        # Проверяем существование JS файлов
        if os.path.exists(js_path):
            js_files = os.listdir(js_path)
            print(f"📄 JS файлы: {js_files}")
            return stealth_path, js_path
        else:
            print("❌ Папка JS не найдена")
            return None, None
            
    except ImportError:
        print("❌ selenium_stealth не установлен")
        return None, None

def create_dynamic_spec_file(main_file='main.py', app_name='OZONScrappy', icon_path='logo.ico'):
    """Создает .spec файл с динамически найденными путями"""
    
    stealth_path, js_path = get_selenium_stealth_path()
    
    if not stealth_path:
        print("❌ Не удалось найти selenium_stealth")
        return False
    
    # Проверяем существование иконки
    if not os.path.exists(icon_path):
        print(f"⚠️  Иконка {icon_path} не найдена, создаю без иконки")
        icon_line = ""
    else:
        print(f"✅ Иконка найдена: {icon_path}")
        icon_line = f"    icon='{icon_path}',"
    
    # Нормализуем пути для Windows
    js_path = js_path.replace('\\', '\\\\')
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Auto-generated spec file for {app_name}

block_cipher = None

a = Analysis(
    ['{main_file}'],
    pathex=[],
    binaries=[],
    datas=[
        (r'{js_path}', 'selenium_stealth/js'),
    ],
    hiddenimports=['selenium_stealth', 'selenium', 'undetected_chromedriver'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Без консоли - красивый GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
{icon_line}
)
'''
    
    spec_filename = f'{app_name}.spec'
    
    with open(spec_filename, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ Создан файл: {spec_filename}")
    print(f"🎯 Название приложения: {app_name}")
    print(f"🖼️  Консоль: Отключена (GUI режим)")
    return spec_filename

def build_exe_with_dynamic_paths(main_file='main.py', app_name='OZONScrappy', icon_path='logo.ico'):
    """Полный процесс создания .exe с автоматическим поиском путей"""
    
    print("🔍 Поиск selenium_stealth...")
    spec_file = create_dynamic_spec_file(main_file, app_name, icon_path)
    
    if not spec_file:
        print("❌ Не удалось создать .spec файл")
        return False
    
    print(f"🚀 Сборка {app_name}.exe...")
    try:
        # Запускаем PyInstaller
        result = subprocess.run([
            'pyinstaller', 
            '--clean',  # Очищаем кеш
            spec_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {app_name}.exe успешно создан!")
            print("📁 Проверьте папку dist/")
            print("🎯 Консоль отключена - приложение запускается без черного окна")
            print("🖼️  Иконка установлена (если logo.ico найдена)")
            return True
        else:
            print("❌ Ошибка при сборке:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ PyInstaller не найден. Установите: pip install pyinstaller")
        return False

# Альтернативное решение - исправление путей во время выполнения
def fix_selenium_stealth_runtime():
    """Исправляет пути selenium_stealth во время выполнения .exe"""
    
    import sys
    import os
    from pathlib import Path
    
    if getattr(sys, 'frozen', False):
        # Мы внутри .exe файла
        application_path = Path(sys._MEIPASS)
        
        # Создаем путь для JS файлов
        js_dir = application_path / 'selenium_stealth' / 'js'
        js_dir.mkdir(parents=True, exist_ok=True)
        
        # Основные JS файлы для selenium-stealth
        js_files = {
            'utils.js': '''
// utils.js для selenium-stealth
(function() {
    'use strict';
    
    // Удаляем признаки автоматизации
    if (navigator.webdriver) {
        delete navigator.webdriver;
    }
    
    // Переопределяем navigator.webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });
    
    // Скрываем automation
    window.chrome = {
        runtime: {},
    };
    
    // Переопределяем plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    
    // Переопределяем languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['ru-RU', 'ru'],
    });
    
})();
            ''',
            
            'chrome_runtime.js': '''
// chrome_runtime.js
window.chrome = {
    runtime: {},
};
            ''',
            
            'navigator_vendor.js': '''
// navigator_vendor.js
Object.defineProperty(navigator, 'vendor', {
    get: () => 'Google Inc.',
});
            ''',
            
            'navigator_plugins.js': '''
// navigator_plugins.js  
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});
            '''
        }
        
        # Создаем JS файлы если их нет
        for filename, content in js_files.items():
            js_file = js_dir / filename
            if not js_file.exists():
                js_file.write_text(content.strip(), encoding='utf-8')
        
        print(f"✅ JS файлы созданы в: {js_dir}")
        return True
    
    return False

# Основной код для интеграции в ваш проект
def setup_selenium_stealth():
    """Настройка selenium_stealth с автоматическим исправлением путей"""
    
    # Исправляем пути если мы в .exe
    fix_selenium_stealth_runtime()
    
    try:
        from selenium import webdriver
        from selenium_stealth import stealth
        
        def create_stealth_driver():
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=options)
            
            # Применяем stealth
            stealth(driver,
                languages=["ru-RU", "ru"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            return driver
        
        return create_stealth_driver
        
    except Exception as e:
        print(f"❌ Ошибка selenium_stealth: {e}")
        print("🔄 Переключаемся на undetected-chromedriver")
        
        # Fallback на undetected-chromedriver
        try:
            import undetected_chromedriver as uc
            
            def create_uc_driver():
                options = uc.ChromeOptions()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                return uc.Chrome(options=options)
            
            return create_uc_driver
            
        except ImportError:
            print("❌ Установите: pip install undetected-chromedriver")
            return None

if __name__ == "__main__":
    print("🛠️ Сборщик OZONScrappy.exe с selenium_stealth")
    print("=" * 50)
    
    # Получаем название главного файла
    main_file = input("Введите название главного файла (по умолчанию main.py): ").strip()
    if not main_file:
        main_file = "main.py"
    
    if not os.path.exists(main_file):
        print(f"❌ Файл {main_file} не найден!")
        sys.exit(1)
    
    # Проверяем наличие иконки
    icon_path = "logo.ico"
    if os.path.exists(icon_path):
        print(f"✅ Иконка найдена: {icon_path}")
    else:
        print(f"⚠️  Иконка {icon_path} не найдена - будет использована стандартная")
    
    print()
    print(f"📄 Главный файл: {main_file}")
    print(f"🎯 Название: OZONScrappy.exe")
    print(f"🖼️  Консоль: Отключена")
    print(f"🎨 Иконка: {icon_path}")
    print()
    
    # Создаем .exe
    success = build_exe_with_dynamic_paths(main_file, 'OZONScrappy', icon_path)
    
    if success:
        print()
        print("🎉 Готово! OZONScrappy.exe создан успешно!")
        print("📁 Файл находится в папке dist/OZONScrappy.exe")
        print("✨ Приложение запускается без консоли")
        print("🚀 Можете запускать на любом компьютере!")
    else:
        print()
        print("❌ Возникли проблемы при создании .exe")
