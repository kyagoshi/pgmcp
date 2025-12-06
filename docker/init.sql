-- テスト用のサンプルテーブルを作成
-- Issue #1: テストデータのバリエーションの拡充
-- Issue #2: コメントやインデックス情報の取得機能

-- =============================================================================
-- 基本テーブル（既存）
-- =============================================================================

-- usersテーブル
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- usersテーブルとカラムにコメントを追加
COMMENT ON TABLE users IS 'ユーザー情報を管理するテーブル';
COMMENT ON COLUMN users.id IS 'ユーザーID（自動採番）';
COMMENT ON COLUMN users.name IS 'ユーザー名';
COMMENT ON COLUMN users.email IS 'メールアドレス';
COMMENT ON COLUMN users.created_at IS 'レコード作成日時';

-- usersテーブルにインデックスを追加
CREATE UNIQUE INDEX users_email_idx ON users (email) WHERE email IS NOT NULL;
CREATE INDEX users_created_at_idx ON users (created_at);

-- ordersテーブル
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ordersテーブルにコメントとインデックスを追加
COMMENT ON TABLE orders IS '注文情報を管理するテーブル';
COMMENT ON COLUMN orders.id IS '注文ID';
COMMENT ON COLUMN orders.user_id IS '注文したユーザーのID';
COMMENT ON COLUMN orders.total_amount IS '注文の合計金額';
COMMENT ON COLUMN orders.status IS '注文ステータス（pending/completed/shipped）';
CREATE INDEX orders_user_id_idx ON orders (user_id);
CREATE INDEX orders_status_idx ON orders (status);
CREATE INDEX orders_user_status_idx ON orders (user_id, status);
CREATE INDEX orders_user_created_idx ON orders (user_id, created_at DESC);

-- productsテーブル
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0
);

-- productsテーブルにコメントとインデックスを追加
COMMENT ON TABLE products IS '商品情報を管理するテーブル';
COMMENT ON COLUMN products.name IS '商品名';
COMMENT ON COLUMN products.price IS '商品価格';
CREATE INDEX products_name_idx ON products USING gin (to_tsvector('english', name));
CREATE INDEX products_price_idx ON products (price);

-- auditスキーマを作成
CREATE SCHEMA audit;

-- audit.logsテーブル
CREATE TABLE audit.logs (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- データ型のバリエーション
-- =============================================================================

-- 数値型テスト用テーブル（smallint, bigint, numeric, real, double precision）
CREATE TABLE numeric_types_test (
    id SERIAL PRIMARY KEY,
    smallint_col SMALLINT,
    bigint_col BIGINT,
    numeric_col NUMERIC(20, 5),
    real_col REAL,
    double_col DOUBLE PRECISION
);

-- 文字列型テスト用テーブル（char, varchar, text）
CREATE TABLE string_types_test (
    id SERIAL PRIMARY KEY,
    char_col CHAR(10),
    varchar_col VARCHAR(255),
    text_col TEXT
);

-- 日付・時刻型テスト用テーブル（date, time, timestamp, interval）
CREATE TABLE datetime_types_test (
    id SERIAL PRIMARY KEY,
    date_col DATE,
    time_col TIME,
    time_with_tz TIME WITH TIME ZONE,
    timestamp_col TIMESTAMP,
    timestamp_with_tz TIMESTAMP WITH TIME ZONE,
    interval_col INTERVAL
);

-- JSON型テスト用テーブル（json, jsonb）
CREATE TABLE json_types_test (
    id SERIAL PRIMARY KEY,
    json_col JSON,
    jsonb_col JSONB
);

-- 配列型テスト用テーブル（integer[], text[]）
CREATE TABLE array_types_test (
    id SERIAL PRIMARY KEY,
    int_array INTEGER[],
    text_array TEXT[],
    multi_dim_array INTEGER[][]
);

-- UUID型テスト用テーブル
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE uuid_types_test (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100),
    reference_id UUID
);

