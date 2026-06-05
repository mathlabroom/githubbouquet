# -*- coding: utf-8 -*-
import os
import urllib.request
import urllib.parse
import gzip  # 引入原生解压利器
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Screens.MessageBox import MessageBox

# 引入 Config 组件来实现复选框列表和数据持久化保存
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSelection, getConfigListEntry, ConfigYesNo

try:
    from enigma import eDVBDB
except ImportError:
    pass

# ==================== 🛠️ 配置区（完全对齐你的 Shell 脚本） 🛠️ ====================
ROOT_FOLDER_NAME = "HSCK-motorcycles"

USER = "mathlabroom"
REPO = "huangseck-m3u8"
BRANCH = "main"          
REMOTE_DIR = "E2_Bouquets"
LOCAL_DIR = "/etc/enigma2"
CONFIG_FILE = "/etc/enigma2/github_bouquet_checkbox.conf"  # 勾选记忆文件
SIZE_FILE = "/etc/enigma2/github_bouquet_sizes.conf"       # ✨ 新增：文件大小账本路径

BOUQUET_LIST = [
    ("CK-国产系列", "国产系列", REPO),
    ("CK-骑兵破解", "骑兵破解", REPO),
    ("CK-日本无码", "日本无码", REPO),
    ("CK-日本有码", "日本有码", REPO),
    ("CK-无码中文字幕", "无码中文字幕", REPO),
    ("CK-有码中文字幕", "有码中文字幕", REPO),
    ("CK-欧美高清", "欧美高清", REPO),
    ("CK-动漫", "动漫", REPO),
    ("MT-三级伦理", "三级伦理", "motorcycles"),
    ("MT-中文字幕", "中文字幕", "motorcycles"),
    ("MT-动漫精品", "动漫精品", "motorcycles"),
    ("MT-国产自拍", "国产自拍", "motorcycles"),
    ("MT-强奸乱伦", "强奸乱伦", "motorcycles"),
    ("MT-无码视频", "无码视频", "motorcycles"),
    ("MT-日本AV", "日本AV", "motorcycles"),
    ("MT-有码视频", "有码视频", "motorcycles"),
    ("MT-欧美极品", "欧美极品", "motorcycles"),
    ("MT-男同女同", "男同女同", "motorcycles"),
    ("MT-重口味", "重口味", "motorcycles")
]
# =======================================================================

