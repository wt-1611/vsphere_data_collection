from pyVim import connect
from pyVmomi import vim,vmodl
import re


#连接和数据中心对象返回
class VMmanager(object):
    def __init__(self, host,user,pwd,port):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.port = port
        self.F = True
        try:
            self.vm_ins = connect.SmartConnectNoSSL(host=host, user=user, port=port, pwd=pwd,connectionPoolTimeout=10)
            self.content= self.vm_ins.RetrieveContent()
            self.result = True

        except:
            self.F = False
            self.mess = "连接错误，请检查账户密码是否正确!!"


    #获取指定类型的所有对象
    def _get_all_obj(self,obj_type,):
        container = self.content.viewManager.CreateContainerView(self.content.rootFolder, obj_type, True)
        return container.view

    #获取所有数据数据中心的对象
    def get_datacenters(self):
        return self._get_all_obj([vim.Datacenter])


    def get_datastore(self,host,ldatastore):

        container={}
        container["关联主机"] = host.name
        stores = host.datastore

        for store in stores:
            storeinfo = store.info
            container["local"] = storeinfo.vmfs.local
            container['存储卷名'] = storeinfo.name
            container['访问URL'] = storeinfo.url
            container['文件系统版本'] = storeinfo.vmfs.version
            container['SSD'] = storeinfo.vmfs.ssd

            storeSummary = store.summary
            container['连接状态'] = storeSummary.accessible
            container['总容量(GiB)'] = round(storeSummary.capacity / (1024*1024*1024),3)
            container['可用容量(GiB)'] = round(storeSummary.freeSpace/ (1024*1024*1024),3)
            container['存储卷类型'] = storeSummary.type
            container['usage'] = round((container['总容量(GiB)']  - container['可用容量(GiB)']) /container['总容量(GiB)'] *100,2)
            ldatastore.append(container)
            container = {}
            container["关联主机"] = host.name

    def get_vm(self,host,lvm):
        container={}
        container["所属主机"] = host.name
        vhosts = host.vm

        for vhost in vhosts:
            config = vhost.config
            container['变更时间'] = config.changeVersion
            container['虚拟机名称'] = config.name
            container['操作系统'] = config.guestFullName
            container['创建时间'] = config.createDate.strftime("%Y-%m-%d %H:%M:%S")

            hardword = config.hardware
            container['虚拟CPU数'] = hardword.numCPU
            container['分配物理内存(MiB)'] = vhost.summary.quickStats.grantedMemory
            D = []
            for divcer in config.datastoreUrl:
                D.append(divcer.name)
                D.append(divcer.url)

            container["存储"] = D
            vconfig = vhost.summary.config
            container['虚拟网卡数'] = vconfig.numEthernetCards
            container['虚拟磁盘数'] = vconfig.numVirtualDisks

            summary =  vhost.summary
            guest = summary.guest
            container['主机名'] = guest.hostName
            container['IP'] = guest.ipAddress



            container['健康状态'] = summary.overallStatus

            stats = summary.quickStats
            container['正常运行时间(day)'] = round(stats.uptimeSeconds /60 /60 /60,2)
            container['使用内存(MiB)'] =  stats.guestMemoryUsage
            container['使用CPU(MHz)'] = stats.overallCpuUsage


            runtime = summary.runtime
            container['电源状态'] = runtime.powerState
            #虚拟机问题通知
            runtime.question

            store = summary.storage
            container['存储使用(GiB)'] = store.committed/ (1024*1024*1024)
            container['存储大小(GiB)'] = store.uncommitted/ (1024*1024*1024)

            nets = vhost.network
            N = []
            for net in nets:
                N.append(net.summary.name)
            container['所属端口组'] = N
            container['健康状态'] = vhost.summary.overallStatus
            container["CPU使用上限(MHz)"] = vhost.summary.runtime.maxCpuUsage
            #lvm[rn] = container
            lvm.append(container)

            container = {}
            container["所属主机"] = host.name




    """
    list:hardw   dict:dic  硬件信息
    list:runtime dict:Run esxi主机运行时
    """
    #esxi对象
    def get_hostsystem(self):
        if not self.F:
            return self.F,self.mess,


        hosts = self._get_all_obj([vim.HostSystem])

        hardw = []
        runtime = []


        ldatastore = []
        lvm = []
        for host in hosts:
            dic = {}
            Run = {}


            #传入存储
            self.get_datastore(host,ldatastore)
            self.get_vm(host,lvm)


            dic["ESXi主机名"] = host.name
            # 硬件信息
            hardware = host.hardware

            # bios信息
            bios = hardware.biosInfo

            dic["厂商"] = bios.vendor
            dic["bios版本"] = bios.biosVersion

            # cpu信息
            Cpu = hardware.cpuInfo

            dic['CPU数'] = Cpu.numCpuPackages
            dic['CPU核数'] = Cpu.numCpuCores
            dic["CPU线程数"] = Cpu.numCpuThreads


            dic["CPU总频率(GHz)"] = round(Cpu.hz / (1000 * 1000 *1000) * Cpu.numCpuCores,3)
            dic['CPU型号'] = hardware.cpuPkg[0].description

            dic['物理内存大小(GiB)'] = round(hardware.memorySize / (1024 * 1024 * 1024),3)

            systeminfo = hardware.systemInfo

            dic["设备型号"] = systeminfo.model

            dic["序列号"] = systeminfo.serialNumber

            #主机运行时
            R = host.runtime
            Run["ESXi主机名"] = host.name
            Run['启动时间'] = R.bootTime.strftime("%Y-%m-%d %H:%M:%S")
            Run["连接状态"] = R.connectionState
            Run["电源状态"] =  R.powerState
            Run['主机状态'] = host.summary.overallStatus


            dic['主机管理IP'] = host.summary.managementServerIp
            dic['系统版本'] = host.summary.config.product.version

            dic['CPU总使用(GHz)'] = host.summary.quickStats.overallCpuUsage /1000
            dic['内存使用(GiB)'] = round(host.summary.quickStats.overallMemoryUsage /1024,2)

            dic['CPU使用率'] = round(dic['CPU总使用(GHz)'] / dic["CPU总频率(GHz)"] *100,2)
            dic['Mem使用率'] = round(dic['内存使用(GiB)'] /dic['物理内存大小(GiB)'] *100,2)

            runtime.append(Run)
            hardw.append(dic)

        return hardw,runtime,ldatastore,lvm






def main(ip,user,pwd,port):


    conn = VMmanager(ip,user,pwd,port)

    esxi = conn.get_hostsystem()

    return esxi
