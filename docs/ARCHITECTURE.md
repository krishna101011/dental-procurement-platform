# Architecture Decision Record — MVP

## Decision
Use a modular monolith.

## Why
The business has one core transactional domain with tight consistency requirements across catalogue, price, inventory, orders and procurement. Microservices at this stage would add deployment and data-consistency complexity without business benefit.

## Boundaries
- Identity / organization
- Catalogue
- Pricing
- Inventory
- Orders
- Procurement
- Analytics
- Audit

## Data principles
- PostgreSQL is the system of record.
- Money is represented with Decimal/Numeric, never floating point.
- Product and SKU are separate concepts in the domain model; this MVP represents the first sellable SKU as a Product record and leaves room for ProductVariant expansion.
- Historical order data is immutable in practice.
- Inventory changes are transaction-backed.
- Prices have source and confidence metadata.

## Tenant isolation
Every organization-owned query is scoped by authenticated organization ID unless the caller has an explicitly privileged internal role.
