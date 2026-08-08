from verifying_passcode import verify_user, add_user, reset_password, get_db_connection
from nicegui import ui, app
import school_home_page
import teacher_page
import lower
from insert import insert
from datetime import datetime


# ============================================================
# ADMIN ACCOUNTS
# ============================================================

ADMIN_ACCOUNTS = {
    "Apostle": "password1234",
    "Principal": "AdminPass2026",
    "Headmaster": "Secret123",

    # You can remove this line if you do not need admin_account
    "admin_account": "password1234",
}

# Used for case-insensitive admin login.
# Example: "apostle", "Apostle", "APOSTLE" will all match.
ADMIN_LOOKUP = {
    username.strip().lower(): password
    for username, password in ADMIN_ACCOUNTS.items()
}


def is_admin_username(username: str) -> bool:
    """
    Checks whether the username belongs to an admin account.
    This check is case-insensitive.
    """
    if not username:
        return False

    return username.strip().lower() in ADMIN_LOOKUP


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticates a user.

    1. First checks hardcoded ADMIN_ACCOUNTS.
    2. Then checks the database using verify_user().

    If you want only database users, remove the hardcoded admin check.
    """
    if not username or not password:
        return False

    username_key = username.strip().lower()

    # 1) Hardcoded admin login
    if username_key in ADMIN_LOOKUP and ADMIN_LOOKUP[username_key] == password:
        return True

    # 2) Database login
    try:
        return bool(verify_user(username.strip(), password))
    except Exception as e:
        print(f"verify_user error: {e}")
        return False


# ============================================================
# LOGIN ACTIVITY LOG
# ============================================================
def update_login_activity(username, status='Active'):
    """
    Records user login events and activity status in the database.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ensure the activity logs table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT, 
                timestamp TEXT,
                status TEXT
            )
        ''')

        # If a new active login happens, mark previous active sessions as inactive
        if status == 'Active':
            cursor.execute("""
                UPDATE activity_logs
                SET status = 'Inactive'
                WHERE status = 'Active'
            """)

        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Insert the new login activity record
        cursor.execute('''
            INSERT INTO activity_logs (username, timestamp, status) 
            VALUES (?, ?, ?)
        ''', (username, current_timestamp, status))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Activity log error: {e}")


# ============================================================
# GLOBAL UI SETTINGS
# ============================================================
# Strictly Navy Blue and White palette
ui.colors(primary='#0A192F', secondary='#FFFFFF', accent='#1E3A8A')


# ============================================================
# CUSTOM UI ANIMATIONS & OVERRIDES
# ============================================================
ui.add_css('''
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-fade-in-up {
    animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes meshMove {
    0%, 100% {
        transform: translate(0, 0) scale(1);
    }
    33% {
        transform: translate(40px, -60px) scale(1.1);
    }
    66% {
        transform: translate(-30px, 30px) scale(0.95);
    }
}

.animate-mesh {
    animation: meshMove 18s ease-in-out infinite;
}

/* Force Quasar Tabs to strictly use Navy Blue and White */
.q-tab--active {
    background-color: #0A192F !important;
    color: #FFFFFF !important;
}
.q-tab__indicator {
    display: none !important;
}
.q-tab {
    color: #0A192F !important;
}
.q-tab:hover {
    background-color: rgba(10, 25, 47, 0.05) !important;
}

/* Ensure inputs strictly use Navy Blue */
.q-field--outlined .q-field__control:before {
    border-color: rgba(10, 25, 47, 0.3) !important;
}
.q-field--outlined .q-field__control:after {
    border-color: #0A192F !important;
}
.q-field__label {
    color: #0A192F !important;
}
.q-field__native, .q-field__input {
    color: #0A192F !important;
}
''')


# SIMPLE REDIRECT HELPERS

def redirect_to_login():
    """
    Shows a small redirect message and sends the user to /login.
    """
    ui.label('Redirecting to login...').classes('text-lg font-semibold')
    ui.timer(0.1, lambda: ui.navigate.to('/login'), once=True)


def redirect_to_teacher():
    """
    Shows a small redirect message and sends the user to /teacher.
    """
    ui.label('Redirecting to teacher page...').classes('text-lg font-semibold')
    ui.timer(0.1, lambda: ui.navigate.to('/teacher'), once=True)



# PROTECTED PAGE WRAPPERS
# ===========================================================
def protected_home():
    """
    Protects /home.
    Only logged-in admins should access this page.
    """
    if not app.storage.user.get('logged_in'):
        redirect_to_login()
        return

    current_user = app.storage.user.get('current_user', '')

    # Allow access if storage says admin,
    # or if the stored current user matches an admin username.
    is_admin = app.storage.user.get('is_admin', False) or is_admin_username(current_user)

    if not is_admin:
        ui.notify('Home is for administrators only', color='#0A192F', textColor='white', position='top')
        redirect_to_teacher()
        return

    school_home_page.home()


def protected_teacher():
    """
    Protects /teacher.
    Any logged-in user can access this page.
    """
    if not app.storage.user.get('logged_in'):
        redirect_to_login()
        return

    teacher_page.teacher()


def protected_insert():
    """
    Protects /insert.
    Any logged-in user can access this page.
    """
    if not app.storage.user.get('logged_in'):
        redirect_to_login()
        return

    insert()


def lower_page():
    """
    Wrapper for the lower page.

    If your lower.py file contains a function called lower(),
    this will call it.

    If your lower page function has a different name,
    change this function accordingly.
    """
    target = getattr(lower, 'lower', None)

    if callable(target):
        target()
    elif callable(lower):
        lower()
    else:
        ui.label('Lower page is not configured correctly.').classes('text-lg font-semibold')



# REDESIGNED LOGIN PAGE (NAVY BLUE & WHITE INTERFACE)

def login_page():
    # Full-screen background (Deep Navy Blue)
    with ui.row().classes(
        'fixed inset-0 w-screen h-screen m-0 p-0 bg-[#0A192F] overflow-y-auto'
    ):
        # Subtle grid background (White with low opacity)
        ui.element('div').classes('absolute inset-0 pointer-events-none').style('''
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
            background-size: 40px 40px;
        ''')

        # Mesh gradient blobs (White with low opacity)
        ui.element('div').classes(
            'absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full '
            'bg-white/5 blur-[100px] animate-mesh pointer-events-none'
        )
        ui.element('div').classes(
            'absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] rounded-full '
            'bg-white/5 blur-[120px] animate-mesh pointer-events-none'
        ).style('animation-delay: -5s;')

        # Main content
        with ui.column().classes(
            'relative z-10 w-full min-h-screen items-center justify-center p-4 gap-6'
        ):
            
            # Login Card (Crisp White)
            with ui.card().classes(
                'w-full max-w-[480px] rounded-3xl border-2 border-[#0A192F] '
                'bg-white shadow-2xl shadow-[#0A192F]/30 animate-fade-in-up'
            ).tight():
                
                # Header
                with ui.column().classes('w-full p-8 pb-4 items-center'):
                    with ui.element('div').classes(
                        'w-16 h-16 rounded-2xl bg-[#0A192F] '
                        'flex items-center justify-center shadow-lg mb-4'
                    ):
                        ui.icon('school').classes('text-4xl text-white')
                    
                    ui.label('EduPortal').classes('text-2xl font-bold text-[#0A192F] tracking-tight')
                    ui.label('School Management System').classes('text-sm text-[#0A192F]/60 mb-6')

                    # Tabs
                    with ui.tabs().classes(
                        'w-full rounded-xl bg-[#0A192F]/5 p-1 border border-[#0A192F]/10'
                    ) as tabs:
                        login_tab = ui.tab('login', label='Sign In').classes(
                            'flex-1 rounded-lg text-xs font-semibold uppercase tracking-wider'
                        )
                        register_tab = ui.tab('register', label='Register').classes(
                            'flex-1 rounded-lg text-xs font-semibold uppercase tracking-wider'
                        )
                        reset_tab = ui.tab('reset', label='Reset').classes(
                            'flex-1 rounded-lg text-xs font-semibold uppercase tracking-wider'
                        )
                
                with ui.tab_panels(tabs, value=login_tab).classes(
                    'w-full bg-transparent p-6 pt-2'
                ):
                    
                    # LOGIN TAB
                    with ui.tab_panel(login_tab).classes('p-0'):
                        with ui.column().classes('w-full gap-5'):
                            
                            username_input = ui.input(label='Username').classes('w-full').props(
                                'outlined dense rounded standout hide-bottom-space '
                                'placeholder="Enter your username"'
                            )
                            
                            password_input = ui.input(
                                label='Password',
                                password=True,
                                password_toggle_button=True
                            ).classes('w-full').props(
                                'outlined dense rounded standout hide-bottom-space '
                                'placeholder="Enter your password"'
                            )

                            with ui.row().classes('w-full justify-end -mt-2'):
                                ui.link(
                                    'Forgot password?',
                                    '#'
                                ).on(
                                    'click',
                                    lambda: tabs.set_value(reset_tab)
                                ).classes(
                                    'text-xs font-semibold text-[#0A192F] hover:text-[#1E3A8A] transition-colors cursor-pointer underline'
                                )

                            with ui.button().classes(
                                'w-full py-3 mt-2 rounded-xl text-white font-bold text-sm tracking-wide '
                                'bg-[#0A192F] hover:bg-[#112240] active:scale-[0.98] transition-all '
                                'shadow-lg shadow-[#0A192F]/20 justify-center items-center gap-2'
                            ).props('unelevated no-caps') as login_btn:
                                login_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                                ui.label('Sign In').classes('font-semibold')

                            with ui.row().classes('w-full justify-center items-center gap-2 mt-4'):
                                ui.label('New to the platform?').classes('text-xs text-[#0A192F]/60')
                                ui.link(
                                    'Create an account',
                                    '#'
                                ).on(
                                    'click',
                                    lambda: tabs.set_value(register_tab)
                                ).classes(
                                    'text-xs font-bold text-[#0A192F] hover:text-[#1E3A8A] transition-colors cursor-pointer underline'
                                )

                        async def handle_page():
                            username = username_input.value.strip()
                            password = password_input.value

                            # Validate empty fields
                            if not username or not password:
                                ui.notify('Please fill the fields', color='#0A192F', textColor='white', position='top')
                                return

                            # Show loading state
                            login_btn.disable()
                            login_spinner.classes(remove='hidden')

                            try:
                                authenticated = authenticate_user(username, password)

                                if authenticated:
                                    admin_user = is_admin_username(username)

                                    # Save login state
                                    app.storage.user['logged_in'] = True
                                    app.storage.user['current_user'] = username
                                    app.storage.user['username'] = username
                                    app.storage.user['name'] = username
                                    app.storage.user['is_admin'] = admin_user

                                    # Record login activity
                                    update_login_activity(username, 'Active')

                                    ui.notify('Login successful!', color='#0A192F', textColor='white', position='top')

                                    # Role-based routing
                                    if admin_user:
                                        ui.navigate.to('/home')
                                    else:
                                        ui.navigate.to('/teacher')
                                else:
                                    ui.notify('Invalid username or password', color='#0A192F', textColor='white', position='top')
                                    login_btn.enable()
                                    login_spinner.classes(add='hidden')

                            except Exception as e:
                                print(f"Login error: {e}")
                                ui.notify(f'An error occurred: {e}', color='#0A192F', textColor='white', position='top')
                                login_btn.enable()
                                login_spinner.classes(add='hidden')

                        login_btn.on_click(handle_page)
                        password_input.on('keydown.enter', handle_page)

                    
                    # REGISTER TAB
                    with ui.tab_panel(register_tab).classes('p-0'):
                        with ui.column().classes('w-full gap-5'):
                            reg_user = ui.input(label='Username').classes('w-full').props(
                                'outlined dense rounded standout hide-bottom-space placeholder="Choose a username"'
                            )
                            
                            reg_email = ui.input(label='Email Address').classes('w-full').props(
                                'outlined dense rounded standout hide-bottom-space type="email" placeholder="name@school.edu"'
                            )

                            reg_pass = ui.input(
                                label='Password',
                                password=True,
                                password_toggle_button=True
                            ).classes('w-full').props(
                                'outlined dense rounded standout hide-bottom-space placeholder="Create a password"'
                            )

                            with ui.button().classes(
                                'w-full py-3 mt-2 rounded-xl text-white font-bold text-sm tracking-wide '
                                'bg-[#0A192F] hover:bg-[#112240] active:scale-[0.98] transition-all '
                                'shadow-lg shadow-[#0A192F]/20 justify-center items-center gap-2'
                            ).props('unelevated no-caps') as reg_btn:
                                reg_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                                ui.label('Create Account').classes('font-semibold')

                            with ui.row().classes('w-full justify-center items-center gap-2 mt-4'):
                                ui.label('Already have an account?').classes('text-xs text-[#0A192F]/60')
                                ui.link(
                                    'Sign in',
                                    '#'
                                ).on(
                                    'click',
                                    lambda: tabs.set_value(login_tab)
                                ).classes(
                                    'text-xs font-bold text-[#0A192F] hover:text-[#1E3A8A] transition-colors cursor-pointer underline'
                                )

                        async def handle_registration():
                            if not reg_user.value or not reg_email.value or not reg_pass.value:
                                ui.notify('All fields are required!', color='#0A192F', textColor='white', position='top')
                                return

                            reg_btn.disable()
                            reg_spinner.classes(remove='hidden')

                            try:
                                add_user(
                                    reg_user.value.strip(),
                                    reg_pass.value,
                                    reg_email.value.strip()
                                )

                                ui.notify('Registration Successful!', color='#0A192F', textColor='white', position='top')
                                tabs.set_value(login_tab)

                            except Exception as e:
                                print(f"Registration error: {e}")
                                ui.notify('Registration failed.', color='#0A192F', textColor='white', position='top')

                            finally:
                                reg_btn.enable()
                                reg_spinner.classes(add='hidden')

                        reg_btn.on_click(handle_registration)
                        reg_pass.on('keydown.enter', handle_registration)

                    
                    # RESET PASSWORD TAB
                    with ui.tab_panel(reset_tab).classes('p-0'):
                        with ui.column().classes('w-full gap-5'):
                            reset_user = ui.input(label='Username').classes('w-full').props(
                                'outlined dense rounded standout hide-bottom-space placeholder="Enter your username"'
                            )

                            reset_email = ui.input(label='Email Address').classes('w-full').props(
                                'outlined dense rounded standout hide-bottom-space type="email" placeholder="name@school.edu"'
                            )

                            reset_pass = ui.input(
                                label='New Password',
                                password=True,
                                password_toggle_button=True
                            ).classes('w-full').props(
                                'outlined dense rounded standout hide-bottom-space placeholder="Enter new password"'
                            )

                            with ui.button().classes(
                                'w-full py-3 mt-2 rounded-xl text-white font-bold text-sm tracking-wide '
                                'bg-[#0A192F] hover:bg-[#112240] active:scale-[0.98] transition-all '
                                'shadow-lg shadow-[#0A192F]/20 justify-center items-center gap-2'
                            ).props('unelevated no-caps') as reset_btn:
                                reset_spinner = ui.spinner(size='sm', color='white').classes('hidden')
                                ui.label('Reset Password').classes('font-semibold')

                            with ui.row().classes('w-full justify-center items-center gap-2 mt-4'):
                                ui.label('Remembered your password?').classes('text-xs text-[#0A192F]/60')
                                ui.link(
                                    'Back to Login',
                                    '#'
                                ).on(
                                    'click',
                                    lambda: tabs.set_value(login_tab)
                                ).classes(
                                    'text-xs font-bold text-[#0A192F] hover:text-[#1E3A8A] transition-colors cursor-pointer underline'
                                )

                        async def handle_reset():
                            reset_btn.disable()
                            reset_spinner.classes(remove='hidden')

                            try:
                                reset_password(
                                    reset_user.value.strip(),
                                    reset_email.value.strip(),
                                    reset_pass.value
                                )

                                ui.notify('Password updated!', color='#0A192F', textColor='white', position='top')
                                tabs.set_value(login_tab)

                            except Exception as e:
                                print(f"Reset password error: {e}")
                                ui.notify('Reset failed.', color='#0A192F', textColor='white', position='top')

                            finally:
                                reset_btn.enable()
                                reset_spinner.classes(add='hidden')

                        reset_btn.on_click(handle_reset)
                        reset_pass.on('keydown.enter', handle_reset)

        # Footer
        with ui.row().classes(
            'fixed bottom-5 left-0 right-0 z-20 justify-center items-center pointer-events-none'
        ):
            ui.label('Designed by Apostle').classes(
                'text-[11px] font-bold uppercase tracking-[0.25em] text-white/60'
            )



# ROUTES

pages = ui.sub_pages(routes={
    '/': login_page,
    '/login': login_page,
    '/home': protected_home,
    '/teacher': protected_teacher,
    '/insert': protected_insert,
    '/lower': lower_page,
})

# Force the router container to occupy full width
pages.classes('w-full')



# RUN APP

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="School Report System",
        storage_secret='some_long_random_string_here'
    )
