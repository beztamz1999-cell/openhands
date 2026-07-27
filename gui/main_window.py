"""
Main Window
Main application window with tabbed interface
"""

import customtkinter as ctk
from typing import Callable, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config


class MainWindow(ctk.CTk):
    """
    Main Application Window
    Modern UI with tabbed interface for different checkers
    """
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("REI Checker - GoLogin Browser Automation")
        self.geometry("1000x700")
        
        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Create UI elements
        self._create_sidebar()
        self._create_content_area()
        
        # Tab frames
        self.tabs = {}
        self.current_tab = None
        
        # Initialize tabs
        self._init_tabs()
    
    def _create_sidebar(self) -> None:
        """Create sidebar navigation"""
        # Sidebar frame
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)
        
        # Logo/Title
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.grid(row=0, padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            title_frame,
            text="🛒 REI Checker",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack()
        
        ctk.CTkLabel(
            title_frame,
            text="GoLogin Automation",
            font=ctk.CTkFont(size=12),
            text_color=("gray70", "gray30")
        ).pack()
        
        # Navigation buttons
        nav_buttons = [
            ("🔍", "Product", "product"),
            ("🔑", "Account", "account"),
            ("💰", "Price", "price"),
            ("📍", "Inventory", "inventory"),
            ("⚙️", "Settings", "settings"),
        ]
        
        self.nav_buttons = {}
        for i, (icon, text, tab_id) in enumerate(nav_buttons):
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}  {text}",
                command=lambda t=tab_id: self.show_tab(t),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                height=45,
                corner_radius=0
            )
            btn.grid(row=1+i, column=0, sticky="ew", padx=10, pady=2)
            self.nav_buttons[tab_id] = btn
        
        # Status indicator
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=7, padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="● Ready",
            font=ctk.CTkFont(size=11),
            text_color=("green", "green")
        )
        self.status_label.pack()
        
        # Token status
        self.token_status = ctk.CTkLabel(
            self.status_frame,
            text="Token: Not Set" if not config.gologin.token else "Token: ✓ Set",
            font=ctk.CTkFont(size=10),
            text_color=("orange", "orange") if not config.gologin.token else ("green", "green")
        )
        self.token_status.pack()
    
    def _create_content_area(self) -> None:
        """Create main content area"""
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Container for tab content
        self.tab_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.tab_container.grid(row=0, column=0, sticky="nsew")
        self.tab_container.grid_rowconfigure(0, weight=1)
        self.tab_container.grid_columnconfigure(0, weight=1)
    
    def _init_tabs(self) -> None:
        """Initialize all tab contents"""
        from gui.product_tab import ProductTab
        from gui.account_tab import AccountTab
        from gui.price_tab import PriceTab
        from gui.inventory_tab import InventoryTab
        from gui.settings_tab import SettingsTab
        
        # Create tab instances
        self.tabs["product"] = ProductTab(self.tab_container, self)
        self.tabs["account"] = AccountTab(self.tab_container, self)
        self.tabs["price"] = PriceTab(self.tab_container, self)
        self.tabs["inventory"] = InventoryTab(self.tab_container, self)
        self.tabs["settings"] = SettingsTab(self.tab_container, self)
        
        # Hide all tabs initially
        for tab in self.tabs.values():
            tab.grid_remove()
        
        # Show product tab by default
        self.show_tab("product")
    
    def show_tab(self, tab_id: str) -> None:
        """Show specified tab"""
        # Hide current tab
        if self.current_tab and self.current_tab in self.tabs:
            self.tabs[self.current_tab].grid_remove()
        
        # Update nav buttons
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(fg_color=("gray80", "gray20"))
            else:
                btn.configure(fg_color="transparent")
        
        # Show new tab
        if tab_id in self.tabs:
            self.tabs[tab_id].grid()
            self.current_tab = tab_id
    
    def set_status(self, text: str, color: str = "green") -> None:
        """Update status label"""
        self.status_label.configure(text=f"● {text}", text_color=(color, color))
        self.update_idletasks()
    
    def set_token_status(self, is_set: bool) -> None:
        """Update token status"""
        if is_set:
            self.token_status.configure(text="Token: ✓ Set", text_color=("green", "green"))
        else:
            self.token_status.configure(text="Token: Not Set", text_color=("orange", "orange"))
    
    def run(self) -> None:
        """Start the application"""
        self.mainloop()
