import api from './request'

export const historyApi = {
  // 获取树状结构数据
  getTree() {
    return api.get('/history/tree')
  },

  // 获取年份列表
  getYears() {
    return api.get('/history/years')
  },

  // 获取月份数据
  getMonths(year: number) {
    return api.get('/history/months', { params: { year } })
  },

  // 获取周数据
  getWeeks(year: number, month: number) {
    return api.get('/history/weeks', { params: { year, month } })
  },

  // 获取日数据
  getDays(year: number, month: number, week?: number) {
    return api.get('/history/days', { params: { year, month, week } })
  },

  // 获取热点详情
  getDetail(periodType: string, periodValue: string) {
    return api.get('/history/detail', { params: { period_type: periodType, period_value: periodValue } })
  },

  // 手动采集
  manualCollect(periodType: string = 'daily') {
    return api.post('/history/collect', null, { params: { period_type: periodType } })
  },

  // 获取调度器状态
  getSchedulerStatus(taskName?: string) {
    return api.get('/history/scheduler/status', { params: { task_name: taskName } })
  }
}
