import { useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, BellRing, Box, CalendarDays, ChevronDown, ChevronRight, CircleDollarSign, Filter, ImagePlus, PackageCheck, Plus, Search, ShoppingCart, Truck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { money, ProductCard, Pill } from '../components/ui';
import { SpendChart } from '../components/Charts';
import { User } from '../App';

type Category = {name:string;count:number;share:number};

export function OverviewPage({user}:{user:User}){
 const [summary,setSummary]=useState<any>({orders:24,revenue:148750,active_products:312,inventory_value:845230});
 const [monthly,setMonthly]=useState<any[]>([]); const [products,setProducts]=useState<any[]>([]); const [orders,setOrders]=useState<any[]>([]); const [proc,setProc]=useState<any>({due_count:5});
 const [activeCategory,setActiveCategory]=useState('All Products'); const [query,setQuery]=useState('');
 useEffect(()=>{
   Promise.allSettled([api('/analytics/summary'),api('/analytics/monthly'),api('/products?limit=20'),api('/orders'),api('/procurement/summary')]).then(([a,b,c,d,e])=>{
     if(a.status==='fulfilled')setSummary((x:any)=>({...x,...(a.value as any)}));
     if(b.status==='fulfilled')setMonthly(b.value as any[]);
     if(c.status==='fulfilled')setProducts(c.value as any[]);
     if(d.status==='fulfilled')setOrders(d.value as any[]);
     if(e.status==='fulfilled')setProc(e.value as any);
   });
 },[]);
 const categories=useMemo<Category[]>(()=>{
   const map=new Map<string,number>(); products.forEach(p=>map.set(p.category_name,(map.get(p.category_name)||0)+1));
   const total=products.length||1; return Array.from(map.entries()).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([name,count])=>({name,count,share:Math.round(count/total*100)}));
 },[products]);
 const filtered=products.filter(p=>`${p.name} ${p.brand_name} ${p.category_name}`.toLowerCase().includes(query.toLowerCase()) && (activeCategory==='All Products'||p.category_name===activeCategory)).slice(0,5);
 const recent=orders.length?orders.slice(0,4):[
   {id:1,order_number:'#DP-2025-0412',created_at:'2025-09-12',status:'delivered',item_count:12,total:18750},
   {id:2,order_number:'#DP-2025-0408',created_at:'2025-09-08',status:'processing',item_count:8,total:12430},
   {id:3,order_number:'#DP-2025-0397',created_at:'2025-09-05',status:'shipped',item_count:6,total:9860},
   {id:4,order_number:'#DP-2025-0389',created_at:'2025-09-02',status:'delivered',item_count:15,total:22300},
 ];
 return <div className="dashboard-page">
   <div className="dashboard-main">
     <section className="welcome-row">
       <div><span className="dash-kicker">DASHBOARD</span><h1>Good Morning,<br/><span>{user.name}</span></h1><p>Here's what's happening with your procurement today.</p></div>
       <div className="dash-date"><CalendarDays size={16}/><span>Mon, 15 Sep 2025</span><ChevronDown size={15}/></div>
     </section>
     <section className="metric-strip">
       <Metric icon={<Box size={19}/>} label="Total Orders" value={summary.orders||24} trend="12%" note="vs last month"/>
       <Metric icon={<ShoppingCart size={19}/>} label="Total Spend" value={money(Number(summary.revenue||148750))} trend="8%" note="vs last month"/>
       <Metric icon={<Truck size={19}/>} label="Pending Deliveries" value={proc.pending_count??5} trend="2" note="need attention" alert/>
       <Metric icon={<PackageCheck size={19}/>} label="In Stock Items" value={summary.active_products||312} trend="15%" note="vs last month"/>
     </section>
     <section className="feature-banner">
       <div className="feature-copy"><span>Trusted brands • Genuine products • Best prices</span><h2>Premium Dental Supplies<br/>for Your Practice</h2><Link to="/catalogue" className="primary-btn">Explore Products <ArrowUpRight size={16}/></Link></div>
       <div className="feature-art"><img src="/product-images/52.svg"/><img src="/product-images/134.svg"/><img src="/product-images/20.svg"/></div>
       <div className="banner-dots"><i className="active"></i><i></i><i></i></div>
     </section>
     <section className="featured-section">
       <div className="section-line"><div><h2>Featured Products</h2></div><Link to="/catalogue" className="text-link">View All <ArrowUpRight size={14}/></Link></div>
       <div className="featured-products">{(filtered.length?filtered:products.slice(0,5)).map(p=><ProductCard key={p.id} product={p}/>)}</div>
     </section>
     <section className="dashboard-bottom">
       <div className="dash-card orders-card"><div className="section-line"><div><h2>Recent Orders</h2></div><Link to="/orders" className="text-link">View All <ArrowUpRight size={13}/></Link></div><div className="order-table"><div className="order-head"><span>Order ID</span><span>Date</span><span>Status</span><span>Amount</span></div>{recent.map((o:any)=><Link key={o.id} className="order-row" to={`/orders/${o.id}`}><span>{o.order_number}</span><span>{new Date(o.created_at).toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'})}</span><span><i className={`status-dot ${o.status}`}></i>{o.status[0].toUpperCase()+o.status.slice(1)}</span><strong>{money(Number(o.total))}</strong></Link>)}</div></div>
       <div className="dash-card spending-card"><div className="section-line"><div><h2>Spending Overview</h2></div><button className="select-btn">This Month <ChevronDown size={13}/></button></div><SpendChart data={monthly}/><div className="spend-summary"><div><strong>{money(Number(summary.revenue||148750))}</strong><span>Total Spend</span></div><div><strong className="positive">↗ 8%</strong><span>vs last month</span></div><div><strong>{summary.orders||24}</strong><span>Total Orders</span></div></div></div>
       <div className="dash-card categories-card"><div className="section-line"><div><h2>Top Categories</h2></div></div><div className="donut" style={{background:`conic-gradient(#1167c7 0 32%, #5ba7ea 32% 56%, #87b9ef 56% 74%, #a9cdf3 74% 88%, #cbdff6 88% 96%, #e8f1fb 96% 100%)`}}><div><strong>{categories[0]?.share||32}%</strong><span>{categories[0]?.name?.split(' ')[0]||'Instruments'}</span></div></div><div className="legend">{(categories.length?categories:[{name:'Instruments',share:32,count:0},{name:'Materials & Consumables',share:24,count:0},{name:'Equipment',share:18,count:0},{name:'Orthodontics',share:14,count:0},{name:'Implants',share:8,count:0}]).map((c:any,i:number)=><div key={c.name}><i className={`legend-dot d${i}`}></i><span>{c.name}</span><b>{c.share}%</b></div>)}</div></div>
     </section>
   </div>
   <aside className="dashboard-aside">
     <div className="aside-card filter-card"><div className="aside-title"><span>Quick Filters</span><button onClick={()=>{setQuery('');setActiveCategory('All Products')}}>Clear All</button></div><label className="aside-search"><Search size={15}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search products..."/></label><div className="filter-group"><div className="filter-head">Category <ChevronDown size={14}/></div>{['Dental Instruments','Materials & Consumables','Equipment','Orthodontics','Implants','Preventive Care'].map((x,i)=><button key={x} className={`check-filter ${activeCategory===x?'selected':''}`} onClick={()=>setActiveCategory(activeCategory===x?'All Products':x)}><span className={`check-box ${activeCategory===x?'checked':''}`}>{activeCategory===x?'✓':''}</span>{x}<small>{[68,124,24,18,12,16][i]}</small></button>)}</div><div className="filter-group"><div className="filter-head">Brand <ChevronDown size={14}/></div><select className="aside-select"><option>All Brands</option><option>3M</option><option>Dentsply Sirona</option><option>Komet</option><option>Medicom</option></select></div><div className="filter-group"><div className="filter-head">Price Range <ChevronDown size={14}/></div><div className="price-inputs"><input placeholder="Min ₹"/><input placeholder="Max ₹"/></div><div className="fake-slider"><i></i><i></i></div><div className="price-labels"><span>₹0</span><span>₹50,000+</span></div></div><div className="filter-group"><div className="filter-head">Availability <ChevronDown size={14}/></div><button className="check-filter selected"><span className="check-box checked">✓</span>In Stock</button><button className="check-filter"><span className="check-box"></span>Out of Stock</button></div><button className="apply-btn"><Filter size={15}/> Apply Filters</button></div>
     <div className="aside-card quick-card"><div className="aside-title"><span>Quick Actions</span></div><Link to="/procurement"><Plus size={17}/> Create New Procurement</Link><Link to="/procurement"><ImagePlus size={17}/> Upload Product Images</Link><Link to="/orders"><ShoppingCart size={17}/> View My Orders</Link><Link to="/clinic"><BellRing size={17}/> Contact Supplier</Link></div>
   </aside>
 </div>
}
function Metric({icon,label,value,trend,note,alert}:{icon:any;label:string;value:any;trend:string;note:string;alert?:boolean}){return <div className="dash-metric"><div className="metric-icon-box">{icon}</div><div className="metric-copy"><span>{label}</span><strong>{value}</strong><small className={alert?'alert-text':'positive'}>↗ {trend} <em>{note}</em></small></div></div>}
