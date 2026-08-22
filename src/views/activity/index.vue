<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <div class="filter-container">
      <el-input
        v-model="listQuery.name"
        placeholder="搜索活动名称"
        style="width: 200px;"
        class="filter-item"
        clearable
        @keyup.enter.native="handleFilter"
      ></el-input>
      <el-select
        v-model="listQuery.type"
        placeholder="类型筛选"
        clearable
        style="width: 150px"
        class="filter-item"
      >
        <el-option label="文化交流" value="文化交流"></el-option>
        <el-option label="学术论坛" value="学术论坛"></el-option>
        <el-option label="经贸合作" value="经贸合作"></el-option>
        <el-option label="青年联谊" value="青年联谊"></el-option>
        <el-option label="政策宣讲" value="政策宣讲"></el-option>
        <el-option label="公益慈善" value="公益慈善"></el-option>
      </el-select>
      <el-select
        v-model="listQuery.status"
        placeholder="状态筛选"
        clearable
        style="width: 120px"
        class="filter-item"
      >
        <el-option label="待举办" value="待举办"></el-option>
        <el-option label="进行中" value="进行中"></el-option>
        <el-option label="已结束" value="已结束"></el-option>
        <el-option label="已取消" value="已取消"></el-option>
      </el-select>
      <el-button class="filter-item" type="primary" icon="el-icon-search" @click="handleFilter">搜索</el-button>
      <el-button class="filter-item" type="success" icon="el-icon-plus" @click="handleAdd">新增活动</el-button>
    </div>

    <!-- 活动列表表格 -->
    <el-table v-loading="listLoading" :data="list" border fit highlight-current-row style="width: 100%">
      <el-table-column align="center" label="ID" width="80">
        <template slot-scope="scope">{{ scope.row.id }}</template>
      </el-table-column>
      <el-table-column align="center" label="活动名称" show-overflow-tooltip>
        <template slot-scope="scope">{{ scope.row.name }}</template>
      </el-table-column>
      <el-table-column align="center" label="类型" width="120">
        <template slot-scope="scope">
          <el-tag size="small">{{ scope.row.type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column align="center" label="活动时间" width="180">
        <template slot-scope="scope">{{ scope.row.time }}</template>
      </el-table-column>
      <el-table-column align="center" label="地点" width="150">
        <template slot-scope="scope">{{ scope.row.location }}</template>
      </el-table-column>
      <el-table-column align="center" label="状态" width="100">
        <template slot-scope="scope">
          <el-tag :type="statusTagType(scope.row.status)" size="small">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column align="center" label="操作" width="180" fixed="right">
        <template slot-scope="scope">
          <el-button type="primary" size="mini" icon="el-icon-edit" @click="handleEdit(scope.row)">编辑</el-button>
          <el-button type="danger" size="mini" icon="el-icon-delete" @click="handleDelete(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <pagination v-show="total > 0" :total="total" :page.sync="listQuery.page" :limit.sync="listQuery.limit" @pagination="getList"></pagination>

    <!-- 新增/编辑弹窗 -->
    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="650px" :close-on-click-modal="false">
      <el-form ref="activityForm" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="活动名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入活动名称"></el-input>
        </el-form-item>
        <el-form-item label="活动类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择类型" style="width: 100%">
            <el-option label="文化交流" value="文化交流"></el-option>
            <el-option label="学术论坛" value="学术论坛"></el-option>
            <el-option label="经贸合作" value="经贸合作"></el-option>
            <el-option label="青年联谊" value="青年联谊"></el-option>
            <el-option label="政策宣讲" value="政策宣讲"></el-option>
            <el-option label="公益慈善" value="公益慈善"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="活动时间" prop="time">
          <el-date-picker
            v-model="form.time"
            type="datetime"
            placeholder="选择活动时间"
            value-format="yyyy-MM-dd HH:mm:ss"
            style="width: 100%"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="活动地点" prop="location">
          <el-input v-model="form.location" placeholder="请输入活动地点"></el-input>
        </el-form-item>
        <el-form-item label="活动状态" prop="status">
          <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
            <el-option label="待举办" value="待举办"></el-option>
            <el-option label="进行中" value="进行中"></el-option>
            <el-option label="已结束" value="已结束"></el-option>
            <el-option label="已取消" value="已取消"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="活动描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入活动描述（可选）"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确 定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { getActivityList, createActivity, updateActivity, deleteActivity } from '@/api/activity'
import Pagination from '@/components/Pagination'

export default {
  name: 'ActivityList',
  components: { Pagination },
  data() {
    return {
      list: [],
      total: 0,
      listLoading: false,
      listQuery: { page: 1, limit: 10, name: '', type: '', status: '' },
      dialogVisible: false,
      dialogTitle: '新增活动',
      submitLoading: false,
      isEdit: false,
      editId: null,
      form: {
        name: '',
        type: '',
        time: '',
        location: '',
        status: '待举办',
        description: ''
      },
      formRules: {
        name: [{ required: true, message: '请输入活动名称', trigger: 'blur' }],
        type: [{ required: true, message: '请选择活动类型', trigger: 'change' }],
        time: [{ required: true, message: '请选择活动时间', trigger: 'change' }],
        location: [{ required: true, message: '请输入活动地点', trigger: 'blur' }],
        status: [{ required: true, message: '请选择状态', trigger: 'change' }]
      }
    }
  },
  created() {
    this.getList()
  },
  methods: {
    // 根据状态返回标签类型
    statusTagType(status) {
      const map = { '待举办': 'warning', '进行中': 'success', '已结束': 'info', '已取消': 'danger' }
      return map[status] || 'info'
    },
    // 获取活动列表
    getList() {
      this.listLoading = true
      getActivityList(this.listQuery).then(response => {
        this.list = response.data.items || []
        this.total = response.data.total || 0
        this.listLoading = false
      }).catch(() => {
        this.listLoading = false
      })
    },
    // 搜索
    handleFilter() {
      this.listQuery.page = 1
      this.getList()
    },
    // 打开新增弹窗
    handleAdd() {
      this.isEdit = false
      this.editId = null
      this.dialogTitle = '新增活动'
      this.form = { name: '', type: '', time: '', location: '', status: '待举办', description: '' }
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.activityForm && this.$refs.activityForm.clearValidate()
      })
    },
    // 打开编辑弹窗
    handleEdit(row) {
      this.isEdit = true
      this.editId = row.id
      this.dialogTitle = '编辑活动'
      this.form = {
        name: row.name,
        type: row.type,
        time: row.time,
        location: row.location,
        status: row.status,
        description: row.description || ''
      }
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.activityForm && this.$refs.activityForm.clearValidate()
      })
    },
    // 提交表单
    handleSubmit() {
      this.$refs.activityForm.validate(valid => {
        if (!valid) return
        this.submitLoading = true
        const action = this.isEdit
          ? updateActivity(this.editId, this.form)
          : createActivity(this.form)
        action.then(() => {
          this.$message.success(this.isEdit ? '修改成功' : '新增成功')
          this.dialogVisible = false
          this.getList()
          this.submitLoading = false
        }).catch(() => {
          this.submitLoading = false
        })
      })
    },
    // 删除活动
    handleDelete(id) {
      this.$confirm('确认删除该活动？此操作不可恢复。', '删除确认', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        deleteActivity(id).then(() => {
          this.$message.success('删除成功')
          this.getList()
        })
      }).catch(() => {})
    }
  }
}
</script>

<style scoped>
.filter-container { padding-bottom: 20px; }
.filter-item { margin-right: 10px; }
</style>
