# 文件名解析服务
# 这是专家建议的核心解析服务，负责从文件名中提取结构化元数据
# 支持正则表达式解析、错误处理和规范化处理

import re
import json
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class ParsedAssetData:
    """
    解析后的资产数据结构
    用于存储从文件名中提取的所有元数据
    """
    submission_date: date  # 提交日期
    task_identifier: str  # 任务标识符
    author_abbreviation: str  # 作者缩写
    version: int  # 版本号
    workload_amount: Optional[str] = None  # 工作量描述
    project_name: Optional[str] = None  # 项目名称
    work_order: Optional[str] = None  # 工单名/内容描述
    file_extension: Optional[str] = None  # 文件扩展名
    is_compliant: bool = True  # 是否符合命名规范
    parse_errors: List[str] = None  # 解析错误信息

class ParserService:
    """
    文件名解析服务
    负责从文件名中提取结构化元数据，支持多种命名规范
    """
    
    def __init__(self):
        # 主要命名规范：`[YYMMDD]-[项目名]-[工单名/内容描述]-[工作量]-[作者缩写]-[版本号].扩展名`
        self.primary_pattern = re.compile(
            r'^(?P<date>\d{6})-(?P<project>.+?)-(?P<desc>.+?)(?:-(?P<workload>\d+\w*))?-(?P<author>[A-Za-z]{2,})-(?P<version>[Vv]\d+)\.(?P<ext>.+)$'
        )
        
        # 备用命名规范：处理一些变体
        self.alternative_patterns = [
            re.compile(r'^(?P<date>\d{6})-(?P<project>.+?)-(?P<desc>.+?)-(?P<author>[A-Za-z]{2,})-(?P<version>[Vv]\d+)\.(?P<ext>.+)$'),
            re.compile(r'^(?P<date>\d{6})-(?P<project>.+?)-(?P<desc>.+?)(?:-(?P<workload>\d+\w*))?-(?P<author>[A-Za-z]{2,})\.(?P<ext>.+)$'),
            re.compile(r'^(?P<date>\d{6})_(?P<project>.+?)_(?P<desc>.+?)(?:_(?P<workload>\d+\w*))?_(?P<author>[A-Za-z]{2,})_(?P<version>[Vv]\d+)\.(?P<ext>.+)$'),
            re.compile(r'^(?P<date>\d{6})_(?P<project>.+?)_(?P<desc>.+?)_(?P<author>[A-Za-z]{2,})_(?P<version>[Vv]\d+)\.(?P<ext>.+)$'),
            re.compile(r'^(?P<date>\d{6})_(?P<project>.+?)_(?P<desc>.+?)(?:_(?P<workload>\d+\w*))?_(?P<author>[A-Za-z]{2,})\.(?P<ext>.+)$'),
            re.compile(r'^(?P<date>\d{6}) (?P<project>.+?) (?P<desc>.+?)(?: (?P<workload>\d+\w*))? (?P<author>[A-Za-z]{2,}) (?P<version>[Vv]\d+)\.(?P<ext>.+)$'),
        ]
        
        # 工作量转换表
        self.workload_conversion = {
            'p': 1.0,  # 1p = 1个页面
            'P': 1.0,
            '条': 0.5,  # 1条 = 0.5个页面
        }
    
    def parse(self, filename: str) -> Optional[ParsedAssetData]:
        """
        解析文件名，提取结构化元数据
        
        Args:
            filename: 原始文件名
            
        Returns:
            ParsedAssetData: 解析后的数据，如果解析失败返回None
        """
        parse_errors = []
        
        # 预处理：去除首尾空格，统一分隔符
        filename = filename.strip().replace(" ", "-").replace("_", "-")
        
        # 尝试主要命名规范
        match = self.primary_pattern.match(filename)
        if match:
            return self._extract_data_from_match(match, parse_errors)
        
        # 尝试备用命名规范
        for pattern in self.alternative_patterns:
            match = pattern.match(filename)
            if match:
                return self._extract_data_from_match(match, parse_errors)
        
        # 如果所有模式都不匹配，记录错误并返回None
        parse_errors.append(f"文件名 '{filename}' 不符合命名规范")
        return None
    
    def _extract_data_from_match(self, match: re.Match, parse_errors: List[str]) -> ParsedAssetData:
        """
        从正则匹配结果中提取数据
        
        Args:
            match: 正则表达式匹配结果
            parse_errors: 错误信息列表
            
        Returns:
            ParsedAssetData: 解析后的数据
        """
        groups = match.groupdict()
        
        try:
            # 解析日期
            date_str = groups.get('date', '')
            submission_date = self._parse_date(date_str)
            if not submission_date:
                parse_errors.append(f"无法解析日期: {date_str}")
                return None
            
            # 解析版本号
            version_str = groups.get('version', 'V1')
            version = self._parse_version(version_str)
            
            # 构建任务标识符
            project = self._normalize_text(groups.get('project', '').strip())
            desc = self._normalize_text(groups.get('desc', '').strip())
            task_identifier = f"{project}-{desc}" if project and desc else desc
            
            # 解析工作量
            workload_amount = groups.get('workload')
            if workload_amount:
                workload_amount = self._normalize_workload(workload_amount)
            
            # 归一化作者缩写
            author_abbreviation = self._normalize_text(groups.get('author', '').strip()).upper()
            
            # 文件类型归类逻辑
            ext = groups.get('ext', '').lower()
            filename = match.string.lower()
            # 如果是压缩包，优先检查文件名中是否有psd/png/jpg等关键词
            if ext in ['zip', 'rar', '7z']:
                for t in ['psd', 'png', 'jpg', 'jpeg', 'ai']:
                    if t in filename:
                        ext = t
                        break
            
            return ParsedAssetData(
                submission_date=submission_date,
                task_identifier=task_identifier,
                author_abbreviation=author_abbreviation,
                version=version,
                workload_amount=workload_amount,
                project_name=project,
                work_order=desc,
                file_extension=ext,
                is_compliant=True,
                parse_errors=parse_errors
            )
            
        except Exception as e:
            parse_errors.append(f"解析过程中发生错误: {str(e)}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """
        解析日期字符串 (YYMMDD 格式)
        
        Args:
            date_str: 日期字符串，格式为 YYMMDD
            
        Returns:
            date: 解析后的日期对象
        """
        if not date_str or len(date_str) != 6:
            return None
        
        try:
            year = int('20' + date_str[:2])  # 假设是21世纪
            month = int(date_str[2:4])
            day = int(date_str[4:6])
            
            return date(year, month, day)
        except ValueError:
            return None
    
    def _parse_version(self, version_str: str) -> int:
        """
        解析版本号
        
        Args:
            version_str: 版本字符串，如 "V1", "V2"
            
        Returns:
            int: 版本号
        """
        if not version_str:
            return 1
        
        # 提取数字部分
        version_match = re.search(r'V?(\d+)', version_str)
        if version_match:
            return int(version_match.group(1))
        
        return 1
    
    def _normalize_workload(self, workload_str: str) -> str:
        """
        标准化工作量描述
        
        Args:
            workload_str: 原始工作量字符串
            
        Returns:
            str: 标准化后的工作量字符串
        """
        if not workload_str:
            return None
        
        # 只保留数字部分
        import re
        match = re.match(r'(\d+)', workload_str)
        if match:
            return match.group(1)
        return workload_str
    
    def calculate_workload_equivalent(self, workload_amount: str) -> Optional[float]:
        """
        计算工作量当量 (WE)
        
        Args:
            workload_amount: 工作量描述，如 "3p", "5条"
            
        Returns:
            float: 工作量当量
        """
        if not workload_amount:
            return None
        
        match = re.match(r'(\d+)([pP条])', workload_amount)
        if match:
            number = int(match.group(1))
            unit = match.group(2)
            conversion_rate = self.workload_conversion.get(unit, 1.0)
            return number * conversion_rate
        
        return None
    
    def validate_filename(self, filename: str) -> Dict[str, Any]:
        """
        验证文件名是否符合规范
        
        Args:
            filename: 文件名
            
        Returns:
            Dict: 验证结果
        """
        parsed_data = self.parse(filename)
        
        if parsed_data is None:
            return {
                'is_valid': False,
                'errors': ['文件名不符合命名规范'],
                'suggestions': [
                    '请使用格式: [YYMMDD]-[项目名]-[工单名/内容描述]-[工作量]-[作者缩写]-[版本号].扩展名',
                    '示例: 250123-金陵中環-热销系列海报-3p-ZY-V1.psd'
                ]
            }
        
        # 放宽合规判定：只要能解析出日期、项目、工单、作者、版本即可
        required_fields = [parsed_data.submission_date, parsed_data.project_name, parsed_data.work_order, parsed_data.author_abbreviation, parsed_data.version]
        is_valid = all(required_fields)
        return {
            'is_valid': is_valid,
            'parsed_data': parsed_data.__dict__,
            'errors': [] if is_valid else ['部分字段缺失']
        }
    
    def generate_task_group_id(self, project_name: str, task_identifier: str, author_abbreviation: str) -> str:
        """
        生成任务组ID，用于关联同一任务的多个版本
        
        Args:
            project_name: 项目名称
            task_identifier: 任务标识符
            author_abbreviation: 作者缩写
            
        Returns:
            str: 任务组ID
        """
        # 使用项目名、任务标识符和作者缩写的组合生成唯一ID
        components = [project_name, task_identifier, author_abbreviation]
        clean_components = [re.sub(r'[^a-zA-Z0-9]', '', comp) for comp in components if comp]
        return '_'.join(clean_components).lower()
    
    def batch_parse(self, filenames: List[str]) -> Dict[str, Any]:
        """
        批量解析文件名，并统计归类分布和异常情况
        """
        results = {
            'total': len(filenames),
            'successful': 0,
            'failed': 0,
            'parsed_data': [],
            'errors': [],
            'project_distribution': {},
            'author_distribution': {},
            'compliant_count': 0,
            'non_compliant_count': 0,
            'error_types': {}
        }
        for filename in filenames:
            parsed_data = self.parse(filename)
            if parsed_data:
                results['successful'] += 1
                results['parsed_data'].append({
                    'filename': filename,
                    'data': parsed_data.__dict__
                })
                # 统计项目分布
                project = parsed_data.project_name or '未知'
                results['project_distribution'][project] = results['project_distribution'].get(project, 0) + 1
                # 统计作者分布
                author = parsed_data.author_abbreviation or '未知'
                results['author_distribution'][author] = results['author_distribution'].get(author, 0) + 1
                # 合规统计
                if parsed_data.is_compliant:
                    results['compliant_count'] += 1
                else:
                    results['non_compliant_count'] += 1
            else:
                results['failed'] += 1
                error_msg = '解析失败'
                results['errors'].append({
                    'filename': filename,
                    'error': error_msg
                })
                # 统计错误类型
                results['error_types'][error_msg] = results['error_types'].get(error_msg, 0) + 1
        return results

    def _normalize_text(self, text: str) -> str:
        """
        归一化文本：去除空格、统一大小写、常见别名映射
        """
        if not text:
            return ''
        # 去除空格、特殊字符
        text = text.replace(' ', '').replace('_', '').replace('-', '').lower()
        # 常见别名映射
        alias_map = {
            '金陵中環': '金陵中环',
            '金陵中环': '金陵中环',
            'jinlingzhonghuan': '金陵中环',
            # 可扩展更多别名
        }
        return alias_map.get(text, text) 