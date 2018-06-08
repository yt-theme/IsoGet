import os
import re
import urllib.request
import sys
import hashlib
import time
import shutil
# mirrors 配置文件 名称
# 检索到 *.iso 下载链接
down_link = []
global_md5_fasle_delete_file = ''
global_md5FileName_list = ''
########################################
# 日志
def WriteLog(article):
    if not LocalFileCheck('log.log'):
        f_log = open('log.log','a')
        f_log.close()
    # 日期
    f_log = open('log.log','a')
    log_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    f_str = log_time + '\n' + article + '\n\n'
    f_log.write(f_str)
    f_log.close()

# 生成文件
def makeFile(file,content):
    # 判断配置文件是否存在
    file_exist = LocalFileCheck(file)
    # 文件不存在则创建文件
    if not file_exist:
        new_file = open(file,'w')
        # 文件默认内容
        if content:
            new_file.write(content + '\n')
        new_file.close()
        # 写入日志
        WriteLog('文件%s创建完成'%(file))
        print('文件%s创建完成'%(file))
# 创建目录
def makeDir(direction):
    dir_exist = LocalFileCheck(direction)
    if not dir_exist:
        os.makedirs(direction)
        WriteLog('创建目录%s完成'%(direction))
        print('创建目录%s完成'%(direction))
# 按 filename 检测本地 文件 是否存在
def LocalFileCheck(filename):
    # 搜索本地 有无 filename 同名 文件
    if os.path.exists(filename):
        return True
    else:
        return False

# md5 校验
def Md5Check(md5_file):
    # 判断 *.md5文件是否存在
    if LocalFileCheck(md5_file):
        # 按行分析
        md5_file = open(md5_file,'r')
        md5_file_line_arr = md5_file.readlines()
        # 每行按空格分割两部分
        md5_arr_to_dic = {}
        for item in md5_file_line_arr:
            item_left = item.split()[0].strip()
            item_right = item.split()[1].strip()
            md5_arr_to_dic[item_right] = item_left
        # 文件列表全局使用
        global global_md5FileName_list
        global_md5FileName_list = md5_arr_to_dic
        # 检测本地是否有 md5_arr_to_dic 中的文件名 同名文件
        for filename in md5_arr_to_dic:
            # 存在文件进行 md5 分段 校验
            if LocalFileCheck(filename):
                # 写入日志
                WriteLog('正在校验' + filename)
                print('正在校验',filename)
                f_md5 = hashlib.md5()
                with open(filename,"rb") as file_name:
                    while True:
                        data = file_name.read(2048)
                        if not data:
                            break
                        f_md5.update(data)
                iso_md5 = f_md5.hexdigest()
                # 写入日志
                WriteLog('校验值' + iso_md5)
                print('校验值',iso_md5)
                if iso_md5 == md5_arr_to_dic[filename]:
                    # 写入日志
                    WriteLog('校验成功')
                    print('校验成功')
                else:
                    WriteLog('校验失败')
                    print('校验失败')
                    # 需要重新下载
                    global global_md5_fasle_delete_file
                    global_md5_fasle_delete_file = filename
                    return -3
            else:
                WriteLog('文件未全部下载')
                print('文件未全部下载')
                return -2
    else:
        WriteLog('未找到md5文件')
        print('未找到md5文件')
        return -1

# 复制 或 移动文件 mode=1表示复制 mode=0表示移动
def CopyOrMovefile(file,targetDir,mode):
    if mode==1:
        shutil.copy(file,targetDir)
    elif mode==0:
        shutil.move(file,targetDir)

# 执行下载
def Download():
    # 分析已下载完成文件

    # 读取配置文件内容
    WriteLog('开始下载')
    print('开始下载')
    f = open('conget.conf','r')
    read_content = f.readlines()

    # 打开链接
    # 请求头
    ua_headers = {
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'
    }

    # 循环遍历 conget.conf 行执行下载
    url_split = {}
    for url in read_content:
        # 如果检测到空行或注释略过   
        if url == "\n" or url.startswith('#'):
            WriteLog('检测到配置文件空行或注释行')
            print('检测到配置文件空行或注释行')
            continue
        tmp = url.split('~')
        tmp_left = tmp[0].strip()
        tmp_right = tmp[1].strip()
        url_split[tmp_left] = tmp_right
    print('url_split',url_split['debian'])

    request = urllib.request.Request(url_split['debian'],headers=ua_headers)
    open_page = urllib.request.urlopen(request)
    page_text = open_page.read()

    # 将已检索到网页写入文件
    html_content = page_text.decode('utf-8')
    file_test = open('html_content','w')
    file_test.write(html_content)
    file_test.close()

    # 正则匹配 MD5
    re_match_md5 = re.compile('<a href="(MD5SUMS)">')
    html_match_md5 = re_match_md5.findall(html_content)
    # 下载 MD5 文件 重命名为 debian.md5
    md5_curl_cmd = 'curl -C - -L -o debian.md5 ' + str(url_split['debian'].strip()) + str(html_match_md5[0])
    os.system(md5_curl_cmd)
    WriteLog('已生成*.md5')
    print('已生成*.md5')

    # 正则匹配 debian*.iso
    re_match_iso = re.compile('<a href="(debian-.*.iso)">debian-.*</a>')
    html_match_iso = re_match_iso.findall(html_content)

    # 将链接拼接
    #print('已检索到')
    for item in html_match_iso:
        # 去掉换行 xx.strip()
        down_link.append(str(url_split['debian'].strip()) + str(item))
        #print(item)

    # 获取最新iso
    # 使用 curl 多线程下载
    iso_curl_cmd = 'curl -C - -L'
    for item in down_link:
        iso_curl_cmd = iso_curl_cmd + ' -O ' + item
    os.system(iso_curl_cmd)
    # 写入日志
    WriteLog('下载过程结束 校验md5')

    # 检测本地文件 并校验 md5 如果 md5失败
    # 如果本地文件名与远程文件名相同 
    #   则重新执行Download() 再校验 
    #       成功 继续下一项下载或完成
    #       否则删除本地文件重新下载 
    # 否则 直接下载
    md5_result_value = Md5Check('debian.md5')
    if md5_result_value == -3:
        WriteLog('删除此文件重新下载')
        print('删除此文件重新下载')
        os.remove(global_md5_fasle_delete_file)
        Download()
    elif md5_result_value == -1:
        WriteLog('尝试使用重新下载')
        print('尝试使用重新下载')
        Download()
    elif md5_result_value == -2:
        WriteLog('尝试使用重新下载')
        print('尝试使用重新下载')
        Download()
    else:
        # 复制已完成*.iso到iso目录
        # 遍历*.md5文件
        copyFile = open('debian.md5','r')
        copyFileName = copyFile.readlines
        for item in global_md5FileName_list:
            WriteLog("移动%s -> iso目录"%(item))
            print("移动%s -> iso目录"%(item))
            CopyOrMovefile(item,'./iso',0)
########################################
makeDir('iso')
# 默认文件内容
default_content = 'debian~https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/'
makeFile('conget.conf',default_content)
while 1:
    Download()
    time.sleep(909)