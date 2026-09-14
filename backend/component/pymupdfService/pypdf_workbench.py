"""Explicit pypdf workbench adapters; rendering delegates to PyMuPDF."""
import io
import json
from contextlib import ExitStack
from pypdf import PdfReader, PdfWriter, Transformation
from .catalog import field, PAGES
from .operations import parse_pages, bundle, json_bytes, process as mupdf_process

TOOLS = []
def add(id, label, category, fields=(), multiple=False, engine='pypdf', input='pdf'):
    TOOLS.append(dict(id=id, label=label, category=category, fields=list(fields), multiple=multiple, engine=engine, input=input))

add('render', 'PDF to images · PyMuPDF renderer', 'Conversion', [PAGES, field('format','Output format','select','png',['png','jpg']), field('dpi','DPI (36–300)','number',96)], engine='PyMuPDF')
add('image-to-pdf','Images to PDF · PyMuPDF','Conversion', multiple=True, engine='PyMuPDF', input='image')
add('select','Reorder / select individual pages','Pages',[PAGES])
add('merge','Merge PDFs with per-file ranges','Pages',[field('ranges','Per-file page ranges, separated by semicolons (blank = all)')],multiple=True)
add('split','Split pages or range groups','Pages',[field('groups','Range groups separated by semicolons; blank = single pages')])
add('rotate','Rotate selected pages','Pages',[PAGES,field('angle','Degrees','select','90',['90','180','270'])])
add('remove','Remove selected pages','Pages',[PAGES])
add('scale','Scale selected pages','Pages',[PAGES,field('factor','Scale factor (0.1–4)','number',1)])
add('crop','Crop selected pages','Pages',[PAGES,field('rect','Crop box: x0,y0,x1,y1 (bottom-left PDF points)',default='0,0,300,400')])
add('transform','Transform page contents','Pages',[PAGES,field('rotate','Rotation','number',0),field('scale','Scale (0.1–4)','number',1),field('x','Horizontal translation','number',0),field('y','Vertical translation','number',0)])
add('text','Extract text','Text & images',[PAGES,field('mode','Mode','select','plain',['plain','layout','orientation']),field('orientation','Orientation','select','0',['0','90','180','270'])])
add('images','Extract embedded images','Text & images',[PAGES])
add('image-info','Inspect embedded images','Text & images',[PAGES])
add('metadata','Basic + XMP metadata','Metadata & navigation')
add('outlines','Bookmarks, destinations and page labels','Metadata & navigation')
add('fields','Inspect form fields','Forms & annotations')
add('fill','Fill form fields','Forms & annotations',[field('values','Field values as JSON object',default='{}')])
add('annotations','List annotations','Forms & annotations',[PAGES])
add('remove-annotations','Remove all annotations','Forms & annotations')
add('attachments','List embedded attachments','Attachments')
add('extract-attachments','Extract attachments','Attachments')
add('content','Inspect page content streams','Content streams',[PAGES,field('mode','View','select','operations',['raw','operations','drawing','rectangles','lines'])])
add('encrypt','Add PDF password','Security',[field('password','New password (8–40 characters)','password')])
add('decrypt','Save unlocked PDF','Security')
add('flatten','Flatten forms / annotations · PyMuPDF','Forms & annotations',engine='PyMuPDF')


