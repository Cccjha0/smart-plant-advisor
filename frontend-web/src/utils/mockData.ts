// Mock data for the plant monitoring system

export const mockPlants = [
  {
    id: '1',
    nickname: '小绿',
    species: '绿萝',
    location: '客厅窗台',
    status: 'healthy',
    lastUpdate: '2分钟前',
    lastDream: '1小时前',
    growthRate: 2.3,
    createdAt: '2024-10-15',
    lastWatering: '2024-11-26 18:30'
  },
  {
    id: '2',
    nickname: '多肉宝宝',
    species: '多肉植物',
    location: '阳台',
    status: 'slightly_stressed',
    lastUpdate: '15分钟前',
    lastDream: '3小时前',
    growthRate: -0.5,
    createdAt: '2024-09-20',
    lastWatering: '2024-11-24 10:00'
  },
  {
    id: '3',
    nickname: '仙人掌君',
    species: '仙人掌',
    location: '书房',
    status: 'healthy',
    lastUpdate: '30分钟前',
    lastDream: '2小时前',
    growthRate: 1.2,
    createdAt: '2024-11-01',
    lastWatering: '2024-11-20 14:00'
  },
  {
    id: '4',
    nickname: '吊兰',
    species: '吊兰',
    location: '卧室',
    status: 'stressed',
    lastUpdate: '2小时前',
    lastDream: '1天前',
    growthRate: -1.8,
    createdAt: '2024-08-05',
    lastWatering: '2024-11-27 09:00'
  }
];

export const mockStats = {
  totalPlants: 4,
  activePlants24h: 3,
  stressedPlants: 1,
  todayDreams: 8
};

export const mockAlerts = [
  {
    id: '1',
    message: '多肉宝宝在过去3天生长率为负',
    time: '30分钟前'
  },
  {
    id: '2',
    message: '吊兰土壤湿度经常接近255（过干）',
    time: '2小时前'
  },
  {
    id: '3',
    message: '小绿的温度传感器2小时未更新数据',
    time: '3小时前'
  }
];

export const mockRecentDreams = [
  {
    id: '1',
    plantName: '小绿',
    time: '1小时前'
  },
  {
    id: '2',
    plantName: '多肉宝宝',
    time: '3小时前'
  },
  {
    id: '3',
    plantName: '仙人掌君',
    time: '5小时前'
  },
  {
    id: '4',
    plantName: '小绿',
    time: '昨天'
  }
];

export const mockMetricsData = {
  weight: [
    { time: '11-22', value: 485 },
    { time: '11-23', value: 478 },
    { time: '11-24', value: 472 },
    { time: '11-25', value: 468 },
    { time: '11-26', value: 462 },
    { time: '11-27', value: 458 },
    { time: '11-28', value: 455 }
  ],
  moisture: [
    { time: '11-22', value: 45 },
    { time: '11-23', value: 52 },
    { time: '11-24', value: 38 },
    { time: '11-25', value: 42 },
    { time: '11-26', value: 48 },
    { time: '11-27', value: 35 },
    { time: '11-28', value: 40 }
  ],
  temperature: [
    { time: '11-22', value: 22 },
    { time: '11-23', value: 23 },
    { time: '11-24', value: 21 },
    { time: '11-25', value: 22 },
    { time: '11-26', value: 24 },
    { time: '11-27', value: 23 },
    { time: '11-28', value: 22 }
  ],
  light: [
    { time: '11-22', value: 320 },
    { time: '11-23', value: 380 },
    { time: '11-24', value: 290 },
    { time: '11-25', value: 350 },
    { time: '11-26', value: 410 },
    { time: '11-27', value: 360 },
    { time: '11-28', value: 340 }
  ]
};

