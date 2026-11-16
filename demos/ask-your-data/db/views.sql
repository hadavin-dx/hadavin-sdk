-- Ask-your-data demo: the only relations the reader login can see. Explicit column lists; no email column.
CREATE SCHEMA analytics;

CREATE VIEW analytics.customers_v AS
    SELECT customer_id, full_name, country, signup_date FROM shop.customers;
COMMENT ON VIEW analytics.customers_v IS 'One row per customer. Contact details are not exposed.';

CREATE VIEW analytics.products_v AS
    SELECT product_id, product_name, category, unit_price FROM shop.products;
COMMENT ON VIEW analytics.products_v IS 'One row per product.';

CREATE VIEW analytics.orders_v AS
    SELECT order_id, customer_id, order_date, status, total_amount FROM shop.orders;
COMMENT ON VIEW analytics.orders_v IS 'One row per order. status is one of placed, paid, shipped, delivered, cancelled, refunded.';

CREATE VIEW analytics.order_items_v AS
    SELECT order_item_id, order_id, product_id, quantity, unit_price, line_amount FROM shop.order_items;
COMMENT ON VIEW analytics.order_items_v IS 'One row per order line. line_amount = quantity * unit_price.';