-- バイナリ型テスト用テーブル（bytea）
CREATE TABLE binary_types_test (
    id SERIAL PRIMARY KEY,
    binary_data BYTEA,
    file_name VARCHAR(255)
);

-- =============================================================================
-- エッジケース
-- =============================================================================

-- NULL値を含むカラムのテスト用テーブル
CREATE TABLE nullable_test (
    id SERIAL PRIMARY KEY,
    required_col VARCHAR(100) NOT NULL,
    nullable_col VARCHAR(100),
    nullable_with_default VARCHAR(100) DEFAULT NULL
);

-- 空文字のデフォルト値テスト用テーブル
CREATE TABLE empty_default_test (
    id SERIAL PRIMARY KEY,
    empty_string_default VARCHAR(100) DEFAULT '',
    space_default VARCHAR(100) DEFAULT ' ',
    normal_default VARCHAR(100) DEFAULT 'default_value'
);

-- 特殊文字を含むテーブル名・カラム名
CREATE TABLE "Special-Table_Name!@#" (
    id SERIAL PRIMARY KEY,
    "Column With Spaces" VARCHAR(100),
    "column-with-dashes" VARCHAR(100),
    "日本語カラム" VARCHAR(100)
);

-- 長いテーブル名・カラム名
CREATE TABLE this_is_a_very_long_table_name_that_tests_the_limits_of_identifier_length (
    id SERIAL PRIMARY KEY,
    this_is_a_very_long_column_name_that_also_tests_identifier_limits VARCHAR(100)
);

-- =============================================================================
-- 複雑なリレーション
-- =============================================================================

-- 複合主キーテスト用テーブル
CREATE TABLE composite_pk_test (
    key_part1 INTEGER NOT NULL,
    key_part2 VARCHAR(50) NOT NULL,
    value TEXT,
    PRIMARY KEY (key_part1, key_part2)
);

-- 複数の外部キーテスト用テーブル
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE multiple_fk_test (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    tag_id INTEGER REFERENCES tags(id),
    description TEXT
);

-- 自己参照外部キーテスト用テーブル
CREATE TABLE self_reference_test (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES self_reference_test(id)
);

-- カスケード削除・更新テスト用テーブル
CREATE TABLE cascade_parent (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE cascade_child (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER NOT NULL REFERENCES cascade_parent(id) ON DELETE CASCADE ON UPDATE CASCADE,
    value TEXT
);

CREATE TABLE cascade_set_null (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER REFERENCES cascade_parent(id) ON DELETE SET NULL ON UPDATE SET NULL,
    value TEXT
);

-- Virtual Foreign Key (UUID PK with *_id)
CREATE TABLE vfk_uuid_parent (
    vfk_uuid_parent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100)
);

CREATE TABLE vfk_uuid_child (
    id SERIAL PRIMARY KEY,
    vfk_uuid_parent_id UUID,
    note TEXT
);

-- Virtual Foreign Key (BIGINT PK with *_no)
CREATE TABLE vfk_no_parent (
    vfk_no_parent_no BIGINT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE vfk_no_child (
    id SERIAL PRIMARY KEY,
    vfk_no_parent_no BIGINT,
    note TEXT
);

-- より複雑な Virtual Foreign Keys（UUID系）
CREATE TABLE vfk_uuid_customer (
    vfk_uuid_customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100)
);

CREATE TABLE vfk_uuid_address (
    vfk_uuid_address_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_customer_id UUID,
    city VARCHAR(100)
);

CREATE TABLE vfk_uuid_order (
    vfk_uuid_order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_customer_id UUID,
    vfk_uuid_address_id UUID,
    total_amount NUMERIC(10,2)
);

CREATE TABLE vfk_uuid_order_item (
    vfk_uuid_order_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_order_id UUID,
    vfk_uuid_product_id UUID,
    quantity INTEGER
);

