import os
import telnetlib
import time
import sys
import re
import json
import cryptocode
import pymongo
import getpass
import tabulate
import datetime
import telegram
import speedtest
import netmiko
import difflib

from netmiko import ConnectHandler

# Khởi tạo thông tin các thiết bị
class Device():
    def __init__(self):
        self.key_encrypt = "vnpt.vlg"
        try:
            self.connect = pymongo.MongoClient("mongodb://localhost:27017/")
            self.database = self.connect["switch"]
        except Exception as e:
            print(e)

    def add_device(self):
        print("Nhập thông tin thiết bị:")
        regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
        ip = input("IP của switch: ")
        while not re.search(regex, ip):
            ip = input("IP switch không hợp lệ, vui lòng nhập lại: ")
        username = input("Tên đăng nhập: ")
        password = cryptocode.encrypt(getpass.getpass("Mật khẩu: "), self.key_encrypt)
        secret = cryptocode.encrypt(getpass.getpass("Secret: "), self.key_encrypt)
        name = input("Tên thiết bị: ")
        ftp_host = input("IP FTP: ")
        while not re.search(regex, ftp_host):
            ftp_host = input("IP FTP không hợp lệ, vui lòng nhập lại: ")
        ftp_username = input("Tên đăng nhập FTP: ")
        ftp_password = cryptocode.encrypt(getpass.getpass("Mật khẩu FTP: "), self.key_encrypt)

        data = {
            "ip": ip,
            "username": username,
            "password": password,
            "secret": secret,
            "name": name,
            "ftp_host": ftp_host,
            "ftp_username": ftp_username,
            "ftp_password": ftp_password
        }
        try:
            self.database['devices'].insert_one(data)
            print("-----------------------------\nThêm thiết bị thành công!")
        except Exception as e:
            print(e)

    def delete_device(self):
        try:
            ip = input("Nhập IP thiết bị muốn xóa: ")
            self.database['devices'].delete_one({"ip": ip})
            print("-----------------------------\nXóa thiết bị thành công!")
        except Exception as e:
            print(e)

    def update_device(self):
        try:
            print("---------------------------------------\n")
            ip = input("Nhập IP thiết bị muốn cập nhật: ")
            regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
            while not re.search(regex, ip):
                ip = input("IP switch không hợp lệ, vui lòng nhập lại: ")
            username = input("Tên đăng nhập: ")
            password = cryptocode.encrypt(getpass.getpass("Mật khẩu: "), self.key_encrypt)
            secret = cryptocode.encrypt(getpass.getpass("Secret: "), self.key_encrypt)
            name = input("Tên thiết bị: ")
            ftp_host = input("IP FTP: ")
            while not re.search(regex, ftp_host):
                ftp_host = input("IP FTP không hợp lệ, vui lòng nhập lại: ")
            ftp_username = input("Tên đăng nhập FTP: ")
            ftp_password = cryptocode.encrypt(getpass.getpass("Mật khẩu FTP: "), self.key_encrypt)
            data = {
                "ip": ip,
                "username": username,
                "password": password,
                "secret": secret,
                "name": name,
                "ftp_host": ftp_host,
                "ftp_username": ftp_username,
                "ftp_password": ftp_password
            }
            try:
                self.database['devices'].update_one({"ip": ip}, {"$set": data})
                print("-----------------------------\nCập nhật thiết bị thành công!")      
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    def show_device(self):
        try:
            list_devices = self.database['devices'].find()
            table = [['IP', 'Tên thiết bị', 'FTP host']]
            for device in list_devices:
                table.append([device['ip'], device['name'], device['ftp_host']])
            print(tabulate.tabulate(table, tablefmt="fancy_grid"))
        except Exception as e:
            print(e)

    def show_menu(self):
        print("\n---------------------------------------")
        print("1. Thêm thiết bị")
        print("2. Xóa thiết bị")
        print("3. Cập nhật thiết bị")
        print("4. Xem danh sách thiết bị")
        print("5. Thoát")
        print("---------------------------------------")

    def clear_screen(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def run(self):
        self.show_menu()
        choice = input("Nhập lựa chọn: ")
        if choice == "1":
            self.add_device()
        elif choice == "2":
            self.delete_device()
        elif choice == "3":
            self.update_device()
        elif choice == "4":
            self.clear_screen()
            self.show_device()
        elif choice == "5":
            sys.exit()
        else:
            print("Lựa chọn không hợp lệ!")
        self.run()

# Kết nối SSH với Switch
class SSH():
    def __init__(self):
        self.key_encrypt = "vnpt.vlg"
        try:
            self.connection = pymongo.MongoClient("mongodb://localhost:27017/")
            self.database = self.connection["switch"]
            self.devices = self.database['devices']
            self.bot_config = self.database['telegram'].find_one()
            self.chat_id = self.bot_config['chat_id']
            self.bot = telegram.Bot(token=self.bot_config['token'])
        except Exception as e:
            print(e)

    def send_telegram_message(self, title, message):
        try:
            self.bot.send_chat_action(chat_id=self.chat_id, action=telegram.ChatAction.TYPING)
            title = "<pre><code class='language-python'>{}</code></pre>".format(title)
            self.bot.send_message(chat_id=self.chat_id, text=title + "\n" + message , parse_mode=telegram.ParseMode.HTML)
        except Exception as e:
            print(e)
            with open("telegram_message.txt", "w", encoding="utf8") as f:
                f.write(str(message))
            f.close()
            self.bot.send_document(chat_id=self.chat_id, document=open("telegram_message.txt", "rb"), caption="<pre>NỘI DUNG TIN NHẮN</pre>", parse_mode=telegram.ParseMode.HTML)
            
    def connect_switch(self, ip, username, password, secret):
        try:
            self.ssh = netmiko.ConnectHandler(device_type="cisco_ios", ip=ip, username=username, password=password, secret=secret)
            if not self.ssh.check_enable_mode():
                self.ssh.enable()
        except Exception as e:
            print(e)

    def disconnect(self):
        try:
            self.ssh.disconnect()
        except Exception as e:
            print(e)

    def execute_command(self, command):
        try:
            return self.ssh.send_command_timing(command)
        except Exception as e:
            print(e)

    def save_config(self, ip):
        try:
            output = self.ssh.send_command_timing("show run")
            filename = "config_{}_{}.txt".format(ip, datetime.datetime.now().strftime("%Y%m%d"))
            with open(filename, "w", encoding="utf8") as f:
                f.write(output)
            f.close()
        except Exception as e:
            print(e)

    def detect_changed_config(self, ip):
        '''
        Thực hiện backup file config của switch
        và sau 2 tiếng, thực hiện đọc file config mới
        và so sánh 2 file config, nếu có sự thay đổi
        thì thông báo cho người dùng
        '''
        try:
            output = self.ssh.send_command("show run")
            old_file = "config_{}_{}.txt".format(ip, datetime.datetime.now().strftime("%Y%m%d"))
            new_file = "temp_config_{}_{}.txt".format(ip, datetime.datetime.now().strftime("%Y%m%d"))
            with open(new_file, "w", encoding="utf8") as f:
                f.write(output)
            f.close()
            if os.path.exists(old_file):
                difference = ""
                with open(old_file, "r", encoding="utf8") as old, open(new_file, "r", encoding="utf8") as new:
                    # Tạo file HTML so sánh sự khác biệt giữa 2 file config
                    difference += difflib.HtmlDiff().make_file(fromlines=old.readlines(),
                                                           tolines=new.readlines(), fromdesc="Old Config", todesc="New Config")
                f.close()
                os.replace(new_file, old_file)
                with open('difference.html', 'w', encoding="utf8") as f:
                    f.write(difference)
                f.close()
                self.bot.send_document(chat_id=self.chat_id, document=open("difference.html", "rb"), caption="<pre>NỘI DUNG FILE CONFIG</pre>", parse_mode=telegram.ParseMode.HTML)
            else:
                self.save_config(ip)
                self.send_telegram_message("Thông báo", "File config của switch {} đã được backup lần đầu".format(ip))
        except Exception as e:
            print(e)

    def backup_config_ftp(self, host, username, password, filename):
        backup_config_filename = filename + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        backup_config_command = "copy running-config ftp://" + str(username) + ":" + str(password) + "@" + str(host) + "/" + backup_config_filename
        try:
            self.execute_command(backup_config_command)
            self.execute_command("\n")
            self.execute_command("\n")
        except Exception as e:
            print(e)

    def speed_test(self):
        try:
            spt = speedtest.Speedtest()
            spt.get_best_server()
            self.send_telegram_message("SPEEDTEST", "<b>Download speed:</b> {} Mb/s\n<b>Upload speed:</b> {} Mb/s\n<b>Latency:</b> {} ms\n<b>Server:</b> {}".format(round((round(spt.download()) / 1048576), 2), round((round(spt.upload()) / 1048576), 2), round(spt.results.ping, 2), spt.results.server['sponsor'] + ' - ' + spt.results.server['name'] + ', ' + spt.results.server['country']))
        except Exception as e:
            print(e)

    def run(self):
        device = self.devices.find_one()
        self.connect_switch(device['ip'], device['username'], cryptocode.decrypt(device['password'], self.key_encrypt), cryptocode.decrypt(device['secret'], self.key_encrypt))
        # self.backup_config(device['ftp_host'], device['ftp_username'], cryptocode.decrypt(device['ftp_password'], self.key_encrypt), device['ip'])
        self.detect_changed_config(device['ip'])
        self.disconnect()

# Kết nối Telnel với Switch
class Telnet():
    def __init__(self):
        self.key_encrypt = "vnpt.vlg"
        try:
            self.connection = pymongo.MongoClient("mongodb://localhost:27017/")
            self.database = self.connection["switch"]
            self.devices = self.database['devices']
            self.bot_config = self.database['telegram'].find_one()
            self.chat_id = self.bot_config['chat_id']
            self.bot = telegram.Bot(token=self.bot_config['token'])
        except Exception as e:
            print(e)

    def send_telegram_message(self, title, message):
        try:
            self.bot.send_chat_action(chat_id=self.chat_id, action=telegram.ChatAction.TYPING)
            title = "<b>{}</b>".format(title)
            self.bot.send_message(chat_id=self.chat_id, text=title + "\n" + message, parse_mode=telegram.ParseMode.HTML)
        except Exception as e:
            print(e)

    def connect_switch(self, ip, username, password, secret):
        try:
            self.tn = telnetlib.Telnet(ip, 23, 5)
            self.tn.read_until(b"Username: ")
            self.tn.write(username.encode('ascii') + b"\n")
            if password:
                self.tn.read_until(b"Password: ")
                self.tn.write(password.encode('ascii') + b"\n")
            self.tn.write(b"enable\n")
            self.tn.write(secret.encode('ascii') + b"\n")
            # self.tn.write(b"\n")
            return self.tn.read_until(b"#").decode('ascii')
        except Exception as e:
            print(e)

    def disconnect_switch(self):
        self.tn.close()

    def execute_command(self, command):
        self.tn.write(command.encode('ascii') + b"\n")
        self.tn.write(b"\r\n")
        # return self.tn.read_eager().decode('ascii')
        return self.tn.read_until(b"#").decode('ascii')

    def backup_config_ftp(self, host, username, password, sw_name):
        backup_config_filename = sw_name + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        backup_config_command = "copy running-config ftp://" + str(username) + ":" + str(password) + "@" + str(host) + "/" + backup_config_filename + "\n\n"
        try:
            return self.execute_command(backup_config_command)
        except Exception as e:
            print(e)

    def speed_test(self):
        try:
            spt = speedtest.Speedtest()
            spt.get_best_server()
            self.send_telegram_message("SPEED TEST", "Download speed: {} Mb/s\nUpload speed: {} Mb/s\nLatency: {} ms\nServer: {}".format(round((round(spt.download()) / 1048576), 2), round((round(spt.upload(
            )) / 1048576), 2), round(spt.results.ping, 2), spt.results.server['sponsor'] + ' - ' + spt.results.server['name'] + ', ' + spt.results.server['country']))
        except Exception as e:
            print(e)

    def ping_test(self):
        self.tn.write("show ip arp\n\n".encode('ascii') + b"\n")
        self.tn.write(b"\r\n")
        print(self.tn.read_until(b"#").decode('ascii'))

    def check_port(self):
        check_port_command = "show interface status\r\n"
        try:
            self.tn.write(check_port_command.encode('ascii'))
            self.tn.write(b"\n")
            # print(self.tn.read_until(b"#").decode('ascii'))
            data = ''
            while data.find('#') == -1:
                data += self.tn.read_very_eager().decode('ascii')
            print(data)
            self.send_telegram_message("CHECK PORT", data)
        except Exception as e:
            print(e)

    def run(self):
        devices_list = self.devices.find()
        for device in devices_list:
            try:
                self.connect_switch(device['ip'], device['username'], cryptocode.decrypt(device['password'], self.key_encrypt), cryptocode.decrypt(device['secret'], self.key_encrypt))
                # self.backup_config_ftp(device['ftp_host'], device['ftp_username'], cryptocode.decrypt(device['ftp_password'], self.key_encrypt), device['ip'].replace(".", "_"))
                # self.send_telegram_message(device['name'], "Backup thành công!")
                # self.speed_test()
                self.ping_test()
                self.disconnect_switch()
            except Exception as e:
                print(e)

if __name__ == "__main__":
    # device = Device()
    # device.run()
    switch = SSH()
    switch.run()