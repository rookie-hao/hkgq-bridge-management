import request from '@/utils/request'

// 获取人员列表
export function getPersonnelList(params) {
  return request({
    url: '/vue-admin-template/personnel/list',
    method: 'get',
    params
  })
}

// 获取人员详情
export function getPersonnelDetail(id) {
  return request({
    url: `/vue-admin-template/personnel/detail?id=${id}`,
    method: 'get'
  })
}

// 新增人员
export function createPersonnel(data) {
  return request({
    url: '/vue-admin-template/personnel/create',
    method: 'post',
    data
  })
}

// 更新人员
export function updatePersonnel(id, data) {
  return request({
    url: '/vue-admin-template/personnel/update',
    method: 'post',
    data: { id, ...data }
  })
}

// 删除人员
export function deletePersonnel(id) {
  return request({
    url: '/vue-admin-template/personnel/delete',
    method: 'post',
    data: { id }
  })
}
