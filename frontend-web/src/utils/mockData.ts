// Mock data for the plant monitoring system (English only)

export const mockPlants = [
  {
    id: '1',
    nickname: 'Little Green',
    species: 'Pothos',
    location: 'Living room window',
    status: 'healthy',
    lastUpdate: '2 minutes ago',
    lastDream: '1 hour ago',
    growthRate: 2.3,
    createdAt: '2024-10-15',
    lastWatering: '2024-11-26 18:30'
  },
  {
    id: '2',
    nickname: 'Succulent Buddy',
    species: 'Succulent',
    location: 'Balcony',
    status: 'slightly_stressed',
    lastUpdate: '15 minutes ago',
    lastDream: '3 hours ago',
    growthRate: -0.5,
    createdAt: '2024-09-20',
    lastWatering: '2024-11-24 10:00'
  },
  {
    id: '3',
    nickname: 'Cactus Pal',
    species: 'Cactus',
    location: 'Study',
    status: 'healthy',
    lastUpdate: '30 minutes ago',
    lastDream: '2 hours ago',
    growthRate: 1.2,
    createdAt: '2024-11-01',
    lastWatering: '2024-11-20 14:00'
  },
  {
    id: '4',
    nickname: 'Hanging Ivy',
    species: 'Ivy',
    location: 'Bedroom',
    status: 'stressed',
    lastUpdate: '2 hours ago',
    lastDream: '1 day ago',
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
    message: 'Succulent Buddy had negative growth over the last 3 days',
    time: '30 minutes ago'
  },
  {
    id: '2',
    message: 'Hanging Ivy soil moisture often near 255 (too dry)',
    time: '2 hours ago'
  },
  {
    id: '3',
    message: 'Little Green temperature sensor has no update for 2 hours',
    time: '3 hours ago'
  }
];

export const mockRecentDreams = [
  { id: '1', plantName: 'Little Green', time: '1 hour ago' },
  { id: '2', plantName: 'Succulent Buddy', time: '3 hours ago' },
  { id: '3', plantName: 'Cactus Pal', time: '5 hours ago' },
  { id: '4', plantName: 'Little Green', time: 'yesterday' }
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
    { name: 'Temperature stress', value: 1.2, max: 10 },
    { name: 'Humidity stress', value: 3.5, max: 10 },
    { name: 'Light stress', value: 2.1, max: 10 },
    { name: 'Growth stress', value: 0.8, max: 10 }
  ]
};

export const mockReports = [
  {
    id: '1',
    plantId: '1',
    timestamp: '2024-11-28 09:30',
    summary: 'Today growth is good, all indicators normal',
    content: `Today’s growth looks good. In the past 24 hours, plant weight dropped from 458g to 455g, within normal transpiration range.

Environment: temperature 22-24°C, good light (avg 340 lux), soil moisture 35-40%. Suitable for pothos.

Growth analysis: 3-day growth rate 0.3%, still positive. Stress factors safe; humidity stress a bit high (3.5/10); water slightly more often.

Advice: keep current routine, watch soil moisture; if it keeps dropping, add ~200ml water in the evening.`,
    trigger: 'manual',
    environment: {
      temperature: 23,
      moisture: 40,
      light: 340,
      weight: 455
    }
  },
  {
    id: '2',
    plantId: '1',
    timestamp: '2024-11-27 14:20',
    summary: 'Post-watering status review',
    content: `Post-watering 5-minute check: absorbed ~180ml, weight up to 642g.

Before watering: soil moisture 34% (slightly dry). Temp 23°C, light good.

After watering: soil moisture up to 65%, ideal. No pooling seen.

Advice: amount is fine, should last 3-4 days. Next watering around Nov 29-30 depending on soil. Watch leaves for overwatering signs.`,
    trigger: 'watering',
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
    summary: 'Trend review',
    content: `On request, we ran a full trend review.

Past 7 days: weight moved from 485g to 468g, daily transpiration ~2.4g, normal. Temperature 20-25°C, stable.

Growth rate slowed from 2.1% to 1.2%, likely seasonal (less daylight).

Suggestion: add 1-2h supplemental light; keep room at 24-26°C.`,
    trigger: 'manual',
    environment: {
      temperature: 25,
      moisture: 28,
      light: 420,
      weight: 320
    }
  }
];

