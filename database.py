"""
Database module for Weekly Grocery Management System
Uses SQLite for data storage with all required entities:
- Users, Categories, Products, Orders, OrderDetails
"""

import sqlite3
import hashlib
from datetime import datetime
from contextlib import contextmanager

DATABASE_PATH = "grocery_management.db"

@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize the database with all required tables"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Users table - stores login and profile information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(40) NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Categories table - defines product groups like Dairy, Beverages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT
            )
        ''')
        
        # Products table - contains item details (name, brand, unit price)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name VARCHAR(100) NOT NULL,
                category_id INTEGER NOT NULL,
                brand VARCHAR(50),
                unit_price DECIMAL(10, 2) NOT NULL,
                unit_measure VARCHAR(20) DEFAULT 'unit',
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            )
        ''')
        
        # Orders table - records each purchase with order date and total amount
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(10, 2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        
        # OrderDetails table - links orders and products with quantity and subtotal
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_details (
                detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                unit_price DECIMAL(10, 2) NOT NULL,
                subtotal DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            )
        ''')
        
        # Shopping Lists table - for planning weekly groceries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shopping_lists (
                list_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                list_name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON UPDATE CASCADE ON DELETE CASCADE
            )
        ''')
        
        # Shopping List Items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shopping_list_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                is_purchased BOOLEAN DEFAULT 0,
                FOREIGN KEY (list_id) REFERENCES shopping_lists(list_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            )
        ''')
        
        # Inventory table - tracks stock and expiry dates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                min_quantity INTEGER DEFAULT 2,
                expiry_date DATE,
                purchase_date DATE DEFAULT CURRENT_DATE,
                location VARCHAR(50) DEFAULT 'Pantry',
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
                    ON UPDATE CASCADE ON DELETE RESTRICT
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_details_order ON order_details(order_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_details_product ON order_details(product_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_expiry ON inventory(expiry_date)')
        
        conn.commit()
        print("Database initialized successfully!")

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

# ==================== USER CRUD OPERATIONS ====================

def create_user(username, email, password):
    """Create a new user"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, hash_password(password)))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"User already exists: {e}")

def get_user_by_username(username):
    """Get user by username"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cursor.fetchone()

def get_user_by_id(user_id):
    """Get user by ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

def get_all_users():
    """Get all users"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, email, created_at FROM users')
        return cursor.fetchall()

def authenticate_user(username, password):
    """Authenticate user and return user data if valid"""
    user = get_user_by_username(username)
    if user and verify_password(password, user['password_hash']):
        return user
    return None

# ==================== CATEGORY CRUD OPERATIONS ====================

def create_category(category_name, description=None):
    """Create a new category"""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO categories (category_name, description)
                VALUES (?, ?)
            ''', (category_name, description))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Category '{category_name}' already exists")

def get_all_categories():
    """Get all categories"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY category_name')
        return cursor.fetchall()

def get_category_by_id(category_id):
    """Get category by ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories WHERE category_id = ?', (category_id,))
        return cursor.fetchone()

def update_category(category_id, category_name, description):
    """Update category"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE categories SET category_name = ?, description = ?
            WHERE category_id = ?
        ''', (category_name, description, category_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_category(category_id):
    """Delete category if no products are linked"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM products WHERE category_id = ?', (category_id,))
        if cursor.fetchone()[0] > 0:
            raise ValueError("Cannot delete category with linked products")
        cursor.execute('DELETE FROM categories WHERE category_id = ?', (category_id,))
        conn.commit()
        return cursor.rowcount > 0

# ==================== PRODUCT CRUD OPERATIONS ====================

def create_product(product_name, category_id, unit_price, brand=None, unit_measure='unit'):
    """Create a new product"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (product_name, category_id, brand, unit_price, unit_measure)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_name, category_id, brand, unit_price, unit_measure))
        conn.commit()
        return cursor.lastrowid

def get_all_products():
    """Get all products with category information"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, c.category_name 
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            ORDER BY c.category_name, p.product_name
        ''')
        return cursor.fetchall()

def get_products_by_category(category_id):
    """Get products by category"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, c.category_name 
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.category_id = ?
            ORDER BY p.product_name
        ''', (category_id,))
        return cursor.fetchall()

