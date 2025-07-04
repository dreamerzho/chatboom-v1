# 文件命名规范检查模块
# 这个模块负责检查文件名是否符合公司规范

import re
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FileNameValidator:
    """
    文件名规范检查器
    负责验证文件名是否符合规范：[YYMMDD]-[项目名]-[工单名/内容描述]-[工作量]-[作者缩写]-[版本号].扩展名
    """
    
    def __init__(self):
        """
        初始化文件名验证器
        """
        # 支持6位、7位、8位日期
        self.pattern = re.compile(
            r'^(\d{6}|\d{7}|\d{8})-([^-]+)-([^-]+)-([^-]+)-([A-Za-z]{2,})-([Vv]\d+)\.([^.]+)$'
        )
        
        # 支持的文件扩展名
        self.supported_extensions = {
            # 设计文件
            'psd', 'ai', 'sketch', 'fig', 'xd',
            # 文档文件
            'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
            # 图片文件
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg',
            # 视频文件
            'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv',
            # 音频文件
            'mp3', 'wav', 'aac', 'flac',
            # 其他文件
            'zip', 'rar', '7z', 'txt', 'rtf'
        }
    
    def validate_filename(self, filename: str) -> Dict[str, any]:
        """
        验证文件名是否符合规范
        参数:
            filename: 要验证的文件名
        返回: 验证结果字典，包含是否合规和解析出的信息
        """
        try:
            # 移除路径，只保留文件名
            clean_filename = filename.split('/')[-1].split('\\')[-1]
            
            # 尝试匹配规范格式
            match = self.pattern.match(clean_filename)
            
            if not match:
                # 检查是否为7位日期，自动修正为8位
                m7 = re.match(r'^(\d{7})-([^-]+)-([^-]+)-([^-]+)-([A-Za-z]{2,})-([Vv]\d+)\.([^.]+)$', clean_filename)
                if m7:
                    date7 = m7.group(1)
                    # 规则：2506027→20250627（前2位为年，后6位为月日）
                    if len(date7) == 7:
                        date8 = '20' + date7[0:2] + date7[2:]
                        fixed_name = clean_filename.replace(date7, date8, 1)
                        match = self.pattern.match(fixed_name)
                        if match:
                            # 自动修正通过，返回修正后的结果
                            date_code, project_name, work_order, workload, author, version, extension = match.groups()
                            return {
                                'is_compliant': True,
                                'filename': fixed_name,
                                'parsed_info': {
                                    'date_code': date8,
                                    'project_name': project_name,
                                    'work_order': work_order,
                                    'workload': workload,
                                    'author_abbreviation': author,
                                    'version': version,
                                    'extension': extension,
                                    'date': self._parse_date_code(date8),
                                    'formatted_date': self._format_date(date8)
                                },
                                'error': None,
                                'suggestion': f'已自动修正7位日期为8位: {fixed_name}'
                            }
                return {
                    'is_compliant': False,
                    'filename': clean_filename,
                    'error': '文件名格式不符合规范（日期字段应为6/7/8位，或其它字段缺失）',
                    'suggestion': self._generate_suggestion(clean_filename)
                }
            
            # 提取各个字段
            date_code, project_name, work_order, workload, author, version, extension = match.groups()
            
            # 放宽合规判定：只要能解析出日期、项目、工单、作者、版本即可
            required_fields = [date_code, project_name, work_order, author, version]
            is_valid = all(required_fields)
            
            return {
                'is_compliant': is_valid,
                'filename': clean_filename,
                'parsed_info': {
                    'date_code': date_code,
                    'project_name': project_name,
                    'work_order': work_order,
                    'workload': workload,
                    'author_abbreviation': author,
                    'version': version,
                    'extension': extension,
                    'date': self._parse_date_code(date_code),
                    'formatted_date': self._format_date(date_code)
                } if is_valid else {},
                'error': None if is_valid else '部分字段缺失',
                'suggestion': None if is_valid else self._generate_suggestion(clean_filename)
            }
                
        except Exception as e:
            logger.error(f"验证文件名失败: {filename}, 错误: {str(e)}")
            return {
                'is_compliant': False,
                'filename': filename,
                'error': f'验证过程出错: {str(e)}',
                'suggestion': '请检查文件名格式'
            }
    
    def _validate_fields(self, date_code: str, project_name: str, work_order: str, 
                        workload: str, author: str, version: str, extension: str) -> Dict[str, any]:
        """
        验证各个字段的格式
        参数:
            date_code: 日期代码 (YYMMDD)
            project_name: 项目名
            work_order: 工单名/内容描述
            workload: 工作量
            author: 作者缩写
            version: 版本号
            extension: 文件扩展名
        返回: 验证结果
        """
        errors = []
        suggestions = []
        
        # 验证日期代码
        if not self._is_valid_date_code(date_code):
            errors.append(f"日期代码 '{date_code}' 格式不正确，应为6位数字 (YYMMDD)或8位数字 (YYYYMMDD)")
            suggestions.append("例如: 240115 表示 2024年1月15日")
        
        # 验证项目名
        if not project_name or len(project_name.strip()) == 0:
            errors.append("项目名不能为空")
            suggestions.append("请输入有效的项目名称")
        
        # 验证工单名/内容描述
        if not work_order or len(work_order.strip()) == 0:
            errors.append("工单名/内容描述不能为空")
            suggestions.append("请输入具体的工作内容描述")
        
        # 验证工作量
        if not self._is_valid_workload(workload):
            errors.append(f"工作量 '{workload}' 格式不正确")
            suggestions.append("格式应为: 数字+单位（P/p/份/稿/张，大小写均可），或纯数字")
        
        # 验证作者缩写
        if not self._is_valid_author_abbreviation(author):
            errors.append(f"作者缩写 '{author}' 格式不正确")
            suggestions.append("应为2-3个英文字母 (如: ZM, LX)")
        
        # 验证版本号
        if not self._is_valid_version(version):
            errors.append(f"版本号 '{version}' 格式不正确")
            suggestions.append("格式应为: v1, V1, v1.0, V1.0, v2, V2, v2.1, V3 等")
        
        # 验证文件扩展名
        if extension.lower() not in self.supported_extensions:
            errors.append(f"不支持的文件扩展名 '{extension}'")
            suggestions.append(f"支持的扩展名: {', '.join(sorted(self.supported_extensions))}")
        
        if errors:
            return {
                'is_valid': False,
                'error': '; '.join(errors),
                'suggestion': '; '.join(suggestions)
            }
        else:
            return {'is_valid': True}
    
    def _is_valid_date_code(self, date_code: str) -> bool:
        """
        验证日期代码格式
        参数:
            date_code: 日期代码 (YYMMDD)
        返回: 是否为有效格式
        """
        if not date_code.isdigit() or len(date_code) not in [6, 8]:
            return False
        
        try:
            if len(date_code) == 6:
                year = int(date_code[:2])
                month = int(date_code[2:4])
                day = int(date_code[4:6])
            else:
                year = int(date_code[:4])
                month = int(date_code[4:6])
                day = int(date_code[6:8])
            
            # 基本范围检查
            if year < 0 or year > 99:
                return False
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            
            # 更严格的日期验证
            full_year = 2000 + year if year < 50 else 1900 + year
            datetime(full_year, month, day)
            return True
            
        except ValueError:
            return False
    
    def _is_valid_workload(self, workload: str) -> bool:
        """
        验证工作量格式
        参数:
            workload: 工作量字符串
        返回: 是否为有效格式
        """
        # 只要有数字即可
        return bool(re.search(r'\d+', workload))
    
    def _is_valid_author_abbreviation(self, author: str) -> bool:
        """
        验证作者缩写格式
        参数:
            author: 作者缩写
        返回: 是否为有效格式
        """
        # 2-3个英文字母，兼容大小写
        return bool(re.match(r'^[A-Za-z]{2,3}$', author))
    
    def _is_valid_version(self, version: str) -> bool:
        """
        验证版本号格式
        参数:
            version: 版本号
        返回: 是否为有效格式
        """
        # v1, V1, v1.0, V1.0, v2, V2, v2.1, V3 等，兼容大小写
        return bool(re.match(r'^[vV]\d+(\.\d+)?$', version))
    
    def _parse_date_code(self, date_code: str) -> Optional[datetime]:
        """
        解析日期代码为datetime对象
        参数:
            date_code: 日期代码 (YYMMDD)
        返回: datetime对象或None
        """
        try:
            if len(date_code) == 6:
                year = int(date_code[:2])
                month = int(date_code[2:4])
                day = int(date_code[4:6])
            else:
                year = int(date_code[:4])
                month = int(date_code[4:6])
                day = int(date_code[6:8])
            
            # 处理年份
            full_year = 2000 + year if year < 50 else 1900 + year
            
            return datetime(full_year, month, day)
        except:
            return None
    
    def _format_date(self, date_code: str) -> str:
        """
        格式化日期代码为可读格式
        参数:
            date_code: 日期代码 (YYMMDD)
        返回: 格式化后的日期字符串
        """
        try:
            date_obj = self._parse_date_code(date_code)
            if date_obj:
                return date_obj.strftime('%Y年%m月%d日')
            else:
                return f"未知日期 ({date_code})"
        except:
            return f"未知日期 ({date_code})"
    
    def _generate_suggestion(self, filename: str) -> str:
        """
        根据当前文件名生成规范建议
        参数:
            filename: 当前文件名
        返回: 建议的规范文件名
        """
        # 移除扩展名
        name_parts = filename.rsplit('.', 1)
        base_name = name_parts[0] if len(name_parts) > 1 else filename
        extension = name_parts[1] if len(name_parts) > 1 else ''
        
        # 尝试从文件名中提取有用信息
        today = datetime.now()
        date_code = today.strftime('%y%m%d')
        
        # 简单的建议格式
        suggestion = f"{date_code}-项目名-工作内容-8h-作者缩写-v1.0"
        
        if extension:
            suggestion += f".{extension}"
        
        return suggestion
    
    def extract_project_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名中提取项目名
        参数:
            filename: 文件名
        返回: 项目名或None
        """
        result = self.validate_filename(filename)
        if result['is_compliant'] and 'parsed_info' in result:
            return result['parsed_info']['project_name']
        return None
    
    def extract_author_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名中提取作者缩写
        参数:
            filename: 文件名
        返回: 作者缩写或None
        """
        result = self.validate_filename(filename)
        if result['is_compliant'] and 'parsed_info' in result:
            return result['parsed_info']['author_abbreviation']
        return None
    
    def get_supported_extensions(self) -> list:
        """
        获取支持的文件扩展名列表
        返回: 扩展名列表
        """
        return sorted(list(self.supported_extensions))

# 使用示例
if __name__ == '__main__':
    validator = FileNameValidator()
    
    # 测试文件名
    test_files = [
        '240115-越城项目-VI设计方案-8h-ZM-v1.0.ai',
        '240115-胤璞项目-网站首页设计-6h-LX-v1.2.psd',
        '设计方案.pdf',  # 不符合规范
        '240115-建杭项目-宣传册制作-12h-WJ-v2.0.indd',
        '修改稿.docx'  # 不符合规范
    ]
    
    for filename in test_files:
        result = validator.validate_filename(filename)
        print(f"文件名: {filename}")
        print(f"结果: {'符合规范' if result['is_compliant'] else '不符合规范'}")
        if result['is_compliant']:
            print(f"解析信息: {result['parsed_info']}")
        else:
            print(f"错误: {result['error']}")
            print(f"建议: {result['suggestion']}")
        print("-" * 50) 