import request from '@/utils/request'

// 获取政策文件列表
export function getPolicyList(params) {
  return request({
    url: '/vue-admin-template/policy/list',
    method: 'get',
    params
  })
}

// 获取政策文件详情
export function getPolicyDetail(id) {
  return request({
    url: `/vue-admin-template/policy/detail?id=${id}`,
    method: 'get'
  })
}

// 新增政策文件
export function createPolicy(data) {
  return request({
    url: '/vue-admin-template/policy/create',
    method: 'post',
    data
  })
}

// 更新政策文件
export function updatePolicy(id, data) {
  return request({
    url: '/vue-admin-template/policy/update',
    method: 'post',
    data: { id, ...data }
  })
}

// 删除政策文件
export function deletePolicy(id) {
  return request({
    url: '/vue-admin-template/policy/delete',
    method: 'post',
    data: { id }
  })
}