CREATE TABLE vfk_uuid_product (
    vfk_uuid_product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_category_id UUID,
    name VARCHAR(100)
);

CREATE TABLE vfk_uuid_category (
    vfk_uuid_category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID,
    name VARCHAR(100)
);

CREATE TABLE vfk_uuid_invoice (
    vfk_uuid_invoice_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_order_id UUID,
    amount NUMERIC(10,2)
);

CREATE TABLE vfk_uuid_payment (
    vfk_uuid_payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_invoice_id UUID,
    vfk_uuid_payment_method_id UUID,
    status VARCHAR(50)
);

CREATE TABLE vfk_uuid_payment_method (
    vfk_uuid_payment_method_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    method_name VARCHAR(50)
);

CREATE TABLE vfk_uuid_shipment (
    vfk_uuid_shipment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_order_id UUID,
    vfk_uuid_warehouse_id UUID,
    tracking_code VARCHAR(50)
);

CREATE TABLE vfk_uuid_warehouse (
    vfk_uuid_warehouse_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_region_id UUID,
    name VARCHAR(100)
);

CREATE TABLE vfk_uuid_region (
    vfk_uuid_region_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100)
);

CREATE TABLE vfk_uuid_shipment_event (
    vfk_uuid_shipment_event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_shipment_id UUID,
    event_type VARCHAR(50)
);

CREATE TABLE vfk_uuid_return_request (
    vfk_uuid_return_request_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_order_id UUID,
    reason_id UUID,
    status VARCHAR(50)
);

CREATE TABLE vfk_uuid_return_reason (
    vfk_uuid_return_reason_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    description TEXT
);

CREATE TABLE vfk_uuid_loyalty_account (
    vfk_uuid_loyalty_account_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_customer_id UUID,
    points INTEGER DEFAULT 0
);

CREATE TABLE vfk_uuid_loyalty_activity (
    vfk_uuid_loyalty_activity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_loyalty_account_id UUID,
    vfk_uuid_order_id UUID,
    delta_points INTEGER
);

CREATE TABLE vfk_uuid_marketing_campaign (
    vfk_uuid_marketing_campaign_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100)
);

CREATE TABLE vfk_uuid_campaign_enrollment (
    vfk_uuid_campaign_enrollment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_customer_id UUID,
    vfk_uuid_marketing_campaign_id UUID
);

CREATE TABLE vfk_uuid_coupon (
    vfk_uuid_coupon_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_marketing_campaign_id UUID,
    code VARCHAR(50)
);

CREATE TABLE vfk_uuid_coupon_redemption (
    vfk_uuid_coupon_redemption_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vfk_uuid_coupon_id UUID,
    vfk_uuid_order_id UUID,
    vfk_uuid_customer_id UUID
);

