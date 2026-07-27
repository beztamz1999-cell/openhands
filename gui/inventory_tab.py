"""
Inventory Tab
Store inventory checker interface
"""

import customtkinter as ctk
import threading
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from gui.main_window import MainWindow

from checkers.inventory import InventoryCheckerSync, InventoryResult, StoreInfo


class InventoryTab(ctk.CTkFrame):
    """Inventory checker tab"""
    
    def __init__(self, parent, main_window: "MainWindow"):
        super().__init__(parent, fg_color="transparent")
        
        self.main_window = main_window
        self.checker = InventoryCheckerSync()
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create tab UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="📍 Store Inventory Checker",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(10, 5))
        
        # Description
        desc = ctk.CTkLabel(
            self,
            text="Check in-store inventory and find nearby REI stores",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        desc.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Input section
        input_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray17"))
        input_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # SKU input
        sku_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        sku_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(sku_frame, text="Product SKU or URL:", width=150, anchor="w").pack(side="left")
        
        self.sku_entry = ctk.CTkEntry(sku_frame, placeholder_text="e.g., 12345 or https://...")
        self.sku_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Zip code
        zip_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        zip_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(zip_frame, text="Zip Code (optional):", width=150, anchor="w").pack(side="left")
        
        self.zip_entry = ctk.CTkEntry(zip_frame, placeholder_text="e.g., 90210", width=150)
        self.zip_entry.pack(side="left", padx=(10, 20))
        
        ctk.CTkLabel(zip_frame, text="Radius (miles):", width=100, anchor="w").pack(side="left")
        
        self.radius_entry = ctk.CTkEntry(zip_frame, placeholder_text="50", width=80)
        self.radius_entry.insert(0, "50")
        self.radius_entry.pack(side="left")
        
        # Buttons
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.check_btn = ctk.CTkButton(
            button_frame,
            text="📍 Check Inventory",
            command=self._on_check,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.check_btn.pack(side="left", padx=(0, 10))
        
        self.find_stores_btn = ctk.CTkButton(
            button_frame,
            text="🏪 Find Stores",
            command=self._on_find_stores,
            height=40,
            fg_color="gray",
            hover_color=("gray70", "gray30")
        )
        self.find_stores_btn.pack(side="left", padx=(0, 10))
        
        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="Clear",
            command=self._clear_results,
            height=40,
            fg_color="gray",
            hover_color=("gray70", "gray30")
        )
        self.clear_btn.pack(side="left")
        
        # Results section
        results_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray17"))
        results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Results header
        results_header = ctk.CTkFrame(results_frame, fg_color="transparent")
        results_header.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            results_header,
            text="📋 Results",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        self.results_status = ctk.CTkLabel(
            results_header,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        self.results_status.pack(side="right")
        
        # Results content
        scroll_frame = ctk.CTkScrollableFrame(results_frame, fg_color="transparent", height=350)
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.results_container = scroll_frame
        
        self._show_empty_state()
    
    def _show_empty_state(self) -> None:
        """Show empty state"""
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        empty = ctk.CTkLabel(
            self.results_container,
            text="Enter a SKU and zip code to check store inventory",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray40")
        )
        empty.pack(pady=50)
    
    def _clear_results(self) -> None:
        """Clear results"""
        self._show_empty_state()
        self.results_status.configure(text="")
    
    def _on_check(self) -> None:
        """Handle check button"""
        sku = self.sku_entry.get().strip()
        if not sku:
            self.main_window.set_status("SKU required", "orange")
            return
        
        zip_code = self.zip_entry.get().strip() or None
        radius = int(self.radius_entry.get() or "50")
        
        self.check_btn.configure(state="disabled", text="⏳ Checking...")
        self.main_window.set_status("Checking inventory...", "blue")
        
        thread = threading.Thread(
            target=self._run_check, 
            args=(sku, zip_code, radius)
        )
        thread.daemon = True
        thread.start()
    
    def _run_check(self, sku: str, zip_code: str | None, radius: int) -> None:
        """Run check in background"""
        try:
            result = self.checker.check(sku, zip_code)
            self.after(0, lambda: self._display_results(result))
        except Exception as e:
            self.after(0, lambda: self._display_error(str(e)))
    
    def _on_find_stores(self) -> None:
        """Handle find stores button"""
        zip_code = self.zip_entry.get().strip()
        if not zip_code:
            self.main_window.set_status("Zip code required", "orange")
            return
        
        radius = int(self.radius_entry.get() or "50")
        
        self.find_stores_btn.configure(state="disabled", text="⏳ Searching...")
        self.main_window.set_status("Finding stores...", "blue")
        
        thread = threading.Thread(
            target=self._run_find_stores, 
            args=(zip_code, radius)
        )
        thread.daemon = True
        thread.start()
    
    def _run_find_stores(self, zip_code: str, radius: int) -> None:
        """Find stores in background"""
        try:
            stores = self.checker.find_stores(zip_code, radius)
            self.after(0, lambda: self._display_stores(stores, zip_code))
        except Exception as e:
            self.after(0, lambda: self._display_error(str(e)))
    
    def _display_results(self, result: InventoryResult) -> None:
        """Display inventory results"""
        self.check_btn.configure(state="normal", text="📍 Check Inventory")
        self.main_window.set_status("Check complete", "green")
        
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        if result.error:
            self._display_error(result.error)
            return
        
        # Online status
        online_frame = ctk.CTkFrame(self.results_container, fg_color="transparent")
        online_frame.pack(fill="x", pady=(0, 15))
        
        online_status = "✅ Online" if result.online else "❌ Out of Stock Online"
        online_color = "green" if result.online else "red"
        
        online_label = ctk.CTkLabel(
            online_frame,
            text=f"🌐 {online_status}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=(online_color, online_color)
        )
        online_label.pack(side="left")
        
        pickup_status = "✅" if result.pickup_available else "❌"
        pickup_label = ctk.CTkLabel(
            online_frame,
            text=f"In-Store Pickup: {pickup_status}",
            font=ctk.CTkFont(size=12)
        )
        pickup_label.pack(side="right")
        
        # Product info
        if result.name:
            ctk.CTkLabel(
                self.results_container,
                text=f"📦 {result.name}",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor="w", pady=(0, 5))
        
        if result.sku:
            ctk.CTkLabel(
                self.results_container,
                text=f"SKU: {result.sku}",
                font=ctk.CTkFont(size=12),
                text_color=("gray60", "gray40")
            ).pack(anchor="w", pady=(0, 15))
        
        # Store inventory
        if result.stores:
            ctk.CTkLabel(
                self.results_container,
                text="🏪 Nearby Stores:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor="w", pady=(10, 10))
            
            for store in result.stores:
                store_frame = ctk.CTkFrame(
                    self.results_container, 
                    fg_color=("gray80", "gray25")
                )
                store_frame.pack(fill="x", pady=(0, 8))
                
                # Store name and stock
                stock_emoji = "🟢" if store.stock == "In Stock" else "🟡" if store.stock == "Limited Stock" else "🔴"
                
                header_frame = ctk.CTkFrame(store_frame, fg_color="transparent")
                header_frame.pack(fill="x", padx=10, pady=(10, 5))
                
                ctk.CTkLabel(
                    header_frame,
                    text=f"{store.name}",
                    font=ctk.CTkFont(size=13, weight="bold")
                ).pack(side="left")
                
                stock_label = ctk.CTkLabel(
                    header_frame,
                    text=f"{stock_emoji} {store.stock}",
                    font=ctk.CTkFont(size=12)
                )
                stock_label.pack(side="right")
                
                # Details
                details = []
                if store.distance:
                    details.append(f"📏 {store.distance}")
                if store.stock_count:
                    details.append(f"📦 {store.stock_count} available")
                if store.sizes:
                    details.append(f"📏 Sizes: {', '.join(store.sizes[:5])}{'...' if len(store.sizes) > 5 else ''}")
                
                if details:
                    ctk.CTkLabel(
                        store_frame,
                        text=" | ".join(details),
                        font=ctk.CTkFont(size=11),
                        text_color=("gray60", "gray40")
                    ).pack(anchor="w", padx=10, pady=(0, 10))
        else:
            no_stores = ctk.CTkLabel(
                self.results_container,
                text="No store inventory data available",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray40")
            )
            no_stores.pack(pady=20)
        
        # Status
        in_stock_count = sum(1 for s in result.stores if s.stock == "In Stock")
        self.results_status.configure(
            text=f"{in_stock_count}/{len(result.stores)} stores with stock" if result.stores else ""
        )
    
    def _display_stores(self, stores: List[dict], zip_code: str) -> None:
        """Display store list"""
        self.find_stores_btn.configure(state="normal", text="🏪 Find Stores")
        self.main_window.set_status("Stores found", "green")
        
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        if not stores:
            no_stores = ctk.CTkLabel(
                self.results_container,
                text=f"No REI stores found near {zip_code}",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray40")
            )
            no_stores.pack(pady=50)
            return
        
        ctk.CTkLabel(
            self.results_container,
            text=f"🏪 REI Stores near {zip_code}:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 15))
        
        for store in stores:
            store_frame = ctk.CTkFrame(
                self.results_container, 
                fg_color=("gray80", "gray25")
            )
            store_frame.pack(fill="x", pady=(0, 8))
            
            header_frame = ctk.CTkFrame(store_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=(10, 5))
            
            ctk.CTkLabel(
                header_frame,
                text=f"📍 {store.get('name', 'Unknown Store')}",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w")
            
            if store.get("distance"):
                ctk.CTkLabel(
                    header_frame,
                    text=f"📏 {store.get('distance')}",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray60", "gray40")
                ).pack(side="right")
            
            details = []
            if store.get("address"):
                details.append(f"📮 {store.get('address')}")
            if store.get("phone"):
                details.append(f"📞 {store.get('phone')}")
            if store.get("hours"):
                details.append(f"🕐 {store.get('hours')}")
            
            if details:
                details_text = "\n".join(details)
                ctk.CTkLabel(
                    store_frame,
                    text=details_text,
                    font=ctk.CTkFont(size=11),
                    text_color=("gray60", "gray40"),
                    justify="left"
                ).pack(anchor="w", padx=10, pady=(0, 10))
        
        self.results_status.configure(text=f"Found {len(stores)} stores")
    
    def _display_error(self, error: str) -> None:
        """Display error"""
        self.check_btn.configure(state="normal", text="📍 Check Inventory")
        self.find_stores_btn.configure(state="normal", text="🏪 Find Stores")
        self.main_window.set_status("Error", "red")
        
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        error_frame = ctk.CTkFrame(self.results_container, fg_color="#ff6b6b")
        error_label = ctk.CTkLabel(
            error_frame,
            text=f"❌ Error: {error}",
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        error_label.pack(pady=10, padx=10)
        error_frame.pack(fill="x", pady=10)
