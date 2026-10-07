from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models import *
from app.schemas.schemas import *
from app.api.deps import get_current_user, require_roles
from app.core.security import create_token, hash_password, verify_password

router = APIRouter()
INTERNAL_ROLES = ("admin", "management", "finance", "operations", "procurement", "warehouse")


def product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id, name=p.name, sku=p.sku, description=p.description, pack_size=p.pack_size, unit=p.unit,
        category_id=p.category_id, brand_id=p.brand_id, supplier_id=p.supplier_id,
        market_benchmark_price=p.price.market_benchmark_price, mrp=p.price.mrp,
        our_selling_price=p.price.our_selling_price, discount=p.price.discount,
        available=p.inventory.available, category_name=p.category.name, brand_name=p.brand.name,
    )

@router.post("/auth/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == data.email)):
        raise HTTPException(409, "Email already registered")
    org = Organization(name=data.business_name, customer_type=data.customer_type, gstin=data.gstin)
    db.add(org); db.flush()
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password), role="owner", organization_id=org.id)
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_token(user.id, user.role)}

@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_token(user.id, user.role)}

@router.get("/auth/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user

@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).where(Category.is_active == True).order_by(Category.sort_order, Category.name)).all()

@router.get("/brands")
def brands(db: Session = Depends(get_db)):
    return db.scalars(select(Brand).where(Brand.is_active == True).order_by(Brand.name)).all()

@router.get("/suppliers")
def suppliers(db: Session = Depends(get_db), user=Depends(require_roles(*INTERNAL_ROLES, "supplier"))):
    return db.scalars(select(Supplier).where(Supplier.is_active == True).order_by(Supplier.name)).all()

@router.get("/products", response_model=list[ProductOut])
def products(
    q: str | None = None, category_id: int | None = None, brand_id: int | None = None,
    supplier_id: int | None = None, available: bool | None = None,
    min_price: Decimal | None = None, max_price: Decimal | None = None,
    limit: int = Query(60, le=250), offset: int = 0, db: Session = Depends(get_db)
):
    stmt = select(Product).options(joinedload(Product.category), joinedload(Product.brand), joinedload(Product.price), joinedload(Product.inventory)).where(Product.is_active == True)
    if q:
        search = f"%{q}%"
        stmt = stmt.where(or_(Product.name.ilike(search), Product.sku.ilike(search), Product.description.ilike(search)))
    if category_id: stmt = stmt.where(Product.category_id == category_id)
    if brand_id: stmt = stmt.where(Product.brand_id == brand_id)
    if supplier_id: stmt = stmt.where(Product.supplier_id == supplier_id)
    if min_price is not None: stmt = stmt.where(Product.price.has(Price.our_selling_price >= min_price))
    if max_price is not None: stmt = stmt.where(Product.price.has(Price.our_selling_price <= max_price))
    if available is True: stmt = stmt.where(Product.inventory.has(Inventory.on_hand - Inventory.reserved - Inventory.damaged - Inventory.quarantined > 0))
    if available is False: stmt = stmt.where(Product.inventory.has(Inventory.on_hand - Inventory.reserved - Inventory.damaged - Inventory.quarantined <= 0))
    rows = db.scalars(stmt.order_by(Product.name).offset(offset).limit(limit)).all()
    return [product_out(p) for p in rows]

@router.get("/products/{product_id}", response_model=ProductOut)
def product(product_id: int, db: Session = Depends(get_db)):
    p = db.scalar(select(Product).options(joinedload(Product.category), joinedload(Product.brand), joinedload(Product.price), joinedload(Product.inventory)).where(Product.id == product_id, Product.is_active == True))
    if not p: raise HTTPException(404, "Product not found")
    return product_out(p)

