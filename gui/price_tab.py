"""
Price Tab
Price tracking interface
"""

import customtkinter as ctk
import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gui.main_window import MainWindow

from checkers.price import PriceTrackerSync, PriceResult


class PriceTab(ctk.CTkFrame):
    """Price tracker tab"""
    
    def __init__(self, parent, main_window: "MainWindow"):
        super().__init__(parent, fg_color="transparent")
        
        self.main_window = main_window
        self.tracker = PriceTrackerSync()
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create tab UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="💰 Price Tracker",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(10, 5))
        
        # Description
        desc = ctk.CTkLabel(
            self,
            text="Track product prices over time and get alerts on price drops",
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
        
        # Options
        options_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.save_history_var = ctk.BooleanVar(value=True)
        save_check = ctk.CTkCheckBox(
            options_frame,
            text="Save to price history",
            variable=self.save_history_var
        )
        save_check.pack(side="left", padx=(0, 20))
        
        self.alert_var = ctk.BooleanVar(value=False)
        alert_check = ctk.CTkCheckBox(
            options_frame,
            text="Alert on price drop",
            variable=self.alert_var
        )
        alert_check.pack(side="left")
        
        # Buttons
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.track_btn = ctk.CTkButton(
            button_frame,
            text="💰 Track Price",
            command=self._on_track,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.track_btn.pack(side="left", padx=(0, 10))
        
        self.history_btn = ctk.CTkButton(
            button_frame,
            text="📜 View History",
            command=self._show_history,
            height=40,
            fg_color="gray",
            hover_color=("gray70", "gray30")
        )
        self.history_btn.pack(side="left", padx=(0, 10))
        
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
            text="📋 Current Price",
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
        scroll_frame = ctk.CTkScrollableFrame(results_frame, fg_color="transparent", height=300)
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.results_container = scroll_frame
        
        self._show_empty_state()
    
    def _show_empty_state(self) -> None:
        """Show empty state"""
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        empty = ctk.CTkLabel(
            self.results_container,
            text="Enter a SKU and click 'Track Price' to see current and historical prices",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray40")
        )
        empty.pack(pady=50)
    
    def _clear_results(self) -> None:
        """Clear results"""
        self._show_empty_state()
        self.results_status.configure(text="")
    
    def _on_track(self) -> None:
        """Handle track button click"""
        sku = self.sku_entry.get().strip()
        if not sku:
            self.main_window.set_status("SKU required", "orange")
            return
        
        save_history = self.save_history_var.get()
        alert_on_drop = self.alert_var.get()
        
        self.track_btn.configure(state="disabled", text="⏳ Tracking...")
        self.main_window.set_status("Tracking price...", "blue")
        
        thread = threading.Thread(
            target=self._run_track, 
            args=(sku, save_history, alert_on_drop)
        )
        thread.daemon = True
        thread.start()
    
    def _run_track(self, sku: str, save_history: bool, alert_on_drop: bool) -> None:
        """Run tracking in background"""
        try:
            result = self.tracker.track(sku, save_history)
            self.after(0, lambda: self._display_results(result, alert_on_drop))
        except Exception as e:
            self.after(0, lambda: self._display_error(str(e)))
    
    def _display_results(self, result: PriceResult, show_alert: bool = False) -> None:
        """Display tracking results"""
        self.track_btn.configure(state="normal", text="💰 Track Price")
        self.main_window.set_status("Tracking complete", "green")
        
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        if result.error:
            self._display_error(result.error)
            return
        
        # Price display
        if result.on_sale:
            price_frame = ctk.CTkFrame(self.results_container, fg_color="#28a745")
            price_text = f"SALE! ${result.price:.2f}"
            if result.original_price:
                price_text += f" (Was ${result.original_price:.2f}, -{result.discount_percent}%)"
        else:
            price_frame = ctk.CTkFrame(self.results_container, fg_color=("gray80", "gray30"))
            price_text = f"${result.price:.2f}" if result.price else "Price not found"
        
        price_label = ctk.CTkLabel(
            price_frame,
            text=price_text,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white" if result.on_sale else None
        )
        price_label.pack(pady=10)
        price_frame.pack(fill="x", pady=(0, 15))
        
        # Alert on price drop
        if result.alert and show_alert:
            alert_frame = ctk.CTkFrame(self.results_container, fg_color="#d4edda")
            alert_label = ctk.CTkLabel(
                alert_frame,
                text=result.alert,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#155724"
            )
            alert_label.pack(pady=10, padx=10)
            alert_frame.pack(fill="x", pady=(0, 15))
        
        # Product info
        info_frame = ctk.CTkFrame(self.results_container, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 15))
        
        if result.name:
            ctk.CTkLabel(
                info_frame,
                text=f"📦 {result.name}",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor="w")
        
        if result.sku:
            ctk.CTkLabel(
                info_frame,
                text=f"SKU: {result.sku}",
                font=ctk.CTkFont(size=12),
                text_color=("gray60", "gray40")
            ).pack(anchor="w")
        
        # Price history
        if result.history:
            history_frame = ctk.CTkFrame(self.results_container, fg_color="transparent")
            history_frame.pack(fill="x", pady=(10, 0))
            
            ctk.CTkLabel(
                history_frame,
                text="📈 Price History:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor="w", pady=(0, 10))
            
            history_info = ctk.CTkFrame(history_frame, fg_color=("gray80", "gray25"))
            history_info.pack(fill="x")
            
            lowest = result.history.get("lowest_price", {})
            highest = result.history.get("highest_price", {})
            
            lowest_price = lowest.get("price") if lowest else None
            highest_price = highest.get("price") if highest else None
            price_changes = result.history.get("price_changes", 0)
            last_checked = result.history.get("last_checked", "Never")
            
            ctk.CTkLabel(
                history_info,
                text=f"  💚 Lowest: ${lowest_price:.2f}" if lowest_price else "  💚 Lowest: N/A",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                history_info,
                text=f"  💔 Highest: ${highest_price:.2f}" if highest_price else "  💔 Highest: N/A",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                history_info,
                text=f"  📊 Price changes: {price_changes}",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                history_info,
                text=f"  🕐 Last checked: {last_checked[:19] if last_checked else 'Never'}",
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray40")
            ).pack(anchor="w", pady=2)
        
        # Status
        history_count = len(result.history.get("prices", [])) if result.history else 0
        self.results_status.configure(text=f"History: {history_count} records")
    
    def _show_history(self) -> None:
        """Show all tracked products"""
        try:
            tracked = self.tracker.get_all()
            
            for widget in self.results_container.winfo_children():
                widget.destroy()
            
            if not tracked:
                empty = ctk.CTkLabel(
                    self.results_container,
                    text="No price history yet. Track some products first!",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray40")
                )
                empty.pack(pady=50)
                return
            
            title = ctk.CTkLabel(
                self.results_container,
                text="📜 All Tracked Products",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            title.pack(anchor="w", pady=(0, 15))
            
            for product in tracked:
                prod_frame = ctk.CTkFrame(self.results_container, fg_color=("gray80", "gray25"))
                prod_frame.pack(fill="x", pady=(0, 10))
                
                name = product.get("name", "Unknown")
                sku = product.get("sku", "")
                last_price = product.get("last_price")
                price_changes = product.get("price_changes", 0)
                
                ctk.CTkLabel(
                    prod_frame,
                    text=f"{name} ({sku})",
                    font=ctk.CTkFont(size=13, weight="bold")
                ).pack(anchor="w", padx=10, pady=(10, 5))
                
                price_text = f"Last: ${last_price:.2f}" if last_price else "Last: N/A"
                price_text += f" | Changes: {price_changes}"
                
                ctk.CTkLabel(
                    prod_frame,
                    text=price_text,
                    font=ctk.CTkFont(size=11),
                    text_color=("gray60", "gray40")
                ).pack(anchor="w", padx=10, pady=(0, 10))
            
            self.results_status.configure(text=f"Total: {len(tracked)} products")
            
        except Exception as e:
            self._display_error(str(e))
    
    def _display_error(self, error: str) -> None:
        """Display error"""
        self.track_btn.configure(state="normal", text="💰 Track Price")
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
