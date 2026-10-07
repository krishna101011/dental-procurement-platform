# dentra — Dental Procurement Platform

A modular-monolith B2B dental + healthcare procurement platform built around the long-term flywheel: supplier procurement → owned inventory → clinic purchasing → recurring orders → procurement intelligence → better supplier terms → private label.

## What this version is

This repository is an interactive MVP foundation, not a collection of static mockups. The frontend is routed, product cards are clickable, product detail pages exist, the cart is functional, checkout creates a real backend order, orders have detail views, and the procurement page calculates purchasing signals from order history.

The visual system is intentionally **dark + soft glass**: premium healthcare SaaS, dense enough for operations, calm enough for clinic users.

## Stack

- Backend: Python 3.11+, FastAPI, Pydantic, SQLAlchemy, Alembic-ready, PostgreSQL, Redis-ready, Pytest
- Frontend: React + TypeScript + Vite + React Router + Recharts + Lucide
- Local database: SQLite fallback for frictionless localhost testing; PostgreSQL is the target production database
- Local product imagery: 232 SVG packshot-style assets under `frontend/public/product-images/`

## Included

- JWT login with Argon2 password hashing
- Multi-tenant organization context
- Customer, admin, procurement, warehouse, management and supplier role foundations
- 232 database-seeded dental/healthcare products
- Category, brand, manufacturer and supplier master data
- Benchmark / MRP / cost / landed cost / selling price / bulk price / discount model
- Inventory with available, reserved, incoming, damaged, returned and quarantined quantities
- Inventory transaction history
- Customer order creation with server-side price + stock validation
- Order history and order detail
- Buyer overview analytics from database order data
- Procurement dashboard with repeat-purchase and reorder signals
- Search + category + brand filtering
- Product detail / add-to-cart / checkout workflow
- Admin pricing console with server-side price change audit trail
- Controlled supplier dashboard
- Clinic organization page
- Responsive desktop / tablet / mobile UI

## Local setup — Windows PowerShell

### 1. From the repository root

```powershell
Copy-Item .env.example backend\.env
py -3.14 -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

### 2. Use SQLite for first local run

```powershell
(Get-Content backend\.env) -replace '^DATABASE_URL=.*','DATABASE_URL=sqlite:///./dental.db' | Set-Content backend\.env
```

### 3. Seed

```powershell
cd backend
python -m app.db.seed
```

### 4. Start the whole stack with one command

Open a fresh PowerShell in the repository root:

```powershell
.\scripts\run-local.ps1
```

This starts:

- FastAPI → http://localhost:8000
- React/Vite → http://localhost:5174
- Swagger → http://localhost:8000/docs

If ports are occupied by another project, the script deliberately uses 5174 for the frontend and stops only listeners on ports 8000 and 5174 before starting this project.

## Manual start

Backend terminal:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

Frontend terminal:

```powershell
cd frontend
npm install
npm run dev
```

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Customer / Owner | doctor@example.com | Demo@12345 |
| Admin | admin@example.com | Admin@12345 |
| Supplier | supplier@example.com | Supplier@12345 |

These are demo credentials only.

## Main user flows

```text
Login
  ↓
Overview
  ├── live order analytics
  ├── reorder signal
  └── quick procurement

Catalogue
  ↓
Product detail
  ↓
Add to cart
  ↓
Checkout
  ↓
Backend validates price + stock
  ↓
Order created
  ↓
Order detail

My Procurement
  ├── Due for reorder
  ├── Frequently purchased
  └── Saved procurement lists

Admin
  ├── Revenue / order analytics
  ├── Inventory readiness
  └── Server-side price editing + audit log
```

## Pricing policy

Seed market values are clearly marked as public Indian market benchmarks with `indicative` confidence. They are not supplier quotations. Generic seed selling prices use the requested approximate discount logic; actual admin pricing is editable without code changes.

## Images

The initial catalogue has one local image asset per seeded SKU. The assets are intentionally **illustrative procurement packshots**, not claimed manufacturer photography. Replace them with licensed supplier/manufacturer images later without changing the product routing or catalogue structure.

## Production hardening still required

- PostgreSQL as the required deployment database
- Full Alembic migration history
- Refresh-token rotation and session revocation
- Full CRUD for organizations, suppliers, brands, categories and warehouses
- Secure product image upload/object storage
- CSV/XLSX validation/import
- GST invoice, payment gateway and shipping integrations
- Receiving workflow for purchase orders
- Batch/lot/expiry inventory
- Explicit recurring-order authorization workflow
- Background workers for notifications and scheduled jobs
- Rate limiting, advanced tenant-isolation tests, Playwright E2E and observability

## Latest frontend refinement

- Refined navy-blue / light-blue / white theme throughout the web workspace.
- Added Procurement Images to **My Procurement**. Users can add multiple JPG/PNG/WEBP images, drag-and-drop images, preview them, and remove them. Images are compressed in-browser and persisted in localStorage for the local demo.
- Preserved the product catalogue, product detail, cart, checkout, orders, admin, supplier, clinic and procurement flows.

## Reference UI build
The frontend now uses a clean white + navy + light-blue DentalProcure workspace inspired by the latest dashboard reference. The dashboard includes KPI cards, a premium dental-supply hero, featured products, quick filters, quick actions, recent orders, spending overview, top categories, and the existing catalogue/procurement/cart/order flows.

### Procurement images
Open **My Procurement** and use **Add images** or drag and drop files into the procurement image panel. Images are compressed and kept in browser local storage for the local demo.