@router.post("/products", response_model=ProductOut)
def create_product(data: ProductCreate, db: Session = Depends(get_db), user=Depends(require_roles("admin", "procurement"))):
    if db.scalar(select(Product).where(Product.sku == data.sku)): raise HTTPException(409, "SKU exists")
    p = Product(name=data.name, sku=data.sku, description=data.description, pack_size=data.pack_size, unit=data.unit,
                category_id=data.category_id, brand_id=data.brand_id, supplier_id=data.supplier_id)
    db.add(p); db.flush()
    benchmark = data.market_benchmark_price; selling = data.our_selling_price or (benchmark * Decimal("0.92")); cost = data.supplier_cost or selling * Decimal("0.70")
    db.add(Price(product_id=p.id, market_benchmark_price=benchmark, mrp=data.mrp or benchmark, supplier_cost=cost,
                 landed_cost=data.landed_cost or cost * Decimal("1.05"), our_selling_price=selling, bulk_price=selling * Decimal("0.97"),
                 price_source="public Indian market benchmark", price_confidence="indicative"))
    db.add(Inventory(product_id=p.id, on_hand=data.stock))
    db.add(AuditLog(actor_user_id=user.id, action="product.created", entity_type="product", entity_id=str(p.id)))
    db.commit(); db.refresh(p)
    return product(p.id, db)

@router.patch("/products/{product_id}/price")
def update_price(product_id: int, data: PriceUpdate, db: Session = Depends(get_db), user=Depends(require_roles("admin", "procurement"))):
    p = db.scalar(select(Product).options(joinedload(Product.price)).where(Product.id == product_id))
    if not p or not p.price: raise HTTPException(404, "Product not found")
    old = p.price.our_selling_price; p.price.our_selling_price = data.our_selling_price; p.price.discount = data.discount
    db.add(PriceHistory(product_id=product_id, old_price=old, new_price=data.our_selling_price, changed_by=user.id))
    db.add(AuditLog(actor_user_id=user.id, action="price.changed", entity_type="product", entity_id=str(product_id)))
    db.commit(); return {"ok": True, "price": str(p.price.our_selling_price)}

@router.patch("/products/{product_id}", response_model=ProductOut)
def edit_product(product_id: int, data: ProductCreate, db: Session = Depends(get_db), user=Depends(require_roles("admin", "procurement"))):
    p = db.get(Product, product_id)
    if not p: raise HTTPException(404, "Product not found")
    for field in ("name","sku","description","pack_size","unit","category_id","brand_id","supplier_id"):
        setattr(p, field, getattr(data, field))
    if p.price:
        p.price.market_benchmark_price=data.market_benchmark_price; p.price.mrp=data.mrp or p.price.mrp
        p.price.supplier_cost=data.supplier_cost or p.price.supplier_cost; p.price.landed_cost=data.landed_cost or p.price.landed_cost
        if data.our_selling_price is not None: p.price.our_selling_price=data.our_selling_price
    if p.inventory: p.inventory.on_hand=data.stock
    db.add(AuditLog(actor_user_id=user.id, action="product.updated", entity_type="product", entity_id=str(product_id)))
    db.commit(); return product(product_id, db)

@router.get("/orders")
def orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    stmt = select(Order).order_by(Order.created_at.desc())
    if user.role not in INTERNAL_ROLES: stmt = stmt.where(Order.organization_id == user.organization_id)
    rows = db.scalars(stmt.limit(100)).all()
    return [{"id":o.id,"order_number":o.order_number,"status":o.status,"subtotal":str(o.subtotal),"tax":str(o.tax),"shipping":str(o.shipping),"total":str(o.total),"created_at":o.created_at.isoformat(),"item_count":len(o.items)} for o in rows]

