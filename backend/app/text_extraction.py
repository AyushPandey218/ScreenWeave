"""Optional OCR text separation with classical inpainting; always preview first."""
import io
import cv2
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR
from .baseline import inspect_image
from .media import image_source
from .typography import text_style


def extract_text(payload):
    inspect_image(payload)
    rgb=np.asarray(Image.open(io.BytesIO(payload)).convert('RGB'))
    h,w=rgb.shape[:2]
    engine=RapidOCR(intra_op_num_threads=2,inter_op_num_threads=1,max_side_len=960,det_limit_side_len=960,det_limit_type='max')
    found,_=engine(payload,use_cls=False)
    mask=np.zeros((h,w),np.uint8)
    texts=[]
    for polygon,value,confidence in found or []:
        if confidence < .65 or not value.strip():
            continue
        points=np.asarray(polygon)
        x,y=np.maximum(0,np.floor(points.min(axis=0)).astype(int))
        right,bottom=np.minimum([w,h],np.ceil(points.max(axis=0)).astype(int))
        if right<=x or bottom<=y:
            continue
        box={'x':int(x),'y':int(y),'width':int(right-x),'height':int(bottom-y),'text':value}
        style=text_style(rgb,box)
        texts.append({**box,**style,'id':f'extracted-{len(texts)}','type':'text'})
        # Restrict cleanup to the OCR polygon, padded to include antialiased edges.
        cv2.fillPoly(mask,[points.astype('int32')],255)
        if len(texts)>=100:
            break
    if not texts:
        raise ValueError('No confident text found in this image. Try a larger or clearer image.')
    mask=cv2.dilate(mask,np.ones((3,3),np.uint8))
    cleaned=cv2.inpaint(rgb,mask,3,cv2.INPAINT_TELEA)
    return {'version':1,'viewport':{'width':w,'height':h},'background':'#ffffff','elements':[{'id':'cleaned-image','type':'image','x':0,'y':0,'width':w,'height':h,'src':image_source(cleaned)},*texts],'limitations':['Text removal uses classical inpainting and may leave artifacts on detailed backgrounds.','OCR and font matching are estimates. Review the preview before applying.']}
