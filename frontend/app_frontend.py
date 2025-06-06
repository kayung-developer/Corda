# frontend/app_frontend.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import requests
from typing import Optional, Dict, Any, List
import threading  # For non-blocking API calls and UI updates

# Configuration
BACKEND_URL = "http://localhost:8000/api/v1"


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None,
                 is_form_data: bool = False) -> Any:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"{self.base_url}{endpoint}"
        try:
            kwargs = {"headers": headers, "timeout": 15}  # Increased timeout
            if params:
                kwargs["params"] = params

            if method.upper() == "GET":
                response = requests.get(url, **kwargs)
            elif method.upper() == "POST":
                if is_form_data:
                    kwargs["data"] = data
                else:
                    kwargs["json"] = data
                response = requests.post(url, **kwargs)
            elif method.upper() == "PUT":
                kwargs["json"] = data
                response = requests.put(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            if response.content:
                try:
                    return response.json()
                except json.JSONDecodeError:  # Handle non-JSON success responses if any
                    return response.text
            return None
        except requests.exceptions.HTTPError as e:
            error_detail = f"HTTP Error: {e.response.status_code}"
            try:
                error_content = e.response.json()
                error_detail = error_content.get("detail", str(e))
                if isinstance(error_detail, list):  # Handle FastAPI validation errors
                    error_detail = "; ".join([err.get("msg", "Validation error") for err in error_detail])
            except json.JSONDecodeError:
                error_detail = e.response.text if e.response.text else error_detail
            # Defer messagebox to UI thread
            return {"error": True, "status_code": e.response.status_code, "detail": error_detail}
        except requests.exceptions.RequestException as e:
            # Defer messagebox to UI thread
            return {"error": True, "status_code": None, "detail": f"Connection Error: {e}"}
        except ValueError as e:  # For unsupported method
            return {"error": True, "status_code": None, "detail": str(e)}

    def login(self, email: str, password: str) -> Dict:  # Return Dict for error handling
        response_data = self._request("POST", "/auth/login",
                                      data={"username": email, "password": password},
                                      is_form_data=True)
        if response_data and not response_data.get("error"):
            self.token = response_data.get("access_token")
            if self.token:
                return {"success": True, "token": self.token}
            return {"error": True, "detail": "Login successful but no token received."}
        return response_data if response_data else {"error": True, "detail": "Unknown login error."}

    def register(self, email: str, password: str, full_name: str) -> Optional[Dict]:
        return self._request("POST", "/auth/register",
                             data={"email": email, "password": password, "full_name": full_name})

    def get_current_user(self) -> Optional[Dict]:
        return self._request("GET", "/auth/me")

    def generate_code(self, prompt: str, language: Optional[str] = None, context: Optional[str] = None) -> Optional[
        Dict]:
        payload = {"prompt": prompt}
        if language and language != "Auto-detect":
            payload["language"] = language
        if context:
            payload["context"] = context
        return self._request("POST", "/assist/generate-code", data=payload)

    def get_plans(self) -> Optional[List[Dict]]:
        return self._request("GET", "/subscriptions/plans")

    def get_subscription_status(self) -> Optional[Dict]:
        return self._request("GET", "/subscriptions/status")

    def subscribe(self, plan_id: str, payment_token: str, gateway: str, is_yearly: bool = False) -> Optional[Dict]:
        payload = {
            "plan_id": plan_id,
            "payment_method_token": payment_token,
            "is_yearly": is_yearly
        }
        return self._request("POST", f"/payments/subscribe/{gateway}", data=payload)


class CodeAssistantApp(ctk.CTk):
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.user_info: Optional[Dict] = None

        self.load_theme()  # Load theme first
        ctk.set_appearance_mode("dark")
        # If you have a CustomTkinter JSON theme file for default_color_theme, you can use it.
        # Otherwise, 'blue', 'green', 'dark-blue' are built-in.
        ctk.set_default_color_theme("blue")

        self.title("✧ Ultimate Code Assistant ✧")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # This line caused the error, ensure self.theme.get("background_color") is valid
        self.configure(fg_color=self.theme.get("background_color"))

        self.current_frame = None
        self.status_bar_label: Optional[ctk.CTkLabel] = None
        self.create_status_bar()
        self.show_login_frame()

    def load_theme(self):
        # Initialize with comprehensive fallback defaults first
        self.theme = {
            "primary_color": "#007AFF", "primary_color_dark": "#0056B3",
            "secondary_color": "#1E1E1E", "background_color": "#121212",
            "content_frame_color": "#1A1A1A", "text_color": "#E0E0E0",
            "text_color_dark": "#B0B0B0", "button_color": "#007AFF",
            "button_hover_color": "#0056B3", "button_text_color": "#FFFFFF",
            "entry_background_color": "#2C2C2E", "entry_border_color": "#007AFF",
            "entry_text_color": "#F0F0F0", "disabled_color": "#4A4A4E",
            "accent_color": "#FF3B30", "success_color": "#34C759",
            "warning_color": "#FF9500"
        }
        self.font_cfg = {
            "family": "System", "family_mono": "Courier", "size_small": 11,
            "size_medium": 13, "size_large": 18, "size_xlarge": 24
        }
        self.corner_radius = 10
        self.padding = {"small": 5, "medium": 10, "large": 15}

        try:
            # Ensure the path to ui_theme.json is correct.
            # If app_frontend.py is in 'frontend/', and ui_theme.json is also in 'frontend/'
            theme_file_path = os.path.join(os.path.dirname(__file__), "ui_theme.json")
            with open(theme_file_path, "r") as f:
                theme_data_from_file = json.load(f)

            # Safely update defaults with values from file
            # Only update if the key exists and its value is a dictionary (for theme and font_cfg)
            if isinstance(theme_data_from_file.get("theme"), dict):
                self.theme.update(theme_data_from_file["theme"])

            if isinstance(theme_data_from_file.get("font"), dict):
                self.font_cfg.update(theme_data_from_file["font"])

            # For non-dict values, get with existing default as fallback
            self.corner_radius = theme_data_from_file.get("corner_radius", self.corner_radius)

            if isinstance(theme_data_from_file.get("padding"), dict):  # padding should also be a dict
                self.padding.update(theme_data_from_file["padding"])

        except FileNotFoundError:
            print(f"Theme file '{os.path.basename(theme_file_path)}' not found. Using default theme.")
        except json.JSONDecodeError:
            print(f"Error decoding '{os.path.basename(theme_file_path)}'. Using default theme.")
        except Exception as e:
            print(f"An unexpected error occurred while loading theme: {e}. Using default theme.")

    def _get_font(self, size_key="size_medium", weight="normal", mono=False):
        family = self.font_cfg.get("family_mono" if mono else "family", "System")
        size = self.font_cfg.get(size_key, 13)
        return (family, size, weight)

    def _apply_theme_to_widget(self, widget, widget_type="default"):
        common_kwargs = {"corner_radius": self.corner_radius}

        if isinstance(widget, ctk.CTkButton):
            fg = self.theme.get("button_color")
            hover = self.theme.get("button_hover_color")
            text_c = self.theme.get("button_text_color")
            if widget_type == "accent":
                fg = self.theme.get("accent_color")
                hover = self.theme.get("primary_color_dark")  # Or a darker accent
            elif widget_type == "outline":
                fg = "transparent"
                text_c = self.theme.get("primary_color")
                common_kwargs["border_width"] = 1
                common_kwargs["border_color"] = self.theme.get("primary_color")

            widget.configure(fg_color=fg, hover_color=hover, text_color=text_c, **common_kwargs)

        elif isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)):
            widget.configure(
                fg_color=self.theme.get("entry_background_color"),
                text_color=self.theme.get("entry_text_color"),
                border_color=self.theme.get("entry_border_color"),
                border_width=1,
                **common_kwargs
            )
            if isinstance(widget, ctk.CTkTextbox):  # Textbox specific
                widget.configure(scrollbar_button_color=self.theme.get("primary_color"),
                                 scrollbar_button_hover_color=self.theme.get("primary_color_dark"))


        elif isinstance(widget, ctk.CTkLabel):
            text_c = self.theme.get("text_color")
            if widget_type == "title":
                text_c = self.theme.get("primary_color")
            elif widget_type == "subtitle":
                text_c = self.theme.get("text_color_dark")
            widget.configure(text_color=text_c)

        elif isinstance(widget, ctk.CTkFrame):
            fg = self.theme.get("content_frame_color")
            if widget_type == "transparent" or widget_type == "auth_form":  # Make auth form bg same as window
                fg = "transparent"
            elif widget_type == "sidebar":
                fg = self.theme.get("secondary_color")

            widget.configure(fg_color=fg, **common_kwargs)

        elif isinstance(widget, ctk.CTkOptionMenu):
            widget.configure(
                fg_color=self.theme.get("entry_background_color"),
                button_color=self.theme.get("primary_color"),
                button_hover_color=self.theme.get("primary_color_dark"),
                text_color=self.theme.get("entry_text_color"),
                dropdown_fg_color=self.theme.get("entry_background_color"),
                dropdown_hover_color=self.theme.get("primary_color_dark"),
                dropdown_text_color=self.theme.get("entry_text_color"),
                **common_kwargs
            )
        elif isinstance(widget, tk.PanedWindow):  # Basic theming for PanedWindow sash
            widget.configure(
                sashrelief=tk.FLAT,
                sashwidth=6,
                bg=self.theme.get("background_color"),  # background of the paned window itself
                sashpad=0,
                showhandle=False
            )
            # Note: CTk doesn't directly style PanedWindow sash, this is best effort.
            # For a truly themed sash, a custom widget or different layout might be needed.

    def _clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = ctk.CTkFrame(self, fg_color="transparent")  # Use window bg
        self.current_frame.pack(fill="both", expand=True, padx=self.padding['large'], pady=(self.padding['large'], 0))
        return self.current_frame

    def create_status_bar(self):
        status_bar_frame = ctk.CTkFrame(self, height=25, corner_radius=0, fg_color=self.theme.get("secondary_color"))
        status_bar_frame.pack(side="bottom", fill="x")
        self.status_bar_label = ctk.CTkLabel(status_bar_frame, text="Ready", font=self._get_font("size_small"),
                                             text_color=self.theme.get("text_color_dark"))
        self.status_bar_label.pack(side="left", padx=self.padding['medium'])

    def update_status(self, message, color_key="text_color_dark"):
        if self.status_bar_label:
            self.status_bar_label.configure(text=message, text_color=self.theme.get(color_key))

    def show_login_frame(self):
        self.title("✧ Login - Ultimate Code Assistant ✧")
        frame = self._clear_frame()
        # Auth form frame to center content
        auth_form_frame = ctk.CTkFrame(frame, width=400, height=400)  # Adjust size as needed
        self._apply_theme_to_widget(auth_form_frame, "auth_form")
        auth_form_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_label = ctk.CTkLabel(auth_form_frame, text="Welcome Back!", font=self._get_font("size_xlarge", "bold"))
        self._apply_theme_to_widget(title_label, "title")
        title_label.pack(pady=(self.padding['large'] * 2, self.padding['medium']))

        subtitle_label = ctk.CTkLabel(auth_form_frame, text="Log in to access your coding superpowers.",
                                      font=self._get_font("size_medium"))
        self._apply_theme_to_widget(subtitle_label, "subtitle")
        subtitle_label.pack(pady=(0, self.padding['large']))

        email_entry = ctk.CTkEntry(auth_form_frame, width=300, font=self._get_font(), placeholder_text="Email Address")
        self._apply_theme_to_widget(email_entry)
        email_entry.pack(pady=self.padding['small'])
        email_entry.insert(0, "user@example.com")

        password_entry = ctk.CTkEntry(auth_form_frame, width=300, show="*", font=self._get_font(),
                                      placeholder_text="Password")
        self._apply_theme_to_widget(password_entry)
        password_entry.pack(pady=self.padding['small'])
        password_entry.insert(0, "string")

        self.login_button = ctk.CTkButton(auth_form_frame, text="Login", width=300, height=40,
                                          command=lambda: self.handle_login_async(email_entry.get(),
                                                                                  password_entry.get()),
                                          font=self._get_font("size_medium", "bold"))
        self._apply_theme_to_widget(self.login_button)
        self.login_button.pack(pady=(self.padding['large'], self.padding['small']))

        register_text = ctk.CTkLabel(auth_form_frame, text="Don't have an account?", font=self._get_font("size_small"))
        self._apply_theme_to_widget(register_text, "subtitle")
        register_text.pack(pady=(self.padding['medium'], 0))

        register_button = ctk.CTkButton(auth_form_frame, text="Sign Up Here",
                                        command=self.show_register_frame,
                                        font=self._get_font("size_small", "bold"),
                                        fg_color="transparent", text_color=self.theme.get("primary_color"),
                                        hover=False)  # Simpler link-like button
        register_button.pack(pady=0)

    def show_register_frame(self):
        self.title("✧ Create Account - Ultimate Code Assistant ✧")
        frame = self._clear_frame()
        auth_form_frame = ctk.CTkFrame(frame, width=400, height=450)
        self._apply_theme_to_widget(auth_form_frame, "auth_form")
        auth_form_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_label = ctk.CTkLabel(auth_form_frame, text="Create Your Account",
                                   font=self._get_font("size_xlarge", "bold"))
        self._apply_theme_to_widget(title_label, "title")
        title_label.pack(pady=(self.padding['large'] * 2, self.padding['medium']))

        name_entry = ctk.CTkEntry(auth_form_frame, width=300, font=self._get_font(), placeholder_text="Full Name")
        self._apply_theme_to_widget(name_entry)
        name_entry.pack(pady=self.padding['small'])

        email_entry = ctk.CTkEntry(auth_form_frame, width=300, font=self._get_font(), placeholder_text="Email Address")
        self._apply_theme_to_widget(email_entry)
        email_entry.pack(pady=self.padding['small'])

        password_entry = ctk.CTkEntry(auth_form_frame, width=300, show="*", font=self._get_font(),
                                      placeholder_text="Password (min 8 chars)")
        self._apply_theme_to_widget(password_entry)
        password_entry.pack(pady=self.padding['small'])

        self.register_button_form = ctk.CTkButton(auth_form_frame, text="Create Account", width=300, height=40,
                                                  command=lambda: self.handle_register_async(name_entry.get(),
                                                                                             email_entry.get(),
                                                                                             password_entry.get()),
                                                  font=self._get_font("size_medium", "bold"))
        self._apply_theme_to_widget(self.register_button_form)
        self.register_button_form.pack(pady=(self.padding['large'], self.padding['small']))

        login_text = ctk.CTkLabel(auth_form_frame, text="Already have an account?", font=self._get_font("size_small"))
        self._apply_theme_to_widget(login_text, "subtitle")
        login_text.pack(pady=(self.padding['medium'], 0))

        login_redirect_button = ctk.CTkButton(auth_form_frame, text="Log In Here", command=self.show_login_frame,
                                              font=self._get_font("size_small", "bold"),
                                              fg_color="transparent", text_color=self.theme.get("primary_color"),
                                              hover=False)
        login_redirect_button.pack(pady=0)

    def _handle_api_response(self, response_data, success_message, success_callback=None,
                             failure_message_prefix="Error"):
        if response_data and response_data.get("error"):
            detail = response_data.get('detail', 'An unknown error occurred.')
            messagebox.showerror(failure_message_prefix, str(detail))
            self.update_status(f"{failure_message_prefix}: {str(detail)[:100]}", "accent_color")
            return False
        elif not response_data:
            messagebox.showerror(failure_message_prefix, "No response from server.")
            self.update_status("Error: No response from server.", "accent_color")
            return False
        else:  # Success
            if success_message:
                messagebox.showinfo("Success", success_message)
            self.update_status(success_message, "success_color")
            if success_callback:
                success_callback(response_data)
            return True

    def _execute_api_call(self, api_call_func, args, button_to_disable, success_message, success_callback=None,
                          failure_message_prefix="Error"):
        self.update_status("Processing...", "warning_color")
        if button_to_disable:
            button_to_disable.configure(state="disabled", text="Processing...")

        def api_thread_task():
            response_data = api_call_func(*args)

            def ui_update_task():
                self._handle_api_response(response_data, success_message, success_callback, failure_message_prefix)
                if button_to_disable:
                    original_text = getattr(button_to_disable, "_original_text", "Submit")
                    button_to_disable.configure(state="normal", text=original_text)

            self.after(0, ui_update_task)  # Schedule UI update on main thread

        # Store original button text if not already stored
        if button_to_disable and not hasattr(button_to_disable, "_original_text"):
            setattr(button_to_disable, "_original_text", button_to_disable.cget("text"))

        threading.Thread(target=api_thread_task, daemon=True).start()

    def handle_login_async(self, email, password):
        if not email or not password:
            messagebox.showerror("Login Error", "Email and password cannot be empty.")
            return
        self._execute_api_call(
            self.api_client.login,
            (email, password),
            self.login_button,
            success_message=None,  # No immediate success message, handled by callback
            success_callback=self._login_success,
            failure_message_prefix="Login Error"
        )

    def _login_success(self, response_data):
        self.user_info = self.api_client.get_current_user()  # Fetch full user info
        if self.user_info and not self.user_info.get("error"):
            self.update_status(f"Logged in as {self.user_info.get('email')}", "success_color")
            self.show_main_app_frame()
        else:
            detail = self.user_info.get('detail',
                                        'Failed to fetch user details.') if self.user_info else 'Failed to fetch user details.'
            messagebox.showerror("Login Error", str(detail))
            self.api_client.token = None  # Clear token on failure

    def handle_register_async(self, name, email, password):
        if not name or not email or not password:
            messagebox.showerror("Registration Error", "All fields are required.")
            return
        if len(password) < 8:
            messagebox.showerror("Registration Error", "Password must be at least 8 characters.")
            return

        self._execute_api_call(
            self.api_client.register,
            (email, password, name),
            self.register_button_form,
            success_message="Account created successfully! Please log in.",
            success_callback=lambda rd: self.show_login_frame(),
            failure_message_prefix="Registration Error"
        )

    def show_main_app_frame(self):
        self.title(f"✧ {self.user_info.get('full_name', self.user_info.get('email'))} - Ultimate Code Assistant ✧")
        frame = self._clear_frame()

        paned_window = tk.PanedWindow(frame, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, bd=0)
        self._apply_theme_to_widget(paned_window)  # Basic theming
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left Pane (Sidebar for controls)
        left_pane = ctk.CTkFrame(paned_window, width=350)  # Fixed width for sidebar
        self._apply_theme_to_widget(left_pane, "sidebar")
        left_pane.pack_propagate(False)  # Prevent shrinking
        paned_window.add(left_pane, minsize=300, stretch="never")

        # --- Sidebar Content ---
        sidebar_content_frame = ctk.CTkScrollableFrame(left_pane, fg_color="transparent")
        sidebar_content_frame.pack(fill="both", expand=True, padx=self.padding['medium'], pady=self.padding['medium'])

        user_email_label = ctk.CTkLabel(sidebar_content_frame, text=self.user_info.get('email', 'N/A'),
                                        font=self._get_font("size_medium", "bold"))
        self._apply_theme_to_widget(user_email_label)
        user_email_label.pack(pady=(0, self.padding['small']), anchor="w")

        plan_name = self.user_info.get('subscription_plan', 'N/A').replace("_", " ").title()
        user_plan_label = ctk.CTkLabel(sidebar_content_frame, text=f"Plan: {plan_name}",
                                       font=self._get_font("size_small"))
        self._apply_theme_to_widget(user_plan_label, "subtitle")
        user_plan_label.pack(pady=(0, self.padding['large']), anchor="w")

        sub_button = ctk.CTkButton(sidebar_content_frame, text="💎 Manage Subscription",
                                   command=self.show_subscription_frame, font=self._get_font("size_small"))
        self._apply_theme_to_widget(sub_button, "outline")
        sub_button.pack(fill="x", pady=(0, self.padding['large']))

        prompt_label = ctk.CTkLabel(sidebar_content_frame, text="📝 Your Prompt:",
                                    font=self._get_font("size_medium", "bold"))
        self._apply_theme_to_widget(prompt_label)
        prompt_label.pack(pady=(self.padding['medium'], self.padding['small']), anchor="w")
        self.prompt_entry = ctk.CTkTextbox(sidebar_content_frame, height=120, font=self._get_font("size_medium"))
        self._apply_theme_to_widget(self.prompt_entry)
        self.prompt_entry.pack(fill="x", expand=False)

        lang_label = ctk.CTkLabel(sidebar_content_frame, text="🌐 Language:", font=self._get_font("size_medium", "bold"))
        self._apply_theme_to_widget(lang_label)
        lang_label.pack(pady=(self.padding['medium'], self.padding['small']), anchor="w")
        self.language_options = ["Auto-detect", "Python", "JavaScript", "Java", "C++", "HTML", "CSS", "SQL", "Go",
                                 "Ruby", "TypeScript"]
        self.language_var = ctk.StringVar(value=self.language_options[0])
        language_menu = ctk.CTkOptionMenu(sidebar_content_frame, variable=self.language_var,
                                          values=self.language_options, font=self._get_font("size_small"))
        self._apply_theme_to_widget(language_menu)
        language_menu.pack(fill="x")

        context_label = ctk.CTkLabel(sidebar_content_frame, text="🔗 Context (Optional):",
                                     font=self._get_font("size_medium", "bold"))
        self._apply_theme_to_widget(context_label)
        context_label.pack(pady=(self.padding['medium'], self.padding['small']), anchor="w")
        self.context_entry = ctk.CTkTextbox(sidebar_content_frame, height=180, font=self._get_font("size_small"))
        self._apply_theme_to_widget(self.context_entry)
        self.context_entry.pack(fill="x", expand=False)

        self.generate_button = ctk.CTkButton(sidebar_content_frame, text="✨ Generate Code", height=40,
                                             command=self.handle_generate_code_async,
                                             font=self._get_font("size_medium", "bold"))
        self._apply_theme_to_widget(self.generate_button)
        self.generate_button.pack(pady=self.padding['large'], fill="x")

        logout_button = ctk.CTkButton(left_pane, text="Logout", height=35, command=self.handle_logout,
                                      font=self._get_font("size_small", "bold"))
        self._apply_theme_to_widget(logout_button, "accent")
        logout_button.pack(side="bottom", pady=self.padding['medium'], padx=self.padding['medium'], fill="x")

        # Right Pane (Main content area for output)
        right_pane = ctk.CTkFrame(paned_window)
        self._apply_theme_to_widget(right_pane, "content_frame_color")  # Matches window bg
        paned_window.add(right_pane, stretch="always", minsize=400)

        output_title_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        output_title_frame.pack(fill="x", padx=self.padding['medium'],
                                pady=(self.padding['medium'], self.padding['small']))

        output_label = ctk.CTkLabel(output_title_frame, text="💡 Generated Output:",
                                    font=self._get_font("size_large", "bold"))
        self._apply_theme_to_widget(output_label)
        output_label.pack(side="left")

        self.output_text = ctk.CTkTextbox(right_pane, font=self._get_font("size_medium", mono=True), wrap=tk.WORD)
        self._apply_theme_to_widget(self.output_text)
        self.output_text.configure(text_color="#D4D4D4")  # Specific for code
        self.output_text.pack(fill="both", expand=True, padx=self.padding['medium'], pady=(0, self.padding['medium']))
        self.update_status("Ready for your command!", "primary_color")

    def handle_generate_code_async(self):
        prompt = self.prompt_entry.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Error", "Prompt cannot be empty.")
            self.update_status("Prompt cannot be empty.", "warning_color")
            return

        language = self.language_var.get()
        context = self.context_entry.get("1.0", tk.END).strip()
        self.output_text.delete("1.0", tk.END)

        self._execute_api_call(
            self.api_client.generate_code,
            (prompt, language, context if context else None),
            self.generate_button,
            success_message=None,  # Handled by callback
            success_callback=self._generate_code_success,
            failure_message_prefix="Code Generation Error"
        )

    def _generate_code_success(self, response_data):
        self.output_text.delete("1.0", tk.END)
        generated_code = response_data.get("generated_code", "Error: No code generated.")
        self.output_text.insert("1.0", generated_code)
        if response_data.get("warnings"):
            warnings_str = "\n\n--- Warnings ---\n" + "\n".join(response_data["warnings"])
            self.output_text.insert(tk.END, warnings_str)
        self.update_status("Code generation complete!", "success_color")

    def show_subscription_frame(self):
        sub_window = ctk.CTkToplevel(self)
        sub_window.title("💎 Manage Subscription")
        sub_window.geometry("750x650")  # Increased size
        sub_window.transient(self)
        sub_window.grab_set()
        sub_window.configure(fg_color=self.theme.get("background_color"))
        sub_window.attributes("-topmost", True)  # Ensure it's on top

        main_scroll_frame = ctk.CTkScrollableFrame(sub_window, fg_color="transparent")
        main_scroll_frame.pack(fill="both", expand=True, padx=self.padding['large'], pady=self.padding['large'])

        title = ctk.CTkLabel(main_scroll_frame, text="Choose Your Plan", font=self._get_font("size_xlarge", "bold"))
        self._apply_theme_to_widget(title, "title")
        title.pack(pady=(self.padding['small'], self.padding['large']))

        status_data = self.api_client.get_subscription_status()
        current_plan_text = "Current Plan: Free Tier"
        if status_data and not status_data.get("error") and status_data.get("is_active"):
            plan_name_str = str(status_data.get('current_plan', 'N/A')).replace("_", " ").title()
            current_plan_text = f"Your Current Plan: {plan_name_str}"
            if status_data.get("expires_at"):
                current_plan_text += f" (Renews/Expires: {status_data.get('expires_at')[:10]})"
        elif status_data and status_data.get("error"):
            current_plan_text = f"Error fetching status: {status_data.get('detail')}"

        status_label = ctk.CTkLabel(main_scroll_frame, text=current_plan_text, font=self._get_font("size_medium"))
        self._apply_theme_to_widget(status_label)
        if status_data and status_data.get("is_active"):
            status_label.configure(text_color=self.theme.get("success_color"))
        status_label.pack(pady=(0, self.padding['large']))

        plans_data = self.api_client.get_plans()
        if plans_data and not isinstance(plans_data, dict) or (
                isinstance(plans_data, dict) and not plans_data.get("error")):
            plans_container = ctk.CTkFrame(main_scroll_frame, fg_color="transparent")  # To use grid for cards
            plans_container.pack(fill="x", expand=True)

            # Configure grid columns to be responsive
            num_columns = 3  # Adjust as needed, e.g., 2 for wider cards
            for i in range(num_columns):
                plans_container.grid_columnconfigure(i, weight=1, uniform="plan_card")

            for i, plan in enumerate(plans_data):
                plan_frame = ctk.CTkFrame(plans_container, border_width=2)
                is_current_plan = status_data and not status_data.get("error") and status_data.get(
                    "current_plan") == plan.get("id") and status_data.get("is_active")

                plan_frame.configure(
                    border_color=self.theme.get("primary_color") if is_current_plan else self.theme.get(
                        "secondary_color"))
                self._apply_theme_to_widget(plan_frame)  # Apply default frame theme first

                plan_frame.grid(row=0, column=i % num_columns, padx=self.padding['medium'], pady=self.padding['medium'],
                                sticky="nsew")

                plan_name = ctk.CTkLabel(plan_frame, text=plan.get("name"), font=self._get_font("size_large", "bold"))
                self._apply_theme_to_widget(plan_name)
                plan_name.pack(pady=(self.padding['large'], self.padding['small']))

                price_text = f"${plan.get('price_monthly')}/mo  |  ${plan.get('price_yearly')}/yr"
                plan_price = ctk.CTkLabel(plan_frame, text=price_text, font=self._get_font("size_medium"))
                self._apply_theme_to_widget(plan_price, "subtitle")
                plan_price.pack(pady=self.padding['small'])

                ctk.CTkFrame(plan_frame, height=1, fg_color=self.theme.get("disabled_color")).pack(fill="x",
                                                                                                   padx=self.padding[
                                                                                                       'large'],
                                                                                                   pady=self.padding[
                                                                                                       'medium'])

                features_label = ctk.CTkLabel(plan_frame, text="Features:", font=self._get_font("size_small", "bold"))
                self._apply_theme_to_widget(features_label)
                features_label.pack(anchor="w", padx=self.padding['medium'])

                for feat in plan.get("features", []):
                    feat_label = ctk.CTkLabel(plan_frame, text=f"✓ {feat}", font=self._get_font("size_small"),
                                              justify="left")
                    self._apply_theme_to_widget(feat_label)
                    feat_label.pack(anchor="w", padx=self.padding['large'], pady=1)

                ctk.CTkFrame(plan_frame, height=1, fg_color=self.theme.get("disabled_color")).pack(fill="x",
                                                                                                   padx=self.padding[
                                                                                                       'large'],
                                                                                                   pady=self.padding[
                                                                                                       'medium'])

                dummy_stripe_token = "pm_card_visa"
                dummy_paypal_order_id = f"PAYPAL_ORDER_{plan.get('id').upper()}"
                dummy_crypto_tx = f"CRYPTO_TX_{plan.get('id').upper()}"

                if is_current_plan:
                    subscribed_label = ctk.CTkButton(plan_frame, text="✓ Current Plan",
                                                     font=self._get_font("size_medium", "bold"), state="disabled")
                    self._apply_theme_to_widget(subscribed_label)
                    subscribed_label.configure(fg_color=self.theme.get("success_color"),
                                               text_color=self.theme.get("button_text_color"))
                    subscribed_label.pack(pady=self.padding['medium'], padx=self.padding['medium'], fill="x")
                else:
                    # Payment buttons frame
                    payment_buttons_frame = ctk.CTkFrame(plan_frame, fg_color="transparent")
                    payment_buttons_frame.pack(pady=self.padding['medium'], padx=self.padding['medium'], fill="x")

                    btn_stripe = ctk.CTkButton(payment_buttons_frame, text="💳 Card", font=self._get_font("size_small"),
                                               command=lambda p=plan.get("id"): self.handle_subscribe_async(sub_window,
                                                                                                            p,
                                                                                                            dummy_stripe_token,
                                                                                                            "stripe"))
                    self._apply_theme_to_widget(btn_stripe)
                    btn_stripe.pack(side="left", expand=True, padx=(0, self.padding['small']))

                    btn_paypal = ctk.CTkButton(payment_buttons_frame, text="🅿️ PayPal",
                                               font=self._get_font("size_small"),
                                               command=lambda p=plan.get("id"): self.handle_subscribe_async(sub_window,
                                                                                                            p,
                                                                                                            dummy_paypal_order_id,
                                                                                                            "paypal"))
                    self._apply_theme_to_widget(btn_paypal)
                    btn_paypal.pack(side="left", expand=True, padx=(0, self.padding['small']))

                    btn_crypto = ctk.CTkButton(payment_buttons_frame, text="₿ Crypto",
                                               font=self._get_font("size_small"),
                                               command=lambda p=plan.get("id"): self.handle_subscribe_async(sub_window,
                                                                                                            p,
                                                                                                            dummy_crypto_tx,
                                                                                                            "crypto"))
                    self._apply_theme_to_widget(btn_crypto)
                    btn_crypto.pack(side="left", expand=True)


        elif plans_data and plans_data.get("error"):
            no_plans_label = ctk.CTkLabel(main_scroll_frame, text=f"Could not load plans: {plans_data.get('detail')}",
                                          font=self._get_font())
            self._apply_theme_to_widget(no_plans_label)
            no_plans_label.pack(pady=10)
        else:
            no_plans_label = ctk.CTkLabel(main_scroll_frame, text="Loading subscription plans...",
                                          font=self._get_font())
            self._apply_theme_to_widget(no_plans_label)
            no_plans_label.pack(pady=10)

        close_button = ctk.CTkButton(sub_window, text="Close", command=sub_window.destroy,
                                     font=self._get_font("size_medium", "bold"), height=40)
        self._apply_theme_to_widget(close_button, "outline")
        close_button.pack(pady=(0, self.padding['large']), padx=self.padding['large'], fill="x", side="bottom")

    def handle_subscribe_async(self, sub_window_ref, plan_id: str, payment_token: str, gateway: str):
        is_yearly = False  # Add UI for this if needed
        confirm = messagebox.askyesno("Confirm Subscription",
                                      f"Subscribe to {plan_id.title()} plan using {gateway.title()}?\n(This is a simulated payment for demonstration)",
                                      parent=sub_window_ref)  # Ensure messagebox is child of toplevel
        if not confirm:
            return

        # Find the button that triggered this to disable it (this is tricky with lambdas like this)
        # For simplicity, we won't disable individual payment buttons here, but show general processing.
        self.update_status(f"Processing {gateway} payment for {plan_id}...", "warning_color")

        def api_thread_task():
            result = self.api_client.subscribe(plan_id, payment_token, gateway, is_yearly)

            def ui_update_task():
                success = self._handle_api_response(
                    result,
                    success_message=result.get("message", f"Successfully subscribed to {plan_id}!"),
                    success_callback=self._subscribe_success,
                    failure_message_prefix="Subscription Error"
                )
                if success:
                    if sub_window_ref.winfo_exists():  # Check if window still exists
                        sub_window_ref.destroy()

            self.after(0, ui_update_task)

        threading.Thread(target=api_thread_task, daemon=True).start()

    def _subscribe_success(self, response_data):
        self.user_info = self.api_client.get_current_user()  # Refresh user info
        if self.current_frame.winfo_exists() and hasattr(self, 'prompt_entry'):
            self.show_main_app_frame()  # Redraw main screen

    def handle_logout(self):
        # Add confirmation dialog
        if not messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            return
        self.api_client.token = None
        self.user_info = None
        self.show_login_frame()
        self.update_status("Logged out successfully.", "primary_color")


if __name__ == "__main__":
    import os

    # Ensure frontend/assets directory exists if you plan to use icons/images later
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)

    api_client = ApiClient(base_url=BACKEND_URL)
    app = CodeAssistantApp(api_client)
    app.mainloop()