@router.get("/orders/{order_id}")
def order_detail(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    o = db.scalar(select(Order).options(joinedload(Order.items)).where(Order.id == order_id))
    if not o: raise HTTPException(404, "Order not found")
    if user.role not in INTERNAL_ROLES and o.organization_id != user.organization_id: raise HTTPException(403, "Forbidden")
    ids=[i.product_id for i in o.items]
    prod_map={p.id:p for p in db.scalars(select(Product).where(Product.id.in_(ids))).all()} if ids else {}
    return {"id":o.id,"order_number":o.order_number,"status":o.status,"subtotal":str(o.subtotal),"tax":str(o.tax),"shipping":str(o.shipping),"total":str(o.total),"created_at":o.created_at.isoformat(),
            "items":[{"id":i.id,"product_id":i.product_id,"product_name":prod_map.get(i.product_id).name if i.product_id in prod_map else "Product","sku":prod_map.get(i.product_id).sku if i.product_id in prod_map else "","quantity":i.quantity,"unit_price":str(i.unit_price),"line_total":str(i.line_total)} for i in o.items]}

@router.post("/orders")
def create_order(data: OrderCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not user.organization_id: raise HTTPException(400, "Organization required")
    if not data.items: raise HTTPException(400, "Order requires at least one item")
    order = Order(order_number=f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}", organization_id=user.organization_id, status="confirmed")
    subtotal=Decimal(0); db.add(order); db.flush()
    try:
        for item in data.items:
            p=db.scalar(select(Product).options(joinedload(Product.price),joinedload(Product.inventory)).where(Product.id==item.product_id,Product.is_active==True))
            if not p: raise HTTPException(404, f"Product {item.product_id} not found")
            if p.inventory.available < item.quantity: raise HTTPException(409, f"Insufficient stock for {p.name}")
            line=p.price.our_selling_price*item.quantity; subtotal+=line; p.inventory.reserved+=item.quantity
            db.add(OrderItem(order_id=order.id, product_id=p.id, quantity=item.quantity, unit_price=p.price.our_selling_price, line_total=line))
        tax=(subtotal*Decimal("0.18")).quantize(Decimal("0.01")); order.subtotal=subtotal; order.tax=tax; order.shipping=Decimal(0); order.total=subtotal+tax
        db.add(AuditLog(actor_user_id=user.id, action="order.created", entity_type="order", entity_id=str(order.id))); db.commit()
    except Exception:
        db.rollback(); raise
    return {"id":order.id,"order_number":order.order_number,"status":order.status,"subtotal":str(subtotal),"tax":str(tax),"total":str(order.total)}

@router.get("/procurement/summary")
def procurement_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not user.organization_id:
        return {"due_count":0,"repeat_count":0,"spend":0,"due_items":[],"frequent_items":[]}
    orders = db.scalars(select(Order).options(joinedload(Order.items)).where(Order.organization_id==user.organization_id).order_by(Order.created_at)).all()
    now = datetime.now(timezone.utc)
    history: dict[int, dict] = {}
    for order in orders:
        for item in order.items:
            h=history.setdefault(item.product_id,{"count":0,"qty":0,"last":None,"first":None})
            h["count"] += 1; h["qty"] += item.quantity
            h["last"] = order.created_at; h["first"] = h["first"] or order.created_at
    pids=list(history)
    products = {p.id:p for p in db.scalars(select(Product).options(joinedload(Product.category),joinedload(Product.brand),joinedload(Product.price)).where(Product.id.in_(pids))).all()} if pids else {}
    due_items=[]; frequent=[]
    for pid,h in history.items():
        p=products.get(pid)
        if not p: continue
        interval=max(14,min(60,int(30 if h["count"]==1 else ((h["last"]-h["first"]).days/max(1,h["count"]-1)))))
        days_since=(now-h["last"].replace(tzinfo=timezone.utc) if h["last"].tzinfo is None else now-h["last"]).days
        if days_since>=interval-5:
            due_items.append({"product_id":p.id,"name":p.name,"brand_name":p.brand.name,"pack_size":p.pack_size,"our_selling_price":str(p.price.our_selling_price),"days_since_last":days_since,"days_overdue":max(0,days_since-interval)})
        if h["count"]>=2:
            frequent.append({"product_id":p.id,"name":p.name,"brand_name":p.brand.name,"pack_size":p.pack_size,"our_selling_price":str(p.price.our_selling_price),"order_count":h["count"],"quantity":h["qty"]})
    spend=sum((o.total for o in orders),Decimal(0))
    return {"due_count":len(due_items),"repeat_count":len(frequent),"spend":str(spend),"next_reorder_in_days":max(0,min([max(0,30-(datetime.now(timezone.utc)-(h["last"].replace(tzinfo=timezone.utc) if h["last"].tzinfo is None else h["last"])).days) for h in history.values()] or [7])),"due_items":sorted(due_items,key=lambda x:x["days_overdue"],reverse=True),"frequent_items":sorted(frequent,key=lambda x:x["order_count"],reverse=True)}


@router.get("/supplier/summary")
def supplier_summary(db: Session = Depends(get_db), user=Depends(require_roles("supplier"))):
    if not user.supplier_id: raise HTTPException(400, "Supplier is not linked to this user")
    supplier=db.get(Supplier,user.supplier_id)
    if not supplier: raise HTTPException(404,"Supplier not found")
    pos=db.scalars(select(PurchaseOrder).options(joinedload(PurchaseOrder.items)).where(PurchaseOrder.supplier_id==supplier.id).order_by(PurchaseOrder.expected_date.desc())).all()
    total=sum((po.total for po in pos),Decimal(0)); units=sum((it.received_quantity for po in pos for it in po.items),0)
    pending=sum((max(0,it.quantity-it.received_quantity) for po in pos for it in po.items),0)
    return {"supplier":{"id":supplier.id,"name":supplier.name,"lead_time_days":supplier.lead_time_days,"fill_rate":float(supplier.fill_rate)},"monthly_supply_value":float(total),"units_received":units,"pending_units":pending,"purchase_orders":[{"id":po.id,"po_number":po.po_number,"status":po.status,"total":str(po.total),"expected_date":po.expected_date.isoformat() if po.expected_date else None,"fill_rate":round((sum(i.received_quantity for i in po.items)/sum(i.quantity for i in po.items))*100,1) if po.items and sum(i.quantity for i in po.items) else 0} for po in pos]}

@router.get("/analytics/summary")
def analytics(db: Session = Depends(get_db), user=Depends(get_current_user)):
    base=select(func.count(Order.id),func.coalesce(func.sum(Order.total),0),func.coalesce(func.avg(Order.total),0))
    if user.role not in ("admin","management"): base=base.where(Order.organization_id==user.organization_id)
    count,total,avg=db.execute(base).one()
    product_count=db.scalar(select(func.count(Product.id)).where(Product.is_active==True)) or 0
    inventory_value=db.scalar(select(func.coalesce(func.sum(Inventory.on_hand*Price.our_selling_price),0)).join(Product,Inventory.product_id==Product.id).join(Price,Price.product_id==Product.id)) or 0
    return {"orders":count,"revenue":float(total or 0),"average_order_value":float(avg or 0),"active_products":product_count,"inventory_value":float(inventory_value)}

@router.get("/analytics/monthly")
def monthly(db: Session = Depends(get_db), user=Depends(get_current_user)):
    stmt=select(Order).order_by(Order.created_at)
    if user.role not in ("admin","management"): stmt=stmt.where(Order.organization_id==user.organization_id)
    buckets={}
    for o in db.scalars(stmt).all():
        key=o.created_at.strftime("%b")
        buckets.setdefault(key,{"month":key,"orders":0,"revenue":0}); buckets[key]["orders"]+=1; buckets[key]["revenue"]+=float(o.total)
    return list(buckets.values())[-12:]

@router.get("/inventory")
def inventory(db: Session = Depends(get_db), user=Depends(require_roles("admin","warehouse","procurement","management"))):
    rows=db.scalars(select(Inventory).options(joinedload(Inventory.product))).all()
    return [{"product_id":r.product_id,"product":r.product.name,"on_hand":r.on_hand,"reserved":r.reserved,"available":r.available,"incoming":r.incoming,"reorder_level":r.reorder_level,"low_stock":r.available<=r.reorder_level} for r in rows]

@router.post("/inventory/{product_id}/adjust")
def adjust_inventory(product_id:int,quantity:int,db:Session=Depends(get_db),user=Depends(require_roles("admin","warehouse"))):
    inv=db.scalar(select(Inventory).where(Inventory.product_id==product_id))
    if not inv: raise HTTPException(404,"Inventory not found")
    inv.on_hand+=quantity; db.add(InventoryTransaction(product_id=product_id,quantity=quantity,transaction_type="adjustment",reference="admin")); db.add(AuditLog(actor_user_id=user.id,action="inventory.adjusted",entity_type="product",entity_id=str(product_id),details=str(quantity))); db.commit(); return {"ok":True,"on_hand":inv.on_hand}
