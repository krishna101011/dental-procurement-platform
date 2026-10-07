import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart3, Bell, Box, Building2, ChevronRight, CircleUserRound, ClipboardList,
  Gauge, HeartPulse, LayoutDashboard, LogOut, Menu, Package, Plus, Search,
  Settings, ShoppingCart, Sparkles, Store, Truck, Users, X
} from 'lucide-react';
import { api } from './lib/api';
import { AuthPage } from './pages/Auth';
import { OverviewPage } from './pages/Overview';
import { CataloguePage } from './pages/Catalogue';
import { ProductPage } from './pages/Product';
import { CartPage } from './pages/Cart';
import { CheckoutPage } from './pages/Checkout';
import { OrdersPage, OrderDetailPage } from './pages/Orders';
import { ProcurementPage } from './pages/Procurement';
import { ClinicPage } from './pages/Clinic';
import { AdminPage } from './pages/Admin';
import { SupplierPage } from './pages/Supplier';

export type User = { id:number; name:string; email:string; role:string; organization_id:number|null };

const navItems = [
  { to:'/', label:'Dashboard', icon:LayoutDashboard },
  { to:'/catalogue', label:'Products', icon:Package },
  { to:'/procurement', label:'My Procurement', icon:ShoppingCart },
  { to:'/cart', label:'Cart', icon:ShoppingCart },
  { to:'/orders', label:'Orders', icon:ClipboardList },
  { to:'/clinic', label:'Vendors', icon:Truck },
  { to:'/admin', label:'Inventory', icon:Box },
  { to:'/', label:'Analytics', icon:BarChart3 },
  { to:'/orders', label:'Reports', icon:ClipboardList },
  { to:'/clinic', label:'Clinic Profile', icon:Building2 },
  { to:'/clinic', label:'Settings', icon:Settings },
];

function Protected({ user, children, roles }: { user:User|null; children:ReactNode; roles?:string[] }) {
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  const [user,setUser] = useState<User|null>(null);
  const [loading,setLoading] = useState(true);
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) { setLoading(false); return; }
    api<User>('/auth/me').then(setUser).catch(() => localStorage.removeItem('token')).finally(() => setLoading(false));
  }, []);

  const logout = () => { localStorage.removeItem('token'); setUser(null); };
  if (loading) return <div className="boot"><div className="logo-mark"><HeartPulse size={20}/></div><span>Loading procurement workspace…</span></div>;
  if (!user) return <Routes><Route path="/login" element={<AuthPage onLogin={setUser}/>} /><Route path="*" element={<Navigate to="/login" replace />} /></Routes>;

  return <AppShell user={user} onLogout={logout}>
    <Routes>
      <Route path="/" element={<OverviewPage user={user} />} />
      <Route path="/catalogue" element={<CataloguePage />} />
      <Route path="/product/:productId" element={<ProductPage />} />
      <Route path="/cart" element={<CartPage />} />
      <Route path="/checkout" element={<CheckoutPage />} />
      <Route path="/orders" element={<OrdersPage />} />
      <Route path="/orders/:orderId" element={<OrderDetailPage />} />
      <Route path="/procurement" element={<ProcurementPage />} />
      <Route path="/clinic" element={<ClinicPage user={user} />} />
      <Route path="/admin" element={<Protected user={user} roles={['admin','procurement','warehouse','finance','management']}><AdminPage user={user}/></Protected>} />
      <Route path="/supplier" element={<Protected user={user} roles={['supplier']}><SupplierPage /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </AppShell>;
}

