-- ==========================================================================
-- FarmConnect — MySQL schema
-- Run once:  mysql -u root -p < database/schema.sql
-- (app.py can also create these tables automatically via SQLAlchemy.)
-- ==========================================================================
CREATE DATABASE IF NOT EXISTS farmconnect
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE farmconnect;

CREATE TABLE IF NOT EXISTS users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  full_name     VARCHAR(120) NOT NULL,
  email         VARCHAR(160) NOT NULL UNIQUE,
  phone         VARCHAR(30),
  password_hash VARCHAR(255) NOT NULL,
  role          ENUM('customer','farmer','admin') NOT NULL,
  status        ENUM('active','suspended') NOT NULL DEFAULT 'active',
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_users_role (role)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS farmers (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  user_id       INT NOT NULL UNIQUE,
  farm_name     VARCHAR(140),
  farm_location VARCHAR(140),
  bio           TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_farmers_location (farm_location)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customers (
  id      INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  address VARCHAR(255),
  city    VARCHAR(90),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Administrators are rows in `users` with role='admin'. This view exposes them.
CREATE OR REPLACE VIEW admins AS
  SELECT id, full_name, email, created_at FROM users WHERE role = 'admin';

CREATE TABLE IF NOT EXISTS categories (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE,
  slug VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  farmer_id        INT NOT NULL,
  category_id      INT NOT NULL,
  name             VARCHAR(160) NOT NULL,
  description      TEXT,
  price            DECIMAL(10,2) NOT NULL,
  quantity         INT NOT NULL DEFAULT 0,
  unit             ENUM('kg','bag','crate','litre','piece') NOT NULL DEFAULT 'kg',
  image            VARCHAR(255),
  location         VARCHAR(140),
  status           ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  rejection_reason VARCHAR(255),
  created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (farmer_id)   REFERENCES farmers(id)   ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES categories(id),
  INDEX idx_products_status (status),
  INDEX idx_products_name (name),
  INDEX idx_products_location (location)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS product_images (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  filename   VARCHAR(255) NOT NULL,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cart (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  product_id INT NOT NULL,
  quantity   INT NOT NULL DEFAULT 1,
  UNIQUE KEY uq_cart_user_product (user_id, product_id),
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS orders (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  user_id        INT NOT NULL,
  full_name      VARCHAR(120) NOT NULL,
  phone          VARCHAR(30)  NOT NULL,
  email          VARCHAR(160) NOT NULL,
  address        VARCHAR(255) NOT NULL,
  payment_method ENUM('cash','momo','card') NOT NULL DEFAULT 'cash',
  total          DECIMAL(10,2) NOT NULL,
  status         ENUM('pending','confirmed','shipped','delivered','cancelled')
                   NOT NULL DEFAULT 'pending',
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_orders_status (status),
  INDEX idx_orders_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS order_items (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  order_id   INT NOT NULL,
  product_id INT NOT NULL,
  farmer_id  INT NOT NULL,
  quantity   INT NOT NULL,
  price      DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (farmer_id)  REFERENCES farmers(id),
  INDEX idx_items_farmer (farmer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notifications (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  message    VARCHAR(255) NOT NULL,
  link       VARCHAR(255),
  is_read    BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reviews (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  user_id    INT NOT NULL,
  rating     TINYINT NOT NULL,
  comment    TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS wishlist (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  product_id INT NOT NULL,
  UNIQUE KEY uq_wish_user_product (user_id, product_id),
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS contact_messages (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(120) NOT NULL,
  email      VARCHAR(160) NOT NULL,
  subject    VARCHAR(160),
  message    TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Seed the product categories -------------------------------------------------
INSERT IGNORE INTO categories (name, slug) VALUES
  ('Vegetables','vegetables'), ('Fruits','fruits'), ('Grains','grains'),
  ('Tubers','tubers'), ('Livestock','livestock'), ('Poultry','poultry'),
  ('Fish','fish'), ('Dairy','dairy'), ('Herbs','herbs'), ('Seeds','seeds'),
  ('Fertilisers','fertilisers'), ('Farm Equipment','farm-equipment'),
  ('Others','others');
