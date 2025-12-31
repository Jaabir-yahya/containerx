"""
Unit tests for inventory service.

Tests inventory service in isolation with real database.
"""

import pytest
from core.services.inventory_service import verify_stock, adjust_inventory
from core.storage.db import get_db
from tests.helpers import (
    get_inventory_quantity,
    get_stock_movements,
    assert_stock_movement_count,
    assert_no_negative_stock
)

class TestInventoryService:
    """Test inventory service operations."""
    
    def test_verify_stock_sufficient(self, clean_db):
        """Test stock verification with sufficient stock."""
        assert verify_stock("MILK001", 50) == True
        assert verify_stock("MILK001", 100) == True  # Exact match
        assert verify_stock("MILK001", 1) == True
    
    def test_verify_stock_insufficient(self, clean_db):
        """Test stock verification with insufficient stock."""
        with pytest.raises(ValueError, match="Insufficient stock"):
            verify_stock("MILK001", 101)
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            verify_stock("MILK001", 200)
    
    def test_verify_stock_nonexistent(self, clean_db):
        """Test stock verification with non-existent SKU."""
        with pytest.raises(ValueError, match="not found"):
            verify_stock("NONEXISTENT", 1)
    
    def test_adjust_inventory_deduction(self, clean_db):
        """Test inventory adjustment with deduction."""
        initial_qty = get_inventory_quantity("MILK001")

        adjust_inventory("MILK001", -10, "test_deduction", None)

        final_qty = get_inventory_quantity("MILK001")
        assert final_qty == initial_qty - 10

        # Verify stock movement was created
        assert_stock_movement_count("MILK001", 1)
        movements = get_stock_movements(sku="MILK001")
        assert movements[0]["quantity_change"] == -10
        assert movements[0]["reason"] == "test_deduction"
    
    def test_adjust_inventory_addition(self, clean_db):
        """Test inventory adjustment with addition."""
        initial_qty = get_inventory_quantity("MILK001")

        adjust_inventory("MILK001", 20, "test_addition", None)

        final_qty = get_inventory_quantity("MILK001")
        assert final_qty == initial_qty + 20

        # Verify stock movement was created
        assert_stock_movement_count("MILK001", 1)
    
    def test_adjust_inventory_prevents_negative(self, clean_db):
        """Test that inventory adjustment prevents negative stock."""
        initial_qty = get_inventory_quantity("MILK001")

        with pytest.raises(ValueError, match="negative"):
            adjust_inventory("MILK001", -(initial_qty + 1), "test", None)

        # Verify stock is unchanged
        final_qty = get_inventory_quantity("MILK001")
        assert final_qty == initial_qty

        # Verify no stock movement was created
        assert_stock_movement_count("MILK001", 0)
    
    def test_adjust_inventory_creates_movement_always(self, clean_db):
        """Test that every inventory adjustment creates a stock movement."""
        initial_count = len(get_stock_movements(sku="MILK001"))

        adjust_inventory("MILK001", -5, "test1", None)
        adjust_inventory("MILK001", 10, "test2", None)
        adjust_inventory("MILK001", -3, "test3", None)

        final_count = len(get_stock_movements(sku="MILK001"))
        assert final_count == initial_count + 3
    
    def test_adjust_inventory_with_order_id(self, clean_db):
        """Test inventory adjustment with related order ID."""
        order_id = "TEST_ORDER_123"

        adjust_inventory("MILK001", -5, "sale", order_id)

        movements = get_stock_movements(sku="MILK001", order_id=order_id)
        assert len(movements) == 1
        assert movements[0]["related_order_id"] == order_id
        assert movements[0]["reason"] == "sale"
    
    def test_adjust_inventory_new_sku_positive(self, clean_db):
        """Test creating new inventory item with positive adjustment."""
        adjust_inventory("NEW_SKU", 50, "initial_stock", None)

        qty = get_inventory_quantity("NEW_SKU")
        assert qty == 50

        movements = get_stock_movements(sku="NEW_SKU")
        assert len(movements) == 1
        assert movements[0]["quantity_change"] == 50
    
    def test_adjust_inventory_new_sku_negative_fails(self, clean_db):
        """Test that negative adjustment fails for new SKU."""
        with pytest.raises(ValueError, match="non-existent"):
            adjust_inventory("NEW_SKU", -10, "test", None)
    
    def test_multiple_adjustments_maintain_consistency(self, clean_db):
        """Test that multiple adjustments maintain inventory consistency."""
        initial_qty = get_inventory_quantity("MILK001")

        adjust_inventory("MILK001", -10, "adjustment1", None)
        adjust_inventory("MILK001", 5, "adjustment2", None)
        adjust_inventory("MILK001", -20, "adjustment3", None)

        final_qty = get_inventory_quantity("MILK001")
        expected_qty = initial_qty - 10 + 5 - 20
        assert final_qty == expected_qty

        # Verify all movements were created
        movements = get_stock_movements(sku="MILK001")
        assert len(movements) == 3

        # Verify no negative stock
        assert_no_negative_stock()

