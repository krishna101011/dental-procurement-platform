import { useEffect, useState } from 'react';
import type { ChangeEvent, DragEvent } from 'react';
import { ArrowRight, CalendarClock, ChevronRight, ImagePlus, Layers3, ListPlus, Repeat2, Sparkles, Trash2, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { money, Pill } from '../components/ui';

type ProcurementImage = { id:string; name:string; dataUrl:string; createdAt:string };
const IMAGE_KEY='dental_procurement_images_v1';

function readStoredImages(): ProcurementImage[]{try{return JSON.parse(localStorage.getItem(IMAGE_KEY)||'[]')}catch{return []}}

async function imageToDataUrl(file:File){
  return new Promise<string>((resolve,reject)=>{
    const reader=new FileReader();
    reader.onerror=()=>reject(new Error('Unable to read image'));
    reader.onload=()=>{
      const img=new Image();
      img.onload=()=>{
        const max=1600; const ratio=Math.min(1,max/Math.max(img.width,img.height));
        const canvas=document.createElement('canvas');
        canvas.width=Math.max(1,Math.round(img.width*ratio)); canvas.height=Math.max(1,Math.round(img.height*ratio));
        canvas.getContext('2d')?.drawImage(img,0,0,canvas.width,canvas.height);
        resolve(canvas.toDataURL('image/jpeg',.82));
      };
      img.onerror=()=>reject(new Error('Invalid image'));
      img.src=String(reader.result);
    };
    reader.readAsDataURL(file);
  });
}

export function ProcurementPage(){
 const [data,setData]=useState<any>({}); const [tab,setTab]=useState('due'); const [images,setImages]=useState<ProcurementImage[]>(readStoredImages); const [busy,setBusy]=useState(false); const [error,setError]=useState('');
 useEffect(()=>{api<any>('/procurement/summary').then(setData).catch(()=>setData({}))},[]);
 useEffect(()=>{localStorage.setItem(IMAGE_KEY,JSON.stringify(images))},[images]);
 const addImages=async(e:ChangeEvent<HTMLInputElement>)=>{const files=Array.from(e.target.files||[]);await addImageFiles(files);e.target.value=''};
 const removeImage=(id:string)=>setImages(prev=>prev.filter(x=>x.id!==id));
 const addImageFiles=async(files:File[])=>{if(!files.length)return;setBusy(true);setError('');try{const next=await Promise.all(files.filter(f=>f.type.startsWith('image/')).slice(0,8).map(async file=>({id:crypto.randomUUID(),name:file.name,dataUrl:await imageToDataUrl(file),createdAt:new Date().toISOString()})));setImages(prev=>[...next,...prev]);if(next.length===0)setError('Please choose an image file.');}catch{setError('One or more images could not be added. Please try JPG, PNG or WEBP files.')}finally{setBusy(false)}};
 const onDrop=(e:DragEvent<HTMLLabelElement>)=>{e.preventDefault();void addImageFiles(Array.from(e.dataTransfer.files||[]))};
 return <div className="page-stack">
  <section className="hero-row"><div><div className="eyebrow">MY PROCUREMENT / WORKSPACE</div><h1>Everything your clinic needs, clearly organised.</h1><p className="page-sub">Track reorder signals, repeat purchases and the images your team attaches to procurement decisions.</p></div><Link to="/catalogue" className="gradient-btn">Find a product <ArrowRight size={16}/></Link></section>
  <section className="proc-overview"><div className="proc-stat glass-card"><div className="stat-icon"><CalendarClock size={18}/></div><span>Due soon</span><strong>{data.due_count||0}</strong><small>Products nearing their expected interval</small></div><div className="proc-stat glass-card"><div className="stat-icon violet"><Repeat2 size={18}/></div><span>Repeat buyers</span><strong>{data.repeat_count||0}</strong><small>Products purchased more than once</small></div><div className="proc-stat glass-card"><div className="stat-icon green"><TrendingUp size={18}/></div><span>Cycle spend</span><strong>{money(Number(data.spend||0))}</strong><small>Tracked order value in your workspace</small></div></section>
  <section className="glass-card procurement-images"><div className="section-head"><div><div className="eyebrow">PROCUREMENT IMAGES</div><h2>Attach product or quotation images</h2><p>Keep visual references with your procurement workspace. Images are saved locally in this browser.</p></div><label className="gradient-btn upload-label"><ImagePlus size={16}/> {busy?'Adding…':'Add images'}<input type="file" accept="image/png,image/jpeg,image/webp" multiple hidden onChange={addImages}/></label></div>{error&&<div className="error-box">{error}</div>}{images.length?<div className="procurement-image-grid">{images.map(img=><div className="procurement-image-card" key={img.id}><img src={img.dataUrl} alt={img.name}/><div><span title={img.name}>{img.name}</span><button className="icon-danger" title="Remove image" onClick={()=>removeImage(img.id)}><Trash2 size={14}/></button></div></div>)}</div>:<label className="procurement-drop" onDragOver={e=>e.preventDefault()} onDrop={onDrop}><ImagePlus size={25}/><strong>Add procurement images</strong><span>Drop photos, quotes, packaging references or screenshots here — up to 8 at a time.</span><input type="file" accept="image/png,image/jpeg,image/webp" multiple hidden onChange={addImages}/></label>}</section>
  <section className="glass-card procurement-workspace"><div className="workspace-tabs"><button className={tab==='due'?'active':''} onClick={()=>setTab('due')}>Due for reorder</button><button className={tab==='frequent'?'active':''} onClick={()=>setTab('frequent')}>Frequently purchased</button><button className={tab==='lists'?'active':''} onClick={()=>setTab('lists')}>Saved lists</button></div>{tab==='lists'?<SavedLists/>:<ProcList items={(tab==='due'?data.due_items:data.frequent_items)||[]} due={tab==='due'}/>}</section>
  <section className="glass-card intelligence-banner"><div className="intel-orb"><Sparkles size={20}/></div><div><div className="eyebrow">RULE-BASED REORDER ENGINE</div><h2>Simple signals. Clear decisions.</h2><p>The MVP uses transparent purchase intervals so clinic teams can understand why a product appears as due.</p></div></section>
 </div>
}
function ProcList({items,due}:{items:any[];due:boolean}){if(!items.length)return <div className="empty-inline"><Layers3 size={20}/><div><strong>No signals yet.</strong><span>Complete a few orders and the procurement rhythm will appear here.</span></div></div>;return <div className="proc-list">{items.map((p:any)=><Link className="proc-row" to={`/product/${p.product_id}`} key={p.product_id}><img src={`/product-images/${p.product_id}.svg`} alt=""/><div><strong>{p.name}</strong><span>{p.brand_name} · {p.pack_size}</span></div><div className="proc-meta"><span>{due?`${p.days_overdue ?? p.days_since_last} days since last order`:`${p.order_count} orders`}</span><b>{money(Number(p.our_selling_price))}</b></div><Pill tone={due?'violet':'teal'}>{due?'DUE':'USUAL'}</Pill><ChevronRight size={16}/></Link>)}</div>}
function SavedLists(){return <div className="saved-list-grid"><Saved title="Monthly Clinic Supplies" count="18 products"/><Saved title="Emergency Supplies" count="9 products"/><Saved title="Endodontic Supplies" count="14 products"/><Saved title="Surgery Supplies" count="11 products"/></div>}
function Saved({title,count}:{title:string;count:string}){return <div className="saved-card"><div className="saved-icon"><ListPlus size={18}/></div><strong>{title}</strong><span>{count}</span><button>Open list <ChevronRight size={14}/></button></div>}
