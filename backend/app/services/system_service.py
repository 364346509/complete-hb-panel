#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统服务
"""

import psutil
import platform
import subprocess
import os
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.system import SystemInfo, SystemMonitor, Process
from app.core.config import settings


class SystemService:
    """系统服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_system_info(self) -> Dict:
        """获取系统基本信息"""
        # 获取系统信息
        uname = platform.uname()
        cpu_info = self._get_cpu_info()
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        info = {
            "hostname": uname.node,
            "os_name": uname.system,
            "os_version": uname.release,
            "kernel_version": uname.version,
            "architecture": uname.machine,
            "cpu_model": cpu_info.get("model", "Unknown"),
            "cpu_cores": psutil.cpu_count(logical=False),
            "total_memory": round(memory_info.total / 1024 / 1024),  # MB
            "total_disk": round(disk_info.total / 1024 / 1024 / 1024),  # GB
            "uptime": int(psutil.boot_time()),
            "load_average": ", ".join([str(x) for x in os.getloadavg()])
        }
        
        # 保存到数据库
        system_info = self.db.query(SystemInfo).first()
        if system_info:
            for key, value in info.items():
                setattr(system_info, key, value)
        else:
            system_info = SystemInfo(**info)
            self.db.add(system_info)
        
        self.db.commit()
        return info
    
    async def get_system_stats(self) -> Dict:
        """获取系统实时统计信息"""
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        
        # 网络流量
        network = psutil.net_io_counters()
        
        # 系统负载
        load_avg = os.getloadavg()
        
        stats = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "network_in": network.bytes_recv,
            "network_out": network.bytes_sent,
            "load_1min": load_avg[0],
            "load_5min": load_avg[1],
            "load_15min": load_avg[2],
            "timestamp": datetime.utcnow()
        }
        
        # 保存监控数据
        monitor = SystemMonitor(**stats)
        self.db.add(monitor)
        self.db.commit()
        
        return stats
    
    async def get_stats_history(self, hours: int = 24) -> List[Dict]:
        """获取历史统计数据"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        stats = self.db.query(SystemMonitor).filter(
            SystemMonitor.timestamp >= start_time
        ).order_by(SystemMonitor.timestamp).all()
        
        return [
            {
                "cpu_usage": stat.cpu_usage,
                "memory_usage": stat.memory_usage,
                "disk_usage": stat.disk_usage,
                "network_in": stat.network_in,
                "network_out": stat.network_out,
                "load_1min": stat.load_1min,
                "load_5min": stat.load_5min,
                "load_15min": stat.load_15min,
                "timestamp": stat.timestamp
            }
            for stat in stats
        ]
    
    async def get_processes(self, limit: int = 50, sort_by: str = "cpu_percent") -> List[Dict]:
        """获取进程列表"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 
                                       'cpu_percent', 'memory_percent', 'memory_info',
                                       'create_time', 'num_threads', 'cmdline']):
            try:
                pinfo = proc.info
                processes.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "cmdline": ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else '',
                    "username": pinfo['username'],
                    "status": pinfo['status'],
                    "cpu_percent": pinfo['cpu_percent'] or 0,
                    "memory_percent": pinfo['memory_percent'] or 0,
                    "memory_rss": pinfo['memory_info'].rss // 1024 if pinfo['memory_info'] else 0,
                    "create_time": datetime.fromtimestamp(pinfo['create_time']),
                    "num_threads": pinfo['num_threads'] or 0
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 排序
        if sort_by in ['cpu_percent', 'memory_percent', 'memory_rss']:
            processes.sort(key=lambda x: x[sort_by], reverse=True)
        
        return processes[:limit]
    
    async def kill_process(self, pid: int) -> bool:
        """终止进程"""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    async def get_disk_usage(self) -> List[Dict]:
        """获取磁盘使用情况"""
        disk_usage = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100
                })
            except PermissionError:
                continue
        
        return disk_usage
    
    async def get_network_interfaces(self) -> List[Dict]:
        """获取网络接口信息"""
        interfaces = []
        
        for interface, addrs in psutil.net_if_addrs().items():
            stats = psutil.net_if_stats().get(interface)
            
            interface_info = {
                "name": interface,
                "is_up": stats.isup if stats else False,
                "speed": stats.speed if stats else 0,
                "addresses": []
            }
            
            for addr in addrs:
                interface_info["addresses"].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
            
            interfaces.append(interface_info)
        
        return interfaces
    
    async def get_system_logs(self, lines: int = 100, level: Optional[str] = None) -> List[str]:
        """获取系统日志"""
        try:
            cmd = ["journalctl", "-n", str(lines), "--no-pager"]
            if level:
                cmd.extend(["-p", level])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.split('\n')
            else:
                return ["无法获取系统日志"]
        except Exception as e:
            return [f"获取日志时出错: {str(e)}"]
    
    def _get_cpu_info(self) -> Dict:
        """获取CPU信息"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        return {"model": line.split(':')[1].strip()}
        except:
            pass
        return {"model": "Unknown"}
