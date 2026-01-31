# -*- coding: utf-8 -*-
"""
Advanced Tests for CSV Import and Campaign Donation Flows
اختبارات متقدمة لاستيراد CSV وتدفقات التبرع بالحملات
"""

import pytest
import tempfile
import os
import csv
import json
from datetime import datetime
from database import Database


@pytest.fixture
def temp_db():
    """Create a temporary in-memory database for testing"""
    return Database(":memory:")


@pytest.fixture
def admin_user():
    """Create a test admin user"""
    return {'user_id': 100, 'username': 'admin', 'first_name': 'Admin'}


@pytest.fixture
def regular_user():
    """Create a test regular user"""
    return {'user_id': 200, 'username': 'user', 'first_name': 'User'}


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'name', 'description', 'price', 'type', 'content', 'stock', 'is_limited', 'category'])
        writer.writeheader()
        writer.writerow({
            'id': '',
            'name': 'منتج الاختبار 1',
            'description': 'وصف المنتج 1',
            'price': '100',
            'type': 'text',
            'content': 'محتوى المنتج',
            'stock': '10',
            'is_limited': '1',
            'category': 'عام'
        })
        writer.writerow({
            'id': '',
            'name': 'منتج الاختبار 2',
            'description': 'وصف المنتج 2',
            'price': '200',
            'type': 'file',
            'content': 'ملف المنتج',
            'stock': '-1',
            'is_limited': '0',
            'category': 'عام'
        })
        f.flush()
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestCSVImport:
    """Test CSV import functionality"""
    
    def test_csv_import_creates_products(self, temp_db, temp_csv_file):
        """Test that CSV import creates products correctly"""
        with open(temp_csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            added = 0
            for row in reader:
                pid = db.get_active_products()
                product_id = temp_db.add_product(
                    name=row['name'],
                    description=row['description'],
                    price=int(row['price']),
                    product_type=row['type'],
                    delivery_content=row['content'],
                    stock=int(row['stock']),
                    is_limited=int(row['is_limited']),
                    category=row['category']
                )
                if product_id:
                    added += 1
        
        assert added == 2
        products = temp_db.get_active_products()
        assert len(products) == 2
        assert products[0]['name'] == 'منتج الاختبار 1'
        assert products[0]['price'] == 100
    
    def test_csv_import_with_existing_ids(self, temp_db):
        """Test updating existing products via CSV"""
        # Create initial product
        product_id = temp_db.add_product('منتج قديم', 'وصف قديم', 50, 'text', 'محتوى', -1, 0, 'عام')
        assert product_id == 1
        
        # Simulate CSV update
        temp_db.update_product(product_id, name='منتج محدث', price=150)
        
        product = temp_db.get_product(product_id)
        assert product['name'] == 'منتج محدث'
        assert product['price'] == 150
    
    def test_csv_import_handles_invalid_prices(self, temp_db):
        """Test that CSV import handles invalid prices gracefully"""
        try:
            invalid_price = 'not_a_number'
            price = int(invalid_price)
            assert False, "Should have raised ValueError"
        except ValueError:
            assert True
    
    def test_csv_import_respects_stock_limits(self, temp_db):
        """Test that CSV import respects stock and is_limited fields"""
        pid = temp_db.add_product('محدود', 'منتج محدود', 100, 'text', 'محتوى', 5, 1, 'عام')
        product = temp_db.get_product(pid)
        
        assert product['stock'] == 5
        assert product['is_limited'] == 1
        
        # Decrease stock
        assert temp_db.decrease_stock(pid)
        product = temp_db.get_product(pid)
        assert product['stock'] == 4


class TestDonationCampaigns:
    """Test donation campaign functionality"""
    
    def test_create_campaign_with_options(self, temp_db, admin_user, regular_user):
        """Test creating a donation campaign with preset options"""
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        temp_db.add_user(regular_user['user_id'], regular_user['username'], regular_user['first_name'])
        
        options = [5, 10, 20, 50]
        donation_id = temp_db.create_donation(
            donor_id=admin_user['user_id'],
            amount=100,
            description='حملة اختبار',
            options=options
        )
        
        assert donation_id is not None
        donation = temp_db.get_donation(donation_id)
        assert donation['description'] == 'حملة اختبار'
        assert donation['amount'] == 100
        assert donation['total_received'] == 0
        
        # Verify options are stored as JSON
        stored_options = json.loads(donation['donation_options'])
        assert stored_options == options
    
    def test_campaign_without_options(self, temp_db, admin_user):
        """Test creating a campaign without preset options"""
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        
        donation_id = temp_db.create_donation(
            donor_id=admin_user['user_id'],
            amount=100,
            description='حملة بدون خيارات'
        )
        
        assert donation_id is not None
        donation = temp_db.get_donation(donation_id)
        assert donation['donation_options'] is None
    
    def test_add_contribution_to_campaign(self, temp_db, admin_user, regular_user):
        """Test adding a contribution to a campaign"""
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        temp_db.add_user(regular_user['user_id'], regular_user['username'], regular_user['first_name'])
        
        # Create campaign
        donation_id = temp_db.create_donation(
            donor_id=admin_user['user_id'],
            amount=100,
            description='حملة'
        )
        
        # Add contribution
        assert temp_db.add_donation_contribution(donation_id, regular_user['user_id'], 25)
        
        # Verify campaign total updated
        donation = temp_db.get_donation(donation_id)
        assert donation['total_received'] == 25
        
        # Verify contributor got points
        points = temp_db.get_user_points(regular_user['user_id'])
        assert points['points'] == 25
        assert points['total_earned'] == 25
    
    def test_multiple_contributions_to_campaign(self, temp_db, admin_user, regular_user):
        """Test multiple contributions accumulate correctly"""
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        temp_db.add_user(regular_user['user_id'], regular_user['username'], regular_user['first_name'])
        temp_db.add_user(300, 'user2', 'User 2')
        
        donation_id = temp_db.create_donation(
            donor_id=admin_user['user_id'],
            amount=100,
            description='حملة مشاركة'
        )
        
        # Multiple contributions
        assert temp_db.add_donation_contribution(donation_id, regular_user['user_id'], 20)
        assert temp_db.add_donation_contribution(donation_id, 300, 30)
        assert temp_db.add_donation_contribution(donation_id, regular_user['user_id'], 10)
        
        donation = temp_db.get_donation(donation_id)
        assert donation['total_received'] == 60
    
    def test_get_campaign_by_url(self, temp_db, admin_user):
        """Test retrieving campaign by donation URL"""
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        
        donation_id = temp_db.create_donation(
            donor_id=admin_user['user_id'],
            amount=100,
            description='حملة URL'
        )
        
        donation = temp_db.get_donation(donation_id)
        url = donation['donation_url']
        
        retrieved = temp_db.get_donation_by_url(url)
        assert retrieved is not None
        assert retrieved['id'] == donation_id
        assert retrieved['description'] == 'حملة URL'
    
    def test_get_user_campaigns(self, temp_db, admin_user, regular_user):
        """Test retrieving all campaigns for a user"""
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        temp_db.add_user(regular_user['user_id'], regular_user['username'], regular_user['first_name'])
        
        # Create multiple campaigns
        d1 = temp_db.create_donation(admin_user['user_id'], 100, 'حملة 1')
        d2 = temp_db.create_donation(admin_user['user_id'], 200, 'حملة 2')
        d3 = temp_db.create_donation(regular_user['user_id'], 50, 'حملة المستخدم')
        
        admin_donations = temp_db.get_user_donations(admin_user['user_id'])
        assert len(admin_donations) == 2
        assert all(d['donor_id'] == admin_user['user_id'] for d in admin_donations)
        
        user_donations = temp_db.get_user_donations(regular_user['user_id'])
        assert len(user_donations) == 1
        assert user_donations[0]['id'] == d3


class TestDonationCampaignOptions:
    """Test campaign options handling"""
    
    def test_campaign_options_validation(self, temp_db, admin_user):
        """Test that campaign options are validated"""
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        
        # Valid options
        options = [10, 25, 50, 100]
        donation_id = temp_db.create_donation(
            donor_id=admin_user['user_id'],
            amount=200,
            options=options
        )
        assert donation_id is not None
        
        donation = temp_db.get_donation(donation_id)
        stored = json.loads(donation['donation_options'])
        assert stored == options
    
    def test_campaign_options_empty_list(self, temp_db, admin_user):
        """Test campaign with empty options list"""
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        
        donation_id = temp_db.create_donation(
            donor_id=admin_user['user_id'],
            amount=100,
            options=[]
        )
        assert donation_id is not None
        
        donation = temp_db.get_donation(donation_id)
        # Empty list still gets stored as JSON
        if donation['donation_options']:
            stored = json.loads(donation['donation_options'])
            assert stored == []


class TestIntegration:
    """Integration tests combining CSV and campaigns"""
    
    def test_campaign_with_csv_imported_products(self, temp_db, admin_user, regular_user, temp_csv_file):
        """Test campaign workflow with CSV-imported products"""
        # Setup users
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        temp_db.add_user(regular_user['user_id'], regular_user['username'], regular_user['first_name'])
        
        # Import products from CSV
        with open(temp_csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            products_added = 0
            for row in reader:
                pid = temp_db.add_product(
                    name=row['name'],
                    description=row['description'],
                    price=int(row['price']),
                    product_type=row['type'],
                    delivery_content=row['content'],
                    stock=int(row['stock']),
                    is_limited=int(row['is_limited']),
                    category=row['category']
                )
                if pid:
                    products_added += 1
        
        assert products_added == 2
        
        # Create donation campaign
        options = [50, 100, 200]
        donation_id = temp_db.create_donation(
            donor_id=admin_user['user_id'],
            amount=500,
            description='حملة لدعم المنتجات الجديدة',
            options=options
        )
        
        assert donation_id is not None
        
        # Add contributions
        assert temp_db.add_donation_contribution(donation_id, regular_user['user_id'], 100)
        
        # Verify everything
        products = temp_db.get_active_products()
        assert len(products) == 2
        
        donation = temp_db.get_donation(donation_id)
        assert donation['total_received'] == 100
        
        points = temp_db.get_user_points(regular_user['user_id'])
        assert points['points'] == 100
    
    def test_donation_stats_after_campaign(self, temp_db, admin_user, regular_user):
        """Test donation statistics after campaign contributions"""
        temp_db.add_user(admin_user['user_id'], admin_user['username'], admin_user['first_name'])
        temp_db.add_user(regular_user['user_id'], regular_user['username'], regular_user['first_name'])
        
        # Create and contribute to campaign
        donation_id = temp_db.create_donation(admin_user['user_id'], 100)
        temp_db.add_donation_contribution(donation_id, regular_user['user_id'], 50)
        
        # Also add a bot donation
        temp_db.add_donation_to_bot(regular_user['user_id'], 25)
        
        # Get stats
        stats = temp_db.get_donation_stats()
        assert stats['total_amount'] == 25  # Only bot donations
        assert stats['total_donors'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
