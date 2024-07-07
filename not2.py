import sys
import os
import shutil
import schedule
import time
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
import threading

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(__file__)

log_file_path = os.path.join(application_path, 'backup_log.txt') 

def backup_folder(src_folder, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    for item in os.listdir(src_folder):
        src_path = os.path.join(src_folder, item)
        dest_path = os.path.join(dest_folder, item)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dest_path)
    print(f"Backup completed from {src_folder} to {dest_folder}")
    log_backup_time()
    update_tray_tooltip()

def list_backup_folders(backup_base_path):
    try:
        folders = [os.path.join(backup_base_path, folder) for folder in os.listdir(backup_base_path)]
        folders = [folder for folder in folders if os.path.isdir(folder)]
        folders.sort(key=os.path.getctime)
    except FileNotFoundError:
        return []
    return folders

def manage_backup_folders(backup_base_path, max_folders=15):
    folders = list_backup_folders(backup_base_path)
    while len(folders) > max_folders:
        oldest_folder = folders.pop(0)
        shutil.rmtree(oldest_folder)
        print(f"Deleted old backup folder: {oldest_folder}")

def update_tray_tooltip():
    last_backup_time = read_last_backup_time()
    if last_backup_time:
        formatted_time = last_backup_time.strftime("%d-%m-%y %H:%M:%S")
        tray_icon.setToolTip(f"Last Backup: {formatted_time}")
    else:
        tray_icon.setToolTip("Application Running - No Backup Completed Yet")

def job():
    src_folder = r"C:\Users\newtr\Desktop\main"
    current_time = datetime.now().strftime("%d-%m-%y_%H-%M-%S")  
    dest_folder = os.path.join(r"D:\backup", current_time) 
    
    try:
        backup_folder(src_folder, dest_folder)
        manage_backup_folders(r"D:\backup")
        tray_icon.showMessage("Backup Status", "Backup completed successfully.", QSystemTrayIcon.Information, 2000)
    except Exception as e:
        tray_icon.showMessage("Backup Status", f"Backup failed: {str(e)}", QSystemTrayIcon.Critical, 2000)
        print(f"Backup failed: {str(e)}") 

def log_backup_time():
    current_time = datetime.now().strftime("%d-%m-%y %H:%M:%S")
    with open(log_file_path, "a") as file:  
        file.write(f"{current_time}\n")

#def read_last_backup_time():
#    try:
#        with open(log_file_path, "r") as file:
#            return datetime.fromisoformat(file.readlines()[-1].strip())
#    except (FileNotFoundError, IndexError):
#        return None

def read_last_backup_time():
    try:
        with open(log_file_path, "r") as file:
            last_line = file.readlines()[-1].strip()
            return datetime.strptime(last_line, "%d-%m-%y %H:%M:%S")  
    except (FileNotFoundError, IndexError):
        return None

def immediate_backup():
    last_backup_time = read_last_backup_time()
    now = datetime.now()
    today_scheduled_time = datetime.strptime(f"{now.strftime('%d-%m-%y')} 12:11", "%d-%m-%y %H:%M")

    if last_backup_time is None or (last_backup_time < today_scheduled_time and now > today_scheduled_time):
        return True
    return False

def run_schedule():
    backup_time = "12:00"
    schedule.every().day.at(backup_time).do(job)
    if immediate_backup():
        job()
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBackup script stopped gracefully.")

def create_system_tray_icon():
    global tray_icon
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon = QIcon(os.path.join(application_path, 'icon.png'))
    tray_icon = QSystemTrayIcon(icon, app)
    tray_icon.setToolTip("Backup Application Running")

    menu = QMenu()
    backup_now_action = QAction("Backup Now", app)
    backup_now_action.triggered.connect(job)
    menu.addAction(backup_now_action)

    exit_action = QAction("Exit", app)
    exit_action.triggered.connect(app.quit)
    menu.addAction(exit_action)

    tray_icon.setContextMenu(menu)
    tray_icon.show()

    backup_thread = threading.Thread(target=run_schedule)
    backup_thread.setDaemon(True)
    backup_thread.start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    create_system_tray_icon()