def get_product_by_id(product_id):
    """Get product by ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, c.category_name 
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.product_id = ?
        ''', (product_id,))
        return cursor.fetchone()

def update_product(product_id, product_name, category_id, unit_price, brand, unit_measure):
    """Update product"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET product_name = ?, category_id = ?, unit_price = ?, 
                brand = ?, unit_measure = ?
            WHERE product_id = ?
        ''', (product_name, category_id, unit_price, brand, unit_measure, product_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_product(product_id):
    """Delete product"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        conn.commit()
        return cursor.rowcount > 0

def search_products(search_term):
    """Search products by name or brand"""
    with get_connection() as conn:
        cursor = conn.cursor()
        search_pattern = f'%{search_term}%'
        cursor.execute('''
            SELECT p.*, c.category_name 
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.product_name LIKE ? OR p.brand LIKE ?
            ORDER BY p.product_name
        ''', (search_pattern, search_pattern))
        return cursor.fetchall()

# ==================== ORDER CRUD OPERATIONS ====================

def create_order(user_id):
    """Create a new order"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, status)
            VALUES (?, 'pending')
        ''', (user_id,))
        conn.commit()
        return cursor.lastrowid

def add_order_detail(order_id, product_id, quantity):
    """Add item to order"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Get product price
        cursor.execute('SELECT unit_price FROM products WHERE product_id = ?', (product_id,))
        product = cursor.fetchone()
        if not product:
            raise ValueError("Product not found")
        
        unit_price = product['unit_price']
        subtotal = unit_price * quantity
        
        cursor.execute('''
            INSERT INTO order_details (order_id, product_id, quantity, unit_price, subtotal)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, product_id, quantity, unit_price, subtotal))
        
        # Update order total
        cursor.execute('''
            UPDATE orders SET total_amount = (
                SELECT SUM(subtotal) FROM order_details WHERE order_id = ?
            ) WHERE order_id = ?
        ''', (order_id, order_id))
        
        conn.commit()
        return cursor.lastrowid

def complete_order(order_id):
    """Mark order as completed"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders SET status = 'completed' WHERE order_id = ?
        ''', (order_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_user_orders(user_id):
    """Get all orders for a user"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM orders 
            WHERE user_id = ? 
            ORDER BY order_date DESC
        ''', (user_id,))
        return cursor.fetchall()

def get_order_details(order_id):
    """Get all items in an order"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT od.*, p.product_name, p.brand, c.category_name
            FROM order_details od
            JOIN products p ON od.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE od.order_id = ?
        ''', (order_id,))
        return cursor.fetchall()

def get_order_by_id(order_id):
    """Get order by ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
        return cursor.fetchone()

def delete_order(order_id):
    """Delete an order"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM orders WHERE order_id = ?', (order_id,))
        conn.commit()
        return cursor.rowcount > 0

# ==================== SHOPPING LIST OPERATIONS ====================

def create_shopping_list(user_id, list_name):
    """Create a new shopping list"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO shopping_lists (user_id, list_name)
            VALUES (?, ?)
        ''', (user_id, list_name))
        conn.commit()
        return cursor.lastrowid

def get_user_shopping_lists(user_id):
    """Get all shopping lists for a user"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT sl.*, 
                   COUNT(sli.item_id) as total_items,
                   SUM(CASE WHEN sli.is_purchased = 1 THEN 1 ELSE 0 END) as purchased_items
            FROM shopping_lists sl
            LEFT JOIN shopping_list_items sli ON sl.list_id = sli.list_id
            WHERE sl.user_id = ?
            GROUP BY sl.list_id
            ORDER BY sl.created_at DESC
        ''', (user_id,))
        return cursor.fetchall()