class GitHubBouquetNestedScreen(Screen, ConfigListScreen):
    skin = """
        <screen name="GitHubBouquetNestedScreen" position="center,center" size="850,550" title="GitHub 嵌套花束自选更新器">
            <widget name="title_label" position="40,20" size="770,35" font="Regular;24" halign="left" transparent="1" foregroundColor="#00ffffff" />
            <widget name="config" position="40,75" size="770,364" itemHeight="52" scrollbarMode="showOnDemand" transparent="0" />
            <eLabel backgroundColor="#00444444" position="40,455" size="770,2" />
            
            <eLabel position="50,475" size="160,36" backgroundColor="#00ff2222" />
            <widget name="key_red" position="50,475" size="160,36" font="Regular;20" halign="center" valign="center" foregroundColor="#00ffffff" transparent="1" zPosition="1" />
            
            <eLabel position="240,475" size="160,36" backgroundColor="#0022ff22" />
            <widget name="key_green" position="240,475" size="160,36" font="Regular;20" halign="center" valign="center" foregroundColor="#00ffffff" transparent="1" zPosition="1" />
            
            <widget name="status" position="420,473" size="380,40" font="Regular;18" halign="right" valign="center" foregroundColor="#00aaaaaa" transparent="1" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        
        self["title_label"] = Label("请使用左右键勾选需要更新的分类:")
        self["key_red"] = Label("取消")
        self["key_green"] = Label("同步选中项")
        self["status"] = Label("按 [绿键] 智能比对大小并同步")
        
        saved_choices = self.load_saved_config()
        self.local_sizes = self.load_local_sizes()  # 加载本地大小记录
        
        self.checkbox_configs = {}
        self.list = []
        
        for idx, item in enumerate(BOUQUET_LIST):
            default_val = saved_choices.get(item[1], True)
            cfg_item = ConfigYesNo(default=default_val)
            self.checkbox_configs[item[1]] = cfg_item
            self.list.append(getConfigListEntry(item[0], cfg_item))
            
        ConfigListScreen.__init__(self, self.list, session=self.session)
        
        self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
            "green": self.start_sync_selected,  
            "ok": self.toggle_current_item,      
            "red": self.close,                   
            "cancel": self.close
        }, -1)

    def toggle_current_item(self):
        current = self["config"].getCurrent()
        if current and current[1]:
            current[1].value = not current[1].value
            self["config"].invalidateCurrent() 

    def load_saved_config(self):
        choices = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and "=" in line:
                            k, v = line.split("=", 1)
                            choices[k] = (v == "True")
            except:
                pass
        return choices

    def save_current_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                for item in BOUQUET_LIST:
                    val = self.checkbox_configs[item[1]].value
                    f.write("%s=%s\n" % (item[1], str(val)))
        except:
            pass

    # ✨ 新增：读取本地大小账本
    def load_local_sizes(self):
        sizes = {}
        if os.path.exists(SIZE_FILE):
            try:
                with open(SIZE_FILE, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and "=" in line:
                            k, v = line.split("=", 1)
                            sizes[k] = int(v)
            except:
                pass
        return sizes

    # ✨ 新增：保存本地大小账本
    def save_local_sizes(self):
        try:
            with open(SIZE_FILE, "w") as f:
                for k, v in self.local_sizes.items():
                    f.write("%s=%d\n" % (k, v))
        except:
            pass

    def get_remote_file_size(self, safe_url):
        """ ✨ 新增：通过 HEAD 请求秒查 GitHub 端文件的字节大小 """
        try:
            req = urllib.request.Request(safe_url, headers={'User-Agent': 'Mozilla/5.0'}, method='HEAD')
            with urllib.request.urlopen(req, timeout=8) as response:
                return int(response.headers.get('Content-Length', 0))
        except:
            return -1

    def start_sync_selected(self):
        self.save_current_config()
        
        selected_items = []
        for item in BOUQUET_LIST:
            if self.checkbox_configs[item[1]].value:
                selected_items.append(item)
                
        if not selected_items:
            self.session.open(MessageBox, "您没有勾选任何分类，请至少选择一项！", MessageBox.TYPE_ERROR)
            return

        self["status"].setText("正在智能核对文件大小...")
        
        success_count = 0
        skip_count = 0
        fail_logs = []
        
        for item in selected_items:
            cat = item[1]
            repo = item[2]
            local_tv_file = os.path.join(LOCAL_DIR, "subbouquet.%s.tv" % cat)
            
            # 生成安全的 GitHub URL
            raw_url = "https://raw.githubusercontent.com/%s/%s/%s/%s/subbouquet.%s.tv.gz" % (
                USER, repo, BRANCH, REMOTE_DIR, cat
            )
            parsed = urllib.parse.urlparse(raw_url)
            encoded_path = urllib.parse.quote(parsed.path)
            safe_url = urllib.parse.urlunparse((
                parsed.scheme, parsed.netloc, encoded_path, parsed.params, parsed.query, parsed.fragment
            ))
            
            # 1. 获取 GitHub 端最新的文件大小
            remote_size = self.get_remote_file_size(safe_url)
            
            # 2. 读取本地账本记录的大小
            local_size_record = self.local_sizes.get(cat, 0)
            
            # 3. 核心智能核对判断
            # 如果本地文件确实躺在 /etc/enigma2 里，且账本大小对得上，且查到了远程大小
            if os.path.exists(local_tv_file) and remote_size > 0 and local_size_record == remote_size:
                skip_count += 1
                continue
                
            # 4. 大小不对或者本地没有，才真正触发网络下载
            success, msg = self.download_gz_file(cat, safe_url, remote_size)
            if success:
                success_count += 1
            else:
                fail_logs.append("%s(%s)" % (item[0], msg))
                
        # 重新持久化大小账本
        self.save_local_sizes()
        
        # 重新生成嵌套主目录
        self.build_nested_structure(selected_items)
        self.refresh_e2_db()
        
        status_msg = "🎉 智能同步完成！下载: %d, 跳过: %d" % (success_count, skip_count)
        self["status"].setText(status_msg)
        
        if fail_logs:
            hint = "同步结束，部分失败:\n%s" % ", ".join(fail_logs)
            self.session.open(MessageBox, hint, MessageBox.TYPE_WARNING)
        else:
            hint_msg = "同步圆满结束！\n真正下载: %d 个更新文件\n智能跳过: %d 个未变动文件" % (success_count, skip_count)
            self.session.open(MessageBox, hint_msg, MessageBox.TYPE_INFO, timeout=5)

    def download_gz_file(self, cat, safe_url, remote_size):
        max_retries = 3
        last_error = "Unknown"
        
        for attempt in range(max_retries):
            try:
                local_path = os.path.join(LOCAL_DIR, "subbouquet.%s.tv" % cat)
                
                req = urllib.request.Request(safe_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=12) as response:
                    compressed_data = response.read()
                
                if not compressed_data:
                    last_error = "Empty"
                    continue
                
                content_bytes = gzip.decompress(compressed_data)
                content_text = content_bytes.decode('utf-8', errors='ignore')
                lines = content_text.splitlines()
                
                fixed_lines = ["#NAME %s" % cat]
                for line in lines:
                    if not line.startswith("#NAME"):
                        fixed_lines.append(line)
                        
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(fixed_lines) + "\n")
                
                try:
                    os.chmod(local_path, 0o644)
                except:
                    pass
                
                # ✨ 下载成功后，把最新的远程大小写入内存账本
                if remote_size > 0:
                    self.local_sizes[cat] = remote_size
                else:
                    # 如果刚才 HEAD 请求失败了但下载成功了，就拿实际下载的数据长度当记录
                    self.local_sizes[cat] = len(compressed_data)
                    
                return True, "OK"
                
            except Exception as e:
                last_error = str(e)
                import time
                time.sleep(1)
                
        return False, last_error

    def build_nested_structure(self, current_active_items):
        root_bouquet_file = os.path.join(LOCAL_DIR, "bouquets.tv")
        root_entry = '#SERVICE 1:7:2:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.github_root_hsck.tv" ORDER BY bouquet\n'
        
        if os.path.exists(root_bouquet_file):
            with open(root_bouquet_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "userbouquet.github_root_hsck.tv" not in content:
                with open(root_bouquet_file, "a", encoding="utf-8") as f:
                    f.write(root_entry)
        
        sub_root_path = os.path.join(LOCAL_DIR, "userbouquet.github_root_hsck.tv")
        with open(sub_root_path, "w", encoding="utf-8") as f:
            f.write("#NAME %s\n" % ROOT_FOLDER_NAME)
            
            for item in BOUQUET_LIST:
                local_file = os.path.join(LOCAL_DIR, "subbouquet.%s.tv" % item[1])
                if item in current_active_items or os.path.exists(local_file):
                    f.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "subbouquet.%s.tv" ORDER BY bouquet\n' % item[1])

    def refresh_e2_db(self):
        try:
            urllib.request.urlopen("http://127.0.0.1/web/servicelistreload?mode=0", timeout=5)
            urllib.request.urlopen("http://127.0.0.1/web/servicelistreload?mode=4", timeout=5)
        except:
            pass

def main(session, **kwargs):
    session.open(GitHubBouquetNestedScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="GitHub 嵌套花束自选更新器",
            description="支持智能大小比对、自选、记忆功能的二级分类器",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="plugin.png",
            fnc=main
        )
    ]
