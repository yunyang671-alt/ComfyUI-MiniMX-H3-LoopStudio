// Pure parsing: safe to validate before uploading images or submitting jobs.
const marker=/(?<![\w./\\\p{L}\p{N}-])([^\s<>:"|?*,，。；;：]+\.(?:png|jpe?g|webp|bmp))\s*[:：]/giu;
const key=name=>String(name).replace(/\\/g,'/').normalize('NFC').toLowerCase();
export function parsePrompts(text){
  if(new TextEncoder().encode(text).length>4*1024*1024)throw new Error('提示词TXT不能超过4MB');
  text=text.replace(/^\uFEFF/,'');
  const matches=[...text.matchAll(marker)], result=new Map();
  if(!matches.length)throw new Error('TXT没有找到“1.jpg:提示词”格式；文件名后请用英文或中文冒号');
  if(text.slice(0,matches[0].index).trim())throw new Error('TXT开头请直接写“文件名:提示词”，不要添加标题或说明');
  matches.forEach((m,i)=>{
    const name=key(m[1]), value=text.slice(m.index+m[0].length,matches[i+1]?.index??text.length).trim();
    if(result.has(name))throw new Error('TXT文件名重复：'+m[1]);
    if(!value)throw new Error('TXT提示词为空：'+m[1]);
    result.set(name,value);
  });
  return result;
}
export function matchPrompts(text,images){
  const prompts=parsePrompts(text),counts=new Map();
  for(const image of images){const name=key(image.name);counts.set(name,(counts.get(name)||0)+1);}
  return images.map(image=>{
    const relative=key(image.relative_path||image.name),name=key(image.name);
    if(prompts.has(relative)&&(relative.includes('/')||counts.get(name)===1))return prompts.get(relative);
    if(prompts.has(name)&&counts.get(name)===1)return prompts.get(name);
    if(prompts.has(name))throw new Error('多个子目录有同名图片，TXT请写相对路径区分：'+relative);
    throw new Error('TXT缺少图片的提示词：'+relative);
  });
}
export function decodePromptText(buffer){
  const bytes=new Uint8Array(buffer);
  if(bytes[0]===0xFF&&bytes[1]===0xFE)return new TextDecoder('utf-16le',{fatal:true}).decode(bytes);
  if(bytes[0]===0xFE&&bytes[1]===0xFF)return new TextDecoder('utf-16be',{fatal:true}).decode(bytes);
  try{return new TextDecoder('utf-8',{fatal:true}).decode(bytes);}
  catch{return new TextDecoder('gb18030',{fatal:true}).decode(bytes);}
}