def add_item_to_shopping_list(list_id, product_id, quantity=1):
    """Add item to shopping list"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Check if item already exists in list
        cursor.execute('''
            SELECT item_id FROM shopping_list_items 
            WHERE list_id = ? AND product_id = ?
        ''', (list_id, product_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE shopping_list_items 
                SET quantity = quantity + ?
                WHERE list_id = ? AND product_id = ?
            ''', (quantity, list_id, product_id))
        else:
            cursor.execute('''
                INSERT INTO shopping_list_items (list_id, product_id, quantity)
                VALUES (?, ?, ?)
            ''', (list_id, product_id, quantity))
        
        conn.commit()
        return cursor.lastrowid

def get_shopping_list_items(list_id):
    """Get all items in a shopping list"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT sli.*, p.product_name, p.brand, p.unit_price, 
                   p.unit_measure, c.category_name
            FROM shopping_list_items sli
            JOIN products p ON sli.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE sli.list_id = ?
            ORDER BY c.category_name, p.product_name
        ''', (list_id,))
        return cursor.fetchall()

def toggle_shopping_list_item(item_id):
    """Toggle purchased status of shopping list item"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE shopping_list_items 
            SET is_purchased = NOT is_purchased
            WHERE item_id = ?
        ''', (item_id,))
        conn.commit()
        return cursor.rowcount > 0

def delete_shopping_list(list_id):
    """Delete a shopping list"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM shopping_lists WHERE list_id = ?', (list_id,))
        conn.commit()
        return cursor.rowcount > 0

def convert_shopping_list_to_order(list_id, user_id):
    """Convert a shopping list to an order"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all items from the shopping list
        items = get_shopping_list_items(list_id)
        if not items:
            raise ValueError("Shopping list is empty")
        
        # Create new order
        order_id = create_order(user_id)
        
        # Add each item to the order
        for item in items:
            add_order_detail(order_id, item['product_id'], item['quantity'])
        
        # Complete the order
        complete_order(order_id)
        
        # Mark shopping list as inactive
        cursor.execute('''
            UPDATE shopping_lists SET is_active = 0 WHERE list_id = ?
        ''', (list_id,))
        conn.commit()
        
        return order_id

# ==================== ANALYTICS & REPORTS ====================

def get_spending_by_category(user_id, start_date=None, end_date=None):
    """Get spending breakdown by category"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT c.category_name, SUM(od.subtotal) as total_spent
            FROM orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN products p ON od.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE o.user_id = ? AND o.status = 'completed'
        '''
        params = [user_id]
        
        if start_date:
            query += ' AND o.order_date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND o.order_date <= ?'
            params.append(end_date)
        
        query += ' GROUP BY c.category_id ORDER BY total_spent DESC'
        cursor.execute(query, params)
        return cursor.fetchall()

def get_monthly_spending(user_id, year=None):
    """Get monthly spending for a user"""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT strftime('%Y-%m', order_date) as month,
                   SUM(total_amount) as total_spent,
                   COUNT(*) as order_count
            FROM orders
            WHERE user_id = ? AND status = 'completed'
        '''
        params = [user_id]
        
        if year:
            query += " AND strftime('%Y', order_date) = ?"
            params.append(str(year))
        
        query += ' GROUP BY month ORDER BY month'
        cursor.execute(query, params)
        return cursor.fetchall()

def get_most_purchased_products(user_id, limit=10):
    """Get most frequently purchased products"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.product_name, p.brand, c.category_name,
                   SUM(od.quantity) as total_quantity,
                   COUNT(DISTINCT o.order_id) as order_count
            FROM orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN products p ON od.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE o.user_id = ? AND o.status = 'completed'
            GROUP BY p.product_id
            ORDER BY total_quantity DESC
            LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()

