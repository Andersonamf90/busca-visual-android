import os, sqlite3, threading, hashlib
from urllib.parse import urljoin, urlparse
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button

APP_DIR = os.path.join(os.path.expanduser('~'), 'visual_search')
DB_PATH = os.path.join(APP_DIR, 'visual_index.sqlite3')
IMAGES_DIR = os.path.join(APP_DIR, 'images')
os.makedirs(IMAGES_DIR, exist_ok=True)

KV = r'''
BoxLayout:
    orientation: 'vertical'
    padding: '12dp'
    spacing: '8dp'
    canvas.before:
        Color:
            rgba: 0.055, 0.075, 0.10, 1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: 'Busca Visual'
        font_size: '24sp'
        bold: True
        size_hint_y: None
        height: '44dp'
        color: 0.95, 0.97, 1, 1
    Label:
        text: 'Índice local de imagens + consulta de páginas públicas'
        font_size: '13sp'
        size_hint_y: None
        height: '32dp'
        color: 0.72, 0.78, 0.86, 1
    Button:
        text: '1. Selecionar foto para comparar'
        size_hint_y: None
        height: '48dp'
        on_release: app.pick_query_image()
    Label:
        text: app.query_path
        size_hint_y: None
        height: '48dp'
        text_size: self.width, None
        halign: 'left'
        color: 0.9, 0.9, 0.9, 1
    Button:
        text: '2. Comparar com o índice local'
        size_hint_y: None
        height: '48dp'
        on_release: app.search_local()
    BoxLayout:
        size_hint_y: None
        height: '44dp'
        spacing: '6dp'
        TextInput:
            id: page_url
            hint_text: 'https://exemplo.com/pagina-publica'
            multiline: False
            input_type: 'url'
        Button:
            text: 'Indexar'
            size_hint_x: None
            width: '100dp'
            on_release: app.index_page(page_url.text)
    Label:
        text: 'O índice guarda imagens públicas e seus links. Respeite os termos e limites dos sites.'
        size_hint_y: None
        height: '42dp'
        font_size: '12sp'
        color: 0.72, 0.78, 0.86, 1
        text_size: self.width, None
    ScrollView:
        do_scroll_x: False
        Label:
            text: app.status
            size_hint_y: None
            height: self.texture_size[1] + dp(24)
            text_size: self.width - dp(12), None
            halign: 'left'
            valign: 'top'
            color: 0.95, 0.97, 1, 1
'''

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_path TEXT NOT NULL,
        source_url TEXT NOT NULL,
        image_hash TEXT NOT NULL,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(source_url, image_hash))''')
    conn.commit()
    return conn

def perceptual_hash(img_bytes):
    """Hash perceptual simples para imagens inteiras; não reconhece rostos."""
    with Image.open(BytesIO(img_bytes)) as im:
        im = ImageOps.exif_transpose(im).convert('L').resize((8, 8))
        px = list(im.getdata())
    avg = sum(px) / len(px)
    bits = ''.join('1' if p >= avg else '0' for p in px)
    return f'{int(bits, 2):016x}'

def hash_distance(a, b):
    try:
        return (int(a, 16) ^ int(b, 16)).bit_count()
    except Exception:
        return 64

class BuscaVisualApp(App):
    query_path = StringProperty('Nenhuma foto selecionada.')
    status = StringProperty('Projeto inicial pronto.\n\nEsta versão compara a semelhança visual da imagem inteira. O motor de reconhecimento facial ainda precisa ser integrado e validado para Android.')

    def build(self):
        db().close()
        return Builder.load_string(KV)

    def popup_message(self, title, message):
        content = BoxLayout(orientation='vertical', padding=12, spacing=8)
        content.add_widget(Label(text=message))
        btn = Button(text='OK', size_hint_y=None, height='44dp')
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.9, 0.55))
        btn.bind(on_release=popup.dismiss)
        popup.open()

    def pick_query_image(self):
        start = '/storage/emulated/0'
        if not os.path.isdir(start): start = os.path.expanduser('~')
        chooser = FileChooserListView(path=start, filters=['*.jpg', '*.jpeg', '*.png', '*.webp', '*.bmp'])
        layout = BoxLayout(orientation='vertical', spacing=6, padding=6)
        layout.add_widget(chooser)
        row = BoxLayout(size_hint_y=None, height='44dp', spacing=6)
        choose, cancel = Button(text='Usar foto'), Button(text='Cancelar')
        row.add_widget(choose); row.add_widget(cancel); layout.add_widget(row)
        popup = Popup(title='Escolher imagem', content=layout, size_hint=(0.95, 0.9))
        def use_file(*_):
            if chooser.selection:
                self.query_path = chooser.selection[0]
                self.status = 'Foto selecionada:\n' + self.query_path + '\n\nToque em comparar para consultar o índice local.'
                popup.dismiss()
        choose.bind(on_release=use_file); cancel.bind(on_release=popup.dismiss); popup.open()

    def search_local(self):
        if not self.query_path or not os.path.isfile(self.query_path):
            self.popup_message('Selecione uma foto', 'Escolha uma imagem antes de pesquisar.'); return
        try:
            with open(self.query_path, 'rb') as f: qh = perceptual_hash(f.read())
            conn = db(); rows = conn.execute('SELECT image_path, source_url, image_hash FROM images').fetchall(); conn.close()
            if not rows:
                self.status = 'O índice está vazio. Informe uma página pública e toque em Indexar.'; return
            ranked = sorted([(hash_distance(qh, row[2]), row[0], row[1]) for row in rows], key=lambda x: x[0])[:10]
            lines = ['Resultados por semelhança visual (não é reconhecimento facial):', '']
            for dist, path, url in ranked:
                similarity = max(0, 100 * (1 - dist / 64))
                lines += [f'{similarity:.1f}% de semelhança visual aproximada', f'Arquivo: {path}', f'Página: {url}', '']
            self.status = '\n'.join(lines)
        except Exception as e: self.status = f'Falha na pesquisa: {e}'

    def index_page(self, url):
        url = (url or '').strip(); parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            self.popup_message('Endereço inválido', 'Digite um endereço completo começando com https:// ou http://.'); return
        self.status = 'Consultando a página pública...'
        threading.Thread(target=self._index_page_worker, args=(url,), daemon=True).start()

    def _index_page_worker(self, url):
        added, errors = 0, []
        try:
            headers = {'User-Agent': 'BuscaVisualAndroid/0.1 (indexação limitada de imagens públicas)'}
            response = requests.get(url, headers=headers, timeout=15); response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser'); image_urls = []
            for tag in soup.find_all('img'):
                src = tag.get('src') or tag.get('data-src')
                if src: image_urls.append(urljoin(url, src))
            for image_url in image_urls[:40]:
                try:
                    if urlparse(image_url).scheme not in ('http', 'https'): continue
                    r = requests.get(image_url, headers=headers, timeout=12, stream=True); r.raise_for_status()
                    if not r.headers.get('Content-Type', '').startswith('image/'):
                        r.close(); continue
                    data = r.content
                    if not data or len(data) > 8 * 1024 * 1024: continue
                    ph = perceptual_hash(data)
                    name = hashlib.sha256((image_url + ph).encode('utf-8')).hexdigest()[:24] + '.jpg'
                    out_path = os.path.join(IMAGES_DIR, name)
                    if not os.path.exists(out_path):
                        with open(out_path, 'wb') as f: f.write(data)
                    conn = db()
                    cur = conn.execute('INSERT OR IGNORE INTO images(image_path, source_url, image_hash) VALUES(?,?,?)', (out_path, url, ph))
                    added += cur.rowcount; conn.commit(); conn.close()
                except Exception as e: errors.append(str(e)[:120])
        except Exception as e: errors.append(str(e)[:200])
        message = f'Indexação concluída.\nNovos registros: {added}\nPágina: {url}'
        if errors: message += '\nAlgumas imagens não estavam acessíveis; isso é comum em páginas que bloqueiam coleta.'
        Clock.schedule_once(lambda _dt: self._set_status(message), 0)

    def _set_status(self, value): self.status = value

if __name__ == '__main__': BuscaVisualApp().run()