-- より複雑な Virtual Foreign Keys（BIGINT系）
CREATE TABLE vfk_no_customer (
    vfk_no_customer_no BIGINT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE vfk_no_order (
    vfk_no_order_no BIGINT PRIMARY KEY,
    vfk_no_customer_no BIGINT,
    total_amount NUMERIC(10,2)
);

CREATE TABLE vfk_no_order_item (
    vfk_no_order_item_no BIGINT PRIMARY KEY,
    vfk_no_order_no BIGINT,
    vfk_no_product_no BIGINT,
    quantity INTEGER
);

CREATE TABLE vfk_no_product (
    vfk_no_product_no BIGINT PRIMARY KEY,
    vfk_no_category_no BIGINT,
    name VARCHAR(100)
);

CREATE TABLE vfk_no_category (
    vfk_no_category_no BIGINT PRIMARY KEY,
    parent_no BIGINT,
    name VARCHAR(100)
);

CREATE TABLE vfk_no_supplier (
    vfk_no_supplier_no BIGINT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE vfk_no_supplier_product (
    vfk_no_supplier_product_no BIGINT PRIMARY KEY,
    vfk_no_supplier_no BIGINT,
    vfk_no_product_no BIGINT
);

CREATE TABLE vfk_no_warehouse (
    vfk_no_warehouse_no BIGINT PRIMARY KEY,
    vfk_no_region_no BIGINT,
    name VARCHAR(100)
);

CREATE TABLE vfk_no_region (
    vfk_no_region_no BIGINT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE vfk_no_inventory (
    vfk_no_inventory_no BIGINT PRIMARY KEY,
    vfk_no_product_no BIGINT,
    vfk_no_warehouse_no BIGINT,
    quantity INTEGER
);

-- =============================================================================
-- その他
-- =============================================================================

-- 大量のカラムを持つテーブル
CREATE TABLE many_columns_test (
    id SERIAL PRIMARY KEY,
    col_01 VARCHAR(100), col_02 VARCHAR(100), col_03 VARCHAR(100), col_04 VARCHAR(100), col_05 VARCHAR(100),
    col_06 VARCHAR(100), col_07 VARCHAR(100), col_08 VARCHAR(100), col_09 VARCHAR(100), col_10 VARCHAR(100),
    col_11 INTEGER, col_12 INTEGER, col_13 INTEGER, col_14 INTEGER, col_15 INTEGER,
    col_16 INTEGER, col_17 INTEGER, col_18 INTEGER, col_19 INTEGER, col_20 INTEGER,
    col_21 TEXT, col_22 TEXT, col_23 TEXT, col_24 TEXT, col_25 TEXT,
    col_26 BOOLEAN, col_27 BOOLEAN, col_28 BOOLEAN, col_29 BOOLEAN, col_30 BOOLEAN
);

-- パーティションテーブル（PostgreSQL 10+）
CREATE TABLE partitioned_logs (
    id SERIAL,
    log_date DATE NOT NULL,
    message TEXT,
    PRIMARY KEY (id, log_date)
) PARTITION BY RANGE (log_date);

CREATE TABLE partitioned_logs_2024 PARTITION OF partitioned_logs
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE partitioned_logs_2025 PARTITION OF partitioned_logs
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- 継承テーブル
CREATE TABLE base_entity (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE person_entity (
    email VARCHAR(255),
    birth_date DATE
) INHERITS (base_entity);

CREATE TABLE organization_entity (
    tax_id VARCHAR(50),
    employee_count INTEGER
) INHERITS (base_entity);

-- =============================================================================
-- サンプルデータの挿入
-- =============================================================================

-- 基本テーブル
INSERT INTO users (name, email) VALUES
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com'),
    ('Charlie', 'charlie@example.com');

INSERT INTO products (name, description, price, stock) VALUES
    ('Laptop', 'High-performance laptop', 1299.99, 10),
    ('Mouse', 'Wireless mouse', 29.99, 50),
    ('Keyboard', 'Mechanical keyboard', 149.99, 25);

INSERT INTO orders (user_id, total_amount, status) VALUES
    (1, 1329.98, 'completed'),
    (2, 29.99, 'pending'),
    (1, 149.99, 'shipped');

-- 数値型テスト
INSERT INTO numeric_types_test (smallint_col, bigint_col, numeric_col, real_col, double_col) VALUES
    (32767, 9223372036854775807, 12345.67890, 3.14159, 3.141592653589793),
    (-32768, -9223372036854775808, -12345.67890, -3.14159, -3.141592653589793),
    (NULL, NULL, NULL, NULL, NULL);

-- 文字列型テスト
INSERT INTO string_types_test (char_col, varchar_col, text_col) VALUES
    ('ABCD      ', 'Variable length string', 'This is a very long text that can contain much more data than varchar'),
    ('', '', ''),
    (NULL, NULL, NULL);

-- 日付・時刻型テスト
INSERT INTO datetime_types_test (date_col, time_col, time_with_tz, timestamp_col, timestamp_with_tz, interval_col) VALUES
    ('2025-12-05', '12:30:00', '12:30:00+09:00', '2025-12-05 12:30:00', '2025-12-05 12:30:00+09:00', '1 year 2 months 3 days'),
    ('1970-01-01', '00:00:00', '00:00:00+00:00', '1970-01-01 00:00:00', '1970-01-01 00:00:00+00:00', '0 seconds'),
    (NULL, NULL, NULL, NULL, NULL, NULL);

-- JSON型テスト
INSERT INTO json_types_test (json_col, jsonb_col) VALUES
    ('{"name": "test", "value": 123}', '{"name": "test", "value": 123, "nested": {"key": "value"}}'),
    ('[]', '[]'),
    (NULL, NULL);

-- 配列型テスト
INSERT INTO array_types_test (int_array, text_array, multi_dim_array) VALUES
    ('{1, 2, 3, 4, 5}', '{"apple", "banana", "cherry"}', '{{1,2},{3,4}}'),
    ('{}', '{}', '{}'),
    (NULL, NULL, NULL);

-- UUID型テスト
INSERT INTO uuid_types_test (name, reference_id) VALUES
    ('First UUID', uuid_generate_v4()),
    ('Second UUID', NULL);

-- バイナリ型テスト
INSERT INTO binary_types_test (binary_data, file_name) VALUES
    (E'\\x48656C6C6F', 'hello.bin'),
    (NULL, 'empty.bin');

-- NULL値テスト
INSERT INTO nullable_test (required_col, nullable_col, nullable_with_default) VALUES
    ('Required', 'Has value', 'Custom value'),
    ('Required only', NULL, NULL);

-- 空文字デフォルト値テスト
INSERT INTO empty_default_test (empty_string_default, space_default, normal_default) VALUES
    (DEFAULT, DEFAULT, DEFAULT);

-- 特殊文字テーブルテスト
INSERT INTO "Special-Table_Name!@#" ("Column With Spaces", "column-with-dashes", "日本語カラム") VALUES
    ('value1', 'value2', '日本語の値');

-- 複合主キーテスト
INSERT INTO composite_pk_test (key_part1, key_part2, value) VALUES
    (1, 'A', 'First combination'),
    (1, 'B', 'Second combination'),
    (2, 'A', 'Third combination');

-- 複数外部キーテスト
INSERT INTO categories (name) VALUES ('Electronics'), ('Books');
INSERT INTO tags (name) VALUES ('Sale'), ('New');
INSERT INTO multiple_fk_test (user_id, category_id, tag_id, description) VALUES
    (1, 1, 1, 'User 1 in Electronics with Sale tag'),
    (2, 2, 2, 'User 2 in Books with New tag');

-- 自己参照テスト
INSERT INTO self_reference_test (name, parent_id) VALUES
    ('Root', NULL),
    ('Child 1', 1),
    ('Child 2', 1),
    ('Grandchild', 2);

-- カスケードテスト
INSERT INTO cascade_parent (name) VALUES ('Parent 1'), ('Parent 2');
INSERT INTO cascade_child (parent_id, value) VALUES (1, 'Child of Parent 1');
INSERT INTO cascade_set_null (parent_id, value) VALUES (1, 'Child with set null');

-- Virtual Foreign Key テストデータ
INSERT INTO vfk_uuid_parent (name) VALUES ('VFK UUID Parent A'), ('VFK UUID Parent B');
INSERT INTO vfk_uuid_child (vfk_uuid_parent_id, note)
SELECT vfk_uuid_parent_id, 'Child for ' || name FROM vfk_uuid_parent;

INSERT INTO vfk_no_parent (vfk_no_parent_no, name) VALUES (1001, 'VFK NO Parent A'), (1002, 'VFK NO Parent B');
INSERT INTO vfk_no_child (vfk_no_parent_no, note) VALUES (1001, 'Child for parent 1001'), (1002, 'Child for parent 1002');

-- 複雑な Virtual Foreign Keys（UUID系）テストデータ
INSERT INTO vfk_uuid_customer (name) VALUES ('C-1'), ('C-2');
INSERT INTO vfk_uuid_address (vfk_uuid_customer_id, city)
SELECT vfk_uuid_customer_id, 'City-' || name FROM vfk_uuid_customer;

INSERT INTO vfk_uuid_order (vfk_uuid_customer_id, vfk_uuid_address_id, total_amount)
SELECT c.vfk_uuid_customer_id, a.vfk_uuid_address_id, 120.50
FROM vfk_uuid_customer c
JOIN vfk_uuid_address a ON a.vfk_uuid_customer_id = c.vfk_uuid_customer_id
LIMIT 2;

INSERT INTO vfk_uuid_product (vfk_uuid_category_id, name) VALUES (NULL, 'P-1'), (NULL, 'P-2');
INSERT INTO vfk_uuid_category (parent_id, name) VALUES (NULL, 'Cat-Root'), (NULL, 'Cat-Leaf');
UPDATE vfk_uuid_product SET vfk_uuid_category_id = (SELECT vfk_uuid_category_id FROM vfk_uuid_category LIMIT 1);

INSERT INTO vfk_uuid_order_item (vfk_uuid_order_id, vfk_uuid_product_id, quantity)
SELECT o.vfk_uuid_order_id, p.vfk_uuid_product_id, 2
FROM vfk_uuid_order o CROSS JOIN LATERAL (
    SELECT vfk_uuid_product_id FROM vfk_uuid_product LIMIT 1
) p
LIMIT 2;

INSERT INTO vfk_uuid_invoice (vfk_uuid_order_id, amount)
SELECT vfk_uuid_order_id, 120.50 FROM vfk_uuid_order;

INSERT INTO vfk_uuid_payment_method (method_name) VALUES ('card'), ('bank');
INSERT INTO vfk_uuid_payment (vfk_uuid_invoice_id, vfk_uuid_payment_method_id, status)
SELECT i.vfk_uuid_invoice_id, pm.vfk_uuid_payment_method_id, 'pending'
FROM vfk_uuid_invoice i
CROSS JOIN LATERAL (
    SELECT vfk_uuid_payment_method_id FROM vfk_uuid_payment_method LIMIT 1
) pm;

INSERT INTO vfk_uuid_region (name) VALUES ('North'), ('South');
INSERT INTO vfk_uuid_warehouse (vfk_uuid_region_id, name)
SELECT vfk_uuid_region_id, 'WH-' || name FROM vfk_uuid_region;
INSERT INTO vfk_uuid_shipment (vfk_uuid_order_id, vfk_uuid_warehouse_id, tracking_code)
SELECT o.vfk_uuid_order_id, w.vfk_uuid_warehouse_id, 'TRK-' || substring(o.vfk_uuid_order_id::text, 1, 8)
FROM vfk_uuid_order o
JOIN vfk_uuid_warehouse w ON TRUE
LIMIT 2;
INSERT INTO vfk_uuid_shipment_event (vfk_uuid_shipment_id, event_type)
SELECT vfk_uuid_shipment_id, 'created' FROM vfk_uuid_shipment;

INSERT INTO vfk_uuid_marketing_campaign (name) VALUES ('Winter'), ('Spring');
INSERT INTO vfk_uuid_coupon (vfk_uuid_marketing_campaign_id, code)
SELECT vfk_uuid_marketing_campaign_id, 'CP-' || substring(vfk_uuid_marketing_campaign_id::text, 1, 6)
FROM vfk_uuid_marketing_campaign;
INSERT INTO vfk_uuid_coupon_redemption (vfk_uuid_coupon_id, vfk_uuid_order_id, vfk_uuid_customer_id)
SELECT cpn.vfk_uuid_coupon_id, ord.vfk_uuid_order_id, ord.vfk_uuid_customer_id
FROM vfk_uuid_coupon cpn
JOIN vfk_uuid_order ord ON TRUE
LIMIT 2;

INSERT INTO vfk_uuid_loyalty_account (vfk_uuid_customer_id, points)
SELECT vfk_uuid_customer_id, 100 FROM vfk_uuid_customer;
INSERT INTO vfk_uuid_loyalty_activity (vfk_uuid_loyalty_account_id, vfk_uuid_order_id, delta_points)
SELECT la.vfk_uuid_loyalty_account_id, o.vfk_uuid_order_id, 10
FROM vfk_uuid_loyalty_account la
JOIN vfk_uuid_order o ON la.vfk_uuid_customer_id = o.vfk_uuid_customer_id;

INSERT INTO vfk_uuid_campaign_enrollment (vfk_uuid_customer_id, vfk_uuid_marketing_campaign_id)
SELECT vfk_uuid_customer_id, vfk_uuid_marketing_campaign_id FROM vfk_uuid_customer, vfk_uuid_marketing_campaign LIMIT 2;

-- 複雑な Virtual Foreign Keys（BIGINT系）テストデータ
INSERT INTO vfk_no_region (vfk_no_region_no, name) VALUES (2001, 'R-North'), (2002, 'R-South');
INSERT INTO vfk_no_warehouse (vfk_no_warehouse_no, vfk_no_region_no, name) VALUES (3001, 2001, 'W-North'), (3002, 2002, 'W-South');
INSERT INTO vfk_no_category (vfk_no_category_no, parent_no, name) VALUES (4001, NULL, 'Electronics'), (4002, 4001, 'Mobile');
INSERT INTO vfk_no_product (vfk_no_product_no, vfk_no_category_no, name) VALUES (5001, 4002, 'Phone'), (5002, 4001, 'Laptop');
INSERT INTO vfk_no_customer (vfk_no_customer_no, name) VALUES (6001, 'Customer-A'), (6002, 'Customer-B');
INSERT INTO vfk_no_order (vfk_no_order_no, vfk_no_customer_no, total_amount) VALUES (7001, 6001, 999.99), (7002, 6002, 199.99);
INSERT INTO vfk_no_order_item (vfk_no_order_item_no, vfk_no_order_no, vfk_no_product_no, quantity) VALUES
    (8001, 7001, 5001, 1),
    (8002, 7001, 5002, 1),
    (8003, 7002, 5002, 2);
INSERT INTO vfk_no_supplier (vfk_no_supplier_no, name) VALUES (9001, 'Supplier-A');
INSERT INTO vfk_no_supplier_product (vfk_no_supplier_product_no, vfk_no_supplier_no, vfk_no_product_no) VALUES (9101, 9001, 5001);
INSERT INTO vfk_no_inventory (vfk_no_inventory_no, vfk_no_product_no, vfk_no_warehouse_no, quantity) VALUES (9201, 5001, 3001, 50), (9202, 5002, 3002, 30);

-- 大量カラムテスト
INSERT INTO many_columns_test (
    col_01, col_02, col_03, col_04, col_05,
    col_11, col_12, col_13, col_14, col_15,
    col_21, col_22,
    col_26, col_27
) VALUES (
    'val1', 'val2', 'val3', 'val4', 'val5',
    1, 2, 3, 4, 5,
    'text1', 'text2',
    true, false
);

-- パーティションテーブルテスト
INSERT INTO partitioned_logs (log_date, message) VALUES
    ('2024-06-15', 'Log from 2024'),
    ('2025-03-20', 'Log from 2025');

-- 継承テーブルテスト
INSERT INTO person_entity (name, email, birth_date) VALUES
    ('John Doe', 'john@example.com', '1990-01-15');
INSERT INTO organization_entity (name, tax_id, employee_count) VALUES
    ('Acme Corp', '123-456-789', 100);