def process(id, paths, options, passwords):
    tool = next((t for t in TOOLS if t['id'] == id), None)
    if not tool: raise ValueError('Unsupported pypdf workbench operation.')
    fields = {f['key']: f for f in tool['fields']}
    if set(options) - set(fields): raise ValueError('Unknown setting.')
    opts = {key: options.get(key,f['default']) for key,f in fields.items()}
    for key,f in fields.items():
        if f['choices'] and opts[key] not in f['choices']: raise ValueError(f'Invalid {key}.')
    if not paths or len(paths) > 10 or (not tool['multiple'] and len(paths) != 1): raise ValueError('Invalid input file count.')
    if tool['engine'] == 'PyMuPDF': return mupdf_process(id,paths,opts,passwords)
    with ExitStack() as stack:
        readers=[]
        for token,path in paths:
            reader=PdfReader(stack.enter_context(open(path,'rb')))
            if reader.is_encrypted and not reader.decrypt(passwords.get(token,'')): raise ValueError('Incorrect input password.')
            readers.append(reader)
        reader=readers[0]
        indices=parse_pages(opts.get('pages',''),len(reader.pages)) if 'pages' in opts else []
        data=None
        if id == 'text':
            data=[]
            for i in indices:
                p=reader.pages[i]
                text=p.extract_text(extraction_mode='layout') if opts['mode']=='layout' else p.extract_text(orientations=(int(opts['orientation']),)) if opts['mode']=='orientation' else p.extract_text()
                data.append(dict(page=i+1,text=text))
        elif id in ('images','image-info'):
            images=[(i,n,img) for i in indices for n,img in enumerate(reader.pages[i].images)]
            if id=='images': return bundle([(f'page-{i+1}-image-{n}.{img.name.rsplit(".",1)[-1]}',img.data,'application/octet-stream') for i,n,img in images])
            data=[dict(page=i+1,index=n,name=img.name,bytes=len(img.data)) for i,n,img in images]
        elif id=='metadata': data=dict(basic=dict(reader.metadata or {}),xmp=reader.xmp_metadata.stream.get_data().decode(errors='replace') if reader.xmp_metadata else None)
        elif id=='outlines': data=dict(outlines=reader.outline,destinations=reader.named_destinations,labels=reader.page_labels)
        elif id=='fields': data=reader.get_fields() or {}
        elif id=='annotations': data=[dict(page=i+1,annotations=[dict(a.get_object()) for a in reader.pages[i].get('/Annots',[])]) for i in indices]
        elif id=='attachments': data=[dict(name=name,count=len(reader.attachments[name])) for name in reader.attachments]
        elif id=='extract-attachments': return bundle([(f'attachment-{n}-{j}.bin',blob,'application/octet-stream') for n,name in enumerate(reader.attachments) for j,blob in enumerate(reader.attachments[name])])
        elif id=='content':
            data=[]
            for i in indices:
                stream=reader.pages[i].get_contents()
                operations=stream.operations if stream else []
                mode=opts['mode']
                if mode=='raw': value=stream.get_data().decode('latin1') if stream else ''
                else:
                    wanted={'drawing':{b're',b'm',b'l',b'c',b'v',b'y',b'h',b'f',b'F',b'B',b'S'},'rectangles':{b're'},'lines':{b'm',b'l'}}.get(mode)
                    value=[dict(operands=operands,operator=operator.decode('latin1')) for operands,operator in operations if wanted is None or operator in wanted]
                data.append(dict(page=i+1,result=value))
        if data is not None: return f'{id}.json',json_bytes(data),'application/json'
        writer=PdfWriter()
        if id=='split':
            groups=opts['groups'].split(';') if opts['groups'].strip() else [str(i+1) for i in range(len(reader.pages))]
            if len(groups)>30: raise ValueError('Maximum 30 split outputs.')
            items=[]
            for n,group in enumerate(groups):
                part=PdfWriter(); part.append(reader,pages=parse_pages(group,len(reader.pages)))
                stream=io.BytesIO();part.write(stream);items.append((f'part-{n+1}.pdf',stream.getvalue(),'application/pdf'))
            return bundle(items)
        if id=='merge':
            ranges=opts['ranges'].split(';') if opts['ranges'].strip() else ['']*len(readers)
            if len(ranges)!=len(readers): raise ValueError('Provide one range group per input file.')
            for source,group in zip(readers,ranges): writer.append(source,pages=parse_pages(group,len(source.pages)))
        elif id=='select': writer.append(reader,pages=indices)
        elif id=='remove':
            remaining=[i for i in range(len(reader.pages)) if i not in indices]
            if not remaining: raise ValueError('At least one page must remain.')
            writer.append(reader,pages=remaining)
        else:
            writer.clone_document_from_reader(reader)
            for i in indices:
                p=writer.pages[i]
                if id=='rotate': p.rotate(int(opts['angle']))
                elif id in ('scale','transform'):
                    factor=float(opts.get('factor',opts.get('scale',1)))
                    if not .1<=factor<=4: raise ValueError('Scale must be 0.1–4.')
                    if id=='scale': p.scale_by(factor)
                    else: p.add_transformation(Transformation().scale(factor).rotate(float(opts['rotate'])).translate(float(opts['x']),float(opts['y'])))
                elif id=='crop':
                    x0,y0,x1,y1=map(float,opts['rect'].split(','))
                    box=p.mediabox
                    if not float(box.left)<=x0<x1<=float(box.right) or not float(box.bottom)<=y0<y1<=float(box.top): raise ValueError('Crop must fit inside the media box.')
                    p.cropbox.lower_left=(x0,y0);p.cropbox.upper_right=(x1,y1)
            if id=='fill':
                values=json.loads(opts['values'])
                if not isinstance(values,dict): raise ValueError('Field values must be an object.')
                if not reader.get_fields(): raise ValueError('This PDF contains no form fields.')
                if set(values)-set(reader.get_fields()): raise ValueError('Unknown form field name.')
                for page in writer.pages:
                    if page.get('/Annots'):
                        writer.update_page_form_field_values(page,values,auto_regenerate=False)
            elif id=='remove-annotations': writer.remove_annotations(None)
            elif id=='encrypt':
                if not 8<=len(str(opts['password']))<=40: raise ValueError('Use 8–40 password characters.')
                writer.encrypt(str(opts['password']),algorithm='AES-256')
        stream=io.BytesIO();writer.write(stream)
        return f'{id}.pdf',stream.getvalue(),'application/pdf'