export const mockDetailedMetrics = [
  { timestamp: '00:00', temperature: 21, light: 0, moisture: 40, weight: 455 },
  { timestamp: '04:00', temperature: 20, light: 0, moisture: 39, weight: 454 },
  { timestamp: '08:00', temperature: 22, light: 150, moisture: 38, weight: 453 },
  { timestamp: '12:00', temperature: 24, light: 400, moisture: 36, weight: 451 },
  { timestamp: '16:00', temperature: 25, light: 350, moisture: 35, weight: 450 },
  { timestamp: '20:00', temperature: 23, light: 100, moisture: 34, weight: 449 },
  { timestamp: '23:59', temperature: 22, light: 0, moisture: 33, weight: 448 }
];

export const mockGrowthAnalysis = {
  dailyWeight: [
    { date: '11-22', actual: 485, reference: 483 },
    { date: '11-23', actual: 478, reference: 481 },
    { date: '11-24', actual: 472, reference: 479 },
    { date: '11-25', actual: 468, reference: 477 },
    { date: '11-26', actual: 462, reference: 475 },
    { date: '11-27', actual: 458, reference: 473 },
    { date: '11-28', actual: 455, reference: 471 }
  ],
  growthRate: [
    { date: '11-22', rate: 2.1 },
    { date: '11-23', rate: 1.8 },
    { date: '11-24', rate: 1.5 },
    { date: '11-25', rate: 1.2 },
    { date: '11-26', rate: 0.8 },
    { date: '11-27', rate: 0.5 },
    { date: '11-28', rate: 0.3 }
  ],
  stressFactors: [
    { name: '温度压力', value: 1.2, max: 10 },
    { name: '湿度压力', value: 3.5, max: 10 },
    { name: '光照压力', value: 2.1, max: 10 },
    { name: '生长压力', value: 0.8, max: 10 }
  ]
};

export const mockReports = [
  {
    id: '1',
    summary: '今日生长状态良好，各项指标正常',
    trigger: 'scheduled',
    timestamp: '2024-11-28 08:00',
    content: `今日小绿的生长状态整体良好。过去24小时内，植物体重从458g降至455g，属于正常的蒸腾作用范围。

环境条件：温度维持在22-24°C之间，光照充足（平均340 lux），土壤湿度保持在35-40%的适宜范围内。这些条件非常适合绿萝的生长需求。

生长分析：3日生长率为0.3%，虽然增速放缓，但仍保持正向增长。压力因子分析显示各项指标均在安全范围内，其中湿度压力略高（3.5/10），建议适当增加浇水频率。

后续建议：继续保持当前的养护节奏，密切关注土壤湿度变化。如果湿度持续下降，建议在傍晚时分补充200ml左右的水分。`
  },
  {
    id: '2',
    summary: '浇水后状态评估 - 水分吸收良好',
    trigger: 'watering',
    timestamp: '2024-11-26 18:35',
    content: `浇水后5分钟监测报告：小绿成功吸收了约180ml水分，体重从462g增至642g。

浇水前状态：土壤湿度34%，略显偏干。温度23°C，光照条件良好。

浇水后变化：土壤湿度迅速上升至65%，达到理想状态。植物根系吸水活跃，未发现积水或渗漏异常。

建议：本次浇水量适中，预计可维持3-4天。下次浇水建议在11月29日或30日，根据土壤湿度实际情况调整。注意观察叶片状态，确保无积水引起的病害迹象。`
  },
  {
    id: '3',
    summary: '手动触发分析 - 生长趋势评估',
    trigger: 'manual',
    timestamp: '2024-11-25 14:20',
    content: `应用户请求，对小绿进行了全面的生长趋势评估。

过去7天数据回顾：植物从485g稳定降至468g，日均蒸腾量约2.4g，符合绿萝的正常代谢水平。环境温度波动在20-25°C之间，整体稳定。

关键发现：生长率从7天前的2.1%逐步降至1.2%，显示生长速度有所放缓。这可能与冬季来临、日照时长减少有关，属于季节性正常现象。

优化建议：考虑在白天增加人工补光时长1-2小时，以弥补自然光照不足。适当提高室内温度至24-26°C，为植物创造更舒适的生长环境。`
  }
];

