import time
import colorama
import paramiko
from datetime import datetime
import configparser
import os
from colorama import init, Fore, Style
import socket

# colorama色定義と初期化
colorama.init(wrap=True)
RED_COLOR = "\033[91m"
YELLOW_COLOR = "\033[93m"
RESET_COLOR = "\033[0m"


def connect_to_device(host, username, password):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # hostがIPアドレスかホスト名かを判定し、適切に接続する
        if host.replace('.', '').isdigit():  # 入力がIPアドレスかどうかをチェック
            host_ip = host
        else:  # 入力がホスト名の場合、ホスト名をIPアドレスに変換
            host_ip = socket.gethostbyname(host)

        ssh_client.connect(host_ip, username=username, password=password, timeout=5)
        print("Connected to", host)
        return ssh_client
    except paramiko.AuthenticationException:
        print("Authentication failed when connecting to", host)
    except paramiko.SSHException as e:
        print("Could not connect to", host, e)
    except Exception as e:
        print("Error:", e)
    return None


def execute_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    if error:
        print("Error:", error)
    else:
        if "show system alarms" in command or "show chassis alarms" in command:
            colorized_output = colorize_alarm_output(output)
            print(colorized_output)  # 色付けされたものをコンソールに表示
            return colorized_output  # 色付けされたものを出力
        else:
            print(output)  # 色付けなしのものをコンソールに表示
            return output  # 色付けされていないものを返す
    # コマンドが "traceroute" の場合は出力をログに追加 回避用
    if "traceroute" in command:
        print("Executing traceroute. Please wait.")
        print(output)
        time.sleep(5)
        return output


def execute_all_commands(ssh_client):
    commands = [
        "show system alarms",
        "show chassis alarms",
        "show chassis routing-engine",
        "show chassis hardware",
        "show chassis environment",
        "show system storage",
        "show chassis cluster status",
        "show virtual-chassis status",
        "ping 8.8.8.8 rapid count 10",
        "ping 133.139.1.1 rapid count 10",
        "ping 10.10.96.6 rapid count 10",
        "ping 10.10.98.9 rapid count 10",
        "traceroute 8.8.8.8"
    ]
    log = ""
    for command in commands:
        print("\nExecuting command:", command)
        log += f"Command: {command}\n"
        output = execute_command(ssh_client, command)
        if "show system alarms" in command or "show chassis alarms" in command:
            log += output  # 色付けされた出力をログに追加
        elif "traceroute" in command:
            print("Executing traceroute. Please wait.")
            print(output)
            time.sleep(5)
            log += output  # traceroute コマンドの結果をログに追加
        else:
            log += f"Command: {command}\n{output}\n"  # 色付けされていない出力をログに追加
    return log


def colorize_alarm_output(output):
    lines = output.split("\n")
    colorized_output = ""
    for line in lines:
        if "No alarms currently active" in line:
            line = f"{Fore.GREEN}{line}{Style.RESET_ALL}"  # アラームがない場合は緑色
        elif "Minor" in line:
            line = f"{Fore.YELLOW}{line}{Style.RESET_ALL}"  # 軽度のアラームは黄色
        elif "Major" in line or "Critical" in line:
            line = f"{Fore.RED}{line}{Style.RESET_ALL}"  # 重大または致命的なアラームは赤色
        colorized_output += line + "\n"
    return colorized_output


def save_log(log, host_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    host_name = host_name.strip().replace('host-name ', '')
    file_name = f"{host_name}_{timestamp}.txt"
    try:
        with open(file_name, 'w') as file:
            file.write(f"Host Name: {host_name}\n\n")  # ホストネームをログの1行目に追加
            file.write(log)
        print("Log saved successfully as", file_name)
    except Exception as e:
        print("Error saving log:", e)


def load_config():
    config = configparser.ConfigParser()
    config_file_path = 'config.ini'
    if os.path.exists(config_file_path):
        config.read(config_file_path)
        username = config.get('credentials', 'username')
        password = config.get('credentials', 'password')
        return username, password
    else:
        print("Config file not found.")
        return None, None


def display_motd():
    motd = """
  (\__/)
  (='.'=)
  (")_(")  Welcome to the Juniper Device Normalcy Check Tools!
    """
    print(motd)


def main():
    display_motd()
    username, password = load_config()
    if username is None or password is None:
        print("Error: Username or password not found in config.ini.")
        return

    while True:
        ip = input("Enter the IP address of the Juniper device: ")
        ssh_client = connect_to_device(ip, username, password)
        if ssh_client:
            while True:
                print("\nChoose an option:")
                print("1. Execute all commands and save log")
                print("2. Execute individual commands and save log")
                print("3. Connect to a different host")
                print("4. Exit")

                choice = input("Enter your choice: ")

                if choice == '1':
                    host_name_output = execute_command(ssh_client,
                                                       "show configuration system host-name")
                    host_name = host_name_output.strip().replace('host-name ', '').split(';')[0].strip()
                    log = execute_all_commands(ssh_client)
                    save_log(log, host_name)
                elif choice == '2':
                    host_name_output = execute_command(ssh_client,
                                                       "show configuration system host-name")
                    host_name = host_name_output.strip().replace('host-name ', '').split(';')[0].strip()
                    log = ""
                    while True:
                        print("\nChoose a command to execute:")
                        print("1. Show system alarms")
                        print("2. Show chassis alarms")
                        print("3. Show chassis routing-engine")
                        print("4. Show chassis hardware")
                        print("5. Show chassis environment")
                        print("6. Show system storage")
                        print("7. Show chassis cluster status")
                        print("8. show virtual-chassis status")
                        print("9. Ping 8.8.8.8")
                        print("10. Ping 133.139.1.1")
                        print("11. Ping 10.10.96.6")
                        print("12. Ping 10.10.98.9")
                        print("13. Traceroute 8.8.8.8")
                        print("14. Return to main menu")

                        sub_choice = input("Enter your choice: ")

                        if sub_choice == '1':
                            log += execute_command(ssh_client, "show system alarms")
                        elif sub_choice == '2':
                            log += execute_command(ssh_client, "show chassis alarms")
                        elif sub_choice == '3':
                            log += execute_command(ssh_client, "show chassis routing-engine")
                        elif sub_choice == '4':
                            log += execute_command(ssh_client, "show chassis hardware")
                        elif sub_choice == '5':
                            log += execute_command(ssh_client, "show chassis environment")
                        elif sub_choice == '6':
                            log += execute_command(ssh_client, "show system storage")
                        elif sub_choice == '7':
                            log += execute_command(ssh_client, "show chassis cluster status")
                        elif sub_choice == '8':
                            log += execute_command(ssh_client, "show virtual-chassis status")
                        elif sub_choice == '9':
                            log += execute_command(ssh_client, "ping 8.8.8.8 rapid count 10")
                        elif sub_choice == '10':
                            log += execute_command(ssh_client, "ping 133.139.1.1 rapid count 10")
                        elif sub_choice == '11':
                            log += execute_command(ssh_client, "ping 10.10.96.6 rapid count 10")
                        elif sub_choice == '12':
                            log += execute_command(ssh_client, "ping 10.10.98.9 rapid count 10")
                        elif sub_choice == '13':
                            log += execute_command(ssh_client, "traceroute 8.8.8.8")
                        elif sub_choice == '14':
                            break
                        else:
                            print("Invalid choice. Please enter a number between 1 and 14.")
                    save_log(log, host_name)
                elif choice == '3':
                    break
                elif choice == '4':
                    ssh_client.close()
                    return
                else:
                    print("Invalid choice. Please enter a number between 1 and 4.")


if __name__ == "__main__":
    main()
