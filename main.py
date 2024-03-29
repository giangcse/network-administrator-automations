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
import ast

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
        sw_cisco = {
            "device_type": "cisco_ios",
            "ip": ip,
            "username": username,
            "password": password,
            "secret": secret,
            "port": 22,
            "verbose": False
        }
        try:
            self.ssh = netmiko.ConnectHandler(**sw_cisco)
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
            self.send_telegram_message("THÔNG BÁO BACKUP", "Đã backup file config của switch {} lên FTP".format(filename))
        except Exception as e:
            print(e)

    def check_port(self):
        try:
            return self.execute_command("show interface status")
        except Exception as e:
            print(e)

    def check_vlan(self):
        try:
            return self.execute_command("show vlan")
        except Exception as e:
            print(e)

    def check_device_status(self):
        try:
            output = self.execute_command("show arp")
            output = output.split("\n")
            regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
            table_data = [['IP', 'Status']]

            for line in output:
                ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', line)
                if ip:
                    ping_output = self.execute_command("ping {} repeat 200".format(ip[0]))
                    if "Success rate" in ping_output:
                        ping_output = ping_output.split("\n")[5]
                        if "100 percent" in ping_output:
                            table_data.append([ip[0], ping_output.split(",")[-1]])
                        else:
                            table_data.append([ip[0], 'Ping failed'])
                    else:
                        table_data.append([ip[0], 'Ping failed'])
            table = tabulate.tabulate(table_data, tablefmt="fancy_grid")
            self.bot.send_message(self.chat_id, '<pre>' + table + '</pre>', parse_mode=telegram.ParseMode.HTML)
        except Exception as e:
            print(e)

    def speed_test(self):
        try:
            spt = speedtest.Speedtest()
            spt.get_best_server()
            self.send_telegram_message("SPEEDTEST", "<b>Download speed:</b> {} Mb/s\n<b>Upload speed:</b> {} Mb/s\n<b>Latency:</b> {} ms\n<b>Server:</b> {}".format(round((round(spt.download()) / 1048576), 2), round((round(spt.upload()) / 1048576), 2), round(spt.results.ping, 2), spt.results.server['sponsor'] + ' - ' + spt.results.server['name'] + ', ' + spt.results.server['country']))
        except Exception as e:
            print(e)

    def save_arp(self, ip):
        try:
            output = self.execute_command("show arp")
            output = output.split("\n")
            output.pop(0)
            result = []
            for i in output:
                line = i.split()
                line.pop(2)
                result.append(" ".join(line))
            # print(result)
            self.database['arp'].insert_one({"ip": str(ip), "log": str(result), "time": int(datetime.datetime.now().timestamp())})
        except Exception as e:
            print(e)

    def check_new_device(self):
        try:
            find_arp = self.database['arp'].find_one(sort=[("time", -1)])
            if len(list(find_arp)) > 0:
                last_log = ast.literal_eval(find_arp['log'])
                try:
                    new_log = self.execute_command("show arp")
                    new_log = new_log.split("\n")
                    new_log.pop(0)
                    new_devices = []
                    for i in new_log:
                        line = i.split()
                        line.pop(2)
                        new_devices.append(" ".join(line))
                    difference = list(set(new_devices).symmetric_difference(set(last_log)))
                    if len(difference) > 0:
                        self.send_telegram_message("CẢNH BÁO CÓ THIẾT BỊ KẾT NỐI/NGẮT KẾT NỐI", "\n".join(map(str, difference)))
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

    def read_message(self):
        try:
            updates = self.bot.get_updates()
            if len(updates) >= 2:
                message = updates[-1].message.text
                if message.startswith("/"):
                    message = message.split("/")[1]
                    self.send_telegram_message(message, self.execute_command(message))
            else:
                print("No message")
        except Exception as e:
            print(e)

    def run(self):
        devices = self.devices.find()
        for device in devices:
            # print(cryptocode.decrypt(device['password'], self.key_encrypt))
            # Kết nối đến switch
            self.connect_switch(device['ip'], device['username'], cryptocode.decrypt(device['password'], self.key_encrypt), cryptocode.decrypt(device['key'], self.key_encrypt))
            # Backup config switch lúc 00:00 mỗi ngày
            # self.backup_config_ftp(device['ip'], device['username'], cryptocode.decrypt(device['password'], self.key_encrypt), device['ip'])
            # Kiểm tra thiết bị còn hoạt động hay không mỗi 2 tiếng
            # self.check_device_status()
            # Kiểm tra thay đôi config switch mỗi 8 tiếng
            # self.detect_changed_config(device['ip'])
            # Check port 5 phút một lần
            # self.check_port()
            # self.read_message()
            # self.disconnect()

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
