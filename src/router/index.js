import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

/* Layout */
import Layout from '@/layout'

/**
 * 路由配置说明：
 * hidden: true                   设为true则不在侧边栏显示（默认false）
 * alwaysShow: true               若设为true则始终显示根菜单
 * redirect: noRedirect           设为noRedirect则在面包屑中不重定向
 * name:'router-name'             用于<keep-alive>（必须设置）
 * meta: {
 *   roles: ['admin','editor']    控制页面角色权限
 *   title: 'title'               侧边栏和面包屑显示的名称（推荐设置）
 *   icon: 'svg-name'/'el-icon-x' 侧边栏显示的图标
 * }
 */

/**
 * 固定路由
 * 不需要权限验证的基础页面
 */
export const constantRoutes = [
  {
    path: '/login',
    component: () => import('@/views/login/index'),
    hidden: true
  },

  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [{
      path: 'dashboard',
      name: 'Dashboard',
      component: () => import('@/views/dashboard/index'),
      meta: { title: '仪表盘', icon: 'el-icon-s-home' }
    }]
  },

  // 人员管理
  {
    path: '/personnel',
    component: Layout,
    redirect: '/personnel/list',
    meta: { title: '人员管理', icon: 'el-icon-user' },
    children: [
      {
        path: 'list',
        name: 'PersonnelList',
        component: () => import('@/views/personnel/index'),
        meta: { title: '人员列表', icon: 'el-icon-user-solid' }
      }
    ]
  },

  // 政策文件管理
  {
    path: '/policy',
    component: Layout,
    redirect: '/policy/list',
    meta: { title: '政策文件管理', icon: 'el-icon-document' },
    children: [
      {
        path: 'list',
        name: 'PolicyList',
        component: () => import('@/views/policy/index'),
        meta: { title: '政策列表', icon: 'el-icon-notebook-2' }
      }
    ]
  },

  // 活动管理
  {
    path: '/activity',
    component: Layout,
    redirect: '/activity/list',
    meta: { title: '活动管理', icon: 'el-icon-date' },
    children: [
      {
        path: 'list',
        name: 'ActivityList',
        component: () => import('@/views/activity/index'),
        meta: { title: '活动列表', icon: 'el-icon-s-order' }
      }
    ]
  },

  // 用户管理（保留）
  {
    path: '/user',
    component: Layout,
    redirect: '/user/list',
    meta: { title: '用户管理', icon: 'el-icon-setting', adminOnly: true },
    children: [
      {
        path: 'list',
        name: 'UserList',
        component: () => import('@/views/user/list'),
        meta: { title: '用户列表', icon: 'el-icon-user-solid', adminOnly: true }
      },
      {
        path: 'create',
        name: 'UserCreate',
        component: () => import('@/views/user/form'),
        meta: { title: '新增用户', icon: 'el-icon-plus' },
        hidden: true
      },
      {
        path: 'edit/:id(\\d+)',
        name: 'UserEdit',
        component: () => import('@/views/user/form'),
        meta: { title: '编辑用户', icon: 'el-icon-edit' },
        hidden: true
      }
    ]
  },

  // 个人中心
  {
    path: '/profile',
    component: Layout,
    redirect: '/profile/index',
    children: [
      {
        path: 'index',
        name: 'Profile',
        component: () => import('@/views/profile/index'),
        meta: { title: '个人中心', icon: 'el-icon-setting' }
      }
    ]
  },

  // 404 页面必须放在最后
  { path: '*', redirect: '/404', hidden: true }
]

const createRouter = () => new Router({
  scrollBehavior: () => ({ y: 0 }),
  routes: constantRoutes
})

const router = createRouter()

export function resetRouter() {
  const newRouter = createRouter()
  router.matcher = newRouter.matcher
}

export default router
