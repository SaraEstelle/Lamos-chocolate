# Stage 3 — Task 0: User Stories & Mockups
## Lamos Chocolate — European Digital Platform

> **Project**: Lamos Chocolate — European Digital Platform
> **Team**: Sara Rebati · Valentin Planchon
> **Stack**: Django 5.x · PostgreSQL 16 · Docker · GitHub Actions

---

## 0.1 — Introduction & Prioritization Method

User Stories are written from the perspective of real system users. They define **what the system must do** before deciding **how it does it**. Each story is prioritized using the **MoSCoW** method:

| Priority | Meaning | Criteria |
|----------|---------|----------|
| **M — Must Have** | Essential for MVP | Without this, the product cannot be delivered |
| **S — Should Have** | Important but not blocking | High added value, deliverable in V1 if time allows |
| **C — Could Have** | Desirable | Nice to have, deferrable to V2 without critical impact |
| **W — Won't Have (this time)** | Out of V1 scope | Documented for the V2 roadmap, not developed now |

---

## 0.2 — User Types Identification

| Actor | Description | Primary Channel |
|-------|-------------|-----------------|
| **Anonymous Visitor** | Internet user discovering the brand, not logged in | Web (desktop + mobile) |
| **Registered B2C Customer** | Individual buyer with an account, can place orders online | Web (desktop + mobile) |
| **B2B Client** | Purchasing manager at a hotel, private bank, or law firm in Switzerland/EU | Web (dedicated form) |
| **Administrator** | Lamos team managing products, orders, and B2B requests from the back-office | Web (Django-powered secure admin panel) |
| **BI Analyst** | Valentin / Lamos team consulting KPI dashboards in Power BI / Looker | Power BI / Looker (external) |

---

## 0.3 — Complete User Stories by Module

### MODULE 1 — Navigation & Brand Discovery

---

**US-01** — Brand discovery (homepage)
**Priority: MUST HAVE**

> *As an anonymous visitor, I want to land on an immersive homepage presenting the Lamos brand, its story and value proposition, so I immediately understand who it is and why this chocolate is different.*

**Acceptance Criteria:**
- Homepage loads in under 3 seconds
- A full-screen hero section with premium visuals and brand tagline is visible without scrolling
- A call-to-action toward the shop and one toward B2B are present above the fold
- The page is responsive (mobile, tablet, desktop)
- Both languages (FR / EN) are accessible via a visible selector in the header

---

**US-02** — Reading the brand story
**Priority: MUST HAVE**

> *As an anonymous visitor, I want to read the story of Lamos Chocolate (origins in Dubai, European expansion, artisanal philosophy), so I can emotionally connect with the brand before purchasing.*

**Acceptance Criteria:**
- Dedicated `/about/` page accessible from the main menu
- Bilingual FR/EN content managed via Django i18n (`{% trans %}` tags)
- Visual / storytelling section present (photos of the manufacturing process, chefs, ingredients)
- No form or access barrier on this page

---

**US-03** — Language selection FR/EN
**Priority: MUST HAVE**

> *As a visitor, I want to switch between French and English at any time from any page, so I can browse in my native language.*

**Acceptance Criteria:**
- Language selector present in the header on all pages
- Selected language persists throughout the session (`django_language` cookie)
- URL reflects the active language (`/fr/shop/` vs `/en/shop/`)
- All labels, product texts, buttons, and emails are translated

---

### MODULE 2 — Product Catalog

---

**US-04** — Browsing the catalog
**Priority: MUST HAVE**

> *As an anonymous visitor or logged-in customer, I want to browse the complete list of Lamos products with their photos, names, formats, and prices, so I can identify what interests me before buying.*

**Acceptance Criteria:**
- Catalog page `/shop/` listing all active products (minimum 3 references at MVP)
- Each product card displays: photo, name, format/weight, price, "Available / Out of Stock" badge
- Dynamic page generated from PostgreSQL via Django ORM
- Bilingual FR/EN, responsive on mobile/desktop

---

**US-05** — Viewing a detailed product page
**Priority: MUST HAVE**