export const mockPhotos = [
  {
    id: '1',
    date: '2024-11-28',
    time: '09:30',
    path: '/home/pi/plants/plant_1/img_20241128_093000.jpg',
    analysisStatus: 'success',
    analysis: '叶片色泽鲜绿，生长态势良好。未发现病虫害迹象，整体健康状况优秀。'
  },
  {
    id: '2',
    date: '2024-11-28',
    time: '15:45',
    path: '/home/pi/plants/plant_1/img_20241128_154500.jpg',
    analysisStatus: 'pending',
    analysis: null
  },
  {
    id: '3',
    date: '2024-11-27',
    time: '10:20',
    path: '/home/pi/plants/plant_1/img_20241127_102000.jpg',
    analysisStatus: 'success',
    analysis: '新叶生长点清晰可见，说明植物处于活跃生长期。建议保持当前养护方式。'
  },
  {
    id: '4',
    date: '2024-11-26',
    time: '16:30',
    path: '/home/pi/plants/plant_1/img_20241126_163000.jpg',
    analysisStatus: 'success',
    analysis: '浇水后叶片挺立，吸水状况良好。土壤表面湿润度适中。'
  },
  {
    id: '5',
    date: '2024-11-25',
    time: '11:15',
    path: '/home/pi/plants/plant_1/img_20241125_111500.jpg',
    analysisStatus: 'success',
    analysis: '部分老叶出现轻微黄化，属于正常代谢现象。整体生长健康。'
  },
  {
    id: '6',
    date: '2024-11-24',
    time: '09:00',
    path: '/home/pi/plants/plant_1/img_20241124_090000.jpg',
    analysisStatus: 'success',
    analysis: '光照充足，叶片舒展。未发现异常状况。'
  },
  {
    id: '7',
    date: '2024-11-20',
    time: '14:30',
    path: '/home/pi/plants/plant_1/img_20241120_143000.jpg',
    analysisStatus: 'success',
    analysis: '植株整体形态优美，株型紧凑。生长平衡性良好。'
  },
  {
    id: '8',
    date: '2024-11-18',
    time: '10:45',
    path: '/home/pi/plants/plant_1/img_20241118_104500.jpg',
    analysisStatus: 'failed',
    analysis: null
  }
];

export const mockDreams = [
  {
    id: '1',
    plantId: '1',
    timestamp: '2024-11-28 10:30',
    description: '今天阳光透过窗帘洒在我的叶片上，温暖而舒适。我感觉到水分在根系中缓缓流动，带来生命的活力。空气中弥漫着泥土的芬芳，这是我最喜欢的味道。',
    environment: {
      temperature: 23,
      moisture: 42,
      light: 340,
      weight: 455
    }
  },
  {
    id: '2',
    plantId: '1',
    timestamp: '2024-11-27 14:20',
    description: '午后的光线格外明媚，我伸展着每一片叶子去捕捉阳光。感觉今天的能量特别充沛，仿佛能听到细胞分裂的声音。',
    environment: {
      temperature: 24,
      moisture: 38,
      light: 380,
      weight: 458
    }
  },
  {
    id: '3',
    plantId: '2',
    timestamp: '2024-11-28 11:15',
    description: '有些口渴了，土壤似乎比昨天更干一些。但我依然坚强，储存在叶片中的水分足以支撑我度过今天。期待主人的照顾。',
    environment: {
      temperature: 25,
      moisture: 28,
      light: 420,
      weight: 320
    }
  },
  {
    id: '4',
    plantId: '2',
    timestamp: '2024-11-27 09:45',
    description: '清晨的第一缕阳光唤醒了我。虽然水分有些不足，但温暖的阳光让我充满希望。我会耐心等待下一次浇水。',
    environment: {
      temperature: 22,
      moisture: 30,
      light: 280,
      weight: 318
    }
  },
  {
    id: '5',
    plantId: '3',
    timestamp: '2024-11-28 15:00',
    description: '作为仙人掌，干燥的环境正是我所习惯的。今天的光照特别强烈，我贪婪地吸收着每一分热量，为夜晚储备能量。',
    environment: {
      temperature: 26,
      moisture: 15,
      light: 500,
      weight: 680
    }
  },
  {
    id: '6',
    plantId: '3',
    timestamp: '2024-11-26 12:30',
    description: '宁静的午后，我静静地矗立在书房里。虽然我不需要太多水分，但每一滴都格外珍贵，我会好好珍藏。',
    environment: {
      temperature: 24,
      moisture: 18,
      light: 450,
      weight: 682
    }
  },
  {
    id: '7',
    plantId: '4',
    timestamp: '2024-11-27 16:00',
    description: '感觉有些疲惫，土壤太干了，我的根系在努力寻找水分。希望主人能注意到我的需求。',
    environment: {
      temperature: 23,
      moisture: 20,
      light: 300,
      weight: 410
    }
  },
  {
    id: '8',
    plantId: '1',
    timestamp: '2024-11-26 08:00',
    description: '清晨的露水让我神清气爽。昨天的浇水来得正是时候，我感觉充满了生命力，准备迎接新的一天。',
    environment: {
      temperature: 21,
      moisture: 55,
      light: 200,
      weight: 462
    }
  }
];

