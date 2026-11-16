-- Ask-your-data demo: base tables (synthetic data only). Applied by an admin role; the app never reads these.
CREATE SCHEMA shop;

CREATE TABLE shop.customers (
    customer_id integer PRIMARY KEY,
    full_name   text NOT NULL,
    email       text NOT NULL,           -- the restricted column: absent from every analytics view
    country     text NOT NULL,
    signup_date date NOT NULL
);

CREATE TABLE shop.products (
    product_id   integer PRIMARY KEY,
    product_name text NOT NULL,
    category     text NOT NULL,
    unit_price   numeric(10, 2) NOT NULL
);

CREATE TABLE shop.orders (
    order_id     integer PRIMARY KEY,
    customer_id  integer NOT NULL REFERENCES shop.customers,
    order_date   date NOT NULL,
    status       text NOT NULL,
    total_amount numeric(12, 2) NOT NULL
);

CREATE TABLE shop.order_items (
    order_item_id integer PRIMARY KEY,
    order_id      integer NOT NULL REFERENCES shop.orders,
    product_id    integer NOT NULL REFERENCES shop.products,
    quantity      integer NOT NULL,
    unit_price    numeric(10, 2) NOT NULL,
    line_amount   numeric(12, 2) NOT NULL
);
