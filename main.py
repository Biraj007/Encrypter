import os
import hashlib
import base64
import binascii
import time
import threading
import re
from tkinter import *
from tkinter import messagebox, filedialog
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from tkinter.ttk import Progressbar

# AES Key Size and Constants
BLOCK_SIZE = 16
AES_KEY_SIZE = 32
MAX_RETRIES = 3
LOCKOUT_TIME = 30  # Lockout duration in seconds

class PasswordManager:
    def __init__(self):
        self.user_password = None
        self.retry_count = 0
        self.lockout_start_time = None

    def hash_password(self, password):
        salt = os.urandom(16)
        salted_hash = salt + hashlib.sha256(salt + password.encode()).digest()
        return salted_hash

    def verify_password(self, password):
        if self.user_password is None:
            return False
        salt = self.user_password[:16]
        expected_hash = self.user_password[16:]
        return hashlib.sha256(salt + password.encode()).digest() == expected_hash

    def validate_password(self, password):
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter."
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter."
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one digit."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character."
        return True, None

    def set_password(self):
        screen = Tk()
        screen.geometry("300x400")
        screen.title("Set Password")

        Label(screen, text="Set your encryption/decryption password", fg="black", font=("calibri", 13)).pack(pady=20)
        Label(screen, text="Password must include:\n- At least 8 characters\n- At least one uppercase letter\n- One lowercase letter\n- One digit\n- One special character", fg="gray", font=("calibri", 10)).pack(pady=5)

        password_var = StringVar()
        Entry(screen, textvariable=password_var, width=19, bd=0, font=("arial", 25), show="*").pack(pady=10)

        def save_password():
            entered_password = password_var.get()
            is_valid, validation_message = self.validate_password(entered_password)
            if not is_valid:
                messagebox.showerror("Password Error", validation_message)
            else:
                self.user_password = self.hash_password(entered_password)
                screen.destroy()

        Button(screen, text="Save Password", height=2, width=20, bg="#1089ff", fg="white", bd=0, command=save_password).pack(pady=20)
        screen.mainloop()

    def check_lockout(self):
        if self.lockout_start_time:
            elapsed_time = time.time() - self.lockout_start_time
            if elapsed_time < LOCKOUT_TIME:
                remaining_time = LOCKOUT_TIME - int(elapsed_time)
                messagebox.showerror("Locked Out", f"Too many failed attempts. Try again in {remaining_time} seconds.")
                return True
            else:
                self.lockout_start_time = None
                self.retry_count = 0
        return False

    def attempt_login(self, password):
        if self.check_lockout():
            return False

        if self.verify_password(password):
            self.retry_count = 0
            return True
        else:
            self.retry_count += 1
            if self.retry_count >= MAX_RETRIES:
                self.lockout_start_time = time.time()
                messagebox.showerror("Locked Out", f"Too many failed attempts. You are locked out for {LOCKOUT_TIME} seconds.")
            else:
                remaining_attempts = MAX_RETRIES - self.retry_count
                messagebox.showerror("Alert!", f"Invalid password. {remaining_attempts} attempt(s) remaining.")
            return False

password_manager = PasswordManager()

# Progress bar function for UI tasks
def show_progress_bar(window, task):
    progress_window = Toplevel(window)
    progress_window.title("Processing")
    progress_window.geometry("300x100")
    progress_window.attributes('-topmost', True)
    Label(progress_window, text="Processing, please wait...").pack(pady=10)
    
    progress = Progressbar(progress_window, orient=HORIZONTAL, length=250, mode='indeterminate')
    progress.pack(pady=10)
    progress.start()

    def close_progress():
        progress.stop()
        time.sleep(1)
        progress_window.destroy()

    threading.Thread(target=lambda: [task(), close_progress()]).start()