def get_weekly_spending(user_id):
    """Get spending for the last 7 days"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date(order_date) as day,
                   SUM(total_amount) as daily_total
            FROM orders
            WHERE user_id = ? 
              AND status = 'completed'
              AND order_date >= date('now', '-7 days')
            GROUP BY day
            ORDER BY day
        ''', (user_id,))
        return cursor.fetchall()

def get_total_spending(user_id):
    """Get total spending for a user"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(total_amount) as total_spent,
                   COUNT(*) as total_orders
            FROM orders
            WHERE user_id = ? AND status = 'completed'
        ''', (user_id,))
        return cursor.fetchone()

# ==================== INVENTORY OPERATIONS ====================

def add_to_inventory(user_id, product_id, quantity, expiry_date=None, location='Pantry', min_quantity=2, notes=None):
    """Add item to inventory"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Check if product already exists in inventory
        cursor.execute('''
            SELECT inventory_id, quantity FROM inventory 
            WHERE user_id = ? AND product_id = ? AND (expiry_date = ? OR (expiry_date IS NULL AND ? IS NULL))
        ''', (user_id, product_id, expiry_date, expiry_date))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing inventory item
            cursor.execute('''
                UPDATE inventory SET quantity = quantity + ?, min_quantity = ?, location = ?, notes = ?
                WHERE inventory_id = ?
            ''', (quantity, min_quantity, location, notes, existing['inventory_id']))
        else:
            # Insert new inventory item
            cursor.execute('''
                INSERT INTO inventory (user_id, product_id, quantity, min_quantity, expiry_date, location, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, product_id, quantity, min_quantity, expiry_date, location, notes))
        
        conn.commit()
        return cursor.lastrowid

def get_user_inventory(user_id):
    """Get all inventory items for a user"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT i.*, p.product_name, p.brand, p.unit_measure, c.category_name
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE i.user_id = ? AND i.quantity > 0
            ORDER BY c.category_name, p.product_name
        ''', (user_id,))
        return cursor.fetchall()

def get_expiring_soon(user_id, days=7):
    """Get items expiring within specified days"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT i.*, p.product_name, p.brand, p.unit_measure, c.category_name,
                   julianday(i.expiry_date) - julianday('now') as days_until_expiry
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE i.user_id = ? 
              AND i.quantity > 0
              AND i.expiry_date IS NOT NULL
              AND i.expiry_date <= date('now', '+' || ? || ' days')
              AND i.expiry_date >= date('now')
            ORDER BY i.expiry_date ASC
        ''', (user_id, days))
        return cursor.fetchall()

def get_expired_items(user_id):
    """Get items that have already expired"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT i.*, p.product_name, p.brand, p.unit_measure, c.category_name,
                   julianday('now') - julianday(i.expiry_date) as days_expired
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE i.user_id = ? 
              AND i.quantity > 0
              AND i.expiry_date IS NOT NULL
              AND i.expiry_date < date('now')
            ORDER BY i.expiry_date ASC
        ''', (user_id,))
        return cursor.fetchall()

def get_low_stock_items(user_id):
    """Get items that are running low (quantity <= min_quantity)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT i.*, p.product_name, p.brand, p.unit_measure, p.unit_price, c.category_name
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE i.user_id = ? 
              AND i.quantity <= i.min_quantity
              AND i.quantity > 0
            ORDER BY i.quantity ASC
        ''', (user_id,))
        return cursor.fetchall()

def get_out_of_stock_items(user_id):
    """Get items that are out of stock (quantity = 0)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT i.*, p.product_name, p.brand, p.unit_measure, p.unit_price, c.category_name
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE i.user_id = ? AND i.quantity = 0
            ORDER BY p.product_name
        ''', (user_id,))
        return cursor.fetchall()

def update_inventory_quantity(inventory_id, quantity):
    """Update inventory quantity"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE inventory SET quantity = ? WHERE inventory_id = ?
        ''', (quantity, inventory_id))
        conn.commit()
        return cursor.rowcount > 0

def update_inventory_item(inventory_id, quantity, min_quantity, expiry_date, location, notes):
    """Update inventory item details"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE inventory 
            SET quantity = ?, min_quantity = ?, expiry_date = ?, location = ?, notes = ?
            WHERE inventory_id = ?
        ''', (quantity, min_quantity, expiry_date, location, notes, inventory_id))
        conn.commit()
        return cursor.rowcount > 0

def delete_inventory_item(inventory_id):
    """Delete inventory item"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM inventory WHERE inventory_id = ?', (inventory_id,))
        conn.commit()
        return cursor.rowcount > 0

