from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

def now(): return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True)
    customer_type: Mapped[str] = mapped_column(String(60), default="dental_clinic")
    gstin: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    users = relationship("User", back_populates="organization")
    orders = relationship("Order", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(40), default="purchaser")
    organization_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    organization = relationship("Organization", back_populates="users")
    supplier = relationship("Supplier")

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    products = relationship("Product", back_populates="category")

class Brand(Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    products = relationship("Product", back_populates="brand")

class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True)
    email: Mapped[str | None] = mapped_column(String(255))
    lead_time_days: Mapped[int] = mapped_column(Integer, default=5)
    fill_rate: Mapped[Decimal] = mapped_column(Numeric(5,2), default=95)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

class Manufacturer(Base):
    __tablename__ = "manufacturers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(220), index=True)
    sku: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="Professional healthcare procurement item.")
    pack_size: Mapped[str] = mapped_column(String(80), default="1 unit")
    unit: Mapped[str] = mapped_column(String(40), default="unit")
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    manufacturer_id: Mapped[int | None] = mapped_column(ForeignKey("manufacturers.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    price = relationship("Price", back_populates="product", uselist=False, cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")

class Price(Base):
    __tablename__ = "prices"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)
    market_benchmark_price: Mapped[Decimal] = mapped_column(Numeric(12,2))
    mrp: Mapped[Decimal] = mapped_column(Numeric(12,2))
    supplier_cost: Mapped[Decimal] = mapped_column(Numeric(12,2))
    landed_cost: Mapped[Decimal] = mapped_column(Numeric(12,2))
    our_selling_price: Mapped[Decimal] = mapped_column(Numeric(12,2))
    bulk_price: Mapped[Decimal | None] = mapped_column(Numeric(12,2))
    discount: Mapped[Decimal] = mapped_column(Numeric(8,2), default=0)
    price_source: Mapped[str] = mapped_column(String(120), default="public Indian market benchmark")
    price_confidence: Mapped[str] = mapped_column(String(40), default="indicative")
    product = relationship("Product", back_populates="price")

class Inventory(Base):
    __tablename__ = "inventory"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)
    on_hand: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)
    incoming: Mapped[int] = mapped_column(Integer, default=0)
    damaged: Mapped[int] = mapped_column(Integer, default=0)
    returned: Mapped[int] = mapped_column(Integer, default=0)
    quarantined: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=10)
    product = relationship("Product", back_populates="inventory")
    @property
    def available(self): return max(0, self.on_hand - self.reserved - self.damaged - self.quarantined)

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]
    transaction_type: Mapped[str] = mapped_column(String(40))
    reference: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_number: Mapped[str] = mapped_column(String(40), unique=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    status: Mapped[str] = mapped_column(String(40), default="confirmed")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0)
    shipping: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    organization = relationship("Organization", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12,2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12,2))
    order = relationship("Order", back_populates="items")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    po_number: Mapped[str] = mapped_column(String(40), unique=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    status: Mapped[str] = mapped_column(String(40), default="pending")
    total: Mapped[Decimal] = mapped_column(Numeric(12,2), default=0)
    expected_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]
    received_quantity: Mapped[int] = mapped_column(Integer, default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12,2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(12,2))
    purchase_order = relationship("PurchaseOrder", back_populates="items")

class ReorderRule(Base):
    __tablename__ = "reorder_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    interval_days: Mapped[int] = mapped_column(Integer, default=30)
    last_order_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class PriceHistory(Base):
    __tablename__ = "price_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    old_price: Mapped[Decimal]
    new_price: Mapped[Decimal]
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
