<template>
  <div class="dashboard-container">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-content">
        <div class="welcome-info">
          <el-avatar :size="70" class="user-avatar">
            <i class="el-icon-user" style="font-size:32px;"></i>
          </el-avatar>
          <div class="welcome-text">
            <h1>欢迎使用港澳台侨管库系统</h1>
            <p class="subtitle">{{ welcomeMessage }}</p>
            <div class="time-display">
              <i class="el-icon-time"></i>
              <span>{{ currentTime }}</span>
              <el-divider direction="vertical"></el-divider>
              <i class="el-icon-date"></i>
              <span>{{ currentDate }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="24" :sm="12" :md="6" v-for="(stat, index) in stats" :key="index">
        <div class="stat-card" :class="stat.type">
          <div class="stat-content">
            <div class="stat-header">
              <div class="stat-icon">
                <i :class="stat.icon"></i>
              </div>
            </div>
            <div class="stat-value">
              <span class="number">{{ stat.value }}</span>
              <span class="unit">{{ stat.unit }}</span>
            </div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :sm="24" :md="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="card-title">
            <i class="el-icon-pie-chart"></i>
            <span>人员地区分布</span>
          </div>
          <div ref="pieChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12">
        <el-card shadow="hover" class="chart-card">
          <div slot="header" class="card-title">
            <i class="el-icon-s-data"></i>
            <span>活动类型统计</span>
          </div>
          <div ref="barChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover" class="action-card">
          <div slot="header" class="card-title">
            <i class="el-icon-s-operation"></i>
            <span>快捷操作</span>
          </div>
          <div class="quick-actions-grid">
            <div class="action-item" v-for="(action, index) in quickActions" :key="index" @click="$router.push(action.path)">
              <div class="action-icon" :style="{ background: action.gradient }">
                <i :class="action.icon"></i>
              </div>
              <span class="action-label">{{ action.label }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import * as echarts from 'echarts'

export default {
  name: 'Dashboard',
  data() {
    return {
      currentTime: '',
      currentDate: '',
      timer: null,
      pieChart: null,
      barChart: null,
      welcomeMessage: '',
      stats: [
        { label: '人员总数', value: 1286, unit: '人', icon: 'el-icon-user-solid', type: 'primary' },
        { label: '政策文件数', value: 85, unit: '份', icon: 'el-icon-document', type: 'success' },
        { label: '活动总数', value: 342, unit: '场', icon: 'el-icon-date', type: 'warning' },
        { label: '本月活动数', value: 18, unit: '场', icon: 'el-icon-s-calendar', type: 'danger' }
      ],
      quickActions: [
        { label: '人员管理', icon: 'el-icon-user', path: '/personnel/list', gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
        { label: '政策文件', icon: 'el-icon-document', path: '/policy/list', gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' },
        { label: '活动管理', icon: 'el-icon-date', path: '/activity/list', gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' },
        { label: '用户管理', icon: 'el-icon-setting', path: '/user/list', gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }
      ]
    }
  },
  computed: {
    ...mapGetters(['name', 'role', 'isAdmin'])
  },
  mounted() {
    this.updateTime()
    this.setWelcomeMessage()
    this.timer = setInterval(() => {
      this.updateTime()
    }, 1000)
    this.$nextTick(() => {
      this.initPieChart()
      this.initBarChart()
    })
  },
  beforeDestroy() {
    clearInterval(this.timer)
    if (this.pieChart) this.pieChart.dispose()
    if (this.barChart) this.barChart.dispose()
  },
  methods: {
    updateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString('zh-CN')
      this.currentDate = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
    },
    setWelcomeMessage() {
      const hour = new Date().getHours()
      if (hour < 6) this.welcomeMessage = '夜深了，注意休息'
      else if (hour < 9) this.welcomeMessage = '早上好，新的一天开始了'
      else if (hour < 12) this.welcomeMessage = '上午好，祝您工作顺利'
      else if (hour < 14) this.welcomeMessage = '中午好，记得午休'
      else if (hour < 17) this.welcomeMessage = '下午好，继续加油'
      else if (hour < 19) this.welcomeMessage = '傍晚好，辛苦了'
      else this.welcomeMessage = '晚上好，注意休息'
    },
    // 初始化按地区分布饼图
    initPieChart() {
      if (!this.$refs.pieChart) return
      this.pieChart = echarts.init(this.$refs.pieChart)
      const option = {
        tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
        legend: { orient: 'vertical', left: 'left', top: 'center' },
        color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#b37feb', '#36cfc9'],
        series: [{
          name: '地区分布',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { show: true, formatter: '{b}\n{d}%' },
          emphasis: { label: { show: true, fontSize: '14', fontWeight: 'bold' } },
          data: [
            { value: 380, name: '香港' },
            { value: 320, name: '澳门' },
            { value: 426, name: '台湾' },
            { value: 160, name: '华侨(东南亚)' }
          ]
        }]
      }
      this.pieChart.setOption(option)
    },
    // 初始化活动类型柱状图
    initBarChart() {
      if (!this.$refs.barChart) return
      this.barChart = echarts.init(this.$refs.barChart)
      const option = {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: ['文化交流', '学术论坛', '经贸合作', '青年联谊', '政策宣讲', '公益慈善'], axisLabel: { interval: 0, rotate: 15 } },
        yAxis: { type: 'value', name: '活动数量(场)' },
        color: ['#409eff'],
        series: [{
          name: '活动数量',
          type: 'bar',
          barWidth: '40%',
          data: [68, 52, 45, 78, 56, 43],
          itemStyle: { borderRadius: [6, 6, 0, 0], color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])}
        }]
      }
      this.barChart.setOption(option)
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;
  background: #f0f2f5;
  min-height: calc(100vh - 84px);
}

.welcome-banner {
  margin-bottom: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 30px 40px;
  color: white;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);

  .banner-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .welcome-info {
    display: flex;
    align-items: center;
    gap: 20px;
  }

  .welcome-text {
    h1 {
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 8px;
    }
    .subtitle {
      font-size: 14px;
      opacity: 0.9;
      margin-bottom: 8px;
    }
  }

  .time-display {
    font-size: 13px;
    opacity: 0.8;
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

.stat-cards {
  .stat-card {
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 10px;
    transition: all 0.3s ease;
    cursor: default;
    position: relative;
    overflow: hidden;

    &.primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    &.success { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    &.warning { background: linear-gradient(135deg, #f6d365 0%, #fda085 100%); }
    &.danger { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }

    .stat-content {
      position: relative;
      z-index: 1;
      color: white;

      .stat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;

        .stat-icon {
          width: 50px;
          height: 50px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          background: rgba(255, 255, 255, 0.2);
          backdrop-filter: blur(5px);
          border: 1px solid rgba(255, 255, 255, 0.3);
        }
      }

      .stat-value {
        margin-bottom: 8px;
        .number {
          font-size: 36px;
          font-weight: 800;
          line-height: 1;
        }
        .unit {
          font-size: 14px;
          margin-left: 4px;
          opacity: 0.9;
        }
      }

      .stat-label {
        font-size: 14px;
        opacity: 0.85;
        font-weight: 500;
      }
    }
  }
}

.chart-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    transform: translateY(-4px);
  }

  ::v-deep .el-card__header {
    border-bottom: 2px solid #f0f2f5;
    padding: 16px 20px;
  }

  .chart-container {
    width: 100%;
    height: 320px;
  }
}

.action-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    transform: translateY(-4px);
  }

  ::v-deep .el-card__header {
    border-bottom: 2px solid #f0f2f5;
    padding: 16px 20px;
  }
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 17px;
  font-weight: 700;
  color: #303133;

  i {
    margin-right: 10px;
    font-size: 20px;
    color: #409eff;
  }
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
  padding: 10px 0;

  .action-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 10px;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    background: #fafafa;

    &:hover {
      transform: translateY(-5px) scale(1.05);
      background: white;
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }

    .action-icon {
      width: 56px;
      height: 56px;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      color: white;
      margin-bottom: 12px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    .action-label {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
    }
  }
}

@media screen and (max-width: 768px) {
  .stat-cards .stat-card .stat-content .stat-value .number {
    font-size: 28px;
  }
  .quick-actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
