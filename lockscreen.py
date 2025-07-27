import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import time
import datetime
import json
import os
import sys
from cryptography.fernet import Fernet

# ======== HELPER FOR BUNDLED RESOURCES ========
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS  # PyInstaller temporary folder
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ======== CONSTANTS ========
PASSWORD_FILE = 'secret.json'
ENCRYPTION_KEY_FILE = 'key.key'
LOGO_PATH = resource_path('sam.jpg')  # Access image safely
DEFAULT_PASSWORD = 'SAM'
ATTEMPT_LOG_FILE = 'attempts.log'

# ======== ENCRYPTION SETUP ========
def generate_key():
    key = Fernet.generate_key()
    with open(ENCRYPTION_KEY_FILE, 'wb') as key_file:
        key_file.write(key)
    return key

def load_key():
    if not os.path.exists(ENCRYPTION_KEY_FILE):
        return generate_key()
    with open(ENCRYPTION_KEY_FILE, 'rb') as key_file:
        return key_file.read()

def encrypt_password(password):
    key = load_key()
    return Fernet(key).encrypt(password.encode()).decode()

def decrypt_password(encrypted):
    key = load_key()
    return Fernet(key).decrypt(encrypted.encode()).decode()

# ======== INIT PASSWORD FILE IF MISSING =========
if not os.path.exists(PASSWORD_FILE):
    encrypted_pw = encrypt_password(DEFAULT_PASSWORD)
    with open(PASSWORD_FILE, 'w') as file:
        json.dump({"password": encrypted_pw}, file)

# ======== GUI SETUP ========
root = tk.Tk()
root.title("Developer Lock Screen")
root.attributes('-fullscreen', True)
root.configure(bg='black')

# ======== Prevent Alt+F4 ========
def disable_close():
    pass

root.protocol("WM_DELETE_WINDOW", disable_close)

# ======== ROUNDED LOGO ========
def make_rounded(img):
    bigsize = (img.size[0] * 3, img.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(img.size, Image.Resampling.LANCZOS)
    img.putalpha(mask)
    return img

if os.path.exists(LOGO_PATH):
    logo_image = Image.open(LOGO_PATH).resize((140, 140))
    rounded = make_rounded(logo_image)
    logo_photo = ImageTk.PhotoImage(rounded)
    logo_label = tk.Label(root, image=logo_photo, bg='black')
    logo_label.pack(pady=(40, 10))

# ======== TITLE + TIME ========
title_frame = tk.Frame(root, bg='black')
title_frame.pack()

title_label = tk.Label(
    title_frame,
    text='Enter Developer Password:',
    font=('Arial', 26, 'bold'),
    fg='white',
    bg='black'
)
title_label.pack(side='left', padx=(0, 20))

clock_label = tk.Label(
    title_frame,
    text='',
    font=('Arial', 20),
    fg='#00cec9',
    bg='black'
)
clock_label.pack(side='left')

# ======== CLOCK ========
def update_time():
    now = time.strftime('%I:%M:%S %p')
    clock_label.config(text=now)
    root.after(1000, update_time)

update_time()

# ======== PASSWORD FIELD ========
password_entry = tk.Entry(
    root,
    font=('Arial', 22),
    show='*',
    width=25,
    justify='center'
)
password_entry.pack(pady=20)
password_entry.focus()

# ======== SHOW/HIDE TOGGLE ========
show_var = tk.BooleanVar()
def toggle_password():
    if show_var.get():
        password_entry.config(show='')
    else:
        password_entry.config(show='*')

toggle_btn = tk.Checkbutton(
    root,
    text='Show Password',
    variable=show_var,
    command=toggle_password,
    font=('Arial', 14),
    bg='black',
    fg='white',
    selectcolor='black',
    activebackground='black'
)
toggle_btn.pack()

# ======== FEEDBACK LABEL ========
feedback_label = tk.Label(root, text='', font=('Arial', 14), fg='red', bg='black')
feedback_label.pack(pady=(10, 0))

# ======== ATTEMPT LOGGING ========
def log_attempt(success, entered=''):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ATTEMPT_LOG_FILE, 'a') as f:
        if success:
            f.write(f"[{timestamp}] SUCCESSFUL LOGIN\n")
        else:
            f.write(f"[{timestamp}] FAILED LOGIN - Entered: {entered}\n")

# ======== LOGIN FUNCTION ========
attempts = 0
def check_password():
    global attempts
    entered = password_entry.get()
    with open(PASSWORD_FILE, 'r') as file:
        data = json.load(file)
    decrypted = decrypt_password(data['password'])

    if entered == decrypted:
        log_attempt(True)
        feedback_label.config(text='Access Granted!', fg='lightgreen')
        root.update()
        time.sleep(1)
        root.destroy()
    else:
        log_attempt(False, entered)
        attempts += 1
        if attempts >= 3:
            feedback_label.config(text='Too many attempts. Please wait...', fg='orange')
            root.update()
            time.sleep(5)
            attempts = 0
        else:
            feedback_label.config(text='Incorrect password. Try again.', fg='red')
        password_entry.delete(0, tk.END)

# ======== UNLOCK BUTTON ========
login_btn = tk.Button(
    root,
    text='Login',
    font=('Arial', 18, 'bold'),
    bg='#00b894',
    fg='white',
    activebackground='#55efc4',
    width=12,
    command=check_password
)
login_btn.pack(pady=20)

# ======== FOOTER ========
footer = tk.Label(
    root,
    text='© 2025 Nahabwe Samuel | Dev Access',
    font=('Helvetica', 10),
    fg='gray',
    bg='black'
)
footer.pack(side=tk.BOTTOM, pady=15)

root.mainloop()