function AppShell({ user,onLogout,children }:{user:User;onLogout:()=>void;children:ReactNode}) {
  const location = useLocation();
  const [mobileOpen,setMobileOpen] = useState(false);
  const [cartCount,setCartCount] = useState(Number(localStorage.getItem('cart_count') || 0));
  useEffect(()=>{const sync=()=>setCartCount(Number(localStorage.getItem('cart_count')||0)); window.addEventListener('cart-changed',sync); return()=>window.removeEventListener('cart-changed',sync)},[]);
  useEffect(()=>{ setMobileOpen(false); },[location.pathname]);

  const admin = ['admin','procurement','warehouse','finance','management'].includes(user.role);
  const supplier = user.role === 'supplier';
  const title = useMemo(() => {
    const match = [...navItems].find(n => n.to === location.pathname);
    if (match) return match.label;
    if (location.pathname.startsWith('/product/')) return 'Product';
    if (location.pathname.startsWith('/orders/')) return 'Order details';
    if (location.pathname === '/cart') return 'Cart';
    if (location.pathname === '/checkout') return 'Checkout';
    if (location.pathname === '/clinic') return 'My Clinic';
    if (location.pathname === '/admin') return 'Admin Console';
    if (location.pathname === '/supplier') return 'Supplier Portal';
    return 'Procurement workspace';
  },[location.pathname]);

  return <div className="app-shell">
    <aside className={mobileOpen ? 'sidebar open' : 'sidebar'}>
      <div className="brand-row">
        <div className="brand-mark"><HeartPulse size={19}/></div>
        <div><div className="brand-name">dentra</div><div className="brand-sub">procurement OS</div></div>
        <button className="mobile-close" onClick={()=>setMobileOpen(false)}><X size={18}/></button>
      </div>
      <div className="workspace-card">
        <div className="workspace-icon"><Building2 size={17}/></div>
        <div><strong>{user.organization_id ? 'Sunrise Dental Clinic' : 'Operations'}</strong><span>{supplier ? 'Supplier workspace' : admin ? 'Internal workspace' : 'Clinic workspace'}</span></div>
        <ChevronRight size={15}/>
      </div>
      <div className="nav-label">WORKSPACE</div>
      <nav className="main-nav">
        {navItems.map(({to,label,icon:Icon})=><Link key={to} className={location.pathname===to?'active':''} to={to}><Icon size={17}/><span>{label}</span></Link>)}
      </nav>
      <div className="nav-label nav-label-spaced">OPERATIONS</div>
      <nav className="main-nav">
        {admin && <Link className={location.pathname==='/admin'?'active':''} to="/admin"><Gauge size={17}/><span>Admin Console</span></Link>}
        {supplier && <Link className={location.pathname==='/supplier'?'active':''} to="/supplier"><Truck size={17}/><span>Supplier Portal</span></Link>}
        <Link className={location.pathname==='/clinic'?'active':''} to="/clinic"><Building2 size={17}/><span>My Clinic</span></Link>
      </nav>
      <div className="sidebar-bottom">
        <div className="mini-user"><div className="avatar">{user.name.slice(0,1).toUpperCase()}</div><div><strong>{user.name}</strong><span>{user.role}</span></div></div>
        <button className="signout" onClick={onLogout}><LogOut size={16}/> Sign out</button>
      </div>
    </aside>
    <div className="main-column">
      <header className="topbar">
        <div className="topbar-left"><button className="mobile-menu" onClick={()=>setMobileOpen(true)}><Menu size={20}/></button><div className="top-brand-mini"><div className="brand-mark"><HeartPulse size={18}/></div><div><div className="brand-name">DentalProcure</div><div className="brand-sub">Smarter sourcing. Healthier smiles.</div></div></div></div>
        <div className="top-search"><Search size={17}/><input placeholder="Search for products, brands, categories..."/><kbd>Ctrl + K</kbd></div>
        <div className="top-actions">
          <button className="top-icon" title="Notifications"><Bell size={18}/><i></i></button>
          <button className="top-icon" title="Appearance">☼</button>
          <Link to="/clinic" className="profile-chip"><div className="avatar tiny">{user.name.slice(0,1).toUpperCase()}</div><span>{user.name}</span><ChevronRight size={13}/></Link>
        </div>
      </header>
      <main className="page-container">{children}</main>
    </div>
  </div>;
}
