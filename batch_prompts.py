"""Parse filename:prompt blocks without interpreting punctuation in the prompt."""
import re
import unicodedata

MARKER = re.compile(r'(?<![\w./\\-])([^\s<>:"|?*,，。；;：]+\.(?:png|jpe?g|webp|bmp))\s*[:：]', re.I)
MAX_TEXT = 4 * 1024 * 1024

def key(name):
    return unicodedata.normalize('NFC', str(name).replace('\\', '/')).lower()

def parse_prompts(text):
    if not isinstance(text, str) or len(text.encode('utf-8')) > MAX_TEXT:
        raise ValueError('提示词TXT必须是文本，且不能超过4MB')
    text = text.lstrip('\ufeff')
    marks = list(MARKER.finditer(text))
    if not marks:
        raise ValueError('TXT没有找到“1.jpg:提示词”格式；文件名后请用英文或中文冒号')
    if text[:marks[0].start()].strip():
        raise ValueError('TXT开头请直接写“文件名:提示词”，不要添加标题或说明')
    result = {}
    for i, mark in enumerate(marks):
        name = key(mark.group(1))
        value = text[mark.end():marks[i+1].start() if i+1 < len(marks) else len(text)].strip()
        if name in result:
            raise ValueError('TXT文件名重复：' + mark.group(1))
        if not value:
            raise ValueError('TXT提示词为空：' + mark.group(1))
        result[name] = value
    return result

def match_prompts(text, images):
    prompts = parse_prompts(text)
    basenames = {}
    for image in images:
        name = key(image.get('name', ''))
        basenames[name] = basenames.get(name, 0) + 1
    result = []
    for image in images:
        relative = key(image.get('relative_path') or image.get('name', ''))
        name = key(image.get('name', ''))
        if relative in prompts and ('/' in relative or basenames[name] == 1):
            result.append(prompts[relative])
        elif name in prompts and basenames[name] == 1:
            result.append(prompts[name])
        elif name in prompts:
            raise ValueError('多个子目录有同名图片，TXT请写相对路径区分：' + relative)
        else:
            raise ValueError('TXT缺少图片的提示词：' + relative)
    return result