# Text encryption function using AES-GCM
def encrypt():
    password = code.get()
    if password_manager.verify_password(password):
        screen1 = Toplevel(screen)
        screen1.title("Encryption")
        screen1.geometry("500x300")
        screen1.configure(bg="#ed3833")

        message = text1.get(1.0, END)
        if not message.strip():
            messagebox.showerror("Error", "No text provided for encryption")
            return

        def process_encryption():
            try:
                key = hashlib.sha256(password.encode()).digest()
                cipher = AES.new(key, AES.MODE_GCM)
                ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
                encrypted_data = base64.b64encode(cipher.nonce + tag + ciphertext).decode('utf-8')

                Label(screen1, text="ENCRYPT", font="arial", fg="white", bg="#ed3833").place(x=10, y=0)
                text2 = Text(screen1, font="Robote 10", bg="white", relief=GROOVE, wrap=WORD, bd=0)
                text2.place(x=10, y=40, width=480, height=230)
                text2.insert(END, encrypted_data)
            except Exception as e:
                messagebox.showerror("Encryption Error", f"Failed to encrypt: {str(e)}")

        show_progress_bar(screen, process_encryption)
    elif password == "":
        messagebox.showerror("Alert!", "Please enter a password")
    else:
        messagebox.showerror("Alert!", "Invalid password")

# Text decryption function using AES-GCM with specific error messages
def decrypt():
    password = code.get()
    if password_manager.attempt_login(password):
        screen2 = Toplevel(screen)
        screen2.title("Decryption")
        screen2.geometry("500x300")
        screen2.configure(bg="#00bd56")

        message = text1.get(1.0, END)
        if not message.strip():
            messagebox.showerror("Error", "No text provided for decryption")
            return

        def process_decryption():
            try:
                key = hashlib.sha256(password.encode()).digest()
                encrypted_data = base64.b64decode(message)
                nonce, tag, ciphertext = encrypted_data[:BLOCK_SIZE], encrypted_data[BLOCK_SIZE:2*BLOCK_SIZE], encrypted_data[2*BLOCK_SIZE:]

                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                decrypted_message = cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')

                Label(screen2, text="DECRYPT", font="arial", fg="white", bg="#00bd56").place(x=10, y=0)
                text2 = Text(screen2, font="Robote 10", bg="white", relief=GROOVE, wrap=WORD, bd=0)
                text2.place(x=10, y=40, width=480, height=230)
                text2.insert(END, decrypted_message)

            except ValueError as e:
                if "MAC check failed" in str(e):
                    messagebox.showerror("Decryption Error", "The message is corrupted or has been tampered with.")
                else:
                    messagebox.showerror("Decryption Error", "Incorrect password provided.")
            except binascii.Error:
                messagebox.showerror("Decryption Error", "The input message is not in the correct format.")
            except Exception as e:
                messagebox.showerror("Decryption Error", f"Failed to decrypt: {str(e)}")

        show_progress_bar(screen, process_decryption)
    elif password == "":
        messagebox.showerror("Alert!", "Please enter a password")
    else:
        messagebox.showerror("Alert!", "Invalid password")

# GUI Setup
def main_screen():
    global screen, code, text1
    screen = Tk()
    screen.geometry("375x500")
    screen.title("Python Encryptor")

    def reset():
        code.set("")
        text1.delete(1.0, END)

    Label(text="Enter text for encryption and decryption", fg="black", font=("calibri", 13)).place(x=10, y=10)
    text1 = Text(font="Robote 20", bg="white", relief=GROOVE, wrap=WORD, bd=0)
    text1.place(x=10, y=50, width=355, height=100)

    Label(text="Enter secret key for encryption and decryption", fg="black", font=("calibri", 13)).place(x=10, y=170)
    code = StringVar()
    Entry(textvariable=code, width=19, bd=0, font=("arial", 25), show="*").place(x=10, y=200)

    Button(text="ENCRYPT", height="2", width=23, bg="#ed3833", fg="white", bd=0, command=encrypt).place(x=10, y=250)
    Button(text="DECRYPT", height="2", width=23, bg="#00bd56", fg="white", bd=0, command=decrypt).place(x=200, y=250)
    Button(text="RESET", height="2", width=50, bg="#1089ff", fg="white", bd=0, command=reset).place(x=10, y=300)

    screen.mainloop()

# Set the initial password and start the application
password_manager.set_password()
main_screen()
