import base64, io, unittest
from unittest.mock import patch
import numpy as np
from PIL import Image, ImageDraw
from app.shapes import detect_shapes
from app.media import image_source
from app.layout import Layout
from reconstruct import reconstruct

class MediaTests(unittest.TestCase):
    def fixture(self):
        image=np.full((340,700,3),18,dtype=np.uint8)
        rng=np.random.default_rng(42)
        for x in (20,370):
            image[30:210,x:x+300]=rng.integers(0,256,(180,300,3),dtype=np.uint8)
        return image
    def test_whole_regions_replace_fragments(self):
        shapes=detect_shapes(self.fixture(),[])
        self.assertEqual(len(shapes),2)
        for photo in shapes:
            self.assertIn('src',photo)
            self.assertAlmostEqual(photo['width'],300,delta=3)
            self.assertAlmostEqual(photo['height'],180,delta=3)
    def test_large_asset_roundtrips_schema(self):
        src=image_source(np.random.default_rng(3).integers(0,256,(700,900,3),dtype=np.uint8))
        self.assertLessEqual(len(src),200000)
        Image.open(io.BytesIO(base64.b64decode(src.split(',')[1]))).verify()
        Layout.model_validate({'viewport':{'width':900,'height':700},'background':'#ffffff','elements':[{'id':'photo','type':'image','x':0,'y':0,'width':900,'height':700,'src':src}]})
    def test_photo_text_not_duplicated(self):
        stream=io.BytesIO();Image.fromarray(self.fixture()).save(stream,format='PNG')
        found=[([[40,60],[130,60],[130,80],[40,80]],'In photo',.99),([[20,260],[120,260],[120,280],[20,280]],'Caption',.99)]
        with patch('reconstruct.RapidOCR') as engine:
            engine.return_value.return_value=(found,None)
            result=reconstruct(stream.getvalue())
        self.assertEqual([e['text'] for e in result['elements'] if e['type']=='text'],['Caption'])
        Layout.model_validate(result)
    def test_left_aligned_placeholder_stays_text(self):
        image=Image.new('RGB',(450,160),'#eeeeee');ImageDraw.Draw(image).rounded_rectangle((30,40,420,100),radius=20,fill='white',outline='#333333',width=2)
        stream=io.BytesIO();image.save(stream,format='PNG')
        with patch('reconstruct.RapidOCR') as engine:
            engine.return_value.return_value=([([[50,60],[140,60],[140,80],[50,80]],'Email address',.99)],None)
            result=reconstruct(stream.getvalue())
        self.assertEqual([e['type'] for e in result['elements']],['input','text'])

    def test_monochrome_photo_regions(self):
        rgb=self.fixture()
        gray=np.repeat(rgb.mean(axis=2).astype('uint8')[:,:,None],3,axis=2)
        shapes=detect_shapes(gray,[])
        self.assertEqual(len(shapes),2)
        self.assertTrue(all('src' in s for s in shapes))

    def test_font_family_exports(self):
        from app.main import package_layout
        from zipfile import ZipFile
        layout=Layout.model_validate({'viewport':{'width':300,'height':100},'background':'#ffffff','elements':[{'id':'title','type':'text','x':10,'y':10,'width':200,'height':40,'text':'Serif title','font_family':'serif'}]}).model_dump(exclude_none=True)
        result=package_layout(layout)
        self.assertIn('font-family:"Times New Roman",serif',result['css'])
        for kind in ('react','tailwind'):
            archive=ZipFile(io.BytesIO(base64.b64decode(result['exports'][kind])))
            self.assertIn('"font_family": "serif"',archive.read('src/layout.json').decode())
        self.assertIn("Times_New_Roman",archive.read('src/classes.ts').decode())
