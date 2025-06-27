# 核心分析服务
# 这是专家建议的核心分析服务，负责实现 WE 计算、负荷指数、项目健康度等核心模型
# 这是项目最关键的价值所在

import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload

from backend.db import db
from models.asset import Asset, AssetAnalysis
from models.employee import EmployeeMapping
from models.project import Project
from parser_service import ParserService
from models import AnalysisConfig

class AnalysisService:
    """
    核心分析服务
    负责实现《精准评估模型 (V2)》中的所有核心计算逻辑
    包括工作量当量计算、负荷指数、项目健康度评估等
    """
    
    def __init__(self):
        self.parser_service = ParserService()
        
        # 工作量当量 (WE) 转换权重
        self.workload_weights = {
            'design': {
                'psd': 1.0,      # Photoshop 设计稿
                'ai': 1.2,       # Illustrator 矢量图
                'sketch': 0.8,   # Sketch 设计稿
                'figma': 0.9,    # Figma 设计稿
                'xd': 0.9,       # Adobe XD
            },
            'copywriting': {
                'doc': 0.5,      # Word 文档
                'docx': 0.5,
                'txt': 0.3,      # 纯文本
                'md': 0.4,       # Markdown
            },
            'video': {
                'mp4': 2.0,      # 视频文件
                'mov': 2.0,
                'avi': 1.8,
                'prproj': 3.0,   # Premiere 项目
            },
            'other': {
                'pdf': 0.3,      # PDF 文档
                'zip': 0.1,      # 压缩包
                'rar': 0.1,
            }
        }
        
        # 负荷指数计算权重
        self.load_weights = {
            'output_we': 0.6,    # 产出WE权重
            'process_we': 0.4,   # 过程成本WE权重
        }
        
        # 项目健康度评估阈值
        self.health_thresholds = {
            'excellent': 85,     # 优秀
            'good': 70,          # 良好
            'warning': 50,       # 预警
            'risk': 30,          # 风险
        }
    
    def calculate_workload_equivalent(self, asset: Asset) -> float:
        """
        计算单个资产的工作量当量 (WE)
        
        Args:
            asset: 资产对象
            
        Returns:
            float: 工作量当量
        """
        # 基础WE：从文件名解析的工作量
        base_we = 0.0
        if asset.workload_amount:
            base_we = self.parser_service.calculate_workload_equivalent(asset.workload_amount)
        
        # 文件类型权重调整
        file_type_weight = self._get_file_type_weight(asset.file_extension, asset.file_category)
        
        # 版本复杂度调整
        version_complexity = self._calculate_version_complexity(asset)
        
        # 最终WE = 基础WE × 文件类型权重 × 版本复杂度
        final_we = base_we * file_type_weight * version_complexity
        
        return round(final_we, 2)
    
    def _get_file_type_weight(self, file_extension: str, file_category: str) -> float:
        """获取文件类型权重"""
        if not file_extension:
            return 1.0
        
        # 根据文件分类选择权重表
        category_weights = self.workload_weights.get(file_category.lower(), self.workload_weights['other'])
        
        # 获取具体文件类型权重
        weight = category_weights.get(file_extension.lower(), 1.0)
        
        return weight
    
    def _calculate_version_complexity(self, asset: Asset) -> float:
        """计算版本复杂度"""
        if asset.version <= 1:
            return 1.0
        
        # 版本越高，复杂度越高，但增长逐渐放缓
        complexity = 1.0 + (asset.version - 1) * 0.3
        return min(complexity, 2.0)  # 最大不超过2倍
    
    def calculate_employee_load_index(self, employee_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        计算员工负荷指数
        
        Args:
            employee_id: 员工ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict: 包含各种负荷指数的字典
        """
        # 获取员工在指定时间段内的所有资产
        assets = Asset.query.filter(
            and_(
                Asset.author_id == employee_id,
                Asset.submission_date >= start_date,
                Asset.submission_date <= end_date
            )
        ).all()
        
        # 计算产出WE
        output_we = sum(asset.workload_equivalent or 0 for asset in assets)
        
        # 计算过程成本WE（基于迭代次数）
        process_we = self._calculate_process_we(assets)
        
        # 计算总负荷指数
        total_load_index = (
            output_we * self.load_weights['output_we'] +
            process_we * self.load_weights['process_we']
        )
        
        # 计算平均迭代次数
        avg_iterations = self._calculate_average_iterations(assets)
        
        # 计算效率评分
        efficiency_score = self._calculate_efficiency_score(output_we, process_we, avg_iterations)
        
        return {
            'output_we': round(output_we, 2),
            'process_we': round(process_we, 2),
            'total_load_index': round(total_load_index, 2),
            'avg_iterations': round(avg_iterations, 1),
            'efficiency_score': round(efficiency_score, 1),
            'asset_count': len(assets),
            'final_version_count': sum(1 for asset in assets if asset.is_final_version)
        }
    
    def _calculate_process_we(self, assets: List[Asset]) -> float:
        """计算过程成本WE"""
        process_we = 0.0
        
        for asset in assets:
            # 每个版本都产生过程成本
            version_cost = 0.5  # 基础版本成本
            
            # 迭代次数越多，过程成本越高
            if asset.version > 1:
                version_cost += (asset.version - 1) * 0.3
            
            process_we += version_cost
        
        return process_we
    
    def _calculate_average_iterations(self, assets: List[Asset]) -> float:
        """计算平均迭代次数"""
        if not assets:
            return 0.0
        
        total_iterations = sum(asset.version for asset in assets)
        return total_iterations / len(assets)
    
    def _calculate_efficiency_score(self, output_we: float, process_we: float, avg_iterations: float) -> float:
        """计算效率评分"""
        if output_we == 0:
            return 0.0
        
        # 效率 = 产出WE / (产出WE + 过程成本WE)
        efficiency_ratio = output_we / (output_we + process_we)
        
        # 迭代次数惩罚
        iteration_penalty = max(0, (avg_iterations - 2) * 0.1)
        
        # 最终效率评分
        efficiency_score = (efficiency_ratio * 100) - (iteration_penalty * 100)
        
        return max(0, min(100, efficiency_score))
    
    def calculate_project_health_score(self, project_id: int) -> Dict[str, Any]:
        """
        计算项目健康度评分
        
        Args:
            project_id: 项目ID
            
        Returns:
            Dict: 项目健康度评估结果
        """
        # 获取项目信息
        project = Project.query.get(project_id)
        if not project:
            return None
        
        # 获取项目资产
        assets = Asset.query.filter(Asset.project_id == project_id).all()
        
        if not assets:
            return {
                'health_score': 100.0,
                'risk_level': 'low',
                'efficiency_score': 100.0,
                'quality_score': 100.0,
                'risk_factors': [],
                'recommendations': [],
                'weData': [],
                'total_we': 0.0
            }
        
        # 计算各项指标
        efficiency_score = self._calculate_project_efficiency(assets)
        quality_score = self._calculate_project_quality(assets)
        
        # 综合健康度评分
        health_score = (efficiency_score * 0.6) + (quality_score * 0.4)
        
        # 确定风险等级
        risk_level = self._determine_risk_level(health_score)
        
        # 识别风险因素
        risk_factors = self._identify_risk_factors(assets, efficiency_score, quality_score)
        
        # 生成改进建议
        recommendations = self._generate_recommendations(risk_factors, health_score)
        
        weData = [{'id': asset.id, 'we': asset.workload_equivalent or 0, 'author': asset.author_id, 'date': asset.submission_date.isoformat() if asset.submission_date else ''} for asset in assets]
        
        return {
            'health_score': round(health_score, 1),
            'risk_level': risk_level,
            'efficiency_score': round(efficiency_score, 1),
            'quality_score': round(quality_score, 1),
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'asset_count': len(assets),
            'total_we': sum(asset.workload_equivalent or 0 for asset in assets),
            'weData': weData
        }
    
    def _calculate_project_efficiency(self, assets: List[Asset]) -> float:
        """计算项目效率评分"""
        if not assets:
            return 100.0
        
        total_output_we = sum(asset.workload_equivalent or 0 for asset in assets)
        total_process_we = self._calculate_process_we(assets)
        
        if total_output_we == 0:
            return 0.0
        
        efficiency_ratio = total_output_we / (total_output_we + total_process_we)
        return efficiency_ratio * 100
    
    def _calculate_project_quality(self, assets: List[Asset]) -> float:
        """计算项目质量评分"""
        if not assets:
            return 100.0
        
        # 基于最终版本比例和平均迭代次数计算质量
        final_versions = [asset for asset in assets if asset.is_final_version]
        final_version_ratio = len(final_versions) / len(assets)
        
        avg_iterations = self._calculate_average_iterations(assets)
        
        # 质量评分 = 最终版本比例 * 70 + 迭代次数评分 * 30
        iteration_score = max(0, 100 - (avg_iterations - 2) * 20)
        quality_score = (final_version_ratio * 70) + (iteration_score * 0.3)
        
        return min(100, quality_score)
    
    def _determine_risk_level(self, health_score: float) -> str:
        """确定风险等级"""
        if health_score >= self.health_thresholds['excellent']:
            return 'excellent'
        elif health_score >= self.health_thresholds['good']:
            return 'good'
        elif health_score >= self.health_thresholds['warning']:
            return 'warning'
        elif health_score >= self.health_thresholds['risk']:
            return 'risk'
        else:
            return 'critical'
    
    def _identify_risk_factors(self, assets: List[Asset], efficiency_score: float, quality_score: float) -> List[str]:
        """识别风险因素"""
        risk_factors = []
        
        # 效率风险
        if efficiency_score < 60:
            risk_factors.append('项目效率偏低，返工成本较高')
        
        # 质量风险
        if quality_score < 60:
            risk_factors.append('项目质量不达标，最终版本比例较低')
        
        # 迭代风险
        avg_iterations = self._calculate_average_iterations(assets)
        if avg_iterations > 4:
            risk_factors.append(f'平均迭代次数过高({avg_iterations:.1f}次)，可能存在需求不明确问题')
        
        # 进度风险
        if len(assets) > 0:
            recent_assets = [a for a in assets if a.submission_date >= date.today() - timedelta(days=7)]
            if len(recent_assets) == 0:
                risk_factors.append('项目近期无新交付，可能存在进度风险')
        
        return risk_factors
    
    def _generate_recommendations(self, risk_factors: List[str], health_score: float) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if '项目效率偏低' in str(risk_factors):
            recommendations.append('建议优化工作流程，减少不必要的返工')
        
        if '项目质量不达标' in str(risk_factors):
            recommendations.append('建议加强需求沟通，提高交付质量')
        
        if '平均迭代次数过高' in str(risk_factors):
            recommendations.append('建议在项目开始前明确需求，减少后期修改')
        
        if '项目近期无新交付' in str(risk_factors):
            recommendations.append('建议检查项目进度，及时调整资源分配')
        
        if health_score < 50:
            recommendations.append('建议召开项目复盘会议，分析问题根源')
        
        return recommendations
    
    def get_dashboard_kpis(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        获取仪表盘核心KPI指标
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict: KPI指标数据
        """
        # 获取时间范围内的所有资产
        assets = Asset.query.filter(
            and_(
                Asset.submission_date >= start_date,
                Asset.submission_date <= end_date
            )
        ).all()
        
        # 计算团队负荷状态
        team_load = self._calculate_team_load_status(assets)
        
        # 计算项目健康度分布
        project_health = self._calculate_project_health_distribution(start_date, end_date)
        
        # 计算待处理风险数量
        pending_risks = self._count_pending_risks()
        
        # 计算平均定稿周期
        avg_finalize_hours = self._calculate_average_finalize_hours(assets)
        
        return {
            'team_load': team_load,
            'project_health': project_health,
            'pending_risks': pending_risks,
            'avg_finalize_hours': avg_finalize_hours
        }
    
    def _calculate_team_load_status(self, assets: List[Asset]) -> Dict[str, int]:
        """计算团队负荷状态分布"""
        # 按员工分组计算负荷指数
        employee_loads = {}
        
        for asset in assets:
            if asset.author_id not in employee_loads:
                employee_loads[asset.author_id] = 0
            employee_loads[asset.author_id] += asset.workload_equivalent or 0
        
        # 根据负荷指数分类
        high_load = sum(1 for load in employee_loads.values() if load > 20)
        medium_load = sum(1 for load in employee_loads.values() if 10 <= load <= 20)
        low_load = sum(1 for load in employee_loads.values() if load < 10)
        
        return {
            'high': high_load,
            'medium': medium_load,
            'low': low_load
        }
    
    def _calculate_project_health_distribution(self, start_date: date, end_date: date) -> Dict[str, int]:
        """计算项目健康度分布"""
        # 获取所有活跃项目
        projects = Project.query.filter(Project.status == 'active').all()
        
        healthy = 0
        warning = 0
        risk = 0
        
        for project in projects:
            health_data = self.calculate_project_health_score(project.id)
            if health_data:
                if health_data['health_score'] >= 70:
                    healthy += 1
                elif health_data['health_score'] >= 50:
                    warning += 1
                else:
                    risk += 1
        
        return {
            'healthy': healthy,
            'warning': warning,
            'risk': risk
        }
    
    def _count_pending_risks(self) -> int:
        """统计待处理风险数量"""
        # 这里可以集成风险事件系统
        # 暂时返回模拟数据
        return 7
    
    def _calculate_average_finalize_hours(self, assets: List[Asset]) -> Dict[str, Any]:
        """计算平均定稿周期"""
        final_assets = [asset for asset in assets if asset.is_final_version and asset.time_to_final]
        
        if not final_assets:
            return {
                'value': 0,
                'change': 0,
                'trend': []
            }
        
        avg_hours = sum(asset.time_to_final for asset in final_assets) / len(final_assets)
        
        # 计算趋势（简化版本）
        trend = [12, 15, 13, 18, 16, 20, 19]  # 模拟数据
        
        return {
            'value': round(avg_hours, 1),
            'change': -0.05,  # 模拟数据
            'trend': trend
        }
    
    def calculate_workload_equivalent_from_parsed_data(self, parsed_data) -> float:
        """
        根据解析数据计算工作量当量 (WE)
        
        Args:
            parsed_data: ParserService解析后的数据对象
            
        Returns:
            float: 工作量当量
        """
        # 基础WE：从工作量描述计算
        base_we = 0.0
        if parsed_data.workload_amount:
            base_we = self._parse_workload_amount(parsed_data.workload_amount)
        
        # 文件类型权重调整
        file_type_weight = self._get_file_type_weight(parsed_data.file_extension, 'other')
        
        # 版本复杂度调整
        version_complexity = 1.0 + (parsed_data.version - 1) * 0.3
        version_complexity = min(version_complexity, 2.0)  # 最大不超过2倍
        
        # 最终WE = 基础WE × 文件类型权重 × 版本复杂度
        final_we = base_we * file_type_weight * version_complexity
        
        return round(final_we, 2)
    
    def _parse_workload_amount(self, workload_str: str) -> float:
        """
        解析工作量描述，转换为WE值
        
        Args:
            workload_str: 工作量字符串，如 "2p", "3条"
            
        Returns:
            float: WE值
        """
        if not workload_str:
            return 1.0  # 默认值
        
        # 处理数字+单位的格式
        import re
        match = re.match(r'(\d+)([pP条])', workload_str)
        if match:
            number = int(match.group(1))
            unit = match.group(2)
            
            # 根据单位转换
            if unit.lower() == 'p':
                return float(number)  # 1p = 1WE
            elif unit == '条':
                return float(number) * 0.5  # 1条 = 0.5WE
        
        # 如果无法解析，尝试直接转换为数字
        try:
            return float(workload_str)
        except ValueError:
            return 1.0  # 默认值
    
    def calculate_employee_baseline(self, employee_id: int) -> Dict[str, Any]:
        """
        计算员工个人能力基线（历史平均迭代次数）
        Args:
            employee_id: 员工ID
        Returns:
            Dict: {avg_iterations, total_projects, total_assets}
        """
        # 获取该员工所有资产
        assets = Asset.query.filter(Asset.author_id == employee_id).all()
        if not assets:
            return {
                'avg_iterations': 0.0,
                'total_projects': 0,
                'total_assets': 0
            }
        # 统计参与项目数
        project_ids = set(asset.project_id for asset in assets if asset.project_id)
        # 统计平均迭代次数
        avg_iterations = sum(asset.version for asset in assets) / len(assets)
        return {
            'avg_iterations': round(avg_iterations, 2),
            'total_projects': len(project_ids),
            'total_assets': len(assets)
        }
    
    def smart_rework_attribution(self, employee_id: int, project_id: int) -> Dict[str, Any]:
        """
        智能返工归因：对比员工在当前项目的迭代次数与其个人能力基线，自动标记归因标签
        Args:
            employee_id: 员工ID
            project_id: 项目ID
        Returns:
            Dict: {current_avg_iterations, personal_baseline, attribution, detail}
        """
        # 1. 计算个人能力基线
        baseline = self.calculate_employee_baseline(employee_id)
        personal_avg = baseline['avg_iterations']
        # 2. 统计该员工在当前项目的平均迭代次数
        assets = Asset.query.filter(Asset.author_id == employee_id, Asset.project_id == project_id).all()
        if not assets:
            return {
                'current_avg_iterations': 0.0,
                'personal_baseline': personal_avg,
                'attribution': '无数据',
                'detail': '该员工在本项目无产出记录'
            }
        current_avg = sum(asset.version for asset in assets) / len(assets)
        # 3. 归因判断（动态参数）
        rework_warning_delta = self.get_param('rework_warning_delta', default=1.0, as_type=float)
        high_baseline_threshold = self.get_param('high_baseline_threshold', default=4.0, as_type=float)
        if current_avg > personal_avg + rework_warning_delta and personal_avg > 0:
            attribution = '项目难度预警'
            detail = f'本项目平均迭代次数({current_avg:.2f})远高于个人基线({personal_avg:.2f})，说明项目难度较高或客户要求高。'
        elif personal_avg > high_baseline_threshold:
            attribution = '技能错配'
            detail = f'员工个人基线({personal_avg:.2f})远高于团队平均，建议关注技能匹配。'
        else:
            attribution = '正常'
            detail = f'本项目迭代次数({current_avg:.2f})与个人基线({personal_avg:.2f})接近，表现正常。'
        return {
            'current_avg_iterations': round(current_avg, 2),
            'personal_baseline': round(personal_avg, 2),
            'attribution': attribution,
            'detail': detail
        }
    
    def get_param(self, key, default=None, as_type=float):
        """从AnalysisConfig表动态读取参数，找不到则用默认值"""
        config = AnalysisConfig.query.filter_by(key=key).first()
        if config:
            try:
                return as_type(config.value)
            except Exception:
                return config.value
        return default 