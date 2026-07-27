"""
Settings Tab
Application settings and configuration
"""

import customtkinter as ctk
from typing import TYPE_CHECKING
import os
from pathlib import Path

if TYPE_CHECKING:
    from gui.main_window import MainWindow

from config import config


class SettingsTab(ctk.CTkFrame):
    """Settings tab"""
    
    def __init__(self, parent, main_window: "MainWindow"):
        super().__init__(parent, fg_color="transparent")
        
        self.main_window = main_window
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create tab UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="⚙️ Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(anchor="w", padx=20, pady=(10, 5))
        
        # Description
        desc = ctk.CTkLabel(
            self,
            text="Configure GoLogin API and browser settings",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        desc.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Settings container
        settings_container = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent",
            height=500
        )
        settings_container.pack(fill="both", expand=True, padx=20)
        
        # ===== GoLogin Section =====
        gologin_section = ctk.CTkFrame(settings_container, fg_color=("gray90", "gray17"))
        gologin_section.pack(fill="x", pady=(0, 15))
        
        section_title = ctk.CTkFrame(gologin_section, fg_color="transparent")
        section_title.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            section_title,
            text="🔐 GoLogin Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Token
        token_frame = ctk.CTkFrame(gologin_section, fg_color="transparent")
        token_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(token_frame, text="API Token:", width=150, anchor="w").pack(side="left")
        
        self.token_entry = ctk.CTkEntry(
            token_frame, 
            placeholder_text="Your GoLogin API token",
            show="•"
        )
        self.token_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        if config.gologin.token:
            self.token_entry.insert(0, config.gologin.token)
        
        self.token_visible = ctk.CTkCheckBox(
            token_frame,
            text="Show",
            width=60,
            command=self._toggle_token_visibility
        )
        self.token_visible.pack(side="left", padx=(10, 0))
        
        # Token help
        token_help = ctk.CTkLabel(
            gologin_section,
            text="💡 Get your token from https://app.gologin.com/ → Settings → API",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40")
        )
        token_help.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Profile ID
        profile_frame = ctk.CTkFrame(gologin_section, fg_color="transparent")
        profile_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(profile_frame, text="Profile ID (optional):", width=150, anchor="w").pack(side="left")
        
        self.profile_entry = ctk.CTkEntry(
            profile_frame, 
            placeholder_text="Use existing profile"
        )
        self.profile_entry.pack(side="left", fill="x", expand=True, padx=(10, 0))
        if config.gologin.profile_id:
            self.profile_entry.insert(0, config.gologin.profile_id)
        
        profile_help = ctk.CTkLabel(
            gologin_section,
            text="Leave empty to create a new profile automatically",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40")
        )
        profile_help.pack(anchor="w", padx=20, pady=(0, 15))
        
        # ===== Proxy Section =====
        proxy_section = ctk.CTkFrame(settings_container, fg_color=("gray90", "gray17"))
        proxy_section.pack(fill="x", pady=(0, 15))
        
        proxy_title = ctk.CTkFrame(proxy_section, fg_color="transparent")
        proxy_title.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            proxy_title,
            text="🌐 Proxy Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Enable proxy
        self.proxy_enabled = ctk.BooleanVar(value=config.proxy.enabled)
        proxy_check = ctk.CTkCheckBox(
            proxy_section,
            text="Enable Proxy",
            variable=self.proxy_enabled,
            command=self._on_proxy_toggle
        )
        proxy_check.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Proxy settings
        self.proxy_host = ctk.CTkEntry(
            proxy_section, 
            placeholder_text="proxy.example.com"
        )
        self.proxy_host.pack(fill="x", padx=20, pady=(0, 10))
        if config.proxy.host:
            self.proxy_host.insert(0, config.proxy.host)
        
        self.proxy_port = ctk.CTkEntry(
            proxy_section, 
            placeholder_text="8080"
        )
        self.proxy_port.pack(fill="x", padx=20, pady=(0, 10))
        if config.proxy.port:
            self.proxy_port.insert(0, str(config.proxy.port))
        
        proxy_auth = ctk.CTkFrame(proxy_section, fg_color="transparent")
        proxy_auth.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(proxy_auth, text="Username:", width=80, anchor="w").pack(side="left")
        
        self.proxy_user = ctk.CTkEntry(proxy_auth, width=150)
        self.proxy_user.pack(side="left", padx=(0, 20))
        if config.proxy.user:
            self.proxy_user.insert(0, config.proxy.user)
        
        ctk.CTkLabel(proxy_auth, text="Password:", width=80, anchor="w").pack(side="left")
        
        self.proxy_pass = ctk.CTkEntry(proxy_auth, width=150, show="•")
        self.proxy_pass.pack(side="left")
        if config.proxy.password:
            self.proxy_pass.insert(0, config.proxy.password)
        
        # ===== Browser Section =====
        browser_section = ctk.CTkFrame(settings_container, fg_color=("gray90", "gray17"))
        browser_section.pack(fill="x", pady=(0, 15))
        
        browser_title = ctk.CTkFrame(browser_section, fg_color="transparent")
        browser_title.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            browser_title,
            text="🖥️ Browser Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Headless mode
        self.headless = ctk.BooleanVar(value=config.browser.headless)
        headless_check = ctk.CTkCheckBox(
            browser_section,
            text="Run in headless mode (no visible browser)",
            variable=self.headless
        )
        headless_check.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Timeouts
        timeout_frame = ctk.CTkFrame(browser_section, fg_color="transparent")
        timeout_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(timeout_frame, text="Timeout (ms):", width=150, anchor="w").pack(side="left")
        
        self.timeout_entry = ctk.CTkEntry(timeout_frame, width=100)
        self.timeout_entry.insert(0, str(config.browser.timeout))
        self.timeout_entry.pack(side="left", padx=(10, 0))
        
        ctk.CTkLabel(
            timeout_frame,
            text="Page Load (ms):",
            width=120,
            anchor="w"
        ).pack(side="left", padx=(20, 0))
        
        self.page_timeout_entry = ctk.CTkEntry(timeout_frame, width=100)
        self.page_timeout_entry.insert(0, str(config.browser.page_load_timeout))
        self.page_timeout_entry.pack(side="left", padx=(10, 0))
        
        # ===== Save Button =====
        save_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        save_frame.pack(fill="x", pady=(10, 20))
        
        self.save_btn = ctk.CTkButton(
            save_frame,
            text="💾 Save Settings",
            command=self._save_settings,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.save_btn.pack(side="left", padx=(0, 10))
        
        self.reset_btn = ctk.CTkButton(
            save_frame,
            text="🔄 Reset to Default",
            command=self._reset_settings,
            height=45,
            fg_color="gray",
            hover_color=("gray70", "gray30")
        )
        self.reset_btn.pack(side="left")
        
        # Status message
        self.status_label = ctk.CTkLabel(
            save_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=(20, 0))
    
    def _toggle_token_visibility(self) -> None:
        """Toggle token visibility"""
        if self.token_visible.get():
            self.token_entry.configure(show="")
        else:
            self.token_entry.configure(show="•")
    
    def _on_proxy_toggle(self) -> None:
        """Handle proxy toggle"""
        enabled = self.proxy_enabled.get()
        self.proxy_host.configure(state="normal" if enabled else "disabled")
        self.proxy_port.configure(state="normal" if enabled else "disabled")
        self.proxy_user.configure(state="normal" if enabled else "disabled")
        self.proxy_pass.configure(state="normal" if enabled else "disabled")
    
    def _save_settings(self) -> None:
        """Save settings to .env file"""
        try:
            # Get values
            token = self.token_entry.get().strip()
            profile_id = self.profile_entry.get().strip()
            proxy_enabled = self.proxy_enabled.get()
            proxy_host = self.proxy_host.get().strip()
            proxy_port = self.proxy_port.get().strip()
            proxy_user = self.proxy_user.get().strip()
            proxy_pass = self.proxy_pass.get()
            headless = self.headless.get()
            timeout = self.timeout_entry.get().strip()
            page_timeout = self.page_timeout_entry.get().strip()
            
            # Create .env content
            env_content = f"""# GoLogin Configuration
GOLOGIN_TOKEN={token}
GOLOGIN_PROFILE_ID={profile_id}

# Proxy Configuration
PROXY_ENABLED={'true' if proxy_enabled else 'false'}
PROXY_HOST={proxy_host}
PROXY_PORT={proxy_port}
PROXY_USER={proxy_user}
PROXY_PASS={proxy_pass}

# Browser Settings
HEADLESS={'true' if headless else 'false'}
BROWSER_TIMEOUT={timeout or '30000'}
PAGE_LOAD_TIMEOUT={page_timeout or '60000'}

# Logging
LOG_LEVEL=INFO
"""
            
            # Write to .env file
            env_path = Path(__file__).parent.parent / ".env"
            env_path.write_text(env_content)
            
            # Update status
            self.status_label.configure(
                text="✅ Settings saved! Restart app to apply.",
                text_color=("green", "green")
            )
            
            # Update main window token status
            self.main_window.set_token_status(bool(token))
            
            # Schedule status clear
            self.after(3000, lambda: self.status_label.configure(text=""))
            
        except Exception as e:
            self.status_label.configure(
                text=f"❌ Error: {str(e)}",
                text_color=("red", "red")
            )
    
    def _reset_settings(self) -> None:
        """Reset settings to default"""
        self.token_entry.delete(0, "end")
        self.profile_entry.delete(0, "end")
        self.proxy_enabled.set(False)
        self.proxy_host.delete(0, "end")
        self.proxy_port.delete(0, "end")
        self.proxy_user.delete(0, "end")
        self.proxy_pass.delete(0, "end")
        self.headless.set(False)
        self.timeout_entry.delete(0, "end")
        self.timeout_entry.insert(0, "30000")
        self.page_timeout_entry.delete(0, "end")
        self.page_timeout_entry.insert(0, "60000")
        
        self.status_label.configure(
            text="Settings reset to default",
            text_color=("gray60", "gray40")
        )