export const mockAdminStats = {
  totalPlants: 4,
  totalImages: 156,
  totalSensorRecords: 12480,
  totalAnalysisResults: 328,
  totalDreams: 145,
  schedulerRunning: true
};

export const mockSchedulerJobs = [
  {
    id: '1',
    name: '每日植物分析',
    description: '每天早上8点对所有植物进行生长分析',
    schedule: '每天 08:00',
    status: 'running',
    nextRun: '2024-11-29 08:00'
  },
  {
    id: '2',
    name: '6小时LLM报告',
    description: '每6小时生成一次LLM分析报告',
    schedule: '每6小时',
    status: 'running',
    nextRun: '2024-11-28 18:00'
  },
  {
    id: '3',
    name: '梦境图生成',
    description: '每天为每个植物生成梦境花园图',
    schedule: '每天 10:00',
    status: 'running',
    nextRun: '2024-11-29 10:00'
  },
  {
    id: '4',
    name: '数据清理任务',
    description: '每周清理30天前的旧传感器数据',
    schedule: '每周日 02:00',
    status: 'running',
    nextRun: '2024-12-01 02:00'
  }
];

export const mockSchedulerLogs = [
  {
    id: '1',
    timestamp: '2024-11-28 10:00',
    jobType: '梦境图生成',
    status: 'success',
    message: '成功为4个植物生成梦境图',
    duration: '45秒'
  },
  {
    id: '2',
    timestamp: '2024-11-28 08:00',
    jobType: '每日植物分析',
    status: 'success',
    message: '完成所有植物的生长分析',
    duration: '2分15秒'
  },
  {
    id: '3',
    timestamp: '2024-11-28 06:00',
    jobType: '6小时LLM报告',
    status: 'success',
    message: '生成了3份新的分析报告',
    duration: '1分30秒'
  },
  {
    id: '4',
    timestamp: '2024-11-28 00:00',
    jobType: '6小时LLM报告',
    status: 'warning',
    message: 'Plant #2 数据不足，跳过报告生成',
    duration: '55秒'
  },
  {
    id: '5',
    timestamp: '2024-11-27 18:00',
    jobType: '6小时LLM报告',
    status: 'success',
    message: '生成了4份新的分析报告',
    duration: '1分45秒'
  },
  {
    id: '6',
    timestamp: '2024-11-27 10:00',
    jobType: '梦境图生成',
    status: 'failed',
    message: 'Plant #4 图片生成失败：API超时',
    duration: '30秒'
  },
  {
    id: '7',
    timestamp: '2024-11-27 08:00',
    jobType: '每日植物分析',
    status: 'success',
    message: '完成所有植物的生长分析',
    duration: '2分20秒'
  },
  {
    id: '8',
    timestamp: '2024-11-27 06:00',
    jobType: '6小时LLM报告',
    status: 'success',
    message: '生成了4份新的分析报告',
    duration: '1分40秒'
  }
];
