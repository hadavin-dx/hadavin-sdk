-- "Lumen Goods": base tables of the full synthetic dataset (db/lumen.py). Applied by an admin role; the app never
-- reads these. All timestamps are UTC. The restricted column is customers.email (absent from every view).
CREATE SCHEMA shop;

CREATE TABLE shop.customers (
    customer_id      integer PRIMARY KEY,
    full_name        text NOT NULL,
    email            text NOT NULL,
    country          text NOT NULL,
    signup_date      date NOT NULL,
    segment          text NOT NULL,
    marketing_opt_in boolean NOT NULL
);
COMMENT ON COLUMN shop.customers.email IS 'Restricted: never exposed to the tool';

CREATE TABLE shop.products (
    product_id integer PRIMARY KEY,
    sku        text NOT NULL,
    name       text NOT NULL,
    category   text NOT NULL,
    unit_cost  numeric(10, 2) NOT NULL,
    list_price numeric(10, 2) NOT NULL,
    is_active  boolean NOT NULL,
    created_at date NOT NULL
);

CREATE TABLE shop.orders (
    order_id         integer PRIMARY KEY,
    customer_id      integer NOT NULL REFERENCES shop.customers,
    order_ts         timestamptz NOT NULL,
    status           text NOT NULL,
    channel          text NOT NULL,
    shipping_country text NOT NULL,
    discount_pct     integer NOT NULL,
    notes            text,
    fl_cd            varchar(1) NOT NULL
);
COMMENT ON COLUMN shop.orders.fl_cd IS 'Fulfilment flag: N normal, R rush, F fraud-review hold';

CREATE TABLE shop.order_items (
    order_item_id integer PRIMARY KEY,
    order_id      integer NOT NULL REFERENCES shop.orders,
    product_id    integer NOT NULL REFERENCES shop.products,
    quantity      integer NOT NULL,
    unit_price    numeric(10, 2) NOT NULL
);

CREATE TABLE shop.payments (
    payment_id integer PRIMARY KEY,
    order_id   integer NOT NULL REFERENCES shop.orders,
    method     text NOT NULL,
    amount     numeric(12, 2) NOT NULL,
    paid_at    timestamptz NOT NULL,
    status     text NOT NULL
);

CREATE TABLE shop.refunds (
    refund_id   integer PRIMARY KEY,
    order_id    integer NOT NULL REFERENCES shop.orders,
    refunded_at timestamptz NOT NULL,
    amount      numeric(12, 2) NOT NULL,
    reason      text NOT NULL
);

CREATE TABLE shop.support_tickets (
    ticket_id   integer PRIMARY KEY,
    customer_id integer NOT NULL REFERENCES shop.customers,
    opened_at   timestamptz NOT NULL,
    closed_at   timestamptz,
    category    text NOT NULL,
    priority    text NOT NULL,
    subject     text NOT NULL,
    csat_score  integer
);
