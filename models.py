from extensions import db
from datetime import datetime, timedelta
from flask_login import UserMixin   
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin,db.Model):

    ROLE = {
        'super_admin': 'super_admin',
        'buyer': 'buyer',
        'seller': 'seller',
    }


    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='buyer')  
    
    # New fields for freelancers
    is_approved = db.Column(db.Boolean, default=False)
    services_rendered = db.Column(db.Text)
    
    # Relationships
    services = db.relationship('Service', backref='seller', lazy=True)
    orders_as_buyer = db.relationship('Order', foreign_keys='Order.buyer_id', backref='buyer', lazy=True)
    orders_as_seller = db.relationship('Order', foreign_keys='Order.seller_id', backref='seller_acc', lazy=True)
    wallet = db.relationship('Wallet', backref='user', uselist=False, lazy=True)
    account_details = db.relationship('AccountDetails', backref='user', uselist=False, lazy=True)

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    base_price = db.Column(db.Numeric(10, 2))  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    packages = db.relationship('Package', backref='service', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='service', lazy=True)

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False) 
    description = db.Column(db.Text, nullable=False)
    benefits = db.Column(db.Text) 
    price = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_time_days = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    STATUS = {
        'pending': 'pending',
        'in_progress': 'in_progress',
        'completed_by_seller': 'completed_by_seller',
        'completed': 'completed',
        'cancelled': 'cancelled',
    }

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = db.relationship('Message', backref='order', lazy=True)
    review = db.relationship('Review', backref='order', uselist=False, lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00)
    pending_balance = db.Column(db.Numeric(10, 2), default=0.00) 
    transactions = db.relationship('Transaction', backref='wallet', lazy=True)

class AccountDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)

class Transaction(db.Model):
    TYPE = {
        'earning': 'earning',
        'withdrawal': 'withdrawal',
        'refund': 'refund',
    }
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='completed') 
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Withdrawal(db.Model):
    STATUS = {
        'pending': 'pending',
        'approved': 'approved',
        'rejected': 'rejected',
    }

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Review(db.Model):
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range'),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), unique=True, nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PasswordReset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False)

    def is_expired(self):
        return datetime.utcnow() > self.created_at + timedelta(minutes=5)


class EmailOTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    contact = db.Column(db.String(20))
    role = db.Column(db.String(20), default='buyer')
    services_rendered = db.Column(db.Text)
    expires_at = db.Column(db.DateTime, nullable=False)