import base64,io,unittest
from unittest.mock import patch
from PIL import Image,ImageDraw
import numpy as np
from fastapi.testclient import TestClient
from app.main import app,job_lock
from app.text_extraction import extract_text
from app.responsive import groups,responsive_css
from app.layout import Layout

class AdvancedTests(unittest.TestCase):
    def image(self):
        image=Image.new('RGB',(300,120),'#dce8ed');ImageDraw.Draw(image).text((20,30),'HELLO',fill='black');b=io.BytesIO();image.save(b,format='PNG');return image,b.getvalue()
    def test_text_separation_and_unchanged_exterior(self):
        original,payload=self.image()
        with patch('app.text_extraction.RapidOCR') as engine:
            engine.return_value.return_value=([([[19,29],[65,29],[65,45],[19,45]],'HELLO',.99)],None)
            layout=extract_text(payload)
        Layout.model_validate(layout)
        self.assertEqual([e['type'] for e in layout['elements']],['image','text'])
        cleaned=np.asarray(Image.open(io.BytesIO(base64.b64decode(layout['elements'][0]['src'].split(',')[1]))))
        np.testing.assert_array_equal(cleaned[80:],np.asarray(original)[80:])
        self.assertFalse(np.array_equal(cleaned,np.asarray(original)))
    def test_no_text_and_invalid_upload(self):
        _,payload=self.image()
        with patch('app.text_extraction.RapidOCR') as engine:
            engine.return_value.return_value=(None,None)
            self.assertEqual(TestClient(app).post('/extract-text',content=payload).status_code,422)
        self.assertEqual(TestClient(app).post('/extract-text',content=b'invalid').status_code,422)
        with job_lock:
            self.assertEqual(TestClient(app).post('/extract-text',content=payload).status_code,429)
    def test_group_membership_and_cycles(self):
        layout={'viewport':{'width':1000,'height':600},'responsive':True,'elements':[{'id':'card','type':'container','x':20,'y':20,'width':300,'height':180},{'id':'label','type':'text','x':40,'y':40,'width':200,'height':30,'parent_id':'card'},{'id':'card2','type':'container','x':400,'y':20,'width':300,'height':180}]}
        self.assertEqual(groups(layout)[0]['ids'],['card','label'])
        self.assertIn('@media(max-width:640px)',responsive_css(layout))
        layout['elements'][0]['parent_id']='label'
        self.assertEqual(sum(len(g['ids']) for g in groups(layout)),3)