def use_inventory_item(inventory_id, quantity_used):
    """Decrease inventory quantity when item is used"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE inventory 
            SET quantity = MAX(0, quantity - ?)
            WHERE inventory_id = ?
        ''', (quantity_used, inventory_id))
        conn.commit()
        return cursor.rowcount > 0

def get_inventory_summary(user_id):
    """Get inventory summary statistics"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as total_items,
                SUM(quantity) as total_quantity,
                SUM(CASE WHEN quantity <= min_quantity AND quantity > 0 THEN 1 ELSE 0 END) as low_stock_count,
                SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END) as out_of_stock_count,
                SUM(CASE WHEN expiry_date IS NOT NULL AND expiry_date <= date('now', '+7 days') AND expiry_date >= date('now') THEN 1 ELSE 0 END) as expiring_soon_count,
                SUM(CASE WHEN expiry_date IS NOT NULL AND expiry_date < date('now') THEN 1 ELSE 0 END) as expired_count
            FROM inventory
            WHERE user_id = ?
        ''', (user_id,))
        return cursor.fetchone()

def get_inventory_by_location(user_id):
    """Get inventory grouped by location"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT location, COUNT(*) as item_count, SUM(quantity) as total_quantity
            FROM inventory
            WHERE user_id = ? AND quantity > 0
            GROUP BY location
            ORDER BY item_count DESC
        ''', (user_id,))
        return cursor.fetchall()

