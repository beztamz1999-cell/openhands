"""
Account Tab
Account checker interface
"""

import customtkinter as ctk
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui.main_window import MainWindow

from checkers.account import AccountCheckerSync, AccountResult


class AccountTab(ctk.CTkFrame):
    """Account checker tab"""
    
    def __init__(self, parent, main_window: "MainWindow"):
        super().__init__(parent, fg_color="transparent")
        
        self.main_window = main_window
        self.checker = AccountCheckerSync()
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create tab UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="🔑 Account Checker",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(10, 5))
        
        # Warning
        warning = ctk.CTkLabel(
            self,
            text="⚠️ Use responsibly and only on accounts you own",
            font=ctk.CTkFont(size=12),
            text_color=("orange", "orange")
        )
        warning.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Input section
        input_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray17"))
        input_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Email input
        email_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        email_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(email_frame, text="Email:", width=150, anchor="w").pack(side="left")
        
        self.email_entry = ctk.CTkEntry(email_frame, placeholder_text="email@example.com")
        self.email_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Password input
        password_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        password_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(password_frame, text="Password:", width=150, anchor="w").pack(side="left")
        
        self.password_entry = ctk.CTkEntry(
            password_frame, 
            placeholder_text="••••••••",
            show="•"
        )
        self.password_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Toggle password visibility
        self.show_password = ctk.CTkCheckBox(
            password_frame,
            text="Show",
            width=60,
            command=self._toggle_password
        )
        self.show_password.pack(side="left", padx=(10, 0))
        
        # Buttons
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.check_btn = ctk.CTkButton(
            button_frame,
            text="🔐 Check Account",
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
        
        # Results content
        scroll_frame = ctk.CTkScrollableFrame(results_frame, fg_color="transparent", height=300)
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.results_container = scroll_frame
        
        # Initial empty state
        self._show_empty_state()
    
    def _toggle_password(self) -> None:
        """Toggle password visibility"""
        if self.show_password.get():
            self.password_entry.configure(show="")
        else:
            self.password_entry.configure(show="•")
    
    def _show_empty_state(self) -> None:
        """Show empty state"""
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        empty = ctk.CTkLabel(
            self.results_container,
            text="Enter email and password to check account validity",
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
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email:
            self.main_window.set_status("Email required", "orange")
            return
        if not password:
            self.main_window.set_status("Password required", "orange")
            return
        
        # Disable button
        self.check_btn.configure(state="disabled", text="⏳ Checking...")
        self.main_window.set_status("Checking account...", "blue")
        
        # Run in thread
        thread = threading.Thread(target=self._run_check, args=(email, password))
        thread.daemon = True
        thread.start()
    
    def _run_check(self, email: str, password: str) -> None:
        """Run check in background"""
        try:
            result = self.checker.check(email, password)
            self.after(0, lambda: self._display_results(result))
        except Exception as e:
            self.after(0, lambda: self._display_error(str(e)))
    
    def _display_results(self, result: AccountResult) -> None:
        """Display results"""
        self.check_btn.configure(state="normal", text="🔐 Check Account")
        
        if result.valid:
            self.main_window.set_status("Account valid", "green")
        elif result.needs_mfa:
            self.main_window.set_status("Needs MFA", "orange")
        elif result.locked:
            self.main_window.set_status("Account locked", "red")
        else:
            self.main_window.set_status("Account invalid", "red")
        
        # Clear previous results
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        # Status indicator
        if result.valid:
            status_color = "#28a745"  # Green
            status_text = "✅ Account Valid"
        elif result.needs_mfa:
            status_color = "#ffc107"  # Yellow
            status_text = "⚠️ Requires MFA"
        elif result.locked:
            status_color = "#dc3545"  # Red
            status_text = "🔒 Account Locked"
        else:
            status_color = "#dc3545"  # Red
            status_text = "❌ Account Invalid"
        
        status_frame = ctk.CTkFrame(self.results_container, fg_color=status_color)
        status_frame.pack(fill="x", pady=(0, 15))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text=status_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        status_label.pack(pady=10)
        
        # Account info
        info_frame = ctk.CTkFrame(self.results_container, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            info_frame,
            text=f"📧 Email: {result.email}",
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w")
        
        # Status details
        if result.errors:
            ctk.CTkLabel(
                info_frame,
                text="Errors:",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("gray60", "gray40")
            ).pack(anchor="w", pady=(10, 5))
            
            for error in result.errors:
                ctk.CTkLabel(
                    info_frame,
                    text=f"  • {error}",
                    font=ctk.CTkFont(size=12)
                ).pack(anchor="w")
        
        if result.needs_mfa:
            mfa_frame = ctk.CTkFrame(self.results_container, fg_color="#fff3cd")
            mfa_label = ctk.CTkLabel(
                mfa_frame,
                text="💡 This account requires multi-factor authentication. Login via browser is needed.",
                font=ctk.CTkFont(size=11),
                text_color="#856404",
                wraplength=400
            )
            mfa_label.pack(pady=10, padx=10)
            mfa_frame.pack(fill="x", pady=(0, 10))
        
        # Update status
        status_detail = "Valid" if result.valid else "Invalid"
        if result.needs_mfa:
            status_detail += " (MFA required)"
        elif result.locked:
            status_detail += " (Locked)"
        self.results_status.configure(text=status_detail)
    
    def _display_error(self, error: str) -> None:
        """Display error"""
        self.check_btn.configure(state="normal", text="🔐 Check Account")
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
