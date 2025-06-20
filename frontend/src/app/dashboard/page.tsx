<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>服务监测系统</title>
    <!-- 引入 Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- 引入 Chart.js 用于图表渲染 -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- 引入 Google Fonts 优化字体显示 -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap" rel="stylesheet">
    <style>
        /* 使用更美观的字体和滚动条样式 */
        body { font-family: 'Inter', sans-serif; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #f1f5f9; }
        ::-webkit-scrollbar-thumb { background: #94a3b8; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body class="bg-slate-50 font-sans text-slate-800">

    <div id="app-container" class="flex min-h-screen">
        <!-- 左侧导航栏 -->
        <aside class="w-64 bg-slate-900 text-slate-200 flex-col flex-shrink-0 hidden lg:flex">
            <div class="p-6 text-2xl font-bold text-white border-b border-slate-700 h-20 flex items-center">
                <span>服务监测系统</span>
            </div>
            <nav class="flex-1 px-4 py-6 space-y-2">
                <a href="#" class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-slate-700 text-white">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7"height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
                    <span class="font-medium">数据概览</span>
                </a>
                <a href="#" class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-800">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                    <span class="font-medium">员工视图</span>
                </a>
            </nav>
        </aside>

        <!-- 右侧主内容区 -->
        <main class="flex-1 overflow-y-auto">
            <header class="px-8 h-20 bg-white/80 backdrop-blur-sm border-b border-slate-200 flex justify-between items-center sticky top-0 z-10">
                <h1 class="text-2xl font-semibold text-slate-900">数据概览</h1>
                <div class="flex items-center space-x-4">
                    <span class="text-sm font-medium text-slate-500">最近7天</span>
                    <div class="w-10 h-10 bg-slate-200 rounded-full flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-lg text-slate-500"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    </div>
                </div>
            </header>

            <!-- 主内容区 -->
            <div class="p-8">
                <!-- KPI 卡片容器 -->
                <div id="kpi-cards-container"></div>
                
                <!-- 中部图表和风险流 -->
                <div class="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm h-96">
                        <canvas id="workloadChart"></canvas>
                    </div>
                    <div id="risk-feed-container" class="lg:col-span-1"></div>
                </div>

                <!-- 底部表格 -->
                <div class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6" style="height: 340px;">
                    <div id="team-performance-container"></div>
                    <div id="project-risk-container"></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        // ===================================================================
        // 数据
        // ===================================================================
        const mockData = {
          kpi: { load: { high: 3, mid: 75, low: 9 }, projectHealth: { healthy: 1, warning: 1, risk: 1 }, riskCount: 7, avgFinalHours: 48.5, avgFinalHoursChange: -5, },
          workloadChart: { labels: ['06-13', '06-14', '06-15', '06-16', '06-17', '06-18', '06-19'], totalWE: [25, 30, 28, 35, 45, 42, 50], processWE: [5, 8, 7, 10, 15, 12, 18] },
          riskFeed: [ { id: 1, type: 'danger', project: 'SKP项目', desc: '主视觉海报已迭代8次', time: '2小时前' }, { id: 2, type: 'warning', project: '越城天地', desc: '内部群提及"又要改"', time: '5小时前' }, { id: 3, type: 'danger', project: '王五', desc: '在【SKP项目】的迭代次数高于其个人基线70%', time: '1天前' } ],
          teamPerformance: { designers: [ { id: 'd1', name: '张三', we: 12.5, process: 3.2, avgIter: 2.1 }, { id: 'd2', name: '王五', we: 8.0, process: 2.5, avgIter: 5.8 } ], copywriters: [ { id: 'c1', name: '李四', we: 12.1, avgIter: 3.5 } ], pmae: [ { id: 'p1', name: '赵六', commWE: 9.8, flowWE: 1.2 } ] },
          projectRisk: [ { id: 'p1', name: 'SKP项目', score: 45, risk: '迭代次数过高', color: 'text-red-500' }, { id: 'p2', name: '越城天地', score: 68, risk: '定稿周期长', color: 'text-yellow-500' }, { id: 'p3', name: '金陵中环', score: 92, risk: '-', color: 'text-green-600' } ]
        };

        // ===================================================================
        // 等待DOM加载完毕后执行
        // ===================================================================
        document.addEventListener('DOMContentLoaded', () => {
            renderAllComponents();
            setupTabs();
        });

        // ===================================================================
        // 组件渲染函数
        // ===================================================================
        function renderAllComponents() {
            // 渲染 KPI 卡片
            const kpiContainer = document.getElementById('kpi-cards-container');
            const kpiData = mockData.kpi;
            kpiContainer.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    ${createKpiCard(
                        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-6 w-6 text-indigo-500"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>', 
                        "团队负荷状态", 
                        '<span class="text-red-500">${kpiData.load.high}</span><span class="text-slate-300">/</span><span class="text-yellow-500">${kpiData.load.mid}</span><span class="text-slate-300">/</span><span class="text-green-500">${kpiData.load.low}</span>',
                        "高 / 中 / 低"
                    )}
                    ${createKpiCard(
                        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-6 w-6 text-green-500"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>',
                        "项目健康度",
                        '<span class="text-green-500">${kpiData.projectHealth.healthy}</span><span class="text-slate-300">/</span><span class="text-yellow-500">${kpiData.projectHealth.warning}</span><span class="text-slate-300">/</span><span class="text-red-500">${kpiData.projectHealth.risk}</span>',
                        "健康 / 预警 / 风险"
                    )}
                    ${createKpiCard(
                        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-6 w-6 text-yellow-500"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
                        "待处理风险",
                        kpiData.riskCount,
                        "个高优先级事项"
                    )}
                     ${createKpiCard(
                        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-6 w-6 text-blue-500"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
                        "平均定稿周期",
                        '${kpiData.avgFinalHours} <span class="text-xl">小时</span>',
                        '比上周 <span class="text-green-500">${kpiData.avgFinalHoursChange}%</span>'
                    )}
                </div>
            `;

            // 渲染风险流
            const riskContainer = document.getElementById('risk-feed-container');
            riskContainer.innerHTML = `
                <div class="bg-white p-6 rounded-xl shadow-sm h-96 flex flex-col">
                    <h3 class="text-lg font-semibold text-slate-800 mb-4 flex-shrink-0">实时风险流</h3>
                    <div class="space-y-5 overflow-y-auto flex-grow pr-2 -mr-2">
                        ${mockData.riskFeed.map(item => `
                            <div class="flex items-start">
                                <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mr-4 bg-opacity-10 ${item.type === 'danger' ? 'bg-red-100' : 'bg-yellow-100'}">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-5 w-5 ${item.type === 'danger' ? 'text-red-500' : 'text-yellow-500'}"><path d="m21.73 18-8-14a2 2 0 0 0-3.46 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
                                </div>
                                <div>
                                    <p class="text-sm font-medium text-slate-700 leading-tight">【${item.project}】${item.desc}</p>
                                    <p class="text-xs text-slate-400 mt-1">${item.time}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

            // 渲染项目风险榜
            const projectRiskContainer = document.getElementById('project-risk-container');
            projectRiskContainer.innerHTML = `
                 <div class="bg-white p-6 rounded-xl shadow-sm h-full flex flex-col">
                    <h3 class="text-lg font-semibold text-slate-800 mb-4 flex-shrink-0">项目风险榜</h3>
                    <div class="relative overflow-auto flex-grow">
                      <table class="w-full text-sm text-left text-slate-500">
                        <thead class="text-xs text-slate-700 uppercase bg-slate-50 sticky top-0">
                          <tr>
                            <th scope="col" class="px-6 py-3">项目</th>
                            <th scope="col" class="px-6 py-3 text-center">健康分</th>
                            <th scope="col" class="px-6 py-3">主要风险</th>
                          </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                          ${mockData.projectRisk.map(item => `
                            <tr>
                              <th scope="row" class="px-6 py-4 font-medium text-slate-900 whitespace-nowrap">${item.name}</th>
                              <td class="px-6 py-4 text-center font-bold ${item.color}">${item.score}</td>
                              <td class="px-6 py-4">${item.risk}</td>
                            </tr>
                          `).join('')}
                        </tbody>
                      </table>
                    </div>
                  </div>
            `;
            
            // 渲染团队效能榜
            renderTeamPerformance();
            
            // 渲染主图表
            renderWorkloadChart();
        }

        // ===================================================================
        // 动态渲染函数
        // ===================================================================
        
        function createKpiCard(icon, title, value, subValue) {
            return `
                <div class="bg-white p-6 rounded-xl shadow-sm flex items-start justify-between">
                    <div>
                        <p class="text-sm font-medium text-slate-500">${title}</p>
                        <p class="text-3xl font-bold text-slate-800 mt-2">${value}</p>
                        <p class="text-xs text-slate-400 mt-1">${subValue}</p>
                    </div>
                    <div class="p-2 bg-slate-100 rounded-full">${icon}</div>
                </div>
            `;
        }
        
        function renderTeamPerformance(activeTab = 'designers') {
            const container = document.getElementById('team-performance-container');
            const perfData = mockData.teamPerformance;
            
            const columns = {
              designers: [ { header: '设计师', accessor: 'name'}, { header: '产出WE', accessor: 'we', cell: (value) => `<span class="font-bold">${value}</span>` }, { header: '过程成本WE', accessor: 'process'}, { header: '平均迭代', accessor: 'avgIter' } ],
              copywriters: [ { header: '文案', accessor: 'name' }, { header: '产出WE', accessor: 'we', cell: (value) => `<span class="font-bold">${value}</span>` }, { header: '平均迭代', accessor: 'avgIter' } ],
              pmae: [ { header: 'PM/AE', accessor: 'name' }, { header: '沟通WE', accessor: 'commWE', cell: (value) => `<span class="font-bold">${value}</span>` }, { header: '流程WE', accessor: 'flowWE' } ]
            };

            const tableHtml = (cols, data) => `
                <table class="w-full text-sm text-left text-slate-500">
                  <thead class="text-xs text-slate-700 uppercase bg-slate-50">
                    <tr>${cols.map(c => `<th scope="col" class="px-6 py-3">${c.header}</th>`).join('')}</tr>
                  </thead>
                  <tbody class="divide-y divide-slate-100">
                    ${data.map(row => `
                        <tr>
                            ${cols.map(c => `
                                <td class="px-6 py-4 font-medium text-slate-700">${c.cell ? c.cell(row[c.accessor]) : row[c.accessor]}</td>
                            `).join('')}
                        </tr>
                    `).join('')}
                  </tbody>
                </table>
            `;

            container.innerHTML = `
                <div class="bg-white p-6 rounded-xl shadow-sm h-full flex flex-col">
                  <div class="flex justify-between items-center mb-1 flex-shrink-0">
                    <h3 class="text-lg font-semibold text-slate-800">团队效能榜</h3>
                    <div class="text-sm font-medium text-center text-slate-500 border-b border-slate-200">
                      <div class="-mb-px flex space-x-4" role="tablist">
                        <button data-tab="designers" class="perf-tab py-2 px-1 border-b-2 ${activeTab === 'designers' ? 'border-indigo-500 text-indigo-600' : 'border-transparent hover:text-slate-600 hover:border-slate-300'}">设计</button>
                        <button data-tab="copywriters" class="perf-tab py-2 px-1 border-b-2 ${activeTab === 'copywriters' ? 'border-indigo-500 text-indigo-600' : 'border-transparent hover:text-slate-600 hover:border-slate-300'}">文案</button>
                        <button data-tab="pmae" class="perf-tab py-2 px-1 border-b-2 ${activeTab === 'pmae' ? 'border-indigo-500 text-indigo-600' : 'border-transparent hover:text-slate-600 hover:border-slate-300'}">PM/AE</button>
                      </div>
                    </div>
                  </div>
                  <div class="relative overflow-auto flex-grow mt-4">
                    ${tableHtml(columns[activeTab], perfData[activeTab])}
                  </div>
                </div>
            `;
        }

        function renderWorkloadChart() {
            if (typeof Chart === 'undefined') {
                console.error("Chart.js is not loaded.");
                return;
            }
            const ctx = document.getElementById('workloadChart').getContext('2d');
            const data = mockData.workloadChart;
            
            const chartData = {
                labels: data.labels,
                datasets: [
                    { type: 'line', label: '过程成本WE', data: data.processWE, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', yAxisID: 'y1', tension: 0.4, fill: true },
                    { type: 'bar', label: '总计WE', data: data.totalWE, backgroundColor: '#3b82f6', yAxisID: 'y', borderRadius: 4 },
                ],
            };
            
            const chartOptions = {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top', align: 'end', labels: { usePointStyle: true, boxWidth: 8, color: '#475569' } },
                    title: { display: true, text: '团队工作量趋势', align: 'start', font: { size: 18, weight: '600' }, color: '#1e293b' },
                    tooltip: { mode: 'index', intersect: false, backgroundColor: '#fff', titleColor: '#1e293b', bodyColor: '#475569', borderWidth: 1, borderColor: '#e2e8f0', bodyFont: {family: 'Inter'}, titleFont: {family: 'Inter'} }
                },
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 12 }, color: '#64748b' } },
                    y: { type: 'linear', display: true, position: 'left', title: { display: true, text: '总计工作量当量 (WE)', color: '#475569' }, grid: { color: '#e2e8f0' }, ticks: { color: '#64748b'} },
                    y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: '过程成本 (WE)', color: '#475569' }, grid: { drawOnChartArea: false }, ticks: { color: '#64748b'} }
                }
            };

            new Chart(ctx, { type: 'bar', data: chartData, options: chartOptions });
        }

        // ===================================================================
        // 事件监听
        // ===================================================================
        function setupTabs() {
            // 使用事件委托来处理tab点击
            const container = document.getElementById('team-performance-container');
            container.addEventListener('click', (event) => {
                if (event.target.matches('.perf-tab')) {
                    const tabName = event.target.getAttribute('data-tab');
                    renderTeamPerformance(tabName);
                }
            });
        }
    </script>
</body>
</html>
