import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from react_export import write_react_project

class TailwindTests(unittest.TestCase):
    def test_static_utilities_and_escaping(self):
        layout=json.loads((Path(__file__).resolve().parents[1]/'tests/fixtures/rounded-layout.json').read_text())
        button=next(e for e in layout['elements'] if e['type']=='button')
        button.update(x=150.5,radius=22,font_size=26,color='#112233',text='<Start & go>')
        with TemporaryDirectory() as temporary:
            output=Path(temporary)/'tailwind'
            write_react_project(layout,'',output,tailwind=True)
            with ZipFile(Path(temporary)/'tailwind.zip') as archive:
                classes=archive.read('src/classes.ts').decode()
                self.assertIn('left-[150.5px]',classes)
                self.assertIn('rounded-[22px]',classes)
                self.assertIn('[font:26px_Arial,sans-serif]',classes)
                self.assertIn('text-[#112233]',classes)
                self.assertIn('element.text',archive.read('src/App.tsx').decode())
                self.assertIn('@tailwindcss/vite',archive.read('vite.config.ts').decode())
                package=json.loads(archive.read('package.json'))
                self.assertIn('tailwindcss',package['devDependencies'])
                self.assertNotIn('#button',archive.read('src/styles.css').decode())