def get_inventory_by_category(user_id):
    """Get inventory grouped by category"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.category_name, COUNT(*) as item_count, SUM(i.quantity) as total_quantity
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE i.user_id = ? AND i.quantity > 0
            GROUP BY c.category_id
            ORDER BY item_count DESC
        ''', (user_id,))
        return cursor.fetchall()

def get_suggested_products(user_id, limit=5):
    """Get suggested products based on purchase history"""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Get products from frequently purchased categories that user hasn't bought recently
        cursor.execute('''
            WITH UserCategories AS (
                SELECT DISTINCT p.category_id, COUNT(*) as frequency
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                JOIN products p ON od.product_id = p.product_id
                WHERE o.user_id = ?
                GROUP BY p.category_id
                ORDER BY frequency DESC
                LIMIT 5
            ),
            RecentProducts AS (
                SELECT DISTINCT od.product_id
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                WHERE o.user_id = ? AND o.order_date >= date('now', '-30 days')
            )
            SELECT p.*, c.category_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.category_id IN (SELECT category_id FROM UserCategories)
              AND p.product_id NOT IN (SELECT product_id FROM RecentProducts)
            ORDER BY RANDOM()
            LIMIT ?
        ''', (user_id, user_id, limit))
        return cursor.fetchall()

# ==================== SAMPLE DATA ====================

def insert_sample_data():
    """Insert sample data for testing"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM categories')
        if cursor.fetchone()[0] > 0:
            print("Sample data already exists!")
            return
        
        # Insert categories
        categories = [
            ('Dairy', 'Milk, cheese, yogurt, and other dairy products'),
            ('Fruits', 'Fresh fruits and berries'),
            ('Vegetables', 'Fresh vegetables and greens'),
            ('Meat & Poultry', 'Fresh and frozen meat products'),
            ('Beverages', 'Drinks, juices, and sodas'),
            ('Bakery', 'Bread, pastries, and baked goods'),
            ('Frozen Foods', 'Frozen meals and ingredients'),
            ('Snacks', 'Chips, crackers, and snack items'),
            ('Household', 'Cleaning supplies and household items'),
            ('Personal Care', 'Hygiene and personal care products')
        ]
        cursor.executemany('''
            INSERT INTO categories (category_name, description) VALUES (?, ?)
        ''', categories)
        
        # Insert products
        products = [
            # Dairy
            ('Whole Milk', 1, 'Organic Valley', 4.99, 'gallon'),
            ('Greek Yogurt', 1, 'Chobani', 5.49, 'pack'),
            ('Cheddar Cheese', 1, 'Tillamook', 6.99, 'lb'),
            ('Butter', 1, 'Kerrygold', 5.49, 'pack'),
            ('Eggs', 1, 'Happy Egg', 5.99, 'dozen'),
            # Fruits
            ('Bananas', 2, 'Dole', 0.59, 'lb'),
            ('Apples', 2, 'Honeycrisp', 2.99, 'lb'),
            ('Strawberries', 2, 'Driscoll', 4.99, 'pack'),
            ('Oranges', 2, 'Sunkist', 1.29, 'each'),
            ('Grapes', 2, 'Red Globe', 3.99, 'lb'),
            # Vegetables
            ('Broccoli', 3, 'Fresh', 2.49, 'bunch'),
            ('Carrots', 3, 'Bolthouse', 2.99, 'bag'),
            ('Spinach', 3, 'Earthbound', 4.49, 'bag'),
            ('Tomatoes', 3, 'Roma', 1.99, 'lb'),
            ('Potatoes', 3, 'Russet', 4.99, 'bag'),
            # Meat & Poultry
            ('Chicken Breast', 4, 'Perdue', 8.99, 'lb'),
            ('Ground Beef', 4, 'Angus', 7.99, 'lb'),
            ('Salmon Fillet', 4, 'Wild Caught', 12.99, 'lb'),
            ('Bacon', 4, 'Oscar Mayer', 6.99, 'pack'),
            ('Turkey Breast', 4, 'Butterball', 7.49, 'lb'),
            # Beverages
            ('Orange Juice', 5, 'Tropicana', 4.99, 'bottle'),
            ('Coffee', 5, 'Starbucks', 9.99, 'bag'),
            ('Green Tea', 5, 'Bigelow', 4.49, 'box'),
            ('Sparkling Water', 5, 'LaCroix', 5.99, 'pack'),
            ('Almond Milk', 5, 'Califia', 4.99, 'carton'),
            # Bakery
            ('Whole Wheat Bread', 6, 'Dave\'s Killer', 5.49, 'loaf'),
            ('Bagels', 6, 'Thomas', 4.29, 'pack'),
            ('Croissants', 6, 'La Boulangerie', 4.99, 'pack'),
            ('Tortillas', 6, 'Mission', 3.49, 'pack'),
            ('English Muffins', 6, 'Thomas', 3.99, 'pack'),
            # Frozen Foods
            ('Ice Cream', 7, 'Ben & Jerry\'s', 5.99, 'pint'),
            ('Frozen Pizza', 7, 'DiGiorno', 7.49, 'each'),
            ('Frozen Vegetables', 7, 'Birds Eye', 2.99, 'bag'),
            ('Frozen Berries', 7, 'Dole', 4.99, 'bag'),
            ('Fish Sticks', 7, 'Gorton\'s', 5.99, 'box'),
            # Snacks
            ('Potato Chips', 8, 'Lay\'s', 4.29, 'bag'),
            ('Pretzels', 8, 'Snyder\'s', 3.99, 'bag'),
            ('Trail Mix', 8, 'Planters', 6.99, 'container'),
            ('Granola Bars', 8, 'Nature Valley', 4.49, 'box'),
            ('Crackers', 8, 'Ritz', 3.99, 'box'),
            # Household
            ('Paper Towels', 9, 'Bounty', 12.99, 'pack'),
            ('Dish Soap', 9, 'Dawn', 3.99, 'bottle'),
            ('Laundry Detergent', 9, 'Tide', 14.99, 'bottle'),
            ('Trash Bags', 9, 'Glad', 9.99, 'box'),
            ('All-Purpose Cleaner', 9, 'Method', 4.99, 'bottle'),
            # Personal Care
            ('Shampoo', 10, 'Pantene', 6.99, 'bottle'),
            ('Toothpaste', 10, 'Colgate', 4.49, 'tube'),
            ('Body Wash', 10, 'Dove', 5.99, 'bottle'),
            ('Deodorant', 10, 'Old Spice', 6.49, 'stick'),
            ('Hand Soap', 10, 'Softsoap', 3.99, 'bottle')
        ]
        cursor.executemany('''
            INSERT INTO products (product_name, category_id, brand, unit_price, unit_measure)
            VALUES (?, ?, ?, ?, ?)
        ''', products)
        
        # Create sample user
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', ('demo_user', 'demo@example.com', hash_password('password123')))
        
        conn.commit()
        print("Sample data inserted successfully!")

if __name__ == '__main__':
    init_database()
    insert_sample_data()