import io
import unittest
import pymupdf
from pypdf import PdfReader
from .test_service import ServiceTest
from .pypdf_workbench import TOOLS
from .operations import parse_pages


class PypdfTest(ServiceTest):
    def run_pypdf(self, tool, options=None, ids=None):
        return self.client.post(f'/api/v1/pymupdf/pypdf/operations/{tool}',json={'file_ids':ids or [self.id],'options':options or {}},headers=self.headers)

    def test_pypdf_menu_operations(self):
        with pymupdf.open(stream=self.pdf,filetype='pdf') as doc:
            image=self.upload(doc[0].get_pixmap().tobytes('png'),'image.png')['id']
        with pymupdf.open() as doc:
            page=doc.new_page()
            widget=pymupdf.Widget();widget.field_name='Name';widget.field_type=pymupdf.PDF_WIDGET_TYPE_TEXT;widget.rect=pymupdf.Rect(20,20,200,50)
            page.add_widget(widget)
            form=self.upload(doc.tobytes(),'form.pdf')['id']
        for tool in TOOLS:
            with self.subTest(tool=tool['id']):
                options={}
                ids=None
                if tool['id']=='encrypt': options={'password':'example-password'}
                elif tool['id']=='remove': options={'pages':'2'}
                elif tool['id']=='fill': options={'values':'{"Name":"Test user"}'};ids=[form]
                elif tool['id']=='field-info': options={'field_name':'Name'};ids=[form]
                elif tool['id'] in ('overlay','underlay','insert'): ids=[self.id,self.id]
                elif tool['id']=='add-attachment': ids=[self.id,self.id]
                elif tool['id']=='image-to-pdf': ids=[image]
                response=self.run_pypdf(tool['id'],options,ids)
                self.assertEqual(response.status_code,200,response.text)
                output=self.client.get(response.json()['downloadUrl'])
                self.assertGreater(len(output.content),0)
                if tool['id']=='fill': self.assertEqual(PdfReader(io.BytesIO(output.content)).get_form_text_fields()['Name'],'Test user')

    def test_reorder_range_and_split_content(self):
        result=self.run_pypdf('select',{'pages':'2,1-2'})
        reader=PdfReader(io.BytesIO(self.client.get(result.json()['downloadUrl']).content))
        self.assertEqual(len(reader.pages),3)
        self.assertIn('Second',reader.pages[0].extract_text())
        self.assertIn('First',reader.pages[1].extract_text())
        self.assertEqual(parse_pages('2-3,1',3),[1,2,0])
        for invalid in ['0','3-1','1-999999999','1,,2','NaN']:
            with self.assertRaises(ValueError): parse_pages(invalid,3)
        response=self.run_pypdf('render',{'pages':'2','format':'png'})
        self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(self.client.get(response.json()['downloadUrl']).content.startswith(b'\x89PNG'))

    def test_supported_annotation_types(self):
        supported = ['free_text','rectangle','ellipse','line','polygon','highlight','text','link','uri_link']
        for annotation_type in supported:
            with self.subTest(annotation_type=annotation_type):
                response = self.run_pypdf('add-annotation', {'annotation_type': annotation_type})
                self.assertEqual(response.status_code, 200, response.text)
                reader = PdfReader(io.BytesIO(self.client.get(response.json()['downloadUrl']).content))
                self.assertTrue(reader.pages[0].get('/Annots'))


if __name__=='__main__': unittest.main()
