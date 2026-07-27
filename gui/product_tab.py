"""
Product Tab
Product availability checker interface
"""

import customtkinter as ctk
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui.main_window import MainWindow

from checkers.product import ProductCheckerSync, ProductResult


class ProductTab(ctk.CTkFrame):
    """Product availability checker tab"""
    
    def __init__(self, parent, main_window: "MainWindow"):
        super().__init__(parent, fg_color="transparent")
        
        self.main_window = main_window
        self.checker = ProductCheckerSync()
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create tab UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="🔍 Product Availability Checker",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(10, 5))
        
        # Description
        desc = ctk.CTkLabel(
            self,
            text="Check if products are available on REI.com with specific size/color options",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        desc.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Input section
        input_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray17"))
        input_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # SKU input
        sku_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        sku_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(sku_frame, text="Product SKU or URL:", width=150, anchor="w").pack(side="left")
        
        self.sku_entry = ctk.CTkEntry(sku_frame, placeholder_text="e.g., 12345 or https://...")
        self.sku_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Size and Color
        options_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(options_frame, text="Size (optional):", width=150, anchor="w").pack(side="left")
        
        self.size_entry = ctk.CTkEntry(options_frame, placeholder_text="e.g., M, L, 10", width=150)
        self.size_entry.pack(side="left", padx=(10, 30))
        
        ctk.CTkLabel(options_frame, text="Color (optional):", width=150, anchor="w").pack(side="left")
        
        self.color_entry = ctk.CTkEntry(options_frame, placeholder_text="e.g., Blue, Black", width=150)
        self.color_entry.pack(side="left", padx=(10, 0))
        
        # Check button
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.check_btn = ctk.CTkButton(
            button_frame,
            text="🔍 Check Availability",
            command=self._on_check,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.check_btn.pack(side="left", padx=(0, 10))
        
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
        
        # Results content (scrollable)
        scroll_frame = ctk.CTkScrollableFrame(results_frame, fg_color="transparent", height=300)
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.results_container = scroll_frame
        
        # Initial empty state
        self._show_empty_state()
    
    def _show_empty_state(self) -> None:
        """Show empty state message"""
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        empty = ctk.CTkLabel(
            self.results_container,
            text="Enter a SKU and click 'Check Availability' to see results",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray40")
        )
        empty.pack(pady=50)
    
    def _clear_results(self) -> None:
        """Clear results"""
        self._show_empty_state()
        self.results_status.configure(text="")
    
    def _on_check(self) -> None:
        """Handle check button click"""
        sku = self.sku_entry.get().strip()
        if not sku:
            self.main_window.set_status("SKU required", "orange")
            return
        
        size = self.size_entry.get().strip() or None
        color = self.color_entry.get().strip() or None
        
        # Disable button during check
        self.check_btn.configure(state="disabled", text="⏳ Checking...")
        self.main_window.set_status("Checking product...", "blue")
        
        # Run in thread
        thread = threading.Thread(target=self._run_check, args=(sku, size, color))
        thread.daemon = True
        thread.start()
    
    def _run_check(self, sku: str, size: str | None, color: str | None) -> None:
        """Run check in background thread"""
        try:
            result = self.checker.check(sku, size, color)
            self.after(0, lambda: self._display_results(result))
        except Exception as e:
            self.after(0, lambda: self._display_error(str(e)))
    
    def _display_results(self, result: ProductResult) -> None:
        """Display check results"""
        # Re-enable button
        self.check_btn.configure(state="normal", text="🔍 Check Availability")
        self.main_window.set_status("Check complete", "green")
        
        # Clear previous results
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        if result.error:
            self._display_error(result.error)
            return
        
        # Status indicator
        status_color = "green" if result.available else "red"
        status_text = "✅ Available" if result.available else "❌ Not Available"
        
        status_frame = ctk.CTkFrame(self.results_container, fg_color=status_color)
        status_frame.pack(fill="x", pady=(0, 15))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text=status_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        status_label.pack(pady=10)
        
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
        
        if result.price:
            price_text = f"💵 Price: ${result.price:.2f}"
            if result.on_sale:
                price_text += f" (Sale! Was ${result.original_price:.2f}, -{result.discount_percent}%)"
            ctk.CTkLabel(
                info_frame,
                text=price_text,
                font=ctk.CTkFont(size=13)
            ).pack(anchor="w")
        
        # Sizes
        if result.sizes:
            ctk.CTkLabel(
                info_frame,
                text="📏 Sizes:",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w", pady=(10, 5))
            
            sizes_text = ", ".join(
                f"{s.size} {'✅' if s.available else '❌'}"
                for s in result.sizes
            )
            ctk.CTkLabel(
                info_frame,
                text=sizes_text,
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w")
        
        # Colors
        if result.colors:
            ctk.CTkLabel(
                info_frame,
                text="🎨 Colors:",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w", pady=(10, 5))
            
            colors_text = ", ".join(
                f"{c.color}{' (selected)' if c.selected else ''}"
                for c in result.colors
            )
            ctk.CTkLabel(
                info_frame,
                text=colors_text,
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w")
        
        # Rating
        if result.rating:
            stars = "★" * int(result.rating) + "☆" * (5 - int(result.rating))
            ctk.CTkLabel(
                info_frame,
                text=f"⭐ Rating: {result.rating}/5 {stars} ({result.reviews or '?'} reviews)",
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", pady=(10, 0))
        
        # Update status
        available_count = sum(1 for s in result.sizes if s.available) if result.sizes else 0
        self.results_status.configure(
            text=f"{available_count}/{len(result.sizes)} sizes available" if result.sizes else ""
        )
    
    def _display_error(self, error: str) -> None:
        """Display error message"""
        self.check_btn.configure(state="normal", text="🔍 Check Availability")
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