export const mockDreams = [
  {
    id: '1',
    plantId: '1',
    timestamp: '2024-11-28 10:30',
    description: 'Sunlight through the curtain, warm and soft. Feeling energy building, leaves stretching for more light.',
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
    description: 'Afternoon light is bright; every leaf reaches out to catch the sun. Cells feel alive with energy.',
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
    description: 'A bit thirsty; soil drier than yesterday, but holding on. Hoping for a drink soon.',
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
    description: 'Morning sun wakes me up. Water is low, but warmth brings hope. Waiting for watering.',
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
    description: 'As a cactus, dry air feels right. Strong light feeds me; storing energy for tonight.',
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
    description: 'Quiet afternoon in the study. I do not need much water, but every drop is precious.',
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
    description: 'Feeling tired; soil too dry and roots hunting for moisture. Hope someone notices.',
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
    description: 'Morning dew is refreshing. Yesterday’s watering was just in time; feeling full of life.',
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
    name: 'Daily plant analysis',
    description: 'Analyze all plants every morning at 08:00',
    schedule: 'Daily 08:00',
    status: 'running',
    nextRun: '2024-11-29 08:00'
  },
  {
    id: '2',
    name: '6-hour LLM report',
    description: 'Generate LLM reports every 6 hours',
    schedule: 'Every 6 hours',
    status: 'running',
    nextRun: '2024-11-28 18:00'
  },
  {
    id: '3',
    name: 'Dream image generation',
    description: 'Generate a dream garden image for each plant',
    schedule: 'Daily 10:00',
    status: 'running',
    nextRun: '2024-11-29 10:00'
  },
  {
    id: '4',
    name: 'Data cleanup task',
    description: 'Clean sensor data older than 30 days',
    schedule: 'Weekly Sun 02:00',
    status: 'running',
    nextRun: '2024-12-01 02:00'
  }
];

export const mockSchedulerLogs = [
  {
    id: '1',
    timestamp: '2024-11-28 10:00',
    jobType: 'Dream image generation',
    status: 'success',
    message: 'Generated dream images for 4 plants',
    duration: '45s'
  },
  {
    id: '2',
    timestamp: '2024-11-28 08:00',
    jobType: 'Daily plant analysis',
    status: 'success',
    message: 'Completed growth analysis for all plants',
    duration: '2m15s'
  },
  {
    id: '3',
    timestamp: '2024-11-28 06:00',
    jobType: '6-hour LLM report',
    status: 'success',
    message: 'Generated 3 new analysis reports',
    duration: '1m30s'
  },
  {
    id: '4',
    timestamp: '2024-11-28 00:00',
    jobType: '6-hour LLM report',
    status: 'warning',
    message: 'Plant #2 had insufficient data, skipped report',
    duration: '55s'
  },
  {
    id: '5',
    timestamp: '2024-11-27 18:00',
    jobType: '6-hour LLM report',
    status: 'success',
    message: 'Generated 4 new analysis reports',
    duration: '1m45s'
  },
  {
    id: '6',
    timestamp: '2024-11-27 10:00',
    jobType: 'Dream image generation',
    status: 'failed',
    message: 'Plant #4 dream image generation failed: API timeout',
    duration: '30s'
  },
  {
    id: '7',
    timestamp: '2024-11-27 08:00',
    jobType: 'Daily plant analysis',
    status: 'success',
    message: 'Completed growth analysis for all plants',
    duration: '2m20s'
  },
  {
    id: '8',
    timestamp: '2024-11-27 06:00',
    jobType: '6-hour LLM report',
    status: 'success',
    message: 'Generated 4 new analysis reports',
    duration: '1m40s'
  }
];