> *As a visitor, I want to click on a product and access a detailed page with full description, ingredients, allergens, available formats, price, and **estimated delivery time**, so I can make an informed purchasing decision.*

**Acceptance Criteria:**
- Clean URL: `/shop/<product-slug>/`
- Long description, ingredients, allergens displayed
- Quantity selector and "Add to Cart" button functional
- **Estimated delivery time displayed** based on current stock and shipping zone (forecasting model)
- Real-time availability indicator

---

**US-06** — Filtering / browsing by category
**Priority: SHOULD HAVE**

> *As a visitor, I want to filter products by type (gift boxes, bars, limited editions), so I can quickly find what matches my needs.*

**Acceptance Criteria:**
- Filters available on the catalog page
- Server-side filtering (Django views) with optional URL query param `?category=coffrets`
- Active filter visually highlighted

---

### MODULE 3 — Cart & Payment (B2C)

---

**US-07** — Adding to cart
**Priority: MUST HAVE**

> *As a visitor or logged-in customer, I want to add products to a persistent cart, so I can prepare my order before proceeding to payment.*

**Acceptance Criteria:**
- "Add to Cart" button on each product page
- Cart counter updated in the header without full page reload (AJAX via `JsonResponse`)
- Cart accessible from all pages via header icon
- Cart persists throughout the session (stored in Django session `request.session['cart']`)
- Cannot add more than available stock

---

**US-08** — Managing the cart
**Priority: MUST HAVE**

> *As a customer, I want to view my cart, modify quantities, and remove items, so I can control what I'm ordering before paying.*

**Acceptance Criteria:**
- Cart page `/cart/` with list of items, editable quantities, unit prices, and total
- Delete button per line item
- Total updated in real time when quantities are modified
- "Proceed to Checkout" button visible and functional

---

**US-09** — Online payment via Stripe
**Priority: MUST HAVE**

> *As a B2C customer, I want to pay for my order securely via credit card, so I can finalize my online purchase.*

**Acceptance Criteria:**
- Stripe Checkout integration (test mode validated with 3 test transactions)
- Redirect to confirmation page after successful payment
- Redirect to error page + cart maintained if payment fails
- **Order is only recorded in the database after Stripe webhook confirmation**
- Confirmation email sent automatically after payment (Django mail)

---

**US-10** — Receiving an order confirmation email
**Priority: MUST HAVE**

> *As a customer who has paid, I want to immediately receive a confirmation email with my order details, so I have a record of my purchase.*

**Acceptance Criteria:**
- Email triggered by the Stripe webhook (`payment_intent.succeeded` event)
- Content: order number, item list, total, shipping address, **estimated delivery time**
- Bilingual email according to the session language
- Professional HTML template consistent with brand identity

---

### MODULE 4 — Customer Accounts & History

---

**US-11** — Creating a customer account
**Priority: MUST HAVE**

> *As a visitor, I want to create an account with my email and a secure password, so I can find my orders and not re-enter my details at each purchase.*

**Acceptance Criteria:**
- `/accounts/register/` form: first name, last name, email, password, password confirmation
- Server-side validation via Django Forms (unique email, valid format, password min 8 chars)
- Password hashing via `django.contrib.auth.hashers.make_password` (PBKDF2 by default)
- Welcome email sent on registration
- Redirect to account page after successful creation

---

**US-12** — Login / Logout
**Priority: MUST HAVE**

> *As a registered customer, I want to log in with my credentials and log out when I wish, so I can secure access to my account.*

**Acceptance Criteria:**
- `/accounts/login/` page with email + password form
- Session managed via `django.contrib.auth` (`login()`, `logout()`)
- Clear error message if incorrect credentials (without revealing which field is wrong)
- Logout via dedicated button, session destroyed

---

**US-13** — Password reset
**Priority: MUST HAVE**

> *As a customer who has forgotten their password, I want to receive a reset link by email, so I can regain access to my account without contacting support.*

**Acceptance Criteria:**
- "Forgot your password?" link on the login page
- Email with a secure time-limited token (1-hour expiration)
- Password reset form accessible via the token link
- Token invalidated after use
- Generic response regardless of whether the email exists (anti-enumeration)

