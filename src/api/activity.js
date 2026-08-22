import request from '@/utils/request'

// 获取活动列表
export function getActivityList(params) {
  return request({
    url: '/vue-admin-template/activity/list',
    method: 'get',
    params
  })
}

// 获取活动详情
export function getActivityDetail(id) {
  return request({
    url: `/vue-admin-template/activity/detail?id=${id}`,
    method: 'get'
  })
}

// 新增活动
export function createActivity(data) {
  return request({
    url: '/vue-admin-template/activity/create',
    method: 'post',
    data
  })
}

// 更新活动
export function updateActivity(id, data) {
  return request({
    url: '/vue-admin-template/activity/update',
    method: 'post',
    data: { id, ...data }
  })
}

// 删除活动
export function deleteActivity(id) {
  return request({
    url: '/vue-admin-template/activity/delete',
    method: 'post',
    data: { id }
  })
}
