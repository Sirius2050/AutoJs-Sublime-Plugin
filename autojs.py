import types

import sublime
import sublime_plugin

import socket
import json
import threading
import traceback
from io import StringIO
from contextlib import closing

hostname = ''
port = 1209


class AutoJsServer:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.conn = None
        self.server = None
        self.t=None
    def get_host_ip(self):  
        try:  
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
            s.connect(('8.8.8.8', 80))  
            ip = s.getsockname()[0]  
        finally:  
            s.close()
        print("Please connect ",ip," with Auto.Js.")
        #return ip  
    def connect(self):
        if(self.t is not None):
            #sublime.status_message("Can't start server because server is running!")
            print("Can't start server because server is running!")
            return
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((hostname, port))
            self.server.listen(1)
            #print("server listening at {0}:{1}".format(self.hostname, self.port))
            self.t = threading.Thread(target=self.listen)
            self.t.setDaemon(True)
            self.t.start()
        except Exception as e:
            print(Exception, ":", e)
            traceback.print_exc()

    def listen(self):
        print("waiting for accepting")
        get_host_ip()
        self.conn, addr = self.server.accept()
        print("accepted: {0}:{1}".format(addr[0], addr[1]))
        sublime.status_message("{0}:{1} connected".format(addr[0], addr[1]))
        try:
            with closing(self.conn.makefile(encoding='utf-8')) as f:
                for line in f:
                    json_obj = json.loads(line)
                    self.on_receive(json_obj)
        except Exception as e:
            print(Exception, ":", e)
            traceback.print_exc()
        finally:
            self.disconnect()

    def on_receive(self, data):
        if data['type'] == 'log':
            print("Log: {0}".format(data['log']))

    def send(self, obj):
        if self.conn is None:
            sublime.error_message("Please connect the device before this action")
        else:
            # print("send", obj)
            self.conn.sendall(bytes(json.dumps(obj) + "\n", 'utf-8'))

    def disconnect(self):
        if self.server is not None:
            try:
                self.server.close()
                print('disconnected')
            except Exception as e:
                print(Exception, ":", e)
            finally:
                self.server = None
                self.conn = None

    def __del__(self):
        self.disconnect()


server = AutoJsServer(hostname, port)


class RunCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        content = self.view.substr(sublime.Region(0, self.view.size()))
        server.send({
            'type': 'command',
            'view_id': self.view.id(),
            'name': self.view.file_name(),
            'command': 'run',
            'script': content
        })


class StopCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        server.send({
            'type': 'command',
            'view_id': self.view.id(),
            'command': 'stop',
        })


class RerunCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        content = self.view.substr(sublime.Region(0, self.view.size()))
        server.send({
            'type': 'command',
            'view_id': self.view.id(),
            'name': self.view.file_name(),
            'script': content,
            'command': 'rerun',
        })


class StopAllCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global server
        server.send({
            'type': 'command',
            'command': 'stopAll'
        })

class SaveToPhoneCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global server
        content = self.view.substr(sublime.Region(0, self.view.size()))
        server.send({
            'type': 'command',
            'view_id': self.view.id(),
            'name': self.view.file_name(),
            'script': content,
            'command': 'save',
        })

class ConnectCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global server
        server.connect()


class DisconnectCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global server
        server.disconnect()