---

**US-14** — Viewing order history
**Priority: MUST HAVE**

> *As a logged-in customer, I want to see the list of my past orders with their status, so I can track my purchases.*

**Acceptance Criteria:**
- `/my-account/orders/` page accessible only if logged in (`@login_required`)
- Orders listed in descending date order
- Each line: order number, date, items, total, status (paid / shipped / delivered)
- Click on an order to see its details

---

### MODULE 5 — B2B Portal (Corporate Gifting)

---

**US-15** — Submitting a B2B request
**Priority: MUST HAVE**

> *As a purchasing manager at a Swiss hotel or private bank, I want to submit a quote request for premium gift boxes in bulk, so I can get a commercial proposal tailored to my needs.*

**Acceptance Criteria:**
- Dedicated `/b2b/` page with form: name, company, sector, professional email, phone, estimated quantity, occasion, free message
- Server-side validation via Django Forms (required fields)
- Automatic email triggered to the Lamos address
- Request stored in the `b2b_requests` PostgreSQL table (`status='new'`)
- Confirmation page displayed after submission

---

**US-16** — Viewing the B2B offer presentation
**Priority: SHOULD HAVE**

> *As a corporate visitor, I want to consult a presentation page of the B2B offer (range, personalization, served sectors), so I understand what Lamos offers to businesses before filling in the form.*

**Acceptance Criteria:**
- B2B section in the main navigation
- Presentation page: advantages, target sectors (hospitality, finance, luxury), gift formats
- Call-to-action toward the B2B form

---

### MODULE 6 — Administrator Panel

---

**US-17** — Administrator authentication
**Priority: MUST HAVE**

> *As a Lamos administrator, I want to log in to a protected administration area with separate credentials from customers, so I have secure and distinct back-office access.*

**Acceptance Criteria:**
- Django Admin (`/admin/`) available for superusers
- Custom back-office (`/backoffice/`) for business-specific functions
- `@admin_required` custom decorator verifying role at each request
- Admin session expires after 30 minutes of inactivity
- No access to the admin panel with a standard customer account

---

**US-18** — Managing the product catalog (CRUD)
**Priority: MUST HAVE**

> *As an administrator, I want to create, edit, and delete products from the admin panel, so I can keep the catalog up to date without technical intervention.*

**Acceptance Criteria:**
- CRUD interface: product list + creation/edit forms
- Editable fields: name (FR+EN), description (FR+EN), price, weight, category, photo, initial stock
- **Forecasting fields**: `production_delay_days`, `batch_size` editable per SKU
- Delete with confirmation (soft delete: `is_active=False`)
- Changes immediately visible on the storefront

---

**US-19** — Stock management
**Priority: MUST HAVE**

> *As an administrator, I want to see stock levels for each product and update them manually, so I avoid selling unavailable items.*

**Acceptance Criteria:**
- Stock level table in the admin panel
- Quick update field without going through the full product form
- Visual indicator (red if stock = 0 or below critical threshold)
- Stock changes logged (timestamp + admin user `updated_by`)

---

**US-20** — Viewing and managing B2B requests
**Priority: MUST HAVE**

> *As an administrator, I want to see all submitted B2B requests with each prospect's contact details and needs, so I can process them and follow up with the right contacts.*

**Acceptance Criteria:**
- `/backoffice/b2b/` page listing all requests
- Visible information: date, company, contact, quantity, status (new / in progress / converted / refused)
- Ability to change the status of a request
- Filtering by status

---

**US-21** — Viewing orders
**Priority: SHOULD HAVE**

> *As an administrator, I want to view all orders placed on the platform with their details (customer, items, amount, payment status), so I can manage shipments and customer service.*

**Acceptance Criteria:**
- `/backoffice/orders/` page listing all orders
- Detail accessible per order
- Ability to update status (paid / shipped / delivered / cancelled)

---

### MODULE 7 — Business Intelligence

---

**US-22** — Accessing the BI dashboard
**Priority: MUST HAVE**

> *As a Lamos manager, I want to access a Power BI / Looker dashboard showing real-time key activity KPIs (orders, revenue, top products, B2C/B2B ratio, stock forecasts), so I can steer the European launch with concrete data.*

**Acceptance Criteria:**
- Minimum 7 live KPIs:
  - Total orders (by period)
  - Revenue (total / by product)
  - Top 3 products (volume + revenue)
  - B2C vs B2B ratio
  - **Days until stockout per SKU** (forecasting model)
  - **Production relaunch alerts** (SKUs to restock)
  - **Monthly seasonality** (peak detection: Christmas, Valentine's Day, Mother's Day)
- Python connector (pandas + psycopg2) linked to PostgreSQL read-only user `lamos_bi_reader`
- Dashboard shareable as a report (link or PDF export)

---

## 0.4 — MoSCoW Summary

| ID | Short Title | Actor | Priority |
|----|-------------|-------|----------|
| US-01 | Immersive homepage | Visitor | **MUST** |
| US-02 | Brand story page | Visitor | **MUST** |
| US-03 | FR/EN language selection | Visitor | **MUST** |
| US-04 | Product catalog | Visitor / Customer | **MUST** |
| US-05 | Detailed product page + estimated delivery | Visitor / Customer | **MUST** |
| US-06 | Catalog filters | Visitor | **SHOULD** |
| US-07 | Add to cart | Visitor / Customer | **MUST** |
| US-08 | Cart management | Customer | **MUST** |
| US-09 | Stripe payment | B2C Customer | **MUST** |
| US-10 | Order confirmation email | B2C Customer | **MUST** |
| US-11 | Account creation | Visitor | **MUST** |
| US-12 | Login / Logout | Customer | **MUST** |
| US-13 | Password reset | Customer | **MUST** |
| US-14 | Order history | Logged-in Customer | **MUST** |
| US-15 | B2B form | B2B Prospect | **MUST** |
| US-16 | B2B offer page | Corporate Visitor | **SHOULD** |
| US-17 | Admin authentication | Admin | **MUST** |
| US-18 | Product CRUD admin | Admin | **MUST** |
| US-19 | Stock management admin | Admin | **MUST** |
| US-20 | B2B requests management | Admin | **MUST** |
| US-21 | Order consultation admin | Admin | **SHOULD** |
| US-22 | BI Dashboard + forecasting | Analyst / Lamos | **MUST** |

**Total Must Have: 18 stories | Should Have: 3 stories | Could Have: 0 | Won't Have: 0**

---

## 0.5 — Mockup Descriptions (V0 — Figma)

Wireframes V0 are produced in **Figma** and cover main screens in desktop (1440px) and mobile (375px).

### Screens to Mock Up

| # | Screen | Description |
|---|--------|-------------|
| M-01 | Homepage | Hero section, navigation, product highlights, B2C/B2B blocks |
| M-02 | Catalog page | Product grid, filters, stock badges |
| M-03 | Product page | Photos, description, quantity selector, cart CTA, **estimated delivery display** |
| M-04 | Cart page | Item list, editable quantities, total, checkout CTA |
| M-05 | Checkout | Shipping address form + Stripe Checkout redirect |
| M-06 | Order confirmation | Order number, summary, estimated delivery, back-to-shop CTA |
| M-07 | Login / Register | Side-by-side forms, password reset link |
| M-08 | Customer area — History | Order list, statuses, expandable detail |
| M-09 | B2B form | Professional contact fields, quantity, occasion, submit |
| M-10 | Backoffice — Dashboard | Quick stats, module links, **stock alerts, production alerts** |
| M-11 | Backoffice — Product CRUD | Product table, edit/delete buttons, creation form |

### Design Principles

- **Palette**: cream/ivory background (#FAF7F2), gold accents (#C8A96E), dark text (#1A1A1A)
- **Typography**: Elegant serif for headings (Playfair Display), sans-serif for body (Inter)
- **Tone**: Artisanal luxury, minimalist, premium — no generic visual elements
- **Mobile-first**: Breakpoints defined at 375px, 768px, 1280px, 1440px

---